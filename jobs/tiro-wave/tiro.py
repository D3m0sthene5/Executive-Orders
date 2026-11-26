"""Tiro: the wave coordinator's clerk (after Marcus Tullius Tiro, Cicero's secretary, who kept and ordered his papers).

It runs claim-kit commands and file bookkeeping for one agent wave and makes no legal judgment. Every wave name,
date, folder and Bentham action comes from the wave's WAVE.json; keys, review sets, prompts, logs and ledgers stay
under a scratch root outside the repository (default /home/claude/<wave short name>-scr, or --scratch / TIRO_SCRATCH).

    python3 -X utf8 -I jobs/tiro-wave/tiro.py --wave baldus-2026-11-25 <subcommand> ...

Subcommands: prepare, render-producer, review-prep, pool-prompt, finish, current, reapply, reuse-reviews, adopt,
gzip-receipts, ledger, cost. See README.md for the whole wave, step by step.
"""
import argparse
import gzip
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I leaves the script's folder off sys.path

import tiro_common as C  # noqa: E402
from tiro_common import TiroError, Wave  # noqa: E402

GZIP_THRESHOLD = 50_000_000
DEFAULT_DECISION = 'D-20261125-auto-adopt-replacements'
DEFAULT_RULING = 'research/readiness/owner_rulings/2026-11-25-auto-adopt-replacements.md'

CURRENT_SNIPPET = r'''
import json, pathlib, sys
repo = pathlib.Path(sys.argv[1]); sys.path.insert(0, str(repo / 'jobs/claim-kit'))
blobs = json.loads(sys.argv[2])
if blobs:
    _orig = pathlib.Path.read_bytes
    def _read_bytes(self):
        k = str(self.resolve())
        return _orig(pathlib.Path(blobs[k])) if k in blobs else _orig(self)
    pathlib.Path.read_bytes = _read_bytes
import batch
for rel in sys.argv[3:]:
    try:
        batch.load_packet(repo / rel, repo)
        print(json.dumps({'packet': rel, 'state': 'CURRENT'}))
    except Exception as e:
        print(json.dumps({'packet': rel, 'state': 'STALE', 'reason': (type(e).__name__ + ': ' + str(e))[:300]}))
'''


# current ---------------------------------------------------------------------------------------------------------
def current(repo, packets, scratch=None, from_index=False, emit=print):
    """CURRENT or STALE per packet (batch.load_packet with source checks); writes nothing in the repository.

    A PACKET.json that is tracked but not on disk (skip-worktree in a lean checkout) is reported NOT_ON_DISK;
    with from_index its bytes are read from the git index into the scratch root instead."""
    repo = Path(repo).resolve()
    sparse = C.run(C.git('config', '--get', 'core.sparseCheckout'), repo).stdout.strip() == 'true'
    rels, blobs, states = [], {}, []
    for p in packets:
        pth = (repo / p).resolve()
        rel = pth.relative_to(repo).as_posix()
        pj = pth / 'PACKET.json'
        if pj.exists():
            rels.append(rel)
            continue
        flag = C.run(C.git('ls-files', '-v', '--', f'{rel}/PACKET.json'), repo).stdout.strip()
        if not flag:
            states.append({'packet': rel, 'state': 'NO_PACKET', 'reason': 'no PACKET.json on disk or in the index'})
            continue
        if not from_index:
            states.append({'packet': rel, 'state': 'NOT_ON_DISK', 'reason': f'PACKET.json is tracked ({flag.split()[0]}) '
                           'but not checked out here; rerun with --from-index to read it from the git index'})
            continue
        if scratch is None:
            raise TiroError('--from-index needs a scratch root (pass --wave or --scratch)')
        dest = Path(scratch) / 'current-blobs' / (rel.replace('/', '__') + '__PACKET.json')
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = C.run_to_file(C.git('cat-file', 'blob', f':{rel}/PACKET.json'), repo, dest)
        if r.returncode:
            states.append({'packet': rel, 'state': 'NO_PACKET', 'reason': r.stderr.strip()[:200]})
            continue
        blobs[str(pj)] = str(dest)
        rels.append(rel)
    if rels:
        r = C.run([sys.executable, '-X', 'utf8', '-c', CURRENT_SNIPPET, str(repo), json.dumps(blobs), *rels], repo,
                  env={'PYTHONDONTWRITEBYTECODE': '1'})
        got = [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]
        if r.returncode or len(got) != len(rels):
            raise TiroError('current check failed: ' + (r.stderr.strip()[-400:] or 'no output'))
        for g in got:
            if blobs and str((repo / g['packet'] / 'PACKET.json').resolve()) in blobs:
                g['packet_json'] = 'read from the git index'
        states += got
    for s in states:
        emit(f"{s['state']} {s['packet']}" + (f" {s['reason']}" if s.get('reason') else '')
             + (f" ({s['packet_json']})" if s.get('packet_json') else ''))
    if sparse:
        emit('note: this checkout is sparse; load_packet reads only checked-out files, so a STALE caused by a '
             'missing held source or prior-research file may be a sparse-checkout artifact (F-20261125-sparse-checkout-defect)')
    return 0 if states and all(s['state'] == 'CURRENT' for s in states) else 1


# gzip-receipts ---------------------------------------------------------------------------------------------------
def gzip_receipts(dirs, threshold=GZIP_THRESHOLD, emit=print):
    """Store files over 50 MB as lossless gzip (-9, mtime 0) with a NAME.COMPRESSED.json record of the sha256."""
    done = []
    for d in dirs:
        for p in sorted(Path(d).rglob('*')):
            if p.is_file() and p.suffix != '.gz' and p.stat().st_size > threshold:
                raw = p.read_bytes()
                sha = hashlib.sha256(raw).hexdigest()
                gz = p.with_name(p.name + '.gz')
                with gzip.GzipFile(gz, 'wb', compresslevel=9, mtime=0) as f:
                    f.write(raw)
                if hashlib.sha256(gzip.decompress(gz.read_bytes())).hexdigest() != sha:
                    gz.unlink()
                    raise TiroError(f'gzip round trip failed for {p}')
                p.with_name(p.stem + '.COMPRESSED.json').write_text(json.dumps({
                    'file': p.name, 'stored_as': gz.name, 'sha256_uncompressed': sha, 'bytes_uncompressed': len(raw),
                    'reason': 'GitHub 100 MB file limit; gzip -9n is lossless (verified by round trip)'}))
                p.unlink()
                emit(f'gz {p} {len(raw)} -> {gz.stat().st_size}')
                done.append(str(p))
    return done


# cost and ledger -------------------------------------------------------------------------------------------------
def transcript_cost(repo, path):
    """List-price dollars and token totals of one Agent-tool transcript (last usage object per message id, priced
    by model from jobs/necker-costs/PRICES.json; 1-hour and 5-minute cache writes separately)."""
    prices = json.loads((Path(repo) / 'jobs/necker-costs/PRICES.json').read_text(encoding='utf-8'))['models']

    def rate(model):
        return next((m for m in prices if re.match(m['match'], model or '')), None)
    last, models = {}, {}
    for line in open(path, encoding='utf-8'):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        msg = e.get('message') if isinstance(e, dict) else None
        if isinstance(msg, dict) and isinstance(msg.get('usage'), dict) and msg.get('id'):
            last[msg['id']] = msg['usage']
            models[msg['id']] = msg.get('model')
    tot = dict(inp=0, cr=0, cw=0, out=0)
    usd = 0.0
    for mid, u in last.items():
        m = rate(models[mid])
        cc = u.get('cache_creation') or {}
        w1, w5 = cc.get('ephemeral_1h_input_tokens', 0) or 0, cc.get('ephemeral_5m_input_tokens', 0) or 0
        wu = max((u.get('cache_creation_input_tokens') or 0) - w1 - w5, 0)
        tot['inp'] += u.get('input_tokens') or 0
        tot['cr'] += u.get('cache_read_input_tokens') or 0
        tot['cw'] += w1 + w5 + wu
        tot['out'] += u.get('output_tokens') or 0
        if m:
            usd += ((u.get('input_tokens') or 0) * m['input'] + (u.get('cache_read_input_tokens') or 0) * m['cache_read']
                    + w1 * m['cache_write_1h'] + (w5 + wu) * m['cache_write_5m'] + (u.get('output_tokens') or 0) * m['output']) / 1e6
    model = '+'.join(sorted({v for v in models.values() if v}) or ['unknown'])
    return {'model': model, 'usd': usd, 'calls': len(last), **tot, 'tokens': sum(tot.values())}


def cost_line(label, role, c):
    return (f"{label} agent-tool {role} {c['model']} cost {c['usd']:.4f} calls {c['calls']} in {c['inp']} "
            f"cache_read {c['cr']} cache_write {c['cw']} out {c['out']}")


def outcome_counts(packet):
    counts = {}
    for r in C.read_csv(Path(packet) / 'decisions.csv'):
        o = (r.get('outcome') or '').strip() or 'blank'
        counts[o] = counts.get(o, 0) + 1
    return {('submitted' if k == 'submit' else k): v for k, v in counts.items()}


def ledger_row(kind, a, wave):
    if kind == 'launch':
        return f"{a.label},launched,{a.role},{a.model},start={a.start or C.now()}"
    fields = [a.label, a.agent_id or '', a.role, a.model, f'end={a.end or C.now()}']
    if a.start:
        fields.append(f'start={a.start}')
    counts = {}
    if a.counts_from:
        counts.update(outcome_counts(wave.packet(a.label if not a.batch else a.batch, a.packet)))
    if a.submitted is not None:
        counts['submitted'] = a.submitted
    if a.blocked is not None:
        counts['blocked'] = a.blocked
    for k in ('submitted', 'blocked'):
        if k in counts:
            fields.append(f'{k}={counts.pop(k)}')
    fields += [f'{k}={v}' for k, v in sorted(counts.items())]
    if a.transcript:
        c = transcript_cost(wave.repo, a.transcript)
        fields += [f"tokens={c['tokens']}", f"usd={c['usd']:.4f}"]
        C.append_log(wave.scr('COSTS.log'), cost_line(a.label, a.role, c))
    elif a.tokens is not None:
        fields.append(f'tokens={a.tokens}')
    fields += list(a.extra or [])
    if any(',' in str(f) for f in fields):
        raise TiroError('ledger fields may not contain commas')
    return ','.join(str(f) for f in fields)


# adopt -----------------------------------------------------------------------------------------------------------
def adopt(wave, batches, packet=None, completion=None, target=None, receipt=None, decision=DEFAULT_DECISION,
          ruling=DEFAULT_RULING, write=False, emit=print):
    """jobs/claim-kit/adopt_replacement.py --standing for the newest complete-vN of each batch (dry plan unless write)."""
    comps = []
    if completion:
        comps = [Path(completion)]
    else:
        for b in batches:
            found = C.version_dirs(wave.packet(b, packet), 'complete-v')
            if not found:
                raise TiroError(f'no complete-vN in {wave.relpath(wave.packet(b, packet))}')
            comps.append(found[-1])
    for c in comps:
        pub = Path(c) / 'PUBLICATION.json'
        if not pub.exists() or json.loads(pub.read_text(encoding='utf-8')).get('mode') != 'replacement_proposal':
            raise TiroError(f'{c} is not a replacement-proposal completion (PUBLICATION.json mode)')
    if len(batches) > 1 and not (target and receipt):
        raise TiroError('several batches: pass --target and --receipt')
    b = batches[0]
    target = target or f'research/readiness/claims/novellae-{wave.date}-{wave.short}-{b}.jsonl'
    receipt = receipt or f'{wave.rel}/{b}/ADOPTION_RECEIPT.json'
    cmd = C.py(C.ADOPT, '--repo', '.', '--decision', decision, '--ruling', ruling,
               *[a for c in comps for a in ('--completion', wave.relpath(c))], '--target', target,
               '--receipt', receipt, '--standing', *(['--write'] if write else []))
    r = C.run(cmd, wave.repo)
    emit(r.stdout.strip()[-3000:])
    if r.stderr.strip():
        emit(r.stderr.strip()[-1500:])
    return r.returncode


# CLI -------------------------------------------------------------------------------------------------------------
def build_parser():
    ap = argparse.ArgumentParser(prog='tiro.py', description=__doc__.split('\n\n')[0])
    ap.add_argument('--repo', default=str(C.DEFAULT_REPO), help='repository root (default: this checkout)')
    ap.add_argument('--wave', help='wave name, wave folder or WAVE.json path (all subcommands but current, gzip-receipts, cost)')
    ap.add_argument('--scratch', help='scratch root outside the repo (default /home/claude/<short>-scr or $TIRO_SCRATCH)')
    sub = ap.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('prepare', help='kit prepare with drop-and-retry, cruden lookups, Geddes views')
    s.add_argument('batch')
    s.add_argument('ids', nargs='*')
    s.add_argument('--ids-from', metavar='PACKET', help="take the orders of this batch's existing packet (re-prepare)")
    s.add_argument('--agent', help='kit agent (default: the wave short name)')
    s.add_argument('--action', help="Bentham action (default: WAVE.json's only action)")
    s.add_argument('--level', default=os.environ.get('LARREY_LEVEL', 'hard'), help='LARREY_LEVEL (default hard)')
    s.add_argument('--packet', default='packet', help='packet folder to write (default packet)')
    s.add_argument('--held-supplement', action='store_true', help='kit writes <packet>-held; views go there')
    s.add_argument('--replacement-proposal', action='store_true')
    s.add_argument('--retries', type=int, default=5)
    s.add_argument('--no-drop', action='store_true', help='stop at the first refusal instead of dropping orders')
    s.add_argument('--no-lookups', action='store_true', help='skip cruden lookups and Geddes views')

    s = sub.add_parser('render-producer', help='producer prompt for one packet -> SCR/prompts/producer-BATCH.txt')
    s.add_argument('batch')
    s.add_argument('route', help='yes, no, undecided, correction, recovery, stale')
    s.add_argument('agent', help='value for the agent column')
    s.add_argument('--note', help='coordinator note file appended to the prompt')
    s.add_argument('--packet')
    s.add_argument('--name', help='prompt file stem after producer- (default BATCH; e.g. y20-v2)')

    s = sub.add_parser('review-prep', help='planted controls, blind review sets, reviewer and reveal prompts, key')
    s.add_argument('batch')
    s.add_argument('applied', help='applied-vN folder holding CLAIMS.proposed.jsonl')
    s.add_argument('--note', help='batch note file inserted in the reviewer prompts')
    s.add_argument('--packet')
    s.add_argument('--kind', default=None, help='plant kind (default date_shift)')
    s.add_argument('--dry-run', action='store_true', help='write only under the scratch root, nothing in the packet')
    s.add_argument('--force', action='store_true', help='replace an existing key')

    s = sub.add_parser('pool-prompt', help='one pooled instruction per arm for several batches')
    s.add_argument('batches', nargs='+')
    s.add_argument('--arm', choices=['A', 'B'], action='append', help='arm (repeatable; default both)')
    s.add_argument('--reveal', action='store_true', help='pool the after-reveal prompts instead')
    s.add_argument('--write', metavar='LABEL', help='also write SCR/prompts/pool-LABEL-ARM.txt')

    s = sub.add_parser('finish', help='control adjudication, pair rule, completion manifest, kit complete')
    s.add_argument('batch')
    s.add_argument('--packet')
    s.add_argument('--publish', action='store_true')
    s.add_argument('--replacement', action='store_true', help='isolated replacement proposal (env REPLACEMENT=1 before)')

    s = sub.add_parser('current', help='is a packet still current? (load_packet with source checks; no writes)')
    s.add_argument('packets', nargs='+', help='packet folders relative to the repo')
    s.add_argument('--from-index', action='store_true', help='read a skip-worktree PACKET.json from the git index')

    s = sub.add_parser('reapply', help='re-prepare, carry sheets over, apply, compare claims')
    s.add_argument('batch')
    s.add_argument('old_packet')
    s.add_argument('old_applied')
    s.add_argument('new_packet', help='packet folder to write; with --held the kit adds -held')
    s.add_argument('--held', action='store_true', help='--held-supplement')
    s.add_argument('--rp', action='store_true', help='--replacement-proposal')
    s.add_argument('--action', help="default: the old packet's ADMISSION.json action")
    s.add_argument('--agent', help="default: the old packet's agent")
    s.add_argument('--level', default=os.environ.get('LARREY_LEVEL', 'hard'))

    s = sub.add_parser('reuse-reviews', help='carry reviews to re-applied claims under D-20261125-reuse-identical-reviews')
    s.add_argument('batch')
    s.add_argument('old_packet')
    s.add_argument('old_applied')
    s.add_argument('new_packet')
    s.add_argument('new_applied')
    s.add_argument('--no-batch-check', action='store_true')
    s.add_argument('--reason', default='', help='why the packet was re-prepared (recorded in REVIEW_REUSE.json)')
    s.add_argument('--force', action='store_true', help='overwrite files already in the new reviews/')
    s.add_argument('--finish', action='store_true', help='then run finish on the new packet')
    s.add_argument('--publish', action='store_true')
    s.add_argument('--replacement', action='store_true')

    s = sub.add_parser('adopt', help='adopt_replacement.py --standing for batches (plan only unless --write)')
    s.add_argument('batches', nargs='+')
    s.add_argument('--packet')
    s.add_argument('--completion', help='completion folder (default: newest complete-vN of the packet)')
    s.add_argument('--target')
    s.add_argument('--receipt')
    s.add_argument('--decision', default=DEFAULT_DECISION)
    s.add_argument('--ruling', default=DEFAULT_RULING)
    s.add_argument('--write', action='store_true')

    s = sub.add_parser('gzip-receipts', help='gzip completion files over 50 MB with a sha256 record')
    s.add_argument('dirs', nargs='+')

    s = sub.add_parser('ledger', help='append a WORKERS_LAUNCH.csv or WORKERS_DONE.csv row in the scratch root')
    s.add_argument('kind', choices=['launch', 'done'])
    s.add_argument('label', help='batch or pool label (y01, pool4-A)')
    s.add_argument('--role', required=True, help='producer, reviewer, ...')
    s.add_argument('--model', required=True, help='sonnet, opus, ...')
    s.add_argument('--agent-id')
    s.add_argument('--start')
    s.add_argument('--end')
    s.add_argument('--submitted', type=int)
    s.add_argument('--blocked', type=int)
    s.add_argument('--tokens', type=int)
    s.add_argument('--transcript', help='Agent-tool transcript: tokens and list-price USD (also SCR/COSTS.log)')
    s.add_argument('--counts-from', action='store_true', help="count outcomes from the batch's decisions.csv")
    s.add_argument('--batch', help='batch for --counts-from when the label is not the batch')
    s.add_argument('--packet')
    s.add_argument('--extra', action='append', help='extra key=value field (repeatable)')

    s = sub.add_parser('cost', help='list-price cost of one Agent-tool transcript')
    s.add_argument('label')
    s.add_argument('role')
    s.add_argument('transcript')
    s.add_argument('--log', help='append the line to this file')
    return ap


def main(argv=None, emit=print):
    a = build_parser().parse_args(argv)
    repo = Path(a.repo).resolve()
    needs_wave = a.cmd not in ('current', 'gzip-receipts', 'cost')
    wave = None
    if needs_wave or a.wave:
        if not a.wave:
            raise TiroError(f'{a.cmd} needs --wave')
        wave = Wave(repo, a.wave, a.scratch)
    if a.cmd == 'prepare':
        import tiro_prep
        ids = list(a.ids)
        if a.ids_from:
            ids += C.packet_meta(wave.packet(a.batch, a.ids_from))['ids']
        res = tiro_prep.prepare(wave, a.batch, ids, a.agent or wave.short, wave.action(a.action), a.level, a.packet,
                                a.held_supplement, a.replacement_proposal, a.retries, not a.no_drop, not a.no_lookups)
        emit(json.dumps(res))
        return 0 if res['state'] in ('ok', 'empty') else 1
    if a.cmd == 'render-producer':
        import tiro_review
        emit(json.dumps(tiro_review.render_producer(wave, a.batch, a.route, a.agent, wave.packet(a.batch, a.packet),
                                                    a.note, a.name)))
        return 0
    if a.cmd == 'review-prep':
        import plants
        import tiro_review
        emit(json.dumps(tiro_review.review_prep(wave, a.batch, wave.packet(a.batch, a.packet), a.applied, a.note,
                                                a.kind or plants.DEFAULT_KIND, a.dry_run, a.force)))
        return 0
    if a.cmd == 'pool-prompt':
        import tiro_review
        for arm in a.arm or ['A', 'B']:
            t = tiro_review.pool_prompt(wave, a.batches, arm, a.reveal)
            if a.write:
                p = wave.scr('prompts', f"pool-{a.write}{'-reveal' if a.reveal else ''}-{arm}.txt")
                p.write_text(t, encoding='utf-8')
                emit(f'# wrote {p}')
            emit(t)
        return 0
    if a.cmd == 'finish':
        import tiro_finish
        return tiro_finish.finish(wave, a.batch, wave.packet(a.batch, a.packet), a.publish,
                                  a.replacement or bool(os.environ.get('REPLACEMENT')), emit)
    if a.cmd == 'current':
        return current(repo, a.packets, wave.scratch if wave else a.scratch, a.from_index, emit)
    if a.cmd == 'reapply':
        import tiro_prep
        emit(json.dumps(tiro_prep.reapply(wave, a.batch, a.old_packet, a.old_applied, a.new_packet, a.held, a.rp,
                                          a.action, a.agent, a.level, emit)))
        return 0
    if a.cmd == 'reuse-reviews':
        import tiro_reuse
        res = tiro_reuse.reuse_reviews(wave, a.batch, a.old_packet, a.old_applied, a.new_packet, a.new_applied,
                                       not a.no_batch_check, a.force, a.reason, emit)
        emit(json.dumps(res))
        if a.finish:
            import tiro_finish
            return tiro_finish.finish(wave, a.batch, wave.packet(a.batch, a.new_packet), a.publish, a.replacement, emit)
        return 0
    if a.cmd == 'adopt':
        return adopt(wave, a.batches, a.packet, a.completion, a.target, a.receipt, a.decision, a.ruling, a.write, emit)
    if a.cmd == 'gzip-receipts':
        gzip_receipts(a.dirs, emit=emit)
        return 0
    if a.cmd == 'ledger':
        row = ledger_row(a.kind, a, wave)
        path = wave.scr('WORKERS_LAUNCH.csv' if a.kind == 'launch' else 'WORKERS_DONE.csv')
        C.append_log(path, row)
        emit(row)
        return 0
    if a.cmd == 'cost':
        line = cost_line(a.label, a.role, transcript_cost(repo, a.transcript))
        emit(line)
        if a.log:
            C.append_log(a.log, line)
        return 0
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except TiroError as e:
        print(f'tiro: {e}', file=sys.stderr)
        sys.exit(2)
