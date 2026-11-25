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
COVER_RULE = 'D-20261125-board-cover-date'
COVER_RULE_SOURCE = 'jobs/kean/register/decisions.jsonl'
LIND_AGREES = 'Lind, research/lind/board-candidates-2026-11-13/CANDIDATES.json: report_date_status INVENTORY_AGREES'
RUN = 'v3'
# Upheld by both blind arms in the first run (o0/o1 review); not rerun. EO 10944 was not upheld and is rerun.
UPHELD = {'EO:10032', 'EO:10056', 'EO:10071', 'EO:10112', 'EO:10140', 'EO:10757', 'EO:10872', 'EO:11663'}
# Upheld by both blind arms in run v2 (o2 review of batch s4, o3 review of batch s3); not rerun in v3.
UPHELD_V2 = {'EO:10105', 'EO:9702'}

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
SUBMISSION = re.compile(r'(sub\W{0,3}mit|trans\W{0,3}mit)\w*\s+(\w+\s+){0,3}?here\W{0,3}with|honor\s+to\s+sub\W{0,3}mit|'
                        r'honor\s+here\W{0,3}with\s+to\s+(?:sub|trans)\W{0,3}mit', re.I)


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


def kit_supports_pergamon(repo):
    """Whether the checkout's claim kit accepts a held excerpt whose raw bytes are only in the Pergamon store."""
    if os.environ.get('OLNEY_ASSUME_PERGAMON_KIT') == '1':
        return True  # preview only (select --out): what the selection would be once the kit change is merged
    path = Path(repo) / SUPPLEMENT
    return path.is_file() and 'def held_bytes(' in path.read_text(encoding='utf-8')


def pergamon_pdf(repo, record, cache_dir):
    """A verified local copy of a Pergamon-stored report (fetched once into cache_dir), or None."""
    target = Path(cache_dir) / 'pergamon' / (record['sha256'] + '.pdf')
    if target.is_file() and sha_file(target) == record['sha256']:
        return target
    try:
        sys.path.insert(0, str(Path(repo) / 'jobs/_lib'))
        import pergamon_store
        data = pergamon_store.Store.from_env().get_verified(record)
    except Exception:  # noqa: BLE001  (offline or refused: the order stays an exception)
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    target.with_suffix('.tmp').write_bytes(data)
    os.replace(target.with_suffix('.tmp'), target)
    return target


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


ABBREVIATION = re.compile(r'(?:\b(?:No|Nos|Co|Cos|Inc|Corp|Ltd|Mr|Messrs|Jr|Sr|St|Ry|R\.\s?R|Bros|U\.\s?S|D\.\s?C|'
                          r'N\.\s?Y|Ill|Pa|Mass|Tex|Ind|Mo|Calif|Wash|Va|Md|Del|Conn|Mich|Wis|Minn|Ky|Tenn|Ala|Ga|Fla|'
                          r'La|Ark|Okla|Kans|Nebr|Colo|Ariz|Oreg|Mont|Wyo|Nev|Vt|Me|vs|et\s+al)|\b[A-Z])$')


def sentence_stop(text, i):
    """Offset of the period that ends the sentence running on from i, skipping the periods of abbreviations
    ('Executive Order No. 10147', 'Railroad Co.', 'D. C.'); -1 if none."""
    while True:
        stop = text.find('.', i)
        if stop < 0 or not ABBREVIATION.search(text[max(0, stop - 12):stop]):
            return stop
        i = stop + 1


def letter_reading(text, cand, date):
    """(offset, raw, None) of the letter of transmittal's own date line when it reads cleanly as ``date``, else
    (offset_or_None, raw_or_None, reason). The reason names why the letter date is not usable."""
    t = cand.get('transmittal') or {}
    cover = cand.get('cover') or {}
    if t.get('kind') not in ('OBSERVED_DATELINE', 'OBSERVED_NO_HEADING') or not isinstance(t.get('offset'), int):
        return None, None, 'letter_date_not_located:' + str(t.get('kind'))
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
            return None, None, 'letter_date_not_found_after_cover'
        off, raw = c_end + found.start(), found.group(0)
    if text[off:off + len(raw)] != raw:
        return off, raw, 'letter_date_offset_mismatch'
    if parse_date(raw) != date:
        return off, raw, 'letter_date_ocr_damaged'
    return off, raw, None


PAGE_LINE = re.compile(r'^=== PDF page \d+(?: of \d+)? ===$')


def address_line(line):
    """Whether a line is the letter's address to the President ('THE PRESIDENT,', OCR-damaged 'THE IORESIDENT,',
    'The PItESmENT', 'DEAR MR. PRESIDENT:')."""
    words = re.findall(r'\S+', line)
    if not words or len(line.strip()) > 60 or not re.match(r'(?:THE|The|TH\S|DEAR|Dear|MR\.?|Mr\.?)$', words[0]):
        return False
    import difflib
    return any(difflib.SequenceMatcher(None, re.sub(r'[^A-Za-z]', '', w).upper(), 'PRESIDENT').ratio() >= 0.6
               for w in words[1:3])


def letter_section(text, c_end, limit=2500):
    """The held letter of transmittal after the cover: {'heading', 'address', 'date_line'} offsets and raw lines,
    any of them None. The date line is the last line before the address to the President, after the cover and
    the heading, that is not page furniture; a line with no digit, no damaged character and no month-like word is a
    place line, not a date line."""
    stop = COVER_STOP.search(text, c_end, c_end + limit)
    end = stop.start() if stop else min(len(text), c_end + limit)
    out = {'heading': None, 'address': None, 'date_line': None, 'date_line_offset': None}
    h = re.search(r'LETTER\s+OF\s+TRANSMITTAL', text[c_end:end], re.I)
    if h:
        out['heading'] = c_end + h.start()
    pos, lines = c_end, []
    for raw in text[c_end:end].split('\n'):
        if address_line(raw):
            out['address'] = pos
            break
        lines.append((pos, raw))
        pos += len(raw) + 1
    if out['address'] is None:
        return out
    import difflib
    for off, raw in reversed(lines):
        if out['heading'] is not None and off + len(raw) <= out['heading']:
            break
        line = raw.strip()
        if (not line or PAGE_LINE.match(line) or re.match(r'LETTER\s+OF\s+TRANSMITTAL', line, re.I)
                or re.fullmatch(r'\(?(?:No\.?|Emergency\s+Board\s+No\.?|A-|Case\s+No\.?\s*A-)\s*[\w\']{1,6}\)?\.?', line, re.I)
                or len(re.sub(r'\W', '', line)) < 3):
            continue
        monthish = any(difflib.SequenceMatcher(None, w.upper(), m).ratio() >= 0.6
                       for w in re.findall(r'[A-Za-z~(\]$@%]{3,10}', line) for m in MONTHS)
        if re.search(r'\d|[~$@%(\]]', line) or monthish:
            out['date_line'], out['date_line_offset'] = line, off + raw.index(line)
        break
    return out


def legible_parts(raw, date):
    """Differences between a damaged date line's cleanly legible parts and the date: [('year', '1968', '1969'), ...]."""
    d = dt.date.fromisoformat(date)
    out = []
    for m in re.finditer(r'(?<![\w$@~])(1[789]\d\d)(?![\w$@~])', raw):
        if int(m.group(1)) != d.year:
            out.append(('year', m.group(1), str(d.year)))
    for m in re.finditer(r'\b(' + '|'.join(MONTHS) + r')\b', raw, re.I):
        if MONTHS.index(m.group(1).upper()) + 1 != d.month:
            out.append(('month', m.group(1), MONTHS[d.month - 1].title()))
        day = re.match(r'\.?\s+(\d{1,2})(?=[,.:;]?\s)', raw[m.end():] + ' ')
        if day and int(day.group(1)) != d.day:
            out.append(('day', day.group(1), str(d.day)))
    return out


# Letter-date failures that D-20261125-board-cover-date covers: the date line is unreadable or was not found. An
# offset mismatch is a data defect, not an unreadable line, and stays an exception.
LETTER_UNREADABLE = ('letter_date_not_located', 'letter_date_not_found_after_cover', 'letter_date_ocr_damaged')
COVER_STOP = re.compile(r'TABLE\s+OF\s+CONTENTS|^\s*CONTENTS\s*$|INTRODUCT|^\s*I\.\s', re.I | re.M)


def cover_clean(text, cand, date):
    """The cover date line, if it is held at its offset and reads cleanly (the whole line) as ``date``."""
    cover = cand.get('cover') or {}
    off, raw = cover.get('offset'), cover.get('raw') or ''
    if not isinstance(off, int) or not raw or text[off:off + len(raw)] != raw or parse_date(raw) != date:
        return None
    return off, raw


def report_span(text, cand, iid, signing_date):
    """Locate the held span over the report's cover date and transmittal letter, through the submission sentence.

    Returns (span, problems). Offsets are code-point offsets into the held text. The letter's own date line ends
    the board clause when it reads cleanly as the corroborated date. When it is unreadable or not found and the
    cover date reads cleanly as that date, the cover date is used instead under D-20261125-board-cover-date
    (``date_basis`` 'cover'), and the claim discloses it. A letter date line that reads cleanly as another date is a
    conflict and stays an exception."""
    problems = []
    date = (cand.get('candidate') or {}).get('board_clause_end', {}).get('date')
    cover = cand.get('cover') or {}
    off, raw, why = letter_reading(text, cand, date)
    basis, letter_note = 'letter', None
    if why:
        clean = cover_clean(text, cand, date) if date and cand.get('report_date_status') in (None, 'INVENTORY_AGREES') else None
        if not why.startswith(LETTER_UNREADABLE) or clean is None:
            if why == 'letter_date_ocr_damaged' and parse_date(cover.get('raw') or '') == date:
                why += '_cover_clean'
            return None, [why]
        if raw and parse_date(raw) not in (None, date):
            return None, ['cover_date_differs_from_letter']
        # Run v3 (o2/o3 review): the claim must say truly whether the held letter's date line is present but
        # unreadable, absent before the address, or whether no letter is held at all. Olney reads the held letter
        # itself rather than relying on Lind's label.
        sec = letter_section(text, clean[0] + len(clean[1]))
        line, line_off = sec['date_line'], sec['date_line_offset']
        if line:
            readings = {parse_date(d.group(0)) for d in DATE_RE.finditer(line)} - {None}
            if readings - {date}:
                return None, ['cover_date_differs_from_letter']
            if readings:
                return None, ['letter_date_line_reads_cleanly_but_lind_did_not']
            status = 'unreadable'
        elif sec['address'] is not None:
            status = 'not_found_before_address'
        elif sec['heading'] is not None:
            return None, ['letter_address_not_located']
        else:
            status = 'no_letter_held'
        if raw and (not line or raw.strip(' .') not in line):
            return None, ['letter_date_line_location_disagrees']
        diffs = legible_parts(line, date) if line else []
        if any(k in ('month', 'day') for k, _, _ in diffs):
            # A legible month or day that differs from the cover reads as another day: a conflict, as a clean
            # reading of another date is. A differing legible year alone (OCR digit errors) is disclosed.
            return None, ['letter_date_legible_part_conflicts']
        before = bool(signing_date and any(k == 'year' and int(a) < int(signing_date[:4]) for k, a, _ in diffs))
        basis, letter_note = 'cover', {'reason': why, 'status': status, 'letter_date_raw': line,
                                       'letter_date_offset': line_off, 'legible_differences': diffs,
                                       'legible_year_before_signing': before, 'signing_date': signing_date}
        off, raw = clean
    c_end = off + len(raw)
    if basis == 'letter':
        m = SUBMISSION.search(text, off, off + 2500)
        if not m:
            return None, ['submission_sentence_not_found']
    else:
        # The letter, if held, follows the cover: its submission sentence must come after an address to the
        # President and before the contents or introduction.
        stop = COVER_STOP.search(text, c_end, c_end + 2500)
        limit = stop.start() if stop else min(len(text), c_end + 2500)
        m = SUBMISSION.search(text, c_end, limit)
        if m and not re.search(r'PRESIDENT', text[c_end:m.start()], re.I):
            m = None
        if letter_note['status'] == 'no_letter_held' and (m or re.search(r'PRESIDENT|P\S{0,2}ESID\S{0,2}NT', text[c_end:limit])):
            # A submission sentence or an address the line screen did not recognise: the letter may be held, so
            # 'no letter was found' would not be safe to state.
            return None, ['letter_address_not_located']
        if letter_note['status'] != 'no_letter_held' and not m:
            return None, ['letter_held_submission_not_found']
    if m:
        stop = sentence_stop(text, m.end())
        if stop < 0 or stop - off > 2500:
            return None, ['submission_sentence_not_closed']
        end = stop + 1
    else:
        # No legible letter: the span is the cover through its date line and the board-number line after it.
        nl = text.find('\n', c_end)
        end = c_end if nl < 0 else nl
        after = re.match(r'\s*\(No\.\s*\d{1,3}\)', text[end:end + 40])
        if after:
            end += after.end()
    start = line_start(text, off)
    heading = None
    for h in re.finditer(r'LETTER\s+OF\s+TRANSMITTAL', text[max(0, off - 400):off], re.I):
        heading = max(0, off - 400) + h.start()
    if heading is not None:
        start = line_start(text, heading)
    if isinstance(cover.get('offset'), int) and (basis == 'cover' or 0 <= start - cover['offset'] <= 1500):
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
    if basis == 'cover':
        if letter_note['letter_date_offset'] is not None and not start <= letter_note['letter_date_offset'] < end:
            problems.append('letter_date_line_outside_span')
        if letter_note['status'] == 'not_found_before_address':
            # 'The letter has no date line' must hold of the quoted span: no printed date in it other than the
            # cover's own date line and the order's signing date.
            for d in DATE_RE.finditer(span):
                if start + d.start() != off and parse_date(d.group(0)) != signing_date:
                    problems.append('letter_date_line_status_uncertain')
                    break
    me = order_number(iid)
    named = numbers_named(span.replace('\n', ' '))
    other = sorted(n for n in named if n != me)
    if other:
        problems.append('other_order_number_in_span:' + '+'.join(other))
    by_number = me in named
    by_date = False
    boards = {int(b) for b in re.findall(r'(?:Emergency\s+Board\s+No\.?|\(No\.)\s*(\d{1,3})\b', span, re.I)}
    if not by_number and signing_date:
        for d in DATE_RE.finditer(span):
            if parse_date(d.group(0)) != signing_date:
                continue
            before = span[max(0, d.start() - 40):d.start()].replace('\n', ' ')
            if re.search(r'(appointed|created)\s+by\s+you\s*(on\s*)?$', before, re.I):
                by_date = True
            # The cover's own 'APPOINTED <date>' line names the order by its signing date only together with the
            # matching board number, since two boards can be appointed on one day.
            elif re.search(r'(appointed|created)\s*(on\s*)?$', before, re.I) and cand.get('peb') in boards:
                by_date = True
    if not (by_number or by_date):
        problems.append('order_identity_not_in_span')
    if boards and cand.get('peb') not in boards:
        problems.append('board_number_mismatch:' + '+'.join(map(str, sorted(boards))))
    out = {'char_start': start, 'char_end': end, 'date': date, 'date_basis': basis, 'date_raw': raw,
           'date_offset': off, 'identity': 'order_number' if by_number else 'appointment_date' if by_date else None,
           'board_numbers_in_span': sorted(boards), 'submission_offset': m.start() if m else None}
    if basis == 'letter':
        out.update(letter_date_raw=raw, letter_date_offset=off)
    else:
        out.update(cover_date_raw=raw, cover_date_offset=off, letter=letter_note)
    return out, problems


# ------------------------------------------------------------------------------------- report-time extensions
#
# Batch o1 review: a President-approved extension of the board's report time that the held report records is a
# later event of the board clause. Olney screens the whole report PDF (pdftotext, no model) for extension wording,
# and records an extension only when its passage is in the held text and prints the approval date and the new
# deadline in full. Anything else is an exception.

EXT_PHRASE = re.compile(
    r'exten(?:sion|sions|d|ds|ded|ding)\s+(?:of\s+)?(?:the\s+|its\s+|this\s+|our\s+)?(?:original\s+)?'
    r'(?:\w+\s+){0,2}?(?:time|date|deadline)\b'
    r'|(?:time|date)\s+(?:limit\s+)?(?:\w+\s+){0,12}?(?:was|be|been|is|were)\s+(?:thus\s+)?extended', re.I)
EXT_NOT = re.compile(r'extended\s+periods?\b|for\s+an\s+extended', re.I)
EXT_CONTEXT = re.compile(r'report|file\b|filing|time\s+limit|President|Emergency\s+Board|the\s+Board', re.I)
EXT_MULTIPLE = re.compile(r'\btwice\b|two\s+occasions|further\s+extension|another\s+extension|second\s+extension|'
                          r'ultimately|\bagain\b|extensions\b', re.I)
# A printed date with or without its year: 'December 17', 'December 17, 1948', 'September 1,1950'.
DATEX = r'(?:' + '|'.join(MONTHS) + r')\.?\s+\d{1,2}(?:st|nd|rd|th|d)?(?:,?\s*\d{4})?\b'
APPROVAL = [re.compile(p, re.I) for p in (
    r'approv\w*\s+(?:by\s+(?:the\s+)?President\s+)?(?:(?:\w+\s+){0,4}?on\s+|\s*:\s*)(' + DATEX + ')',
    r'\bon\s+(' + DATEX + r'),?\s+(?:President\s+\w+\s+|the\s+President\s+)(?:\w+\s+){0,2}?(?:approv|extend|grant)\w*',
    r'President,?\s+on\s+(' + DATEX + r'),?\s+(?:approv|extend|grant)\w*',
    r'(?:granted|extended)\s+by\s+the\s+President\s+on\s+(' + DATEX + ')',
    # 'On February 6, 1969, this extension was approved by President Nixon' (EO 11445, o3 review)
    r'\bon\s+(' + DATEX + r'),?\s+(?:\w+\s+){0,4}?(?:was|were|had\s+been)\s+(?:duly\s+)?approv\w*')]
DEADLINE = re.compile(r'(?:not\s+later\s+than(?:\s+and\s+including)?|until|to\s+and\s+including|to\s+on\s+or\s+before|'
                      r'on\s+or\s+before|to|through)\s+(' + DATEX + ')', re.I)
APPROVED_WORDING = re.compile(r'approv|grant|President\s+(?:\w+\s+){0,3}?extended|extended\s+by\s+the\s+President', re.I)
MODAL_ONLY = re.compile(r'(?:can|could|may|might|would)\s+be\s+extended', re.I)


def resolve(raw, lo, hi):
    """(iso, year_inferred) for a printed date: as printed when the year is printed, otherwise the one year that
    puts it between lo and hi (ISO dates). None when unreadable, outside the bounds or not unique."""
    raw = re.sub(r'(\d)(?:st|nd|rd|th|d)\b', r'\1', raw)
    full = parse_date(raw) or parse_date(re.sub(r'(\d)\s+(\d{4})$', r'\1, \2', raw.strip()))
    if full:
        return (full, False) if lo <= full <= hi else None
    m = re.fullmatch(r'\s*(' + '|'.join(MONTHS) + r')\.?\s+(\d{1,2})\s*', raw, re.I)
    if not m:
        return None
    found = []
    for year in range(int(lo[:4]), int(hi[:4]) + 1):
        try:
            iso = dt.date(year, MONTHS.index(m.group(1).upper()) + 1, int(m.group(2))).isoformat()
        except ValueError:
            continue
        if lo <= iso <= hi:
            found.append(iso)
    return (found[0], True) if len(found) == 1 else None


PAGE_MARK = re.compile(r'^=== PDF page (\d+)(?: of \d+)? ===$', re.M)


def unspace(text):
    """Join letters a damaged text layer prints one by one ('r e p o r t' -> 'report')."""
    return re.sub(r'\b(?:[A-Za-z] ){2,}[A-Za-z]\b', lambda m: m.group(0).replace(' ', ''), text)


def extension_hits(text):
    """Start offsets of report-time extension wording in text (whitespace-normalized by the caller if needed).

    Two screens, united so the run v2 screen is never narrowed: the v2 phrase screen, and (run v3, after the o2/o3
    review found three misses) any extension word, OCR-damaged or not ('extended to December 10, 1961 the date',
    'an extension of 30 days', 'e~tend the time', 'this extension was approved'), or wording of more or postponed
    time, whose own sentence or a neighbouring one speaks of the report, its filing or its time."""
    out = set()
    for m in EXT_PHRASE.finditer(text):
        window = text[max(0, m.start() - 300):m.end() + 300]
        if EXT_NOT.search(text[max(0, m.start() - 10):m.end() + 10]) or not EXT_CONTEXT.search(window):
            continue
        out.add(m.start())
    for m in EXT_WORD.finditer(text):
        if EXT_WORD_NOT.search(text[max(0, m.start() - 40):m.end() + 40]):
            continue
        # A verb ('extended to December 10, 1961 the date for the filing') carries its object in its own sentence;
        # a noun ('an extension', 'a postponement') may name the report in a neighbouring sentence.
        noun = re.match(r'(?:ex|e\W{1,2})tension|postpon|continuance|additional|more|further', m.group(0), re.I)
        if EXT_REPORT_TIME.search(around(text, m.start(), 1 if noun else 0)):
            out.add(m.start())
    return sorted(out)


# Run v3 broad screen. An extension word: 'extend', 'extended', 'extension', with OCR damage in the x ('e~tend',
# 'e*tension'); or more or postponed time.
EXT_WORD = re.compile(r'\b(?:ex|e[^\w\s]{1,2})ten(?:d|sion)\w*|\badditional\s+(?:time|period|\d+\s+days|thirty\s+days)'
                      r'|\b(?:more|further)\s+time\b|\bpostpon\w*|\bcontinuance\b', re.I)
# Uses that are not a grant of time: an adjective before a noun ('after extended hearings'), and statute names.
EXT_WORD_NOT = re.compile(r'extended\s+(?:hearings?|periods?|discussions?|negotiations?|conferences?|sessions?|'
                          r'study|consideration)\b|for\s+an\s+extended\b|Extension\s+Act', re.I)
# The report-time context the extension word's sentence (or a neighbouring one) must carry.
EXT_REPORT_TIME = re.compile(r'\breport|\brendition\b|\bfil(?:e|ed|ing)\b|\bsubmi|\btime\s+(?:limit|within|for)\b|'
                             r'\b(?:30|thirty)[- ]days?\b|\bdeadline|exten\w*\s+of\s+(?:the\s+)?time|'
                             r'exten\w*\s+(?:the\s+)?time', re.I)
SENTENCE_END = re.compile(r'[.;!?]["\'\u201d\u2019)]*(?=\s+[A-Z0-9("\'\u201c])')


def around(text, i, k=1, ahead=None):
    """The sentence holding offset i together with k sentences before it and ``ahead`` (default k) after it
    (sentence ends are approximate: initials such as 'D. C.' split one, which only narrows the context)."""
    ahead = k if ahead is None else ahead
    ends = [m.end() for m in SENTENCE_END.finditer(text)]
    before = [e for e in ends if e <= i]
    after = [e for e in ends if e > i]
    lo = before[-1 - k] if len(before) > k else 0
    hi = after[ahead] if len(after) > ahead else len(text)
    return text[lo:hi]


# Procedural events the board rule does not decide (o2 review, EO 10760): a stipulation of the parties about the
# proceedings, a reconstitution of the board (another membership, a one-member board, a replaced member), a
# reconvening, and a report period restarted from a later date. Any of them sends the order to exceptions, except
# a stipulation that is part of a report-time extension Olney records as a dated later event.
PROC_TERMS = [
    ('stipulation', re.compile(r'\bstipulat\w*', re.I)),
    ('reconstitution', re.compile(r'\breconstitut\w*|\bin\s+place\s+of\s+(?:the\s+)?(?:[\w-]+\s+){0,2}(?:board|members?)\b|'
                                  r'\bone[\s-]*(?:man|member)\s+board|\bthus\s+constituted', re.I)),
    ('member_change', re.compile(r'\b(?:resign\w*|vacanc\w*|replac\w*|substitut\w*|successor|to\s+succeed|'
                                 r'succeed\w*\s+(?:\w+\s+){0,3}?as\s+(?:a\s+)?(?:member|chairman))', re.I)),
    ('reconvening', re.compile(r'\breconven\w*', re.I)),
    ('restarted_period', re.compile(r'\bdays\s+(?:from|after)\s+(' + DATEX + r')|\bnew\s+(?:period|board)\b|'
                                    r'\b(?:begin|start|commenc|run)\w*\s+(?:anew|again)\b|'
                                    r'\bproceedings?\s+(?:\w+\s+){0,6}?continued\b|\bcontinu\w*\s+(?:the\s+)?proceedings', re.I)),
]
PROC_CONTEXT = re.compile(r'\bEmergency\s+Board\b|\b(?:the|this|said|such|our)\s+Board\b|\bproceedings?\b|'
                          r'\bExecutive\s+order\b|\bthe\s+President\b|\breport\s+(?:to|its|of)\b|\binvestigation\b', re.I)


def procedural_hits(text, signing=None, report_date=None):
    """[(offset, kind)] of procedural-event wording in text. A member change counts only when its context names a
    member of a board; 'N days from <date>' does not count when the date is the order's own signing date."""
    out = []
    for kind, rx in PROC_TERMS:
        for m in rx.finditer(text):
            # The proceedings are named in the sentence itself or the two before it (a stipulation follows the
            # board's convening; an agreement's own 'stipulation' is not followed back to the board).
            ctx = around(text, m.start(), 2, 0)
            if not PROC_CONTEXT.search(ctx):
                continue
            if kind == 'member_change' and not re.search(r'\bmember', ctx, re.I):
                continue
            if kind == 'restarted_period' and m.group(1) and signing:
                when = resolve(m.group(1), plus_days(signing, -366), plus_days(report_date or signing, 366))
                if when and when[0] == signing:
                    continue
            out.append((m.start(), kind))
    return sorted(out)


def procedural_problems(text, full_pages, events, signing, report_date, info=None):
    """Problems for the procedural events the report records (the whole report PDF and the held text). A stipulation
    inside the held passage of a recorded, dated extension is that extension's record and is not a problem; its
    page goes to ``info['covered_stipulation_pages']``."""
    info = {} if info is None else info
    info.setdefault('covered_stipulation_pages', [])
    if full_pages is None:
        return ['report_pdf_text_unreadable']
    pages = held_pages(text)
    held_max = max((p for p, _, _ in pages), default=0)
    full = {}
    for n, page in enumerate(full_pages, 1):
        hits = procedural_hits(unspace(re.sub(r'\s+', ' ', soft(page)[0])), signing, report_date)
        if hits:
            full[n] = sorted({k for _, k in hits})
    problems = {f'report_procedural_event_outside_held_text:{k}:p{p}' for p, ks in full.items() if p > held_max
                for k in ks}
    norm, back = soft(text)
    for page, lo, hi in pages:
        nlo, nhi = next(i for i, b in enumerate(back) if b >= lo), next(i for i, b in enumerate(back) if b >= hi)
        hits = procedural_hits(norm[nlo:nhi], signing, report_date)
        if page in full and not hits:
            problems.add(f'report_procedural_event_not_located_in_held_text:p{page}')
        for off, kind in hits:
            raw = back[nlo + off]
            if kind == 'stipulation' and any(e['char_start'] <= raw < e['char_end'] and e.get('approval_date')
                                             for e in events):
                info['covered_stipulation_pages'].append(page)
                continue
            problems.add(f'report_procedural_event:{kind}:p{page}')
    return sorted(problems)


def screen_full_report(pages):
    """{page_number: hit_count} of extension wording over the whole report (pdftotext pages, 1-based)."""
    found = {}
    for n, page in enumerate(pages, 1):
        hits = extension_hits(unspace(re.sub(r'\s+', ' ', soft(page)[0])))
        if hits:
            found[n] = len(hits)
    return found


def held_pages(text):
    """[(page_number, start, end)] of the held text's '=== PDF page N ===' sections."""
    marks = list(PAGE_MARK.finditer(text))
    return [(int(m.group(1)), m.end(), marks[i + 1].start() if i + 1 < len(marks) else len(text))
            for i, m in enumerate(marks)]


def sentences(norm, lo, hi):
    """[(start, end)] sentence ranges of norm[lo:hi] (a period, semicolon or colon followed by space and a capital,
    digit or parenthesis ends a sentence; initials such as 'D. C.' may split one, which only fails closed)."""
    out, s = [], lo
    for m in re.finditer(r'[.;](?=\s+[A-Z0-9(])', norm[lo:hi]):
        e = lo + m.end()
        if e - s > 1:
            out.append((s, e))
        s = e
        while s < hi and norm[s].isspace():
            s += 1
    if hi - s > 1:
        out.append((s, hi))
    return out


def extension_events(text, signing, report_date, full_pages, me=None, info=None):
    """(events, problems) for the report-time extensions a held report records.

    ``full_pages`` are the whole report's pdftotext pages (or None when the PDF could not be read). An extension
    becomes an event only when its passage is in the held text (``text``) and prints the President's approval date
    and the new report deadline as full dates; the event's span is the held passage. Any extension wording the held
    text cannot carry this way is a problem, so the order stays an exception rather than omitting the event. An
    extension printed without the President's approval date is a problem too (run v3): it cannot be dated exactly.
    ``info``, when given, receives the pages whose only extension wording is modal ('modal_pages')."""
    info = {} if info is None else info
    info.setdefault('modal_pages', [])
    if full_pages is None:
        return [], ['report_pdf_text_unreadable']
    found = screen_full_report(full_pages)
    pages = held_pages(text)
    held_max = max((p for p, _, _ in pages), default=0)
    problems = sorted({f'report_extension_outside_held_text:p{p}' for p in found if p > held_max})
    norm, back = soft(text)
    events = []
    for page, lo, hi in pages:
        nlo, nhi = next(i for i, b in enumerate(back) if b >= lo), next(i for i, b in enumerate(back) if b >= hi)
        hits = extension_hits(norm[nlo:nhi])
        if page not in found and not hits:
            continue
        sents = sentences(norm, nlo, nhi)
        if not hits:
            problems.append(f'report_extension_not_located_in_held_text:p{page}')
            continue
        chosen = set()
        for h in hits:
            idx = next((i for i, (s, e) in enumerate(sents) if s <= nlo + h < e), None)
            if idx is None:
                problems.append(f'report_extension_not_located_in_held_text:p{page}')
                continue
            chosen.add(idx)
            # The sentence before, when it too speaks of extending ('agreeing to extend until April 20, 1946 the
            # date for the Board to submit its report'), belongs to the same record.
            if idx and EXT_WORD.search(norm[sents[idx - 1][0]:sents[idx - 1][1]]):
                chosen.add(idx - 1)
            for j in range(idx + 1, min(idx + 3, len(sents))):
                if re.search(r'President|approv|grant|exten|e[^\w\s]{1,2}ten', norm[sents[j][0]:sents[j][1]], re.I):
                    chosen.add(j)
                else:
                    break
        groups, run = [], []
        for i in sorted(chosen):
            if run and i != run[-1] + 1:
                groups.append(run)
                run = []
            run.append(i)
        if run:
            groups.append(run)
        for g in groups:
            s0, s1 = sents[g[0]][0], sents[g[-1]][1]
            passage = re.sub(r'\s+', ' ', norm[s0:s1])
            if EXT_MULTIPLE.search(passage):
                problems.append(f'report_extension_multiple:p{page}')
                continue
            if numbers_named(passage) - {me}:
                problems.append(f'report_extension_by_executive_order:p{page}')
                continue
            lo = signing or '1900-01-01'
            approvals = {resolve(m.group(1), lo, report_date) for rx in APPROVAL for m in rx.finditer(passage)}
            approval_raw = {m.group(1) for rx in APPROVAL for m in rx.finditer(passage)}
            deadline_raw = {m.group(1) for m in DEADLINE.finditer(passage)} - approval_raw
            # A deadline printed without its year is read as the one such date within a year after the approval
            # (or, undated, after the signing); whether the report met it is checked below, never assumed.
            dated = {d for d, _ in approvals if d}
            start = min(dated) if len(dated) == 1 else lo
            deadlines = {resolve(r, lo, plus_days(report_date, 3660)) if parse_date(r) else
                         resolve(r, start, plus_days(start, 364)) for r in deadline_raw}
            if None in approvals or None in deadlines:
                problems.append(f'report_extension_date_unresolved:p{page}')
                continue
            if not deadlines and not approvals and MODAL_ONLY.search(passage) and not APPROVED_WORDING.search(passage):
                # Wording that time 'can be extended', with no extension granted, in a report made within the
                # order's own thirty days: no extension is recorded.
                if signing and report_date <= plus_days(signing, 30):
                    info['modal_pages'].append(page)
                    continue
            if len({d for d, _ in approvals}) > 1:
                problems.append(f'report_extension_approval_date_ambiguous:p{page}')
                continue
            if len({d for d, _ in deadlines}) != 1:
                problems.append(f'report_extension_deadline_{"not_printed" if not deadlines else "ambiguous"}:p{page}')
                continue
            (deadline, d_inferred), = deadlines
            approved, a_inferred = next(iter(approvals)) if approvals else (None, False)
            if approved is None and {m.group(0) for m in re.finditer(DATEX, passage, re.I)} - deadline_raw:
                # Another date is printed in the record (perhaps the approval in wording the patterns do not read):
                # 'no approval date printed' would not be safe to state.
                problems.append(f'report_extension_approval_date_unparsed:p{page}')
                continue
            if approved is None:
                # Run v3 (o2 review, EO 10969): an extension the report prints without the President's approval date
                # cannot be dated exactly, so the order is an exception (it is never recorded as an undated note).
                problems.append(f'report_extension_approval_date_not_printed:p{page}')
                continue
            if approved and not approved < deadline:
                problems.append(f'report_extension_dates_out_of_order:p{page}')
                continue
            if report_date > deadline:
                problems.append(f'report_after_extended_deadline:p{page}')
                continue
            raw0 = back[s0]
            raw1 = back[s1] if s1 < len(back) else len(text)
            while raw1 > raw0 and text[raw1 - 1].isspace():
                raw1 -= 1
            events.append({'approval_date': approved, 'approval_year_inferred': a_inferred,
                           'approval_printed': bool(APPROVED_WORDING.search(passage)),
                           'new_deadline': deadline, 'deadline_year_inferred': d_inferred, 'page': page,
                           'char_start': raw0, 'char_end': raw1})
    # One extension printed twice (the narrative and the NMB letter, say) is one event.
    # A dated record of the same deadline wins over an undated one.
    merged = {}
    for e in sorted(events, key=lambda e: e['approval_date'] is None):
        key = e['new_deadline']
        if key not in merged:
            merged[key] = e
        elif e['approval_date'] and e['approval_date'] != merged[key]['approval_date']:
            problems.append('report_extension_records_disagree')
    events = sorted(merged.values(), key=lambda e: e['new_deadline'])
    if len(events) > 1:
        problems.append('report_extension_multiple:records')
    return events, sorted(set(problems))


def pdftotext_pages(pdf, cache_dir):
    """The PDF's text by page (pdftotext, reading order), cached by the PDF's SHA-256; None if unreadable."""
    raw = Path(pdf).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    cache = Path(cache_dir) / (sha + '.txt')
    if not cache.is_file():
        cache.parent.mkdir(parents=True, exist_ok=True)
        run = subprocess.run(['pdftotext', '-q', str(pdf), str(cache) + '.tmp'], capture_output=True)
        if run.returncode or not Path(str(cache) + '.tmp').is_file():
            return None
        os.replace(str(cache) + '.tmp', cache)
    pages = cache.read_text(encoding='utf-8', errors='replace').split('\f')
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return pages


def pdftotext_version():
    try:
        run = subprocess.run(['pdftotext', '-v'], capture_output=True, text=True)
        return (run.stderr or run.stdout).splitlines()[0].strip()
    except (OSError, IndexError):
        return None


# The statutory no-change sentence. OCR of the Federal Register damages single words of this fixed wording
# ('thff board', 'nas made', 'ehange'); one damaged letter in 'the', 'board', 'has' or 'change' is tolerated, and
# the claim quotes the held text as it stands.
STANDSTILL = re.compile(r'thirty\s+days\s+after\s+(th[a-z]{1,2}\s+)?(said\s+)?[bB][a-z]{3,4}\s+([hn]as\s+)?'
                        r'(shall\s+have\s+)?made\s+its\s+report', re.I)
NO_CHANGE = re.compile(r'no\s+(change|[a-z]hange|[a-z]?nange|c[a-z]ange|ch[a-z]nge)\b', re.I)


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
        if NO_CHANGE.search(norm):
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
    if not NO_CHANGE.search(sentence) or not re.search(r'except\s+by\s+agreement', sentence, re.I):
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


SAVINGS_WORDS = re.compile(r'\b(?:sav(?:e|es|ed|ing|ings)|except\w*|provid\w*|nothing|pending|notwithstanding|'
                           r'continu\w*|effect\w*)\b', re.I)
SAVINGS_TERMS = "save or saving, except, provided, nothing, pending, notwithstanding, continue and effect"


def savings_scan(repo, claim):
    """(scan, problem). The filed claim's savings source must be the held text of the revoking order (EO 12553 or
    EO 12379). Olney reads that order from its heading to its FR document line for savings wording; a hit outside
    the subject lines of its table of revoked orders is a problem (o2/o3 review: the savings text is generated
    from what Olney itself read, never carried from another claim)."""
    cleanup = cleanup_of(claim)
    src = (claim.get('savings_residuals') or {}).get('source') or {}
    path = src.get('text_path')
    if not cleanup or not path or Path(path).name != f'EO_{order_number(cleanup[0])}.txt':
        return None, 'savings_source_not_the_revoking_order'
    full = Path(repo) / path
    if not full.is_file():
        return None, 'savings_source_text_missing'
    raw = full.read_bytes()
    if src.get('text_sha256') not in (None, hashlib.sha256(raw).hexdigest()):
        return None, 'savings_source_text_changed'
    text = raw.decode('utf-8')
    head = re.search(r'Executive\s+Order\s+' + order_number(cleanup[0]) + r'\b', text)
    revoked = re.search(r'are\s+revoked\s*:', text[head.end():]) if head else None
    if not revoked:
        return None, 'savings_source_table_not_found'
    t0 = head.end() + revoked.end()
    close = re.search(r'^\s*(?:Editorial\s+note|T\s?H\s?E\s+W\s?H\s?I\s?T\s?E\s+H\s?O\s?U\s?S\s?E)', text[t0:], re.M | re.I)
    doc = re.search(r'\[FR\s+Doc', text[t0:])
    if not close or not doc or doc.start() < close.start():
        return None, 'savings_source_table_not_found'
    t1, end = t0 + close.start(), t0 + doc.start()
    inside = outside = 0
    for m in SAVINGS_WORDS.finditer(text, head.start(), end):
        if t0 <= m.start() < t1:
            inside += 1
        else:
            outside += 1
    scan = {'instrument': cleanup[0], 'text_path': path, 'hits_in_table': inside, 'hits_outside_table': outside}
    return scan, ('savings_source_wording_outside_table' if outside else None)


def savings_words(r, actor, cdate, ends):
    """The savings reason, generated from what Olney read and from this claim's own clause ends."""
    sc = r['savings_scan']
    found = (f"found them only in the subject lines of its table of revoked orders" if sc['hits_in_table']
             else "found none")
    return (f"{actor} ({cdate}) revokes this order by number. Olney read its held text ({sc['text_path']}), from "
            f"its heading to its Federal Register document line, for {SAVINGS_TERMS} and {found}, so it carries no "
            f"savings or transition provision. This claim ends {ends}, before that revocation, and no held source "
            f"read for this claim shows a command of the order continuing after that. Section 10 of the Railway "
            f"Labor Act, which the order applied, does not depend on the order.")


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
    eumenes, ptolemy, ladder, readiness, locks, claims, lanes, include_pc, cache_dir = ctx
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
    pdf = None
    if not local or not (Path(repo) / local).is_file():
        local = None
        # A report held only in the Pergamon store goes through the kit's Pergamon supplement route when the
        # checkout's claim kit carries it (proposed/pergamon_supplement.patch, applied as a code change).
        pg = (eumenes.get(sha) or {}).get('pergamon')
        if not kit_supports_pergamon(repo):
            reasons.append('report_bytes_pergamon_only_kit_gap')
        elif not (isinstance(pg, dict) and pg.get('sha256') == sha and pg.get('locator')):
            reasons.append('report_bytes_not_held')
        else:
            pdf = pergamon_pdf(repo, pg, cache_dir)
            if pdf is None:
                reasons.append('report_pergamon_fetch_failed')
    else:
        pdf = Path(repo) / local
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
        rec['savings_scan'], problem = savings_scan(repo, claim)
        if problem:
            reasons.append(problem)
    if text is not None and not any(r.startswith(('letter_date', 'report_date')) for r in reasons):
        span, problems = report_span(text, cand, iid, signing)
        reasons += problems
        rec['span'] = span
        if span and pdf is not None:
            pages = pdftotext_pages(pdf, cache_dir)
            ext_info, proc_info = {}, {}
            events, problems = extension_events(text, signing, span['date'], pages, order_number(iid), ext_info)
            reasons += problems
            rec['extensions'] = events
            # Run v3 (o2 review, EO 10760): stipulations, reconstitution and restarted periods are exceptions.
            reasons += procedural_problems(text, pages, events, signing, span['date'], proc_info)
            if pages is not None:
                rec['full_report_screen'] = {
                    'tool': pdftotext_version(), 'pages': len(pages),
                    'pages_without_text': sum(1 for pg in pages if len(re.sub(r'\s', '', pg)) < 40),
                    'held_text_pages': [p for p, _, _ in held_pages(text)],
                    'extension_pages': sorted(screen_full_report(pages)),
                    'modal_only_pages': sorted(set(ext_info['modal_pages'])),
                    'covered_stipulation_pages': sorted(set(proc_info['covered_stipulation_pages']))}
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
    cache_dir = Path(os.environ.get('OLNEY_CACHE_DIR') or Path.home() / '.cache/eo-olney')
    ctx = (eumenes, ptolemy, ladder, readiness, locks, claims, lanes, include_pc, cache_dir)
    selected, exceptions, excluded = [], [], []
    for iid in universe:
        if iid in UPHELD | UPHELD_V2:
            excluded.append(iid)
            continue
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
    return {'schema': 'eo-olney-selection/v2', 'rule': RULE, 'cover_rule': COVER_RULE, 'run': RUN,
            'universe': len(universe), 'excluded_already_upheld': excluded, 'judged': len(universe) - len(excluded),
            'universe_definition': 'Lind CANDIDATES.json orders in the production.one_step_away stratum',
            'kit_supports_pergamon': kit_supports_pergamon(repo),
            'universe_lanes': dict({k: sum(1 for i in universe if lanes.get(i, '').startswith(k)) for k in ('c', 'p')},
                                   none=sum(1 for i in universe if i not in lanes)),
            'include_pc_lanes': include_pc, 'selected': selected, 'exceptions': exceptions,
            'exceptions_by_reason_any': dict(sorted(by_reason.items())),
            'wall_seconds': round(time.monotonic() - started, 2), 'model_tokens': 0}


# ------------------------------------------------------------------------------------------------- writing

def alias(iid, part):
    return f'olney_{part}_' + re.sub(r'\W', '_', order_number(iid))


def ext_alias(iid, k):
    return f'olney_ext{k}_' + re.sub(r'\W', '_', order_number(iid))


def letter_words(sp):
    """What the held text shows of the letter of transmittal on the cover route, true of the quoted span (run v3,
    o2/o3 review: a date line present but unreadable is never described as not found)."""
    letter = sp.get('letter') or {}
    status = letter.get('status')
    if status == 'unreadable':
        out = (f"the letter of transmittal's date line is in the held text but does not read cleanly as a date "
               f"('{letter['letter_date_raw']}')")
        diffs = letter.get('legible_differences') or []
        if diffs:
            out += '; ' + ' and '.join(f"its legible {k} reads {a} where the cover reads {b}" for k, a, b in diffs)
            if letter.get('legible_year_before_signing'):
                out += f", and that year is earlier than the order's signing on {letter['signing_date']}"
        return out
    if status == 'not_found_before_address':
        return 'the held letter of transmittal has no date line before its address to the President'
    if status == 'no_letter_held':
        return 'no letter of transmittal was found after the cover in the held text'
    raise ValueError('cover route without a letter status: ' + str(status))


BASIS_WORDS = {'unreadable': "the letter's date line does not read cleanly",
               'not_found_before_address': 'the held letter has no date line',
               'no_letter_held': 'no letter of transmittal was found after the cover'}


def date_words(sp):
    """How the span dates the report: the clean letter date line, or (D-20261125-board-cover-date) the cover."""
    if sp.get('date_basis') == 'cover':
        return (f"{letter_words(sp)}; under owner decision {COVER_RULE} the report is dated by its cover, whose date "
                f"line '{sp['cover_date_raw']}' reads cleanly as {sp['date']}")
    raw = sp.get('letter_date_raw') or sp.get('date_raw') or sp['date']
    return f"the letter of transmittal's date line '{raw}' reads cleanly as {sp['date']}"


def declaration(sel):
    """source_supplement declaration: the report span twice (board end, standstill end), and each recorded
    report-time extension's held passage, from the same held report."""
    entries = []
    for r in sel:
        sp = r['span']
        source = {'url': r['report_url'], 'sha256': r['report_sha256'], 'text_path': r['report_text_path'],
                  'text_sha256': r['report_text_sha256'], 'page_or_item': r['report_page_or_item'],
                  'local_path': r['report_local_path']}
        board = f"Emergency Board No. {r['peb']} ({r['instrument_id']})"
        what = ('Report cover and letter of transmittal' if sp.get('submission_offset') is not None
                else 'Report cover')
        rule = RULE + (f' (a); dated by the cover under {COVER_RULE}' if sp.get('date_basis') == 'cover' else ' (a)')
        entries.append({'alias': alias(r['instrument_id'], 'board'), 'instrument_ids': [r['instrument_id']],
                        'actor_id': board, 'source': source, 'char_start': sp['char_start'], 'char_end': sp['char_end'],
                        'reason': f"{what} of {board}, dated {sp['date']}"
                                  + (', through the sentence submitting the report' if sp.get('submission_offset') is not None else '')
                                  + f"; evidences the report on that date ({rule})."})
        if r.get('standstill_range'):
            entries.append({'alias': alias(r['instrument_id'], 'standstill'), 'instrument_ids': [r['instrument_id']],
                            'actor_id': r['instrument_id'], 'source': source, 'char_start': sp['char_start'],
                            'char_end': sp['char_end'],
                            'reason': f"Same report span: dates the report ({sp['date']}) from which the order's own "
                                      f"no-change sentence runs thirty days ({RULE} (b))."})
        for k, e in enumerate(r.get('extensions') or [], 1):
            entries.append({'alias': ext_alias(r['instrument_id'], k), 'instrument_ids': [r['instrument_id']],
                            'actor_id': f"The President (extension of the report time of {board})",
                            'source': source, 'char_start': e['char_start'], 'char_end': e['char_end'],
                            'reason': f"Held report passage (PDF page {e['page']}) recording an extension of the "
                                      f"board's time to report, to {e['new_deadline']}"
                                      + (f", approved on {e['approval_date']}" if e['approval_date'] else '')
                                      + '; a later event of the board clause (batch o1 review).'})
    return {'schema': 'eo-source-excerpt-declarations/v1', 'sources': entries}


def pages_words(pages):
    pages = sorted(set(pages))
    return ('page ' if len(pages) == 1 else 'pages ') + ', '.join(map(str, pages))


def screen_words(r):
    """What Olney's whole-report screen found, stated only as far as the screen reaches."""
    sc = r.get('full_report_screen') or {}
    exts = r.get('extensions') or []
    pages, blank = sc.get('pages'), sc.get('pages_without_text') or 0
    out = (f"Olney screened the {pages - blank} of {pages} report PDF pages that have a text layer ({sc.get('tool')})"
           + (f"; the other {blank} have fewer than 40 characters of text and could not be screened" if blank else '')
           + ". It looked for wording that extends the board's time to report (any form of 'extend' or 'extension', "
             "also with a damaged x, or more or postponed time, in or near a sentence about the report or its time) "
             "and for wording about the proceedings of a stipulation, a reconstituted board, a changed member, a "
             "reconvening or a restarted report period.")
    if exts:
        out += (f" The extension wording it found is on the held {pages_words(e['page'] for e in exts)} and records "
                + ('one extension' if len(exts) == 1 else f'{len(exts)} extensions')
                + ", recorded as a later event of the board clause.")
    elif sc.get('modal_only_pages'):
        out += (f" The only extension wording it found, on {pages_words(sc['modal_only_pages'])}, says that the time "
                f"for the report can be extended; no extension was granted, and the report was made within the "
                f"order's thirty days.")
    else:
        out += " It found no wording extending the board's time to report."
    if sc.get('covered_stipulation_pages'):
        out += (f" The only stipulation it found, on {pages_words(sc['covered_stipulation_pages'])}, is the parties' "
                f"agreement to that extension; it found no other procedural wording.")
    else:
        out += ' It found none of the procedural wording.'
    return out


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
    cover = sp.get('date_basis') == 'cover'
    if cover:
        disclosure = (f'Disclosed under {COVER_RULE}: the report date is read from the cover, not from the letter '
                      f'of transmittal; the report was made on or about that date, and receipt by the President may '
                      f'have been later.')
    else:
        disclosure = ('The transmittal letter evidences submission on its date; receipt by the President may have '
                      'been later.')
    exts = r.get('extensions') or []
    whole_end = plus_days(D, 30) if r.get('standstill_range') else D
    later = [{'id': ceid, 'effective_date': cdate, 'effective_date_confirmed': True,
              'mechanism': f'{cmech} (formal disposition: {actor} cleanup revocation, kept under {RULE})'}]
    board_later = list(later)
    ext_words = []
    for k, e in enumerate(exts, 1):
        eid = 'SUPPLEMENT:' + ext_alias(iid, k)
        inferred = []
        if e['approval_year_inferred']:
            inferred.append('the approval date')
        if e['deadline_year_inferred']:
            inferred.append('the new deadline')
        year_note = ''
        if e['approval_year_inferred']:
            year_note += (" The passage prints the approval date without the year; the year is the only one that "
                          f"puts it between the order's signing and the report ({D}).")
        if e['deadline_year_inferred']:
            year_note += (" The passage prints the new deadline without the year; the year is the only one that puts "
                          "it within a year after the approval.")
        if not e['approval_date']:
            # Run v3: an extension without a printed approval date is an exception at selection; never written.
            problems.append('extension_without_approval_date:' + eid)
            continue
        board_later.append({'id': eid, 'effective_date': e['approval_date'], 'effective_date_confirmed': True,
                            'mechanism': f"extension of the board's time to report, to {e['new_deadline']}, "
                                         f"approved by the President on {e['approval_date']} (held report, PDF "
                                         f"page {e['page']}); the board clause continued and its report of {D} "
                                         f"completed it.{year_note}"})
        ext_words.append(f"extended to {e['new_deadline']} with the President's approval of {e['approval_date']} "
                         f"(later event {eid})")
    board_reason = (f"Ended by completion of its task under {rule_ref} (a): the board was created to investigate the "
                    f"dispute and report to the President. The held report of Emergency Board No. {r['peb']} "
                    f"(SHA-256 {r['report_sha256'][:12]}...) is dated {D}: {date_words(sp)}"
                    + ("; the letter submits the report" if sp.get('submission_offset') is not None else '')
                    + f". The NMB inventory's closing date for the board agrees ({LIND_AGREES}). So the task was "
                      f"performed on {D}. {disclosure}"
                    + (f" The order's report time was {'; '.join(ext_words)}; an extension moved the deadline and did "
                       f"not end the clause." if ext_words else '')
                    + f" The report deadline in the order is not the end. {actor} ({cdate}) stays the formal "
                      f"disposition, recorded as a later event.")
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
                     later_event_ids=canon([e['id'] for e in board_later]), later_events=canon(board_later),
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
                                 f"after the board has made its report'. Report date {D} (held report, above"
                                 + (f"; dated by the cover under {COVER_RULE}" if cover else '') + f"). Inclusive "
                                 f"reading: the period ends at the end of the thirtieth day after {D}, that is {D} + "
                                 f"30 days = {end}. Exclusive reading, stated as the alternative: {plus_days(D, 29)}. "
                                 f"{disclosure} {actor} ({cdate}) stays the formal disposition, recorded as a later "
                                 f"event."),
                         inventory_char_start=str(s0), inventory_char_end=str(s1),
                         inventory_reason=inv.format(rule=RULE, a=s0, b=s1)))
    basis_words = (f"the cover date ({BASIS_WORDS[sp['letter']['status']]}; {COVER_RULE})" if cover
                   else 'the letter of transmittal date')
    has_standstill = bool(r.get('standstill_range'))
    ends = f"the board clause on {D} (completion of its task)" + (
        f" and the no-change period on {whole_end} (its own terms)" if has_standstill else '')
    row = dict(decision_row)
    row.update(outcome='submit', approved='true', original_confirmed='true', inventory_confirmed='true',
               original_pages_confirmed='true' if (claim.get('claim_kit') or {}).get('original_pages_confirmed') else 'false',
               research_rationale=(
                   f"Scripted replacement proposal (Olney {RUN}, zero model tokens) applying {rule_ref} to {iid}. "
                   f"Original: the dossier's held original {orig_id}, the same printing the filed claim "
                   f"({r['claim_file']}) cites. Report: NMB report of Emergency Board No. {r['peb']}, held bytes "
                   f"{r['report_local_path'] or 'in the Pergamon store'}, text {r['report_text_path']}; the quoted "
                   f"span runs from the cover"
                   + (" to the sentence submitting the report" if sp.get('submission_offset') is not None else
                      " through its date line (no letter of transmittal was found after the cover in the held text)")
                   + f", and names the order by {sp['identity'].replace('_', ' ')}. Report dated by {basis_words}. "
                   f"Clause ends: board {D}"
                   + (f"; no-change period {whole_end} (inclusive; exclusive {plus_days(D, 29)})" if r.get('standstill_range') else '')
                   + f". Whole-order end {whole_end}. Formal disposition {actor} of {cdate}. "
                   + (f"Report-time extensions recorded: {len(exts)}. " if exts else '')
                   + f"The savings state and the later-source search are carried from the filed claim; the "
                     f"savings reason is generated from Olney's own reading of {actor}."),
               savings_state=sav.get('state') or '', savings_source_id=sav_id or '',
               savings_reason=savings_words(r, actor, cdate, ends), search_ids=canon(chosen),
               conflict_resolutions='{}', unresolved_material_gaps='[]', publication_kind='whole_case',
               earlier_end_check=(f"No earlier end: the board's task could not be complete before its report of {D}"
                                  + (", and the no-change period runs from the report" if has_standstill else '')
                                  + f". {screen_words(r)} No amendment, reconvening, supplemental report or "
                                    f"congressional action is flagged for this order in Lind's exception checks or "
                                    f"the NMB inventory."),
               scope_check=("The clauses cover the order's operative text: the board clause"
                            + (" and the no-change sentence" if has_standstill else '')
                            + "; the recitals and heading stay with the board clause."),
               independent_command_check=("No command other than create-investigate-report"
                                          + (" and the no-change sentence" if has_standstill else '')
                                          + " is present (scripted wording screen; any other wording sends the "
                                            "order to exceptions)."),
               savings_check=(f"Savings state {sav.get('state')} is the filed claim's; the reason is Olney's reading "
                              f"of {actor}'s held text and this claim's own clause ends."))
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
    receipt = {'schema': 'eo-olney-batch/v2', 'run': RUN, 'batch': name, 'orders': ids, 'steps': {}, 'per_order': {},
               'code_sha256': sha_file(__file__), 'selection_sha256': sha_file(HERE / 'output/SELECTION.json'),
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
                                         'date_basis': r['span'].get('date_basis'),
                                         'extensions': [{k: e[k] for k in ('approval_date', 'new_deadline', 'page')}
                                                        for e in r.get('extensions') or []],
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
GROUP = [('letter_date_legible_part_conflicts', 'letter_and_cover_dates_conflict'),
         ('letter_date_line', 'letter_reading_doubt'), ('letter_address', 'letter_reading_doubt'),
         ('letter_held_submission', 'submission_sentence_not_found'),
         ('report_procedural', 'report_procedural_event'), ('savings_source', 'savings_source_doubt'),
         ('letter_date', 'letter_date_unreadable_and_cover_not_clean'), ('cover_date', 'letter_and_cover_dates_conflict'),
         ('submission', 'submission_sentence_not_found'), ('order_identity', 'report_identity_doubt'),
         ('other_order', 'report_identity_doubt'), ('board_number', 'report_identity_doubt'),
         ('span_too_long', 'report_identity_doubt'), ('report_extension', 'report_extension_not_scriptable'),
         ('report_after_extended', 'report_extension_not_scriptable'), ('report_pdf', 'report_extension_not_scriptable'),
         ('report_pergamon_fetch', 'report_bytes_pergamon_only_kit_gap')]
# What each remaining exception needs before the rule can be applied to it (handback item 4).
NEEDS = {
    'follow_on_order': 'A producer claim: the order amends or extends another board order, so its end follows the '
                       'parent board and the instrument that names it (not covered by the board rule as written).',
    'report_shared_with_follow_on_order': 'One report answers two orders (a board order and its follow-on); a '
                                          'producer must assign the report to each order and decide whether the '
                                          'follow-on reset the deadline. Needs a two-order claim, reviewed together.',
    'congressional_action': 'Congress legislated on the dispute (NMB inventory); a producer must decide whether '
                            'the statute ended or displaced the board or the no-change period. Owner rule does not '
                            'cover it.',
    'reconvened_or_supplemental_report': 'The board reconvened or filed a supplemental report; which report '
                                         'completed the task needs a producer judgment and a second span.',
    'nmb_lists_extra_documents': 'The NMB lists further documents for the board (letters, a second report); a '
                                 'producer must read them for a later report or reconvening.',
    'multi_clause_claim': 'The filed claim has more than two clauses (extra commands); each needs its own end '
                          'beyond the board rule.',
    'dossier_inventory_not_single_clause': 'The kit dossier splits the order into several clauses (often FR '
                                           'layout or added commands); a producer must reconcile the inventory '
                                           'before the scripted split applies.',
    'report_date_not_corroborated': "Lind's report date is not corroborated (image check needed or held readings "
                                    'conflict); needs a page-image check of the cover and letter (Lind '
                                    'UNREAD_IMAGE_CHECK_NEEDED/CONFLICT_IMAGE_CHECK_NEEDED).',
    'letter_date_unreadable_and_cover_not_clean': 'Neither the letter date line nor the cover date reads cleanly '
                                                  'as the corroborated date; needs a page-image reading.',
    'letter_and_cover_dates_conflict': 'The letter date line reads cleanly as a date other than the cover date '
                                       '(an OCR misreading or a real difference); needs a page-image reading of '
                                       'both lines. D-20261125-board-cover-date covers only an unreadable line.',
    'submission_sentence_not_found': 'The letter is held but no submission sentence was found; needs a manual '
                                     'span or a page check.',
    'report_identity_doubt': 'The quoted span does not name the order (number, or appointment date with the board '
                             'number), or names another order; needs a producer identity check.',
    'report_extension_not_scriptable': 'The report records a report-time extension Olney cannot carry as a later '
                                       'event: outside the held pages (needs a held text of the later pages), '
                                       'several extensions, an unparsed or ambiguous approval date or deadline, '
                                       'or (run v3) no printed approval date or new deadline. '
                                       'Needs a producer to record each extension, or a held text of the pages.',
    'filed_claim_changed_since_lind': 'A claim file newer than the one Lind read names the order (EO 11343 was filed '
                                      'by standing auto-adoption after the v2 review); Olney does not replace it.',
    'report_procedural_event': 'The report records a stipulation about the proceedings, a reconstituted board or '
                               'changed member, a reconvening or a report period restarted from a later date (o2 '
                               'review, EO 10760). The board rule does not say which act completed the task or when '
                               'the no-change period ran; needs a producer claim that records the event.',
    'letter_reading_doubt': "Olney's reading of the held letter (its date line or its address to the President) "
                            "disagrees with Lind's, or a 'no date line' statement would not hold of the quoted span; "
                            'needs a page-image reading of the letter.',
    'savings_source_doubt': "The filed claim's savings source is not the revoking order's held text, or that text has "
                            'savings wording outside its table of revoked orders; needs a producer savings reading.',
    'clause_inventory_doubt': 'The order text has wording beyond create-investigate-report and the no-change '
                              'sentence (another command, damaged or interleaved FR text); needs a producer '
                              'clause inventory.',
    'report_bytes_pergamon_only_kit_gap': 'The report bytes are only in the Pergamon store; needs the claim-kit '
                                          'change on branch claude/olney-v2 merged, then an Olney rerun.',
    'original_bytes_not_held': "The order's own Federal Register bytes are only a custody record; needs the "
                               'original PDF kept (dispatch refuses the packet).',
}


def primary(reasons):
    """One reason per order for a breakdown that sums: the order's case-level exception before any extraction or
    wording doubt, and the Pergamon-only kit gap last (so its count is the orders blocked by that gap alone)."""
    keys = [r.split(':', 1)[0] for r in reasons]
    for k in PRIORITY:
        if k in keys:
            return k
    rest = [k for k in keys if k != 'report_bytes_pergamon_only_kit_gap']
    for k in rest:
        for prefix, name in GROUP:
            if k.startswith(prefix):
                return name
    return 'clause_inventory_doubt' if rest else 'report_bytes_pergamon_only_kit_gap'


def report(repo, preview=None):
    repo = Path(repo)
    selection = json.loads((HERE / 'output/SELECTION.json').read_bytes())
    batches = []
    for p in sorted((repo / OLNEY).glob('*/OLNEY_BATCH.json')):
        b = json.loads(p.read_bytes())
        if b.get('run') == selection.get('run') and not b.get('trial'):
            batches.append(b)
    per = {}
    for b in batches:
        for i, v in b['per_order'].items():
            per[i] = dict(v, batch=b['batch'])
    failing = {i: {k: v.get(k) for k in ('batch', 'outcome', 'problems', 'apply_outcome', 'apply_errors',
                                         'selected_source_blockers', 'checker_failures', 'checker_unverified',
                                         'checker_gate_errors') if v.get(k)}
               for i, v in per.items() if not v.get('checker_all_checks_passed')}
    # An order the kit refuses at dispatch (its original's bytes are only a custody record) is an exception too.
    after = {e['instrument_id']: list(e['reasons']) for e in selection['exceptions']}
    for i, v in failing.items():
        if 'dispatch_source_blocked' in (v.get('problems') or []):
            after[i] = ['original_bytes_not_held:dispatch_source_blocked']
    by_primary = {}
    for i, reasons in after.items():
        k = 'original_bytes_not_held' if reasons[0].startswith('original_bytes_not_held') else primary(reasons)
        by_primary.setdefault(k, []).append(i)
    passing_ids = sorted(i for i, v in per.items() if v.get('checker_all_checks_passed'))
    folders = {b['batch']: f"{OLNEY}/{b['batch']}/supplemented" for b in batches}
    result = {'schema': 'eo-olney-result/v2', 'run': selection.get('run'), 'rule': RULE,
              'cover_rule': selection.get('cover_rule'), 'model_tokens': 0,
              'universe': selection['universe'], 'universe_lanes': selection['universe_lanes'],
              'excluded_already_upheld': selection.get('excluded_already_upheld', []),
              'judged': selection.get('judged', selection['universe']),
              'kit_supports_pergamon': selection.get('kit_supports_pergamon'),
              'selected': len(selection['selected']), 'selected_ids': [r['instrument_id'] for r in selection['selected']],
              'selected_by_date_basis': {k: sorted(r['instrument_id'] for r in selection['selected']
                                                   if r['span'].get('date_basis') == k) for k in ('letter', 'cover')},
              'selected_with_extensions': {r['instrument_id']: r['extensions'] for r in selection['selected']
                                           if r.get('extensions')},
              'exceptions': len(after),
              'exceptions_by_reason_any': selection['exceptions_by_reason_any'],
              'exceptions_by_primary_reason': {k: len(v) for k, v in sorted(by_primary.items(), key=lambda x: -len(x[1]))},
              'exceptions_by_primary_reason_ids': {k: sorted(v) for k, v in sorted(by_primary.items())},
              'exception_needs': {k: NEEDS.get(k, '') for k in sorted(by_primary)},
              'exceptions_list': after,
              'prepared': sum(len(b['orders']) for b in batches if 'prepare' in b['steps']),
              'checker_passing': passing_ids,
              'checker_passing_by_batch': {b['batch']: sorted(passing(b)) for b in batches},
              'review_packets': {b['batch']: folders[b['batch']] for b in batches if passing(b)},
              'failing': failing,
              'batches': [{'batch': b['batch'], 'orders': len(b['orders']), 'passing': len(passing(b)),
                           'wall_seconds': {k: v.get('wall_seconds') for k, v in b['steps'].items()}} for b in batches],
              'selection_wall_seconds': selection['wall_seconds']}
    if preview:
        pv = json.loads(Path(preview).read_bytes())
        extra = sorted({r['instrument_id'] for r in pv['selected']} - set(result['selected_ids']))
        result['pergamon_kit_preview'] = {
            'note': 'Selection with the claim-kit Pergamon change assumed merged (select --out, '
                    'OLNEY_ASSUME_PERGAMON_KIT=1); no packet was prepared for these orders.',
            'selected': len(pv['selected']), 'additional_orders': extra}
    dump(HERE / 'output/RESULT.json', result)
    lines = ['# Olney result (run ' + str(result['run']) + ')', '',
             f"Rules {RULE} and {result['cover_rule']}; zero model tokens. The universe is the "
             f"{result['universe']} board orders in production.one_step_away (Lind candidates). The "
             f"{len(result['excluded_already_upheld'])} orders upheld by both blind arms in earlier runs are not "
             f"rerun ({', '.join(result['excluded_already_upheld'])}), so {result['judged']} orders were judged.", '',
             f"- Selected: {result['selected']} ({len(result['selected_by_date_basis']['letter'])} dated by the "
             f"letter of transmittal, {len(result['selected_by_date_basis']['cover'])} by the cover under "
             f"{result['cover_rule']}; {len(result['selected_with_extensions'])} with recorded report-time "
             f"extensions)",
             f"- Prepared: {result['prepared']}",
             f"- Checker-passing: {len(passing_ids)}",
             f"- Exceptions: {result['exceptions']} (including orders the kit refused at dispatch)", '']
    if result['review_packets']:
        lines += ['## Checker-passing packets for blind review', '', '| Batch | Packet | Orders |', '|---|---|---|']
        lines += [f"| {k} | `{v}` | {', '.join(result['checker_passing_by_batch'][k])} |"
                  for k, v in result['review_packets'].items()]
        lines += ['']
    lines += ['## Exceptions, one primary reason per order, and what each needs', '',
              '| Primary reason | Orders | Needs |', '|---|---:|---|']
    lines += [f"| {k} | {v} | {result['exception_needs'].get(k, '')} |"
              for k, v in result['exceptions_by_primary_reason'].items()]
    lines += ['', '## Exceptions, every reason (an order can carry several)', '', '| Reason | Orders |', '|---|---:|']
    lines += [f'| {k} | {v} |' for k, v in sorted(result['exceptions_by_reason_any'].items(), key=lambda x: -x[1])]
    if result.get('pergamon_kit_preview'):
        pv = result['pergamon_kit_preview']
        lines += ['', '## After the claim-kit Pergamon change is merged', '',
                  f"A preview selection with the change assumed selects {pv['selected']} orders, adding "
                  f"{len(pv['additional_orders'])}: {', '.join(pv['additional_orders'])}. {pv['note']}"]
    lines += ['', '## Batches', '', '| Batch | Orders | Passing | Wall seconds by step |', '|---|---:|---:|---|']
    lines += [f"| {b['batch']} | {b['orders']} | {b['passing']} | {canon(b['wall_seconds'])} |" for b in result['batches']]
    if failing:
        lines += ['', '## Not checker-passing', '']
        lines += [f'- {i}: {canon(v)[:400]}' for i, v in sorted(failing.items())]
    (HERE / 'output/RESULT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--repo', type=Path, default=HERE.parents[1])
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('select')
    s.add_argument('--include-pc-lanes', action='store_true', help='also select orders assigned to the PC lanes')
    s.add_argument('--out', type=Path, help='write the selection here instead of output/SELECTION.json (previews)')
    s = sub.add_parser('run')
    s.add_argument('--batch', required=True)
    s.add_argument('--n', type=int, default=8)
    s.add_argument('--ids', nargs='*')
    s = sub.add_parser('report')
    s.add_argument('--preview', type=Path, help='a Pergamon-kit preview selection to summarize')
    a = p.parse_args(argv)
    repo = a.repo.resolve()
    if a.command == 'select':
        result = select(repo, a.include_pc_lanes)
        if os.environ.get('OLNEY_ASSUME_PERGAMON_KIT') == '1' and not a.out:
            raise SystemExit('a Pergamon preview is written with --out, never as the run selection')
        dump(a.out or HERE / 'output/SELECTION.json', result)
        print(json.dumps({k: result[k] for k in ('universe', 'universe_lanes', 'exceptions_by_reason_any', 'wall_seconds')}
                         | {'selected': len(result['selected']), 'exceptions': len(result['exceptions'])}, indent=2))
        return 0
    if a.command == 'run':
        selection = json.loads((HERE / 'output/SELECTION.json').read_bytes())
        done = set()
        for p_ in (repo / OLNEY).glob('*/OLNEY_BATCH.json'):
            b = json.loads(p_.read_bytes())
            if b.get('run') == RUN:
                done |= set(b['orders'])
        ids = a.ids or [r['instrument_id'] for r in selection['selected'] if r['instrument_id'] not in done][:a.n]
        if not ids or len(ids) > 20:
            raise SystemExit('1-20 orders per batch')
        receipt = run_batch(repo, a.batch, ids, selection)
        print(json.dumps({'batch': a.batch, 'orders': len(ids), 'passing': len(passing(receipt)),
                          'steps': {k: {'rc': v['returncode'], 's': v['wall_seconds']} for k, v in receipt['steps'].items()}},
                         indent=2))
        return 0
    if a.command == 'report':
        r = report(repo, a.preview)
        print(json.dumps({k: r[k] for k in ('selected', 'exceptions', 'prepared')} | {'passing': len(r['checker_passing'])}))
        return 0


if __name__ == '__main__':
    sys.exit(main())
