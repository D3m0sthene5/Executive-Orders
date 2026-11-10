"""Per-order dispatch inputs read from claim-kit's compiled outputs, for the Larrey triage gates.

Larrey (jobs/larrey-triage) asks, before any agent is sent to an order, whether the order holds every input its
route needs. The answers come from the same records the claim kit would freeze into that order's dossier:

- a decided order: its compiled dossier, jobs/claim-kit/output/dossiers/<EO_n>.json;
- an undecided order: the compiled overlay inputs (OVERLAY_INPUTS, OWN_TERMS, ACTING_PROVISIONS, CLAUSES and
  STATUS_LEADS), read the way status_overlay assembles them (build.package: ORIGINAL, CLAUSES, TERM, ACT,
  ACTOR_TEXT and CURRENT records).

Standard library only, no model tokens, nothing written. A feature is a fact about held records, never a status:
"no ending record held" means the route cannot accept a NO from this dossier today, not that the order is in force.
"""
import glob
import json
import os
import re
from pathlib import Path

KIT_OUT = "jobs/claim-kit/output"
# Record kinds status_overlay accepts as a basis (status_overlay._decision_errors). OWN_TEXT and PARENT_END are
# Accursius F5's own-text records (PR 274); counted when a dossier carries them, so the gate follows that route.
BASIS_PREFIXES = ("ACT:", "TERM:", "ACTOR_TEXT:", "CURRENT:", "OWN_TEXT:", "PARENT_END:")
ACTOR_TEXT_MAX_BYTES = 50000          # build.package: a larger actor text gets an overflow pointer, not an id
# working_text.GRADES (claim-kit), copied so that this module needs no claim-kit import; test_kit_features
# checks the copy against the kit's own set.
WORKING_GRADES = frozenset({"government_printed_reproduction", "government_printed_copy", "compiled_transcription",
                            "compiled_transcription_lead", "archival_replica_scan_pending_codebook",
                            "machine_read_government_printed_copy", "mirror_transcription"})
# National Emergencies Act, 50 U.S.C. 1622(d): a declared emergency ends on its anniversary unless continued by a
# notice. An order that rests on an emergency declared before 2025-10-14 needs a continuation notice through the
# 2026-10-14 cutoff. The words below find orders that invoke such an emergency; they decide nothing.
EMERGENCY = re.compile(r"national emergency|International Emergency Economic Powers|National Emergencies Act", re.I)
NEA_BEFORE = "2025-10-14"
NOTICE_PREFIXES = ("NOTICE:", "NEA_NOTICE:")


def _held(rec):
    """An exact held record, as status_overlay requires of a basis: a source with a text path, and text."""
    if not isinstance(rec, dict):
        return False
    src = rec.get("source")
    return isinstance(src, dict) and bool(src.get("text_path")) and bool(rec.get("text"))


def _features(iid, status, orig, clauses, basis_kinds, actor_text, notice_held, original_text=None,
              working_confirmation=False, current_leads=0):
    grade = (orig or {}).get("grade") or ((orig or {}).get("source") or {}).get("grade")
    signing = (orig or {}).get("signing_date") or ""
    emergency = bool(original_text) and bool(EMERGENCY.search(original_text)) and bool(signing) and signing < NEA_BEFORE
    return {
        "instrument_id": iid, "status": status,
        "has_original": bool(orig),
        "original_acceptable": bool((orig or {}).get("acceptable_as_original")),
        # Accursius F6 (PR 276) freezes working_text_basis on an undecided original the rulings credit.
        "working_text_basis": bool((orig or {}).get("working_text_basis")),
        "working_text_grade": grade in WORKING_GRADES,
        "working_text_confirmation": bool(working_confirmation),
        "original_grade": grade,
        "page_check_owed": bool((orig or {}).get("requires_page_check")),
        "clauses": int(clauses),
        "basis_kinds": sorted(basis_kinds),
        "actor_text": bool(actor_text),
        "emergency_needs_notice": emergency,
        "notice_held": bool(notice_held),
        "current_leads": int(current_leads),
    }


def from_dossier(d, status=None):
    """Features of one claim-kit dossier (a compiled decided dossier, or a frozen overlay base_dossier)."""
    recs = d.get("evidence") or {}
    orig = recs.get(d.get("original_source_id") or "") if d.get("original_source_id") else None
    kinds, actor_text, notice = set(), False, False
    for k, v in recs.items():
        if not isinstance(v, dict) or ":effective#" in k:
            continue
        if k.startswith(NOTICE_PREFIXES) and _held(v):
            notice = True
        if k.startswith(BASIS_PREFIXES) and _held(v) and v.get("kind") != "report_deadline":
            kinds.add(k.split(":", 1)[0])
            if k.startswith("ACTOR_TEXT:"):
                actor_text = True
    clauses = sum(1 for k in recs if k.startswith("CLAUSES:"))
    if status is None:
        status = d.get("whole_order_status")
    return _features(d.get("instrument_id"), status, orig, clauses, kinds, actor_text, notice,
                     original_text=(orig or {}).get("text"),
                     working_confirmation=d.get("working_text_confirmation") is not None,
                     current_leads=len(d.get("current_law_leads") or []))


def from_overlay(inputs, terms, acts, clause, actor_ok, lead=None):
    """Features of one undecided order from its compiled overlay records (the build.package assembly).

    actor_ok(actor_id) -> True when the actor has a compiled selected text that package() would frame as an
    ACTOR_TEXT record (a CLAUSES source, and not an overflow actor text).
    """
    iid = inputs["instrument_id"]
    orig = inputs.get("selected") or None
    kinds = set()
    for t in terms:
        if _held(t) and t.get("kind") != "report_deadline":
            kinds.add("TERM")
    actors = set(inputs.get("known_actor_ids") or [])
    for a in acts:
        actors.add(a.get("actor_id"))
        for v in [a] + list(a.get("alternative_provisions") or []):
            if _held({"source": v.get("actor_source"), "text": v.get("provision_text")}):
                kinds.add("ACT")
    actor_text = any(isinstance(x, str) and actor_ok(x) for x in actors)
    if actor_text:
        kinds.add("ACTOR_TEXT")
    current = 0
    for frag in (lead or {}).get("current_law_leads") or []:
        if isinstance(frag, dict) and all(k in frag for k in ("text", "char_start", "char_end", "source")) \
                and _held(frag):
            kinds.add("CURRENT")
        current += 1
    nclauses = len((clause or {}).get("clauses") or [])
    return _features(iid, None, orig, nclauses, kinds, actor_text, False,
                     working_confirmation=inputs.get("working_text_confirmation") is not None,
                     current_leads=current)


def _shards(out, stem):
    files = [out / (stem + ".jsonl")] + sorted(Path(p) for p in glob.glob(str(out / (stem + ".part*.jsonl"))))
    for f in files:
        if not f.exists():
            continue
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    yield json.loads(line)


def load(repo, out_rel=KIT_OUT):
    """{instrument_id: features} for every decided dossier and every undecided overlay input."""
    out = Path(repo) / out_rel
    result = {}
    for p in sorted((out / "dossiers").glob("*.json")):
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        result[d["instrument_id"]] = from_dossier(d)
    inputs = {r["instrument_id"]: r for r in _shards(out, "OVERLAY_INPUTS")}
    if not inputs:
        return result
    want = set(inputs)
    terms, acts, leads = {}, {}, {}
    for r in _shards(out, "OWN_TERMS"):
        if r.get("instrument_id") in want:
            terms.setdefault(r["instrument_id"], []).append(r)
    for r in _shards(out, "ACTING_PROVISIONS"):
        if r.get("target_id") in want:
            acts.setdefault(r["target_id"], []).append(r)
    for r in _shards(out, "STATUS_LEADS"):
        if r.get("instrument_id") in want:
            leads[r["instrument_id"]] = r
    clause_rows, clause_src = {}, set()
    for r in _shards(out, "CLAUSES"):
        i = r.get("instrument_id")
        if isinstance(r.get("source"), dict):
            clause_src.add(i)
        if i in want:
            clause_rows[i] = r          # last compiled row wins, as status_overlay does
    overflow = set()
    for p in (out / "actor-texts").glob("*.json"):
        try:
            with open(p, encoding="utf-8") as fh:
                overflow.add(json.load(fh).get("instrument_id"))
        except ValueError:
            continue

    def actor_ok(a):
        return a in clause_src and a not in overflow

    for iid, r in inputs.items():
        result[iid] = from_overlay(r, terms.get(iid, []), acts.get(iid, []), clause_rows.get(iid), actor_ok,
                                   leads.get(iid))
    return result


def fingerprint(repo, out_rel=KIT_OUT):
    """SHA-256 of the compiled SUMMARY.json the features were read from (None when absent)."""
    import hashlib
    p = Path(repo) / out_rel / "SUMMARY.json"
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
