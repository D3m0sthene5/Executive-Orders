#!/usr/bin/env python3
"""Gilbreth: measurement probe for claim-kit producer waves (stdlib only, deterministic, zero model tokens).

Named for Frank and Lillian Gilbreth, whose time-and-motion studies broke work into measured elements so that
the wasted motions could be cut.

Reads packet folders, prep logs, producer prompts and worker ledgers of the Bracton wave and the Junto lean
two-arm trial and writes:
  jobs/gilbreth/output/MEASURES.json
  jobs/gilbreth/output/packets/<wave>__<label>.csv   (one row per packet member)

Every number in MEASURES.json carries its basis in a sibling "basis" field or in the top-level "bases" table:
  measured  = read directly from a file, ledger or timestamp
  estimated = computed with a stated model (bytes/4 tokens; Bartolus call-cost model for dollars)
  inferred  = allocated or deduced (for example worker tokens split evenly across a packet's orders)

Usage:
  python3 -I jobs/gilbreth/gilbreth.py [--transcripts DIR] [--pc-lanes CSV] [--filed CSV]
    --transcripts  folder of per-call subagent transcripts (*.jsonl, named <label>-<agent id>.jsonl)
    --pc-lanes     the PC lane ledger LANES.csv (label,agent_id,model,start_utc,end_utc,tokens,tool_uses,ms,result)
    --filed        CSV with instrument_id,upheld_a,upheld_b,filed (1/0) once review and filing are done
Run from the repository root.
"""
import csv
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(REPO, 'jobs', 'gilbreth', 'output')

WAVES = [
    {
        'wave': 'bracton',
        'root': 'research/excavator/claude-bracton-2026-11-25',
        'packet_glob': ['c[0-9][0-9]', 's[0-9][0-9]', 'r[0-9][0-9]', 'p[0-9][0-9]'],
        'scr': '/home/claude/bracton-scr',
        'prompt': lambda scr, lab: f'{scr}/prompts/producer-{lab}.txt',
        'log': lambda scr, lab: f'{scr}/logs/prep-{lab}.log',
    },
    {
        'wave': 'junto-lean',
        'root': 'research/excavator/claude-junto-lean-2026-11-25',
        'packet_glob': ['arm0/a[0-9][0-9]', 'arm1/b[0-9][0-9]'],
        'scr': '/home/claude/junto-scr',
        'prompt': lambda scr, lab: f'{scr}/prompts/producer-{lab.split("/")[0]}/{lab.split("/")[1]}.txt',
        'log': lambda scr, lab: f'{scr}/logs/prep-{lab.replace("/", "-")}.log',
    },
]

# The fixed reading list (steps 1-4 of every producer prompt; step 5, LOOKUPS.md, is per packet).
# 'section' = (start marker, end regex) when the prompt asks for only part of a file.
FIXED_READING = [
    ('1 production route', 'research/excavator/claude-production-2026-10-28/PRODUCTION_ROUTE.md', None),
    ('2 claim schema', 'research/stage19/CLAIM_SCHEMA.md', None),
    ('2 BATCH.md: Before assigning a producer', 'jobs/claim-kit/BATCH.md', ('## Before assigning a producer', r'(?m)^## ')),
    ('2 BATCH.md: Read every original paragraph', 'jobs/claim-kit/BATCH.md',
     ('Read every original and common source independently', r'\n\s*\n')),
    ('3 ruling evidence-not-convenience', 'research/readiness/owner_rulings/2026-10-28-evidence-not-convenience.md', None),
    ('3 ruling transcription-as-text', 'research/readiness/owner_rulings/2026-10-21-transcription-as-text.md', None),
    ('3 ruling until-and-further-exempt', 'research/readiness/owner_rulings/2026-10-21-until-and-further-exempt.md', None),
    ('3 ruling strike-and-insert', 'research/readiness/owner_rulings/2026-10-21-strike-and-insert.md', None),
    ('4 NIRA brief: Sheet fields section', 'research/excavator/claude-nira-sweep-2026-10-29/PRODUCER_BRIEF.md',
     ('## Sheet fields for a plain code approval', r'(?m)^## ')),
]

# Block taxonomy: first matching pattern wins (checked against the producer's exact blocker text).
BLOCK_KINDS = [
    ('work_not_completed', r'[Ww]ork not completed|no missing source identified'),
    ('held_but_not_in_packet_catalogue',
     r'not (a )?source in the packet|not registered packet evidence|source supplement|not in this packet|'
     r'no citable evidence id|[Cc]itable evidence id|not an evidence record|No EO \d+ evidence id|not recognised by working-text gate'),
    ('nmb_emergency_board_report_custody_only',
     r'\bNMB\b|PEB[- ]?\d|National Mediation Board|[Ee]mergency [Bb]oard (report|No)|board report PDF|board\'s report'),
    ('commission_report_or_transmittal_date',
     r'final report submission date|report submission|submission of the .{0,40}report|transmittal|'
     r'final report.{0,60}not held|dates the .{0,60}report'),
    ('task_performance_record', r'performance records|records of completion'),
    ('nea_continuation_notice', r'National Emergencies|\bNEA\b|continuation notice'),
    ('current_cfr_text', r'\bCFR\b|eCFR|Code of Federal Regulations'),
    ('statute_text', r'U\.S\.C\.|\bUSC\b|Stat\.|statute|Public Law|Pub\. L\.'),
    ('own_original_custody_only', r'ORIGINAL:EO|CLAUSES:EO|original.{0,40}custody|Mandatory sources? not held'),
    ('fr_page_image', r'page image|FR page'),
    ('public_land_order', r'[Pp]ublic [Ll]and [Oo]rder'),
    ('later_order_text', r'(Executive Order|EO)\s?\d{3,5}.{0,60}(not held|text|bytes|custody)'),
    ('proclamation_or_other_instrument', r'[Pp]roclamation|[Rr]eorganization [Pp]lan|[Mm]emorandum'),
    ('treaty_or_agreement', r'[Tt]reaty|[Aa]greement'),
]

PASS_STATUSES = {'gpo_published_hash_match', 'held_bytes_verified', 'held_bytes_in_release_or_repo'}
MASS_REVOCATION_MIN_TARGETS = 5   # an ACT target revoking >= this many scanned members is treated as a cleanup table


def rel(p):
    return os.path.relpath(p, REPO)


def fsize(p):
    p = p if os.path.isabs(p) else os.path.join(REPO, p)
    try:
        return os.path.getsize(p)
    except OSError:
        return None


def tok(b):
    return None if b is None else int(round(b / 4))


def load_json(p, default=None):
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def secs(a, b):
    a, b = parse_ts(a) if isinstance(a, str) else a, parse_ts(b) if isinstance(b, str) else b
    return None if (a is None or b is None) else (b - a).total_seconds()


def mtime_iso(p):
    try:
        return datetime.fromtimestamp(os.path.getmtime(p), timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    except OSError:
        return None


# ---------------------------------------------------------------- prices and dollar estimate

def load_prices():
    d = load_json(os.path.join(REPO, 'jobs/necker-costs/PRICES.json'), {})
    return d.get('models', [])


def price_for(model, prices):
    for m in prices:
        if re.search(m['match'], model or ''):
            return m
    return None


def dollars_bartolus(final_tokens, tool_uses, model, prices):
    """Bartolus REPORT.md cost model (estimated): each call re-reads about half the final context at
    cache-read price, the final context is written once at the 5-minute write price, about 800 output
    tokens per call; calls = tool uses + 1."""
    p = price_for(model, prices)
    if p is None or final_tokens is None or tool_uses is None:
        return None
    n = tool_uses + 1
    usd = (n * final_tokens / 2 * p['cache_read'] + final_tokens * p['cache_write_5m'] + 800 * n * p['output']) / 1e6
    return round(usd, 4)


def dollars_usage(u, model, prices):
    p = price_for(model, prices)
    if p is None:
        return None
    return round((u['input'] * p['input'] + u['cache_read'] * p['cache_read'] + u['cache_write_5m'] * p['cache_write_5m']
                  + u['cache_write_1h'] * p['cache_write_1h'] + u['output'] * p['output']) / 1e6, 4)


# ---------------------------------------------------------------- ledgers

def read_launch(path):
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            out[r['label']] = r
    return out


def read_done(path):
    """WORKERS_DONE.csv rows: label,agent,role,model,key=value,... (note may contain commas)."""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('label,'):
                continue
            parts = line.split(',')
            rec = {'label': parts[0], 'agent_id': parts[1], 'role': parts[2], 'model': parts[3]}
            last = None
            for piece in parts[4:]:
                if '=' in piece and re.match(r'^[a-z_]+=', piece):
                    k, v = piece.split('=', 1)
                    rec[k] = v
                    last = k
                elif last:
                    rec[last] += ',' + piece
            for k in ('tokens', 'tool_uses', 'ms', 'submitted', 'blocked'):
                if k in rec:
                    try:
                        rec[k] = int(rec[k])
                    except ValueError:
                        pass
            out[rec['label']] = rec
    return out


def read_pc_lanes(path):
    out = {}
    if not path or not os.path.exists(path):
        return out
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            mdl = r.get('model') or ''
            mdl = {'sonnet': 'claude-sonnet-5-5', 'opus': 'claude-opus-5-5'}.get(mdl, mdl)
            rec = {'label': r.get('label'), 'agent_id': r.get('agent_id'), 'role': 'producer', 'model': mdl,
                   'start': r.get('start_utc'), 'end': r.get('end_utc')}
            for k in ('tokens', 'tool_uses', 'ms'):
                try:
                    rec[k] = int(r.get(k) or '')
                except ValueError:
                    rec[k] = None
            out[rec['label']] = rec
    return out


def read_transcripts(folder, prices):
    """Per-call usage from Claude Code subagent transcripts (*.jsonl). Returns {label: summary}."""
    out = {}
    if not folder or not os.path.isdir(folder):
        return out
    for p in sorted(glob.glob(os.path.join(folder, '*.jsonl'))):
        label = os.path.basename(p).split('-')[0]
        u = {'requests': 0, 'input': 0, 'cache_read': 0, 'cache_write_5m': 0, 'cache_write_1h': 0, 'output': 0,
             'max_prompt': 0, 'tool_result_bytes': 0, 'first_ts': None, 'last_ts': None, 'model': None}
        seen = set()
        with open(p, encoding='utf-8', errors='replace') as f:
            for line in f:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                ts = o.get('timestamp')
                if ts:
                    u['first_ts'] = u['first_ts'] or ts
                    u['last_ts'] = ts
                msg = o.get('message') or {}
                if o.get('type') == 'user' and isinstance(msg.get('content'), list):
                    for c in msg['content']:
                        if isinstance(c, dict) and c.get('type') == 'tool_result':
                            u['tool_result_bytes'] += len(json.dumps(c.get('content'), ensure_ascii=False))
                us = msg.get('usage')
                if not us:
                    continue
                key = msg.get('id') or o.get('requestId') or len(seen)
                if key in seen:
                    continue
                seen.add(key)
                u['model'] = u['model'] or msg.get('model')
                u['requests'] += 1
                cc = us.get('cache_creation') or {}
                w5 = cc.get('ephemeral_5m_input_tokens')
                w1 = cc.get('ephemeral_1h_input_tokens')
                wt = us.get('cache_creation_input_tokens') or 0
                if w5 is None and w1 is None:
                    w5, w1 = wt, 0
                u['input'] += us.get('input_tokens') or 0
                u['cache_read'] += us.get('cache_read_input_tokens') or 0
                u['cache_write_5m'] += w5 or 0
                u['cache_write_1h'] += w1 or 0
                u['output'] += us.get('output_tokens') or 0
                prompt = (us.get('input_tokens') or 0) + (us.get('cache_read_input_tokens') or 0) + wt
                u['max_prompt'] = max(u['max_prompt'], prompt)
        u['usd_list_price'] = dollars_usage(u, u['model'], prices)
        u['basis'] = 'measured (per-call usage in transcript, priced at PRICES.json list rates)'
        out.setdefault(label, []).append({'file': os.path.basename(p), **u})
    return out


# ---------------------------------------------------------------- prompts and fixed reading

def section_bytes(text, start_marker, end_re):
    i = text.find(start_marker)
    if i < 0:
        return None
    m = re.compile(end_re).search(text, i + len(start_marker))
    j = m.start() if m else len(text)
    return len(text[i:j].encode('utf-8'))


def fixed_reading():
    rows = []
    for label, path, sec in FIXED_READING:
        full = fsize(path)
        b = full
        if sec and full is not None:
            with open(os.path.join(REPO, path), encoding='utf-8') as f:
                b = section_bytes(f.read(), sec[0], sec[1])
        rows.append({'step': label, 'path': path, 'whole_file_bytes': full, 'asked_bytes': b,
                     'asked_tokens_est': tok(b), 'whole_file_tokens_est': tok(full)})
    # BATCH.md counted once for whole-file reading
    seen, whole = set(), 0
    for r in rows:
        if r['path'] not in seen and r['whole_file_bytes']:
            whole += r['whole_file_bytes']
            seen.add(r['path'])
    asked = sum(r['asked_bytes'] or 0 for r in rows)
    return {'files': rows, 'asked_bytes': asked, 'asked_tokens_est': tok(asked),
            'whole_files_bytes': whole, 'whole_files_tokens_est': tok(whole),
            'basis': 'measured bytes; tokens estimated as bytes/4'}


def parse_prompt(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        t = f.read()
    m = re.search(r'ROUTE:\s*(\S+)', t)
    am = re.search(r'ASSIGNED MEMBERS:\s*(.*?)\s\.\s', t)
    assigned = re.findall(r'EO:\d+[A-Z-]*', am.group(1)) if am else []
    return {'path': path, 'bytes': len(t.encode('utf-8')), 'tokens_est': tok(len(t.encode('utf-8'))),
            'route': m.group(1) if m else None, 'assigned': assigned}


# ---------------------------------------------------------------- prep logs

def parse_log(path):
    if not os.path.exists(path):
        return None
    start = done = None
    exit_code = None
    viewfail = 0
    errors = []
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = re.match(r'PREPARE \S+ .*start (\S+)', line)
            if m:
                start = m.group(1)
            m = re.match(r'DONE \S+ (\S+)', line)
            if m:
                done = m.group(1)
            m = re.match(r'PREPARE_EXIT (\d+)', line)
            if m:
                exit_code = int(m.group(1))
            if line.startswith('VIEWFAIL'):
                viewfail += 1
            if line.startswith('claim-kit:') or line.startswith('LOOKUPS_FAIL') or 'Error' in line[:40]:
                errors.append(line.strip()[:240])
    return {'path': path, 'start': start, 'done': done, 'wall_s': secs(start, done), 'prepare_exit': exit_code,
            'view_failures': viewfail, 'errors': errors, 'basis': 'measured (log timestamps, 1 s resolution)'}


# ---------------------------------------------------------------- packet

def classify_block(text):
    for kind, pat in BLOCK_KINDS:
        if re.search(pat, text or ''):
            return kind
    return 'other' if text else 'unstated'


def source_status(s):
    sts = [c.get('status') for c in s.get('checks', [])]
    return sts[0] if sts else None


def applied_dirs(pk):
    ds = []
    for d in glob.glob(os.path.join(pk, 'applied-v*')):
        m = re.search(r'applied-v(\d+)$', d)
        if m and os.path.isdir(d):
            ds.append((int(m.group(1)), d))
    return [d for _, d in sorted(ds)]


def file_digest(p):
    import hashlib
    try:
        with open(p, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except OSError:
        return None


def repair_rounds(pk):
    rounds = []
    prev_claims = None
    for d in applied_dirs(pk):
        s = load_json(os.path.join(d, 'SUMMARY.json'), {}) or {}
        c = load_json(os.path.join(d, 'CHECK_SUMMARY.json'))
        g = load_json(os.path.join(d, 'GEDDES_LINT.json'))
        claims = file_digest(os.path.join(d, 'CLAIMS.proposed.jsonl'))
        af = (c or {}).get('actionable_failures') or []
        af_codes = []
        for a in af:
            if not isinstance(a, dict):
                af_codes.append(str(a)[:60])
                continue
            parts = [f"{a.get('instrument_id', '?')}:"]
            for k in ('errors', 'mechanical_failures', 'unverified'):
                for e in a.get(k) or []:
                    parts.append(f"{k}={str(e).split('@')[0][:60]}")
            af_codes.append(' '.join(parts))
        af_codes = sorted(set(af_codes))
        apply_m = mtime_iso(os.path.join(d, 'SUMMARY.json'))
        check_m = mtime_iso(os.path.join(d, 'CHECK_SUMMARY.json')) if c is not None else None
        rounds.append({
            'dir': os.path.basename(d),
            'apply_counts': s.get('counts'),
            'apply_wall_s': s.get('wall_seconds'),
            'batch_check_ran': c is not None,
            'claims_checked': (c or {}).get('claims_checked'),
            'strict_pass': (c or {}).get('strict_claim_pass'),
            'strict_fail': (c or {}).get('strict_claim_fail'),
            'actionable_failures': len(af),
            'actionable_failure_codes': af_codes,
            'geddes_flags': (g or {}).get('defect_flags'),
            'geddes_coverage_gaps': (g or {}).get('coverage_gaps'),
            'geddes_resolutions_file': os.path.exists(os.path.join(d, 'GEDDES_RESOLUTIONS.json')),
            'claims_changed_from_previous': (None if prev_claims is None else claims != prev_claims),
            'apply_written_utc': apply_m,
            'check_written_utc': check_m,
            'apply_to_check_s': secs(apply_m, check_m),
        })
        prev_claims = claims
    # reason the round after each one was needed (inferred from what the earlier round shows)
    for i in range(len(rounds) - 1):
        r, nxt = rounds[i], rounds[i + 1]
        why = []
        if not r['batch_check_ran']:
            why.append('no batch-check output in this round (apply only, or batch-check not finished)')
        if r['actionable_failures']:
            why.append('batch-check actionable failures: ' + ', '.join(r['actionable_failure_codes']))
        if r['strict_fail']:
            why.append(f"strict claim failures {r['strict_fail']}")
        if r['geddes_flags']:
            why.append(f"Geddes flags {r['geddes_flags']}")
        if nxt['claims_changed_from_previous'] is False:
            why.append('next round has byte-identical CLAIMS.proposed.jsonl (no claim change)')
        r['why_next_round'] = '; '.join(why) or 'not visible in outputs'
        r['why_basis'] = 'inferred from this round\'s outputs'
    return rounds


def order_texts(member):
    """Held text files a producer must read for one order: its original and the later actors' texts."""
    own, actors = {}, {}
    for s in member.get('sources', []):
        eid = s['evidence_id']
        tp = (s.get('source') or {}).get('text_path')
        if not tp:
            continue
        if eid.startswith('ORIGINAL:'):
            own[tp] = fsize(tp)
        elif eid.startswith('ACTOR_TEXT:'):
            actors[tp] = fsize(tp)
    return own, actors


def own_original_item(member):
    for s in member.get('sources', []):
        if s['evidence_id'].startswith('ORIGINAL:'):
            return (s.get('source') or {}).get('page_or_item')
    return None


def event_sources(member):
    """Sources that could show an actual event (a report, a performance, an expiry) other than the order's own
    text: TERM or FACT sources whose item is not the order's own original page."""
    own_item = own_original_item(member)
    iid = member['instrument_id']
    num = iid.split(':')[1]
    out = []
    for s in member.get('sources', []):
        eid = s['evidence_id']
        src = s.get('source') or {}
        tp = src.get('text_path') or ''
        item = src.get('page_or_item') or ''
        if not (eid.startswith('TERM:') or eid.startswith('FACT:')):
            continue
        if own_item and item == own_item:
            continue
        if 'app-executive-orders' in tp or 'app-transcriptions' in tp:
            continue  # APP mirror of the order's own text, not an event source
        out.append({'evidence_id': eid, 'status': source_status(s), 'item': item[:80],
                    'provider': '/'.join(tp.split('/')[:2]), 'text_path': tp})
    return out


def act_targets(member):
    return sorted({s['evidence_id'].split('>')[1].split(':effective')[0] for s in member.get('sources', [])
                   if s['evidence_id'].startswith('ACT:') and '>' in s['evidence_id']})


def current_sources(member):
    return [s for s in member.get('sources', []) if s['evidence_id'].startswith('CURRENT:')]


def packet_record(w, label, pk, ledgers, transcripts, prices, fixed, filed):
    scr = w['scr']
    rec = {'wave': w['wave'], 'label': label, 'packet': rel(pk)}
    rec['prep'] = parse_log(w['log'](scr, label))
    rec['prompt'] = parse_prompt(w['prompt'](scr, label))
    disp = load_json(os.path.join(pk, 'DISPATCH_CHECK.json'))
    prep = load_json(os.path.join(pk, 'PREPARE.json'))
    rec['prepared'] = disp is not None
    report_p = os.path.join(pk, 'PRODUCER_REPORT.md')
    rec['finished'] = os.path.exists(report_p)
    if not rec['prepared']:
        rec['state'] = 'prepare_failed'
        return rec, []
    rec['dispatch'] = {'wall_s': disp.get('wall_seconds'), 'state': disp.get('state'),
                       'members': len(disp.get('packet_members') or []),
                       'dispatchable': len(disp.get('dispatchable_ids') or []),
                       'source_blocked': len(disp.get('source_blocked_ids') or [])}
    rec['prepare_json'] = {k: (prep or {}).get(k) for k in ('bounded_preparation_seconds', 'readable_view_bytes',
                                                           'lossless_packet_json_bytes', 'orders')}
    # report timestamps
    if rec['finished']:
        with open(report_p, encoding='utf-8') as f:
            rt = f.read()
        ts = re.findall(r'(20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ)', rt[:600])
        rec['report'] = {'start': ts[0] if ts else None, 'end': ts[1] if len(ts) > 1 else None,
                         'bytes': len(rt.encode('utf-8'))}
        fb = None
        lines = rt.splitlines()
        for i, ln in enumerate(lines):
            if re.search(r'(?i)(opened beyond|beyond (the )?views|full-packet files)', ln):
                rest = re.sub(r'(?i)^.*?(opened beyond (the )?views?|beyond (the )?views|full-packet files opened[^:]*)[:.]?\s*', '', ln).strip(' #*:')
                tail = []
                for ln2 in lines[i + 1:]:
                    if not ln2.strip() and not tail:
                        continue
                    if ln2.startswith('#') or not ln2.strip():
                        break
                    tail.append(ln2.strip())
                fb = ' '.join([rest] + tail).strip()[:400]
                break
        rec['report']['files_beyond_views'] = fb
    else:
        rec['state'] = 'producer_running_or_not_started'
    # worker
    led = ledgers.get(label) or {}
    launch = led.get('launch') or {}
    done = led.get('done') or {}
    rec['worker'] = {'agent_id': launch.get('agent_id') or done.get('agent_id'), 'model': launch.get('model') or done.get('model'),
                     'launch': launch.get('start'), 'end': done.get('end'), 'tokens_final_context': done.get('tokens'),
                     'tool_uses': done.get('tool_uses'), 'ms': done.get('ms'),
                     'ledger_note': done.get('note'),
                     'basis': 'measured (worker ledger: tokens at hand-back = final context size, not cumulative)'}
    wk = rec['worker']
    wk['usd_est'] = dollars_bartolus(wk['tokens_final_context'], wk['tool_uses'], wk['model'], prices)
    wk['usd_basis'] = 'estimated (Bartolus model: calls=tool_uses+1, half final context re-read per call, final context written once, 800 output tokens per call)'
    if wk['tool_uses'] is not None and wk['tokens_final_context'] is not None:
        wk['est_cumulative_prompt_tokens'] = int((wk['tool_uses'] + 1) * wk['tokens_final_context'] / 2)
    tr = transcripts.get(label.split('/')[-1]) or transcripts.get(label)
    if tr:
        rec['transcripts'] = tr
    # phases
    ph = {}
    if rec['prep']:
        ph['prep_s'] = rec['prep']['wall_s']
        ph['queue_wait_s'] = secs(rec['prep']['done'], wk['launch'])
    if wk['ms'] is not None:
        ph['producer_session_s'] = round(wk['ms'] / 1000, 1)
    elif rec.get('report', {}).get('end'):
        ph['producer_session_s'] = secs(wk['launch'] or rec['report']['start'], rec['report']['end'])
        ph['producer_session_basis'] = 'measured from launch to report end (ledger end not yet recorded)'
    rounds = repair_rounds(pk)
    rec['repair_rounds'] = rounds
    ph['apply_s_total'] = round(sum(r['apply_wall_s'] or 0 for r in rounds), 2)
    bc = [r['apply_to_check_s'] for r in rounds if r['apply_to_check_s'] is not None]
    ph['batch_check_s_total'] = round(sum(bc), 1) if bc else None
    ph['batch_check_basis'] = 'measured (mtime of SUMMARY.json to mtime of CHECK_SUMMARY.json in each applied dir; includes any gap between the two commands)'
    if ph.get('producer_session_s') is not None:
        ph['producer_reasoning_s'] = round(ph['producer_session_s'] - ph['apply_s_total'] - (ph['batch_check_s_total'] or 0), 1)
        ph['producer_reasoning_basis'] = 'inferred: session minus apply and batch-check walls (includes all reading and tool latency)'
    rec['phases'] = ph
    rec['applied_versions'] = len(rounds)
    end_t = parse_ts(wk.get('end')) if wk.get('end') else None
    rec['rounds_written_after_ledger_end'] = ([r['dir'] for r in rounds if end_t and r['apply_written_utc']
                                               and parse_ts(r['apply_written_utc']) > end_t] if end_t else None)

    # members
    members = {m['instrument_id']: m for m in disp.get('members', [])}
    decisions = {}
    dp = os.path.join(pk, 'decisions.csv')
    if os.path.exists(dp):
        with open(dp, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                decisions[r['instrument_id']] = r
    assess = {}
    ap = os.path.join(pk, 'ASSESSMENT.jsonl')
    if os.path.exists(ap):
        with open(ap, encoding='utf-8') as f:
            for line in f:
                try:
                    o = json.loads(line)
                    assess[o['id']] = o
                except (ValueError, KeyError):
                    pass
    final = rounds[-1]['dir'] if rounds else None
    claims_ids = set()
    if final:
        cp = os.path.join(pk, final, 'CLAIMS.proposed.jsonl')
        if os.path.exists(cp):
            with open(cp, encoding='utf-8') as f:
                for line in f:
                    try:
                        o = json.loads(line)
                    except ValueError:
                        continue
                    iid = o.get('instrument_id') or (o.get('claim') or {}).get('instrument_id')
                    if iid:
                        claims_ids.add(iid)
    lookups_b = fsize(os.path.join(pk, 'LOOKUPS.md'))
    dispatchable = set(disp.get('dispatchable_ids') or [])
    rows = []
    packet_text_paths = {}
    for iid in disp.get('packet_members') or sorted(members):
        m = members.get(iid, {'instrument_id': iid, 'sources': [], 'research_tasks': [], 'blockers': []})
        num = iid.split(':')[1]
        view_b = fsize(os.path.join(pk, 'views', f'EO_{num}.json'))
        own, actors = order_texts(m)
        for p_, b_ in list(own.items()) + list(actors.items()):
            packet_text_paths[p_] = b_
        dec = decisions.get(iid, {})
        a = assess.get(iid, {})
        outcome = (dec.get('outcome') or '').strip()
        if rec['finished']:
            if iid not in dispatchable:
                final_outcome = 'dispatch_blocked'
            elif outcome == 'submit':
                final_outcome = 'submitted'
            elif outcome in ('blocked', 'unresolved'):
                final_outcome = outcome
            else:
                final_outcome = outcome or 'unknown'
        else:
            final_outcome = 'pending'
        blocker = a.get('blocker') or ''
        if not blocker and iid not in dispatchable:
            blocker = '; '.join(f"{b['evidence_id']} ({source_status(b)})" for b in m.get('blockers', []))
        if iid not in dispatchable:
            bkind = 'own_original_custody_only' if any('ORIGINAL:' in b['evidence_id'] or 'CLAUSES:' in b['evidence_id']
                                                       for b in m.get('blockers', [])) else classify_block(blocker)
        else:
            bkind = classify_block(blocker) if final_outcome in ('blocked', 'unresolved') else ''
        ev = event_sources(m)
        tasks = sorted({t['kind'] for t in m.get('research_tasks', [])})
        f = filed.get(iid, {})
        rows.append({
            'wave': w['wave'], 'packet': label, 'instrument_id': iid,
            'route': (rec['prompt'] or {}).get('route') or ('pc' if re.match(r'^p\d\d$', label) else ''),
            'assigned': int(iid in dispatchable), 'dispatch_blocked': int(iid not in dispatchable),
            'outcome': final_outcome, 'decisions_outcome': outcome,
            'in_final_claims_file': int(iid in claims_ids),
            'upheld_a': f.get('upheld_a', ''), 'upheld_b': f.get('upheld_b', ''), 'filed': f.get('filed', ''),
            'assessment_operative_force': a.get('operative_force_at_cutoff', ''),
            'assessment_formal_validity': a.get('formal_validity_at_cutoff', ''),
            'assessment_first_cause': a.get('first_cause', ''),
            'block_kind': bkind, 'blocker': blocker[:400],
            'view_bytes': view_b, 'view_tokens_est': tok(view_b),
            'own_original_bytes': sum(v or 0 for v in own.values()),
            'actor_texts_bytes': sum(v or 0 for v in actors.values()),
            'actor_texts_n': len(actors),
            'lookups_share_bytes': (round(lookups_b / max(1, len(members))) if lookups_b else None),
            'research_tasks': '|'.join(tasks),
            'act_targets': '|'.join(act_targets(m)),
            'event_sources_n': len(ev),
            'event_sources_held': sum(1 for e in ev if e['status'] in PASS_STATUSES),
            'event_sources_custody_only': sum(1 for e in ev if e['status'] == 'custody_record_only'),
            'event_sources_not_held': sum(1 for e in ev if e['status'] in ('not_held', 'held_but_different_hash')),
            'event_items': '|'.join(sorted({e['item'] for e in ev}))[:300],
            'event_providers': '|'.join(sorted({e['provider'] for e in ev})),
            'current_sources_n': len(current_sources(m)),
            'current_sources_held': sum(1 for s in current_sources(m) if source_status(s) in PASS_STATUSES),
            'has_filed_claim': int(bool(((m.get('readiness_scope') or {}).get('required_evidence_ids')) is not None)),
            'state': m.get('state'),
        })
    # sources DISPATCH_CHECK reports as held whose text file is absent now or was written after the producer launched
    launch_t = parse_ts(wk['launch']) if wk.get('launch') else None
    held_missing, held_late, late_dirs = 0, 0, {}
    seen_tp = set()
    for m in members.values():
        for s_ in m.get('sources', []):
            tp = (s_.get('source') or {}).get('text_path')
            if not tp or tp in seen_tp or source_status(s_) not in PASS_STATUSES:
                continue
            seen_tp.add(tp)
            ap_ = os.path.join(REPO, tp)
            if not os.path.exists(ap_):
                held_missing += 1
            elif launch_t and wk.get('end'):
                mt = datetime.fromtimestamp(os.path.getmtime(ap_), timezone.utc)
                end_t = parse_ts(wk['end'])
                if end_t and mt > launch_t:
                    held_late += 1
                    k = '/'.join(tp.split('/')[:2])
                    late_dirs[k] = late_dirs.get(k, 0) + 1
    rec['materialization'] = {'held_sources_checked': len(seen_tp), 'held_text_missing_now': held_missing,
                              'held_text_written_after_producer_launch': held_late, 'late_by_job': late_dirs,
                              'basis': 'measured file existence and mtime; a file written after launch was absent or '
                                       'different while the producer ran (inferred)'}
    # view composition: bytes by top-level section over this packet's views
    vsec = {}
    for r in rows:
        vp = os.path.join(pk, 'views', f"EO_{r['instrument_id'].split(':')[1]}.json")
        v = load_json(vp)
        if isinstance(v, dict):
            for k, val in v.items():
                vsec[k] = vsec.get(k, 0) + len(json.dumps(val, ensure_ascii=False).encode('utf-8'))
    rec['view_sections_bytes'] = dict(sorted(vsec.items(), key=lambda x: -x[1]))
    rec['lookups_md_bytes'] = lookups_b
    rec['held_texts_unique_bytes'] = sum(v or 0 for v in packet_text_paths.values())
    rec['held_texts_unique_n'] = len(packet_text_paths)
    # per-packet counts
    cnt = {'members': len(rows), 'assigned': sum(r['assigned'] for r in rows),
           'dispatch_blocked': sum(r['dispatch_blocked'] for r in rows)}
    for k in ('submitted', 'blocked', 'unresolved', 'pending'):
        cnt[k] = sum(1 for r in rows if r['outcome'] == k)
    cnt['filed'] = sum(1 for r in rows if str(r['filed']) == '1') if filed else None
    cnt['upheld_both'] = (sum(1 for r in rows if str(r['upheld_a']) == '1' and str(r['upheld_b']) == '1')
                          if filed else None)
    rec['counts'] = cnt
    t = wk['tokens_final_context']
    usd = wk['usd_est']
    def per(x, n):
        return None if (x is None or not n) else round(x / n, 4 if isinstance(x, float) else 0)
    rec['unit_costs'] = {
        'tokens_per_attempted': per(t, cnt['assigned']), 'usd_est_per_attempted': per(usd, cnt['assigned']),
        'tokens_per_member': per(t, cnt['members']),
        'tokens_per_submitted': per(t, cnt['submitted']), 'usd_est_per_submitted': per(usd, cnt['submitted']),
        'tokens_per_filed': per(t, cnt['filed']) if cnt['filed'] else None,
        'usd_est_per_filed': per(usd, cnt['filed']) if cnt['filed'] else None,
        'basis': 'tokens measured (final context); dollars estimated; producer only (review not yet run)'}
    # fixed share
    pb = (rec['prompt'] or {}).get('bytes') or 0
    fixed_asked = pb + fixed['asked_bytes']
    fixed_whole = pb + fixed['whole_files_bytes']
    per_order_b = sum((r['view_bytes'] or 0) for r in rows if r['assigned']) + (lookups_b or 0) + rec['held_texts_unique_bytes']
    rec['reading'] = {
        'prompt_bytes': pb, 'fixed_list_asked_bytes': fixed['asked_bytes'], 'fixed_list_whole_bytes': fixed['whole_files_bytes'],
        'fixed_total_asked_tokens_est': tok(fixed_asked), 'fixed_total_whole_tokens_est': tok(fixed_whole),
        'lookups_md_tokens_est': tok(lookups_b),
        'assigned_views_tokens_est': tok(sum((r['view_bytes'] or 0) for r in rows if r['assigned'])),
        'held_texts_tokens_est': tok(rec['held_texts_unique_bytes']),
        'per_packet_reading_tokens_est': tok(per_order_b),
        'basis': 'bytes measured; tokens estimated as bytes/4; what each producer actually opened is not visible without transcripts'}
    if t:
        rec['reading']['fixed_share_of_final_context_asked'] = round(tok(fixed_asked) / t, 3)
        rec['reading']['fixed_share_of_final_context_whole'] = round(tok(fixed_whole) / t, 3)
        rec['reading']['per_packet_reading_share_of_final_context_if_all_read'] = round(tok(per_order_b) / t, 3)
        rec['reading']['share_basis'] = ('estimated upper bound: assumes the producer read the whole fixed list; '
                                         'because the fixed part is loaded first it is re-read at nearly every call, '
                                         'so its share of cumulative prompt tokens is close to its share of final context')
    return rec, rows


# ---------------------------------------------------------------- pre-screens

def prescreens(rows, mass_targets):
    """Zero-token pre-screens on packet data available before any producer runs. Returns per-rule results."""
    def r_dispatch(r):
        return r['dispatch_blocked'] == 1

    def r_custody_event(r):
        # order needs an actual-event fact, the event leads exist, and none of them has held bytes
        return ('actual_event_fact' in r['research_tasks'] and r['event_sources_n'] > 0
                and r['event_sources_held'] == 0)

    def r_custody_event_cleanup(r):
        # as above, and the only held later actor is a cleanup revocation table
        acts = [a for a in r['act_targets'].split('|') if a]
        return r_custody_event(r) and bool(acts) and all(a in mass_targets for a in acts)

    def r_event_none_held(r):
        # order needs an actual-event fact and no event source with held bytes exists (leads or not)
        return 'actual_event_fact' in r['research_tasks'] and r['event_sources_held'] == 0

    def r_no_current_law(r):
        return ('operative_current_law' in r['research_tasks'] and r['current_sources_held'] == 0)

    rules = {
        'R0_dispatch_blocked': (r_dispatch, 'DISPATCH_CHECK already marks the order source_blocked'),
        'R1_event_leads_custody_only': (r_custody_event, 'order needs an actual-event fact (actual_event_fact task); '
                                         'every event lead other than its own text is custody_record_only or not held'),
        'R1c_event_leads_custody_only_and_only_cleanup_revocation': (
            r_custody_event_cleanup, 'R1 and every held later actor (ACT target) is a cleanup revocation table '
                                     f'(an ACT target shared by >= {MASS_REVOCATION_MIN_TARGETS} scanned members)'),
        'R3_event_needed_none_held': (r_event_none_held, 'order needs an actual-event fact and no event source '
                                      'other than its own text has held bytes (custody-only leads or no leads)'),
        'R3r_R3_on_correction_route_only': (lambda r: r.get('route') == 'correction' and r_event_none_held(r),
                                            'R3 applied only to correction-route packets'),
        'R2_current_law_needed_none_held': (r_no_current_law, 'order needs a current-law predicate '
                                            '(operative_current_law task) and no CURRENT:* source has held bytes'),
    }
    out = {}
    done = [r for r in rows if r['outcome'] not in ('pending', 'unknown')]
    pend = [r for r in rows if r['outcome'] == 'pending']
    for name, (fn, desc) in rules.items():
        blocked = [r for r in done if r['outcome'] in ('blocked', 'unresolved', 'dispatch_blocked')]
        submitted = [r for r in done if r['outcome'] == 'submitted']
        pred_b = [r for r in blocked if fn(r)]
        pred_s = [r for r in submitted if fn(r)]
        assigned_blocked = [r for r in blocked if r['outcome'] != 'dispatch_blocked']
        out[name] = {
            'rule': desc,
            'finished_orders_scored': len(done),
            'actual_blocks': len(blocked), 'actual_blocks_excluding_dispatch': len(assigned_blocked),
            'predicted_and_blocked': len(pred_b),
            'predicted_and_blocked_excluding_dispatch': sum(1 for r in assigned_blocked if fn(r)),
            'hit_rate': round(len(pred_b) / len(blocked), 3) if blocked else None,
            'hit_rate_excluding_dispatch': (round(sum(1 for r in assigned_blocked if fn(r)) / len(assigned_blocked), 3)
                                            if assigned_blocked else None),
            'submitted_scored': len(submitted),
            'predicted_but_submitted': len(pred_s),
            'false_block_rate': round(len(pred_s) / len(submitted), 3) if submitted else None,
            'false_block_basis': ('measured against producer outcomes only; a submission later rejected by review '
                                  'would make a "false block" a correct one') if submitted else
                                 'not measurable yet: no finished order was submitted',
            'by_block_kind': {k: {'blocks': sum(1 for r in blocked if (r['block_kind'] or 'unstated') == k),
                                  'predicted': sum(1 for r in blocked if (r['block_kind'] or 'unstated') == k and fn(r))}
                              for k in sorted({(r['block_kind'] or 'unstated') for r in blocked})},
            'predicted_but_submitted_ids': sorted(r['instrument_id'] for r in pred_s),
            'predicted_ids_finished': sorted(r['instrument_id'] for r in done if fn(r)),
            'prediction_for_pending_orders': {'pending_scored': len(pend), 'predicted_block': sum(1 for r in pend if fn(r)),
                                              'ids': sorted(r['instrument_id'] for r in pend if fn(r))},
        }
    return out


# ---------------------------------------------------------------- past wave comparison

def bartolus_comparison(prices):
    import subprocess
    def show(path):
        try:
            return subprocess.run(['git', '-C', REPO, 'show', f'origin/main:{path}'], capture_output=True, text=True,
                                  timeout=30).stdout
        except Exception:
            return ''
    w = show('research/excavator/claude-bartolus-2026-11-24/WORKERS.csv')
    rp = show('research/excavator/claude-bartolus-2026-11-24/REPORT.md')
    if not w:
        return None
    workers = list(csv.DictReader(w.splitlines()))
    batches = {}
    for line in rp.splitlines():
        m = re.match(r'\|\s*([a-z]\d\d)\s*\|[^|]*\|\s*(\d+)[^|]*\|\s*(\d+)\s*\|\s*(\d+)', line)
        if m:
            batches[m.group(1)] = {'attempted': int(m.group(2)), 'submitted': int(m.group(3)), 'filed': int(m.group(4))}
    for b in batches.values():
        b.update({'producer_tokens': 0, 'producer_tool_uses': 0, 'producer_ms': 0, 'producer_usd_est': 0.0,
                  'review_tokens': 0, 'review_usd_est': 0.0, 'producer_sessions': 0, 'review_sessions': 0})
    for r in workers:
        lab = r['label']
        keys = [k for k in batches if lab.startswith(k) or lab.endswith(k) or ('+' in lab and k in lab.split('-')[0].split('+'))]
        if lab.startswith('status-'):
            keys = [lab.split('-', 1)[1]]
        if not keys:
            continue
        t, tu, ms = int(r['tokens'] or 0), int(r['tool_uses'] or 0), int(r['ms'] or 0)
        usd = dollars_bartolus(t, tu, r['model'], prices) or 0.0
        for k in keys:
            if k not in batches:
                continue
            share = 1 / len(keys)
            b = batches[k]
            if r['role'] == 'producer':
                b['producer_tokens'] += t * share
                b['producer_tool_uses'] += tu * share
                b['producer_ms'] += ms * share
                b['producer_usd_est'] += usd * share
                b['producer_sessions'] += 1
            else:
                b['review_tokens'] += t * share
                b['review_usd_est'] += usd * share
                b['review_sessions'] += 1
    for k, b in batches.items():
        for f in ('producer_tokens', 'producer_tool_uses', 'producer_ms', 'review_tokens'):
            b[f] = int(round(b[f]))
        b['producer_usd_est'] = round(b['producer_usd_est'], 2)
        b['review_usd_est'] = round(b['review_usd_est'], 2)
        b['producer_tokens_per_attempted'] = round(b['producer_tokens'] / b['attempted']) if b['attempted'] else None
        b['producer_min_per_attempted'] = round(b['producer_ms'] / 60000 / b['attempted'], 2) if b['attempted'] else None
        tot = b['producer_usd_est'] + b['review_usd_est']
        b['usd_est_per_filed'] = round(tot / b['filed'], 2) if b['filed'] else None
    tot_att = sum(b['attempted'] for b in batches.values())
    tot_fil = sum(b['filed'] for b in batches.values())
    tot_p = sum(b['producer_usd_est'] for b in batches.values())
    tot_r = sum(b['review_usd_est'] for b in batches.values())
    return {'source': 'git show origin/main:research/excavator/claude-bartolus-2026-11-24/{WORKERS.csv,REPORT.md}',
            'batches': batches, 'attempted': tot_att, 'filed': tot_fil,
            'producer_usd_est': round(tot_p, 2), 'review_usd_est': round(tot_r, 2),
            'usd_est_per_filed_producer_plus_review': round((tot_p + tot_r) / tot_fil, 2) if tot_fil else None,
            'review_share_of_usd_est': round(tot_r / (tot_p + tot_r), 3) if (tot_p + tot_r) else None,
            'basis': 'tokens measured; dollars estimated with the same Bartolus model; workers mapped to batches by label (inferred); coordinator excluded'}


# ---------------------------------------------------------------- second pass: per-call transcripts

FIXED_LIST_MARKERS = ('PRODUCTION_ROUTE.md', 'CLAIM_SCHEMA.md', 'BATCH.md', 'owner_rulings', 'PRODUCER_BRIEF.md')


def tool_category(name, inp):
    s = json.dumps(inp, ensure_ascii=False) if inp is not None else ''
    if name == 'Read' and 'prompts/producer-' in s:
        return 'read_prompt_file'
    if any(m in s for m in FIXED_LIST_MARKERS):
        return 'fixed_reading_list'
    if 'LOOKUPS.md' in s:
        return 'lookups_md'
    if '/views/' in s or 'views\\\\' in s or 'views/EO_' in s:
        return 'views'
    if 'kit.py apply' in s or 'kit.py\\" apply' in s:
        return 'kit_apply'
    if 'batch-check' in s:
        return 'kit_batch_check'
    if 'geddes' in s:
        return 'geddes'
    if 'kit.py view' in s:
        return 'kit_view'
    if 'cruden' in s or 'texts/' in s or 'fr-originals' in s or 'SOURCES.jsonl' in s:
        return 'held_texts_and_source_records'
    if 'PACKET.json' in s or 'load_packet' in s or 'READ.md' in s or 'DISPATCH_CHECK' in s:
        return 'full_packet_files'
    if name in ('Write', 'Edit') or 'decisions.csv' in s or 'clauses.csv' in s or 'ASSESSMENT' in s:
        return 'writing_sheets_and_reports'
    if 'date -u' in s:
        return 'clock'
    return f'other_{name}'


def analyze_transcript(path, prices):
    """cost.py method (last usage per message id, priced per call) plus a per-call attribution: the growth of the
    prompt between call i and call i+1 is charged to the tool results of call i; a chunk added at call i is re-read
    at cache-read price on every later call."""
    calls, order, tool_uses, results = {}, [], {}, {}
    ts_first = ts_last = None
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            ts = e.get('timestamp')
            if ts:
                ts_first = ts_first or ts
                ts_last = ts
            msg = e.get('message') if isinstance(e, dict) else None
            if not isinstance(msg, dict):
                continue
            if e.get('type') == 'assistant' and msg.get('id'):
                mid = msg['id']
                if mid not in calls:
                    order.append(mid)
                    calls[mid] = {'model': msg.get('model'), 'ts': ts, 'tools': []}
                if isinstance(msg.get('usage'), dict):
                    calls[mid]['usage'] = msg['usage']
                    calls[mid]['ts_end'] = ts
                for c in msg.get('content') or []:
                    if isinstance(c, dict) and c.get('type') == 'tool_use':
                        tool_uses[c['id']] = (mid, c.get('name'), c.get('input'))
                        calls[mid]['tools'].append(c['id'])
            elif e.get('type') == 'user' and isinstance(msg.get('content'), list):
                for c in msg['content']:
                    if isinstance(c, dict) and c.get('type') == 'tool_result':
                        results[c.get('tool_use_id')] = (len(json.dumps(c.get('content'), ensure_ascii=False).encode('utf-8')), ts)
    rows = []
    tot = {'input': 0, 'cache_read': 0, 'cache_write_5m': 0, 'cache_write_1h': 0, 'output': 0}
    usd = 0.0
    for mid in order:
        c = calls[mid]
        u = c.get('usage') or {}
        p = price_for(c['model'], prices)
        cc = u.get('cache_creation') or {}
        w1, w5 = cc.get('ephemeral_1h_input_tokens', 0) or 0, cc.get('ephemeral_5m_input_tokens', 0) or 0
        wu = max((u.get('cache_creation_input_tokens') or 0) - w1 - w5, 0)
        inp, cr, out = u.get('input_tokens') or 0, u.get('cache_read_input_tokens') or 0, u.get('output_tokens') or 0
        cost = 0.0
        if p:
            cost = (inp * p['input'] + cr * p['cache_read'] + w1 * p['cache_write_1h'] + (w5 + wu) * p['cache_write_5m']
                    + out * p['output']) / 1e6
        usd += cost
        tot['input'] += inp
        tot['cache_read'] += cr
        tot['cache_write_5m'] += w5 + wu
        tot['cache_write_1h'] += w1
        tot['output'] += out
        cats = [tool_category(tool_uses[t][1], tool_uses[t][2]) for t in c['tools'] if t in tool_uses]
        res_b = sum(results.get(t, (0, None))[0] for t in c['tools'])
        tool_end = max([results[t][1] for t in c['tools'] if t in results and results[t][1]] or [None]) if c['tools'] else None
        rows.append({'id': mid, 'model': c['model'], 'prompt': inp + cr + w1 + w5 + wu, 'output': out, 'usd': cost,
                     'cats': cats, 'tool_result_bytes': res_b, 'ts': c['ts'], 'ts_end': c.get('ts_end'), 'tool_end': tool_end})
    n = len(rows)
    p0 = price_for(rows[0]['model'], prices) if rows else None
    # attribution of re-read cost to what each call added
    by_cat = {}
    for i, r in enumerate(rows[:-1]):
        added = max(rows[i + 1]['prompt'] - r['prompt'], 0)
        later = n - (i + 1)
        rr = added * later * (p0['cache_read'] if p0 else 0) / 1e6 + added * (p0['cache_write_5m'] if p0 else 0) / 1e6
        cats = r['cats'] or ['assistant_text_only']
        for cat in cats:
            b = by_cat.setdefault(cat, {'calls': 0, 'tokens_added': 0, 'usd_attributed': 0.0, 'tool_result_bytes': 0})
            b['calls'] += 1 / len(cats)
            b['tokens_added'] += added / len(cats)
            b['usd_attributed'] += rr / len(cats)
            b['tool_result_bytes'] += r['tool_result_bytes'] / len(cats)
    base = rows[0]['prompt'] if rows else 0
    base_usd = (base * (n - 1) * p0['cache_read'] + base * p0['cache_write_5m']) / 1e6 if (rows and p0) else None
    out_usd = sum(r['output'] for r in rows) * (p0['output'] if p0 else 0) / 1e6
    # time: model time per call (call start to usage end) versus tool time (tool_use to tool_result)
    def dt(a, b):
        try:
            fa = datetime.fromisoformat(a.replace('Z', '+00:00'))
            fb = datetime.fromisoformat(b.replace('Z', '+00:00'))
            return (fb - fa).total_seconds()
        except (AttributeError, ValueError, TypeError):
            return None
    tool_time = {}
    for i, r in enumerate(rows):
        if r['tool_end'] and r['ts_end']:
            d = dt(r['ts_end'], r['tool_end'])
            if d is not None and d >= 0:
                for cat in r['cats'] or ['none']:
                    tool_time[cat] = tool_time.get(cat, 0) + d / max(1, len(r['cats']))
    span = dt(ts_first, ts_last)
    return {
        'file': os.path.basename(path), 'calls': n, 'usd_list_price': round(usd, 4), **tot,
        'first_call_prompt_tokens': base, 'final_prompt_tokens': rows[-1]['prompt'] if rows else None,
        'max_prompt_tokens': max((r['prompt'] for r in rows), default=0),
        'base_context_usd': round(base_usd, 4) if base_usd is not None else None,
        'base_context_share': round(base_usd / usd, 3) if (base_usd and usd) else None,
        'output_usd': round(out_usd, 4), 'output_share': round(out_usd / usd, 3) if usd else None,
        'cache_read_usd': round(tot['cache_read'] * (p0['cache_read'] if p0 else 0) / 1e6, 4),
        'by_category': {k: {'calls': round(v['calls'], 1), 'tokens_added': int(v['tokens_added']),
                            'usd_attributed': round(v['usd_attributed'], 4),
                            'share_of_usd': round(v['usd_attributed'] / usd, 3) if usd else None}
                        for k, v in sorted(by_cat.items(), key=lambda x: -x[1]['usd_attributed'])},
        'tool_wall_s_by_category': {k: round(v, 1) for k, v in sorted(tool_time.items(), key=lambda x: -x[1])},
        'session_span_s': span,
        'basis': ('measured: per-call usage priced at PRICES.json list rates (cost.py method). Attribution is estimated: '
                  'prompt growth after a call is charged to that call\'s tool results and re-read at cache-read price on '
                  'every later call; first-call prompt is the system prompt, tool definitions and task text'),
    }


# ---------------------------------------------------------------- second pass: worker ledger with passes

def ledger_rows(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('label,'):
                continue
            parts = line.split(',')
            rec = {'label': parts[0], 'agent_id': parts[1], 'role': parts[2], 'model': parts[3]}
            last = None
            for piece in parts[4:]:
                if re.match(r'^[a-z_]+=', piece):
                    k, v = piece.split('=', 1)
                    rec[k] = v
                    last = k
                elif last:
                    rec[last] += ',' + piece
            if 'tokens_total' in rec and 'tokens' not in rec:
                rec['tokens'] = rec['tokens_total']
            for k in ('tokens', 'tool_uses', 'ms'):
                try:
                    rec[k] = int(rec[k]) if k in rec else None
                except ValueError:
                    rec[k] = None
            rows.append(rec)
    return rows


def session_costs(rows, prices, k_by_model):
    """Group ledger rows by agent id. A later row of the same agent is cumulative when its tool uses and ms are not
    smaller than the previous row's (it then replaces it); otherwise it is an incremental pass and its cost is added
    with every call re-reading the full context (inferred rule)."""
    by_agent = {}
    for r in rows:
        by_agent.setdefault(r['agent_id'], []).append(r)
    out = {}
    for aid, rs in by_agent.items():
        rs.sort(key=lambda r: r.get('end') or '')
        base = rs[0]
        label = base['label']
        tokens, tu, ms, usd, unknown = base['tokens'], base['tool_uses'], base['ms'], 0.0, []
        usd = dollars_bartolus(tokens, tu, base['model'], prices)
        calls = (tu + 1) if tu is not None else None
        for r in rs[1:]:
            if r['tokens'] is None or r['tool_uses'] is None:
                unknown.append(r['label'])
                continue
            if tu is not None and r['tool_uses'] >= tu and (r['ms'] or 0) >= (ms or 0):
                tokens, tu, ms = r['tokens'], r['tool_uses'], r['ms']
                usd = dollars_bartolus(tokens, tu, r['model'], prices)
                calls = tu + 1
            else:
                p = price_for(r['model'], prices)
                n = r['tool_uses'] + 1
                add = (n * r['tokens'] * p['cache_read'] + max(r['tokens'] - (tokens or 0), 0) * p['cache_write_5m']
                       + 800 * n * p['output']) / 1e6 if p else 0
                usd = (usd or 0) + add
                tokens = r['tokens']
                tu = (tu or 0) + r['tool_uses']
                ms = (ms or 0) + (r['ms'] or 0)
                calls = (calls or 0) + n
        model = base['model']
        k = k_by_model.get(model)
        out[aid] = {'label': label, 'labels': [r['label'] for r in rs], 'role': base['role'], 'model': model,
                    'final_context_tokens': tokens, 'tool_uses': tu, 'calls_est': calls, 'ms': ms,
                    'usd_bartolus_est': round(usd, 4) if usd is not None else None,
                    'usd_calibrated_est': round(usd * k, 4) if (usd is not None and k) else None,
                    'passes_without_usage': unknown,
                    'fields': {kk: vv for kk, vv in base.items() if kk not in ('label', 'agent_id', 'role', 'model')}}
        for r in rs[1:]:
            for kk in ('submitted', 'blocked', 'upheld', 'rejected', 'reviewed'):
                if kk in r:
                    out[aid]['fields'][kk] = r[kk]
    return out


# ---------------------------------------------------------------- second pass: reviews

def canon_sha(o):
    import hashlib
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()


def read_jsonl(p):
    out = []
    if not os.path.exists(p):
        return out
    with open(p, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    return out


def review_batches():
    """(batch label, packet dir, review-set dir) for every reviewed batch."""
    out = []
    B = os.path.join(REPO, 'research/excavator/claude-bracton-2026-11-25')
    for d in sorted(glob.glob('/home/claude/bracton-scr/review/*')):
        lab = os.path.basename(d)
        pk = os.path.join(B, lab, 'packet')
        alias = os.path.join(B, lab, 'PACKET_IS_AT.txt')
        if not os.path.isdir(pk) and os.path.exists(alias):
            with open(alias, encoding='utf-8') as f:
                m = re.search(r'(\.\./\S+?)\s', f.read())
            if m:
                pk = os.path.normpath(os.path.join(B, lab, m.group(1)))
        out.append(('bracton', lab, pk, d))
    J = os.path.join(REPO, 'research/excavator/claude-junto-lean-2026-11-25')
    for d in sorted(glob.glob('/home/claude/junto-scr/review/arm*/*')):
        lab = os.path.relpath(d, '/home/claude/junto-scr/review')
        out.append(('junto-lean', lab, os.path.join(J, lab, 'packet'), d))
    return out


def review_measures(sessions):
    by_label = {s['label']: s for s in sessions.values()}
    batches = []
    for wave, lab, pk, rd in review_batches():
        genuine = {o['instrument_id']: canon_sha(o) for o in read_jsonl(os.path.join(rd, 'GENUINE_CONTROLS.jsonl'))}
        rset = read_jsonl(os.path.join(rd, 'REVIEW_SET.jsonl'))
        set_ids = [o.get('instrument_id') for o in rset]
        seq = load_json(os.path.join(rd, 'SEQ_B.json'))
        rv = os.path.join(pk, 'reviews')
        arms = {}
        for arm in ('A', 'B'):
            blind = read_jsonl(os.path.join(rv, f'BLIND_REVIEW_{arm}.jsonl'))
            after = read_jsonl(os.path.join(rv, f'AFTER_REVEAL_{arm}.jsonl'))
            if not blind and not after:
                continue
            ctrl_caught = ctrl_missed = gen_rej = gen_up = 0
            final = {}
            rej_fields = []
            for o in blind:
                iid = o['instrument_id']
                is_ctrl = iid in genuine and o.get('claim_sha256') != genuine[iid]
                v = o.get('verdict', '')
                if is_ctrl:
                    if v.startswith('rejected'):
                        ctrl_caught += 1
                    else:
                        ctrl_missed += 1
                else:
                    final[iid] = v
                    if v.startswith('rejected'):
                        gen_rej += 1
                        rej_fields.append(str(o.get('defects'))[:160])
                    else:
                        gen_up += 1
            for o in after:
                final[o['instrument_id']] = o.get('verdict', '')
            sess = by_label.get(f'{lab}-{arm}')
            arms[arm] = {'blind_reviews': len(blind), 'after_reveal_reviews': len(after),
                         'controls_caught': ctrl_caught, 'controls_missed': ctrl_missed,
                         'blind_genuine_rejected': gen_rej, 'blind_genuine_upheld': gen_up,
                         'final_upheld_ids': sorted(i for i, v in final.items() if v.startswith('upheld')),
                         'final_rejected_ids': sorted(i for i, v in final.items() if v.startswith('rejected')),
                         'genuine_rejection_defect_fields': rej_fields,
                         'session': ({k: sess[k] for k in ('final_context_tokens', 'tool_uses', 'ms', 'usd_bartolus_est',
                                                            'usd_calibrated_est', 'model')} if sess else None)}
        if not arms:
            continue
        both = set(arms.get('A', {}).get('final_upheld_ids', [])) & set(arms.get('B', {}).get('final_upheld_ids', []))
        disagree = []
        if 'A' in arms and 'B' in arms:
            for iid in set_ids:
                va = 'up' if iid in arms['A']['final_upheld_ids'] else ('rej' if iid in arms['A']['final_rejected_ids'] else None)
                vb = 'up' if iid in arms['B']['final_upheld_ids'] else ('rej' if iid in arms['B']['final_rejected_ids'] else None)
                if va and vb and va != vb:
                    disagree.append(iid)
        compared = sum(1 for iid in set_ids if all(
            iid in arms[a]['final_upheld_ids'] + arms[a]['final_rejected_ids'] for a in ('A', 'B') if a in arms)) if len(arms) == 2 else 0
        usd = [a['session']['usd_calibrated_est'] for a in arms.values() if a.get('session') and a['session'].get('usd_calibrated_est') is not None]
        tok = [a['session']['final_context_tokens'] for a in arms.values() if a.get('session') and a['session'].get('final_context_tokens')]
        batches.append({'wave': wave, 'batch': lab, 'claims_in_set': len(set_ids), 'set_bytes': fsize(os.path.join(rd, 'REVIEW_SET.jsonl')),
                        'controls_planted': len(genuine), 'arms': arms, 'upheld_by_both': sorted(both),
                        'arm_disagreements': sorted(disagree), 'claims_compared_by_both': compared,
                        'sequential_B': seq,
                        'review_usd_calibrated_est': round(sum(usd), 4) if usd else None,
                        'review_final_context_tokens': sum(tok) if tok else None,
                        'review_usd_per_upheld': round(sum(usd) / len(both), 4) if (usd and both) else None})
    # totals
    tot = {'batches': len(batches), 'claims_reviewed': sum(b['claims_in_set'] for b in batches),
           'controls_planted': sum(b['controls_planted'] for b in batches)}
    tot['controls_caught_arm_sessions'] = sum(a['controls_caught'] for b in batches for a in b['arms'].values())
    tot['controls_missed_arm_sessions'] = sum(a['controls_missed'] for b in batches for a in b['arms'].values())
    tot['blind_genuine_rejections'] = sum(a['blind_genuine_rejected'] for b in batches for a in b['arms'].values())
    rej_all = tot['controls_caught_arm_sessions'] + tot['blind_genuine_rejections']
    tot['blind_rejections'] = rej_all
    tot['share_of_blind_rejections_that_are_control_catches'] = round(tot['controls_caught_arm_sessions'] / rej_all, 3) if rej_all else None
    tot['upheld_by_both'] = sum(len(b['upheld_by_both']) for b in batches)
    tot['claims_compared_by_both'] = sum(b['claims_compared_by_both'] for b in batches)
    tot['arm_disagreements'] = sum(len(b['arm_disagreements']) for b in batches)
    usd = [b['review_usd_calibrated_est'] for b in batches if b['review_usd_calibrated_est'] is not None]
    tot['review_usd_calibrated_est'] = round(sum(usd), 3) if usd else None
    tot['review_usd_per_upheld'] = round(sum(usd) / tot['upheld_by_both'], 3) if (usd and tot['upheld_by_both']) else None
    # fixed per-session overhead: least squares of final-context tokens on claims in set
    pts = [(b['claims_in_set'], a['session']['final_context_tokens'], (b['set_bytes'] or 0)) for b in batches
           for arm, a in b['arms'].items() if a.get('session') and a['session'].get('final_context_tokens')
           and not (b.get('sequential_B') and arm == 'B')]
    fit = None
    if len(pts) >= 3:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        sxx = sum((x - mx) ** 2 for x in xs)
        if sxx:
            b1 = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
            fit = {'sessions': len(pts), 'intercept_tokens': int(my - b1 * mx), 'tokens_per_claim': int(b1),
                   'by_set_size': {}}
            for n in sorted(set(xs)):
                v = [y for x, y in zip(xs, ys) if x == n]
                fit['by_set_size'][str(n)] = {'sessions': len(v), 'mean_final_context_tokens': int(sum(v) / len(v)),
                                              'tokens_per_claim': int(sum(v) / len(v) / n)}
    tot['reviewer_session_fit'] = fit
    tot['basis'] = ('verdicts measured from reviews/ files; a blind review is a control when its claim hash differs from '
                    'the genuine claim in GENUINE_CONTROLS.jsonl; final verdict = after-reveal verdict when present; '
                    'dollars estimated (Bartolus model times the transcript calibration factor); regression inferred')
    return {'batches': batches, 'totals': tot}


# ---------------------------------------------------------------- second pass: filing, trial arms, Olney, refresh

def filing_measures():
    filed = {}
    for p in sorted(glob.glob(os.path.join(REPO, 'research/readiness/claims/junto-arm*-2026-11-25-*-refresh.jsonl'))):
        m = re.search(r'(arm[01])-([ab]\d\d)-refresh', p)
        for o in read_jsonl(p):
            filed[o.get('instrument_id')] = f'{m.group(1)}/{m.group(2)}' if m else rel(p)
    props = {}
    for p in sorted(glob.glob(os.path.join(REPO, 'research/excavator/claude-bracton-2026-11-25/*-refresh/REPLACEMENT_PROPOSAL.jsonl'))):
        lab = os.path.basename(os.path.dirname(p)).replace('-refresh', '')
        for o in read_jsonl(p):
            iid = o.get('instrument_id') or (o.get('claim') or {}).get('instrument_id') or o.get('id')
            props[iid] = lab
    return {'trial_filed': filed, 'trial_filed_by_batch': _count(filed.values()),
            'bracton_replacement_proposals': props, 'bracton_proposals_by_batch': _count(props.values()),
            'basis': 'measured (claim and proposal files)'}


def _count(vals):
    c = {}
    for v in vals:
        c[v] = c.get(v, 0) + 1
    return dict(sorted(c.items()))


def refresh_measures(prices):
    d = load_json('/home/claude/junto-scr/REFRESH_RESULT.json', {}) or {}
    orders = d.get('orders') or {}
    verdicts = _count(o.get('verdict') for o in orders.values())
    logs = glob.glob('/home/claude/junto-scr/refresh_logs/*')
    mt = sorted(os.path.getmtime(p) for p in logs)
    refresh_pk = sorted(glob.glob(os.path.join(REPO, 'research/excavator/*-2026-11-25/**/*-refresh*/**/PREPARE.json'), recursive=True))
    prep_mt = sorted(os.path.getmtime(p) for p in refresh_pk)
    allm = mt + prep_mt
    tools_b = sum(fsize(p) or 0 for p in ('/home/claude/junto-scr/refresh_tool.py', '/home/claude/junto-scr/stage_refresh.py',
                                            '/home/claude/junto-scr/run_line.sh'))
    wall_logged = 0.0
    for p in logs:
        if p.endswith('.log'):
            try:
                with open(p, encoding='utf-8', errors='replace') as f:
                    t = f.read()
                m = re.findall(r'"wall_seconds":\s*([\d.]+)', t)
                wall_logged += max(float(x) for x in m) if m else 0
            except OSError:
                pass
    opus = price_for('claude-opus-5-5', prices)
    return {'orders_refreshed': len(orders), 'verdicts': verdicts,
            'checker_pass': sum(1 for o in orders.values() if o.get('actual_checker_pass')),
            'content_changed': sum(1 for o in orders.values() if o.get('verdict') == 'content_changed'),
            'refresh_packets_prepared': len(refresh_pk),
            'scripted_wall_span_s': round(max(allm) - min(allm), 1) if allm else None,
            'apply_and_batch_check_wall_logged_s': round(wall_logged, 1),
            'coordinator_tool_code_bytes': tools_b,
            'coordinator_tool_code_output_usd_est': round(tools_b / 4 * opus['output'] / 1e6, 3) if opus else None,
            'model_tokens_in_scripts': 0,
            'basis': ('measured: REFRESH_RESULT.json verdicts, file mtimes of refresh logs and refreshed PREPARE.json; '
                      'coordinator reasoning tokens are not measured; tool-code output dollars estimated as bytes/4 '
                      'output tokens at Opus list price (a floor: it excludes the coordinator context re-reads)')}


def olney_measures():
    d = load_json(os.path.join(REPO, 'jobs/olney-board-route/output/RESULT.json'), {}) or {}
    b = d.get('batches') or []
    return {'universe': d.get('universe'), 'selected': d.get('selected'), 'prepared': d.get('prepared'),
            'checker_passing': len(d.get('checker_passing') or []), 'exceptions': d.get('exceptions'),
            'exceptions_by_primary_reason': d.get('exceptions_by_primary_reason'), 'model_tokens': d.get('model_tokens'),
            'scripted_wall_s': round(sum(sum((x.get('wall_seconds') or {}).values()) for x in b) + (d.get('selection_wall_seconds') or 0), 1),
            'basis': 'measured (jobs/olney-board-route/output/RESULT.json)'}


def second_pass(args, prices, packets, pc):
    # 1. per-call transcripts and the calibration factor
    tr = {}
    if args['--transcripts'] and os.path.isdir(args['--transcripts']):
        for p in sorted(glob.glob(os.path.join(args['--transcripts'], '*.jsonl'))):
            lab = os.path.basename(p).split('-')[0]
            a = analyze_transcript(p, prices)
            L = pc.get(lab) or {}
            a['ledger_final_context_tokens'] = L.get('tokens')
            a['ledger_tool_uses'] = L.get('tool_uses')
            a['bartolus_est_usd'] = dollars_bartolus(L.get('tokens'), L.get('tool_uses'), L.get('model'), prices)
            a['measured_over_bartolus'] = (round(a['usd_list_price'] / a['bartolus_est_usd'], 3)
                                           if a.get('bartolus_est_usd') else None)
            tr[lab] = a
    ks = [a['measured_over_bartolus'] for a in tr.values() if a.get('measured_over_bartolus')]
    k = round(sum(ks) / len(ks), 3) if ks else None
    k_by_model = {'claude-sonnet-5-5': k, 'claude-opus-5-5': k} if k else {}
    # 2. sessions from every ledger
    rows = []
    for scr in ('/home/claude/bracton-scr', '/home/claude/junto-scr'):
        for r in ledger_rows(os.path.join(scr, 'WORKERS_DONE.csv')):
            r['ledger'] = os.path.basename(scr)
            rows.append(r)
    for lab, r in pc.items():
        if r.get('agent_id'):
            rows.append({'label': lab, 'agent_id': r['agent_id'], 'role': 'producer', 'model': r['model'],
                         'tokens': r['tokens'], 'tool_uses': r['tool_uses'], 'ms': r['ms'], 'end': r['end'], 'ledger': 'pc'})
    for r in rows:
        r.setdefault('end', '')
    sessions = session_costs(rows, prices, k_by_model)
    for aid, s_ in sessions.items():
        if aid in {a['file'].split('-')[1].split('.')[0] for a in tr.values()}:
            lab = s_['label']
            s_['usd_measured_transcript'] = tr.get(lab, {}).get('usd_list_price')

    def usd_of(s_):
        return s_.get('usd_measured_transcript') or s_.get('usd_calibrated_est') or 0.0
    by_role = {}
    for s_ in sessions.values():
        b = by_role.setdefault(s_['role'], {'sessions': 0, 'final_context_tokens': 0, 'usd_est': 0.0})
        b['sessions'] += 1
        b['final_context_tokens'] += s_['final_context_tokens'] or 0
        b['usd_est'] = round(b['usd_est'] + usd_of(s_), 3)
    # 3. reviews, filing, trial, Olney, refresh
    rv = review_measures(sessions)
    fil = filing_measures()
    up_by_batch = {b['batch']: len(b['upheld_by_both']) for b in rv['batches']}

    def group(pred):
        ss = [s_ for s_ in sessions.values() if pred(s_['label'])]
        return {'producer_usd_est': round(sum(usd_of(s_) for s_ in ss if s_['role'] == 'producer'), 3),
                'review_usd_est': round(sum(usd_of(s_) for s_ in ss if s_['role'] == 'reviewer'), 3),
                'other_usd_est': round(sum(usd_of(s_) for s_ in ss if s_['role'] not in ('producer', 'reviewer')), 3),
                'producer_sessions': sum(1 for s_ in ss if s_['role'] == 'producer'),
                'review_sessions': sum(1 for s_ in ss if s_['role'] == 'reviewer'),
                'passes_without_usage': sorted(x for s_ in ss for x in s_['passes_without_usage'])}
    trial = {}
    for arm in ('arm0', 'arm1'):
        g = group(lambda l, a=arm: l.startswith(a + '/'))
        nfiled = sum(1 for v in fil['trial_filed'].values() if v.startswith(arm))
        tot = g['producer_usd_est'] + g['review_usd_est']
        att = sum((p.get('counts') or {}).get('assigned') or 0 for p in packets if p['wave'] == 'junto-lean' and p['label'].startswith(arm))
        g.update({'attempted': att, 'filed': nfiled, 'usd_est_total': round(tot, 3),
                  'usd_est_per_filed': round(tot / nfiled, 3) if nfiled else None,
                  'review_usd_per_filed': round(g['review_usd_est'] / nfiled, 3) if nfiled else None})
        trial[arm] = g
    seq = [b['sequential_B'] for b in rv['batches'] if b.get('sequential_B')]
    fit = rv['totals'].get('reviewer_session_fit') or {}
    skipped = sum(x.get('skipped_genuine') or 0 for x in seq)
    trial['sequential_review'] = {
        'batches': seq, 'arm_B_claims_skipped': skipped,
        'skipped_tokens_est': (skipped * fit.get('tokens_per_claim', 0)) if fit else None,
        'basis': 'skipped counts measured (SEQ_B.json); token saving estimated as skipped claims times the fitted marginal reviewer tokens per claim'}
    bracton_c = group(lambda l: re.match(r'^c\d\d', l) is not None)
    bracton_c['upheld_or_proposed'] = sum(v for k_, v in up_by_batch.items() if re.match(r'^c\d\d$', k_))
    bracton_c['proposals'] = sum(1 for v in fil['bracton_replacement_proposals'].values() if v.startswith('c'))
    tot_c = bracton_c['producer_usd_est'] + bracton_c['review_usd_est']
    bracton_c['usd_est_per_upheld'] = round(tot_c / bracton_c['upheld_or_proposed'], 3) if bracton_c['upheld_or_proposed'] else None
    bracton_c['usd_est_per_proposal'] = round(tot_c / bracton_c['proposals'], 3) if bracton_c['proposals'] else None
    pcg = group(lambda l: re.match(r'^p\d\d', l) is not None)
    ol = group(lambda l: l.startswith('o0') or l.startswith('o1') or l.startswith('olney'))
    ol_up = up_by_batch.get('o0', 0) + up_by_batch.get('o1', 0)
    ol_props = sum(1 for v in fil['bracton_replacement_proposals'].values() if v.startswith('o'))
    ol.update({'upheld_by_both': ol_up, 'proposals': ol_props,
               'usd_est_per_proposal_review_only': round(ol['review_usd_est'] / ol_props, 3) if ol_props else None,
               'usd_est_per_proposal_with_build': round((ol['review_usd_est'] + ol['other_usd_est']) / ol_props, 3) if ol_props else None,
               'scripted': olney_measures()})
    ref = refresh_measures(prices)
    return {
        'calibration': {'factor_measured_over_bartolus': k, 'per_transcript': ks,
                        'basis': 'measured transcript list-price dollars divided by the Bartolus estimate for the same session; '
                                 'applied to every cloud session (Sonnet measured; Opus reviewers inferred)'},
        'transcripts': tr, 'sessions': sessions, 'usd_by_role': by_role,
        'reviews': rv, 'filing': fil, 'trial': trial,
        'bracton_correction_lanes': bracton_c, 'bracton_pc_lanes': pcg, 'olney': ol, 'refresh': ref,
    }


# ---------------------------------------------------------------- main

def main(argv):
    args = {'--transcripts': None, '--pc-lanes': None, '--filed': None}
    i = 0
    while i < len(argv):
        if argv[i] in args and i + 1 < len(argv):
            args[argv[i]] = argv[i + 1]
            i += 2
        else:
            sys.exit(f'unknown argument {argv[i]}')
    prices = load_prices()
    fixed = fixed_reading()
    transcripts = read_transcripts(args['--transcripts'], prices)
    filed = {}
    if args['--filed'] and os.path.exists(args['--filed']):
        with open(args['--filed'], encoding='utf-8') as f:
            for r in csv.DictReader(f):
                filed[r['instrument_id']] = r
    pc = read_pc_lanes(args['--pc-lanes'])

    packets, all_rows = [], []
    os.makedirs(os.path.join(OUT, 'packets'), exist_ok=True)
    for w in WAVES:
        launch = read_launch(os.path.join(w['scr'], 'WORKERS_LAUNCH.csv'))
        done = read_done(os.path.join(w['scr'], 'WORKERS_DONE.csv'))
        ledgers = {}
        for lab in set(launch) | set(done):
            ledgers[lab] = {'launch': launch.get(lab), 'done': done.get(lab)}
        for lab, r in pc.items():
            ledgers.setdefault(lab, {'launch': {'start': r['start'], 'agent_id': r['agent_id'], 'model': r['model']},
                                     'done': {**r}})
        root = os.path.join(REPO, w['root'])
        labels = []
        for g in w['packet_glob']:
            for d in sorted(glob.glob(os.path.join(root, g))):
                if os.path.isdir(d):
                    labels.append(os.path.relpath(d, root))
        # packets that failed prepare have no folder; pick them up from prep logs
        for lp in sorted(glob.glob(os.path.join(w['scr'], 'logs', 'prep-*.log'))):
            lab = os.path.basename(lp)[5:-4]
            if w['wave'] == 'junto-lean':
                lab = lab.replace('-', '/', 1)
            if lab not in labels:
                labels.append(lab)
        for lab in sorted(set(labels)):
            pk = os.path.join(root, lab, 'packet')
            rec, rows = packet_record(w, lab, pk, ledgers, transcripts, prices, fixed, filed)
            packets.append(rec)
            all_rows.extend(rows)
            if rows:
                fn = os.path.join(OUT, 'packets', f"{w['wave']}__{lab.replace('/', '_')}.csv")
                with open(fn, 'w', newline='', encoding='utf-8') as f:
                    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                    wr.writeheader()
                    wr.writerows(rows)

    # cleanup-revocation targets (ACT target shared by many scanned members)
    tc = {}
    for r in all_rows:
        for a in filter(None, r['act_targets'].split('|')):
            tc[a] = tc.get(a, 0) + 1
    mass = {a for a, n in tc.items() if n >= MASS_REVOCATION_MIN_TARGETS}

    finished = [p for p in packets if p.get('finished')]
    frows = [r for r in all_rows if r['outcome'] != 'pending']

    # block taxonomy with tokens on blocked orders (allocated evenly per packet: inferred)
    tok_per_order = {}
    for p in finished:
        t = (p.get('worker') or {}).get('tokens_final_context')
        u = (p.get('worker') or {}).get('usd_est')
        a = (p.get('counts') or {}).get('assigned') or 0
        tok_per_order[p['label']] = (t / a if (t and a) else None, u / a if (u and a) else None)
    tax = {}
    for r in frows:
        if r['outcome'] not in ('blocked', 'unresolved', 'dispatch_blocked'):
            continue
        k = r['block_kind'] or 'unstated'
        g = tax.setdefault(k, {'orders': 0, 'dispatch_blocked': 0, 'assigned_blocked': 0, 'tokens_alloc': 0,
                               'usd_est_alloc': 0.0, 'tokens_unknown_orders': 0, 'ids': [], 'example_blocker': ''})
        g['orders'] += 1
        g['ids'].append(r['instrument_id'])
        if r['dispatch_blocked']:
            g['dispatch_blocked'] += 1
        else:
            g['assigned_blocked'] += 1
            t, u = tok_per_order.get(r['packet'], (None, None))
            if t is None:
                g['tokens_unknown_orders'] += 1
            else:
                g['tokens_alloc'] += t
                g['usd_est_alloc'] += u or 0
        if not g['example_blocker'] and r['blocker']:
            g['example_blocker'] = r['blocker'][:300]
    for g in tax.values():
        g['tokens_alloc'] = int(round(g['tokens_alloc']))
        g['usd_est_alloc'] = round(g['usd_est_alloc'], 3)
        g['basis'] = ('orders measured; tokens inferred: worker final-context tokens split evenly over assigned orders '
                      '(dispatch-blocked orders get none); orders whose worker ledger row is missing are counted in tokens_unknown_orders')

    # shared-source leverage
    lev_doc, lev_class = {}, {}
    for r in frows:
        if r['outcome'] not in ('blocked', 'unresolved', 'dispatch_blocked'):
            continue
        docs = set(re.findall(r'PEB[- ]?0*(\d+)', r['blocker']))
        docs = {f'NMB PEB-{int(d):03d} report' for d in docs}
        for it in filter(None, r['event_items'].split('|')):
            mm = re.match(r'(PEB-\d+)-Report\.pdf', it)
            if mm and r['block_kind'] == 'nmb_emergency_board_report_custody_only':
                docs.add(f'NMB {mm.group(1)} report')
        for d in re.findall(r'\d+ CFR [\d.]+', r['blocker']):
            docs.add(d)
        if r['block_kind'] == 'own_original_custody_only':
            docs.add(f"own FR original of {r['instrument_id']}")
        for d in docs:
            lev_doc.setdefault(d, set()).add(r['instrument_id'])
        cls = r['block_kind']
        if cls == 'nmb_emergency_board_report_custody_only':
            cls = 'commit bytes of source-ladder NMB emergency-board report PDFs'
        elif cls == 'own_original_custody_only':
            cls = 'commit bytes of the FR originals held only as custody records'
        lev_class.setdefault(cls, set()).add(r['instrument_id'])
    # potential leverage across all prepared members (including pending): orders whose event leads are custody-only NMB PDFs
    nmb_all = sorted(r['instrument_id'] for r in all_rows if 'PEB-' in r['event_items'] and r['event_sources_held'] == 0)
    own_custody_all = sorted(r['instrument_id'] for r in all_rows if r['dispatch_blocked'])
    leverage = {
        'by_single_document_finished': sorted(([d, len(v)] for d, v in lev_doc.items()), key=lambda x: (-x[1], x[0]))[:25],
        'by_acquisition_class_finished': sorted(([c, len(v)] for c, v in lev_class.items()), key=lambda x: (-x[1], x[0])),
        'all_prepared_members_with_only_custody_NMB_event_leads': {'count': len(nmb_all), 'ids': nmb_all},
        'all_prepared_members_dispatch_blocked_on_own_original': {'count': len(own_custody_all), 'ids': own_custody_all},
        'basis': 'measured from blocker text and DISPATCH_CHECK sources; whether acquisition would make the order fileable is inferred, not shown',
    }

    # wave-level totals for finished packets
    def ssum(key, sub):
        vals = [(p.get(sub) or {}).get(key) for p in finished]
        vals = [v for v in vals if isinstance(v, (int, float))]
        return sum(vals) if vals else None
    totals = {
        'packets_scanned': len(packets), 'packets_prepared': sum(1 for p in packets if p.get('prepared')),
        'packets_prepare_failed': sorted(p['label'] for p in packets if not p.get('prepared')),
        'packets_finished': sorted(f"{p['wave']}:{p['label']}" for p in finished),
        'orders_finished': len(frows),
        'outcomes_finished': {k: sum(1 for r in frows if r['outcome'] == k)
                              for k in ('submitted', 'blocked', 'unresolved', 'dispatch_blocked')},
        'worker_tokens_finished_known': ssum('tokens_final_context', 'worker'),
        'worker_usd_est_finished_known': ssum('usd_est', 'worker'),
        'finished_packets_without_ledger_row': sorted(p['label'] for p in finished
                                                      if (p.get('worker') or {}).get('tokens_final_context') is None),
        'orders_pending': sum(1 for r in all_rows if r['outcome'] == 'pending'),
    }

    second = second_pass(args, prices, packets, pc)

    measures = {
        'schema': 'gilbreth-measures/v2',
        'second_pass': second,
        'generated_by': 'jobs/gilbreth/gilbreth.py',
        'bases': {
            'measured': 'read directly from a file, ledger or timestamp',
            'estimated': 'computed with a stated model: tokens = bytes/4; dollars = Bartolus call model at PRICES.json list rates',
            'inferred': 'allocated or deduced, e.g. worker tokens split evenly over a packet\'s assigned orders',
        },
        'caveats': [
            'Worker ledger "tokens" is the context size at hand-back (Claude Code subagent total), not cumulative billed tokens; '
            'cumulative prompt tokens are larger by roughly (tool_uses+1)/2.',
            'Per-call transcripts are not visible for cloud lanes; what each producer opened is known only from its report.',
            'Batch-check wall is taken from file mtimes and includes any pause between apply and batch-check.',
            'False-block rates count only producer outcomes; a reviewer rejection of a submitted order would turn a '
            '"false block" into a correct one.',
        ],
        'fixed_reading_list': fixed,
        'mass_revocation_targets': sorted(mass),
        'totals_finished': totals,
        'block_taxonomy': tax,
        'prescreens': prescreens(all_rows, mass),
        'shared_source_leverage': leverage,
        'past_wave_bartolus': bartolus_comparison(prices),
        'transcripts': transcripts or None,
        'packets': packets,
    }
    with open(os.path.join(OUT, 'MEASURES.json'), 'w', encoding='utf-8') as f:
        json.dump(measures, f, indent=1, sort_keys=False, default=str)
        f.write('\n')
    # compact console summary
    print(json.dumps({'totals': totals, 'taxonomy': {k: {kk: v[kk] for kk in ('orders', 'assigned_blocked', 'tokens_alloc')}
                                                      for k, v in tax.items()},
                      'fixed_tokens_est': {'asked': fixed['asked_tokens_est'], 'whole': fixed['whole_files_tokens_est']}},
                     indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
