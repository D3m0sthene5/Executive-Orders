# Proposal: fill `formal_revocation_after_earlier_cessation` from filed claims

**This is a proposal only.** Nothing here edits `jobs/readiness-tracker/tracker.py` or
`research/stage19/code/claim_gate.py`. Pushing a change to the tracker's folder starts the tracker job, so it needs
the coordinator's go-ahead (WORKER_RULES, "Jobs"). Line numbers refer to commit `857313b455`.

## Why the column is blank

`tracker.py` sets the column at lines 745-746 and writes it at line 780:

```python
later_formal = (claim_gate.derived(claim)["formal_revocation_after_earlier_cessation"]
                if v2 and hasattr(claim_gate, "derived") else None)
...
"formal_revocation_after_earlier_cessation": {True: "yes", False: "no"}.get(later_formal, ""),
```

There are two reasons it is blank:

- **Only v2 claims are read.** `claim_gate.derived()` (`research/stage19/code/claim_gate.py:108`) returns `None` for
  any claim whose schema is not v2. Of the 1,527 filed claims, 1,343 are v1, so every one of them gives a blank.
- **Every v2 claim is a cleanup bound.** All 184 v2 claims are the R3 re-tags (task C3). Their whole-order end has
  `date_kind: not_later_than`, so `derived()` returns `None` by design: the first end is unresolved. That is
  correct, and the proposal leaves it unchanged.

The result is 0 of 14,998 orders filled. The design never failed; it was never given a v1 claim to read.

## The smallest change

Add four definitions (about 80 lines) to `tracker.py` and use them for v1 claims that pass the gate. It reads only the claim's own
fields, which have already been through the gate and the claim checker. It reads no text and makes no network
call.

```python
EO_NUM_RE = re.compile(r"\b(?:EO|Executive\s+Orders?)(?:\s*Nos?\.?)?\s*:?\s*(\d{1,5}[A-Z]?)\b")


def is_date(s):
    try:
        return bool(s) and datetime.date.fromisoformat(s).isoformat() == s
    except ValueError:
        return False


def classify_mechanism(text):
    t = (text or "").lower()
    # Negated wording names a mechanism only to deny it ("not a revocation or supersession of EO 9278").
    t = re.sub(r"\b(not|no|neither|nor)\s+(a\s+|an\s+|the\s+)?(express\s+)?(revocation|supersession|revoked|superseded"
               r"|amendment|second end|end)\b[^;.)]*", " ", t)
    if re.search(r"strik|substitut|deletes? (this|the|item)|deletion|amendment by|^amend$|inserts? a different"
                 r"|to read as follows|amended to read", t):
        return "amendment_treated_as_end"
    if "implied" in t:
        return "implied_supersession"
    if re.search(r"revo|supersed|supersess|rescind|rescission", t):
        return "formal"
    if re.search(r"statut|joint res|s\.\s?j\.\s?res|act of congress|legislat|public law|pub\.\s?l", t):
        return "statutory"
    if re.search(r"own[_ -]terms|expir|sunset|fixed[_ ]term|fixed[_ ]period|until|single[_ ]day|fiscal|date[_ ]cap"
                 r"|cessation_date|of term|fixed[_ ]date|fixed[_ ]end|period", t):
        return "own_terms"
    if re.search(r"exhaust|perform|one[_ -]time|self[_ ]executing|dispositive|completed|successor appointed", t):
        return "exhaustion"
    if re.search(r"discontinu|terminat|lapse|abolish|ceased", t):
        return "termination_by_later_instrument_or_body_end"
    if "report" in t:
        return "report_deadline"
    return "other"


def v1_formal_after_cessation(claim):
    """The rule TRACKER_FIX.md proposes for v1 claims, using only the claim's own fields.

    True: the whole-order end is exact and is an own-terms, exhaustion, implied-supersession or termination end
    (not a revocation, and not a route an owner ruling keeps open), and the earliest instrument listed as an
    express revocation or supersession on every operative clause takes effect after that end, without naming a
    different order "as amended" instead of this one (TC09). False: the whole-order end is itself an express
    revocation or supersession, or the earliest such instrument takes effect on or before the end. None otherwise.
    """
    w = claim.get("whole_order_end") if isinstance(claim.get("whole_order_end"), dict) else None
    if not w or not is_date(w.get("date", "")):
        return None
    route = classify_mechanism(" ".join(str(w.get(k, "")) for k in ("mechanism", "mechanism_note", "mechanism_detail")))
    if route == "formal":
        return False
    if route not in ("own_terms", "exhaustion", "implied_supersession", "termination_by_later_instrument_or_body_end"):
        return None
    me = claim.get("instrument_id", "").split(":", 1)[-1]
    clauses = [c for c in claim.get("operative_clauses") or [] if isinstance(c, dict)]
    if not clauses:
        return None
    per = []
    for c in clauses:
        acts = {}
        for e in c.get("later_events") or []:
            if not isinstance(e, dict) or not is_date(str(e.get("effective_date", ""))):
                continue
            mech = " ".join(str(e.get(k, "")) for k in ("mechanism", "mechanism_detail"))
            if classify_mechanism(mech) != "formal":
                continue
            named = set(EO_NUM_RE.findall(mech)) - set(EO_NUM_RE.findall(str(e.get("actor", ""))))
            if "as amended" in mech.lower() and named and me not in named:
                continue  # revokes another (parent) order as amended, not this one by name
            for a in EO_NUM_RE.findall(str(e.get("actor", ""))) or [str(e.get("actor", ""))]:
                acts[a] = min(acts.get(a, "9999"), e["effective_date"])
        per.append(acts)
    common = set.intersection(*[set(a) for a in per])
    if not common:
        return None
    first = min(max(a[x] for a in per) for x in common)
    return first > w["date"]
```

Then replace lines 745-746 with:

```python
        if v2 and hasattr(claim_gate, "derived"):
            later_formal = claim_gate.derived(claim)["formal_revocation_after_earlier_cessation"]
        elif claim is not None and not gate_errors and not contested:
            later_formal = v1_formal_after_cessation(claim)
        else:
            later_formal = None
```

No other line changes. `SUMMARY.json` already counts the `yes` rows (line 884). A `no` row would add a count
beside it: `sum(... == "no")`, one more line, which is optional.

The code above is copied verbatim from `scripts/measure.py` (`EO_NUM_RE`, `is_date`, `classify_mechanism` and
`v1_formal_after_cessation`). `tracker.py` already imports `re`; it needs `import datetime` for `is_date`. The
counts below were measured by running this exact block, and it agrees with `measure.py` on every one of the
1,343 v1 claims. The unit tests are in `scripts/test_measure.py` (cleanup after a sunset is yes, revocation as the end is no, the same day is no, a parent
revoked "as amended" is blank, and a route an owner ruling keeps open is blank).

## What it would write (measured on `857313b455`, `SUMMARY.json` → `tracker_fix_claim_only_rule`)

| Value | v1 claims | Of which ready for human review |
|---|---:|---:|
| `yes`: formally revoked after an earlier end | 32 | 30 |
| `no`: the revocation was the end, or came on or before it | 487 | 456 |
| blank: no exact end, an open route, or no revocation listed on every clause | 824 | 699 |
| v2 claims (unchanged; all bounded) | 184 | n/a |

Two of the 32 `yes` claims and 16 of the 487 `no` claims currently fail the gate. The guard `not gate_errors`
leaves those blank, so the tracker would publish 30 `yes` and 471 `no`.

All 32 `yes` claims are also in this measure's category `formally_revoked_after_evidenced_earlier_end`, with held,
verified bytes on both sides. The measure has 10 further filed-claim rows in that category. Their formal revocation
comes from a disposition note or a Formulario lemma, not from the claim itself, so the claim-only rule leaves them
blank. That is correct for a tracker column, which should rest on reviewed claim fields.

## What it deliberately does not do

- It reads no disposition table or OFR note. The tracker column then never rests on a lead.
- It does not treat a v2 `not_later_than` end as an earlier end (R3). Those 184 claims stay blank. Of them, 145 are
  EO 12553 emergency-board orders, and 140 disclose "functionally spent".
- It does not count a strike-and-insert amendment, a report deadline, or a statute that does not name the order
  as an earlier end. Each of these stays blank until its ruling is wired (D-20261021-strike-and-insert,
  D-20261021-report-deadline, A-20261106-1).
- It changes no status, readiness step, blocker or count other than this column.
