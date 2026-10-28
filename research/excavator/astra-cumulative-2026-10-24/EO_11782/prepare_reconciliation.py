"""Reconcile the specifically selected historical claim; no automatic adoption."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
OLD = ROOT / 'research/readiness/reviews/astra-2026-10-18'
selected = OLD / 'producer/EO_11782/v4/claim.json'
claim = json.loads(selected.read_text())
text_path = 'jobs/fr-originals/data/full_run/texts/EO_12212.txt'
text = (ROOT / text_path).read_text()
start = text.index('1-101.')
end = text.index('1-102.')
effective = {
    'url': 'https://www.govinfo.gov/content/pkg/FR-1980-05-05/pdf/FR-1980-05-05.pdf',
    'sha256': 'c5e3e5df15eaac449cc25acd03a1988903fb13937ed5a77a3710a668f16fb9b0',
    'page_or_item': '45 FR 29557, PDF page 11, complete EO 12212; section 1-101',
    'text_path': text_path,
    'text_sha256': hashlib.sha256((ROOT / text_path).read_bytes()).hexdigest(),
    'quoted_parts': [text[start:end].rstrip()],
    'read_method': 'Complete held official extract read on 2026-10-24; historical source review separately attributed in RECONCILIATION.md. Official printing, not signed original.',
}
membership = next(c for c in claim['operative_clauses'] if c['scope_id'].endswith('sec1-membership'))
event = next(e for e in membership['later_events'] if e['effective_date'] == '1980-05-04')
event['supporting_sources'] = [{'source': effective}]
membership['later_events'].sort(key=lambda e: e['effective_date'])
claim['research_rationale'] = claim['research_rationale'].replace(
    'This is a proposed producer finding awaiting independent review and mechanical custody verification; not human certification.',
    'Reconciled from the Astra October 18 selected v4 proposal and its version-specific independent AI review, with the PR56 corrected-v3 complete three-section inventory. The five operative units preserve all three sections; establishment and membership, and advice and coordination, are separately tracked. The October 18 search and its corrected ladder coverage are reused with their recorded limits, not represented as a new search. PR56 acquisition aliases for the revoker are not earlier events. On October 24 the previously reviewed EO12212 section1-101 is attached as an explicit supporting citation to the membership event; no new legal event or changed cutoff is inferred. Historical read-method statements remain attributed to the original producer/reviewer, not asserted as new reads. This reconciled proposal requires current whole-case independent AI review and mechanical evidence verification; it is not human certification.')
claim['later_source_search'].append({
    'repository': 'PR56 frozen preparation packet and corrected-v3 source-reviewed partial',
    'checked_on': '2026-10-24',
    'query_or_scope': 'Reconciled current EO11782 gaps, complete original inventory and chain with the selected October18 v4 claim and reviews. The three spurious earlier actor labels share EO12379 raw bytes and are acquisition aliases, as PR56 independently reviewed; no new earlier instrument follows from those wrappers. The earlier numeric/current-law/named-body search scope is reused as recorded, including USC currency through October9 and bounded held-text coverage. This is an artifact reconciliation, not a newly executed corpus search.',
})
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'claim-v5.json').write_text(json.dumps(claim, indent=2, ensure_ascii=False)+'\n')
(OUT / 'PROPOSED_CLAIMS.jsonl').write_text(json.dumps(claim, ensure_ascii=False)+'\n')
pins = []
for path in [selected, OLD/'BATCH1_SELECTION.json', OLD/'CHECKPOINT_BATCH1_AUDIT.json', OLD/'reviewer/EO_11782/v3/REVIEW.json', OLD/'reviewer/EO_11782/v3/SOURCE_AUDIT.json', OLD/'reviewer/EO_11782/v4/REVIEW.json', OLD/'producer/EO_11782/v2/NAMED_SEARCH.json', OLD/'producer/EO_11782/v4/LADDER_SEARCH.json', ROOT/'research/excavator/astra-source-first-2026-10-23/CLAIMS.partial.corrected-v3.jsonl', ROOT/'research/excavator/astra-source-first-2026-10-23/review/after-reveal-v3/REVIEW.json']:
    pins.append({'path':str(path.relative_to(ROOT)), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(OUT/'INPUT_PINS.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps({'candidate':str((OUT/'claim-v5.json').relative_to(ROOT)), 'file_sha256':hashlib.sha256((OUT/'claim-v5.json').read_bytes()).hexdigest(), 'source_count':len(pins)}))
