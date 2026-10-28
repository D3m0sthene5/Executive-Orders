"""Offline NMB annual-report identity leads for the existing source queue.

An annual case narrative can connect an EO date to a board number even when
the board index's date denotes a later appointment. No date window is widened,
no source is fetched, and no factual or legal answer is approved here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time

from fetch_ladder import html_to_text
from report_dates import parse_dates, parse_peb_table, TEXT_DATE_RX, MONTHS
from request_contract import normalize_request

HEADER = re.compile(r"^Case[^\n]{0,120}?Emergency\s+Board\s+No\.\s*(\d{1,3}(?:-[A-Z])?)\b", re.I | re.M)
EO_DATE = re.compile(r"Executive\s+order.{0,90}?(?:dated|date\s+of)\s*(" + TEXT_DATE_RX.pattern + r")", re.I | re.S)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def norm(text):
    text = re.sub(r'(?<=\w)[\-\u00ad]\s*\n\s*(?=\w)', '', text)
    return ' '.join(re.findall(r'[a-z0-9]+', text.lower()))


def original_dates(text):
    # Search-only repair of literal spaced month letters ("M arch"). Quotes and
    # custody bytes are unchanged; no digit or year correction is attempted.
    for month in MONTHS:
        text = re.sub(r'\b' + r'\s*'.join(month) + r'(?=\s*\d)', month, text, flags=re.I)
    return parse_dates(text)


def held(repo, ref):
    p = Path(ref['path'])
    if p.is_absolute() or '..' in p.parts or not (repo / p).resolve().is_relative_to(repo):
        raise ValueError('unsafe input path')
    p = (repo / p).resolve()
    if p.stat().st_size > 5_000_000:
        raise ValueError('input exceeds five MB bound')
    raw = p.read_bytes()
    if sha(raw) != ref['sha256'] or raw.startswith(b'version https://git-lfs.github.com/spec/v1'):
        raise ValueError('unheld or changed input')
    return raw


def cases(text):
    headers = list(HEADER.finditer(text))
    for i, h in enumerate(headers):
        end = headers[i+1].start() if i+1 < len(headers) else len(text)
        if end-h.start() > 20_000:
            # Retain the omission; do not silently truncate the last narrative.
            yield {'board': h.group(1), 'hold': 'case exceeds bounded span', 'char_start': h.start(), 'char_end': end}
        else:
            yield {'board': h.group(1), 'char_start': h.start(), 'char_end': end, 'text': text[h.start():end]}


def propose(repo, plan):
    started = time.monotonic()
    repo = Path(repo).resolve()
    if plan.get('schema') != 'nmb-series-plan/v1' or not 1 <= len(plan['questions']) <= 12 or len(plan['sources']) > 4:
        raise ValueError('bounded NMB plan required')
    index = parse_peb_table(held(repo, plan['index']).decode('utf-8'))
    index_by_board = {}
    for row in index:
        index_by_board.setdefault(str(row['peb']), []).append(row)
    sources = []
    for s in plan['sources']:
        raw = held(repo, s['raw'])
        text = held(repo, s['text']).decode('utf-8')
        if html_to_text(raw.decode('utf-8')) != text:
            raise ValueError('text is not the unchanged ladder extraction')
        year = s['fiscal_year']
        if not re.search(r'fiscal\s+year\s+ended\s+June\s+30,?\s*' + str(year), text[:12000], re.I):
            raise ValueError('annual edition not established by title/front matter')
        sources.append((s, list(cases(text))))
    proposals, unresolved, omissions = [], [], []
    ids = [q['instrument_id'] for q in plan['questions']]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate question member')
    for s, records in sources:
        omissions += [dict(r, source=s['text']) for r in records if r.get('hold')]
    for q in plan['questions']:
        if not re.fullmatch(r'EO:\d{1,5}[A-Za-z]?', q['instrument_id']):
            raise ValueError('invalid instrument identity')
        original = held(repo, q['identity_source']).decode('utf-8')
        a, b = q['identity_span']
        if not (type(a) is int and type(b) is int and 0 <= a < b <= len(original)):
            raise ValueError('invalid identity span')
        headings = re.findall(r'^[ \t]*EXECUTIVE[ \t]+ORDER[ \t]+(?:NO\.?[ \t]*)?(\d{1,5}[A-Z]?)[ \t]*$', original[a:b], re.I | re.M)
        if not headings or set(x.upper() for x in headings) != {q['instrument_id'].split(':')[1].upper()}:
            raise ValueError('original heading does not bind exact instrument identity')
        aliases = q['identity_terms']
        if len(aliases) < 2 or any(not norm(x) or (' '+norm(x)+' ') not in (' '+norm(original[a:b])+' ') for x in aliases):
            raise ValueError('identity terms not grounded in original span')
        if q['order_date'] not in original_dates(original[a:b]):
            raise ValueError('order reference date not present in original span')
        matches = []
        for s, records in sources:
            for r in records:
                if r.get('hold') or not all((' '+norm(x)+' ') in (' '+norm(r['text'])+' ') for x in aliases):
                    continue
                references = [m for m in EO_DATE.finditer(r['text'][:1400])
                              if parse_dates(m.group(1)) == [q['order_date']]]
                if not references:
                    continue
                # The index supplies URLs, never the EO date or occurrence fact.
                rows = index_by_board.get(r['board'], [])
                if len(rows) != 1 or not rows[0]['pdfs']:
                    continue
                m = references[0]
                matches.append({'instrument_id':q['instrument_id'], 'board':r['board'],
                    'order_date':q['order_date'], 'index_date':rows[0]['created'],
                    'date_meaning':'EO-reference date and index date are separate unreviewed propositions',
                    'source':s, 'char_start':r['char_start'], 'char_end':r['char_end'], 'text':r['text'],
                    'eo_reference_span':[r['char_start']+m.start(),r['char_start']+m.end()],
                    'identity_source':q['identity_source'], 'identity_span':[a,b], 'identity_terms':aliases,
                    'urls':rows[0]['pdfs'], 'status':'unreviewed_identity_lead'})
        if len(matches) != 1:
            unresolved.append({'instrument_id':q['instrument_id'], 'matching_cases':len(matches),
                               'reason':'missing or ambiguous exact identity; no relaxed date/name fallback'})
        else:
            proposals.append(matches[0])
    queue = []
    for p in proposals:
        request = {'instrument_id':p['instrument_id'], 'urls':p['urls'], 'step':'shared_sources',
            'citation':'NMB PEB '+p['board']+' report; identity candidate from annual case narrative',
            'requested_by':plan['requested_by'],
            'note':'UNREVIEWED identity lead from '+p['source']['text']['path']+
                ' chars '+str(p['char_start'])+'-'+str(p['char_end'])+
                '; inspect report identity and date meanings. No delivery, exhaustion or legal effect inferred.'}
        if normalize_request(request)['errors']:
            raise ValueError('generated request violates existing contract')
        queue.append(request)
    return {'schema':'nmb-series-proposals/v1', 'proposals':proposals, 'unresolved':unresolved,
        'omitted_cases':omissions, 'fetch_queue_proposed':queue, 'machine_seconds':time.monotonic()-started,
        'legal_findings':False, 'factual_answers':0, 'network_requests':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    dest = (repo/args.out).resolve()
    if not dest.is_relative_to(repo/'research/excavator') or dest.exists():
        raise ValueError('new isolated research output required')
    manifest = (repo/args.manifest).resolve()
    if not manifest.is_relative_to(repo):
        raise ValueError('manifest must remain inside repository')
    result = propose(repo,json.loads(manifest.read_text()))
    dest.mkdir(parents=True)
    (dest/'RESULTS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (dest/'FETCH_QUEUE_PROPOSED.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in result['fetch_queue_proposed']))
    print(json.dumps({'proposals':len(result['proposals']),'unresolved':len(result['unresolved']),
                      'omitted_cases':len(result['omitted_cases']),'network_requests':0}))


if __name__ == '__main__':
    main()
