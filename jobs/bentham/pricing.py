#!/usr/bin/env python3
"""Pricing: API list-price dollars for recorded tokens, from jobs/necker-costs/PRICES.json only.

Bentham used to carry its own table (Opus 5 and Sonnet 4.x rates, one cache-write rate for both
time-to-live classes). The models in the waves' transcripts are Opus 5.5 and Sonnet 5.5, which list
lower, so Bentham's costs ran 1.3x to 1.9x high (Gutenberg, 2026-11-09: measured against the 16
`claude -p` sessions of the Haloander and Cujas waves whose own `total_cost_usd` was logged). This
module reads Necker's PRICES.json, the one maintained table, and applies its rules:

* rates are per exact model, matched by the table's ``match`` regular expressions, in order;
* 5-minute and 1-hour cache writes have separate rates; a write total with no split is priced at the
  5-minute rate and reported as ``unclassified`` (a lower bound if it was really a 1-hour write);
* ``speed == "fast"`` multiplies every rate by the model's ``fast_multiplier``; a row total does not
  record speed, so only per-call pricing (sessions.py) can apply it;
* Haiku 5.5's long-prompt rates apply per request, so they too are applied per call; a row total that
  might contain long prompts is priced at the short rates and flagged;
* a model the table does not match is left unpriced (``None``), never guessed;
* a row with no model id but a family alias (``opus``/``sonnet``/``haiku``) is priced at the alias's
  current model and flagged ``assumed_model``.

Dollars are API-equivalent estimates, not invoices.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REL = "jobs/necker-costs/PRICES.json"
CATS = ("fresh_input", "cache_read", "cache_write_5m", "cache_write_1h", "cache_write_unclassified", "output")
RATE_KEY = {"fresh_input": "input", "cache_read": "cache_read", "cache_write_5m": "cache_write_5m",
            "cache_write_1h": "cache_write_1h", "cache_write_unclassified": "cache_write_5m", "output": "output"}


class PricingError(RuntimeError):
    pass


class Prices:
    def __init__(self, data: dict, source: str = REL):
        if not isinstance(data, dict) or not isinstance(data.get("models"), list) or not data["models"]:
            raise PricingError(f"{source}: no 'models' list")
        self.source = source
        self.retrieved = data.get("retrieved")
        self.models = []
        for m in data["models"]:
            missing = [k for k in ("match", "input", "cache_write_5m", "cache_write_1h", "cache_read", "output")
                       if k not in m]
            if missing:
                raise PricingError(f"{source}: model {m.get('name')!r} lacks {missing}")
            self.models.append((re.compile(m["match"]), m))
        self.aliases = {k: v for k, v in (data.get("aliases_for_telemetry_without_a_model_id") or {}).items()
                        if k in ("opus", "sonnet", "haiku")}

    @classmethod
    def load(cls, repo) -> "Prices":
        p = Path(repo) / REL
        try:
            return cls(json.loads(p.read_text(encoding="utf-8")), REL)
        except FileNotFoundError:
            raise PricingError(f"{REL} is missing; Bentham prices tokens only from Necker's table") from None
        except json.JSONDecodeError as e:
            raise PricingError(f"{REL} is not valid JSON: {e}") from None

    def entry(self, model: str):
        model = (model or "").strip()
        for pat, m in self.models:
            if pat.search(model):
                return m
        return None

    def resolve(self, model: str, family_hint: str | None = None):
        """(model id used for pricing, assumed?) — an alias is used only when no model id is recorded."""
        model = (model or "").strip()
        if model:
            return model, False
        if family_hint in self.aliases:
            return self.aliases[family_hint], True
        return "", False

    def rates(self, model: str, fast: bool = False, long_prompt: bool = False):
        m = self.entry(model)
        if m is None:
            return None
        base = dict(m.get("long_prompt") or {}) if long_prompt and m.get("long_prompt") else {}
        r = {k: float(base.get(k, m[k])) for k in ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")}
        if fast and m.get("fast_multiplier"):
            r = {k: v * float(m["fast_multiplier"]) for k, v in r.items()}
        return r

    def call_usd(self, model: str, tokens: dict, fast: bool = False):
        """Dollars for one model call; tokens keyed by CATS (missing or None counts as 0)."""
        m = self.entry(model)
        if m is None:
            return None
        n = {k: int(tokens.get(k) or 0) for k in CATS}
        thr = m.get("long_prompt_threshold_tokens")
        prompt = n["fresh_input"] + n["cache_read"] + n["cache_write_5m"] + n["cache_write_1h"] + n["cache_write_unclassified"]
        r = self.rates(model, fast=fast, long_prompt=bool(thr and prompt > thr))
        return sum(n[k] * r[RATE_KEY[k]] for k in CATS) / 1e6

    def row_usd(self, row: dict, family_hint: str | None = None):
        """Dollars for an aggregated usage row. Returns (usd or None, flags).

        A precomputed ``usd_list`` column (written by sessions.py per call, with fast mode and long-prompt
        rates applied) is used as is. Otherwise the row total is priced at its model's standard rates.
        """
        flags = []
        pre = row.get("usd_list")
        if pre not in (None, ""):
            try:
                return float(pre), ["per_call"]
            except ValueError:
                raise PricingError(f"usd_list {pre!r} is not a number") from None
        model, assumed = self.resolve(row.get("model"), family_hint)
        if assumed:
            flags.append("assumed_model")
        m = self.entry(model)
        if m is None:
            return None, flags + ["unpriced_model"]
        if m.get("long_prompt_threshold_tokens"):
            flags.append("long_prompt_rates_not_applied")
        if m.get("fast_multiplier"):
            flags.append("fast_mode_not_visible")
        n = {k: int(float(row.get(k) or 0)) for k in CATS}
        r = self.rates(model)
        return sum(n[k] * r[RATE_KEY[k]] for k in CATS) / 1e6, flags
