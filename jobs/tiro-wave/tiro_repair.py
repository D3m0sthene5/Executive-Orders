"""Tiro fix-and-recheck (owner rule, 2026-11-25; coordinator bookkeeping, no legal judgment).

The rule the owner approved: when a reviewer rejects a claim for a specific LOCAL defect (a wrong page label, one
misdescribed clause), the producer may fix only that defect and the rejecting reviewer re-checks only that point,
with the other reviewer's uphold carried over if nothing else in the claim changed. A claim whose fix touches anything
beyond the flagged point still needs both reviewers again. Planted controls are never repairable, and a claim both
arms rejected is not repairable under this rule.

repair_prep()  lists the genuine claims exactly one arm rejected, with only LOCAL defects of a repairable class, and
               writes the producer repair prompt (scratch only).
repair_check() diffs each repaired claim against the reviewed version and accepts it only if every changed path lies
               inside the flagged anchors and is a field FIELD_MAP allows for the defect's class. It writes the
               carried uphold (REPAIR_CARRIED_<arm>.jsonl), the re-check prompt and set, and REPAIR_RECEIPT.json.
verify_receipt() is what finish runs before it counts a repaired claim (tiro_finish.pair_rule, repairs=...).
"""
import copy
import json
import re
from pathlib import Path

import tiro_common as C
from tiro_common import PROMPTS, TiroError, load_jsonl, render, write_jsonl

RULE = ("Owner 2026-11-25 (AskUserQuestion, answer \"Yes\"): when a reviewer rejects a claim for a specific local "
        "defect, the producer may fix only that defect and the rejecting reviewer re-checks only that point, with the "
        "other reviewer's uphold carried over if nothing else in the claim changed; a claim whose fix touches anything "
        "beyond the flagged point still needs both reviewers again.")
ARMS = 'AB'
CLASSES = ('date', 'omission', 'misdescription', 'citation', 'page_label', 'convention', 'other')
LOCALITIES = ('LOCAL', 'STRUCTURAL')
PROSE = frozenset({'research_rationale', 'judgment_reason', 'legal_basis', 'reason', 'mechanism_note'})

# What a fix for each defect class may change, inside the anchors (the clause or top-level field) the defect's
# `fields` name. `leaf`: the last key of a changed path; `subtree`: any key on the path below the anchor; `derived`:
# claim-level disclosures the kit recomputes from the edited sources. convention and other have no entry: a defect of
# those classes is never repairable under this rule.
FIELD_MAP = {
    'page_label': {'leaf': frozenset({'page_or_item', 'evidence_id', 'char_start', 'char_end', 'location_confidence',
                                      'location_verified', 'requires_page_check'}),
                   'subtree': frozenset(), 'derived': frozenset()},
    'date': {'leaf': frozenset({'date', 'effective_date', 'earliest', 'latest', 'date_kind', 'checked_through'}) | PROSE,
             'subtree': frozenset(), 'derived': frozenset()},
    'misdescription': {'leaf': frozenset({'state_at_cutoff', 'mechanism', 'mechanism_note', 'first_cause', 'actor'}) | PROSE,
                       'subtree': frozenset({'first_end', 'current_predicate'}), 'derived': frozenset()},
    'omission': {'leaf': PROSE, 'subtree': frozenset({'later_events'}), 'derived': frozenset({'fr_fulltext_captures'})},
    'citation': {'leaf': PROSE, 'subtree': frozenset({'source'}), 'derived': frozenset({'fr_fulltext_captures'})},
}
REPAIRABLE = tuple(FIELD_MAP)
PATH_RE = re.compile(r'^[A-Za-z_]+(\[[^\]]+\])?(\.[A-Za-z_]+(\[[^\]]+\])?)*$')


# Paths ------------------------------------------------------------------------------------------------------------
def anchor(path):
    """The clause (operative_clauses[S]) or top-level field a flagged path lies in."""
    m = re.match(r'^(operative_clauses\[[^\]]+\])', path)
    return m.group(1) if m else re.split(r'[.\[]', path, maxsplit=1)[0]


def segments(path):
    return [s for s in re.sub(r'\[[^\]]*\]', '', path).split('.') if s]


def covered(path, anc):
    return path == anc or path.startswith(anc + '.') or path.startswith(anc + '[')


def allowed(path, defects):
    """True when some defect's class and anchors allow a change at path."""
    for d in defects:
        fm = FIELD_MAP.get(d.get('class'))
        if not fm:
            continue
        segs = segments(path)
        if segs and segs[0] in fm['derived']:
            return True
        for anc in d.get('anchors', []):
            if not covered(path, anc):
                continue
            below = segments(path)[len(segments(anc)):]
            if (segs and segs[-1] in fm['leaf']) or any(s in fm['subtree'] for s in below):
                return True
    return False


# Defect tags ------------------------------------------------------------------------------------------------------
def normalize_defect(d, tag=None, tag_source=None):
    """A defect object with class, locality, fields and anchors, or a status saying why it cannot be used."""
    out = copy.deepcopy(d) if isinstance(d, dict) else {'problem': d}
    if tag and (out.get('class') not in CLASSES or out.get('locality') not in LOCALITIES):  # never over a reviewer's tags
        out.update({k: v for k, v in tag.items() if k in ('class', 'locality', 'fields')})
        out['tag_source'] = tag_source
    fields = out.get('fields')
    if not fields and isinstance(out.get('field'), str) and PATH_RE.match(out['field'].strip()):
        fields = [out['field'].strip()]
    fields = [f.strip() for f in fields or [] if isinstance(f, str) and f.strip()]
    out['fields'] = fields
    out['anchors'] = sorted({anchor(f) for f in fields})
    cls, loc = out.get('class'), out.get('locality')
    if cls not in CLASSES or loc not in LOCALITIES:
        out['status'] = 'untagged'
    elif loc != 'LOCAL':
        out['status'] = 'structural'
    elif cls not in REPAIRABLE:
        out['status'] = f'class_{cls}_not_repairable'
    elif not fields or not all(PATH_RE.match(f) for f in fields):
        out['status'] = 'local_without_exact_fields'
    else:
        out['status'] = 'repairable'
    return out


def _reviewed(wave, packet):
    afr = Path(packet) / 'APPLIED_FOR_REVIEW'
    if not afr.exists():
        raise TiroError(f'no {wave.relpath(packet)}/APPLIED_FOR_REVIEW: run review-prep (or reuse-reviews) first')
    applied = afr.read_text(encoding='utf-8').strip()
    path = Path(packet) / applied / 'CLAIMS.proposed.jsonl'
    if not path.exists():
        raise TiroError(f'no {wave.relpath(path)}')
    return applied, path


def _key(wave, batch):
    keyf = wave.key_path(batch)
    if not keyf.exists():
        raise TiroError(f'no key {keyf}')
    return keyf, json.loads(keyf.read_text(encoding='utf-8'))


def _records(packet, name):
    return {r['claim_sha256']: r for r in load_jsonl(Path(packet) / 'reviews' / name) if r.get('claim_sha256')}


def plan_path(wave, batch):
    return wave.scr('repair', batch, 'REPAIR_PLAN.json')


# repair-prep ------------------------------------------------------------------------------------------------------
def repair_prep(wave, batch, packet, tags=None):
    """List the genuine claims exactly one arm rejected with only LOCAL defects of a repairable class; write
    SCR/repair/BATCH/REPAIR_PLAN.json and, when any claim is repairable, SCR/prompts/repair-producer-BATCH.txt.

    tags is an optional JSON file {instrument_id: [tag per defect, in order]} with class, locality and fields for
    reviews written before reviewers tagged their defects; a tag is used only for a defect the reviewer left
    untagged, and each tag used is marked with its source. Writes nothing in
    the packet."""
    packet = Path(packet)
    applied, cpath = _reviewed(wave, packet)
    keyf, key = _key(wave, batch)
    controls = {k['instrument_id'] for k in key.get('controls', [])}
    tag_map, tag_src = {}, None
    if tags:
        tag_map = json.loads(Path(tags).read_text(encoding='utf-8'))
        tag_src = {'path': str(tags), 'sha256': C.file_sha(tags), 'kind': 'coordinator tags for untagged reviews'}
    blind = {a: _records(packet, f'BLIND_REVIEW_{a}.jsonl') for a in ARMS}
    after = {a: _records(packet, f'AFTER_REVEAL_{a}.jsonl') for a in ARMS}
    rows, cands = [], []
    for line_no, c in enumerate(load_jsonl(cpath), 1):
        iid, sha = c['instrument_id'], C.canon(c)
        rec = {a: blind[a].get(sha) for a in ARMS}
        verdicts = {a: (rec[a] or {}).get('verdict') for a in ARMS}
        row = {'instrument_id': iid, 'claim_sha256': sha, 'verdicts': verdicts}
        if iid in controls:
            ar = {a: (after[a].get(sha) or {}).get('verdict') for a in ARMS}
            row.update(status='planted_control_never_repairable', after_reveal=ar)
            rows.append(row)
            continue
        rejected = [a for a in ARMS if verdicts[a] == 'rejected']
        upheld = [a for a in ARMS if verdicts[a] == 'upheld']
        if len(rejected) == 2:
            row['status'] = 'rejected_by_both_arms_not_repairable'
        elif not rejected:
            row['status'] = 'no_rejection' if len(upheld) == 2 else 'missing_review'
        elif len(upheld) != 1:
            row['status'] = 'other_arm_did_not_uphold'
        else:
            r_arm, u_arm = rejected[0], upheld[0]
            raw = rec[r_arm].get('defects') or []
            given = tag_map.get(iid) or []
            defects = [normalize_defect(d, given[i] if i < len(given) else None, tag_src if i < len(given) else None)
                       for i, d in enumerate(raw)]
            bad = sorted({d['status'] for d in defects if d['status'] != 'repairable'})
            row.update(rejecting_arm=r_arm, upholding_arm=u_arm, rejecting_reviewer=rec[r_arm].get('reviewer'),
                       upholding_reviewer=rec[u_arm].get('reviewer'), defects=defects,
                       status='repairable' if defects and not bad else
                       ('rejection_without_defects' if not defects else 'not_repairable: ' + ', '.join(bad)))
            if row['status'] == 'repairable':
                row['may_change'] = {'anchors': sorted({a for d in defects for a in d['anchors']}),
                                     'classes': sorted({d['class'] for d in defects})}
                cands.append(row)
        rows.append(row)
    plan = {'schema': 'tiro-repair-plan/v1', 'rule': RULE, 'batch': batch, 'wave': wave.name,
            'packet': wave.relpath(packet), 'reviewed_applied': applied,
            'reviewed_claims': {'path': wave.relpath(cpath), 'sha256': C.file_sha(cpath)},
            'key_sha256': C.file_sha(keyf), 'tags': tag_src, 'field_map': {k: {kk: sorted(v) for kk, v in fm.items()}
                                                                          for k, fm in FIELD_MAP.items()},
            'orders': rows, 'repairable': [r['instrument_id'] for r in cands]}
    pp = plan_path(wave, batch)
    pp.parent.mkdir(parents=True, exist_ok=True)
    pp.write_text(json.dumps(plan, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    prompt = None
    if cands:
        prompt = wave.scr('prompts', f'repair-producer-{batch}.txt')
        prompt.parent.mkdir(parents=True, exist_ok=True)
        prompt.write_text(producer_repair_prompt(wave, batch, packet, applied, cands), encoding='utf-8')
    return {'batch': batch, 'reviewed_applied': applied, 'plan': str(pp), 'prompt': str(prompt) if prompt else None,
            'repairable': plan['repairable'],
            'not_repairable': {r['instrument_id']: r['status'] for r in rows
                               if r['status'] not in ('repairable', 'no_rejection')}}


def reviewer_text(d):
    """The defect as the reviewer wrote it (without Tiro's bookkeeping, and without tags a tags file supplied)."""
    drop = {'anchors', 'status', 'tag_source'} | ({'class', 'locality', 'fields'} if d.get('tag_source') else set())
    return {k: v for k, v in d.items() if k not in drop}


def _allowed_text(d):
    fm = FIELD_MAP[d['class']]
    keys = ', '.join(sorted(fm['leaf']) + [k + '.*' for k in sorted(fm['subtree'])])
    parts = []
    for anc in d['anchors']:
        if anc.startswith('operative_clauses['):
            parts.append(f'inside {anc}, only the keys {keys}')
        elif anc in fm['leaf'] or anc in fm['subtree']:
            parts.append(f'the field {anc}' + ('' if anc in fm['leaf'] else ' and what lies under it'))
        else:
            parts.append(f'inside {anc}, only the keys {keys}')
    der = (f"; the derived {', '.join(sorted(fm['derived']))} disclosure may follow the edited sources"
           if fm['derived'] else '')
    return '; '.join(parts) + der


def producer_repair_prompt(wave, batch, packet, applied, cands):
    items = []
    for r in cands:
        lines = [f"- {r['instrument_id']} (rejected by arm {r['rejecting_arm']}; reviewed claim_sha256 {r['claim_sha256']}):"]
        for i, d in enumerate(r['defects'], 1):
            lines.append(f"  defect {i}, as the reviewer wrote it: " + json.dumps(reviewer_text(d), ensure_ascii=False))
            lines.append(f"  defect {i} tags ({'coordinator tags file' if d.get('tag_source') else 'reviewer'}): "
                         f"class {d['class']}, LOCAL, fields {', '.join(d['fields'])}")
            lines.append(f"  you may change, for defect {i}: {_allowed_text(d)}")
        items.append('\n'.join(lines))
    nxt = C.next_version(packet, 'applied-v').name
    return render((PROMPTS / 'repair_producer.txt').read_text(encoding='utf-8'), {
        'REPO': wave.repo, 'PACKETPATH': wave.relpath(packet), 'APPLIED': applied, 'NEXTAPPLIED': nxt,
        'ITEMS': '\n'.join(items), 'SCRATCH': f"{wave.scr('work', batch)}/", 'BATCH': batch})


# repair-check -----------------------------------------------------------------------------------------------------
def _load_plan(wave, batch, packet):
    pp = plan_path(wave, batch)
    if not pp.exists():
        raise TiroError(f'no {pp}: run repair-prep first')
    plan = json.loads(pp.read_text(encoding='utf-8'))
    applied, cpath = _reviewed(wave, packet)
    if plan['packet'] != wave.relpath(packet) or plan['reviewed_applied'] != applied:
        raise TiroError(f"repair plan is for {plan['packet']}/{plan['reviewed_applied']}, not "
                        f"{wave.relpath(packet)}/{applied}")
    if C.file_sha(cpath) != plan['reviewed_claims']['sha256']:
        raise TiroError(f'{wave.relpath(cpath)} changed since repair-prep; rerun repair-prep')
    keyf, key = _key(wave, batch)
    if C.file_sha(keyf) != plan['key_sha256']:
        raise TiroError(f'key {keyf} changed since repair-prep; rerun repair-prep')
    return plan, cpath, key


def compare_repairs(plan, old_path, new_path, controls):
    """{'accepted': [...], 'refused': [...], 'unchanged': [...]} for the plan's repairable orders. Raises TiroError
    when any other order differs or the two files hold different orders: the producer may touch only the planned
    claims."""
    old = {c['instrument_id']: c for c in load_jsonl(old_path)}
    new = {c['instrument_id']: c for c in load_jsonl(new_path)}
    if set(old) != set(new):
        raise TiroError(f'repaired claims hold different orders: only old {sorted(set(old) - set(new))}, '
                        f'only new {sorted(set(new) - set(old))}')
    rows = {r['instrument_id']: r for r in plan['orders'] if r['status'] == 'repairable'}
    stray = sorted(i for i in old if i not in rows and C.canon(old[i]) != C.canon(new[i]))
    if stray:
        raise TiroError(f'orders outside the repair plan changed: {stray}; their reviews no longer match')
    res = {'accepted': [], 'refused': [], 'unchanged': []}
    for iid, r in sorted(rows.items()):
        if iid in controls:
            raise TiroError(f'{iid} is a planted control; controls are never repairable')
        o, n = old[iid], new[iid]
        if C.canon(o) != r['claim_sha256']:
            raise TiroError(f'{iid}: reviewed claim hash differs from the plan')
        paths = C.claim_diff(o, n)
        if not paths:
            res['unchanged'].append({'instrument_id': iid})
            continue
        bad = [p for p in paths if not allowed(p, r['defects'])]
        entry = {'instrument_id': iid, 'old_claim_sha256': r['claim_sha256'], 'new_claim_sha256': C.canon(n),
                 'rejecting_arm': r['rejecting_arm'], 'carried_arm': r['upholding_arm'], 'changed_paths': paths,
                 'defects': r['defects']}
        if bad:
            entry.update(outside_flagged_point=bad, route='needs both reviewers again (full review of the new version)')
            res['refused'].append(entry)
        else:
            res['accepted'].append(entry)
    return res


def carried_record(rec, new_sha, receipt_rel, adjudicator):
    out = copy.deepcopy(rec)
    out['review_carried_from_claim_sha256'] = rec['claim_sha256']
    out['claim_sha256'] = new_sha
    out['carried_under'] = 'tiro fix-and-recheck: ' + RULE
    out['carried_by'] = adjudicator
    out['repair_receipt'] = receipt_rel
    return out


def repair_check(wave, batch, packet, repaired, batch_check=True, dry_run=False, force=False, emit=print):
    """Accept or refuse each repaired claim; write the carried upholds, re-check sets and prompts and the receipt.

    In the packet it writes reviews/REPAIR_CARRIED_<arm>.jsonl and REPAIR_RECEIPT.json (with dry_run both go under
    SCR/repair/BATCH/ instead). Returns the receipt summary; raises TiroError on a structural refusal."""
    packet = Path(packet)
    plan, old_path, key = _load_plan(wave, batch, packet)
    new_path = packet / repaired / 'CLAIMS.proposed.jsonl'
    if not new_path.exists():
        raise TiroError(f'no {wave.relpath(new_path)}')
    if repaired == plan['reviewed_applied']:
        raise TiroError('the repaired applied folder is the reviewed one; the producer writes a new applied-vN')
    controls = {k['instrument_id'] for k in key.get('controls', [])}
    if batch_check:
        log = wave.scr('logs', f'bc-{batch}-{packet.name}-{repaired}.log')
        r = C.run(C.kit('batch-check', wave.relpath(packet), wave.relpath(packet / repaired)), wave.repo)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(r.stdout + '\n' + r.stderr, encoding='utf-8')
        emit(f'batch-check {batch} {repaired} {r.returncode}')
        if r.returncode:
            raise TiroError(f'batch-check failed for {wave.relpath(packet / repaired)} (log {log}); nothing accepted')
    res = compare_repairs(plan, old_path, new_path, controls)
    out_dir = wave.scr('repair', batch) if dry_run else packet
    rv_dir = wave.scr('repair', batch, 'reviews') if dry_run else packet / 'reviews'
    receipt_path = out_dir / 'REPAIR_RECEIPT.json'
    receipt_rel = str(receipt_path) if dry_run else wave.relpath(receipt_path)
    if receipt_path.exists() and not force:
        raise TiroError(f'{receipt_path} exists; pass --force to replace it')
    blind = {a: _records(packet, f'BLIND_REVIEW_{a}.jsonl') for a in ARMS}
    carried, recheck = {a: [] for a in ARMS}, {a: [] for a in ARMS}
    new_claims = {c['instrument_id']: c for c in load_jsonl(new_path)}
    old_claims = {c['instrument_id']: c for c in load_jsonl(old_path)}
    for e in res['accepted']:
        up = blind[e['carried_arm']].get(e['old_claim_sha256'])
        if not up or up.get('verdict') != 'upheld':
            raise TiroError(f"{e['instrument_id']}: arm {e['carried_arm']} has no uphold of the reviewed version to carry")
        carried[e['carried_arm']].append(carried_record(up, e['new_claim_sha256'], receipt_rel, wave.adjudicator))
        recheck[e['rejecting_arm']].append(e)
    files = {}
    rv_dir.mkdir(parents=True, exist_ok=True)
    for a in ARMS:
        if carried[a]:
            f = rv_dir / f'REPAIR_CARRIED_{a}.jsonl'
            write_jsonl(f, carried[a])
            files[f'REPAIR_CARRIED_{a}'] = {'path': str(f) if dry_run else wave.relpath(f), 'sha256': C.file_sha(f)}
    prompts = {}
    rd = wave.scr('repair', batch)
    rd.mkdir(parents=True, exist_ok=True)
    for a in ARMS:
        if not recheck[a]:
            continue
        sp = rd / f'RECHECK_SET_{a}.jsonl'
        write_jsonl(sp, [new_claims[e['instrument_id']] for e in recheck[a]])
        pth = wave.scr('prompts', f'recheck-{batch}-{a}.txt')
        pth.parent.mkdir(parents=True, exist_ok=True)
        pth.write_text(recheck_prompt(wave, batch, a, packet, sp, recheck[a], old_claims, new_claims,
                                      blind[a], receipt_rel), encoding='utf-8')
        prompts[a] = str(pth)
    receipt = {'schema': 'tiro-repair-receipt/v1', 'rule': RULE, 'batch': batch, 'wave': wave.name,
               'packet': wave.relpath(packet), 'adjudicator': wave.adjudicator,
               'reviewed_applied': plan['reviewed_applied'], 'repaired_applied': repaired,
               'reviewed_claims': {'path': wave.relpath(old_path), 'sha256': C.file_sha(old_path)},
               'repaired_claims': {'path': wave.relpath(new_path), 'sha256': C.file_sha(new_path)},
               'plan_sha256': C.file_sha(plan_path(wave, batch)), 'key_sha256': plan['key_sha256'],
               'field_map': plan['field_map'], 'repairs': res['accepted'], 'refused': res['refused'],
               'unchanged': res['unchanged'], 'carried_files': files,
               'recheck_files': {a: f'{wave.relpath(packet)}/reviews/RECHECK_{a}.jsonl' for a in prompts}}
    receipt_path.write_text(json.dumps(receipt, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    return {'batch': batch, 'accepted': [e['instrument_id'] for e in res['accepted']],
            'refused': {e['instrument_id']: e['outside_flagged_point'] for e in res['refused']},
            'unchanged': [e['instrument_id'] for e in res['unchanged']], 'receipt': str(receipt_path),
            'recheck_prompts': prompts, 'dry_run': dry_run}


def _show(v, limit=700):
    t = json.dumps(v, ensure_ascii=False)
    return t if len(t) <= limit else t[:limit] + ' ...(truncated; read the claim)'


def recheck_prompt(wave, batch, arm, packet, set_path, entries, old_claims, new_claims, blind, receipt_rel):
    items = []
    for e in entries:
        iid = e['instrument_id']
        orig = blind.get(e['old_claim_sha256']) or {}
        lines = [f"- {iid}: your earlier rejection of claim_sha256 {e['old_claim_sha256']} named these defects:"]
        for d in e['defects']:
            lines.append('  ' + json.dumps(reviewer_text(d), ensure_ascii=False))
        lines.append(f"  repaired claim_sha256 {e['new_claim_sha256']}; Tiro verified that only these paths changed:")
        for p in e['changed_paths']:
            lines.append(f"    {p}: before {_show(C.value_at(old_claims[iid], p))}")
            lines.append(f"    {' ' * len(p)}  after  {_show(C.value_at(new_claims[iid], p))}")
        lines.append(f"  your earlier record's reviewer name: {orig.get('reviewer')}")
        items.append('\n'.join(lines))
    return render((PROMPTS / 'recheck.txt').read_text(encoding='utf-8'), {
        'REPO': wave.repo, 'ARM': arm, 'BATCH': batch, 'SETPATH': set_path.as_posix(),
        'PACKETDIR': wave.relpath(packet), 'ITEMS': '\n'.join(items), 'RECEIPT': receipt_rel,
        'REVIEWERNAME': wave.reviewer_name(batch, arm), 'REVSCRATCH': wave.scr('rev', f'{batch}-{arm}-recheck').as_posix(),
        'SCRROOT': wave.scratch.as_posix(), 'WAVEDIR': wave.rel})


# finish support ---------------------------------------------------------------------------------------------------
def verify_receipt(wave, batch, packet, receipt_path):
    """Re-verify a repair receipt against the packet and build the repairs map pair_rule() takes:
    {new claim hash: {'instrument_id', 'rejecting_arm', 'carried_arm', 'records': {arm: review record or None},
    'problems': [...]}}. Returns (receipt, repaired applied folder name, repairs, extra review files per arm,
    receipt path)."""
    packet = Path(packet)
    rp = Path(receipt_path)
    if not rp.is_absolute():
        rp = (wave.repo / rp) if (wave.repo / rp).exists() else (packet / rp)
    if not rp.exists():
        raise TiroError(f'no repair receipt {receipt_path}')
    receipt = json.loads(rp.read_text(encoding='utf-8'))
    if receipt.get('schema') != 'tiro-repair-receipt/v1' or receipt.get('batch') != batch:
        raise TiroError(f'{rp} is not a tiro repair receipt for {batch}')
    if receipt['packet'] != wave.relpath(packet):
        raise TiroError(f"repair receipt is for {receipt['packet']}, not {wave.relpath(packet)}")
    old_path = packet / receipt['reviewed_applied'] / 'CLAIMS.proposed.jsonl'
    new_path = packet / receipt['repaired_applied'] / 'CLAIMS.proposed.jsonl'
    for p, pin in ((old_path, receipt['reviewed_claims']), (new_path, receipt['repaired_claims'])):
        if not p.exists() or C.file_sha(p) != pin['sha256']:
            raise TiroError(f'{wave.relpath(p) if p.exists() else p} does not match the repair receipt')
    keyf, key = _key(wave, batch)
    controls = {k['instrument_id'] for k in key.get('controls', [])}
    # Re-run the same comparison: every accepted repair must still be accepted with the same new hash. A refused
    # order keeps its changed claim, which has no review, so finish blocks it until both arms review it again.
    plan = {'orders': [{'instrument_id': e['instrument_id'], 'status': 'repairable', 'claim_sha256': e['old_claim_sha256'],
                        'rejecting_arm': e['rejecting_arm'], 'upholding_arm': e['carried_arm'], 'defects': e['defects']}
                       for e in receipt['repairs'] + receipt['refused']]}
    res = compare_repairs(plan, old_path, new_path, controls)
    got = {e['instrument_id']: e['new_claim_sha256'] for e in res['accepted']}
    want = {e['instrument_id']: e['new_claim_sha256'] for e in receipt['repairs']}
    if got != want:
        raise TiroError(f'repair receipt no longer matches the claims: receipt {want}, now {got}')
    for name, pin in receipt.get('carried_files', {}).items():
        f = packet / 'reviews' / f'{name}.jsonl'
        if not f.exists() or C.file_sha(f) != pin['sha256']:
            raise TiroError(f'{name}.jsonl is missing or changed since repair-check')
    blind = {a: _records(packet, f'BLIND_REVIEW_{a}.jsonl') for a in ARMS}
    recheck = {a: _records(packet, f'RECHECK_{a}.jsonl') for a in ARMS}
    carried = {a: _records(packet, f'REPAIR_CARRIED_{a}.jsonl') for a in ARMS}
    repairs, extra = {}, {a: [] for a in ARMS}
    for a in ARMS:
        for name in (f'RECHECK_{a}.jsonl', f'REPAIR_CARRIED_{a}.jsonl'):
            if (packet / 'reviews' / name).exists():
                extra[a].append(packet / 'reviews' / name)
    for e in receipt['repairs']:
        new, old = e['new_claim_sha256'], e['old_claim_sha256']
        r_arm, c_arm = e['rejecting_arm'], e['carried_arm']
        problems, records = [], {}
        rej = blind[r_arm].get(old) or {}
        rc = recheck[r_arm].get(new)
        if rc and rc.get('reviewer') != rej.get('reviewer'):
            problems.append(f'arm {r_arm} re-check reviewer {rc.get("reviewer")} is not the rejecting reviewer '
                            f'{rej.get("reviewer")}')
            rc = None
        records[r_arm] = rc
        cr = carried[c_arm].get(new)
        up = blind[c_arm].get(old)
        if not (cr and up and up.get('verdict') == 'upheld' and cr.get('review_carried_from_claim_sha256') == old):
            problems.append(f'arm {c_arm} carried uphold missing or not derived from its uphold of {old}')
            cr = None
        records[c_arm] = cr
        repairs[new] = {'instrument_id': e['instrument_id'], 'rejecting_arm': r_arm, 'carried_arm': c_arm,
                        'records': records, 'problems': problems}
    return receipt, receipt['repaired_applied'], repairs, extra, rp
