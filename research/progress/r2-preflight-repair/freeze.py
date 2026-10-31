"""Freeze a purposive diagnostic cohort before changing preflight; no filing."""
import datetime, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'jobs/claim-kit'))
import excavate

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    if (HERE/'FREEZE.json').exists():
        raise SystemExit('Frozen selection already exists; preserve it and record any representation erratum separately.')
    cases = []
    for n, strata in [('7952', 'valid unnumbered paragraphs; contingent effective date'),
                      ('8083', 'historical opening-command regression; native dossier'),
                      ('8123', 'neighboring instruments; native dossier'),
                      ('8220', 'footnote belonging to neighboring EO8219'),
                      ('8729', 'ambiguous interleaved contents and page break'),
                      ('8930', 'recitals and printed convention material'),
                      ('13613', 'modern numbered order; native dossier')]:
        iid = 'EO:' + n
        path = ROOT / ('jobs/fr-originals/data/full_run/texts/EO_' + n + '.txt')
        text = path.read_text()
        raw_sha = re.search(r'SHA-256 of the downloaded file: ([a-f0-9]{64})', text)[1]
        raw = ROOT / ('jobs/astra-source-retention/output/pdf/' + raw_sha + '.pdf')
        if not raw.exists() and n == '13613':
            raw = ROOT / 'research/stage21/original_sources/EO_13613.pdf'
        assert sha(raw) == raw_sha
        location = re.search(r'Location: ([^\n]+)', text)[1]
        source = {'text_path': str(path.relative_to(ROOT)), 'text_sha256': sha(path),
                  'sha256': raw_sha, 'url': re.search(r'Source: ([^\n]+)', text)[1],
                  'page_or_item': location}
        native = ROOT / ('jobs/claim-kit/output/dossiers/EO_' + n + '.json')
        if native.exists():
            d = json.loads(native.read_text())
            assert d['evidence'][d['original_source_id']]['source']['text_sha256'] == source['text_sha256']
            kind = 'current committed native dossier original/inventory projection'
            clauses = d['clauses']
            inventory_pin = {'path': str(native.relative_to(ROOT)), 'sha256': sha(native)}
        else:
            clauses = excavate.segment(iid, text, source)['clauses']
            kind = 'current excavate.segment lead on held FR text; no native dossier exists'
            inventory_pin = {'code_path': 'jobs/claim-kit/excavate.py', 'sha256': sha(ROOT/'jobs/claim-kit/excavate.py')}
        original_id = 'ORIGINAL:' + iid
        d = {'instrument_id': iid, 'original_source_id': original_id, 'actor_provisions': [],
             'evidence': {original_id: {'text': text, 'char_start': 0, 'char_end': len(text), 'source': source}},
             'clauses': clauses}
        dest = HERE/'frozen'/('EO_'+n+'.json')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(d, indent=2, ensure_ascii=False)+'\n')
        pages = re.search(r'PDF pages (\d+)-(\d+)', location)
        cases.append({'instrument_id': iid, 'strata': strata, 'inventory_kind': kind,
                      'inventory_pin': inventory_pin, 'frozen_dossier': str(dest.relative_to(ROOT)),
                      'frozen_sha256': sha(dest), 'text_path': source['text_path'],
                      'text_sha256': source['text_sha256'], 'raw_pdf': str(raw.relative_to(ROOT)),
                      'source_sha256': raw_sha, 'pdf_pages': list(range(int(pages[1]), int(pages[2])+1))})
    manifest = {'base': '88cef0253ed735b2a6e612770f25f9148641ce93',
                'frozen_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'selection': 'Purposive edge-case cohort fixed before implementation; no prevalence estimate.',
                'cases': cases}
    (HERE/'FREEZE.json').write_text(json.dumps(manifest, indent=2)+'\n')
    cards = [{k:c[k] for k in ('instrument_id','raw_pdf','source_sha256','pdf_pages')} for c in cases]
    (HERE/'SOURCE_CARDS.json').write_text(json.dumps(cards, indent=2)+'\n')
    print('Frozen',len(cases),'cases; no canonical records modified.')

if __name__ == '__main__':
    main()
