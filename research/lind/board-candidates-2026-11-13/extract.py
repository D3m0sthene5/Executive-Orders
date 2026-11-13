"""Board cohort: extract and classify inputs for candidate ending corrections (isolated candidates, never claims).

Zero model tokens. For every order with a stored NMB report (jobs/eumenes-nmb-reports/output/SOURCES.jsonl) it records:
- the report's board number and Pergamon locator;
- the dates the held text extract shows: the transmittal-letter date and the cover date, each OBSERVED, DAMAGED
  (month and year readable, day not) or ABSENT, with character offsets;
- the public NMB inventory row (created, closed, comment, extra links), kept as an independent value, never a substitute;
- order-side inputs from the order's current effective claim: kind (creates a board / follow-on order), the exact
  "no change ... thirty days after ... report" sentence if any, the clause count;
- flags for every demonstrated exception, and a candidate standstill end ONLY when the transmittal date is OBSERVED,
  marked INFERRED_UNDER_RULE (D-20261108-board-rule), with both counting readings.

Usage: python3 -I research/lind/board-candidates-2026-11-13/extract.py
"""
import csv
import datetime as dt
import glob
import html
import json
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october',
          'november', 'december']
MON = r'(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?'
YEAR = r'(1[\.\s]?9[\.\s]?\d[\.\s]?\d|2[\.\s]?0[\.\s]?\d[\.\s]?\d)'
DATE = re.compile(r'\b' + MON + r'\s{0,3}(\d{1,2})\s{0,2}[,.]?\s{0,3}' + YEAR, re.I)
DAMAGED = re.compile(r'\b' + MON + r'\s{0,3}([^\s\d,]{1,4}\d?|\d[^\s\d,]{1,3})\s{0,2}[,.]?\s{0,3}' + YEAR, re.I)
TRANSMITTAL = re.compile(r'L\s*E\s*T\s*T\s*E\s*R\s+O\s*F\s+T\s*R\s*A\s*N\s*S\s*M\s*I\s*T\s*T\s*A\s*L', re.I)
SALUTATION = re.compile(r'(?i)(The\s+President\s*,?\s*The\s+White\s+House|Dear\s+Mr\.?\s+President|Mr\.?\s+President\s*:)')
SUBMIT = re.compile(r'(?i)(submits?|transmits?)\s+(herewith|its report|the report)|honou?r\s+to\s+submit')
NOCHANGE = re.compile(r'(?is)[^.]*(?:no\s+change[^.]{0,300}?(?:thirty|30)\s+days\s+after[^.]{0,200}?report|(?:thirty|30)\s+days\s+after[^.]{0,200}?report[^.]{0,300}?no\s+change)[^.]*\.')


def parse_date(m):
    mon = m.group(1).lower()[:3]
    month = [x[:3] for x in MONTHS].index('sep' if mon == 'sep' else mon) + 1
    year = int(re.sub(r'[\.\s]', '', m.group(3)))
    return dt.date(year, month, int(m.group(2)))


def first_date(text, start, end, anchor=None, closed=None):
    """First date in text[start:end] strictly after the order's signing date (anchor) and within three years of it.
    A date whose month and day equal the NMB closed date but whose year differs is DAMAGED (OCR year), not observed.
    A month-and-year reading with an unreadable day is DAMAGED."""
    window = text[start:end]
    for m in DATE.finditer(window):
        try:
            d = parse_date(m)
        except ValueError:
            continue
        if anchor and d <= anchor:
            continue                      # the board's creation date or earlier, not the report date
        if anchor and d > anchor + dt.timedelta(days=3 * 366):
            if closed and (d.month, d.day) == (closed.month, closed.day):
                return 'DAMAGED', None, start + m.start(), m.group(0) + ' (year unreadable: OCR year differs)'
            continue
        return 'OBSERVED', d.isoformat(), start + m.start(), m.group(0)
    dmg = DAMAGED.search(window)
    if dmg:
        return 'DAMAGED', None, start + dmg.start(), dmg.group(0)
    return 'ABSENT', None, None, ''


ADDRESS = re.compile(r'(?i)(T\s*h\s*e\s+P\s*r\s*e\s*s\s*i\s*d\s*e\s*n\s*t|Mr\.?\s+President|Dear\s+Mr)')
COVER_NO = re.compile(r'\(\s*No\.\s*\d+\s*\)')


def dateline(text, start, end, anchor, closed):
    """The letter's date line: the first date between the heading and the address to the President.
    OCR digits misread as letters (i, l, I, O, o) are corrected only when the corrected date equals the NMB closed
    date (an independent check); otherwise the reading stays DAMAGED."""
    a = ADDRESS.search(text, start, end)
    stop = a.start() if a else min(end, start + 300)
    seg = text[start:stop]
    m = DATE.search(seg)
    if m:
        try:
            d = parse_date(m)
            if not anchor or anchor < d <= anchor + dt.timedelta(days=3 * 366):
                return 'OBSERVED_DATELINE', d.isoformat(), start + m.start(), m.group(0)
        except ValueError:
            pass
    fixed = re.sub(r'(?<=[\dA-Za-z])[iIl|](?=[\d,])|(?<=\d)[iIl|]|[iIl|](?=\d)', '1', seg)
    fixed = re.sub(r'(?<=\d)[Oo]|[Oo](?=\d)', '0', fixed)
    m2 = DATE.search(fixed)
    if m2:
        try:
            d = parse_date(m2)
            if closed and d == closed:
                return 'OBSERVED_DATELINE_OCR_CORRECTED', d.isoformat(), start + m2.start(), seg[m2.start():m2.end()]
        except ValueError:
            pass
    dmg = DAMAGED.search(seg)
    if dmg or re.search(MON, seg, re.I):
        return 'DAMAGED', None, start, seg.strip()[:80]
    return None


def cover_report_date(text, anchor):
    """The date printed just above '(No. NN)' on the report cover."""
    m = COVER_NO.search(text[:6000])
    if not m:
        return None
    dates = list(DATE.finditer(text[max(0, m.start() - 160):m.start()]))
    if not dates:
        return None
    try:
        d = parse_date(dates[-1])
    except ValueError:
        return None
    if anchor and not (anchor < d <= anchor + dt.timedelta(days=3 * 366)):
        return None
    return d.isoformat()


def inventory():
    t = (HERE / 'nmb-inventory/list-of-presidential-emergency-board.html').read_text(encoding='utf-8', errors='replace')
    rows = {}
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S):
        cells = [re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', c))).strip()
                 for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', r, re.S)]
        if len(cells) >= 8 and cells[0].isdigit():
            links = [u.split('/')[-1] for u in re.findall(r'href="([^"]+)"', r)]
            rows[int(cells[0])] = {'carrier': cells[1], 'type': cells[2], 'created': cells[5], 'closed': cells[6],
                                   'comment': cells[7], 'links': links}
    return rows


def us_date(s):
    try:
        mo, d, y = (int(x) for x in s.split('/'))
        return dt.date(y, mo, d).isoformat()
    except (ValueError, AttributeError):
        return None


def main():
    reports = [json.loads(l) for l in open(REPO / 'jobs/eumenes-nmb-reports/output/SOURCES.jsonl', encoding='utf-8')]
    text_of = {}
    for l in open(REPO / 'jobs/source-ladder/output/SOURCES.jsonl', encoding='utf-8'):
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if r.get('sha256') and r.get('text_path'):
            text_of.setdefault(r['sha256'], r['text_path'])
    claims = {}
    for f in sorted(glob.glob(str(REPO / 'research/readiness/claims/*.jsonl')), key=os.path.getmtime):
        for l in open(f, encoding='utf-8'):
            try:
                c = json.loads(l)
            except ValueError:
                continue
            claims[c.get('instrument_id')] = (os.path.relpath(f, REPO), c)
    tracker = {r['instrument_id']: r for r in csv.DictReader(open(REPO / 'jobs/readiness-tracker/output/READINESS_BY_ORDER.csv', encoding='utf-8'))}
    inv = inventory()
    signed = {}
    for row in csv.DictReader(open(REPO / 'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv', encoding='utf-8')):
        try:
            signed[row['id']] = dt.date.fromisoformat(row['date_effective'][:10])
        except (ValueError, KeyError):
            pass
    shared = {}
    for r in reports:
        for i in r['instrument_ids']:
            shared[i] = [x for x in r['instrument_ids'] if x != i]
    out = []
    for r in reports:
        peb = re.search(r'PEB-(\d+)', r['page_or_item'])
        peb = int(peb.group(1)) if peb else None
        tp = text_of.get(r['sha256'])
        tpath = REPO / 'jobs/source-ladder/output' / tp if tp else None
        text = tpath.read_text(encoding='utf-8', errors='replace') if tpath and tpath.exists() else ''
        tp = str(tpath.relative_to(REPO)) if text else tp
        tm = TRANSMITTAL.search(text)
        row_inv0 = inv.get(peb) or {}
        closed0 = us_date(row_inv0.get('closed', ''))
        closed0 = dt.date.fromisoformat(closed0) if closed0 else None
        anchor = min((signed[i] for i in r['instrument_ids'] if i in signed), default=None)
        created0 = us_date(row_inv0.get('created', ''))
        if anchor is None and created0:
            anchor = dt.date.fromisoformat(created0)   # NMB 'created' = the creating order's date; an anchor only
        if tm:
            dl = dateline(text, tm.end(), tm.end() + 2500, anchor, closed0)
            if dl and dl[0] != 'DAMAGED':
                t_kind, t_date, t_off, t_raw = dl
            else:
                t_kind, t_date, t_off, t_raw = first_date(text, tm.end(), tm.end() + 2500, anchor, closed0)
                if t_kind == 'OBSERVED':
                    t_kind = 'OBSERVED_BODY_ONLY'   # weaker: a date in the letter body, not its date line
                elif dl:
                    t_kind, t_date, t_off, t_raw = dl
            c_kind, c_date, c_off, c_raw = first_date(text, 0, tm.start(), anchor, closed0)
        else:
            sal = SALUTATION.search(text)
            if sal:
                # A letter to the President without the heading: the date line sits just before or after it.
                k, t_date, t_off, t_raw = first_date(text, max(0, sal.start() - 400), sal.end() + 2500, anchor, closed0)
                t_kind = {'OBSERVED': 'OBSERVED_NO_HEADING'}.get(k, k)
            else:
                t_kind, t_date, t_off, t_raw = 'NO_TRANSMITTAL_MARKER', None, None, ''
            c_kind, c_date, c_off, c_raw = first_date(text, 0, 3000, anchor, closed0)
        cover_rd = cover_report_date(text, anchor)
        submit = bool(SUBMIT.search(text[tm.end():tm.end() + 2500])) if tm else bool(SUBMIT.search(text[:6000]))
        row_inv = inv.get(peb) or {}
        for iid in r['instrument_ids']:
            cf, c = claims.get(iid, (None, None))
            cls = (c or {}).get('operative_clauses', [])
            otext = re.sub(r'\s+', ' ', ' '.join((x.get('original_operative_text') or '') for x in cls))
            nc = NOCHANGE.search(otext)
            low = otext.lower()
            creates = bool(re.search(r'board[^.]{0,80}(is hereby |are hereby )?(created|established)|hereby create|creat(e|ing) an emergency board|establish(ing)? an emergency board|there is (hereby )?(created|established)[^.]{0,40}board', low))
            followon = bool(shared.get(iid)) and not creates
            flags = []
            if not text:
                flags.append('no_held_report_text')
            if t_kind not in ('OBSERVED_DATELINE', 'OBSERVED_DATELINE_OCR_CORRECTED'):
                flags.append('transmittal_date_' + t_kind.lower())  # OBSERVED_NO_HEADING is weaker than a headed letter
            if cover_rd and t_date and cover_rd != t_date:
                flags.append('cover_date_differs')
            if t_date and not submit:
                flags.append('no_submission_wording_after_transmittal')
            closed = us_date(row_inv.get('closed', ''))
            if not row_inv:
                flags.append('board_not_in_nmb_inventory')
            elif t_date and closed and closed != t_date:
                flags.append('nmb_closed_date_differs')
            comment = row_inv.get('comment', '')
            if re.search(r'(?i)supplement', comment):
                flags.append('nmb_supplement_published')
            if re.search(r'(?i)second peb|reconven', comment):
                flags.append('nmb_second_board_or_reconvened')
            if re.search(r'(?i)congression|public law|pl \d', comment):
                flags.append('nmb_congressional_action')
            if len(row_inv.get('links', [])) > 1:
                flags.append('nmb_extra_documents')
            if shared.get(iid):
                flags.append('report_shared_with:' + '+'.join(shared[iid]))
            if followon:
                flags.append('follow_on_order_not_board_creation')
            if not c:
                flags.append('no_current_claim')
            if len(cls) > 2:
                flags.append('more_than_two_clauses')
            if not nc and c:
                flags.append('no_thirty_day_sentence_in_claim_text')
            if (tracker.get(iid) or {}).get('ready_for_human_review') == 'yes':
                flags.append('already_ready')
            # Report date status: CORROBORATED only when a reading of the held report (letter date line, cover, or
            # a letter without heading) equals the independent NMB inventory 'closed' date. Image checks (CROSSCHECK.md)
            # found every single-reading disagreement to be an extraction or OCR error, so one reading is not enough.
            readings = {k: v for k, v in (('transmittal', t_date), ('cover', cover_rd)) if v}
            if closed and closed in readings.values():
                rd_status, rd = 'CORROBORATED', closed
            elif readings and not closed:
                rd_status, rd = 'SINGLE_SOURCE_NO_INVENTORY', None
            elif readings:
                rd_status, rd = 'CONFLICT_IMAGE_CHECK_NEEDED', None
            else:
                rd_status, rd = 'UNREAD_IMAGE_CHECK_NEEDED', None
            cand = {}
            if rd and creates:
                d = dt.date.fromisoformat(rd)
                cand = {'board_clause_end': {'date': rd, 'basis': 'report date CORROBORATED: held-report reading ' + str(sorted(k for k, v in readings.items() if v == rd)) + ' equals NMB inventory closed date; transmittal evidences submission, receipt by the President may be later',
                                             'transmittal_reading': {'kind': t_kind, 'offset': t_off, 'raw': t_raw}},
                        'standstill_end': None if not nc else {'basis': 'INFERRED_UNDER_RULE D-20261108-board-rule (end of the 30th day after the report date)',
                                           'inclusive_reading': (d + dt.timedelta(days=30)).isoformat(),
                                           'exclusive_reading': (d + dt.timedelta(days=29)).isoformat(),
                                           'sentence': nc.group(0)[:400]}}
            out.append({'instrument_id': iid, 'peb': peb, 'report_sha256': r['sha256'],
                        'pergamon_locator': (r.get('pergamon') or {}).get('locator'), 'nmb_url': r.get('url'),
                        'report_text_path': tp, 'transmittal': {'kind': t_kind, 'date': t_date, 'offset': t_off, 'raw': t_raw},
                        'cover': {'kind': c_kind, 'date': c_date, 'offset': c_off, 'raw': c_raw}, 'cover_report_date': cover_rd,
                        'submission_wording': submit, 'nmb_inventory': row_inv, 'claim_file': cf,
                        'clauses': len(cls), 'creates_board': creates, 'tracker_blockers': (tracker.get(iid) or {}).get('blockers'),
                        'report_date_status': rd_status, 'flags': flags, 'candidate': cand})
    out.sort(key=lambda x: int(x['instrument_id'][3:]))
    (HERE / 'CANDIDATES.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    with open(HERE / 'CANDIDATES.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['instrument_id', 'peb', 'report_date_status', 'transmittal_kind', 'transmittal_date', 'cover_kind', 'cover_date', 'nmb_closed',
                    'nmb_comment', 'creates_board', 'clauses', 'candidate_board_end', 'candidate_standstill_end_inclusive', 'flags'])
        for x in out:
            w.writerow([x['instrument_id'], x['peb'], x['report_date_status'], x['transmittal']['kind'], x['transmittal']['date'], x['cover']['kind'],
                        x['cover']['date'], x['nmb_inventory'].get('closed'), x['nmb_inventory'].get('comment'), x['creates_board'],
                        x['clauses'], (x['candidate'].get('board_clause_end') or {}).get('date'),
                        ((x['candidate'].get('standstill_end') or {}) or {}).get('inclusive_reading'), ';'.join(x['flags'])])
    print(len(out), 'orders written')


if __name__ == '__main__':
    main()
