"""B1 (owner ruling R9): admit held-official-page numbered ids to the census; fill dates.
Run: python3 -I research/dorotheus/scripts/b1_admit.py <denominator_inputs_dir> <main_checkout>
Inputs dir holds e2/ADMIT_LIST.csv copied from origin/claude/justinian-denominator."""
import csv, hashlib, re, sys, os
inp, main = sys.argv[1], sys.argv[2]
CEN = 'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv'
CLASS = 'admitted_numbered_2026_11_06'
LFS = 'releases/source_books/OFR_1974_Hoover_Proclamations_and_Executive_Orders_v2_uc1.c025504761.pdf'
def sha_of(path):
    # the held PDF is a git-LFS pointer in checkouts; the pointer's oid is the sha256 of the real bytes
    b = open(os.path.join(main, path), 'rb').read()
    m = re.search(rb'oid sha256:([0-9a-f]{64})', b)
    return m.group(1).decode() if b.startswith(b'version https://git-lfs') and m else hashlib.sha256(b).hexdigest()
def group(d):
    y = int(d[:4])
    return '1862–1906' if y <= 1906 else '1907–1936' if y <= 1936 else '1937–1989' if y <= 1989 else '1990–2026'
rows = list(csv.DictReader(open(CEN, encoding='utf-8', newline='')))
fields = list(rows[0].keys()); ids = {r['id'] for r in rows}
H = {r['instrument_id']: r for r in csv.DictReader(open(os.path.join(main, 'jobs/ofr-compilations/output/HOOVER_V2_ORDERS.csv')))}
adm = []; seen = set(); not_adm = []
for r in csv.DictReader(open(os.path.join(inp, 'e2/ADMIT_LIST.csv'))):
    i = 'EO:' + r['number'] + r['suffix']
    if r['already_in_census(yes/no)'].startswith('yes') or i in ids or i in seen: continue
    if r['group'] == 'c_lettered' or r['candidate_id'].startswith('ADM-c-') or not r['held_official_path'].startswith('releases/'):
        not_adm.append((i, r['held_official_page_or_locator'])); continue
    seen.add(i); adm.append((i, r))
out = []
for i, r in adm:
    h = H[i]; assert h['date'] == r['date'], i
    out.append(dict(id=i, number=r['number'], suffix=r['suffix'], date=r['date'], held_official_path=r['held_official_path'],
        held_official_page=r['held_official_page_or_locator'], held_official_sha256=sha_of(r['held_official_path']),
        text_path='jobs/ofr-compilations/output/' + h['text_path'], source_row='jobs/ofr-compilations/output/HOOVER_V2_ORDERS.csv:' + i))
# census append
for o in out:
    rows.append({**{k: '' for k in fields}, 'id': o['id'], 'bibliographic_class': CLASS, 'included_in_bibliography': '1',
        'deduplicated_document_proxy': '1', 'document_authentication': 'unadjudicated', 'presidential_signer_verification': 'unadjudicated',
        'signer_capacity': 'unadjudicated', 'presidential_delegation': 'unadjudicated', 'date_source_type': 'ofr_1974_hoover_compilation',
        'date_effective': o['date'], 'year_group': group(o['date']), 'substantive_status_inherited': 'indeterminate'})
# item 3: lowercase id
n7933 = 0
for r in rows:
    if r['id'] == 'EO:7933a': r['id'] = 'EO:7933A'; n7933 += 1
# item 4: date fills
fills = []
nara = {}
for r in csv.DictReader(open('research/stage13/CENSUS/NARA_UNNUMBERED_EDITORIAL_DATES_18.csv', encoding='utf-8-sig')):
    nara[r['instrument_id']] = r
for r in rows:
    if r['id'] in nara and r['year_group'] == 'Unknown date':
        n = nara[r['id']]; d = n['reference_date']
        fills.append((r['id'], r['date_effective'], r['year_group'], d)); r['date_effective'] = d; r['year_group'] = group(d); r['date_source_type'] = 'nara_codification_1989_source_row'
for i in ['EO:5857', 'EO:5860', 'EO:5865', 'EO:5866', 'EO:5869']:
    r = next(x for x in rows if x['id'] == i); assert r['date_effective'] == '' and r['year_group'] == 'Unknown date'
    d = H[i]['date']; fills.append((i, '', 'Unknown date', d)); r['date_effective'] = d; r['year_group'] = group(d)
    r['date_source_type'] = 'ofr_1974_hoover_compilation'
w = csv.DictWriter(open(CEN, 'w', encoding='utf-8', newline=''), fieldnames=fields, lineterminator='\n'); w.writeheader(); w.writerows(rows)
w = csv.DictWriter(open('research/stage15/CENSUS/ADMISSIONS_2026-11-06.csv', 'w', encoding='utf-8', newline=''), fieldnames=list(out[0]), lineterminator='\n'); w.writeheader(); w.writerows(out)
print(len(out), 'admitted;', n7933, 'renamed;', len(fills), 'fills;', len(rows), 'rows'); print(not_adm)
for f in fills: print(f)
