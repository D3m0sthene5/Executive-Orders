#!/usr/bin/env python3
"""Kean: one shared register of owner decisions, open owner questions and experiment results.

Named for Thomas Kean, chair of the 9/11 Commission. The Commission found that the agencies held the
pieces (the FBI's Phoenix memo of July 2001 among them) but never put them together, and it asked
that sharing become the default ("need to share" in place of "need to know"). This project failed
the same way: an owner ruling sat unused while a tool still said the decision was pending; questions
for the owner stayed in one agent's notes; results stayed in one chat. Kean gives those three kinds
of information one home that every agent reads first and writes before stopping.

Files (append-only JSON lines; the latest `rev` of an id is current):
  jobs/kean/register/decisions.jsonl  owner decisions, whether tools implement them, and old wording
                                      that contradicts them
  jobs/kean/register/asks.jsonl       questions waiting for the owner, and their answers
  jobs/kean/register/findings.jsonl   what was tried, what was expected, what happened, the lesson
  jobs/kean/register/legacy_reports.txt   reports written before Kean that no finding summarizes yet
  HANDOFF/KEAN.md                     the brief, generated from the register; agents read it first

Commands (run from the repo root, `python3 -I jobs/kean/kean.py <command>`):
  search TERM...        find earlier work on a subject before starting new work
  brief                 regenerate HANDOFF/KEAN.md, HANDOFF/KEAN_ASKS.md and HANDOFF/NEWEST.md
  newest                print the newest entry (first "## " block) of each HANDOFF/notes-*.md
  check [--strict]      validate the register and the coverage rules; --strict exits 1 on errors
  add-ask / answer      record a question for the owner / record the owner's answer
  add-decision / wire   record an owner decision / record which files implement it
  add-finding           record an experiment's result

Standard library only. Nothing here changes a claim, status, count, codebook or census.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

REGISTER = "jobs/kean/register"
BRIEF = "HANDOFF/KEAN.md"
ASKS_PAGE = "HANDOFF/KEAN_ASKS.md"   # full text of the open asks (owner ruling R6, 2026-11-06)
NEWEST_PAGE = "HANDOFF/NEWEST.md"   # the newest entry of every HANDOFF/notes-*.md (Justinian B1)
NEWEST_ENTRY_MAX_BYTES = 3500       # keeps NEWEST.md well under 50 KB; longer entries point at their file
FILES = {"decisions": "decisions.jsonl", "asks": "asks.jsonl", "findings": "findings.jsonl"}
LEGACY = "legacy_reports.txt"
# Agent notes entries dated on or after this day must cite a Kean ask id when they ask the owner something.
KEAN_START = "2026-10-28"
# The brief is read at the start of every session, so it stays small: the newest findings only, the rest by search.
BRIEF_FINDINGS = 6
BRIEF_MAX_BYTES = 16384  # owner ruling R6 (D-20261106-justinian-r6), was 8192
DRIFT_BEGIN, DRIFT_END = "<!-- kean:drift -->", "<!-- /kean:drift -->"
RULINGS_DIR = "research/readiness/owner_rulings/"
REPORT_RE = re.compile(r"^research/(excavator|production)/[^/]+/REPORT\.md$")
ASK_ID_RE = re.compile(r"\bA-\d{8}-(?:\d+|[a-z][a-z0-9]*(?:-[a-z0-9]+)*)\b")  # numbered or session-named (A-20261106-mabillon-register)
ENTRY_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})")
NO_ASK_RE = re.compile(r"@owner\W{0,3}(none|no ask|nothing|n/a)\b", re.I)

WIRING = ("wired", "partly_wired", "not_wired", "not_verified", "no_wiring_needed")
ASK_STATUS = ("open", "answered", "withdrawn")
VERDICTS = ("worked", "partly_worked", "failed", "stopped_at_gate", "inconclusive", "no_record", "analysis")
REQUIRED = {
    "decisions": ("id", "date", "title", "ruling", "sources", "wiring"),
    "asks": ("id", "date", "asked_by", "question", "why", "status"),
    "findings": ("id", "date", "by", "tried", "expected", "result", "verdict", "lesson", "sources"),
}
# Gutenberg (2026-11-09): optional structured numbers on a finding, so Bentham and Junto read wave costs and yields
# instead of hand-typed prose. Every field is optional except wave; unknown keys are errors.
MEASURE_KEYS = {"wave", "usd", "orders", "controls", "note"}
USD_KEYS = {"total", "by_role", "by_model", "basis"}
USD_BASES = ("list_price", "reported_cost", "mixed")
ORDER_KEYS = ("attempted", "submitted", "filed")
CONTROL_KEYS = ("planted", "missed")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,80}$")


def _amount(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and 0 <= v < 1e7


def validate_measures(m):
    """Errors in a finding's measures object (empty list when valid or absent)."""
    if m is None:
        return []
    if not isinstance(m, dict):
        return ["measures must be an object"]
    e = [f"measures: unknown key {k}" for k in sorted(set(m) - MEASURE_KEYS)]
    if not isinstance(m.get("wave"), str) or not SLUG_RE.match(m["wave"]):
        e.append("measures.wave must be a lower-case slug such as cujas-2026-11-08")
    u = m.get("usd")
    if u is not None:
        if not isinstance(u, dict):
            e.append("measures.usd must be an object")
        else:
            e += [f"measures.usd: unknown key {k}" for k in sorted(set(u) - USD_KEYS)]
            if u.get("basis") not in USD_BASES:
                e.append(f"measures.usd.basis must be one of {', '.join(USD_BASES)}")
            if "total" in u and not _amount(u["total"]):
                e.append("measures.usd.total must be a nonnegative number")
            for part in ("by_role", "by_model"):
                d = u.get(part)
                if d is None:
                    continue
                if not isinstance(d, dict) or not d or not all(isinstance(k, str) and k and _amount(v) for k, v in d.items()):
                    e.append(f"measures.usd.{part} must map names to nonnegative numbers")
                elif _amount(u.get("total")) and abs(sum(d.values()) - u["total"]) > max(0.01, 0.01 * u["total"]):
                    e.append(f"measures.usd.{part} sums to {sum(d.values()):.2f}, not total {u['total']:.2f}")
            if not any(k in u for k in ("total", "by_role", "by_model")):
                e.append("measures.usd needs total, by_role or by_model")
    for key, names in (("orders", ORDER_KEYS), ("controls", CONTROL_KEYS)):
        d = m.get(key)
        if d is None:
            continue
        if not isinstance(d, dict) or set(d) - set(names) or not d:
            e.append(f"measures.{key} may hold only {', '.join(names)}")
            continue
        if not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in d.values()):
            e.append(f"measures.{key} values must be nonnegative integers")
            continue
        chain = [d[k] for k in names if k in d]
        if chain != sorted(chain, reverse=True):
            e.append(f"measures.{key} must satisfy {' >= '.join(names)}")
    if "note" in m and not isinstance(m["note"], str):
        e.append("measures.note must be text")
    return e


def wave_measures(rows):
    """{wave: measures} from the current revision of every finding that carries them (newest finding wins)."""
    out = {}
    for f in sorted(current(rows), key=lambda r: (r.get("date", ""), r.get("id", ""))):
        m = f.get("measures")
        if isinstance(m, dict) and not validate_measures(m):
            out[m["wave"]] = dict(m, finding=f["id"])
    return out


SEARCH_GLOBS = (":(glob)HANDOFF/*.md", ":(glob)research/**/*.md", ":(glob)jobs/*/README.md", ":(glob)jobs/*/README.txt",
                "AGENTS.md", "CLAUDE.md", "README.md", "PROGRESS.md", ":(glob)jobs/kean/register/*.jsonl")


# ---------------------------------------------------------------- repository access

class Repo:
    """Reads the working tree, falling back to git's index so sparse checkouts still validate."""

    def __init__(self, root="."):
        self.root = os.path.abspath(root)
        self._tracked = None

    def path(self, rel):
        return os.path.join(self.root, rel.replace("/", os.sep))

    def git(self, *args):
        try:
            return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            return ""

    def tracked(self):
        if self._tracked is None:
            self._tracked = set(self.git("ls-files", "-z").split("\0")) - {""}
        return self._tracked

    def exists(self, rel):
        return os.path.exists(self.path(rel)) or rel in self.tracked() or any(
            t.startswith(rel.rstrip("/") + "/") for t in self.tracked() if rel.endswith("/"))

    def read(self, rel):
        """Text of a file from the working tree, else from HEAD; None if neither has it."""
        p = self.path(rel)
        if os.path.exists(p):
            with open(p, encoding="utf-8", errors="replace") as fh:
                return fh.read()
        if rel in self.tracked():
            out = self.git("show", "HEAD:" + rel)
            return out if out else None
        return None


# ---------------------------------------------------------------- register

def today():
    return dt.date.today().isoformat()


def load(repo, kind):
    """All rows of one register file, in order. Malformed lines raise ValueError with the line number."""
    rel = f"{REGISTER}/{FILES[kind]}"
    text = repo.read(rel) or ""
    rows = []
    for n, line in enumerate(text.splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError as exc:
                raise ValueError(f"{rel} line {n} is not JSON: {exc}") from None
    return rows


def current(rows):
    """Latest revision of each id, keeping first-appearance order."""
    cur, order = {}, []
    for r in rows:
        i = r.get("id")
        if i not in cur:
            order.append(i)
        if i not in cur or r.get("rev", 0) >= cur[i].get("rev", 0):
            cur[i] = r
    return [cur[i] for i in order]


def append(repo, kind, record):
    rel = f"{REGISTER}/{FILES[kind]}"
    os.makedirs(repo.path(REGISTER), exist_ok=True)
    with open(repo.path(rel), "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")


def next_id(rows, prefix, day):
    stem = f"{prefix}-{day.replace('-', '')}-"
    n = max([int(r["id"][len(stem):]) for r in rows if str(r.get("id", "")).startswith(stem)
             and r["id"][len(stem):].isdigit()] + [0])
    return f"{stem}{n + 1}"


def legacy_reports(repo):
    text = repo.read(f"{REGISTER}/{LEGACY}") or ""
    return [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]


# ---------------------------------------------------------------- checks

def stale_text_hits(repo, decision):
    """Old wording that contradicts a decision and is still present in its file."""
    hits = []
    for item in decision.get("stale_text", []):
        content = repo.read(item.get("path", ""))
        if content is not None and item.get("text") and item["text"] in content:
            hits.append(item)
    return hits


def check(repo):
    """Return (errors, warnings). Errors are structural and fail CI under --strict."""
    errors, warnings = [], []
    reg = {}
    for kind in FILES:
        try:
            reg[kind] = load(repo, kind)
        except ValueError as exc:
            errors.append(str(exc))
            reg[kind] = []
    for kind, rows in reg.items():
        seen = set()
        for r in rows:
            rid = r.get("id", "?")
            missing = [f for f in REQUIRED[kind] if not r.get(f)]
            if missing:
                errors.append(f"{kind} {rid}: missing {', '.join(missing)}")
            key = (rid, r.get("rev", 0))
            if key in seen:
                errors.append(f"{kind} {rid}: revision {key[1]} appears twice")
            seen.add(key)
            for s in r.get("sources", []):
                if not re.match(r"https?://", s) and not repo.exists(s):
                    errors.append(f"{kind} {rid}: source not in the repository: {s}")
        for r in current(rows):
            if kind == "decisions" and r.get("wiring") not in WIRING:
                errors.append(f"decision {r.get('id')}: wiring must be one of {', '.join(WIRING)}")
            if kind == "asks" and r.get("status") not in ASK_STATUS:
                errors.append(f"ask {r.get('id')}: status must be one of {', '.join(ASK_STATUS)}")
            if kind == "asks" and r.get("status") == "answered" and not r.get("answer"):
                errors.append(f"ask {r.get('id')}: answered without an answer")
            if kind == "findings" and r.get("verdict") not in VERDICTS:
                errors.append(f"finding {r.get('id')}: verdict must be one of {', '.join(VERDICTS)}")
            if kind == "findings":
                errors += [f"finding {r.get('id')}: {x}" for x in validate_measures(r.get("measures"))]

    tracked = repo.tracked()
    # Every owner ruling file has a decision.
    ruling_sources = {s for d in reg["decisions"] for s in d.get("sources", [])}
    for f in sorted(t for t in tracked if t.startswith(RULINGS_DIR) and t.endswith(".md")):
        if f not in ruling_sources:
            errors.append(f"owner ruling with no Kean decision: {f} (python3 -I jobs/kean/kean.py add-decision ...)")
    # Every experiment report has a finding, unless it predates Kean and is listed as legacy.
    finding_sources = {s for f in reg["findings"] for s in f.get("sources", [])}
    legacy = set(legacy_reports(repo))
    for f in sorted(t for t in tracked if REPORT_RE.match(t)):
        if f not in finding_sources and f not in legacy:
            errors.append(f"report with no Kean finding: {f} (python3 -I jobs/kean/kean.py add-finding ...)")
    for f in sorted(legacy & finding_sources):
        warnings.append(f"{f} is summarized now; remove it from {REGISTER}/{LEGACY}")
    # Questions for the owner in agent notes must be registered.
    ask_ids = {a["id"] for a in reg["asks"]}
    for notes in sorted(t for t in tracked if re.match(r"^HANDOFF/notes-[^/]+\.md$", t)):
        date = None
        for n, line in enumerate((repo.read(notes) or "").splitlines(), 1):
            m = ENTRY_RE.match(line)
            if m:
                date = m.group(1)
                continue
            if not date or date < KEAN_START or "@owner" not in line.lower() or NO_ASK_RE.search(line):
                continue
            ids = ASK_ID_RE.findall(line)
            if not ids:
                errors.append(f"{notes}:{n}: asks the owner without a Kean ask id (python3 -I jobs/kean/kean.py add-ask ...)")
            for i in ids:
                if i not in ask_ids:
                    errors.append(f"{notes}:{n}: cites unknown Kean ask {i}")
    # The brief must match the register.
    fresh = render_brief(repo, reg)
    if strip_drift(repo.read(BRIEF) or "") != strip_drift(fresh):
        errors.append(f"{BRIEF} is out of date (python3 -I jobs/kean/kean.py brief)")
    if len(fresh.encode("utf-8")) > BRIEF_MAX_BYTES:
        errors.append(f"{BRIEF} is {len(fresh.encode('utf-8'))} bytes, over the {BRIEF_MAX_BYTES}-byte limit; shorten entries")
    if repo.read(ASKS_PAGE) != render_asks(repo, reg):
        errors.append(f"{ASKS_PAGE} is out of date (python3 -I jobs/kean/kean.py brief)")
    # Notes change in every session; a stale NEWEST.md is reported, not failed.
    if repo.read(NEWEST_PAGE) != render_newest(repo):
        warnings.append(f"{NEWEST_PAGE} is out of date (python3 -I jobs/kean/kean.py brief)")
    # Drift is reported, not failed: it is what the brief exists to show.
    for d in current(reg["decisions"]):
        for h in stale_text_hits(repo, d):
            warnings.append(f"decision {d['id']}: contradicting text still in {h['path']}: \"{h['text'][:80]}\"")
    return errors, warnings


# ---------------------------------------------------------------- brief

def _one(text, n=220):
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def strip_drift(text):
    """The brief without its drift block, which reflects other files and is not part of the freshness check."""
    return re.sub(re.escape(DRIFT_BEGIN) + r".*?" + re.escape(DRIFT_END), "", text, flags=re.S)


HEALTH = "jobs/davy-chain-health/output/HEALTH.json"


def chain_health(repo):
    """Gutenberg: Davy's daily claim-drafts -> claim-kit health verdict, one line, so a break is seen at session start."""
    try:
        h = json.loads(open(os.path.join(str(repo), HEALTH), encoding="utf-8").read())
    except (OSError, ValueError):
        return None
    if not isinstance(h, dict) or h.get("verdict") not in ("pass", "fail"):
        return None
    mark = "FAIL" if h["verdict"] == "fail" else "pass"
    return (f"**Chain health ({mark}, {str(h.get('checked_utc', ''))[:16]}Z, as of `{str(h.get('input_commit') or '')[:10]}`):** "
            + _one(str(h.get("summary", "")), 300)
            + (" Fix it before preparing a paid batch (`" + HEALTH.replace("HEALTH.json", "HEALTH.md") + "`)."
               if h["verdict"] == "fail" else ""))


def _measures_arg(text):
    raw = open(text[1:], encoding="utf-8").read() if text.startswith("@") else text
    try:
        m = json.loads(raw)
    except ValueError as exc:
        raise SystemExit(f"--measures is not JSON: {exc}") from None
    errs = validate_measures(m)
    if errs:
        raise SystemExit("--measures refused: " + "; ".join(errs))
    return m


def render_brief(repo, reg=None):
    if reg is None:
        reg = {k: load(repo, k) for k in FILES}
    decisions, asks, findings = (current(reg[k]) for k in ("decisions", "asks", "findings"))
    open_asks = sorted((a for a in asks if a["status"] == "open"), key=lambda a: (a["date"], a["id"]))
    needs_work = [d for d in decisions if d["wiring"] in ("partly_wired", "not_wired")]
    unverified = sorted(d["id"] for d in decisions if d["wiring"] == "not_verified")
    drift = [(d, h) for d in decisions for h in stale_text_hits(repo, d)]
    newest = sorted(findings, key=lambda f: (f["date"], f["id"]), reverse=True)[:BRIEF_FINDINGS]
    L = []
    w = L.append
    w("# Kean brief: read this first")
    w("")
    w("Generated from `jobs/kean/register/` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand. Named for")
    w("Thomas Kean, chair of the 9/11 Commission, which found that agencies held the pieces but did not share them.")
    w("")
    w("- **Start:** read this page and only the newest entry of each `HANDOFF/notes-*.md`. Before proposing any tool,")
    w("  pilot or speed-up, run `python3 -I jobs/kean/kean.py search <words>`.")
    w("- **Stop:** record results (`add-finding`), questions for the owner (`add-ask`; cite the id in your notes) and")
    w("  owner decisions you received (`add-decision`, `wire`). Routine progress stays in your notes. See `jobs/kean/README.md`.")
    w("")
    health = chain_health(repo)
    if health:
        w(health)
        w("")
    w(f"## Waiting for the owner ({len(open_asks)})")
    w("")
    if open_asks:
        w(", ".join(f"**{a['id']}**" for a in open_asks) + f". Full questions: `{ASKS_PAGE}`.")
    else:
        w("Nothing.")
    w("")
    pinned = [d for d in decisions if d.get("pinned")]
    if pinned:
        w("## Standing owner requirements")
        w("")
        for d in pinned:
            w(f"- **{d['title']}** ({d['id']}): {_one(d['ruling'], 900)}")
        w("")
    w(f"## Owner decisions not yet carried out by the tools ({len(needs_work)})")
    w("")
    for d in needs_work:
        w(f"- **{d['id']}** ({d['wiring'].replace('_', ' ')}): {_one(d['ruling'], 300)}"
          + (f" {_one(d['wiring_note'], 260)}" if d.get("wiring_note") else ""))
    if not needs_work:
        w("Nothing.")
    if unverified:
        w(f"- Not yet checked against the tools: {', '.join(unverified)}.")
    w("")
    w(DRIFT_BEGIN)
    if drift:
        w("**Old wording that contradicts an owner decision is still in these files; remove it:**")
        for d, h in drift:
            w(f"- `{h['path']}` ({d['id']}): \"{_one(h['text'], 110)}\"")
        w("")
    w(DRIFT_END)
    w(f"## Newest results ({len(newest)} of {len(findings)}; `search` finds the rest)")
    w("")
    for f in newest:
        w(f"- {f['date']} {f['id']} **{f['verdict'].replace('_', ' ')}**: {_one(f['tried'], 110)} "
          f"Lesson: {_one(f['lesson'], 200)}")
    w("")
    legacy = legacy_reports(repo)
    w(f"Register: {len(decisions)} owner decisions, {sum(1 for a in asks if a['status'] == 'answered')} answered "
      f"questions, {len(findings)} results; {len(legacy)} older reports not yet summarized "
      f"(`jobs/kean/register/legacy_reports.txt`).")
    return "\n".join(L) + "\n"


def render_asks(repo, reg=None):
    """HANDOFF/KEAN_ASKS.md: every open ask in full (owner ruling R6); generated, never edited by hand."""
    if reg is None:
        reg = {k: load(repo, k) for k in FILES}
    asks = current(reg["asks"])
    open_asks = sorted((a for a in asks if a["status"] == "open"), key=lambda a: (a["date"], a["id"]))
    L = ["# Questions waiting for the owner", "",
         "Generated from `jobs/kean/register/asks.jsonl` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand.",
         "Answer with `kean.py answer --id ID --answer TEXT`.", ""]
    for a in open_asks:
        L += [f"## {a['id']} ({a['date']}, {a['asked_by']})", "", str(a["question"]).strip(), "",
              f"*Why:* {str(a['why']).strip()}", ""]
        if a.get("sources"):
            L += ["Sources: " + ", ".join(f"`{x}`" for x in a["sources"]), ""]
    if not open_asks:
        L += ["Nothing is waiting.", ""]
    return "\n".join(L)


def newest_entries(repo):
    """The first "## " block of each HANDOFF/notes-*.md, the same rule as awk '/^## /{n++} n==1'."""
    on_disk = {"HANDOFF/" + n for n in (os.listdir(repo.path("HANDOFF")) if os.path.isdir(repo.path("HANDOFF")) else [])}
    notes = sorted(p for p in repo.tracked() | on_disk if re.fullmatch(r"HANDOFF/notes-[^/]+\.md", p))
    out = []
    for path in notes:
        text = repo.read(path) or ""
        block, inside = [], False
        for line in text.splitlines():
            if line.startswith("## "):
                if inside:
                    break
                inside = True
            if inside:
                block.append(line)
        entry = "\n".join(block).strip()
        raw = entry.encode("utf-8")
        if len(raw) > NEWEST_ENTRY_MAX_BYTES:
            entry = raw[:NEWEST_ENTRY_MAX_BYTES].decode("utf-8", "ignore").rstrip() + f"\n\n… (truncated; read `{path}`)"
        out.append((path, entry or "(no dated entry)"))
    return out


def render_newest(repo):
    L = ["# Newest handoff entries", "",
         "Generated by `python3 -I jobs/kean/kean.py brief` (also `kean.py newest`); do not edit by hand. The first",
         "`## ` entry of each `HANDOFF/notes-*.md`; older entries are history (`kean.py search` finds them).", ""]
    for path, entry in newest_entries(repo):
        L += [f"# `{path}`", "", entry, ""]
    return "\n".join(L)


def write_brief(repo):
    text = render_brief(repo)
    with open(repo.path(BRIEF), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    with open(repo.path(ASKS_PAGE), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_asks(repo))
    with open(repo.path(NEWEST_PAGE), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_newest(repo))
    return text


# ---------------------------------------------------------------- search

def search(repo, terms, limit=8):
    """Rank register entries and checked-out notes/reports by how many of the terms they contain."""
    terms = [t.lower() for t in terms if t.strip()]
    out = []
    for kind in FILES:
        for r in current(load(repo, kind)):
            blob = json.dumps(r, ensure_ascii=False).lower()
            if all(t in blob for t in terms):
                out.append((sum(blob.count(t) for t in terms) + 1000, f"[{kind}] {r['id']}",
                            _one(r.get("question") or r.get("ruling") or f"{r.get('tried')} Result: {r.get('result')}", 260)))
    files = [f for f in repo.git("ls-files", "-z", "--", *SEARCH_GLOBS).split("\0") if f]
    unread = 0
    for f in files:
        if f.startswith(REGISTER + "/"):
            continue
        p = repo.path(f)
        if not os.path.exists(p):
            unread += 1
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        low = text.lower()
        if all(t in low for t in terms):
            line = next((l for l in text.splitlines() if terms[0] in l.lower()), "")
            out.append((sum(low.count(t) for t in terms), f, _one(line, 160)))
    out.sort(key=lambda x: (-x[0], x[1]))
    return out[:limit], unread


# ---------------------------------------------------------------- command line

def main(argv=None):
    ap = argparse.ArgumentParser(prog="kean", description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("terms", nargs="+"); s.add_argument("--limit", type=int, default=8)
    sub.add_parser("brief")
    sub.add_parser("newest")
    c = sub.add_parser("check"); c.add_argument("--strict", action="store_true")
    a = sub.add_parser("add-ask")
    for f in ("question", "why", "asked-by"):
        a.add_argument("--" + f, required=True)
    a.add_argument("--source", action="append", default=[]); a.add_argument("--date", default=None); a.add_argument("--id")
    n = sub.add_parser("answer")
    n.add_argument("--id", required=True); n.add_argument("--answer", required=True)
    n.add_argument("--status", default="answered", choices=ASK_STATUS); n.add_argument("--decision"); n.add_argument("--date")
    d = sub.add_parser("add-decision")
    for f in ("title", "ruling"):
        d.add_argument("--" + f, required=True)
    d.add_argument("--source", action="append", required=True); d.add_argument("--wiring", default="not_verified", choices=WIRING)
    d.add_argument("--implemented-by", action="append", default=[]); d.add_argument("--wiring-note", default="")
    d.add_argument("--stale-text", action="append", default=[], help="PATH::TEXT that contradicts the decision")
    d.add_argument("--pinned", action="store_true", help="show the full ruling in every brief")
    d.add_argument("--date"); d.add_argument("--id")
    wi = sub.add_parser("wire")
    wi.add_argument("--id", required=True); wi.add_argument("--wiring", required=True, choices=WIRING)
    wi.add_argument("--implemented-by", action="append", default=[]); wi.add_argument("--wiring-note")
    wi.add_argument("--clear-stale-text", action="store_true")
    f = sub.add_parser("add-finding")
    for x in ("tried", "expected", "result", "lesson", "by"):
        f.add_argument("--" + x, required=True)
    f.add_argument("--verdict", required=True, choices=VERDICTS); f.add_argument("--source", action="append", required=True)
    f.add_argument("--keyword", action="append", default=[]); f.add_argument("--date"); f.add_argument("--id")
    f.add_argument("--measures", help="JSON object, or @FILE: wave, usd {total, by_role, by_model, basis}, "
                                      "orders {attempted, submitted, filed}, controls {planted, missed}")
    am = sub.add_parser("add-measures", help="attach structured numbers to an existing finding (new revision)")
    am.add_argument("--id", required=True); am.add_argument("--measures", required=True)
    args = ap.parse_args(argv)
    repo = Repo(args.root)

    if args.cmd == "search":
        hits, unread = search(repo, args.terms, args.limit)
        for score, where, snippet in hits:
            print(f"{where}\n    {snippet}")
        if not hits:
            print("No earlier work found for: " + " ".join(args.terms))
        if unread:
            print(f"({unread} tracked notes or reports are not checked out here and were not searched;"
                  " `git sparse-checkout add research` widens the search.)")
        return 0
    if args.cmd == "brief":
        write_brief(repo)
        print(f"wrote {BRIEF}, {ASKS_PAGE} and {NEWEST_PAGE}")
        return 0
    if args.cmd == "newest":
        sys.stdout.write(render_newest(repo))
        return 0
    if args.cmd == "check":
        errors, warnings = check(repo)
        for e in errors:
            print("ERROR " + e)
        for w_ in warnings:
            print("WARN  " + w_)
        print(f"Kean check: {len(errors)} errors, {len(warnings)} warnings")
        return 1 if (errors and args.strict) else 0

    if args.cmd == "add-ask":
        rows = load(repo, "asks")
        day = args.date or today()
        rec = {"id": args.id or next_id(rows, "A", day), "rev": 0, "date": day, "asked_by": args.asked_by,
               "question": args.question, "why": args.why, "status": "open", "sources": args.source}
        append(repo, "asks", rec)
    elif args.cmd == "answer":
        cur = {r["id"]: r for r in current(load(repo, "asks"))}
        if args.id not in cur:
            ap.error(f"no ask {args.id}")
        rec = dict(cur[args.id], rev=cur[args.id].get("rev", 0) + 1, status=args.status, answer=args.answer,
                   answered_on=args.date or today())
        if args.decision:
            rec["decision"] = args.decision
        append(repo, "asks", rec)
    elif args.cmd == "add-decision":
        rows = load(repo, "decisions")
        day = args.date or today()
        stale = []
        for item in args.stale_text:
            path, _, text = item.partition("::")
            stale.append({"path": path, "text": text})
        rec = {"id": args.id or next_id(rows, "D", day), "rev": 0, "date": day, "title": args.title, "ruling": args.ruling,
               "sources": args.source, "wiring": args.wiring, "implemented_by": args.implemented_by,
               "wiring_note": args.wiring_note, "stale_text": stale, "pinned": args.pinned}
        append(repo, "decisions", rec)
    elif args.cmd == "wire":
        cur = {r["id"]: r for r in current(load(repo, "decisions"))}
        if args.id not in cur:
            ap.error(f"no decision {args.id}")
        rec = dict(cur[args.id], rev=cur[args.id].get("rev", 0) + 1, wiring=args.wiring,
                   implemented_by=sorted(set(cur[args.id].get("implemented_by", []) + args.implemented_by)))
        if args.wiring_note is not None:
            rec["wiring_note"] = args.wiring_note
        if args.clear_stale_text:
            rec["stale_text"] = []
        append(repo, "decisions", rec)
    elif args.cmd == "add-finding":
        rows = load(repo, "findings")
        day = args.date or today()
        rec = {"id": args.id or next_id(rows, "F", day), "rev": 0, "date": day, "by": args.by, "tried": args.tried,
               "expected": args.expected, "result": args.result, "verdict": args.verdict, "lesson": args.lesson,
               "sources": args.source, "keywords": args.keyword}
        if args.measures:
            rec["measures"] = _measures_arg(args.measures)
        append(repo, "findings", rec)
    elif args.cmd == "add-measures":
        cur = {r["id"]: r for r in current(load(repo, "findings"))}
        if args.id not in cur:
            raise SystemExit(f"no finding {args.id}")
        rec = dict(cur[args.id], rev=cur[args.id].get("rev", 0) + 1, measures=_measures_arg(args.measures))
        append(repo, "findings", rec)
    print(f"recorded {rec['id']}")
    write_brief(repo)
    print(f"wrote {BRIEF}; commit both")
    return 0


if __name__ == "__main__":
    sys.exit(main())
