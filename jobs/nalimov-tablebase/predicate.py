"""Zero-token predicates Nalimov shares with Respondendi.

Vendored verbatim from jobs/respondendi-adoption/respondendi.py (branch claude/respondendi-standing-adoption,
commit dd43ba18229278ae18bdb2804d67eb5a81133320, PR #270): `_norm`, `_id_pattern`, `named_end_in`, `_segments`,
`_later_acts`, plus the express_named_revocation parameters of its RULE.md v2. They are copied, not imported, because
PR #270 is not merged; `test_nalimov.PredicateParityTests` proves the copy equals the original whenever
jobs/respondendi-adoption is checked out. Once #270 merges, `load()` prefers the real module and RULE.md.

Nothing here decides a status: the predicates only say whether a held sentence reads as an express, named,
unqualified end, the same test Respondendi applies before it will adopt anything.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

ABBREV = re.compile(r"\b(nos?|secs?|f\.\s?r|u\.\s?s\.\s?c|stat|ex|ord|proc|jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec|e\.\s?o|p\.\s?r)\.")
LABELS = re.compile(r"^\s*([a-z ]+?)\s*(?:by)?\s*:", re.I)
YEAR = re.compile(r"\b(1[789]\d\d|20\d\d)\b")

# RULE.md v2 (respondendi-rule-sha256 of dd43ba1822) "kinds.express_named_revocation", verbatim.
EXPRESS = {
    "status": "no",
    "act_verbs": ["revoke", "supersede", "terminate", "transfer", "other"],
    "ending_verbs": ["revoked", "revoke", "revoking", "superseded", "supersedes", "supersede", "rescinded", "repealed",
                     "terminated"],
    "pre_qualifiers": ["section", "sec ", "secs ", "paragraph", "subsection", "so much of", "that part of", "part of",
                       "parts ", "provisions of", "provision of", "established by", "created by", "issued under",
                       "pursuant to", "as amended by", "which revoked", "revoking", "revoked by", "clause", "schedule ",
                       "sentence of"],
    "qualifiers": ["in part", "so far as", "insofar as", "in so far as", "except", "to the extent", "as of the dates",
                   "partial", "with respect to", "as to ", "as it applies", "as it affects", "in its application",
                   "relating to", "other than", "provided", "subject to", "effective upon", "shall be", "until",
                   "for the period", " not ", "neither", "without revoking", "nothing in", "reinstat", "suspend"],
    "max_provision_chars": 3000,
    "text_bases": ["original", "working"],
    "status_only": True,
}
CUTOFF = "2026-10-14"


def _norm(text):
    t = re.sub(r"[­�]", "", str(text or ""))
    t = re.sub(r"([A-Za-z])-\s*\n\s*([A-Za-z])", r"\1\2", t)            # rejoin words broken at line ends
    t = re.sub(r"\s+", " ", t).lower()
    return ABBREV.sub(lambda m: m.group(1).replace(".", "").replace(" ", "") + " ", t)


def _id_pattern(iid):
    """The order's full printed number: EO:341A matches 341A or 341-A, never 341 or '341 a'; EO:341 never matches 341A."""
    match = re.fullmatch(r"EO:(\d+)([A-Za-z]?)", iid or "")
    if not match:
        return None
    num, suffix = match.group(1), match.group(2).lower()
    tail = (r"-?" + suffix + r"(?![a-z\d])") if suffix else r"(?!\d)(?!-?[a-z]\b)"
    return r"(?<![\d])" + num + tail


def named_end_in(text, iid, kind):
    """Zero-token: a sentence of text introduces iid as 'Executive Order (No.) N', carries an ending verb, no
    qualifier, no partial or relational phrase in the 80 characters before the number, and no 'is amended' between
    the number and the verb; and no sentence naming the order carries a qualifier."""
    pattern = _id_pattern(iid)
    if not pattern:
        return False
    verbs = r"\b(?:" + "|".join(re.escape(v) for v in kind["ending_verbs"]) + r")\b"
    passed = False
    for sentence in re.split(r"(?<=[.;])\s+", _norm(text)):
        hits = list(re.finditer(pattern, sentence))
        if not hits:
            continue
        if any(q in sentence for q in kind["qualifiers"]):
            return False
        for m in hits:
            pre = sentence[max(0, m.start() - 120):m.start()]
            if not re.search(r"(executive orders?|ex ord|e o)\b[^;]{0,120}$", pre):
                continue
            if any(q in pre[-80:] for q in kind["pre_qualifiers"]):
                return False
            verb = re.search(verbs, sentence)
            if not verb:
                continue
            between = sentence[m.end():verb.start()] if verb.start() > m.end() else ""
            if re.search(r"\b(is|are) (hereby )?(further )?amended\b", between):
                return False
            passed = True
    return passed


def _segments(history):
    """Catalog note entries ('Revoked by: EO 13241, December 18, 2001'), one per label."""
    return [seg.strip() for h in history for seg in re.split(r"\||\n|(?<=\d{4}) (?=[a-z ]+ by:)", h) if seg.strip()]


def _later_acts(history, end_date, skip=None):
    """Catalog entries that act on the order after its claimed end (an amendment, continuation, reinstatement,
    suspension or second ending after the end means the claimed end is not the whole story)."""
    year = int(end_date[:4]) if end_date else 9999
    out = []
    for seg in _segments(history):
        if seg == skip or not re.match(r"(amended|continued|reinstated|suspended|superseded|revoked|extended|nullified|rescinded|terminated|modified) by", seg):
            continue
        years = [int(y) for y in YEAR.findall(seg)]
        if years and max(years) > year:
            out.append(seg)
    return out


def _date(value):
    value = str(value or "")
    return value if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) else None


def witness_pattern(actor):
    """Respondendi's second witness: a catalog note entry naming the same actor as ending the order."""
    num = re.sub(r"\D", "", actor or "")
    word = r"(eo|executive order)" if str(actor).startswith("EO:") else r"(proc|proclamation)"
    return re.compile(r"^(revoked|superseded|rescinded|terminated) by: ?" + word + r" ?(no )?" + num + r"\b")


def second_witness(segments, actor):
    pat = witness_pattern(actor)
    return [seg for seg in segments if pat.match(seg) and not re.search(r"\(|\bpart|\bsec|\bsection|in part", seg)]


def respondendi_module(repo=REPO):
    """The real Respondendi module, or None while PR #270 is unmerged in this checkout."""
    path = Path(repo) / "jobs/respondendi-adoption/respondendi.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("nalimov_respondendi", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def express_kind(repo=REPO):
    """The rule's express kind: from the real RULE.md when it is checked out, else the vendored copy."""
    mod = respondendi_module(repo)
    if mod is not None:
        try:
            return mod.parameters(repo)["kinds"]["express_named_revocation"]
        except Exception:  # noqa: BLE001 - a malformed rule falls back to the reviewed copy, and the parity test fails
            return dict(EXPRESS)
    return dict(EXPRESS)
