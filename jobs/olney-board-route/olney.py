#!/usr/bin/env python3
"""Olney: a zero-token scripted route for the railway and airline emergency-board orders.

Named for Richard Olney, the Attorney General whose 1894 Pullman injunction made railway labor disputes a federal
question and led, through the Erdman Act of 1898, to the Railway Labor Act boards these orders create.

The route applies owner rule D-20261108-board-rule (research/readiness/owner_rulings/2026-11-08-haloander-decisions.md
item 2) to the orders where it applies directly, with no model tokens:

  select   choose the orders and write every other order to an exceptions list with its reasons
  run      for one batch: kit prepare, add the report's transmittal span through source_supplement.py, write
           decisions.csv and clauses.csv under the rule, kit apply, kit batch-check, record the checker result
  report   write output/RESULT.json and output/RESULT.md from the batch receipts

Nothing here reviews, reveals, files, or touches Kean or HANDOFF. Every legal value the script writes comes from the
owner rule applied to held bytes; the claims still need blind review and owner adoption as replacement proposals.
See README.md.
"""
import argparse
import base64
import csv
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
WAVE = 'research/excavator/claude-bracton-2026-11-25'
OLNEY = WAVE + '/olney'
STRATUM = 'jobs/bentham/output/strata/production.one_step_away.txt'
LIND = 'research/lind/board-candidates-2026-11-13'
CANDIDATES = LIND + '/CANDIDATES.json'
EUMENES = 'jobs/eumenes-nmb-reports/output/SOURCES.jsonl'
PTOLEMY = 'jobs/ptolemy-custody/output/SOURCES.jsonl'
LADDER = 'jobs/source-ladder/output/SOURCES.jsonl'
READINESS = 'jobs/readiness-tracker/output/READINESS_BY_ORDER.csv'
LOCKS = 'research/readiness/CLAIM_KIT_LOCK.json'
DOSSIERS = 'jobs/claim-kit/output/dossiers'
CLAIMS = 'research/readiness/claims'
KIT = 'jobs/claim-kit/kit.py'
SUPPLEMENT = 'jobs/claim-kit/source_supplement.py'
RULE = 'D-20261108-board-rule'
RULE_FILE = 'research/readiness/owner_rulings/2026-11-08-haloander-decisions.md'
AGENT = 'claude'
ACTION = 'production.one_step_away'
CLEANUP = {'EO:12553': '1986-02-25', 'EO:12379': '1982-08-17'}

MONTHS = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER',
          'NOVEMBER', 'DECEMBER']
DATE_RE = re.compile(r'\b(' + '|'.join(MONTHS) + r')\.?\s+(\d{1,2}),\s*(\d{4})\b', re.I)

# Lind flags that are only labels of how a date was read; every other flag is an exception the rule does not decide.
INFORMATIONAL_FLAGS = {
    'transmittal_date_observed_no_heading', 'transmittal_date_observed_body_only', 'transmittal_date_damaged',
    'transmittal_date_no_transmittal_marker', 'transmittal_date_absent', 'nmb_closed_date_differs',
    'cover_date_differs', 'no_submission_wording_after_transmittal', 'no_thirty_day_sentence_in_claim_text'}
FLAG_REASON = {
    'nmb_congressional_action': 'congressional_action',
    'nmb_supplement_published': 'reconvened_or_supplemental_report',
    'nmb_second_board_or_reconvened': 'reconvened_or_supplemental_report',
    'nmb_extra_documents': 'nmb_lists_extra_documents',
    'more_than_two_clauses': 'multi_clause_claim',
    'no_current_claim': 'no_current_claim',
    'already_ready': 'already_ready',
    'follow_on_order_not_board_creation': 'follow_on_order',
}
# Words that signal a command other than create-investigate-report and the standstill (rule part (c)).
OTHER_COMMAND = re.compile(
    r'compensat|expens|per\s+diem|Defense\s+Production|section\s+502|Secretary\s+of|shall\s+be\s+paid|'
    r'is\s+hereby\s+amended|hereby\s+extended|extend(ed|ing)\s+the\s+time|Executive\s+Order\s+No\.?\s*\d|'
    r'reconven|revoked|superseded', re.I)
SUBMISSION = re.compile(r'(sub\W{0,3}mit|trans\W{0,3}mit)\w*\s+(\w+\s+){0,3}?here\W{0,3}with|honor\s+to\s+sub\W{0,3}mit',
                        re.I)


def canon(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode())


def jsonl(path):
    out = []
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    return out


def git_show(repo, rel):
    """A file from origin/main (the sparse checkout may lack it); None if absent there too."""
    path = Path(repo) / rel
    if path.is_file():
        return path.read_bytes()
    run = subprocess.run(['git', '-c', 'gc.auto=0', 'show', 'origin/main:' + rel], cwd=repo, capture_output=True)
    return run.stdout if run.returncode == 0 else None


def lane_ids(repo):
    """{instrument_id: lane} from the wave's ids/c*.txt (cloud lanes) and ids/p*.txt (PC lanes) as they stand in this
    checkout (the PC lanes were repacked to non-board orders); origin/main only when the folder is absent here."""
    lanes = {}
    folder = Path(repo) / WAVE / 'ids'
    if folder.is_dir():
        for f in sorted(folder.glob('[cp][0-9][0-9].txt')):
            for iid in f.read_text().split():
                lanes[iid] = f.stem
        return lanes
    for prefix, count in (('c', 12), ('p', 11)):
        for n in range(1, count + 1):
            raw = git_show(repo, f'{WAVE}/ids/{prefix}{n:02d}.txt')
            for iid in (raw or b'').decode().split():
                lanes[iid] = f'{prefix}{n:02d}'
    return lanes


# ---------------------------------------------------------------------------------------------- dates and text

def parse_date(raw):
    """ISO date of a cleanly printed 'Month D, YYYY' (the whole string), else None."""
    m = re.fullmatch(r'\s*' + DATE_RE.pattern + r'\.?\s*', raw or '', re.I)
    if not m:
        return None
    try:
        return dt.date(int(m.group(3)), MONTHS.index(m.group(1).upper()) + 1, int(m.group(2))).isoformat()
    except ValueError:
        return None


def plus_days(iso, n):
    return (dt.date.fromisoformat(iso) + dt.timedelta(days=n)).isoformat()


def line_start(text, i):
    return text.rfind('\n', 0, i) + 1


def soft(text):
    """Text with soft hyphens and line-end hyphenation removed, plus a map back to raw offsets."""
    out, back, i = [], [], 0
    while i < len(text):
        ch = text[i]
        if ch == '­':
            i += 1
            continue
        if ch == '-' and re.match(r'-[ \t]*\n[ \t]*', text[i:]) and i and text[i - 1].isalpha():
            m = re.match(r'-[ \t]*\n[ \t]*', text[i:])
            i += m.end()
            continue
        out.append(ch)
        back.append(i)
        i += 1
    back.append(len(text))
    return ''.join(out), back


def order_number(iid):
    return iid.split(':', 1)[1]


def numbers_named(text):
    found = set()
    for m in re.finditer(r'Executive\s+Order\s*(?:No\W{0,3})?\s*([\d][\d,\s]{2,7}\d)', text, re.I):
        found.add(re.sub(r'\D', '', m.group(1)))
    return found


def report_span(text, cand, iid, signing_date):
    """Locate the held span over the report's cover date and transmittal letter, through the submission sentence.

    Returns (span, problems). Offsets are code-point offsets into the held text. The letter's own date line must
    read cleanly as the corroborated date; a garbled letter date is an exception even when the cover is clean."""
    problems = []
    date = (cand.get('candidate') or {}).get('board_clause_end', {}).get('date')
    t = cand.get('transmittal') or {}
    cover = cand.get('cover') or {}
    if t.get('kind') not in ('OBSERVED_DATELINE', 'OBSERVED_NO_HEADING') or not isinstance(t.get('offset'), int):
        return None, ['letter_date_not_located:' + str(t.get('kind'))]
    off, raw = t['offset'], t.get('raw') or ''
    if isinstance(cover.get('offset'), int) and off <= cover['offset']:
        # Lind's OBSERVED_NO_HEADING reading is the cover's date line here. Look for the letter's own date line:
        # the last date after the cover and before the address to the President, within 1500 characters.
        c_end = cover['offset'] + len(cover.get('raw') or '')
        addr = re.search(r'(THE|MR\.?|DEAR\s+MR\.?)\s+PRESIDENT', text[c_end:c_end + 1500], re.I)
        found = None
        if addr:
            window = text[c_end:c_end + addr.start()]
            for d in re.finditer(r'[A-Za-z]{3,10}\.?\s+\d{1,2},\s*\S{4,6}', window):
                found = d
        if not found:
            return None, ['letter_date_not_found_after_cover']
        off, raw = c_end + found.start(), found.group(0)
        if parse_date(raw) != date:
            return None, ['letter_date_ocr_damaged' + ('_cover_clean' if parse_date(cover.get('raw') or '') == date else '')]
    if text[off:off + len(raw)] != raw:
        return None, ['letter_date_offset_mismatch']
    if parse_date(raw) != date:
        reason = 'letter_date_ocr_damaged'
        if parse_date(cover.get('raw') or '') == date:
            reason += '_cover_clean'
        return None, [reason]
    m = SUBMISSION.search(text, off, off + 2500)
    if not m:
        return None, ['submission_sentence_not_found']
    stop = text.find('.', m.end())
    if stop < 0 or stop - off > 2500:
        return None, ['submission_sentence_not_closed']
    end = stop + 1
    start = line_start(text, off)
    heading = None
    for h in re.finditer(r'LETTER\s+OF\s+TRANSMITTAL', text[max(0, off - 400):off], re.I):
        heading = max(0, off - 400) + h.start()
    if heading is not None:
        start = line_start(text, heading)
    if isinstance(cover.get('offset'), int) and 0 <= start - cover['offset'] <= 1500:
        c = cover['offset']
        if parse_date(cover.get('raw') or '') not in (None, date):
            problems.append('cover_date_differs_from_letter')
        lead = None
        for h in re.finditer(r'APPOINTED|CREATED|EMERGENCY\s+BOARD', text[max(0, c - 1500):c], re.I):
            lead = max(0, c - 1500) + h.start()
        start = line_start(text, lead if lead is not None else c)
    span = text[start:end]
    if len(span) > 4000:
        problems.append('span_too_long')
    me = order_number(iid)
    named = numbers_named(span.replace('\n', ' '))
    other = sorted(n for n in named if n != me)
    if other:
        problems.append('other_order_number_in_span:' + '+'.join(other))
    by_number = me in named
    by_date = False
    if not by_number and signing_date:
        for d in DATE_RE.finditer(span):
            if parse_date(d.group(0)) == signing_date and re.search(r'(appointed|created)\s+by\s+you\s*(on\s*)?$',
                                                                    span[max(0, d.start() - 40):d.start()].replace('\n', ' '), re.I):
                by_date = True
    if not (by_number or by_date):
        problems.append('order_identity_not_in_span')
    boards = {int(b) for b in re.findall(r'(?:Emergency\s+Board\s+No\.?|\(No\.)\s*(\d{1,3})\b', span, re.I)}
    if boards and cand.get('peb') not in boards:
        problems.append('board_number_mismatch:' + '+'.join(map(str, sorted(boards))))
    return {'char_start': start, 'char_end': end, 'date': date, 'letter_date_raw': raw, 'letter_date_offset': off,
            'identity': 'order_number' if by_number else 'appointment_date' if by_date else None,
            'board_numbers_in_span': sorted(boards), 'submission_offset': m.start()}, problems


STANDSTILL = re.compile(r'thirty\s+days\s+after\s+(the\s+)?(said\s+)?board\s+(has\s+)?(shall\s+have\s+)?made\s+its\s+report',
                        re.I)


def split_clause(clause_text, clause_start):
    """(board_range, standstill_range_or_None, problems): absolute offsets in the held order text.

    The standstill is the sentence containing 'thirty days after the board has made its report'; it must also say
    'no change' and 'except by agreement' and end the clause. Anything else is doubt about the inventory."""
    norm, back = soft(clause_text)
    problems = []
    creates = len(re.findall(r'hereby\s+create', norm, re.I))
    if creates != 1:
        problems.append(f'board_creation_sentences:{creates}')
    hits = list(STANDSTILL.finditer(norm))
    loose = len(re.findall(r'thirty\s+days\s+after', norm, re.I))
    if len(hits) > 1 or loose > len(hits):
        return None, None, problems + ['standstill_sentence_ambiguous']
    if not hits:
        if re.search(r'no\s+change', norm, re.I):
            problems.append('no_change_wording_without_standstill_pattern')
        other = OTHER_COMMAND.search(norm)
        if other:
            problems.append('other_command_wording:' + other.group(0)[:40])
        end = len(clause_text.rstrip())
        return (clause_start, clause_start + end), None, problems
    h = hits[0]
    prior = [m.end() for m in re.finditer(r'[.:;]\s*\n', norm[:h.start()])]
    s0 = prior[-1] if prior else None
    if s0 is None:
        return None, None, problems + ['standstill_sentence_start_not_found']
    tail = re.search(r'arose\W{0,3}\.?', norm[h.end():h.end() + 600]) or re.search(r'\.\s*(\n|$)', norm[h.end():])
    if not tail:
        return None, None, problems + ['standstill_sentence_end_not_found']
    s1 = h.end() + tail.end()
    sentence = norm[s0:s1]
    if not re.search(r'no\s+change', sentence, re.I) or not re.search(r'except\s+by\s+agreement', sentence, re.I):
        problems.append('standstill_sentence_lacks_no_change_or_agreement')
    rest = norm[s1:].strip()
    # Text after the standstill is accepted only as page furniture (signature, place and date, FR document line,
    # the next document's heading): no operative verb. It is left out of both clauses.
    if rest and re.search(r'\b(shall|hereby|herein|authoriz\w*|direct\w*|provided)\b', rest, re.I):
        problems.append('text_after_standstill:' + rest[:40])
    board_text = norm[:s0]
    other = OTHER_COMMAND.search(board_text)
    if other:
        problems.append('other_command_wording:' + other.group(0)[:40])
    raw_s0 = back[s0]
    while raw_s0 < len(clause_text) and clause_text[raw_s0].isspace():
        raw_s0 += 1
    raw_s1 = back[s1] if s1 < len(back) else len(clause_text)
    while raw_s1 > raw_s0 and clause_text[raw_s1 - 1].isspace():
        raw_s1 -= 1
    board_end = len(clause_text[:back[s0]].rstrip())
    return ((clause_start, clause_start + board_end), (clause_start + raw_s0, clause_start + raw_s1), problems)


# ------------------------------------------------------------------------------------------------- selection

def filed_claims(repo, ids):
    """{iid: [(file, claim)]} for every filed claim line naming one of ids."""
    found = {}
    keys = {'"instrument_id":"%s"' % i for i in ids} | {'"instrument_id": "%s"' % i for i in ids}
    for path in sorted((Path(repo) / CLAIMS).glob('*.jsonl')):
        with path.open(encoding='utf-8') as fh:
            for line in fh:
                if '"instrument_id"' not in line or not any(k in line for k in keys):
                    continue
                try:
                    c = json.loads(line)
                except ValueError:
                    continue
                if c.get('instrument_id') in ids:
                    found.setdefault(c['instrument_id'], []).append((path.relative_to(repo).as_posix(), c))
    return found


def file_date(rel):
    m = re.search(r'(\d{4}-\d{2}-\d{2})', rel)
    return m.group(1) if m else ''


def decode_eid(ref):
    if not isinstance(ref, dict) or not isinstance(ref.get('evidence_id'), str):
        return None
    raw = ref['evidence_id']
    try:
        return base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)).decode('utf-8')
    except (ValueError, UnicodeError):
        return None


def current_claim(cand, claims):
    """The filed claim Lind read (its claim_file), provided no later-dated claim file names the order."""
    rows = claims.get(cand['instrument_id'], [])
    lind = cand.get('claim_file')
    mine = [c for f, c in rows if f == lind]
    if not lind or not mine:
        return None, 'no_current_claim'
    later = sorted({f for f, _ in rows if file_date(f) > file_date(lind)})
    if later:
        return None, 'filed_claim_changed_since_lind:' + later[-1].rsplit('/', 1)[-1]
    return mine[-1], None


def cleanup_of(claim):
    """(instrument, date, evidence_id, mechanism) of the filed claim's cleanup revocation, or None."""
    fd = claim.get('formal_disposition') if isinstance(claim.get('formal_disposition'), dict) else {}
    found = set()
    for c in claim.get('operative_clauses') or []:
        fe = c.get('first_end') if isinstance(c, dict) else None
        if isinstance(fe, dict) and fe.get('actor') in CLEANUP and fe.get('date') == CLEANUP[fe['actor']]:
            found.add((fe['actor'], fe['date'], decode_eid(fe.get('source')),
                       fe.get('mechanism_note') or fe.get('mechanism')))
    if fd.get('instrument') in CLEANUP:
        found = {f for f in found if f[0] == fd['instrument']}
    return found.pop() if len(found) == 1 else None


def load_inputs(repo):
    repo = Path(repo)
    stratum = set((repo / STRATUM).read_text().split())
    cands = {c['instrument_id']: c for c in json.loads(git_show(repo, CANDIDATES))}
    eumenes = {r['sha256']: r for r in jsonl(repo / EUMENES)}
    ptolemy = {r['sha256']: r for r in jsonl(repo / PTOLEMY)}
    ladder = {}
    for r in jsonl(repo / LADDER):
        if r.get('text_path') and r.get('sha256'):
            ladder.setdefault((r['sha256'], 'jobs/source-ladder/output/' + r['text_path']), r)
    with open(repo / READINESS, encoding='utf-8') as fh:
        readiness = {r['instrument_id']: r for r in csv.DictReader(fh) if r['instrument_id'] in cands}
    locks = json.loads((repo / LOCKS).read_bytes()).get('orders', {}) if (repo / LOCKS).exists() else {}
    return stratum, cands, eumenes, ptolemy, ladder, readiness, locks


def judge(repo, iid, cand, ctx):
    """(record, reasons): the mechanical plan for one order, and every reason the rule does not apply directly."""
    eumenes, ptolemy, ladder, readiness, locks, claims, lanes, include_pc = ctx
    reasons, rec = [], {'instrument_id': iid, 'peb': cand.get('peb'), 'lane': lanes.get(iid)}
    if lanes.get(iid, '').startswith('p') and not include_pc:
        reasons.append('pc_lane_order:' + lanes[iid])
    tr = readiness.get(iid, {})
    if tr.get('blockers') != 'FIRST_END_UNRESOLVED' or tr.get('claim_present') != 'yes':
        reasons.append('tracker_not_single_first_end_blocker:' + (tr.get('blockers') or 'none'))
    if not cand.get('creates_board'):
        reasons.append('follow_on_order')
    if cand.get('report_date_status') != 'INVENTORY_AGREES':
        reasons.append('report_date_not_corroborated:' + str(cand.get('report_date_status')))
    for flag in cand.get('flags') or []:
        if flag.startswith('report_shared_with:'):
            reasons.append('report_shared_with_follow_on_order')
        elif flag not in INFORMATIONAL_FLAGS:
            reasons.append(FLAG_REASON.get(flag, 'flag:' + flag))
    lock = locks.get(iid)
    if lock and lock.get('agent') != AGENT:
        reasons.append('reserved_by_other_agent:' + str(lock.get('agent')))
    claim, why = current_claim(cand, claims)
    if why:
        reasons.append(why)
    sha = cand.get('report_sha256')
    if sha not in eumenes:
        reasons.append('report_not_in_eumenes_store')
    kept = ptolemy.get(sha)
    local = f"jobs/ptolemy-custody/output/{kept['cache_path']}" if kept and kept.get('cache_path') else None
    if not local or not (Path(repo) / local).is_file():
        reasons.append('report_bytes_pergamon_only_kit_gap')
        local = None
    lrec = ladder.get((sha, cand.get('report_text_path')))
    text = text_sha = None
    if not lrec:
        reasons.append('report_text_record_mismatch')
    else:
        tpath = Path(repo) / cand['report_text_path']
        if not tpath.is_file():
            reasons.append('report_text_missing')
        else:
            raw = tpath.read_bytes()
            text_sha = hashlib.sha256(raw).hexdigest()
            if lrec.get('text_sha256') not in (None, text_sha):
                reasons.append('report_text_changed')
            text = raw.decode('utf-8')
    dpath = Path(repo) / DOSSIERS / (iid.replace(':', '_') + '.json')
    dossier = json.loads(dpath.read_bytes()) if dpath.is_file() else None
    if dossier is None:
        reasons.append('no_kit_dossier')
    signing = None
    if dossier:
        orig = dossier['evidence'].get(dossier.get('original_source_id') or '', {})
        signing = orig.get('signing_date')
        if dossier.get('whole_order_status') != 'no':
            reasons.append('dossier_status_not_no')
        if dossier.get('conflicts'):
            reasons.append('dossier_conflicts')
        if orig.get('acceptable_as_original') is not True or orig.get('requires_page_check'):
            reasons.append('original_not_plain_held_original')
        if len(dossier.get('clauses') or []) != 1:
            reasons.append('dossier_inventory_not_single_clause:%d' % len(dossier.get('clauses') or []))
        if claim and (claim.get('original_representation') or {}).get('sha256') != (orig.get('source') or {}).get('sha256'):
            reasons.append('filed_claim_original_differs_from_dossier')
    if claim:
        if len(claim.get('operative_clauses') or []) > 2:
            reasons.append('multi_clause_claim')
        if cleanup_of(claim) is None:
            reasons.append('filed_claim_cleanup_revocation_not_found')
    if text is not None and not any(r.startswith(('letter_date', 'report_date')) for r in reasons):
        span, problems = report_span(text, cand, iid, signing)
        reasons += problems
        rec['span'] = span
    if dossier and len(dossier.get('clauses') or []) == 1:
        c = dossier['clauses'][0]
        orig = dossier['evidence'][dossier['original_source_id']]
        if not (orig['char_start'] <= c['char_start'] < c['char_end'] <= orig['char_end']):
            reasons.append('clause_outside_original_span')
        else:
            board, standstill, problems = split_clause(c['text'], c['char_start'])
            reasons += problems
            rec['board_range'], rec['standstill_range'] = board, standstill
    rec.update(report_sha256=sha, report_local_path=local, report_text_path=cand.get('report_text_path'),
               report_text_sha256=text_sha, report_url=(lrec or {}).get('url'),
               report_page_or_item=(lrec or {}).get('page_or_item'), claim_file=cand.get('claim_file'),
               dossier_fingerprint=(dossier or {}).get('fingerprint'))
    return rec, sorted(set(reasons))


def select(repo, include_pc=False):
    started = time.monotonic()
    repo = Path(repo)
    stratum, cands, eumenes, ptolemy, ladder, readiness, locks = load_inputs(repo)
    lanes = lane_ids(repo)
    universe = sorted((set(cands) & stratum), key=lambda i: int(re.sub(r'\D', '', i) or 0))
    claims = filed_claims(repo, set(universe))
    ctx = (eumenes, ptolemy, ladder, readiness, locks, claims, lanes, include_pc)
    selected, exceptions = [], []
    for iid in universe:
        rec, reasons = judge(repo, iid, cands[iid], ctx)
        (exceptions if reasons else selected).append(dict(rec, reasons=reasons) if reasons else rec)
    by_reason = {}
    for e in exceptions:
        for r in e['reasons']:
            key = r.split(':', 1)[0]
            by_reason[key] = by_reason.get(key, 0) + 1
    primary = {}
    for e in exceptions:
        key = e['reasons'][0].split(':', 1)[0]
        primary[key] = primary.get(key, 0) + 1
    return {'schema': 'eo-olney-selection/v1', 'rule': RULE, 'universe': len(universe),
            'universe_definition': 'Lind CANDIDATES.json orders in the production.one_step_away stratum',
            'universe_lanes': dict({k: sum(1 for i in universe if lanes.get(i, '').startswith(k)) for k in ('c', 'p')},
                                   none=sum(1 for i in universe if i not in lanes)),
            'include_pc_lanes': include_pc, 'selected': selected, 'exceptions': exceptions,
            'exceptions_by_reason_any': dict(sorted(by_reason.items())),
            'wall_seconds': round(time.monotonic() - started, 2), 'model_tokens': 0}


# ------------------------------------------------------------------------------------------------- writing

def alias(iid, part):
    return f'olney_{part}_' + re.sub(r'\W', '_', order_number(iid))


def declaration(sel):
    """source_supplement declaration: the report span twice (board end, standstill end), held bytes from Ptolemy."""
    entries = []
    for r in sel:
        sp = r['span']
        source = {'url': r['report_url'], 'sha256': r['report_sha256'], 'text_path': r['report_text_path'],
                  'text_sha256': r['report_text_sha256'], 'page_or_item': r['report_page_or_item'],
                  'local_path': r['report_local_path']}
        board = f"Emergency Board No. {r['peb']} ({r['instrument_id']})"
        entries.append({'alias': alias(r['instrument_id'], 'board'), 'instrument_ids': [r['instrument_id']],
                        'actor_id': board, 'source': source, 'char_start': sp['char_start'], 'char_end': sp['char_end'],
                        'reason': f"Report cover and letter of transmittal of {board}, dated {sp['date']}, through "
                                  f"the sentence submitting the report; evidences submission on that date ({RULE} (a))."})
        if r.get('standstill_range'):
            entries.append({'alias': alias(r['instrument_id'], 'standstill'), 'instrument_ids': [r['instrument_id']],
                            'actor_id': r['instrument_id'], 'source': source, 'char_start': sp['char_start'],
                            'char_end': sp['char_end'],
                            'reason': f"Same report span: dates the report ({sp['date']}) from which the order's own "
                                      f"no-change sentence runs thirty days ({RULE} (b))."})
    return {'schema': 'eo-source-excerpt-declarations/v1', 'sources': entries}


def fill_rows(r, dossier, claim, decision_row, searches):
    """(decision_row, clause_rows, problems) under the rule. decision_row is the kit's prepared blank row."""
    iid, sp = r['instrument_id'], r['span']
    D = sp['date']
    problems = []
    cleanup = cleanup_of(claim)
    actor, cdate, ceid, cmech = cleanup
    if ceid not in dossier['evidence']:
        problems.append('cleanup_evidence_not_in_dossier:' + str(ceid))
    sav = claim.get('savings_residuals') or {}
    sav_id = decode_eid(sav.get('source'))
    if sav_id and sav_id not in dossier['evidence']:
        problems.append('savings_evidence_not_in_dossier:' + sav_id)
    wanted = {e.get('repository') for e in claim.get('later_source_search') or []}
    chosen = [s['search_id'] for s in searches if s.get('complete') and not s.get('coverage_warning')
              and (s.get('entry') or {}).get('repository') in wanted]
    got = {(s.get('entry') or {}).get('repository') for s in searches if s['search_id'] in chosen}
    if wanted - got:
        problems.append('filed_later_source_search_not_in_dossier')
    orig_id = dossier['original_source_id']
    rule_ref = f'owner rule {RULE} ({RULE_FILE} item 2)'
    disclosure = ('The transmittal letter evidences submission on its date; receipt by the President may have been '
                  'later.')
    later = [{'id': ceid, 'effective_date': cdate, 'effective_date_confirmed': True,
              'mechanism': f'{cmech} (formal disposition: {actor} cleanup revocation, kept under {RULE})'}]
    board_reason = (f"Ended by completion of its task under {rule_ref} (a): the board was created to investigate the "
                    f"dispute and report to the President. The held report of Emergency Board No. {r['peb']} "
                    f"(SHA-256 {r['report_sha256'][:12]}..., NMB inventory closing date agrees) has a letter of "
                    f"transmittal dated {D} that submits the report herewith, so the task was performed on {D}. "
                    f"{disclosure} The report deadline in the order is not the end. {actor} ({cdate}) stays the "
                    f"formal disposition, recorded as a later event.")
    clause_base = {'instrument_id': iid, 'clause_id': '', 'state': 'terminated', 'effective_date_confirmed': 'true',
                   'current_basis_id': '', 'current_legal_basis': '', 'checked_through': '',
                   'later_event_ids': canon([ceid]), 'later_events': canon(later),
                   'inventory_source_id': orig_id}
    inv = ("Inventory corrected under {rule}: the order's own no-change sentence ('from this date and for thirty days "
           "after the board has made its report ... no change, except by agreement') is a separate operative clause "
           "from the board clause (create, investigate, report). Offsets {a} to {b} of the held original text.")
    rows = []
    b0, b1 = r['board_range']
    rows.append(dict(clause_base, scope_id=iid + '#board', end_id='SUPPLEMENT:' + alias(iid, 'board'),
                     effective_date=D, mechanism='completion_of_task', reason=board_reason,
                     inventory_char_start=str(b0), inventory_char_end=str(b1),
                     inventory_reason=(inv if r.get('standstill_range') else
                                       "Board clause under {rule}: the whole operative text (create, investigate, "
                                       "report); the order has no no-change sentence. Offsets {a} to {b} of the held "
                                       "original text.").format(rule=RULE, a=b0, b=b1)))
    whole_end = D
    if r.get('standstill_range'):
        s0, s1 = r['standstill_range']
        end = plus_days(D, 30)
        whole_end = end
        rows.append(dict(clause_base, scope_id=iid + '#standstill', end_id='SUPPLEMENT:' + alias(iid, 'standstill'),
                         effective_date=end, mechanism='expiry_by_own_terms',
                         reason=(f"Ended by its own terms under {rule_ref} (b): the sentence runs 'for thirty days "
                                 f"after the board has made its report'. Report date {D} (held letter of transmittal, "
                                 f"above). Inclusive reading: the period ends at the end of the thirtieth day after "
                                 f"{D}, that is {D} + 30 days = {end}. Exclusive reading, stated as the alternative: "
                                 f"{plus_days(D, 29)}. {disclosure} {actor} ({cdate}) stays the formal disposition, "
                                 f"recorded as a later event."),
                         inventory_char_start=str(s0), inventory_char_end=str(s1),
                         inventory_reason=inv.format(rule=RULE, a=s0, b=s1)))
    row = dict(decision_row)
    row.update(outcome='submit', approved='true', original_confirmed='true', inventory_confirmed='true',
               original_pages_confirmed='true' if (claim.get('claim_kit') or {}).get('original_pages_confirmed') else 'false',
               research_rationale=(
                   f"Scripted replacement proposal (Olney, zero model tokens) applying {rule_ref} to {iid}. Original: "
                   f"the dossier's held original {orig_id}, the same printing the filed claim ({r['claim_file']}) "
                   f"cites. Report: NMB report of Emergency Board No. {r['peb']}, held bytes "
                   f"{r['report_local_path']} (also in the Pergamon store), text {r['report_text_path']}; the quoted "
                   f"span runs from the cover to the sentence submitting the report, and names the order by "
                   f"{sp['identity'].replace('_', ' ')}. Clause ends: board {D}"
                   + (f"; no-change period {whole_end} (inclusive; exclusive {plus_days(D, 29)})" if r.get('standstill_range') else '')
                   + f". Whole-order end {whole_end}. Formal disposition {actor} of {cdate}. Savings and later-source "
                   f"search are carried from the filed claim."),
               savings_state=sav.get('state') or '', savings_source_id=sav_id or '',
               savings_reason=sav.get('reason') or '', search_ids=canon(chosen), conflict_resolutions='{}',
               unresolved_material_gaps='[]', publication_kind='whole_case',
               earlier_end_check=(f"No earlier end: the board's task could not be complete before its report of {D}, "
                                  f"and the no-change period runs from the report. No extension, amendment or "
                                  f"reconvening is flagged for this order (Lind exception checks; NMB inventory)."),
               scope_check=f"The clauses cover the order's operative text: board clause and (if present) the "
                           f"no-change sentence; the recitals and heading stay with the board clause.",
               independent_command_check=("No command other than create-investigate-report and the no-change "
                                          "sentence is present (scripted wording screen; any other wording sends the "
                                          "order to exceptions)."),
               savings_check=f"Carried from the filed claim: {sav.get('state')}.")
    return row, rows, problems


# ------------------------------------------------------------------------------------------------- running

def kit(repo, *args, timeout=1800):
    started = time.monotonic()
    run = subprocess.run([sys.executable, '-B', str(Path(repo) / KIT), '--repo', str(repo), *map(str, args)],
                         cwd=str(Path(repo) / 'jobs/claim-kit'), capture_output=True, text=True, timeout=timeout)
    return run, round(time.monotonic() - started, 2)


def supplement(repo, *args, timeout=1800):
    started = time.monotonic()
    run = subprocess.run([sys.executable, '-B', str(Path(repo) / SUPPLEMENT), '--repo', str(repo), *map(str, args)],
                         cwd=str(Path(repo) / 'jobs/claim-kit'), capture_output=True, text=True, timeout=timeout)
    return run, round(time.monotonic() - started, 2)


def tail(run):
    return ((run.stdout or '')[-3000:], (run.stderr or '')[-3000:])


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as fh:
        rd = csv.DictReader(fh)
        return rd.fieldnames, list(rd)


def write_csv(path, fields, rows):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def run_batch(repo, name, ids, selection):
    repo = Path(repo).resolve()
    by = {r['instrument_id']: r for r in selection['selected']}
    sel = [by[i] for i in ids]
    folder = repo / OLNEY / name
    if folder.exists():
        raise SystemExit('batch folder exists: ' + str(folder))
    folder.mkdir(parents=True)
    receipt = {'schema': 'eo-olney-batch/v1', 'batch': name, 'orders': ids, 'steps': {}, 'per_order': {},
               'model_tokens': 0, 'started_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    path = folder / 'OLNEY_BATCH.json'

    def step(label, run, secs, extra=None):
        receipt['steps'][label] = {'returncode': run.returncode, 'wall_seconds': secs, **(extra or {})}
        if run.returncode:
            receipt['steps'][label]['output_tail'] = tail(run)
        dump(path, receipt)

    base = folder / 'packet'
    run, secs = kit(repo, 'prepare', *ids, '--agent', AGENT, '--action', ACTION, '--replacement-proposal',
                    '--write', base)
    step('prepare', run, secs)
    if not (base / 'PACKET.json').exists():
        return receipt
    prep = json.loads((base / 'PREPARE.json').read_bytes())
    blocked = set(prep.get('dispatch_check', {}).get('source_blocked_ids') or [])
    decl = folder / 'SUPPLEMENT_SOURCES.json'
    dump(decl, declaration(sel))
    packet = folder / 'supplemented'
    run, secs = supplement(repo, 'prepare', '--parent', base, '--sources', decl, '--agent', AGENT, '--write', packet)
    step('supplement', run, secs)
    if not (packet / 'PACKET.json').exists():
        return receipt
    sys.path.insert(0, str(repo / 'jobs/claim-kit'))
    import batch as B
    _, dossiers = B.load_packet(packet, repo, check_sources=False)
    claims = filed_claims(repo, set(ids))
    dfields, drows = read_csv(packet / 'decisions.csv')
    cfields, _ = read_csv(packet / 'clauses.csv')
    out_d, out_c = [], []
    started = time.monotonic()
    for row in drows:
        iid = row['instrument_id']
        r = by[iid]
        claim = next(c for f, c in reversed(claims[iid]) if f == r['claim_file'])
        problems = []
        if iid in blocked:
            problems.append('dispatch_source_blocked')
        if dossiers[iid].get('source_supplement', {}).get('parent_dossier_sha256') != r['dossier_fingerprint']:
            problems.append('dossier_changed_since_selection')
        if not problems:
            drow, crows, problems = fill_rows(r, dossiers[iid], claim, row, dossiers[iid].get('machine_searches') or [])
        if problems:
            row = dict(row, outcome='blocked', unresolved_material_gaps=canon(['olney: ' + p for p in problems]))
            out_d.append(row)
            out_c += [dict({k: '' for k in cfields}, instrument_id=iid, scope_id=c['scope_id'], clause_id=c['id'],
                           effective_date_confirmed='false', later_event_ids='[]', later_events='[]')
                      for c in dossiers[iid]['clauses']]
            receipt['per_order'][iid] = {'outcome': 'blocked', 'problems': problems}
        else:
            out_d.append(drow)
            out_c += crows
            receipt['per_order'][iid] = {'outcome': 'submit', 'board_end': r['span']['date'],
                                         'standstill_end': crows[1]['effective_date'] if len(crows) > 1 else None}
    write_csv(packet / 'decisions.csv', dfields, out_d)
    write_csv(packet / 'clauses.csv', cfields, out_c)
    receipt['steps']['write_sheets'] = {'returncode': 0, 'wall_seconds': round(time.monotonic() - started, 2)}
    applied = packet / 'applied-v1'
    run, secs = kit(repo, 'apply', packet, '--write', applied)
    step('apply', run, secs)
    if not (applied / 'AUDIT.json').exists():
        return receipt
    for a in json.loads((applied / 'AUDIT.json').read_bytes()):
        receipt['per_order'].setdefault(a['instrument_id'], {}).update(apply_outcome=a['outcome'],
                                                                      apply_errors=a.get('errors', [])[:5])
    sel_check = applied / 'SELECTED_SOURCE_CHECK.json'
    if sel_check.exists():
        for m in json.loads(sel_check.read_bytes()).get('members', []):
            receipt['per_order'].setdefault(m['instrument_id'], {}).update(
                selected_source_state=m['state'], selected_source_blockers=[b.get('kind') for b in m['blockers']][:5])
    run, secs = kit(repo, 'batch-check', packet, applied)
    step('batch_check', run, secs)
    per = applied / 'actual-checker' / 'PER_CLAIM.json'
    if per.exists():
        for c in json.loads(per.read_bytes()).get('claims', []):
            receipt['per_order'].setdefault(c.get('instrument_id'), {}).update(
                checker_all_checks_passed=bool(c.get('all_checks_passed')),
                checker_failures=[f if isinstance(f, str) else f.get('status') or f.get('check') for f in c.get('failures', [])][:5],
                checker_unverified=[u if isinstance(u, str) else u.get('status') or u.get('check') for u in c.get('unverified', [])][:5],
                checker_gate_errors=c.get('gate_errors', [])[:5])
    receipt['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    dump(path, receipt)
    return receipt


def passing(receipt):
    return [i for i, v in receipt.get('per_order', {}).items() if v.get('checker_all_checks_passed')]


PRIORITY = ['no_current_claim', 'filed_claim_changed_since_lind', 'tracker_not_single_first_end_blocker',
            'reserved_by_other_agent', 'pc_lane_order', 'follow_on_order', 'report_shared_with_follow_on_order',
            'congressional_action', 'reconvened_or_supplemental_report', 'nmb_lists_extra_documents',
            'multi_clause_claim', 'dossier_inventory_not_single_clause', 'report_date_not_corroborated']


def primary(reasons):
    """One reason per order for a breakdown that sums: the order's case-level exception before any extraction or
    wording doubt, and the Pergamon-only kit gap last (so its count is the orders blocked by that gap alone)."""
    keys = [r.split(':', 1)[0] for r in reasons]
    for k in PRIORITY:
        if k in keys:
            return k
    rest = [k for k in keys if k != 'report_bytes_pergamon_only_kit_gap']
    group = {'letter_date': 'letter_date_unreadable_or_unlocated', 'submission': 'letter_date_unreadable_or_unlocated',
             'cover_date': 'letter_date_unreadable_or_unlocated', 'order_identity': 'report_identity_doubt',
             'other_order': 'report_identity_doubt', 'board_number': 'report_identity_doubt'}
    for k in rest:
        for prefix, name in group.items():
            if k.startswith(prefix):
                return name
    return 'clause_inventory_doubt' if rest else 'report_bytes_pergamon_only_kit_gap'


def report(repo):
    repo = Path(repo)
    selection = json.loads((HERE / 'output/SELECTION.json').read_bytes())
    batches = []
    for p in sorted((repo / OLNEY).glob('*/OLNEY_BATCH.json')):
        batches.append(json.loads(p.read_bytes()))
    per = {}
    for b in batches:
        for i, v in b['per_order'].items():
            per[i] = dict(v, batch=b['batch'])
    failing = {i: {k: v.get(k) for k in ('batch', 'outcome', 'problems', 'apply_outcome', 'apply_errors',
                                         'selected_source_blockers', 'checker_failures', 'checker_unverified',
                                         'checker_gate_errors') if v.get(k)}
               for i, v in per.items() if not v.get('checker_all_checks_passed')}
    result = {'schema': 'eo-olney-result/v1', 'rule': RULE, 'model_tokens': 0,
              'universe': selection['universe'], 'universe_lanes': selection['universe_lanes'],
              'selected': len(selection['selected']), 'selected_ids': [r['instrument_id'] for r in selection['selected']],
              'exceptions': len(selection['exceptions']),
              'exceptions_by_reason_any': selection['exceptions_by_reason_any'],
              'exceptions_by_primary_reason': dict(sorted(
                  {k: sum(1 for e in selection['exceptions'] if primary(e['reasons']) == k)
                   for k in {primary(e['reasons']) for e in selection['exceptions']}}.items(), key=lambda x: -x[1])),
              'exceptions_list': {e['instrument_id']: e['reasons'] for e in selection['exceptions']},
              'prepared': sum(len(b['orders']) for b in batches if 'prepare' in b['steps']),
              'checker_passing': sorted(i for i, v in per.items() if v.get('checker_all_checks_passed')),
              'failing': failing,
              'batches': [{'batch': b['batch'], 'orders': len(b['orders']), 'passing': len(passing(b)),
                           'wall_seconds': {k: v.get('wall_seconds') for k, v in b['steps'].items()}} for b in batches],
              'selection_wall_seconds': selection['wall_seconds']}
    dump(HERE / 'output/RESULT.json', result)
    lines = ['# Olney result', '',
             f"Rule {RULE}; zero model tokens. Universe {result['universe']} board orders in production.one_step_away "
             f"({result['universe_lanes'].get('c')} were in cloud lanes c01-c12, {result['universe_lanes'].get('p')} in PC "
             f"lanes, {result['universe_lanes'].get('none')} unassigned after the PC repack).", '',
             f"- Selected: {result['selected']}",
             f"- Exceptions: {result['exceptions']} (an order can carry several reasons)",
             f"- Prepared: {result['prepared']}",
             f"- Checker-passing: {len(result['checker_passing'])}",
             f"- Failing: {len(failing)}", '', '## Exceptions, one primary reason per order', '',
             '| Primary reason | Orders |', '|---|---:|']
    lines += [f'| {k} | {v} |' for k, v in result['exceptions_by_primary_reason'].items()]
    lines += ['', '## Exceptions, every reason (an order can carry several)', '', '| Reason | Orders |', '|---|---:|']
    lines += [f'| {k} | {v} |' for k, v in sorted(result['exceptions_by_reason_any'].items(), key=lambda x: -x[1])]
    lines += ['', '## Batches', '', '| Batch | Orders | Passing | Wall seconds by step |', '|---|---:|---:|---|']
    lines += [f"| {b['batch']} | {b['orders']} | {b['passing']} | {canon(b['wall_seconds'])} |" for b in result['batches']]
    if failing:
        lines += ['', '## Failing', '']
        lines += [f'- {i}: {canon(v)[:400]}' for i, v in sorted(failing.items())]
    (HERE / 'output/RESULT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--repo', type=Path, default=HERE.parents[1])
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('select')
    s.add_argument('--include-pc-lanes', action='store_true', help='also select orders assigned to the PC lanes')
    s = sub.add_parser('run')
    s.add_argument('--batch', required=True)
    s.add_argument('--n', type=int, default=8)
    s.add_argument('--ids', nargs='*')
    sub.add_parser('report')
    a = p.parse_args(argv)
    repo = a.repo.resolve()
    if a.command == 'select':
        result = select(repo, a.include_pc_lanes)
        dump(HERE / 'output/SELECTION.json', result)
        print(json.dumps({k: result[k] for k in ('universe', 'universe_lanes', 'exceptions_by_reason_any', 'wall_seconds')}
                         | {'selected': len(result['selected']), 'exceptions': len(result['exceptions'])}, indent=2))
        return 0
    if a.command == 'run':
        selection = json.loads((HERE / 'output/SELECTION.json').read_bytes())
        done = set()
        for p_ in (repo / OLNEY).glob('*/OLNEY_BATCH.json'):
            done |= set(json.loads(p_.read_bytes())['orders'])
        ids = a.ids or [r['instrument_id'] for r in selection['selected'] if r['instrument_id'] not in done][:a.n]
        if not ids or len(ids) > 20:
            raise SystemExit('1-20 orders per batch')
        receipt = run_batch(repo, a.batch, ids, selection)
        print(json.dumps({'batch': a.batch, 'orders': len(ids), 'passing': len(passing(receipt)),
                          'steps': {k: {'rc': v['returncode'], 's': v['wall_seconds']} for k, v in receipt['steps'].items()}},
                         indent=2))
        return 0
    if a.command == 'report':
        r = report(repo)
        print(json.dumps({k: r[k] for k in ('selected', 'exceptions', 'prepared')} | {'passing': len(r['checker_passing'])}))
        return 0


if __name__ == '__main__':
    sys.exit(main())
