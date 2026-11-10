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
import re
import sys
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


def _editorial(rec):
    """status_overlay refuses the 1989 OFR codification snapshot as a status basis."""
    meta = rec.get("meta") if isinstance(rec.get("meta"), dict) else {}
    return "ofr_codification_1989_in_force" in (rec.get("basis_code"), meta.get("basis_code"))


def _basis(rec):
    """A record status_overlay would accept as a basis: exact held evidence, not a report deadline, not editorial."""
    return _held(rec) and rec.get("kind") != "report_deadline" and not _editorial(rec)


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


class KitRules:
    """The claim kit's own freeze-time rules, used when this checkout carries them (Whitworth I2).

    - ``own_text``: Accursius F5 (PR 274) ``own_text.records(iid, original, clauses)`` frames OWN_TEXT /
      PARENT_END records from an order's own words at freeze time.
    - ``working_text_basis``: Accursius F6 (PR 276) ``status_overlay.working_text_basis(dossier)`` says which
      ruling lets a non-original text carry an undecided status.
    On a kit that predates them they are absent and the gates follow the older rules. Nothing here copies them:
    when the kit's rules change, the gates change with them.
    """

    def __init__(self, kit_dir=None, own_text=None, working_text_basis=None):
        self.own_text, self.working_text_basis, self.loaded = own_text, working_text_basis, []
        if kit_dir is None:
            return
        kit_dir = Path(kit_dir)
        if str(kit_dir) not in sys.path:
            sys.path.insert(0, str(kit_dir))
        if self.own_text is None and (kit_dir / "own_text.py").is_file():
            try:
                import own_text
                self.own_text = own_text.records
                self.loaded.append("own_text.records")
            except Exception as exc:          # reported in SUMMARY.json, never guessed around
                self.loaded.append("own_text.records unavailable: %s" % exc)
        if self.working_text_basis is None and (kit_dir / "status_overlay.py").is_file():
            try:
                import status_overlay
                fn = getattr(status_overlay, "working_text_basis", None)
                if fn is not None:
                    self.working_text_basis = fn
                    self.loaded.append("status_overlay.working_text_basis")
            except Exception as exc:
                self.loaded.append("status_overlay unavailable: %s" % exc)


def _apply_rules(iid, orig, clauses, dossier, kinds, rules):
    """Undecided route: a credited working text (F6) and own-text basis records (F5), by the kit's own functions.

    Adds the basis kinds own_text finds to ``kinds``; returns whether working_text_basis credits the text."""
    wtb = False
    if rules is None or not orig:
        return wtb
    if rules.working_text_basis is not None and not orig.get("acceptable_as_original"):
        try:
            wtb = rules.working_text_basis(dossier) is not None
        except (KeyError, TypeError, ValueError):
            wtb = False
    if rules.own_text is not None and orig.get("text") and not kinds:
        for k in rules.own_text(iid, orig, clauses or []) or {}:
            if str(k).startswith(BASIS_PREFIXES):
                kinds.add(str(k).split(":", 1)[0])
    return wtb


def from_dossier(d, status=None, rules=None):
    """Features of one claim-kit dossier (a compiled decided dossier, or a frozen overlay base_dossier)."""
    recs = d.get("evidence") or {}
    orig = recs.get(d.get("original_source_id") or "") if d.get("original_source_id") else None
    kinds, actor_text, notice = set(), False, False
    for k, v in recs.items():
        if not isinstance(v, dict):
            continue
        if k.startswith(NOTICE_PREFIXES) and _held(v):
            notice = True
        # An ACT's effective-wording record (ACT:...:effective#n) starts with ACT: and is exact held text, so
        # status_overlay accepts it like its parent; it is counted the same way.
        if k.startswith(BASIS_PREFIXES) and _basis(v):
            kinds.add(k.split(":", 1)[0])
            if k.startswith("ACTOR_TEXT:"):
                actor_text = True
    clauses = sum(1 for k in recs if k.startswith("CLAUSES:"))
    if status is None:
        status = d.get("whole_order_status")
    wtb = False
    if status not in ("yes", "no"):
        wtb = _apply_rules(d.get("instrument_id"), orig, d.get("clauses"), d, kinds, rules)
    f = _features(d.get("instrument_id"), status, orig, clauses, kinds, actor_text, notice,
                  original_text=(orig or {}).get("text"),
                  working_confirmation=d.get("working_text_confirmation") is not None,
                  current_leads=len(d.get("current_law_leads") or []))
    f["working_text_basis"] = f["working_text_basis"] or wtb
    return f


def from_overlay(inputs, terms, acts, clause, actor_ok, lead=None, rules=None, read_text=None):
    """Features of one undecided order from its compiled overlay records (the build.package assembly).

    actor_ok(actor_id) -> True when the actor has a compiled selected text that package() would frame as an
    ACTOR_TEXT record (a CLAUSES source, and not an overflow actor text). read_text(rel) -> the held text, read
    only when the kit's own-text rule (F5) must look at the order's words and no other basis is held.
    """
    iid = inputs["instrument_id"]
    orig = inputs.get("selected") or None
    kinds = set()
    for t in terms:
        if _basis(t):
            kinds.add("TERM")
    actors = set(inputs.get("known_actor_ids") or [])
    for a in acts:
        actors.add(a.get("actor_id"))
        for v in [a] + list(a.get("alternative_provisions") or []):
            if _basis(dict(v, source=v.get("actor_source"), text=v.get("provision_text"))):
                kinds.add("ACT")
    actor_text = any(isinstance(x, str) and actor_ok(x) for x in actors)
    if actor_text:
        kinds.add("ACTOR_TEXT")
    current = 0
    for frag in (lead or {}).get("current_law_leads") or []:
        # build.package frames CURRENT:{iid}#{n} from a lead with exact text, offsets and a source (F3's leads).
        if isinstance(frag, dict) and all(k in frag for k in ("text", "char_start", "char_end", "source")) \
                and _basis(frag):
            kinds.add("CURRENT")
        current += 1
    nclauses = len((clause or {}).get("clauses") or [])
    wtb = False
    if orig and rules is not None:
        original = {"text": None, "char_start": 0, "char_end": 0, "source": orig.get("source"),
                    "signing_date": orig.get("signing_date"), "grade": orig.get("grade"),
                    "acceptable_as_original": bool(orig.get("acceptable_as_original")),
                    "requires_page_check": bool(orig.get("requires_page_check"))}
        if rules.own_text is not None and not kinds and read_text is not None and orig.get("text_path"):
            original["text"] = read_text(orig["text_path"])
            original["char_end"] = len(original["text"] or "")
        dossier = {"instrument_id": iid, "original_source_id": "O", "evidence": {"O": original}}
        if inputs.get("working_text_confirmation") is not None:
            dossier["working_text_confirmation"] = inputs["working_text_confirmation"]
        wtb = _apply_rules(iid, original, (clause or {}).get("clauses"), dossier, kinds, rules)
    f = _features(iid, None, orig, nclauses, kinds, actor_text, False,
                  working_confirmation=inputs.get("working_text_confirmation") is not None,
                  current_leads=current)
    f["working_text_basis"] = f["working_text_basis"] or wtb
    return f


def _shards(out, stem):
    files = [out / (stem + ".jsonl")] + sorted(Path(p) for p in glob.glob(str(out / (stem + ".part*.jsonl"))))
    for f in files:
        if not f.exists():
            continue
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    yield json.loads(line)


CODE_KIT = Path(__file__).resolve().parents[1] / "claim-kit"


def load(repo, out_rel=KIT_OUT, rules=None):
    """{instrument_id: features} for every decided dossier and every undecided overlay input.

    rules: KitRules; by default the claim kit next to this file (the code, not the data checkout)."""
    rules = KitRules(CODE_KIT) if rules is None else rules
    out = Path(repo) / out_rel
    result = {}
    for p in sorted((out / "dossiers").glob("*.json")):
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        result[d["instrument_id"]] = from_dossier(d, rules=rules)
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

    def read_text(rel):
        try:
            return (Path(repo) / rel).read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            return None

    for iid, r in inputs.items():
        result[iid] = from_overlay(r, terms.get(iid, []), acts.get(iid, []), clause_rows.get(iid), actor_ok,
                                   leads.get(iid), rules=rules, read_text=read_text)
    return result
