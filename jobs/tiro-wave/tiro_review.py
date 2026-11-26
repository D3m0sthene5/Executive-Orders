"""Tiro prompts and review sets: producer prompt, planted controls, blind reviewer and reveal prompts, pooled arms.

Coordinator bookkeeping only. Keys, review sets and prompts are written under the wave's scratch root, outside
the repository; review-prep writes into the packet only reviews/ and APPLIED_FOR_REVIEW (and nothing with --dry-run).
"""
import glob
import json
import random
import re
from pathlib import Path

import plants
from tiro_common import PROMPTS, TiroError, load_jsonl, render, write_jsonl


def _dispatch_record(packet):
    """Newest dispatch-vN.json (by number), else DISPATCH_CHECK.json."""
    recs = []
    for p in Path(packet).glob('dispatch-v*.json'):
        m = re.fullmatch(r'dispatch-v(\d+)\.json', p.name)
        if m:
            recs.append((int(m.group(1)), p))
    path = sorted(recs)[-1][1] if recs else Path(packet) / 'DISPATCH_CHECK.json'
    if not path.exists():
        raise TiroError(f'no DISPATCH_CHECK.json or dispatch-vN.json in {packet}')
    return json.loads(path.read_text(encoding='utf-8'))


def producer_prompt(wave, batch, route, agent, packet, note=None):
    """The Papinian producer prompt for one packet, as render_producer.py built it."""
    if not (PROMPTS / f'route_{route}.txt').exists():
        known = sorted(p.stem[6:] for p in PROMPTS.glob('route_*.txt'))
        raise TiroError(f'unknown route {route!r}; known: {", ".join(known)}')
    d = _dispatch_record(packet)
    ok, blocked = d['dispatchable_ids'], d['source_blocked_ids']
    miss = {}
    for t in d.get('source_recovery_tasks', []):
        for r in t.get('affected_references', []):
            if r.get('required'):
                miss.setdefault(r['instrument_id'], set()).add(
                    f"{r['evidence_id']} ({'/'.join(t.get('check_statuses', []))})")
    dnote = 'All members passed the dispatch check.' if not blocked else (
        'DISPATCH-BLOCKED (not assigned; do not research; write only their assessment row from the view, and leave '
        'their decisions.csv rows as prepared): '
        + '; '.join(f"{i}: mandatory source not held: {', '.join(sorted(miss.get(i, ['see DISPATCH_CHECK.json'])))}"
                    for i in blocked))
    brief = (PROMPTS / f'route_{route}.txt').read_text(encoding='utf-8').strip()
    t = (PROMPTS / 'producer.txt').read_text(encoding='utf-8')
    t = t.replace('{{ROUTENAME}}', route).replace('{{ROUTEBRIEF}}', brief)
    undecided = Path(packet) / 'undecided'
    precheck = '(no undecided/ folder in this packet: no coordinator precheck)'
    if undecided.exists():
        lines = ['COORDINATOR PRECHECK (mechanical, from the frozen evidence; you still verify):']
        for ev in sorted(glob.glob(str(undecided / '*/EVIDENCE.json'))):
            e = json.loads(Path(ev).read_text(encoding='utf-8'))
            dz = e['base_dossier']
            o = dz['evidence'].get(dz.get('original_source_id'), {})
            ids = list(dz.get('evidence', {}))
            h = e['history_packet']['history']
            lines.append(
                f"- {e['instrument_id']}: original {dz.get('original_source_id')} acceptable_as_original="
                f"{o.get('acceptable_as_original')} requires_page_check={o.get('requires_page_check')}; "
                f"ending-type records {sum(i.startswith(('ACT:', 'TERM:', 'ACTOR_TEXT:')) for i in ids)}, CURRENT records "
                f"{sum(i.startswith('CURRENT:') for i in ids)}; history observations {len(h.get('observation_ids', []))}, "
                f"flags {h.get('flags')}")
        precheck = '\n'.join(lines)
        t = t.replace('edit only decisions.csv, clauses.csv and RATIONALES.json',
                      'edit only decisions.csv, clauses.csv, RATIONALES.json and the STATUS_DECISION.json files under undecided/')
    t = render(t, {'PRECHECK': precheck, 'PACKETPATH': wave.relpath(packet), 'ASSIGNEDLIST': ', '.join(ok) or 'none',
                   'DISPATCHNOTE': dnote, 'SCRATCH': f'{wave.scr("work", batch)}/', 'AGENTNAME': agent,
                   'REPO': wave.repo, 'WAVEDIR': wave.rel})
    if note:
        t += '\n\nCOORDINATOR NOTE FOR THIS BATCH:\n' + Path(note).read_text(encoding='utf-8')
    return t, ok, blocked


def render_producer(wave, batch, route, agent, packet, note=None, name=None):
    t, ok, blocked = producer_prompt(wave, batch, route, agent, packet, note)
    out = wave.scr('prompts', f'producer-{name or batch}.txt')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(t, encoding='utf-8')
    return {'batch': batch, 'packet': wave.relpath(packet), 'assigned': len(ok), 'blocked': blocked,
            'chars': len(t), 'prompt': str(out)}


def reveal_prompt(batch, arm, controls, genuine_path, packet_rel):
    ids = ', '.join(k['instrument_id'] for k in controls)
    defects = '; '.join(sorted({k['defect'] for k in controls}))
    return (f"After-reveal step for batch {batch}, arm {arm}. The claim(s) for {ids} in your review set were planted "
            f"controls ({defects}). The genuine version(s) the producer filed are in {genuine_path} (one JSON claim "
            "per line). Review each genuine version on its merits with the same blinding and the same standard as your "
            "blind review (it must pass every check you applied to other claims; do not uphold it just because it is "
            "the genuine one), applying jobs/tiro-wave/RUBRIC.md and tagging any rejection as it says. "
            f"Write one JSON object per genuine claim to {packet_rel}/reviews/AFTER_REVEAL_{arm}.jsonl, "
            f"in the same format as your BLIND_REVIEW_{arm}.jsonl records, with claim_sha256 computed the same way over "
            "the genuine claim, the same reviewer name, verdict \"upheld_after_reveal\" if it is right or \"rejected\" "
            f"with defects if not, and started_utc/ended_utc. Do not change BLIND_REVIEW_{arm}.jsonl. Reply in at most "
            "60 words with each order and its verdict.")


def review_prep(wave, batch, packet, applied, note=None, kind=plants.DEFAULT_KIND, dry_run=False, force=False,
                seed=None):
    """Plant controls and write two separately shuffled blind review sets with their reviewer and reveal prompts.

    kind is 'rotation' (default: successive kinds from a seed-dependent start) or one plant kind; seed defaults to
    the batch name. The key records the seed, the kind order and, per control, its kind and planted defect.

    Writes SCR/review/BATCH/{REVIEW_SET,REVIEW_SET_A,REVIEW_SET_B,GENUINE_CONTROLS}.jsonl, the private key
    SCR/keys/BATCH.json and SCR/prompts/{reviewer,reveal}-BATCH-{A,B}.txt; in the packet, reviews/ and
    APPLIED_FOR_REVIEW (skipped with dry_run). Refuses to overwrite an existing key unless force: a key in use
    is what finish scores the arms against."""
    packet = Path(packet)
    claims_path = packet / applied / 'CLAIMS.proposed.jsonl'
    if not claims_path.exists():
        raise TiroError(f'no {wave.relpath(packet)}/{applied}/CLAIMS.proposed.jsonl')
    keyf = wave.key_path(batch)
    if keyf.exists() and not force:
        raise TiroError(f'key {keyf} exists (reviews may be in flight); pass --force to replace it, or use another --scratch')
    claims = load_jsonl(claims_path)
    try:
        made = plants.make_controls(claims, batch, kind=kind, seed=seed)
    except ValueError as e:
        raise TiroError(str(e))
    key = {'batch': batch, 'wave': wave.name, 'packet': packet.name, 'applied': applied,
           'plant_kind': made['kind'], 'plant_seed': made['seed'], 'plant_rotation': made['rotation'],
           'controls': made['controls']}
    rd = wave.scr('review', batch)
    rd.mkdir(parents=True, exist_ok=True)
    wave.scr('keys').mkdir(parents=True, exist_ok=True)
    wave.scr('prompts').mkdir(parents=True, exist_ok=True)
    write_jsonl(rd / 'REVIEW_SET.jsonl', made['review_rows'])
    write_jsonl(rd / 'GENUINE_CONTROLS.jsonl', made['genuine'])
    keyf.write_text(json.dumps(key, indent=1), encoding='utf-8')
    if not dry_run:
        (packet / 'reviews').mkdir(exist_ok=True)
        (packet / 'APPLIED_FOR_REVIEW').write_text(applied + '\n', encoding='utf-8')
    bn = Path(note).read_text(encoding='utf-8').strip() if note else ''
    pk = wave.relpath(packet)
    template = (PROMPTS / 'reviewer.txt').read_text(encoding='utf-8')
    prompts = {}
    for arm in 'AB':
        rows = list(made['review_rows'])
        random.Random(f'bartolus-{batch}-{arm}').shuffle(rows)
        sp = rd / f'REVIEW_SET_{arm}.jsonl'
        write_jsonl(sp, rows)
        t = render(template, {'SETPATH': sp.as_posix(), 'PACKETDIR': pk, 'BATCHNOTE': bn,
                              'REVSCRATCH': wave.scr('rev', f'{batch}-{arm}').as_posix(), 'ARM': arm,
                              'REVIEWERNAME': wave.reviewer_name(batch, arm), 'REPO': wave.repo,
                              'SCRROOT': wave.scratch.as_posix(), 'WAVEDIR': wave.rel})
        rp = wave.scr('prompts', f'reviewer-{batch}-{arm}.txt')
        rp.write_text(t, encoding='utf-8')
        vp = wave.scr('prompts', f'reveal-{batch}-{arm}.txt')
        vp.write_text(reveal_prompt(batch, arm, made['controls'], (rd / 'GENUINE_CONTROLS.jsonl').as_posix(), pk),
                      encoding='utf-8')
        prompts[arm] = [str(rp), str(vp)]
    return {'batch': batch, 'packet': pk, 'applied': applied, 'claims': len(claims), 'kind': kind,
            'seed': made['seed'], 'mode': made['mode'],
            'control_kinds': {k['instrument_id']: k['kind'] for k in made['controls']},
            'controls': sorted(k['instrument_id'] for k in made['controls']),
            'key': str(keyf), 'prompts': prompts, 'dry_run': dry_run,
            'packet_writes': [] if dry_run else [f'{pk}/reviews/', f'{pk}/APPLIED_FOR_REVIEW']}


def pool_prompt(wave, batches, arm, reveal=False):
    """One instruction for one agent per arm that reviews several batches' sets in turn.

    Each batch's own reviewer (or reveal) prompt is inlined verbatim, so the agent needs to open nothing under the
    scratch root beyond each set's SETPATH and its own scratch folders, exactly as in a one-batch review."""
    kind = 'reveal' if reveal else 'reviewer'
    parts = []
    for b in batches:
        p = wave.scr('prompts', f'{kind}-{b}-{arm}.txt')
        if not p.exists():
            raise TiroError(f'no {p}: run review-prep for {b} first')
        parts.append((b, p.read_text(encoding='utf-8').strip()))
    names = ', '.join(b for b, _ in parts)
    head = (f"You are one independent blind reviewer, arm {arm}, for {len(parts)} separate "
            f"{'after-reveal steps' if reveal else 'review sets'}: {names}. Do them one at a time, in this order. "
            "Each has its own complete instruction below; for each, follow its instruction exactly as if it were your "
            "only task: its blinding rule, the files it lets you open, its output file and its scratch folder. One "
            "set's instruction never lets you open another set's packet or files except where that other set's own "
            "instruction names them. Review every claim on its merits; do not carry a verdict from one set into "
            "another. Read the shared briefs and rulings once, at the start, and do not reread them for each set. "
            "Ignore each set's own reply-length line; instead, when every set is done, reply once in at most "
            f"{60 * len(parts)} words: for each set, its counts and each rejection's order and defect.")
    body = '\n\n'.join(f"===== SET {i} of {len(parts)}: batch {b}, arm {arm} =====\n{t}" for i, (b, t) in enumerate(parts, 1))
    return head + '\n\n' + body + '\n'
