#!/usr/bin/env python3
"""Hollerith: run one claim-kit model stage for one packet through a model runner.

Standard library only. Run with `python3 -I driver.py ...`.

What it does
  draft   the producer stage: fills decisions.csv / clauses.csv / RATIONALES.json for a prepared packet.
  review  one blind reviewer stage (also the stage for a planted control: the reviewer cannot tell).
  after-reveal  the review whose verdict is `upheld_after_reveal` (the coordinator supplies the reveal note).
  kit     deterministic claim-kit stages (prepare, dispatch-check, apply, batch-check, complete) passed through
          to jobs/claim-kit/kit.py unchanged, logged at zero cost so the cost log shows the whole flow.
  install copy a validated draft into its packet folder (the old blank sheets are kept beside them).
  cost    summarize the cost log.   schema  print a stage schema.

What it never does
  It decides no law, publishes nothing, writes no claim, status or human review, and never overwrites a file.
  Output schemas are derived from claim-kit's own validators (see the comments by each schema), not invented.

Spending: a per-run, per-UTC-day and campaign-total cap, all read from the JSONL cost log before any model call.
Billing basis is explicit (`--auth api-key` or `--auth subscription`): see BILLING.md, because an API key in the
environment silently overrides a subscription login and `--bare` cannot use a subscription token.

Exit codes: 0 ok; 1 stage failed after the one allowed retry; 2 bad arguments or inputs; 3 spending cap reached
(no model call made); 4 blinding refusal.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

LEGAL_CUTOFF = "2026-10-14"            # claim_gate.LEGAL_CUTOFF and PACKET['legal_cutoff']
MAX_RETRIES = 1                        # one retry: at most two model calls per stage run
KIT_STAGES = ("prepare", "dispatch-check", "apply", "batch-check", "complete", "view")
DEFAULT_COST_LOG = "research/hollerith-drivers/cost/COST_LOG.jsonl"
DEFAULT_RUN_CAP, DEFAULT_DAY_CAP, DEFAULT_TOTAL_CAP = 2.0, 10.0, 100.0
MAX_PROMPT_SOURCE_CHARS = 300_000
MAX_READ_CHARS = 900_000
DATE = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"


class CapReached(Exception):
    pass


class StageFailed(Exception):
    pass


class BlindingRefusal(Exception):
    pass


class InputError(Exception):
    pass


# --------------------------------------------------------------------------------------------- helpers

def canon(value):
    """Stage 19 canonical JSON (COMPLETION.md): sorted keys, UTF-8, no spaces, ensure_ascii False."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_text(text):
    return sha256_bytes(text.encode("utf-8"))


def now_utc():
    return datetime.now(timezone.utc)


def write_new(path, data):
    """Create a new file; refuse to overwrite."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        with open(path, "xb") as handle:
            handle.write(data)
    else:
        with open(path, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(data)


def dump_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


# ------------------------------------------------------------------------------------ schema validation
# A small subset of JSON Schema, enough for the schemas below (and what `claude --json-schema` accepts).

def _is(value, kind):
    if kind == "string":
        return isinstance(value, str)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "array":
        return isinstance(value, list)
    if kind == "object":
        return isinstance(value, dict)
    if kind == "null":
        return value is None
    raise ValueError("unsupported schema type " + str(kind))


def validate(value, schema, path="$"):
    """Return a list of error strings (empty when valid)."""
    errors = []
    kinds = schema.get("type")
    if kinds is not None:
        kinds = kinds if isinstance(kinds, list) else [kinds]
        if not any(_is(value, k) for k in kinds):
            return [path + ": expected " + "/".join(kinds) + ", got " + type(value).__name__]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(path + ": not one of " + canon(schema["enum"]))
    if "const" in schema and value != schema["const"]:
        errors.append(path + ": must equal " + canon(schema["const"]))
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(path + ": shorter than " + str(schema["minLength"]))
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(path + ": does not match " + schema["pattern"])
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(path + ": below " + str(schema["minimum"]))
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(path + ": above " + str(schema["maximum"]))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(path + ": fewer than " + str(schema["minItems"]) + " items")
        if "items" in schema:
            for i, item in enumerate(value):
                errors += validate(item, schema["items"], f"{path}[{i}]")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(path + ": missing " + key)
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(path + ": unknown field " + key)
        elif isinstance(schema.get("additionalProperties"), dict):
            for key, item in value.items():
                if key not in props:
                    errors += validate(item, schema["additionalProperties"], f"{path}.{key}")
        for key, sub in props.items():
            if key in value:
                errors += validate(value[key], sub, f"{path}.{key}")
    return errors


# ------------------------------------------------------------------------------------------ the schemas
# Field names come from batch.py ROW_FIELDS / CLAUSE_FIELDS (the CSV columns `kit.py apply` reads). The driver keeps
# instrument_id/dossier_sha256/agent from the blank sheet; the model supplies only judgment fields. Enumerations are
# the ones research/stage19/code/claim_gate.py and assemble.py branch on: clause state (operative, terminated,
# never_activated), savings state (none_after_bounded_search, continuing_independent, transferred_or_accrued),
# publication_kind (whole_case, partial_research), outcome (submit, unresolved, blocked, route_owner).
# JSON-valued CSV columns are native JSON here; the driver canon-encodes them into the cell.

_S = {"type": "string"}
_SN = {"type": ["string", "null"]}
_B = {"type": "boolean"}
_STRS = {"type": "array", "items": _S}

DECISION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["instrument_id", "outcome", "approved", "original_confirmed", "original_pages_confirmed",
                 "inventory_confirmed", "research_rationale", "savings_state", "savings_source_id", "savings_reason",
                 "search_ids", "conflict_resolutions", "unresolved_material_gaps", "earlier_end_check",
                 "scope_check", "independent_command_check", "savings_check", "publication_kind"],
    "properties": {
        "instrument_id": _S,
        "outcome": {"type": "string", "enum": ["submit", "unresolved", "blocked", "route_owner"]},
        "approved": _B, "original_confirmed": _B, "original_pages_confirmed": _B, "inventory_confirmed": _B,
        "research_rationale": _S,
        "savings_state": {"type": ["string", "null"],
                          "enum": ["none_after_bounded_search", "continuing_independent", "transferred_or_accrued", None]},
        "savings_source_id": _SN, "savings_reason": _S,
        "search_ids": _STRS,
        "conflict_resolutions": {"type": "object", "additionalProperties": _S},
        "unresolved_material_gaps": _STRS,
        "earlier_end_check": _S, "scope_check": _S, "independent_command_check": _S, "savings_check": _S,
        "working_text": {"type": ["object", "null"]},
        "source_notes": {"type": ["array", "null"], "items": {"type": "object"}},
        "publication_kind": {"type": "string", "enum": ["whole_case", "partial_research"]},
    },
}

CLAUSE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["instrument_id", "scope_id", "state", "end_id", "effective_date", "effective_date_confirmed",
                 "current_basis_id", "current_legal_basis", "checked_through", "later_event_ids", "later_events",
                 "reason"],
    "properties": {
        "instrument_id": _S, "scope_id": _S, "clause_id": _SN,
        "state": {"type": ["string", "null"], "enum": ["operative", "terminated", "never_activated", None]},
        "end_id": _SN,
        "effective_date": {"type": ["string", "null"]},
        "mechanism": _SN,
        "effective_date_confirmed": _B,
        "current_basis_id": _SN, "current_legal_basis": _S, "checked_through": _SN,
        "later_event_ids": _STRS,
        "later_events": {"type": "array", "items": {"type": "object"}},
        "reason": _S,
        "inventory_source_id": _SN,
        "inventory_char_start": {"type": ["integer", "null"], "minimum": 0},
        "inventory_char_end": {"type": ["integer", "null"], "minimum": 0},
        "inventory_reason": _SN,
    },
}

DRAFT_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["decisions", "clauses", "rationales"],
    "properties": {
        "decisions": {"type": "array", "minItems": 1, "items": DECISION_SCHEMA},
        "clauses": {"type": "array", "items": CLAUSE_SCHEMA},
        "rationales": {"type": "object", "additionalProperties": _S},
    },
}

# The reviewer's own judgment. The record fields completion.review_record() demands (reviewer, model_family,
# independent, separate_context, review_kind, scope, verdict, claim_sha256, instrument_id) are stamped by the driver,
# never chosen by the model. decision/locus/reason/confidence are the verdict-row fields mountweazel.py `score` reads
# (decision accept or reject for a claim card; confidence 0-1).
REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["decision", "locus", "reason", "confidence"],
    "properties": {
        "decision": {"type": "string", "enum": ["accept", "reject"]},
        "locus": {"type": "string", "minLength": 1},
        "reason": {"type": "string", "minLength": 40},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "expected_gate_errors": _STRS,
    },
}
SCHEMAS = {"draft": DRAFT_SCHEMA, "review": REVIEW_SCHEMA, "after-reveal": REVIEW_SCHEMA}


# ------------------------------------------------------------------------------------------- cost log

def read_log(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            raise InputError(f"cost log line {number} is not JSON; refusing to guess spend")
        if not isinstance(row, dict):
            raise InputError(f"cost log line {number} is not an object")
        rows.append(row)
    return rows


def counted(row):
    value = row.get("cost_counted_usd")
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def day_of(row):
    return str(row.get("ts", ""))[:10]


class CapPolicy:
    def __init__(self, run=DEFAULT_RUN_CAP, day=DEFAULT_DAY_CAP, total=DEFAULT_TOTAL_CAP):
        self.run, self.day, self.total = float(run), float(day), float(total)


def budget_left(rows, policy, run_spent, today):
    """Dollars this attempt may spend, or raise CapReached. Reads only the cost log."""
    day_spent = sum(counted(r) for r in rows if day_of(r) == today)
    total_spent = sum(counted(r) for r in rows)
    if day_spent >= policy.day:
        raise CapReached(f"daily cap reached: {day_spent:.4f} of {policy.day:.2f} USD counted on {today}")
    if total_spent >= policy.total:
        raise CapReached(f"campaign cap reached: {total_spent:.4f} of {policy.total:.2f} USD counted")
    if run_spent >= policy.run:
        raise CapReached(f"per-run cap reached: {run_spent:.4f} of {policy.run:.2f} USD")
    return round(min(policy.run - run_spent, policy.day - day_spent, policy.total - total_spent), 6)


def append_log(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


# ------------------------------------------------------------------------------------------- runners

class Request:
    def __init__(self, stage, role, prompt, system, schema, model, budget_usd, max_turns, timeout):
        self.stage, self.role, self.prompt, self.system, self.schema = stage, role, prompt, system, schema
        self.model, self.budget_usd, self.max_turns, self.timeout = model, budget_usd, max_turns, timeout


class Result:
    def __init__(self, output=None, tokens=None, cost_usd=None, wall_seconds=0.0, error=None):
        self.output, self.cost_usd, self.wall_seconds, self.error = output, cost_usd, wall_seconds, error
        self.tokens = tokens or {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}


class DryRunner:
    """Canned outputs for tests: each call pops the next item (a dict output, or a string beginning ERROR:)."""
    basis = "dry"

    def __init__(self, outputs, cost_usd=0.0, tokens=None):
        self.outputs, self.cost_usd, self.calls = list(outputs), cost_usd, []
        self.tokens = tokens or {"input": 10, "output": 5, "cache_creation": 0, "cache_read": 0}

    def run(self, request):
        self.calls.append(request)
        if not self.outputs:
            return Result(error="dry runner has no canned output left", cost_usd=self.cost_usd, tokens=self.tokens)
        item = self.outputs.pop(0)
        if isinstance(item, str) and item.startswith("ERROR:"):
            return Result(error=item[6:].strip() or "dry error", cost_usd=self.cost_usd, tokens=self.tokens)
        return Result(output=item, cost_usd=self.cost_usd, tokens=dict(self.tokens), wall_seconds=0.0)


def build_env(auth, base):
    """Environment for the claude child. Removes every credential that would override the chosen billing basis."""
    env = dict(base)
    for key in ("CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
                "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE", "ANTHROPIC_FEDERATION_RULE_ID"):
        env.pop(key, None)
    if auth == "api-key":
        if not env.get("ANTHROPIC_API_KEY"):
            raise InputError("--auth api-key needs ANTHROPIC_API_KEY in the environment")
        env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    elif auth == "subscription":
        if not env.get("CLAUDE_CODE_OAUTH_TOKEN"):
            raise InputError("--auth subscription needs CLAUDE_CODE_OAUTH_TOKEN (from `claude setup-token`)")
        env.pop("ANTHROPIC_API_KEY", None)   # otherwise -p silently bills the API key (BILLING.md F4)
    else:
        raise InputError("--auth must be api-key or subscription for the claude runner")
    env["DISABLE_AUTOUPDATER"] = "1"
    return env


def build_command(binary, auth, request):
    """claude -p command. --bare only with an API key (bare mode never reads a subscription token, BILLING.md F5)."""
    cmd = [binary]
    if auth == "api-key":
        cmd.append("--bare")
    cmd += ["-p", "--output-format", "json", "--json-schema", json.dumps(request.schema, sort_keys=True),
            "--model", request.model, "--max-budget-usd", f"{request.budget_usd:.4f}",
            "--max-turns", str(request.max_turns), "--no-session-persistence",
            "--tools", "", "--permission-mode", "dontAsk", "--system-prompt", request.system]
    if auth != "api-key":
        cmd += ["--strict-mcp-config", "--disable-slash-commands"]
    return cmd


def parse_claude_json(text):
    """Parse the json output of `claude -p`. Returns (output, tokens, cost, error)."""
    try:
        data = json.loads(text)
    except ValueError:
        return None, None, None, "claude output is not JSON"
    if isinstance(data, list):
        results = [d for d in data if isinstance(d, dict) and d.get("type") == "result"]
        data = results[-1] if results else {}
    if not isinstance(data, dict):
        return None, None, None, "claude output has no result object"
    cost = data.get("total_cost_usd")
    cost = float(cost) if isinstance(cost, (int, float)) and not isinstance(cost, bool) else None
    tokens = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}
    model_usage = data.get("modelUsage")
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    if isinstance(model_usage, dict) and model_usage:     # whole tree, subagents included (cost-tracking doc)
        for entry in model_usage.values():
            if isinstance(entry, dict):
                tokens["input"] += int(entry.get("inputTokens") or 0)
                tokens["output"] += int(entry.get("outputTokens") or 0)
                tokens["cache_creation"] += int(entry.get("cacheCreationInputTokens") or 0)
                tokens["cache_read"] += int(entry.get("cacheReadInputTokens") or 0)
    else:
        tokens = {"input": int(usage.get("input_tokens") or 0), "output": int(usage.get("output_tokens") or 0),
                  "cache_creation": int(usage.get("cache_creation_input_tokens") or 0),
                  "cache_read": int(usage.get("cache_read_input_tokens") or 0)}
    if data.get("is_error"):
        return None, tokens, cost, "claude reported an error: " + str(data.get("subtype") or data.get("result"))[:200]
    out = data.get("structured_output")
    if not isinstance(out, dict):
        raw = data.get("result")
        if isinstance(raw, str):
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
            try:
                out = json.loads(raw)
            except ValueError:
                out = None
    if not isinstance(out, dict):
        return None, tokens, cost, "no structured output in the claude result"
    return out, tokens, cost, None


class ClaudeRunner:
    def __init__(self, auth, binary="claude", environ=None, runner=subprocess.run):
        self.auth, self.binary, self.environ, self._run = auth, binary, environ if environ is not None else os.environ, runner
        self.basis = "metered_api" if auth == "api-key" else "subscription"

    def run(self, request):
        env = build_env(self.auth, self.environ)
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="hollerith-cwd-") as cwd, \
                tempfile.TemporaryDirectory(prefix="hollerith-cfg-") as cfg:
            env["CLAUDE_CONFIG_DIR"] = cfg       # no inherited settings, hooks, memory or CLAUDE.md
            try:
                proc = self._run(build_command(self.binary, self.auth, request), input=request.prompt.encode("utf-8"),
                                 capture_output=True, cwd=cwd, env=env, timeout=request.timeout)
            except (OSError, subprocess.TimeoutExpired) as exc:
                return Result(error=type(exc).__name__ + ": " + str(exc)[:200], wall_seconds=time.monotonic() - started)
        wall = round(time.monotonic() - started, 3)
        out, tokens, cost, error = parse_claude_json(proc.stdout.decode("utf-8", "replace"))
        if proc.returncode != 0 and not error:
            error = f"claude exited {proc.returncode}"
        return Result(output=out, tokens=tokens, cost_usd=cost, wall_seconds=wall, error=error)


# ------------------------------------------------------------------------------------- stage execution

def run_stage(*, stage, packet, role, prompt, system, schema, semantic, runner, model, policy, log_path,
              clock=now_utc, max_turns=4, timeout=1800, extra=None):
    """One stage for one packet: at most one retry, every attempt logged, caps read from the log first."""
    run_id = uuid.uuid4().hex[:12]
    run_spent, feedback, last_errors = 0.0, "", []
    for attempt in range(MAX_RETRIES + 1):
        rows = read_log(log_path)
        now = clock()
        try:
            budget = budget_left(rows, policy, run_spent, now.strftime("%Y-%m-%d"))
        except CapReached:
            if attempt == 0:
                raise
            break
        full_prompt = prompt + feedback
        request = Request(stage, role, full_prompt, system, schema, model, budget, max_turns, timeout)
        result = runner.run(request)
        errors = []
        outcome = "ok"
        if result.error:
            outcome, errors = "runner_error", [result.error]
        else:
            errors = validate(result.output, schema)
            if not errors:
                errors = semantic(result.output)
            if errors:
                outcome = "schema_invalid"
        reported = result.cost_usd
        assumed = reported is None
        cost = budget if assumed else reported        # unknown spend counts as the whole budget granted
        run_spent += cost
        row = {"ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "run_id": run_id, "stage": stage, "packet": packet,
               "role": role, "attempt": attempt + 1, "model": request.model,
               "auth_basis": runner.basis, "tokens": result.tokens, "total_cost_usd": reported,
               "cost_counted_usd": round(cost, 6), "cost_assumed": assumed,
               "wall_seconds": round(result.wall_seconds, 3), "outcome": outcome,
               "prompt_sha256": sha256_text(full_prompt), "errors": [e[:200] for e in errors[:3]]}
        if extra:
            row.update(extra)
        append_log(log_path, row)
        if outcome == "ok":
            return {"output": result.output, "run_id": run_id, "attempts": attempt + 1, "cost_counted_usd": round(run_spent, 6),
                    "tokens": result.tokens, "prompt_sha256": row["prompt_sha256"], "model": request.model}
        last_errors = errors
        feedback = ("\n\nYour previous reply was rejected for these format or consistency reasons (fix them and "
                    "reply with the corrected JSON object only):\n- " + "\n- ".join(e[:300] for e in errors[:12]))
    raise StageFailed("; ".join(last_errors)[:900] or "stage failed")


# ------------------------------------------------------------------------------- draft stage (producer)

DRAFT_SYSTEM = (
    "You are the producer in a source-first research workflow on the lifecycle of United States executive orders. "
    "Reply with exactly one JSON object that matches the schema you were given, and nothing else. Every field is a "
    "research judgment drawn only from the packet text in the user message. Never invent an evidence or source id: "
    "use ids that appear in the packet. If the packet does not support a confident conclusion, choose outcome "
    "'unresolved' or 'blocked' and list what is missing in unresolved_material_gaps. A report deadline is never an end. "
    "A citation or a 1989 snapshot cannot establish current operative status. Your output is a hypothesis for "
    "independent review, never a certification."
)

DRAFT_TASK = """Complete the decision sheet for the claim-kit packet below.

Rules (from jobs/claim-kit AGENT_PROTOCOL.md, BATCH.md and the claim gate):
- decisions: exactly one object per packet member (skeleton lists them). outcome is submit, unresolved, blocked or route_owner.
  A submitted member needs substantive earlier_end_check, scope_check, independent_command_check and savings_check, a
  research_rationale, and publication_kind whole_case or partial_research. A check may be '@rationale:KEY' only if KEY is
  defined in rationales.
- clauses: for each submitted member, one object per clause in the skeleton (same scope_id; omit clause_id unless the
  inventory is corrected, in which case give inventory_source_id, inventory_char_start, inventory_char_end and
  inventory_reason for every replacement clause). state is operative, terminated or never_activated.
  terminated or never_activated needs end_id (an evidence id from the packet), effective_date (YYYY-MM-DD) and
  effective_date_confirmed true. operative needs current_basis_id, current_legal_basis and checked_through {cutoff}.
  Give every clause a reason. For a member that is not submitted you may omit its clause objects.
- savings_state is none_after_bounded_search, continuing_independent, transferred_or_accrued (or null when not submitted).
- Set approved true only for a member you submit after reading its sources; it is producer approval, not independent review.
- Overflow pointers in the packet that were not loaded are not evidence: block rather than guess.

SKELETON (members and clauses, with blank judgment fields):
{skeleton}

PACKET (READ.md, the frozen dossier text):
{read}
"""


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, fields, rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    write_new(path, buffer.getvalue())


def load_packet_inputs(folder):
    folder = Path(folder)
    for name in ("PACKET.json", "READ.md", "decisions.csv", "clauses.csv"):
        if not (folder / name).is_file():
            raise InputError("packet folder lacks " + name)
    packet = json.loads((folder / "PACKET.json").read_bytes())
    decisions, clauses = read_csv(folder / "decisions.csv"), read_csv(folder / "clauses.csv")
    read = (folder / "READ.md").read_text(encoding="utf-8")
    if len(read) > MAX_READ_CHARS:
        raise InputError("READ.md is too large for a no-tool draft; prepare a smaller packet")
    fields = (list(decisions[0].keys()) if decisions else [], list(clauses[0].keys()) if clauses else [])
    return packet, decisions, clauses, read, fields


def draft_skeleton(decisions, clauses):
    return {"decisions": [{"instrument_id": r["instrument_id"],
                           "blank_unresolved_material_gaps": json.loads(r.get("unresolved_material_gaps") or "[]")}
                          for r in decisions],
            "clauses": [{"instrument_id": c["instrument_id"], "scope_id": c["scope_id"], "clause_id": c["clause_id"]}
                        for c in clauses]}


def draft_prompt(packet, decisions, clauses, read):
    return DRAFT_TASK.format(cutoff=packet.get("legal_cutoff", LEGAL_CUTOFF),
                             skeleton=json.dumps(draft_skeleton(decisions, clauses), ensure_ascii=False, indent=1), read=read)


def draft_semantic(decisions, clauses):
    """Mirror the checks batch.apply and assemble make, so a bad draft is caught before it costs a review."""
    blank_ids = [r["instrument_id"] for r in decisions]
    blank_scopes = {}
    for c in clauses:
        blank_scopes.setdefault(c["instrument_id"], []).append(c["scope_id"])

    def check(out):
        errors = []
        ids = [d["instrument_id"] for d in out["decisions"]]
        if sorted(ids) != sorted(blank_ids):
            errors.append("decisions must name every packet member exactly once: expected " + canon(sorted(blank_ids)))
            return errors
        keys = out["rationales"]
        by_clause = {}
        for c in out["clauses"]:
            by_clause.setdefault(c["instrument_id"], []).append(c)
        for c in out["clauses"]:
            if c["instrument_id"] not in blank_ids:
                errors.append("clause row outside packet: " + c["instrument_id"])

        def ref_ok(text):
            if isinstance(text, str) and text.startswith("@rationale:"):
                key = text.split(":", 1)[1]
                return key in keys and bool(keys[key].strip())
            return True
        for d in out["decisions"]:
            iid = d["instrument_id"]
            for field in ("research_rationale", "earlier_end_check", "scope_check", "independent_command_check",
                          "savings_check", "savings_reason"):
                if not ref_ok(d[field]):
                    errors.append(f"{iid}: {field} cites an undefined @rationale key")
            if d["outcome"] != "submit":
                continue
            for field in ("earlier_end_check", "scope_check", "independent_command_check", "savings_check", "research_rationale"):
                if not d[field].strip():
                    errors.append(f"{iid}: submitted member needs substantive {field}")
            if d["savings_state"] is None:
                errors.append(f"{iid}: submitted member needs savings_state")
            rows = by_clause.get(iid, [])
            if not rows:
                errors.append(f"{iid}: submitted member needs clause rows")
                continue
            corrected = [r for r in rows if r.get("inventory_source_id")]
            if corrected:
                for r in rows:
                    if not (r.get("inventory_source_id") and r.get("inventory_char_start") is not None
                            and r.get("inventory_char_end") is not None and (r.get("inventory_reason") or "").strip()):
                        errors.append(f"{iid}/{r['scope_id']}: a corrected inventory needs all four inventory_* fields on every clause")
            elif sorted(r["scope_id"] for r in rows) != sorted(blank_scopes.get(iid, [])):
                errors.append(f"{iid}: clause scope ids must equal the packet inventory " + canon(sorted(blank_scopes.get(iid, []))))
            for r in rows:
                where = f"{iid}/{r['scope_id']}"
                if not r["reason"].strip() or not ref_ok(r["reason"]):
                    errors.append(f"{where}: reason required")
                if r["state"] is None:
                    errors.append(f"{where}: state required")
                elif r["state"] in ("terminated", "never_activated"):
                    if not r["end_id"]:
                        errors.append(f"{where}: end_id required")
                    if not (r["effective_date"] and re.match(DATE, r["effective_date"])):
                        errors.append(f"{where}: effective_date must be YYYY-MM-DD")
                    if r["effective_date_confirmed"] is not True:
                        errors.append(f"{where}: effective_date_confirmed must be true")
                else:
                    if not r["current_basis_id"] or not r["current_legal_basis"].strip():
                        errors.append(f"{where}: operative needs current_basis_id and current_legal_basis")
                    if r["checked_through"] != LEGAL_CUTOFF:
                        errors.append(f"{where}: checked_through must be {LEGAL_CUTOFF}")
        return errors
    return check


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return canon(value)
    return str(value)


def draft_to_csv(out, decisions, clauses, fields):
    """Merge the model's judgment into the blank sheets, keeping identity columns from the packet."""
    blank = {r["instrument_id"]: r for r in decisions}
    rows = []
    for d in out["decisions"]:
        row = dict(blank[d["instrument_id"]])
        for key, value in d.items():
            if key == "instrument_id":
                continue
            if key in ("working_text", "source_notes") and value is None:
                continue
            row[key] = _cell(value)
        rows.append(row)
    given = {}
    for c in out["clauses"]:
        given.setdefault(c["instrument_id"], []).append(c)
    clause_rows = []
    for iid in blank:
        if iid in given:
            for c in given[iid]:
                row = {k: "" for k in fields[1]}
                for key, value in c.items():
                    if key in row:
                        row[key] = _cell(value)
                clause_rows.append(row)
        else:
            clause_rows += [c for c in clauses if c["instrument_id"] == iid]
    return rows, clause_rows


def do_draft(args, runner, policy, clock=now_utc):
    folder = Path(args.packet)
    packet, decisions, clauses, read, fields = load_packet_inputs(folder)
    out_dir = Path(args.out)
    if out_dir.exists():
        raise InputError("--out exists; refusing to overwrite")
    if not args.no_dispatch_check:
        code = run_kit(args, "dispatch-check", [str(folder)], log=False)
        if code != 0:
            raise InputError("dispatch-check did not exit 0; do not launch a producer on this packet")
    label = args.packet_label or (folder.name + ":" + str(packet.get("fingerprint", ""))[:12])
    prompt = draft_prompt(packet, decisions, clauses, read)
    res = run_stage(stage="draft", packet=label, role="producer", prompt=prompt, system=DRAFT_SYSTEM, schema=DRAFT_SCHEMA,
                    semantic=draft_semantic(decisions, clauses), runner=runner, model=args.model, policy=policy,
                    log_path=args.cost_log, clock=clock, max_turns=4, timeout=args.timeout)
    rows, clause_rows = draft_to_csv(res["output"], decisions, clauses, fields)
    write_csv(out_dir / "decisions.csv", fields[0], rows)
    write_csv(out_dir / "clauses.csv", fields[1], clause_rows)
    write_new(out_dir / "RATIONALES.json", dump_json(res["output"]["rationales"]))
    write_new(out_dir / "DRAFT_RECEIPT.json", dump_json({
        "schema": "hollerith-draft-receipt/v1", "packet": label, "packet_fingerprint": packet.get("fingerprint"),
        "model": res["model"], "auth_basis": runner.basis, "attempts": res["attempts"], "run_id": res["run_id"],
        "cost_counted_usd": res["cost_counted_usd"], "tokens": res["tokens"], "prompt_sha256": res["prompt_sha256"],
        "note": "AI producer draft; a hypothesis for independent review. Not a certification."}))
    return res


def do_install(draft_dir, packet_dir):
    draft_dir, packet_dir = Path(draft_dir), Path(packet_dir)
    for name in ("decisions.csv", "clauses.csv", "RATIONALES.json", "DRAFT_RECEIPT.json"):
        if not (draft_dir / name).is_file():
            raise InputError("draft folder lacks " + name)
    receipt = json.loads((draft_dir / "DRAFT_RECEIPT.json").read_bytes())
    packet = json.loads((packet_dir / "PACKET.json").read_bytes())
    if receipt.get("packet_fingerprint") != packet.get("fingerprint"):
        raise InputError("draft was made for a different packet fingerprint")
    for name in ("decisions.csv", "clauses.csv", "RATIONALES.json"):
        backup = packet_dir / (name + ".blank")
        if backup.exists():
            raise InputError("a draft is already installed here (" + backup.name + " exists)")
    for name in ("decisions.csv", "clauses.csv", "RATIONALES.json"):
        shutil.move(str(packet_dir / name), str(packet_dir / (name + ".blank")))
        shutil.copyfile(str(draft_dir / name), str(packet_dir / name))


# ----------------------------------------------------------------------- review stage (blind or reveal)

REVIEW_SYSTEM = (
    "You are an independent source reviewer of one proposed lifecycle claim about a United States executive order. "
    "You know nothing about how the claim was produced. Judge only from the claim card and the source texts in the "
    "user message. Reply with exactly one JSON object matching the schema, and nothing else."
)

REVIEW_TASK = """Review the claim card below against the source texts supplied after it.

Do this before you decide:
- Check that each quoted span is exactly in its source at the stated character offsets (offsets are Unicode code-point
  positions in the text file; CRLF counts as two characters) and that the quote supports what the claim says it supports.
- Test whether an earlier ending, an amendment, a partial revocation, a savings clause or an independent command
  would change the claim. A report deadline is never an end. A citation or a 1989 snapshot does not prove current status.
- Check that the claim's inventory of operative clauses is complete for the source supplied.
Answer decision accept only if you found nothing that undermines the claim; otherwise reject, and put the exact field
or quote span you rely on in locus and the substantive reason in reason (at least one full sentence).
confidence is your probability (0 to 1) that your decision is right.{scope_rule}

CLAIM CARD:
{card}

SOURCE TEXTS (only these are available; raw files are not supplied):
{sources}
"""

SCOPE_RULES = {
    "whole_case": "",
    "partial_research": ("\nThis claim is filed as partial research: if you accept it, expected_gate_errors must list, "
                         "as exact strings, every Stage 19 completeness error that this partial claim still carries "
                         "(a nonempty list)."),
}

BLIND_MARKERS = re.compile(r"SEEDED|KEY\.sealed|genuine_claim_sha256|seeded_by|leak_needle|eo-claim-kit-control-seed|"
                           r"planted_claim_sha256|MW-[CS][0-9]|control_adjudication|CONTROL_ADJUDICATION")
FORBIDDEN_KEYS = {"verdict", "adjudication", "after_reveal_review", "reviewer", "seed", "planted", "genuine_claim_sha256"}
FORBIDDEN_PATH_PARTS = re.compile(r"(^keys?$|sealed|adjudicat|genuine|control[-_]?seed|seed[-_]?receipt|mutation)", re.I)


def load_card(path, line=None):
    path = Path(path)
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    if path.suffix == ".jsonl":
        lines = [ln for ln in text.splitlines() if ln.strip()]
        if line is None:
            if len(lines) != 1:
                raise InputError("a .jsonl card file with several lines needs --line N (one card per review run)")
            line = 1
        if not 1 <= line <= len(lines):
            raise InputError("--line out of range")
        obj = json.loads(lines[line - 1])
    else:
        obj = json.loads(text)
    if not isinstance(obj, dict):
        raise InputError("a card must be one JSON object")
    claim = obj["claim"] if isinstance(obj.get("claim"), dict) and "item_id" in obj else obj
    iid = claim.get("instrument_id")
    if not isinstance(iid, str) or not iid:
        raise InputError("card has no claim.instrument_id")
    return obj, claim, obj.get("item_id") if "item_id" in obj else iid, sha256_bytes(raw)


def _walk(value, visit, path=""):
    if isinstance(value, dict):
        visit(value, path)
        for k, v in value.items():
            _walk(v, visit, path + "/" + str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _walk(v, visit, path + f"[{i}]")


def collect_sources(card, source_root, allow_roots, max_chars=MAX_PROMPT_SOURCE_CHARS):
    """Text files the card cites by `text_path`, read only inside explicit allow roots and hash-checked."""
    root = Path(source_root).resolve()
    allowed = []
    for rel in allow_roots:
        target = (root / rel).resolve()
        if not target.is_relative_to(root):
            raise InputError("allow-source-root escapes the source root: " + str(rel))
        allowed.append(target)
    if not allowed:
        raise InputError("at least one --allow-source-root is required")
    found = {}

    def visit(node, path):
        tp = node.get("text_path")
        if isinstance(tp, str):
            found.setdefault(tp, node.get("text_sha256"))
    _walk(card, visit)
    sources, total = [], 0
    for tp, declared in found.items():
        if Path(tp).is_absolute() or re.match(r"^[A-Za-z]:", tp) or ".." in Path(tp).parts:
            raise InputError("unsafe source path: " + tp)
        full = (root / tp).resolve()
        if not any(full.is_relative_to(a) for a in allowed) or not full.is_file() or full.is_symlink():
            raise InputError("source path is not a regular file inside an allowed root: " + tp)
        data = full.read_bytes()
        digest = sha256_bytes(data)
        if declared is not None and declared != digest:
            raise InputError("source hash differs from the card's text_sha256: " + tp)
        text = data.decode("utf-8")
        total += len(text)
        if total > max_chars:
            raise InputError("sources exceed the prompt cap; refusing to truncate silently")
        sources.append({"path": tp, "sha256": digest, "hash_declared": declared is not None, "text": text})
    return sources


def blinding_errors(card_path, card, prompt, source_root, allow_roots):
    errors = []
    for part in list(Path(card_path).parts) + [str(Path(source_root)).replace("\\", "/")] + list(allow_roots):
        for piece in re.split(r"[\\/]", str(part)):
            if FORBIDDEN_PATH_PARTS.search(piece):
                errors.append("path component looks like a key, seed or adjudication location: " + piece)
    found = set()

    def visit(node, path):
        for key in node:
            if str(key).lower() in FORBIDDEN_KEYS:
                found.add(str(key))
    _walk(card, visit)
    if found:
        errors.append("card carries review/control fields: " + ", ".join(sorted(found)))
    marker = BLIND_MARKERS.search(prompt)
    if marker:
        errors.append("prompt contains a seeding or control marker: " + marker.group(0))
    return errors


def review_prompt(card, sources, scope):
    blocks = []
    for s in sources:
        note = "" if s["hash_declared"] else " (card declared no text hash; unverified)"
        blocks.append(f"=== {s['path']} (sha256 {s['sha256']}){note} ===\n{s['text']}\n=== end {s['path']} ===")
    return REVIEW_TASK.format(scope_rule=SCOPE_RULES[scope], card=json.dumps(card, ensure_ascii=False, indent=1, sort_keys=True),
                              sources="\n\n".join(blocks) if blocks else "(the card cites no text files)")


def review_semantic(scope):
    def check(out):
        errors = []
        gaps = out.get("expected_gate_errors")
        if scope == "partial_research" and out["decision"] == "accept" and not gaps:
            errors.append("a partial_research acceptance needs a nonempty expected_gate_errors list")
        if scope == "whole_case" and gaps:
            errors.append("expected_gate_errors must be empty for a whole_case review")
        return errors
    return check


def do_review(args, runner, policy, clock=now_utc, after_reveal=False):
    if args.scope not in SCOPE_RULES:
        raise InputError("--scope must be whole_case or partial_research (copy the manifest's publication_kind)")
    if Path(args.out).exists():
        raise InputError("--out exists; refusing to overwrite")
    card, claim, item_id, card_file_sha = load_card(args.card, args.line)
    sources = collect_sources(card, args.source_root, args.allow_source_root or [])
    prompt = review_prompt(card, sources, args.scope)
    if after_reveal:
        if not args.reveal_note:
            raise InputError("--reveal-note FILE is required for an after-reveal review")
        prompt += "\n\nREVEAL NOTE FROM THE COORDINATOR (read after your first review):\n" + Path(args.reveal_note).read_text(encoding="utf-8")
    else:
        problems = blinding_errors(args.card, card, prompt, args.source_root, args.allow_source_root or [])
        if problems:
            raise BlindingRefusal("; ".join(problems))
    label = args.packet_label or claim["instrument_id"]
    stage = "after-reveal" if after_reveal else "review"
    res = run_stage(stage=stage, packet=label, role=args.reviewer, prompt=prompt, system=REVIEW_SYSTEM, schema=REVIEW_SCHEMA,
                    semantic=review_semantic(args.scope), runner=runner, model=args.model, policy=policy,
                    log_path=args.cost_log, clock=clock, max_turns=4, timeout=args.timeout)
    out = res["output"]
    verdict = {"accept": "upheld_after_reveal" if after_reveal else "upheld", "reject": "rejected"}[out["decision"]]
    record = {"item_id": item_id, "instrument_id": claim["instrument_id"], "claim_sha256": sha256_text(canon(claim)),
              "reviewer": args.reviewer, "model_family": args.model_family, "independent": True, "separate_context": True,
              "review_kind": "independent_ai_source_review", "scope": args.scope, "verdict": verdict,
              "decision": out["decision"], "locus": out["locus"], "reason": out["reason"], "confidence": out["confidence"]}
    if out.get("expected_gate_errors"):
        record["expected_gate_errors"] = out["expected_gate_errors"]
    write_new(args.out, dump_json(record))
    write_new(str(args.out) + ".receipt.json", dump_json({
        "schema": "hollerith-review-receipt/v1", "stage": stage, "packet": label, "model": res["model"],
        "auth_basis": runner.basis, "attempts": res["attempts"], "run_id": res["run_id"], "cost_counted_usd": res["cost_counted_usd"],
        "tokens": res["tokens"], "prompt_sha256": res["prompt_sha256"], "card_file_sha256": card_file_sha,
        "sources": [{"path": s["path"], "sha256": s["sha256"]} for s in sources],
        "isolation": "fresh process, empty working directory, empty config directory, no tools, no session persistence"}))
    return res


# ------------------------------------------------------------------------------------------ kit stages

def kit_command(args, stage, rest):
    repo = Path(args.repo).resolve()
    kit = Path(args.kit) if args.kit else repo / "jobs/claim-kit/kit.py"
    return [sys.executable, "-I", str(kit), "--repo", str(repo), stage] + list(rest)


def run_kit(args, stage, rest, log=True, clock=now_utc, runner=subprocess.run):
    if stage not in KIT_STAGES:
        raise InputError("unknown kit stage " + stage)
    started = time.monotonic()
    proc = runner(kit_command(args, stage, rest), cwd=str(Path(args.repo).resolve()))
    code = proc.returncode
    if log:
        append_log(args.cost_log, {"ts": clock().strftime("%Y-%m-%dT%H:%M:%SZ"), "stage": stage,
                                   "packet": args.packet_label or (rest[0] if rest else ""), "role": "deterministic",
                                   "model": None, "auth_basis": "none",
                                   "tokens": {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0},
                                   "total_cost_usd": 0.0, "cost_counted_usd": 0.0, "cost_assumed": False,
                                   "wall_seconds": round(time.monotonic() - started, 3),
                                   "outcome": "ok" if code == 0 else "failed", "exit_code": code})
    return code


# ------------------------------------------------------------------------------------------------- CLI

def summarize(rows, today):
    by_stage = {}
    for r in rows:
        s = by_stage.setdefault(r.get("stage"), {"calls": 0, "usd": 0.0, "wall_seconds": 0.0, "input": 0, "output": 0,
                                                 "cache_creation": 0, "cache_read": 0})
        s["calls"] += 1
        s["usd"] = round(s["usd"] + counted(r), 6)
        s["wall_seconds"] = round(s["wall_seconds"] + float(r.get("wall_seconds") or 0), 3)
        for k in ("input", "output", "cache_creation", "cache_read"):
            s[k] += int((r.get("tokens") or {}).get(k) or 0)
    return {"rows": len(rows), "total_counted_usd": round(sum(counted(r) for r in rows), 6),
            "today_counted_usd": round(sum(counted(r) for r in rows if day_of(r) == today), 6),
            "assumed_cost_rows": sum(1 for r in rows if r.get("cost_assumed")), "by_stage": by_stage}


def common(p):
    p.add_argument("--repo", default=".")
    p.add_argument("--kit", default=None, help="path to kit.py (default <repo>/jobs/claim-kit/kit.py)")
    p.add_argument("--runner", choices=("claude", "dry"), default="claude")
    p.add_argument("--auth", choices=("api-key", "subscription"), default=None,
                   help="billing basis for the claude runner (explicit on purpose; see BILLING.md)")
    p.add_argument("--model", default="claude-sonnet-5-5")
    p.add_argument("--model-family", default="Anthropic")
    p.add_argument("--claude-bin", default="claude")
    p.add_argument("--dry-canned", default=None, help="JSON list of canned outputs for the dry runner")
    p.add_argument("--cost-log", default=None)
    p.add_argument("--max-run-usd", type=float, default=DEFAULT_RUN_CAP)
    p.add_argument("--max-day-usd", type=float, default=DEFAULT_DAY_CAP)
    p.add_argument("--max-total-usd", type=float, default=DEFAULT_TOTAL_CAP)
    p.add_argument("--timeout", type=int, default=1800)
    p.add_argument("--packet-label", default=None)


def make_runner(args):
    if args.runner == "dry":
        canned = json.loads(Path(args.dry_canned).read_text(encoding="utf-8")) if args.dry_canned else []
        return DryRunner(canned)
    if args.auth is None:
        raise InputError("--auth api-key or --auth subscription is required with the claude runner")
    build_env(args.auth, os.environ)           # fail early on a missing credential
    return ClaudeRunner(args.auth, args.claude_bin)


def main(argv=None, runner=None, clock=now_utc):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("draft")
    common(s)
    s.add_argument("packet")
    s.add_argument("--out", required=True)
    s.add_argument("--no-dispatch-check", action="store_true", help="dry runner only")
    for name in ("review", "after-reveal"):
        s = sub.add_parser(name)
        common(s)
        s.add_argument("--card", required=True)
        s.add_argument("--line", type=int, default=None)
        s.add_argument("--source-root", required=True)
        s.add_argument("--allow-source-root", action="append")
        s.add_argument("--reviewer", required=True)
        s.add_argument("--scope", required=True)
        s.add_argument("--out", required=True)
        s.add_argument("--reveal-note", default=None)
    s = sub.add_parser("kit")
    common(s)
    s.add_argument("stage")
    s.add_argument("rest", nargs=argparse.REMAINDER)
    s = sub.add_parser("install")
    s.add_argument("draft")
    s.add_argument("packet")
    s = sub.add_parser("cost")
    common(s)
    s = sub.add_parser("schema")
    s.add_argument("stage", choices=sorted(SCHEMAS))
    args = parser.parse_args(argv)
    try:
        if args.cmd == "schema":
            print(json.dumps(SCHEMAS[args.stage], indent=1, sort_keys=True))
            return 0
        if args.cmd == "install":
            do_install(args.draft, args.packet)
            return 0
        repo = Path(args.repo)
        args.cost_log = args.cost_log or str(repo / DEFAULT_COST_LOG)
        if args.cmd == "cost":
            print(json.dumps(summarize(read_log(args.cost_log), clock().strftime("%Y-%m-%d")), indent=1, sort_keys=True))
            return 0
        if args.cmd == "kit":
            return run_kit(args, args.stage, [a for a in args.rest if a != "--"], clock=clock)
        policy = CapPolicy(args.max_run_usd, args.max_day_usd, args.max_total_usd)
        if args.cmd == "draft" and args.no_dispatch_check and args.runner != "dry":
            raise InputError("--no-dispatch-check is for the dry runner only")
        runner = runner or make_runner(args)
        if args.cmd == "draft":
            res = do_draft(args, runner, policy, clock)
        else:
            res = do_review(args, runner, policy, clock, after_reveal=(args.cmd == "after-reveal"))
        print(json.dumps({"ok": True, "attempts": res["attempts"], "cost_counted_usd": res["cost_counted_usd"],
                          "out": args.out}, sort_keys=True))
        return 0
    except CapReached as exc:
        print("REFUSED (cap): " + str(exc), file=sys.stderr)
        return 3
    except BlindingRefusal as exc:
        print("REFUSED (blinding): " + str(exc), file=sys.stderr)
        return 4
    except StageFailed as exc:
        print("FAILED: " + str(exc), file=sys.stderr)
        return 1
    except (InputError, OSError, ValueError, KeyError) as exc:
        print("ERROR: " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
