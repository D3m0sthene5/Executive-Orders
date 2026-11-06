"""Build DISPOSITION.csv (150 rows) and PLANTS.csv for the Dorotheus wave (coordinator tool; clerical, no legal
judgment: every reading comes from a producer assessment row, an existing filed claim, or a recorded outcome).

usage: python3 -I disposition.py
Inputs: SAMPLE.csv, yesprobe DRAW.json, /tmp/claude-0/dorotheus-wave/{batches.json,COORDINATOR_LOG.txt,keys/,
outcomes.json}, each packet's decisions.csv, newest dispatch-v*.json, ASSESSMENT.jsonl, reviews/ and the two
published claim files. outcomes.json (written by the coordinator after completion) maps an instrument id to
{"outcome": filed|rejected_review|blocked, "claim_sha256", "note"} for every submitted member.
Per-order context_tokens and turns: the packet's worker totals (input + cache read + cache write; turns) split
equally over the packet's members. Ready/owner-routed orders used no worker: 0.
"""
import csv, glob, json, re, sys
from pathlib import Path
REPO = Path('/home/user/Executive-Orders'); E = Path('/tmp/claude-0/dorotheus-wave')
SW = REPO / 'research/excavator/dorotheus-sample-2026-11-06'; YW = REPO / 'research/excavator/dorotheus-yesprobe-2026-11-06'
sys.path.insert(0, str(REPO / 'jobs/claim-kit')); import batch
COLS = ['id', 'wave', 'group', 'packet', 'attempts', 'outcome', 'claimed_status', 'operative_force_at_cutoff',
        'operative_force_basis', 'formal_validity_at_cutoff', 'formal_disposition', 'first_cause',
        'formal_revocation_after_earlier_cessation', 'blocker', 'reviewer_A', 'reviewer_B', 'reviewer_C',
        'claim_sha256', 'context_tokens', 'turns']
def jl(p): return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()] if Path(p).exists() else []
def canon(o):
    import hashlib; return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
def cause(mech):
    m = (mech or '').lower()
    for k, v in (('statut', 'legislative'), ('repeal', 'legislative'), ('act of congress', 'legislative'), ('revok', 'later_presidential'),
                 ('revoc', 'later_presidential'), ('supersed', 'later_presidential'), ('own_terms', 'under_original_terms'),
                 ('own terms', 'under_original_terms'), ('expir', 'under_original_terms'), ('perform', 'completion_of_task'),
                 ('complet', 'completion_of_task'), ('exhaust', 'completion_of_task'), ('court', 'judicial'), ('judic', 'judicial'),
                 ('regulat', 'regulatory'), ('never', 'never_activated')):
        if k in m: return v
    return 'unresolved'
def from_claim(c, path):
    """Readings for an existing filed claim (mapped mechanically from its fields)."""
    st = c.get('whole_order_status'); r = {'claimed_status': st}
    mechs = [((cl.get('first_end') or {}).get('mechanism') or '') for cl in c.get('operative_clauses', [])]
    evs = [e for cl in c.get('operative_clauses', []) for e in cl.get('later_events', []) if isinstance(e, dict)]
    rev = [e for e in evs if re.search(r'revok|revoc|supersed', json.dumps(e).lower())]
    if st == 'yes':
        r.update(operative_force_at_cutoff='yes', formal_validity_at_cutoff='unrevoked', formal_disposition='', first_cause='unresolved' if False else '',
                 formal_revocation_after_earlier_cessation='no',
                 operative_force_basis=f"Existing filed YES claim ({path}): current predicate checked through 2026-10-14.")
        r['first_cause'] = ''
    else:
        we = c.get('whole_order_end') or {}
        first_rev = bool(re.search(r'revok|revoc|supersed', (we.get('mechanism') or '').lower()))
        later_rev = [e for e in rev if (e.get('effective_date') or e.get('date') or '') > (we.get('date') or '')]
        r.update(operative_force_at_cutoff='no', first_cause=cause(we.get('mechanism')),
                 operative_force_basis=f"Existing filed NO claim ({path}): whole order ended {we.get('date')} by {we.get('actor')} ({we.get('mechanism')}).",
                 formal_validity_at_cutoff='revoked' if first_rev or rev else 'unknown',
                 formal_disposition=(f"{we.get('actor')}, {we.get('date')}" if first_rev else
                                     (f"{later_rev[0].get('actor')}, {later_rev[0].get('effective_date') or later_rev[0].get('date')}" if later_rev else '')),
                 formal_revocation_after_earlier_cessation='no' if first_rev else ('yes' if later_rev else 'unknown'))
    return r
def workers():
    """worker name -> {packet, tokens, turns, cost, model}"""
    out = {}
    for line in (E / 'COORDINATOR_LOG.txt').read_text().splitlines():
        m = re.match(r'END (\S+) model=(\S+) .*cost=([0-9.]+) turns=(\d+) in=(\d+) cache_read=(\d+) cache_write=(\d+) out=(\d+)', line)
        if not m: continue
        n = m.group(1); pk = re.search(r'-(d\d\d|u\d\d\d|y\d\d|ux\d|S\d)(?:-|$)', n)
        g = pk.group(1) if pk else None; g = {'S1': 'ux1', 'S2': 'ux2'}.get(g, g)
        out[n] = {'packet': g, 'model': m.group(2), 'cost': float(m.group(3)), 'turns': int(m.group(4)),
                  'tokens': int(m.group(5)) + int(m.group(6)) + int(m.group(7)), 'out': int(m.group(8))}
    return out
def main():
    plan = json.load(open(E / 'batches.json')); outcomes = json.load(open(E / 'outcomes.json')) if (E / 'outcomes.json').exists() else {}
    S = list(csv.DictReader(open(SW / 'SAMPLE.csv'))); D = json.load(open(YW / 'DRAW.json'))['draw']
    own = batch.owners(REPO); W = workers()
    where = {(('yesprobe' if p.startswith('y') else 'sample'), i): p for p, ids in plan['packets'].items() for i in ids}
    per_packet = {}
    for w in W.values():
        if w['packet']: per_packet.setdefault(w['packet'], [0, 0]); per_packet[w['packet']][0] += w['tokens']; per_packet[w['packet']][1] += w['turns']
    attempts = {}
    for n in W:
        m = re.match(r'producer-(\S+)-a(\d)', n)
        if m: attempts[m.group(1)] = max(attempts.get(m.group(1), 0), int(m.group(2)))
    A2 = {('y03', 'EO:12046'), ('y03', 'EO:12163')}
    rb = {i: b for b, ids in plan.get('review_batches', {}).items() for i in ids}
    rows = []
    def packet_info(p):
        P = (YW if p.startswith('y') else SW) / p / 'packet'
        rec = json.load(open(sorted(glob.glob(str(P / 'dispatch-v*.json')))[-1]))
        miss = {}
        for t in rec.get('source_recovery_tasks', []):
            for r in t.get('affected_references', []):
                if r.get('required'):
                    miss.setdefault(r['instrument_id'], set()).add(f"{'/'.join(t.get('check_statuses', []))} {(t.get('native_wanted', {}).get('urls') or ['?'])[0]} sha256 {t.get('expected_sha256', '')[:16]}")
        for m in rec.get('members', []):
            if m.get('instrument_id') in rec['source_blocked_ids'] and m['instrument_id'] not in miss:
                miss[m['instrument_id']] = {b.get('kind', '') + ': ' + b.get('reason', '') for b in m.get('blockers', [])}
        dec = {r['instrument_id']: r for r in csv.DictReader(open(P / 'decisions.csv', encoding='utf-8-sig'))}
        ass = {r['id']: r for r in jl(P / 'ASSESSMENT.jsonl')}
        rv = {}
        for f in glob.glob(str(P / 'reviews/*.jsonl')) + glob.glob(str(SW / 'ux*/reviews/*.jsonl')):
            arm = Path(f).stem.rsplit('_', 1)[-1]; kind = 'after' if 'AFTER_REVEAL' in f else 'blind'
            for r in jl(f): rv.setdefault((r.get('instrument_id'), arm), []).append((kind, r))
        return P, set(rec['source_blocked_ids']), miss, dec, ass, rv
    cache = {}
    for wave, ids, grp in [('sample', [r['id'] for r in S], {r['id']: r['group'] for r in S}), ('yesprobe', D, {i: 'yes_probe' for i in D})]:
        for i in ids:
            row = dict.fromkeys(COLS, ''); row.update(id=i, wave=wave, group=grp[i], attempts=0, context_tokens=0, turns=0)
            pre = plan['pre_routed'].get(i if wave == 'sample' else 'Y|' + i)
            if pre:
                o = own.get(i)
                if o:
                    c = jl(REPO / o['path'])[o['line'] - 1]
                    ready = pre == 'ready_existing' or o['owner'].startswith('claude-2026-11-05-icecore')
                    if ready:
                        row.update(from_claim(c, o['path'])); row.update(outcome='ready_existing', claim_sha256=o['claim_sha256'])
                    else:
                        row.update(outcome='nonresponse_dispatch', operative_force_at_cutoff='unknown', formal_validity_at_cutoff='unknown',
                                   first_cause='unresolved', formal_revocation_after_earlier_cessation='unknown',
                                   operative_force_basis=f"unknown: not produced; an incomplete claim of another owner exists ({o['path']}, status {c.get('whole_order_status')})",
                                   blocker=f"existing incomplete claim of another owner ({o['owner']}, {o['path']} line {o['line']}); claim-kit routes it to its owner or an explicit replacement proposal")
                rows.append(row); continue
            p = where[(wave, i)]; row['packet'] = p
            if p not in cache: cache[p] = packet_info(p)
            P, blocked, miss, dec, ass, rv = cache[p]
            a = ass.get(i, {})
            for k in ('operative_force_at_cutoff', 'operative_force_basis', 'formal_validity_at_cutoff', 'formal_disposition', 'first_cause',
                      'formal_revocation_after_earlier_cessation'):
                row[k] = a.get(k, '') if a else ''
            if not a:
                row.update(operative_force_at_cutoff='unknown', formal_validity_at_cutoff='unknown', first_cause='unresolved',
                           formal_revocation_after_earlier_cessation='unknown', operative_force_basis='unknown: no assessment row written')
            n_members = len(plan['packets'][p]); tok, tu = per_packet.get(p, [0, 0])
            extra = per_packet.get(rb.get(i), [0, 0]); nb = len(plan.get('review_batches', {}).get(rb.get(i), [])) or 1
            row['context_tokens'] = round(tok / n_members + extra[0] / nb); row['turns'] = round(tu / n_members + extra[1] / nb, 1)
            if i in blocked:
                row.update(outcome='nonresponse_dispatch', attempts=0, blocker='mandatory source not held: ' + '; '.join(sorted(miss.get(i, ['see dispatch receipt']))))
                rows.append(row); continue
            row['attempts'] = 2 if (p, i) in A2 else 1
            d = dec.get(i, {})
            for arm in 'ABC':
                recs = rv.get((i, arm), [])
                row['reviewer_' + arm] = ';'.join(sorted({f"{k}:{r.get('verdict')}" for k, r in recs}))
            if i in outcomes:
                o = outcomes[i]; row.update(outcome=o['outcome'], claim_sha256=o.get('claim_sha256', ''), claimed_status=o.get('status', a.get('claimed_status', '')))
                if o['outcome'] != 'filed': row['blocker'] = o.get('note', '')
            elif d.get('outcome') in ('blocked', 'unresolved'):
                row.update(outcome='blocked', claimed_status=a.get('claimed_status', '') if a.get('outcome') == 'submit' else '',
                           blocker=a.get('blocker') or d.get('unresolved_material_gaps', '')[:600])
            else:
                row.update(outcome='nonresponse_producer', blocker=a.get('blocker') or 'producer did not decide this member after its attempts')
            rows.append(row)
    with open(SW / 'DISPOSITION.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)
    plants = []
    strict = {}
    for f in glob.glob(str(E / 'mwscore/*.score.json')):
        b, arm = Path(f).name.split('.')[0].rsplit('-', 1)
        try: strict[(b, arm)] = 'yes' if json.load(open(f))['pooled']['strict']['k'] else 'no'
        except Exception: pass
    for p in sorted(plan['packets']) + ['ux1', 'ux2']:
        f = (YW if p.startswith('y') else SW) / p / 'packet/completion/PLANTS.json'
        if p.startswith('ux'): f = SW / p / 'completion/PLANTS.json'
        if f.exists(): plants += json.load(open(f))
    for r in plants:
        r['caught_strict'] = strict.get((r['packet'], r['arm']), '') if r['defect_type'].startswith('mountweazel') else r['caught']
    with open(SW / 'PLANTS.csv', 'w', newline='', encoding='utf-8') as f:
        cols = ['packet', 'plant_id', 'defect_type', 'arm', 'caught', 'caught_strict']
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows({k: r[k] for k in cols} for r in plants)
    import collections
    print(len(rows), collections.Counter((r['wave'], r['outcome']) for r in rows))
if __name__ == '__main__': main()
