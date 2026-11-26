"""Tiro plants: planted controls for blind review sets (coordinator bookkeeping; no legal judgment).

A planted control is a deliberately wrong copy of one submitted claim, mixed into the review set so the wave can
measure whether each blind reviewer catches a known defect. review-prep calls make_controls(); finish asks
names_defect() whether a reviewer's rejection named the planted defect.

Four kinds. The three newer ones copy defects that genuine claims were actually rejected for on 2026-11-25, and each
leaves the claim schema-valid, cites only sources the genuine claim already cites (so the claim kit's source, quote
and dossier checks pass wherever the genuine claim passed), and adds no Geddes pre-review flag
(jobs/geddes/prereview_checks.py); test_tiro_plants.py checks all three properties.

- event_drop: one recorded later event (one acting instrument, removed from every clause that records it), with any
  count of such events in the prose lowered by one so the claim stays internally consistent.
- clause_misdescription: one clause's operative effect misdescribed. In a YES claim an ended clause becomes operative
  (its first_end removed, a continuing predicate citing the clause's own text added); in a NO claim a terminated
  clause is recorded as never_activated (or the reverse).
- citation_drop: one cited source of another instrument (and its quote) removed from every slot that cites it; each
  slot falls back to the order's own text, and the conclusion it supported is left unchanged.
- date_shift: the original plant (dates moved back three years). Geddes date_before_signing catches it mechanically,
  so it tests attention rather than judgment; it stays one kind of the rotation.

The kind is chosen deterministically from a seed (default: the batch name) recorded in the key. The default,
'rotation', starts at a seed-dependent place in ROTATION and gives successive controls successive kinds, skipping a
kind no remaining claim can take. Each key entry records its kind, mode, a one-line description of the planted defect
(shown in the reveal step) and the identifiers a rejection must name. Keys written before kinds existed (no "kind"
field) are judged as date_shift, which is what they were.
"""
import base64
import copy
import hashlib
import json
import random
import re

LEGACY_KIND = 'date_shift'
DEFAULT_KIND = 'rotation'
SEED_PREFIX = 'bartolus-controls:'   # unchanged since Bartolus so a batch name draws the same date_shift controls
ROTATION_PREFIX = 'tiro-plant-rotation:'
CLAIMS_PER_CONTROL = 15
LEGAL_CUTOFF = '2026-10-14'
FACT_MARKER = 'norton_factual_event'
ENDED_STATES = ('terminated', 'never_activated')


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


# Shared helpers ----------------------------------------------------------------------------------------------------
def _clauses(c):
    return [x for x in c.get('operative_clauses') or [] if isinstance(x, dict)]


def _has_end(c):
    return bool((isinstance(c.get('whole_order_end'), dict) and c['whole_order_end'].get('date')) or any(
        isinstance(x.get('first_end'), dict) and x['first_end'].get('date') for x in _clauses(c)))


def _has_event(c):
    return any(isinstance(e, dict) and (e.get('effective_date') or e.get('date'))
               for x in _clauses(c) for e in x.get('later_events', []))


def evidence_name(src):
    """The decoded evidence id of a source (ACT:EO:1>EO:2, CLAUSES:EO:1#sec1, ...), or ''."""
    if not isinstance(src, dict):
        return ''
    ident = src.get('evidence_id') or ''
    if src.get('evidence_id_encoding') == 'base64url-utf8' and isinstance(ident, str):
        try:
            return base64.urlsafe_b64decode(ident + '=' * (-len(ident) % 4)).decode('utf-8')
        except (ValueError, UnicodeError):
            return ''
    return ident if isinstance(ident, str) else ''


INSTRUMENT = re.compile(r'\b([A-Z][A-Z_]{1,9}):(\d[\w.-]*\w|\d)')


def foreign_instruments(src, own):
    """Instrument ids (EO:13332, FRDOC:2017-06583) a source's evidence id names other than the claim's own order."""
    names = {f'{a}:{b}' for a, b in INSTRUMENT.findall(evidence_name(src))}
    if isinstance(src, dict) and isinstance(src.get('instrument_id'), str):
        names.add(src['instrument_id'])
    return sorted(n for n in names if n != own)


def _number(ident):
    """'EO:14144' -> '14144'; 'FRDOC:2017-06583' -> '2017-06583'."""
    return ident.split(':', 1)[1] if ':' in ident else ident


def _is_capture_or_derivative(src):
    return isinstance(src, dict) and (src.get('acceptable_as_original') is False or 'grade' in src
                                      or src.get('role') == 'acting_instrument_text' and 'grade' in src)


def _marked(o):
    return isinstance(o, dict) and (FACT_MARKER in o or (isinstance(o.get('source'), dict) and FACT_MARKER in o['source']))


# Prose: the producer-written explanatory fields (as Geddes reads them) ----------------------------------------------
def _map_strings(value, fn, skip=('source', 'quote', 'text', 'actor', 'date', 'mechanism')):
    if isinstance(value, str):
        return fn(value)
    if isinstance(value, list):
        return [_map_strings(v, fn, skip) for v in value]
    if isinstance(value, dict):
        return {k: (v if k in skip else _map_strings(v, fn, skip)) for k, v in value.items()}
    return value


def map_prose(claim, claim_fn, clause_fn=None):
    """Apply claim_fn to claim-level prose and clause_fn(clause, text) to each clause's prose, in place."""
    clause_fn = clause_fn or (lambda clause, t: claim_fn(t))
    if isinstance(claim.get('research_rationale'), str):
        claim['research_rationale'] = claim_fn(claim['research_rationale'])
    sav = claim.get('savings_residuals')
    if isinstance(sav, dict) and isinstance(sav.get('reason'), str):
        sav['reason'] = claim_fn(sav['reason'])
    for k in ('unresolved_material_gaps', 'source_notes'):
        if k in claim:
            claim[k] = _map_strings(claim[k], claim_fn)
    we = claim.get('whole_order_end')
    if isinstance(we, dict):
        for k in list(we):
            if k not in ('actor', 'date', 'mechanism', 'source'):
                we[k] = _map_strings(we[k], claim_fn)
    for x in _clauses(claim):
        if isinstance(x.get('judgment_reason'), str):
            x['judgment_reason'] = clause_fn(x, x['judgment_reason'])
        cp = x.get('current_predicate')
        if isinstance(cp, dict) and isinstance(cp.get('legal_basis'), str):
            cp['legal_basis'] = clause_fn(x, cp['legal_basis'])


def prose_text(claim):
    parts = []
    map_prose(copy.deepcopy(claim), lambda t: parts.append(t) or t)
    return '\n'.join(parts)


NUMBER_WORDS = ('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen '
                'sixteen seventeen eighteen nineteen twenty').split()
NUM = r'(\d{1,2}|' + '|'.join(NUMBER_WORDS) + r')'
ADJ = r'(?:(?:held|annual|Federal\s+Register|later|presidential|NEA|separate|recorded|subsequent|amending)\s+)*'
NOTICE_NOUNS = r'(?:continuation\s+notices?|notices?\s+(?:of\s+)?continu\w*|notices?\s+continuing|notices?\b)'
AMEND_NOUNS = r'(?:amendments?\b|amending\s+(?:orders?|instruments?|executive\s+orders?)\b|amendatory\s+orders?\b)'


def _num_value(tok):
    t = tok.lower()
    return int(t) if t.isdigit() else NUMBER_WORDS.index(t) if t in NUMBER_WORDS else None


def _num_form(old_tok, n):
    if old_tok.isdigit() or n >= len(NUMBER_WORDS):
        return str(n)
    w = NUMBER_WORDS[n]
    return w.capitalize() if old_tok[:1].isupper() else w


def _recount(text, nouns, old, new):
    """Lower every stated count `old` of `nouns` in text to `new`; returns (text, replacements)."""
    pat = re.compile(rf'\b{NUM}(\s+{ADJ}){nouns}', re.I)
    count = 0

    def sub(m):
        nonlocal count
        if _num_value(m.group(1)) != old:
            return m.group(0)
        count += 1
        rest = m.group(0)[len(m.group(1)):]
        if new == 1:
            rest = re.sub(r'(notice|amendment|order|instrument)s\b', r'\1', rest, count=1, flags=re.I)
        return _num_form(m.group(1), new) + rest
    return pat.sub(sub, text), count


def _event_kind(event):
    mech = re.sub(r'[_\s]+', ' ', str(event.get('mechanism') or '').lower()).strip()
    if re.match(r'(?:annual )?continuation (?:of (?:the )?(?:a )?national emergency|notice)|national emergency continuation notice', mech):
        return 'notice'
    if re.search(r'\bamend', mech):
        return 'amendment'
    return 'other'


# Kinds -------------------------------------------------------------------------------------------------------------
class DateShift:
    """Dates moved back three years. Mode 'end' (every first_end and whole_order_end date) when any claim has an end
    date; else 'event' (every later_events date); else 'signing' (every signing_date)."""
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

    # Rotation interface: the set-level mode decides which claims can take it.
    def eligible(self, claim, ctx):
        mode, elig = ctx.setdefault('date_shift', self.choose(ctx['claims']))
        return any(c is claim for c in elig)

    def plant_one(self, claim, rng, ctx):
        mode = ctx['date_shift'][0]
        p, n = self.plant(claim, mode)
        return p, {'mode': mode, 'changed': n, 'defect': self.defect(mode), 'type': self.type(mode), 'match': []}


class EventDrop:
    """One recorded later event dropped (one acting instrument, from every clause recording it), with stated counts
    of that event type in the prose lowered by one. Prefers an instrument the prose never names, and for annual
    notices one that is neither the first nor the last, so no date range in the prose goes stale."""
    name = 'event_drop'
    words = ('later_event', 'omit', 'omission', 'missing', 'missed', 'absent', 'not recorded', 'unrecorded',
             'unaddressed', 'leaves out', 'left out', 'does not record', 'no record', 'not listed', 'unlisted', 'gap')

    def _candidates(self, c):
        own = c.get('instrument_id')
        enders = {x['first_end'].get('actor') for x in _clauses(c) if isinstance(x.get('first_end'), dict)}
        if isinstance(c.get('whole_order_end'), dict):
            enders.add(c['whole_order_end'].get('actor'))
        groups = {}
        for x in _clauses(c):
            for e in x.get('later_events') or []:
                if not isinstance(e, dict) or not e.get('actor') or _marked(e):
                    continue
                groups.setdefault(e['actor'], []).append((x.get('scope_id'), e))
        out = []
        for actor, evs in groups.items():
            if actor in enders or actor == own:
                continue
            out.append(actor)
        return groups, sorted(out)

    def eligible(self, claim, ctx):
        return bool(self._candidates(claim)[1])

    def plant_one(self, claim, rng, ctx):
        groups, cands = self._candidates(claim)
        text = prose_text(claim)
        kinds = {a: _event_kind(groups[a][0][1]) for a in cands}
        notice_dates = sorted({e.get('effective_date') or '' for a in cands if kinds[a] == 'notice' for _, e in groups[a]})

        def mentioned(a):
            if re.search(rf'(?<![\w-]){re.escape(_number(a))}(?![\w-])', text):
                return True
            d = groups[a][0][1].get('effective_date') or ''
            return bool(d) and d in text

        def edge(a):
            d = groups[a][0][1].get('effective_date') or ''
            return kinds[a] == 'notice' and bool(notice_dates) and d in (notice_dates[0], notice_dates[-1])
        best = min((mentioned(a), edge(a)) for a in cands)
        actor = rng.choice([a for a in cands if (mentioned(a), edge(a)) == best])
        kind = kinds[actor]
        same_kind = lambda evs: {e['actor'] for e in evs if isinstance(e, dict) and e.get('actor')
                                 and _event_kind(e) == kind}
        all_events = [e for x in _clauses(claim) for e in x.get('later_events') or []]
        union_old = len(same_kind(all_events))
        per_clause_old = {x.get('scope_id'): len(same_kind(x.get('later_events') or [])) for x in _clauses(claim)}
        p = copy.deepcopy(claim)
        scopes, removed, first = [], 0, groups[actor][0][1]
        for x in _clauses(p):
            keep = [e for e in x.get('later_events') or [] if not (isinstance(e, dict) and e.get('actor') == actor)]
            if len(keep) != len(x.get('later_events') or []):
                removed += len(x['later_events']) - len(keep)
                scopes.append(x.get('scope_id'))
                x['later_events'] = keep
        _refresh_capture_disclosure(p)
        recounts = 0
        if kind in ('notice', 'amendment'):
            nouns = NOTICE_NOUNS if kind == 'notice' else AMEND_NOUNS

            def claim_fn(t):
                nonlocal recounts
                t, k = _recount(t, nouns, union_old, union_old - 1)
                recounts += k
                return t

            def clause_fn(x, t):
                nonlocal recounts
                old = per_clause_old.get(x.get('scope_id'))
                if x.get('scope_id') in scopes and old:
                    t, k = _recount(t, nouns, old, old - 1)
                    recounts += k
                return t
            map_prose(p, claim_fn, clause_fn)
        what = (f"later event {actor} ({first.get('mechanism')}, effective {first.get('effective_date')}) removed from "
                f"{len(scopes)} clause(s) ({', '.join(scopes)})")
        what += (f"; {recounts} stated count(s) in the prose lowered from {union_old} to {union_old - 1}" if recounts
                 else '; no stated count needed changing')
        what += '; the prose still names it' if best[0] else '; the prose does not name it'
        return p, {'mode': kind, 'changed': removed, 'defect': what, 'type': 'event_drop_' + kind,
                   'match': [actor, _number(actor)]}


def _refresh_capture_disclosure(p):
    """Keep fr_fulltext_captures equal to the captures the remaining later events still cite (the kit's rule)."""
    disc = p.get('fr_fulltext_captures')
    if not isinstance(disc, dict) or not isinstance(disc.get('captures'), list):
        return
    cited = set()
    for x in _clauses(p):
        for e in x.get('later_events') or []:
            s = e.get('source') if isinstance(e, dict) else None
            if isinstance(s, dict):
                cited.add(tuple(s.get(k) for k in ('instrument_id', 'url', 'sha256', 'text_path', 'text_sha256')))
    keep = [r for r in disc['captures'] if tuple(r.get(k) for k in ('instrument_id', 'url', 'sha256', 'text_path',
                                                                      'text_sha256')) in cited]
    if keep:
        disc['captures'] = keep
    else:
        p.pop('fr_fulltext_captures')


class ClauseMisdescription:
    """One clause's operative effect misdescribed. YES claim: an ended clause recorded as operative, its first_end
    removed and a continuing predicate citing the clause's own text added (mode ended_to_operative). NO claim: a
    terminated clause recorded as never_activated, or a never_activated clause as terminated (mode state_swap)."""
    name = 'clause_misdescription'
    words = ('state_at_cutoff', 'operative', 'terminated', 'never_activated', 'never activated', 'first_end',
             'current_predicate', 'misdescri', 'ended', 'revoked', 'superseded', 'continuing', 'in force', 'state')
    BASIS = ("The clause's own text sets no end and no held instrument ended it; it is recorded as continuing in force "
             f"through {LEGAL_CUTOFF}.")

    def _candidates(self, c):
        return [x.get('scope_id') for x in _clauses(c) if x.get('state_at_cutoff') in ENDED_STATES
                and isinstance(x.get('first_end'), dict) and isinstance(x.get('original_source'), dict)
                and (c.get('whole_order_status') == 'yes' or x.get('state_at_cutoff') in ENDED_STATES)]

    def eligible(self, claim, ctx):
        return claim.get('whole_order_status') in ('yes', 'no') and bool(self._candidates(claim))

    def plant_one(self, claim, rng, ctx):
        scope = rng.choice(sorted(self._candidates(claim)))
        p = copy.deepcopy(claim)
        x = next(x for x in _clauses(p) if x.get('scope_id') == scope)
        fe = x['first_end']
        if p.get('whole_order_status') == 'yes':
            x['state_at_cutoff'] = 'operative'
            x.pop('first_end')
            x['current_predicate'] = {'checked_through': LEGAL_CUTOFF, 'legal_basis': self.BASIS,
                                      'source': copy.deepcopy(x['original_source'])}
            mode = 'ended_to_operative'
            what = (f"clause {scope} recorded as operative through {LEGAL_CUTOFF}: its first_end ({fe.get('mechanism')} "
                    f"by {fe.get('actor')} on {fe.get('date') or fe.get('latest')}) was removed and a continuing "
                    "predicate citing the clause's own text was added")
        else:
            old = x['state_at_cutoff']
            x['state_at_cutoff'] = 'never_activated' if old == 'terminated' else 'terminated'
            mode = 'state_swap'
            what = (f"clause {scope} recorded as {x['state_at_cutoff']} instead of {old}; its first_end "
                    f"({fe.get('mechanism')} by {fe.get('actor')} on {fe.get('date') or fe.get('latest')}) is unchanged")
        suffix = scope.split('#', 1)[1] if isinstance(scope, str) and '#' in scope else scope
        return p, {'mode': mode, 'changed': 1, 'defect': what, 'type': 'clause_misdescription_' + mode,
                   'match': sorted({scope, suffix})}


class CitationDrop:
    """One cited source of another instrument (and its quote) removed from every first_end, whole_order_end,
    current_predicate, savings_residuals or formal_disposition slot that cites it; each slot falls back to the
    order's own text (the clause's original_source, else original_representation) and the conclusion is unchanged.
    Never a source that a later event, an original_source or the original_representation also cites, a working-text
    or FR-capture source, or a factual-event citation, so the remaining citations stay exactly what the kit accepts."""
    name = 'citation_drop'
    words = ('source', 'cite', 'citation', 'quote', 'evidence', 'support', 'unsupported', 'does not show',
             'does not say', 'own text')
    RANK = {'first_end': 0, 'whole_order_end': 0, 'formal_disposition': 0, 'current_predicate': 1,
            'savings_residuals': 2}

    def _slots(self, c):
        """[(slot path, rank, source, fallback source, setter)]."""
        out = []
        rep = c.get('original_representation')
        for x in _clauses(c):
            for key in ('first_end', 'current_predicate'):
                o = x.get(key)
                if isinstance(o, dict) and isinstance(o.get('source'), dict):
                    out.append((f"operative_clauses[{x.get('scope_id')}].{key}.source", self.RANK[key], o['source'],
                                x.get('original_source'), o))
        for key in ('whole_order_end', 'savings_residuals', 'formal_disposition'):
            o = c.get(key)
            if isinstance(o, dict) and isinstance(o.get('source'), dict):
                out.append((f'{key}.source', self.RANK[key], o['source'], rep, o))
        return out

    def _groups(self, c):
        own = c.get('instrument_id')
        pinned = {evidence_name(c.get('original_representation'))}
        for x in _clauses(c):
            pinned.add(evidence_name(x.get('original_source')))
            for e in x.get('later_events') or []:
                if isinstance(e, dict):
                    pinned.add(evidence_name(e.get('source')))
        groups = {}
        for path, rank, src, fallback, _ in self._slots(c):
            name = evidence_name(src)
            if (not name or name in pinned or not isinstance(fallback, dict) or evidence_name(fallback) == name
                    or _is_capture_or_derivative(src) or FACT_MARKER in src or not foreign_instruments(src, own)):
                continue
            groups.setdefault(name, []).append((path, rank))
        # A source is removable only if every slot citing it can fall back.
        for path, rank, src, fallback, _ in self._slots(c):
            name = evidence_name(src)
            if name in groups and not any(p == path for p, _ in groups[name]):
                groups.pop(name)
        return groups

    def eligible(self, claim, ctx):
        return bool(self._groups(claim))

    def plant_one(self, claim, rng, ctx):
        groups = self._groups(claim)
        best = min(min(r for _, r in v) for v in groups.values())
        name = rng.choice(sorted(k for k, v in groups.items() if min(r for _, r in v) == best))
        p = copy.deepcopy(claim)
        removed, label = [], None
        for path, rank, src, fallback, holder in self._slots(p):
            if evidence_name(src) == name:
                label = label or src.get('page_or_item')
                holder['source'] = copy.deepcopy(fallback)
                removed.append(path)
        foreign = foreign_instruments(next(s for _, _, s, _, _ in self._slots(claim) if evidence_name(s) == name),
                                      claim.get('instrument_id'))
        slot_names = sorted({re.sub(r'^operative_clauses\[[^\]]*\]\.', '', r) for r in removed})
        what = (f"cited source {', '.join(foreign)} ({label}) and its quote removed from {len(removed)} slot(s) "
                f"({', '.join(slot_names)}); each now cites the order's own text and the conclusion is unchanged")
        return p, {'mode': slot_names[0].split('.')[0], 'changed': len(removed), 'defect': what,
                   'type': 'citation_drop_' + slot_names[0].split('.')[0],
                   'match': sorted(set(foreign) | {_number(f) for f in foreign} | set(slot_names))}


KINDS = {k.name: k for k in (EventDrop(), ClauseMisdescription(), CitationDrop(), DateShift())}
ROTATION = ('event_drop', 'clause_misdescription', 'citation_drop', 'date_shift')


def rotation_order(seed):
    start = int(hashlib.sha256((ROTATION_PREFIX + seed).encode()).hexdigest(), 16) % len(ROTATION)
    return list(ROTATION[start:] + ROTATION[:start])


def make_controls(claims, batch, kind=DEFAULT_KIND, per=CLAIMS_PER_CONTROL, seed_prefix=SEED_PREFIX, seed=None):
    """Plant controls in one batch's submitted claims.

    kind is 'rotation' (default) or one kind name. seed defaults to the batch name; the same seed draws the same
    orders and the same kinds every time. Returns {'mode', 'kind', 'seed', 'rotation', 'review_rows' (claims in file
    order, controls replaced by their planted copies), 'genuine' (the real versions of the controls), 'controls' (key
    entries: instrument_id, planted and genuine claim hashes, kind, mode, type, defect, match)}.

    kind='date_shift' draws exactly the orders the pre-rotation tool drew for the same batch name."""
    seed = seed or batch
    if kind != DEFAULT_KIND and kind not in KINDS:
        raise ValueError(f'unknown plant kind {kind!r}; known: {DEFAULT_KIND}, {", ".join(sorted(KINDS))}')
    n = control_count(len(claims), per)
    rng = random.Random(hashlib.sha256((seed_prefix + seed).encode()).hexdigest())
    planted = {}
    if kind == 'date_shift':
        k = KINDS[kind]
        mode, elig = k.choose(claims)
        for c in rng.sample(sorted(elig, key=lambda c: c['instrument_id']), min(n, len(elig))):
            p, changed = k.plant(c, mode)
            planted[c['instrument_id']] = (p, {'mode': mode, 'changed': changed, 'defect': k.defect(mode),
                                               'type': k.type(mode), 'match': []}, kind)
        order = [kind]
    else:
        order = rotation_order(seed) if kind == DEFAULT_KIND else [kind]
        ctx = {'claims': claims}
        for i in range(n):
            for j in range(len(order)):
                kname = order[(i + j) % len(order)]
                k = KINDS[kname]
                elig = sorted((c for c in claims if c['instrument_id'] not in planted and k.eligible(c, ctx)),
                              key=lambda c: c['instrument_id'])
                if elig:
                    c = rng.choice(elig)
                    p, info = k.plant_one(c, rng, ctx)
                    planted[c['instrument_id']] = (p, info, kname)
                    break
            else:
                if kind != DEFAULT_KIND:
                    raise ValueError(f'plant kind {kind} fits no claim in {batch}')
    rows, genuine, controls = [], [], []
    for c in claims:
        if c['instrument_id'] not in planted:
            rows.append(c)
            continue
        p, info, kname = planted[c['instrument_id']]
        if not info['changed'] or _canon(p) == _canon(c):
            raise ValueError(f'plant {kname}/{info["mode"]} changed nothing in {c["instrument_id"]}')
        rows.append(p)
        genuine.append(c)
        entry = {'instrument_id': c['instrument_id'], 'planted': _canon(p), 'genuine': _canon(c),
                 'defect': info['defect'], 'type': info['type'], 'kind': kname, 'mode': info['mode']}
        if info['match']:
            entry['match'] = info['match']
        controls.append(entry)
    modes = sorted({k['mode'] for k in controls})
    return {'mode': ','.join(modes), 'kind': kind, 'seed': seed, 'rotation': order, 'review_rows': rows,
            'genuine': genuine, 'controls': controls}


def kind_of(control):
    return control.get('kind') or LEGACY_KIND


def _has_token(text, token):
    return re.search(rf'(?<![\w-]){re.escape(token.lower())}(?![\w-])', text) is not None


def names_defect(record, control):
    """True when a review record rejected the claim and its defects or reasons name the planted defect: for a key
    entry with 'match' identifiers, one of them (the dropped instrument, the misdescribed clause, the removed source)
    and one of the kind's words; otherwise one of the kind's words."""
    if not record or record.get('verdict') != 'rejected':
        return False
    text = json.dumps([record.get('defects', []), record.get('reasons', ''), record.get('reason', '')],
                      ensure_ascii=False).lower()
    words = any(w in text for w in KINDS[kind_of(control)].words)
    if control.get('match'):
        return words and any(_has_token(text, t) for t in control['match'])
    return words


def _canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
