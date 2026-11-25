"""Stateless render mode for the Maudslay conveyor (opt-in: `conveyor.py run --stateless`), and the helpers the paired
replay gauge (gauge_stateless.py) shares with it.

Finding (Papinian, research/excavator/claude-papinian-2026-11-10): agent workers made about 60-110 calls each at about
170-214k context per call (about 2.3M tokens, $0.64 per attempted order, $4.71 per filed claim), although the evidence
one order needs is about 16.5k tokens for a producer and 9.7k for a reviewer. A stateless stage is one request with no
tools: the rules and the evidence are rendered into the prompt by scripts, and the answer comes back through
`claude -p --json-schema`.

Prompt layout (all deterministic, no timestamps, no machine paths, so the bytes repeat):

  producer   system prompt file (PREFIX, byte-identical for every order on a route):
                 COMMON rule files + producer role/route text
             stdin (SUFFIX): the order's evidence, then the instruction to answer.
  reviewer   system prompt file (PREFIX, byte-identical for arm A and arm B of one order):
                 COMMON rule files + reviewer role text + the order's evidence
             stdin (SUFFIX): the arm's text and the claim.

Nothing here makes a legal judgment. The scripts compute receipts (hashes, quoted-span checks, grep hits) and serve
bounded file ranges; the model answers; the conveyor writes the sheet rows from the answer and its existing checks
decide what is used.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPTS = HERE / "prompts"

CUTOFF_TOKENS = 150_000          # a rendered prompt above this (chars/4) stays on the agent route
PAD = 600                        # characters of context on each side of every cited span
WINDOW_CHARS_CAP = 300_000       # windows beyond this are listed, not inlined (the need_more round can fetch them)
CRUDEN_HITS_CAP = 60

PRODUCTION_ROUTE = "research/excavator/claude-production-2026-10-28/PRODUCTION_ROUTE.md"
CLAIM_SCHEMA = "research/stage19/CLAIM_SCHEMA.md"
BATCH_MD = "jobs/claim-kit/BATCH.md"
PRODUCER_BRIEF = "research/excavator/claude-nira-sweep-2026-10-29/PRODUCER_BRIEF.md"
REVIEWER_BRIEF = "research/excavator/claude-nira-sweep-2026-10-29/REVIEWER_BRIEF.md"
RULINGS_DIR = "research/readiness/owner_rulings/"
RULINGS = ("2026-10-28-evidence-not-convenience.md", "2026-10-21-transcription-as-text.md",
           "2026-10-21-until-and-further-exempt.md", "2026-10-21-strike-and-insert.md")
UNDECIDED_RULING = "2026-11-05-empty-status-history.md"
BATCH_SECTION = "## Before assigning a producer"
BATCH_PARAGRAPH = "Read every original and common source independently"
BRIEF_SECTION = "## Sheet fields for a plain code approval"

CRUDEN = "research/excavator/claude-nira-sweep-2026-10-29/cruden.py"
NOTE_RE = re.compile(r"(?:Revoked|Superseded)\s+by\b", re.I)

DECISION_FIELDS_FIXED = ("instrument_id", "dossier_sha256", "agent")
DECISION_BOOLS = ("approved", "original_confirmed", "original_pages_confirmed", "inventory_confirmed")
DECISION_JSON_LIST = ("search_ids", "unresolved_material_gaps", "source_notes")
DECISION_JSON_DICT = ("conflict_resolutions", "working_text")
CLAUSE_BOOLS = ("effective_date_confirmed",)
CLAUSE_JSON_LIST = ("later_event_ids", "later_events")
CLAUSE_INTS = ("inventory_char_start", "inventory_char_end")
OUTCOMES = ("submit", "unresolved", "blocked", "route_owner")

# need_more: never serve answers, other workers' material or anything outside the repository.
FORBIDDEN_PARTS = {"reviews", "completion", "control", "controls", "scratch", "undecided", "complete-v1", "complete-v2",
                   "complete-v3", "stateless-calls-2026-11-24", ".git"}
FORBIDDEN_NAMES = {"decisions.csv", "clauses.csv", "assessment.jsonl", "assessment.json", "rationales.json",
                   "claims.proposed.jsonl", "producer_report.md", "applied_for_review", "ledger.jsonl",
                   "controls.json", "adjudicate.json", "adjudication.json", "report.md"}
FORBIDDEN_PREFIXES = ("research/readiness/claims/", "research/readiness/decisions/")
FORBIDDEN_DIR_RE = re.compile(r"^(applied-v\d+|complete-v\d+|workers|out)$")
NEED_MAX_REQUESTS = 6
NEED_MAX_BYTES = 20_000
NEED_MAX_TOTAL = 80_000


def est_tokens(text):
    """Token estimate used for the cutoff and the forecast: characters / 4, rounded up."""
    return -(-len(text) // 4)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canon_sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def slug(iid):
    return iid.replace(":", "_")


# ---------------------------------------------------------------------------------------------------------------
# Rule files (the COMMON block)


def _norm(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_rel(repo, rel):
    return _norm((Path(repo) / rel).read_text(encoding="utf-8"))


def section(text, heading):
    """The block from the line starting with `heading` to the next heading of the same or higher level."""
    lines = text.split("\n")
    level = len(heading) - len(heading.lstrip("#"))
    for i, ln in enumerate(lines):
        if ln.startswith(heading):
            j = i + 1
            while j < len(lines):
                m = re.match(r"^(#+)\s", lines[j])
                if m and len(m.group(1)) <= level:
                    break
                j += 1
            return "\n".join(lines[i:j]).strip("\n")
    raise ValueError(f"heading {heading!r} not found")


def paragraph(text, start):
    """The paragraph (up to the next blank line) whose first line starts with `start`."""
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if ln.startswith(start):
            j = i
            while j < len(lines) and lines[j].strip():
                j += 1
            return "\n".join(lines[i:j])
    raise ValueError(f"paragraph starting {start!r} not found")


def rule_blocks(repo, role, undecided=False):
    """[(label, text)] for the rule files, in a fixed order."""
    blocks = [(PRODUCTION_ROUTE, read_rel(repo, PRODUCTION_ROUTE).strip("\n")),
              (CLAIM_SCHEMA, read_rel(repo, CLAIM_SCHEMA).strip("\n"))]
    batch = read_rel(repo, BATCH_MD)
    blocks.append((f'{BATCH_MD} section "Before assigning a producer"', section(batch, BATCH_SECTION)))
    blocks.append((f'{BATCH_MD} paragraph "{BATCH_PARAGRAPH}..."', paragraph(batch, BATCH_PARAGRAPH)))
    for name in RULINGS + ((UNDECIDED_RULING,) if undecided else ()):
        blocks.append((RULINGS_DIR + name, read_rel(repo, RULINGS_DIR + name).strip("\n")))
    brief = read_rel(repo, PRODUCER_BRIEF)
    blocks.append((f'{PRODUCER_BRIEF} section "Sheet fields for a plain code approval"', section(brief, BRIEF_SECTION)))
    if role == "reviewer":
        blocks.append((REVIEWER_BRIEF, read_rel(repo, REVIEWER_BRIEF).strip("\n")))
    return blocks


def common_block(repo, role, undecided=False):
    out = ["=== RULE FILES (the repository's rules, inlined; you cannot open files) ==="]
    for label, text in rule_blocks(repo, role, undecided):
        out.append(f"\n--- RULE FILE: {label} ---\n{text}")
    return "\n".join(out) + "\n"


def role_text(role, route_name="", route_text=""):
    t = _norm((PROMPTS / f"stateless_{role}.txt").read_text(encoding="utf-8"))
    return t.replace("<<ROUTE_NAME>>", route_name).replace("<<ROUTE>>", route_text.strip())


def producer_prefix(repo, route_name, route_text, undecided=False):
    return common_block(repo, "producer", undecided) + "\n" + role_text("producer", route_name, route_text)


def reviewer_prefix(repo, evidence, undecided=False):
    """Rules + role + the order's evidence: identical for arm A and arm B of one order."""
    return (common_block(repo, "reviewer", undecided) + "\n" + role_text("reviewer")
            + "\n=== ORDER EVIDENCE ===\n" + evidence)


# ---------------------------------------------------------------------------------------------------------------
# Evidence: text, windows, receipts, grep, cruden


class Texts:
    """Held text files by repository-relative path, read once; offsets are character offsets of the decoded text."""

    def __init__(self, repo):
        self.repo = Path(repo).resolve()
        self.cache = {}

    def get(self, rel):
        if not rel:
            return None
        if rel in self.cache:
            return self.cache[rel]
        val = None
        try:
            p = (self.repo / rel).resolve()
            if p.is_relative_to(self.repo) and p.is_file():
                raw = p.read_bytes()
                val = (raw.decode("utf-8", "replace"), hashlib.sha256(raw).hexdigest())
        except (OSError, ValueError):
            val = None
        self.cache[rel] = val
        return val


def cited_spans(obj):
    """[(text_path, start, end)] for every dict that names a held text file and a character range: a source record
    (text_path, char_start, char_end), a view clause (source.text_path), a cruden hit (file)."""
    out = []

    def walk(o):
        if isinstance(o, dict):
            src = o.get("source") if isinstance(o.get("source"), dict) else {}
            tp = o.get("text_path") or src.get("text_path") or o.get("file")
            cs, ce = o.get("char_start"), o.get("char_end")
            if isinstance(tp, str) and isinstance(cs, int) and isinstance(ce, int) and ce >= cs:
                out.append((tp, cs, ce))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(obj)
    seen, uniq = set(), []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


def merge_windows(spans, pad=PAD):
    """{path: [(start, end)]} windows of +/-pad around each span, overlapping ones merged, in order."""
    by = {}
    for tp, s, e in spans:
        by.setdefault(tp, []).append((max(0, s - pad), e + pad))
    out = {}
    for tp, ws in by.items():
        ws.sort()
        merged = [list(ws[0])]
        for a, b in ws[1:]:
            if a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        out[tp] = [tuple(m) for m in merged]
    return out


def render_windows(texts, spans, skip_paths=(), pad=PAD, cap=WINDOW_CHARS_CAP):
    """Windows around every cited span (the whole-text files in skip_paths are already inlined). Returns (text, omitted)."""
    parts, omitted, used = [], [], 0
    wins = merge_windows([s for s in spans if s[0] not in set(skip_paths)], pad)
    for tp in sorted(wins):
        got = texts.get(tp)
        if got is None:
            omitted.append(f"{tp} (not held at this path)")
            continue
        body, sha = got
        for a, b in wins[tp]:
            b = min(b, len(body))
            if a >= len(body):
                omitted.append(f"{tp} chars {a}-{b} (beyond the end of the text)")
                continue
            chunk = body[a:b]
            if used + len(chunk) > cap:
                omitted.append(f"{tp} chars {a}-{b}")
                continue
            used += len(chunk)
            parts.append(f"--- WINDOW {tp} chars {a}-{b} (file sha256 {sha}) ---\n{chunk}\n--- END WINDOW ---")
    return "\n".join(parts), omitted


def receipts(texts, obj):
    """Hash and quoted-span check receipts, computed here. One line per text file (sha256 of the file against every
    text_sha256 the evidence records for it) and per quoted span (the quote against text[start:end])."""
    hashes, quotes = {}, []

    def walk(o):
        if isinstance(o, dict):
            src = o.get("source") if isinstance(o.get("source"), dict) else o
            tp = o.get("text_path") or src.get("text_path")
            if isinstance(tp, str):
                want = o.get("text_sha256") or src.get("text_sha256")
                if isinstance(want, str):
                    hashes.setdefault(tp, set()).add(want)
                cs, ce = o.get("char_start"), o.get("char_end")
                q = o.get("quote") if isinstance(o.get("quote"), str) else (o.get("text") if isinstance(o.get("text"), str) else None)
                if q is not None and isinstance(cs, int) and isinstance(ce, int):
                    quotes.append((tp, cs, ce, q, "quote" if isinstance(o.get("quote"), str) else "text"))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(obj)
    lines = []
    for tp in sorted(hashes):
        got = texts.get(tp)
        if got is None:
            lines.append(f"HASH {tp}: FILE NOT FOUND in the repository")
            continue
        verdicts = ["match" if got[1] == h else f"MISMATCH (recorded {h[:16]}...)" for h in sorted(hashes[tp])]
        lines.append(f"HASH {tp}: file sha256 {got[1]} vs recorded text_sha256: {'; '.join(verdicts)}")
    seen = set()
    for tp, cs, ce, q, kind in quotes:
        if (tp, cs, ce, q) in seen:
            continue
        seen.add((tp, cs, ce, q))
        got = texts.get(tp)
        if got is None:
            lines.append(f"SPAN {tp} {cs}-{ce}: FILE NOT FOUND")
            continue
        actual = got[0][cs:ce]
        if actual == q:
            res = "exact"
        elif q and actual.startswith(q.rstrip(".… ")):
            res = "prefix match (the recorded text is shorter than the span)"
        elif q in actual and q:
            res = "contained in the span"
        else:
            res = "MISMATCH (the quoted text is not the held bytes at this span)"
        lines.append(f"SPAN {tp} chars {cs}-{ce} ({kind}, {len(q)} chars): {res}")
    return "\n".join(lines) if lines else "(no hashed text files or quoted spans in the evidence)"


def note_grep(texts, paths, extra_json=None, context=220):
    """Every "Revoked by" / "Superseded by" note in the named held texts and in a LOOKUPS row (a JSON value)."""
    lines = []
    for tp in sorted(set(paths)):
        got = texts.get(tp)
        if got is None:
            continue
        for m in NOTE_RE.finditer(got[0]):
            a, b = max(0, m.start() - context), min(len(got[0]), m.end() + context)
            snippet = re.sub(r"\s+", " ", got[0][a:b])
            lines.append(f"NOTE {tp} chars {m.start()}-{m.end()}: ...{snippet}...")
    if extra_json is not None:
        blob = json.dumps(extra_json, ensure_ascii=False, sort_keys=True)
        for m in NOTE_RE.finditer(blob):
            a, b = max(0, m.start() - context), min(len(blob), m.end() + context)
            lines.append(f"NOTE LOOKUPS row: ...{blob[a:b]}...")
    return "\n".join(lines) if lines else "(none found in the order's held texts or its LOOKUPS row)"


def cruden_block(hits):
    if hits is None:
        return "(cruden number search not run)"
    if not hits:
        return "(cruden found no held text citing this order by number)"
    lines = []
    for h in hits[:CRUDEN_HITS_CAP]:
        ctx = re.sub(r"\s+", " ", str(h.get("context") or ""))[:320]
        lines.append(f"- {h.get('file')} chars {h.get('char_start')}-{h.get('char_end')} "
                     f"[{h.get('match')}] sha256 {h.get('raw_sha256')}: {ctx}")
    if len(hits) > CRUDEN_HITS_CAP:
        lines.append(f"(+{len(hits) - CRUDEN_HITS_CAP} more hits not shown)")
    return "\n".join(lines)


def cruden_hits_from_file(path, ids):
    """{iid: [hits]} (compact fields only) from a `cruden.py number ... --write FILE` result."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    keep = ("file", "raw_sha256", "char_start", "char_end", "match", "context")
    return {iid: [{k: h.get(k) for k in keep} for h in (data.get("queries", {}).get(iid, {}).get("hits") or [])]
            for iid in ids}


def run_cruden_numbers(repo, ids, out_path, python=None, timeout=1800):
    """`cruden.py number EO:N ... --write OUT` once for many orders; returns {iid: [hits]}."""
    cmd = [python or sys.executable, "-X", "utf8", "-I", str(Path(repo) / CRUDEN), "number", *ids, "--write", str(out_path)]
    p = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if p.returncode:
        raise RuntimeError(f"cruden number failed ({p.returncode}): {(p.stderr or p.stdout)[-300:]}")
    return cruden_hits_from_file(out_path, ids)


def cache_evidence(workers):
    """Cache sharing across processes, from ledger worker records of stateless calls. Per prefix hash: how many
    processes used it, the prefix size, and for each process the first model call's cache_read and cache_write. The
    second and later processes should show cache_read of about the prefix size."""
    by = {}
    for w in workers:
        st = w.get("stateless") if isinstance(w, dict) else None
        if not st or not st.get("calls"):
            continue
        first = st["calls"][0]
        by.setdefault(st["prefix_sha256"], {"prefix_tokens_est": st.get("prefix_tokens_est"), "processes": []})[
            "processes"].append({"label": w.get("label"), "started_utc": w.get("started_utc"),
                                 "first_call_cache_read": first["cache_read"],
                                 "first_call_cache_write": first["cache_write"], "first_call_input": first["input"],
                                 "calls": len(st["calls"])})
    out = []
    for sha, d in sorted(by.items()):
        procs = sorted(d["processes"], key=lambda r: r.get("started_utc") or "")
        later = procs[1:]
        pt = d["prefix_tokens_est"] or 0
        out.append({"prefix_sha256": sha, "prefix_tokens_est": pt, "processes": len(procs),
                    "later_processes_with_cache_read_near_prefix": sum(
                        1 for r in later if pt and r["first_call_cache_read"] >= 0.8 * pt),
                    "later_processes": len(later), "detail": procs})
    return out


def _cap(s, n):
    s = str(s)
    return s if len(s) <= n else s[:n] + "...(cut)"


def view_original_path(view):
    lead = (view.get("lookup_leads") or {}).get("original") or {}
    if lead.get("text_path"):
        return lead["text_path"]
    cat = (view.get("source_catalogue") or {}).get(view.get("original_source_id") or "") or {}
    if cat.get("text_path"):
        return cat["text_path"]
    return ((view.get("own_text_boundary") or {}).get("source") or {}).get("text_path")


def view_order_text_paths(view, iid):
    """Held texts of the order itself (not of the later instruments that act on it)."""
    paths = set()
    p = view_original_path(view)
    if p:
        paths.add(p)
    for key, rec in (view.get("source_catalogue") or {}).items():
        if isinstance(rec, dict) and rec.get("text_path") and (key.startswith(("ORIGINAL:", "CLAUSES:"))
                                                              or key.startswith(f"TERM:{iid}:")) and iid in key:
            paths.add(rec["text_path"])
    return sorted(paths)


def compact_view(view):
    """The parts of an order's Geddes view that are not text: header, missing list, machine-search coverage, later-event
    chain, prior research, conflicts. Long strings are cut; nothing is invented."""
    out = {}
    for k in ("instrument_id", "title", "signing_date", "whole_order_status", "missing", "conflicts", "own_text_boundary",
              "current_canonical_claim", "lookup_corpus_scope"):
        if k in view:
            out[k] = view[k]
    ms = []
    for s in (view.get("machine_searches") or {}).get("searches", []):
        cov = s.get("coverage") or {}
        ms.append({"search_id": s.get("search_id"), "checked_on": s.get("checked_on"), "complete": s.get("complete"),
                   "machine_hits_for_this_order": s.get("machine_hits_for_this_order"),
                   "repository": _cap(cov.get("repository"), 400), "query_or_scope": _cap(cov.get("query_or_scope"), 500),
                   "scope_note": _cap(cov.get("scope_note"), 400)})
    out["machine_searches"] = ms
    chain = (view.get("later_events_chain") or {}).get("chain") or {}
    ev = []
    for e in chain.get("events", [])[:25]:
        src = e.get("source") or {}
        ev.append({"id": e.get("id"), "actor_id": e.get("actor_id"), "signing_date": e.get("signing_date"),
                   "verb": e.get("verb"), "how_named": e.get("how_named"), "sections_touched": e.get("sections_touched"),
                   "provision_text": _cap(e.get("provision_text"), 600),
                   "source_text_path": src.get("text_path"), "source_page_or_item": src.get("page_or_item")})
    out["later_events"] = {"notes": chain.get("notes"), "events": ev}
    out["citable_evidence_ids"] = [{"evidence_id": r.get("evidence_id"), "role": r.get("role"), "actor_id": r.get("actor_id"),
                                    "text_path": r.get("text_path")}
                                   for r in ((view.get("later_events_chain") or {}).get("citable_evidence") or {}).get("records", [])[:40]]
    pr = view.get("prior_research_for_order")
    if pr is not None:
        out["prior_research"] = json.loads(_cap(json.dumps(pr, ensure_ascii=False, sort_keys=True), 6000)) \
            if len(json.dumps(pr)) <= 6000 else _cap(json.dumps(pr, ensure_ascii=False, sort_keys=True), 6000)
    return out


def clause_table(view, texts, orig_path):
    rows = []
    orig = texts.get(orig_path)
    for c in (view.get("clause_inventory") or {}).get("clauses", []) or view.get("clauses", []):
        cid = c.get("id")
        s, e = c.get("char_start"), c.get("char_end")
        head = ""
        if orig and isinstance(s, int) and isinstance(e, int):
            head = re.sub(r"\s+", " ", orig[0][s:e])[:90]
        rows.append(f"- clause_id {cid} | scope_id {c.get('scope_id')} | {c.get('kind')} | {c.get('label')} | "
                    f"chars {s}-{e} | state hint {c.get('lifecycle_state')} | starts: \"{head}\"")
    return "\n".join(rows) if rows else "(no clause inventory in the view)"


def producer_evidence(repo, iid, view, prepared_row, prepared_clauses, cruden_hits, lookups_row=None, texts=None):
    """The ORDER EVIDENCE block for a producer. Returns (text, meta)."""
    texts = texts or Texts(repo)
    orig = view_original_path(view)
    got = texts.get(orig) if orig else None
    spans = [s for s in cited_spans(view) if s[0] != orig]
    spans += [(h["file"], h["char_start"], h["char_end"]) for h in (cruden_hits or [])
              if isinstance(h.get("char_start"), int) and isinstance(h.get("char_end"), int) and h.get("file") != orig]
    win_text, omitted = render_windows(texts, spans, skip_paths=[orig] if orig else [])
    own = view_order_text_paths(view, iid)
    header = {k: view.get(k) for k in ("instrument_id", "title", "signing_date", "whole_order_status") if k in view}
    parts = [f"ORDER: {iid}", f"ORDER SLUG (prefix of every rationale key): {slug(iid)}.",
             "ORDER HEADER: " + json.dumps(header, ensure_ascii=False),
             "PREPARED DECISION ROW (the conveyor keeps instrument_id, dossier_sha256 and agent): "
             + json.dumps({k: prepared_row.get(k, "") for k in ("instrument_id", "dossier_sha256")}, ensure_ascii=False),
             "PREPARED CLAUSE ROWS (scope_id / clause_id): "
             + json.dumps([{"scope_id": c.get("scope_id"), "clause_id": c.get("clause_id")} for c in prepared_clauses],
                          ensure_ascii=False),
             "\n=== CLAUSE INVENTORY (spans are character offsets into the HELD ORDER TEXT below) ===\n"
             + clause_table(view, texts, orig)]
    if got:
        parts.append(f"\n=== HELD ORDER TEXT, IN FULL: {orig} (sha256 {got[1]}, {len(got[0])} characters) ===\n{got[0]}\n"
                     "=== END HELD ORDER TEXT ===")
    else:
        parts.append(f"\n=== HELD ORDER TEXT: not readable at {orig!r}; say so in a block, do not guess ===")
    parts.append("\n=== WINDOWS: +/-600 characters around every cited span in other held texts ===\n"
                 + (win_text or "(none)"))
    if omitted:
        parts.append("WINDOWS NOT INLINED (size cap or path): " + "; ".join(omitted[:40]))
    parts.append("\n=== CRUDEN NUMBER CITATIONS (held texts that cite this order by number) ===\n" + cruden_block(cruden_hits))
    parts.append("\n=== RECEIPTS (computed by script: hashes and quoted-span checks) ===\n" + receipts(texts, view))
    parts.append("\n=== GREP: \"Revoked by\" / \"Superseded by\" in the order's held texts and LOOKUPS row ===\n"
                 + note_grep(texts, own, lookups_row))
    parts.append("\n=== VIEW DIGEST (missing list, machine-search coverage, later-event chain, prior research) ===\n"
                 + json.dumps(compact_view(view), ensure_ascii=False, indent=1, sort_keys=True))
    meta = {"order_text_chars": len(got[0]) if got else 0, "windows_omitted": len(omitted)}
    return "\n".join(parts) + "\n", meta


def claim_original_path(claim):
    rep = claim.get("original_representation") or {}
    if rep.get("text_path"):
        return rep["text_path"]
    for oc in claim.get("operative_clauses", []):
        p = (oc.get("original_source") or {}).get("text_path")
        if p:
            return p
    return None


def reviewer_evidence(repo, claim, cruden_hits, lookups_row=None, texts=None):
    """The ORDER EVIDENCE block for a reviewer, built from the claim's own cited spans. Returns (text, meta). It depends
    on the claim's sources and not on the arm, so arm A and arm B render identical bytes."""
    texts = texts or Texts(repo)
    iid = claim.get("instrument_id")
    orig = claim_original_path(claim)
    got = texts.get(orig) if orig else None
    spans = [s for s in cited_spans(claim) if s[0] != orig]
    spans += [(h["file"], h["char_start"], h["char_end"]) for h in (cruden_hits or [])
              if isinstance(h.get("char_start"), int) and isinstance(h.get("char_end"), int) and h.get("file") != orig]
    win_text, omitted = render_windows(texts, spans, skip_paths=[orig] if orig else [])
    number = slug(iid).split("_")[-1] if iid else None
    own_paths = sorted({p for p in [orig] + [sp[0] for sp in cited_spans(claim) if number and number in sp[0]] if p})
    parts = [f"ORDER: {iid}"]
    if got:
        parts.append(f"=== HELD ORDER TEXT, IN FULL: {orig} (sha256 {got[1]}, {len(got[0])} characters) ===\n{got[0]}\n"
                     "=== END HELD ORDER TEXT ===")
    else:
        parts.append(f"=== HELD ORDER TEXT: not readable at {orig!r} ===")
    parts.append("\n=== WINDOWS: +/-600 characters around every span the claim cites in other held texts ===\n"
                 + (win_text or "(none)"))
    if omitted:
        parts.append("WINDOWS NOT INLINED (size cap or path): " + "; ".join(omitted[:40]))
    parts.append("\n=== CRUDEN NUMBER CITATIONS ===\n" + cruden_block(cruden_hits))
    parts.append("\n=== RECEIPTS (computed by script) ===\n" + receipts(texts, claim))
    parts.append("\n=== GREP: \"Revoked by\" / \"Superseded by\" in the order's held texts and LOOKUPS row ===\n"
                 + note_grep(texts, own_paths, lookups_row))
    return "\n".join(parts) + "\n", {"order_text_chars": len(got[0]) if got else 0, "windows_omitted": len(omitted)}


def over_cutoff(prefix, suffix, cutoff=CUTOFF_TOKENS):
    """True when the rendered prompt (prefix + suffix, chars/4) exceeds the cutoff: the order stays on the agent route."""
    return est_tokens(prefix) + est_tokens(suffix) > cutoff


def producer_suffix(evidence, repair=None):
    t = ("=== ORDER EVIDENCE ===\n" + evidence +
         "\nAnswer now through the JSON schema: one object with decision, clauses, rationales and assessment "
         "(or, only if a specific held file is missing, need_more).")
    if repair:
        t += "\n\n" + repair
    return t


def reviewer_suffix(arm, mode, claim):
    mode_text = ("This is an after-reveal review. In an earlier blind review set, the claim for this order was a planted "
                 "control with a deliberate date defect. The claim below is the genuine version the producer filed. Review it "
                 "on its merits with the same strict standard as a blind review; do not uphold it because it is the genuine "
                 "one. Verdict is \"upheld_after_reveal\" if it is right, or \"rejected\" with defects if not."
                 if mode == "after_reveal" else
                 "This is a blind review. Some claims may be deliberately wrong (planted controls); review it on its "
                 "merits. Verdict is \"upheld\" or \"rejected\".")
    return (f"REVIEW ARM: {arm}\nMODE: {mode}\n{mode_text}\n\nCLAIM TO REVIEW (JSON, sorted keys):\n"
            + json.dumps(claim, sort_keys=True, ensure_ascii=False, indent=1)
            + "\n\nAnswer now through the JSON schema (verdict, defects, reasons; or, only if a specific held file is "
              "missing, need_more).")


# ---------------------------------------------------------------------------------------------------------------
# Schemas


_NEED_MORE = {"type": "array", "maxItems": NEED_MAX_REQUESTS,
              "items": {"type": "object", "properties": {"path": {"type": "string"}, "start": {"type": "integer"},
                                                         "end": {"type": "integer"}, "why": {"type": "string"}},
                        "required": ["path", "start", "end"]}}


def producer_schema():
    s = {"type": "string"}
    b = {"type": "boolean"}
    arr = {"type": "array", "items": {"type": "string"}}
    decision = {"type": "object", "properties": {
        "outcome": {"type": "string", "enum": list(OUTCOMES)},
        "approved": b, "original_confirmed": b, "original_pages_confirmed": b, "inventory_confirmed": b,
        "research_rationale": s, "savings_state": s, "savings_source_id": s, "savings_reason": s,
        "search_ids": arr, "conflict_resolutions": {"type": "object"}, "unresolved_material_gaps": arr,
        "earlier_end_check": s, "scope_check": s, "independent_command_check": s, "savings_check": s,
        "working_text": {"type": "object"}, "source_notes": {"type": "array"}, "publication_kind": s},
        "required": ["outcome"]}
    clause = {"type": "object", "properties": {
        "scope_id": s, "clause_id": s, "state": s, "end_id": s, "effective_date": s, "mechanism": s,
        "effective_date_confirmed": b, "current_basis_id": s, "current_legal_basis": s, "checked_through": s,
        "later_event_ids": arr, "later_events": {"type": "array", "items": {"type": "object"}}, "reason": s,
        "inventory_source_id": s, "inventory_char_start": {"type": "integer"}, "inventory_char_end": {"type": "integer"},
        "inventory_reason": s}, "required": ["scope_id"]}
    assessment = {"type": "object", "properties": {
        "id": s, "operative_force_at_cutoff": s, "operative_force_basis": s, "formal_validity_at_cutoff": s,
        "formal_disposition": s, "first_cause": s, "formal_revocation_after_earlier_cessation": s,
        "claimed_status": s, "outcome": s, "blocker": s}}
    return {"type": "object", "properties": {
        "decision": decision, "clauses": {"type": "array", "items": clause},
        "rationales": {"type": "object", "additionalProperties": s}, "assessment": assessment,
        "status_decision": {"type": "object"}, "need_more": _NEED_MORE}}


def reviewer_schema(mode="blind"):
    verdicts = ["upheld_after_reveal", "rejected"] if mode == "after_reveal" else ["upheld", "rejected"]
    defect = {"type": "object", "properties": {"field": {"type": "string"}, "claim_says": {"type": "string"},
                                               "source_says": {"type": "string"}, "problem": {"type": "string"}},
              "required": ["field", "problem"]}
    return {"type": "object", "properties": {
        "verdict": {"type": "string", "enum": verdicts}, "defects": {"type": "array", "items": defect},
        "reasons": {"type": "string"}, "need_more": _NEED_MORE}}


def schema_text(schema):
    return json.dumps(schema, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------------------------------------------
# The worker command


STATELESS_TEMPLATE = ["claude", "-p", "--tools", "", "--system-prompt-file", "{prefix_file}", "--json-schema", "{schema}",
                      "--setting-sources", "", "--strict-mcp-config", "--output-format", "stream-json", "--verbose",
                      "--model", "{model}"]


def is_stateless_command(argv):
    return "--system-prompt-file" in [str(t) for t in argv]


def validate_stateless_command(argv):
    """Refuse a stateless claude command that could use tools, settings, MCP servers or an old session."""
    toks = [str(t) for t in argv]
    for flag in ("-p", "--tools", "--system-prompt-file", "--json-schema", "--output-format", "--verbose",
                 "--setting-sources", "--strict-mcp-config", "--model"):
        if flag not in toks:
            raise ValueError(f"stateless claude command lacks {flag}")
    if toks[toks.index("--tools") + 1] != "":
        raise ValueError('stateless claude command must pass --tools "" (no tools)')
    if toks[toks.index("--setting-sources") + 1] != "":
        raise ValueError('stateless claude command must pass --setting-sources "" (no CLAUDE.md or settings)')
    if toks[toks.index("--output-format") + 1] != "stream-json":
        raise ValueError("stateless claude command must use --output-format stream-json")
    bad = [t for t in toks if t in ("--bare", "--allowedTools", "--allowed-tools", "--add-dir", "--permission-mode",
                                    "--dangerously-skip-permissions", "--mcp-config")]
    if bad:
        raise ValueError(f"stateless claude command must not carry {bad}")
    return toks


# ---------------------------------------------------------------------------------------------------------------
# Event stream


def _usage_row(u, mid=None, model=None):
    cc = u.get("cache_creation") if isinstance(u.get("cache_creation"), dict) else {}
    write = int(u.get("cache_creation_input_tokens") or 0)
    w1h = int(cc.get("ephemeral_1h_input_tokens") or 0)
    return {"message_id": mid, "model": model, "input": int(u.get("input_tokens") or 0),
            "cache_read": int(u.get("cache_read_input_tokens") or 0), "cache_write": write, "cache_write_1h": w1h,
            "output": int(u.get("output_tokens") or 0)}


def _json_from_text(text):
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t)
    try:
        v = json.loads(t)
        return v if isinstance(v, dict) else None
    except ValueError:
        a, b = t.find("{"), t.rfind("}")
        if 0 <= a < b:
            try:
                v = json.loads(t[a:b + 1])
                return v if isinstance(v, dict) else None
            except ValueError:
                return None
    return None


def parse_stream(text):
    """Parse `claude -p --output-format stream-json --verbose` events.

    Returns {"calls": [per model call usage: input, cache_read, cache_write, cache_write_1h, output], "answer": dict|None,
    "answer_from": str, "is_error": bool, "result_seen": bool, "session_id", "num_turns", "cli_usd", "result_text"}.
    The answer is the result event's structured_output when present, else a StructuredOutput tool call's input, else
    JSON in the result text or in the last assistant text. A call is one model request: the last usage per message id."""
    calls, order, answer, answer_from = {}, [], None, ""
    res = {"is_error": False, "result_seen": False, "session_id": None, "num_turns": None, "cli_usd": None,
           "result_text": None, "result_usage": None}
    last_text = None
    for line in text.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if not isinstance(ev, dict):
            continue
        t = ev.get("type")
        if t == "system" and ev.get("session_id"):
            res["session_id"] = ev["session_id"]
        elif t == "assistant" and isinstance(ev.get("message"), dict):
            m = ev["message"]
            mid = m.get("id") or f"anon{len(order)}"
            if isinstance(m.get("usage"), dict):
                if mid not in calls:
                    order.append(mid)
                calls[mid] = _usage_row(m["usage"], mid, m.get("model"))
            for blk in m.get("content") or []:
                if not isinstance(blk, dict):
                    continue
                if blk.get("type") == "tool_use" and "structured" in str(blk.get("name", "")).lower() \
                        and isinstance(blk.get("input"), dict) and answer is None:
                    answer, answer_from = blk["input"], "tool_use"
                if blk.get("type") == "text" and blk.get("text"):
                    last_text = blk["text"]
        elif t == "result":
            res.update(result_seen=True, is_error=bool(ev.get("is_error")), num_turns=ev.get("num_turns"),
                       cli_usd=ev.get("total_cost_usd"), result_text=ev.get("result"),
                       session_id=ev.get("session_id") or res["session_id"])
            if isinstance(ev.get("usage"), dict):
                res["result_usage"] = _usage_row(ev["usage"])
            so = ev.get("structured_output")
            if isinstance(so, dict):
                answer, answer_from = so, "structured_output"
    if answer is None:
        for src, label in ((res["result_text"], "result_text"), (last_text, "assistant_text")):
            v = _json_from_text(src)
            if v is not None:
                answer, answer_from = v, label
                break
    rows = [calls[m] for m in order]
    if not rows and res["result_usage"]:
        rows = [res["result_usage"]]
    return {"calls": rows, "answer": answer, "answer_from": answer_from, "is_error": res["is_error"],
            "result_seen": res["result_seen"], "session_id": res["session_id"], "num_turns": res["num_turns"],
            "cli_usd": res["cli_usd"], "result_text": res["result_text"]}


# ---------------------------------------------------------------------------------------------------------------
# Prices (jobs/necker-costs/PRICES.json, list price)


ALIASES = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5"}


def load_prices(repo):
    return json.loads((Path(repo) / "jobs/necker-costs/PRICES.json").read_text(encoding="utf-8"))


def price_row(prices, model):
    model = ALIASES.get(str(model), str(model))
    for m in prices.get("models", []):
        if re.search(m["match"], model):
            return m
    return None


def call_usd(prices, model, call):
    """List-price dollars of one model call; None when the model is not in the price table. Cache writes are priced at
    the 1-hour rate for the part the call reports as 1-hour and at the 5-minute rate otherwise. A Haiku 5.5 request
    whose prompt exceeds the long-prompt threshold uses the long-prompt rates."""
    row = price_row(prices, model)
    if row is None:
        return None
    prompt = call["input"] + call["cache_read"] + call["cache_write"]
    rates = row
    if row.get("long_prompt") and prompt > row.get("long_prompt_threshold_tokens", 10 ** 12):
        rates = dict(row, **row["long_prompt"])
    w1h = min(call.get("cache_write_1h") or 0, call["cache_write"])
    w5 = call["cache_write"] - w1h
    return (call["input"] * rates["input"] + call["cache_read"] * rates["cache_read"]
            + w5 * rates["cache_write_5m"] + w1h * rates.get("cache_write_1h", rates["cache_write_5m"])
            + call["output"] * rates["output"]) / 1e6


def forecast_usd(prices, model, prefix_tokens, suffix_tokens, output_tokens, prefix_cached):
    """Forecast for one request: the prefix is read from cache when an earlier request wrote it, else written (5-minute
    rate); the suffix is written (the CLI may or may not cache it; writing is the dearer assumption)."""
    call = {"input": 0, "cache_read": prefix_tokens if prefix_cached else 0,
            "cache_write": suffix_tokens + (0 if prefix_cached else prefix_tokens), "cache_write_1h": 0,
            "output": output_tokens}
    return call_usd(prices, model, call)


# ---------------------------------------------------------------------------------------------------------------
# Answer -> sheet


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def read_csv_file(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), list(rd)


def write_csv_file(path, fields, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def decision_row(answer, prep_row, fields, agent):
    """One decisions.csv row (exactly the prepared column set) from the answer's decision object."""
    d = answer.get("decision") if isinstance(answer.get("decision"), dict) else {}
    row = {k: prep_row.get(k, "") for k in fields}
    for k in fields:
        if k in DECISION_FIELDS_FIXED or k not in d:
            continue
        row[k] = _cell(d[k])
    row["instrument_id"], row["dossier_sha256"], row["agent"] = prep_row["instrument_id"], prep_row["dossier_sha256"], agent
    if row.get("outcome") not in OUTCOMES:
        raise ValueError(f"outcome {row.get('outcome')!r} is not one of {OUTCOMES}")
    return row


def clause_rows(answer, iid, prep_clauses, fields, outcome):
    """clauses.csv rows: for a submit the answer's clauses (clause_id defaults to the prepared one for the scope);
    otherwise the prepared rows, unchanged."""
    if outcome != "submit":
        return [dict(c) for c in prep_clauses]
    by_scope = {c["scope_id"]: c for c in prep_clauses}
    rows = []
    for c in answer.get("clauses") or []:
        base = dict(by_scope.get(c.get("scope_id"), {}))
        row = {k: base.get(k, "") for k in fields}
        for k in fields:
            if k in c:
                row[k] = _cell(c[k])
        if not row.get("clause_id") and base.get("clause_id"):
            row["clause_id"] = base["clause_id"]
        row["instrument_id"] = iid
        rows.append(row)
    return rows


def write_answer_sheet(answer, iid, folder, prep_dec_fields, prep_row, prep_clause_fields, prep_clauses, agent):
    """Write decisions.csv, clauses.csv, RATIONALES.json and ASSESSMENT.json in `folder` from a producer answer. The
    column sets are exactly the prepared sheets'. Raises ValueError when the answer is not a usable sheet."""
    if not isinstance(answer, dict) or not isinstance(answer.get("decision"), dict):
        raise ValueError("the answer has no decision object")
    folder = Path(folder)
    row = decision_row(answer, prep_row, prep_dec_fields, agent)
    crows = clause_rows(answer, iid, prep_clauses, prep_clause_fields, row["outcome"])
    write_csv_file(folder / "decisions.csv", prep_dec_fields, [row])
    write_csv_file(folder / "clauses.csv", prep_clause_fields, crows)
    rat = answer.get("rationales") if isinstance(answer.get("rationales"), dict) else {}
    (folder / "RATIONALES.json").write_text(json.dumps({str(k): str(v) for k, v in rat.items()}, ensure_ascii=False,
                                                        indent=1) + "\n", encoding="utf-8")
    assess = dict(answer.get("assessment") or {}) if isinstance(answer.get("assessment"), dict) else {}
    assess["id"] = iid
    assess.setdefault("outcome", row["outcome"])
    (folder / "ASSESSMENT.json").write_text(json.dumps(assess, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if isinstance(answer.get("status_decision"), dict):
        (folder / "STATUS_DECISION.json").write_text(json.dumps(answer["status_decision"], ensure_ascii=False, indent=1)
                                                     + "\n", encoding="utf-8")
    return row, crows


def check_cells(row, crows):
    """The cell-level parse the kit's apply does (jobs/claim-kit/batch.py _apply_rows): explicit true/false booleans,
    JSON lists and objects of the right type, integer inventory offsets. Returns a list of errors."""
    errs = []
    if row.get("outcome") == "submit":
        for k in DECISION_BOOLS:
            if row.get(k) not in ("true", "false"):
                errs.append(f"decisions.{k}: explicit true/false required")
    for k in DECISION_JSON_LIST + DECISION_JSON_DICT:
        v = row.get(k, "")
        if v == "" and k in ("working_text", "source_notes"):
            continue
        try:
            r = json.loads(v)
        except ValueError:
            errs.append(f"decisions.{k}: not JSON")
            continue
        if not isinstance(r, list if k in DECISION_JSON_LIST else dict):
            errs.append(f"decisions.{k}: wrong JSON type")
    for i, c in enumerate(crows):
        for k in CLAUSE_BOOLS:
            if c.get(k, "") not in ("", "true", "false"):
                errs.append(f"clauses[{i}].{k}: explicit true/false required")
        for k in CLAUSE_JSON_LIST:
            if c.get(k, ""):
                try:
                    if not isinstance(json.loads(c[k]), list):
                        errs.append(f"clauses[{i}].{k}: wrong JSON type")
                except ValueError:
                    errs.append(f"clauses[{i}].{k}: not JSON")
        for k in CLAUSE_INTS:
            if c.get(k, "") and not re.fullmatch(r"\d+", c[k]):
                errs.append(f"clauses[{i}].{k}: integer required")
    return errs


def validate_sheet_folder(folder, iid, prep_dec_fields, prep_row, prep_clause_fields, shared_rationales=None):
    """The conveyor's Batch.validate_sheet checks on a producer folder, without a Batch. Returns (row, clauses, rationales,
    assessment); raises ValueError."""
    folder = Path(folder)
    f, rows = read_csv_file(folder / "decisions.csv")
    if f != prep_dec_fields:
        raise ValueError("decisions.csv header changed")
    if len(rows) != 1 or rows[0].get("instrument_id") != iid:
        raise ValueError("decisions.csv must hold exactly one row, for this order")
    row = rows[0]
    if row.get("dossier_sha256") != prep_row.get("dossier_sha256"):
        raise ValueError("dossier_sha256 differs from the prepared row")
    if row.get("outcome") not in OUTCOMES:
        raise ValueError(f"outcome {row.get('outcome')!r} is not one of {OUTCOMES}")
    f2, crows = read_csv_file(folder / "clauses.csv")
    if f2 != prep_clause_fields:
        raise ValueError("clauses.csv header changed")
    if any(c.get("instrument_id") != iid for c in crows):
        raise ValueError("clauses.csv holds a row for another order")
    rat = json.loads((folder / "RATIONALES.json").read_text(encoding="utf-8"))
    if not isinstance(rat, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in rat.items()):
        raise ValueError("RATIONALES.json must be an object of strings")
    bad = [k for k in rat if not k.startswith(slug(iid) + ".")]
    if bad:
        raise ValueError(f"rationale keys must start with {slug(iid)}.: {bad[:3]}")
    shared = shared_rationales or {}
    for v in list(row.values()) + [x for c in crows for x in c.values()]:
        if isinstance(v, str) and v.startswith("@rationale:"):
            key = v.split(":", 1)[1]
            if key not in rat and key not in shared:
                raise ValueError(f"undefined rationale {key}")
    errs = check_cells(row, crows)
    if errs:
        raise ValueError("; ".join(errs[:4]))
    assess = json.loads((folder / "ASSESSMENT.json").read_text(encoding="utf-8"))
    if assess is not None and (not isinstance(assess, dict) or assess.get("id") not in (None, iid)):
        raise ValueError("ASSESSMENT.json must be one object for this order")
    return row, crows, rat, assess


# ---------------------------------------------------------------------------------------------------------------
# need_more


def serve_need_more(repo, requests, extra_forbidden=(), max_requests=NEED_MAX_REQUESTS, max_bytes=NEED_MAX_BYTES,
                    max_total=NEED_MAX_TOTAL):
    """Serve a worker's named repository files and byte ranges, bounded. Only repository-relative paths that resolve
    inside the repository are served; absolute paths, `..`, symlinks out of the repository, paths under the scratch or
    control folders (extra_forbidden: absolute folders), answer-bearing folders and files (reviews, completion, applied
    and complete versions, decision sheets, filed claims, ledgers) and scratch/control path parts are refused. Returns
    (text, report) where report lists each request's outcome."""
    repo = Path(repo).resolve()
    forb = [Path(p).resolve() for p in extra_forbidden]
    out, report, total = [], [], 0
    reqs = requests if isinstance(requests, list) else []
    for i, r in enumerate(reqs):
        why = None
        path = r.get("path") if isinstance(r, dict) else None
        try:
            start, end = int(r.get("start")), int(r.get("end"))
        except (TypeError, ValueError, AttributeError):
            start = end = None
        if i >= max_requests:
            why = f"more than {max_requests} requests"
        elif not isinstance(path, str) or not path.strip():
            why = "no path"
        elif start is None or start < 0 or end <= start:
            why = "bad byte range"
        else:
            norm = path.replace("\\", "/")
            if norm.startswith("/") or re.match(r"^[A-Za-z]:", norm) or ".." in norm.split("/"):
                why = "only repository-relative paths without .. are served"
            else:
                p = (repo / norm)
                try:
                    rp = p.resolve()
                except OSError:
                    rp = None
                if rp is None or not rp.is_relative_to(repo):
                    why = "path resolves outside the repository"
                elif any(rp == f or rp.is_relative_to(f) for f in forb):
                    why = "path is under the scratch or control folders"
                else:
                    rel = rp.relative_to(repo).as_posix()
                    parts = [x.lower() for x in rel.split("/")]
                    if rel.lower().startswith(FORBIDDEN_PREFIXES):
                        why = "filed claims and decision sheets are not served"
                    elif any(x in FORBIDDEN_PARTS for x in parts[:-1]) or any(FORBIDDEN_DIR_RE.match(x) for x in parts[:-1]):
                        why = "answer-bearing, scratch or control folder"
                    elif parts[-1] in FORBIDDEN_NAMES:
                        why = "answer-bearing file"
                    elif not rp.is_file():
                        why = "not a file"
        if why is None:
            n = min(end - start, max_bytes)
            if total + n > max_total:
                why = f"total served bytes would exceed {max_total}"
        if why:
            out.append(f"--- REFUSED request {i + 1}: {path!r} {start}-{end}: {why} ---")
            report.append({"request": i + 1, "path": path, "served": False, "reason": why})
            continue
        with rp.open("rb") as fh:
            fh.seek(start)
            data = fh.read(min(end - start, max_bytes))
        total += len(data)
        out.append(f"--- SERVED {norm} bytes {start}-{start + len(data)} ---\n{data.decode('utf-8', 'replace')}\n--- END ---")
        report.append({"request": i + 1, "path": norm, "served": True, "bytes": len(data)})
    return "\n".join(out), report


def need_more_suffix(suffix, first_answer_requests, served_text):
    """The second-round user message: the same suffix, then what was asked and what the script served."""
    return (suffix + "\n\n=== NEED_MORE ROUND: you asked for the files below; this is your final answer, so need_more "
            "must now be empty ===\nYOUR REQUESTS: " + json.dumps(first_answer_requests, ensure_ascii=False)
            + "\n" + served_text)
