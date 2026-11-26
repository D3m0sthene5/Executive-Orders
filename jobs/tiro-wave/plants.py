"""Tiro plants: planted controls for blind review sets (coordinator bookkeeping; no legal judgment).

A planted control is a deliberately wrong copy of one submitted claim, mixed into the review set so the wave can
measure whether each blind reviewer catches a known defect. review-prep calls make_controls(); finish asks
names_defect() whether a reviewer's rejection named the planted defect.

To add a kind, write a class with the same four members as DateShift (name, choose(), plant(), words) and register
it in KINDS. Each key entry records its kind, so finish judges every control by the words of its own kind, and keys
written before kinds existed (no "kind" field) are judged as date_shift, which is what they were.
"""
import copy
import hashlib
import json
import random

DEFAULT_KIND = 'date_shift'
SEED_PREFIX = 'bartolus-controls:'   # unchanged since Bartolus so a batch name draws the same controls as before
CLAIMS_PER_CONTROL = 15


def control_count(n_claims, per=CLAIMS_PER_CONTROL):
    """max(1, round(n/15)) controls for a non-empty set (Python rounds halves to even, as the old script did)."""
    return max(1, round(n_claims / per)) if n_claims else 0


def shift_date(d, years=3):
    """YYYY-MM-DD... moved back `years` years; 29 February becomes 28 February; anything else is returned unchanged."""
    if not isinstance(d, str) or len(d) < 10 or not d[:4].isdigit():
        return d
    md = d[4:10]
    md = '-02-28' if md == '-02-29' else md
    return f'{int(d[:4]) - years:04d}{md}{d[10:]}'


def _has_end(c):
    return bool((isinstance(c.get('whole_order_end'), dict) and c['whole_order_end'].get('date')) or any(
        isinstance(x.get('first_end'), dict) and x['first_end'].get('date') for x in c.get('operative_clauses', [])))


def _has_event(c):
    return any(isinstance(e, dict) and (e.get('effective_date') or e.get('date'))
               for x in c.get('operative_clauses', []) for e in x.get('later_events', []))


class DateShift:
    """Today's plant: dates moved back three years. Mode 'end' (every first_end and whole_order_end date) when any
    claim has an end date; else 'event' (every later_events date); else 'signing' (every signing_date)."""
    name = 'date_shift'
    words = ('date', 'first_end', 'whole_order_end', 'signing', 'later_event', 'effective', 'year')
    DEFECT = {'end': 'every first_end and whole_order_end date moved back three years',
              'event': 'every later_events effective date moved back three years',
              'signing': 'every signing_date of the order moved back three years'}

    def choose(self, claims):
        """(mode, eligible claims) for this set."""
        elig = [c for c in claims if _has_end(c)]
        if elig:
            return 'end', elig
        elig = [c for c in claims if _has_event(c)]
        if elig:
            return 'event', elig
        return 'signing', list(claims)

    def plant(self, claim, mode):
        """(planted copy, number of fields changed)."""
        p = copy.deepcopy(claim)
        n = 0
        if mode == 'end':
            we = p.get('whole_order_end')
            if isinstance(we, dict) and we.get('date'):
                we['date'] = shift_date(we['date'])
                n += 1
            for x in p.get('operative_clauses', []):
                fe = x.get('first_end')
                if isinstance(fe, dict) and fe.get('date'):
                    fe['date'] = shift_date(fe['date'])
                    n += 1
        elif mode == 'event':
            for x in p.get('operative_clauses', []):
                for e in x.get('later_events', []):
                    for k in ('effective_date', 'date'):
                        if isinstance(e, dict) and e.get(k):
                            e[k] = shift_date(e[k])
                            n += 1
        else:
            def walk(o):
                nonlocal n
                if isinstance(o, dict):
                    for k in list(o):
                        if k == 'signing_date' and isinstance(o[k], str):
                            o[k] = shift_date(o[k])
                            n += 1
                        else:
                            walk(o[k])
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(p)
        return p, n

    def defect(self, mode):
        return self.DEFECT[mode]

    def type(self, mode):
        return 'date_shift_' + mode


KINDS = {DateShift.name: DateShift()}


def make_controls(claims, batch, kind=DEFAULT_KIND, per=CLAIMS_PER_CONTROL, seed_prefix=SEED_PREFIX):
    """Plant controls in one batch's submitted claims.

    Returns {'mode', 'kind', 'review_rows' (claims in file order, controls replaced by their planted copies),
    'genuine' (the real versions of the controls), 'controls' (key entries: instrument_id, planted and genuine
    claim hashes, defect, type, kind)}. The draw is seeded by the batch name, so a rerun picks the same orders."""
    if kind not in KINDS:
        raise ValueError(f'unknown plant kind {kind!r}; known: {", ".join(sorted(KINDS))}')
    k = KINDS[kind]
    mode, elig = k.choose(claims)
    n = control_count(len(claims), per)
    rng = random.Random(hashlib.sha256((seed_prefix + batch).encode()).hexdigest())
    picks = {c['instrument_id'] for c in rng.sample(sorted(elig, key=lambda c: c['instrument_id']), min(n, len(elig)))}
    rows, genuine, controls = [], [], []
    for c in claims:
        if c['instrument_id'] not in picks:
            rows.append(c)
            continue
        p, changed = k.plant(c, mode)
        if not changed:
            raise ValueError(f'plant {kind}/{mode} changed nothing in {c["instrument_id"]}')
        rows.append(p)
        genuine.append(c)
        controls.append({'instrument_id': c['instrument_id'], 'planted': _canon(p), 'genuine': _canon(c),
                         'defect': k.defect(mode), 'type': k.type(mode), 'kind': kind})
    return {'mode': mode, 'kind': kind, 'review_rows': rows, 'genuine': genuine, 'controls': controls}


def kind_of(control):
    return control.get('kind') or DEFAULT_KIND


def names_defect(record, control):
    """True when a review record rejected the claim and its defects or reasons use one of the control kind's words."""
    if not record or record.get('verdict') != 'rejected':
        return False
    text = json.dumps([record.get('defects', []), record.get('reasons', ''), record.get('reason', '')],
                      ensure_ascii=False).lower()
    return any(w in text for w in KINDS[kind_of(control)].words)


def _canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
