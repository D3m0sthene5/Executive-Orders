"""Review-only exact known-defect correlation; never imported by Geddes.

The signatures below encode the independent examiner's disclosed comparison
of flag meanings to historical defects. They are not production checks.
"""
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[5]
H=lambda b:hashlib.sha256(b).hexdigest()
def run(path):
 raw=path.read_bytes();d=json.loads(raw);m=json.loads((path.parent.parent/'inventory/MANIFEST.json').read_text());refs={r['instrument_id']:r for r in m['rows']};rows=[]
 specs={
 'EO:6275':('reasoning_order_identity_mismatch','6513I','Source-bound omitted I suffix is the exact recorded identity defect.'),
 'EO:6312':('reasoning_order_identity_mismatch','6885A','Source-bound omitted A suffix is the exact recorded identity defect.'),
 'EO:6578':('reasoning_order_identity_mismatch','6925A','Source-bound omitted A suffix matches one exact defect; no credit for separately resolving recital versus command semantics.'),
 'EO:9538':('fr_issue_date_mismatch','1945-04-17','Flag corrects mistaken publication issue, not signing or filing date.'),
 'EO:10138':('fr_citation_mismatch','4241','Flag identifies exact erroneous 4333 versus own page4241.'),
 'EO:10139':('fr_citation_mismatch','4241','Flag identifies exact erroneous 4333 versus own page4241.'),
 'EO:11314':('attributed_quote_not_verbatim','report on or before October 18th','Flag identifies exact report-date paraphrase presented as quotation.'),
 'EO:11329':('attributed_quote_not_verbatim','report on or before March 8','Flag identifies exact report-date paraphrase presented as quotation.'),
 'EO:11431':('attributed_quote_not_verbatim','report on or before October 2','Flag identifies exact report-date paraphrase presented as quotation.')}
 concepts={'EO:6875':{'approval_recommended','hearing_recital'},'EO:10285':{'status_quo'},'EO:10303':{'status_quo'},'EO:10314':{'non_derogation'},'EO:10319':{'non_derogation'},'EO:11013':{'standstill'},'EO:12095':{'standstill'}}
 actors={'EO:10634':{'EO:10773','EO:11051','EO:11725'},'EO:10915':{'EO:11963'},'EO:11026':{'EO:11029'},'EO:12398':{'EO:12429','EO:12447','EO:12455'},'EO:12429':{'EO:12447','EO:12455'}}
 for r in d['rejected']:
  iid=r['instrument_id'];assert r['prior_claim']==refs[iid]['prior_claim'];matches=[];note='No exact recorded defect matched; unrelated flags and coverage gaps receive no recall credit.'
  if iid in specs:
   code,needle,note=specs[iid];matches=[f for f in r['flags'] if f['code']==code and needle in f.get('detail','')]
  if iid in concepts:
   matches=[f for f in r['flags'] if f['code']=='attributed_stock_phrase_absent' and f.get('concept') in concepts[iid]]
   note='Flag names the same source-absent attributed concept as an exact historical defect. Other semantic defects in the case are not silently deemed caught.'
  if iid in actors:
   matches=[f for f in r['flags'] if f['code']=='later_instrument_named_without_event_source' and f.get('actor') in actors[iid]]
   note='Flag identifies a specifically recorded missing later-event actor. It does not itself approve date, mechanism, legal scope or the whole lifecycle.'
  if iid=='EO:6876':
   matches=[f for f in r['flags'] if f['code']=='literal_name_counterexample' and any(c.get('instrument_id')=='EO:6930' and c.get('date')=='1934-12-27' and c.get('text_sha256')=='2d237594f29e3a1063d931a395ffb01744dd0dfa73ec701dc87308689f7125d5' for c in f.get('counterexamples',[]))]
   note='Independent source reading in NAME_6876_SOURCE_CORRELATION.json confirms this exact EO6930 passage identifies the Cotton Textile Code after1934-10-16; unrelated recommendation flags receive no credit.'
  if not matches:note='No exact recorded defect matched; unrelated flags and coverage gaps receive no recall credit.'
  rows.append({'instrument_id':iid,'prior_claim':r['prior_claim'],'review_defects':r['review_defects'],'any_flag':bool(r['flags']),'exact_defect_caught':bool(matches),'matching_flags':matches,'note':note})
 assert len(rows)==40 and set(refs)=={r['instrument_id'] for r in rows}
 return {'schema':'geddes-independent-exact-defect-correlation/v1','evaluation_path':str(path.relative_to(ROOT)),'evaluation_sha256':H(raw),'module_sha256':d['module_sha256'],'known_versions':40,'with_any_flag':sum(r['any_flag'] for r in rows),'exact_defects_caught':sum(r['exact_defect_caught'] for r in rows),'original_filed_metric_total_flagged':d['filed_versions_with_flags'],'original_filed_metric_target_max':5,'scope':'Retrospective known development-set correlation only; not independent held-out science, whole-case approval, certified human review or new claim filing. New/unrecognized flag types need manual examination before credit.','rows':rows}
if __name__=='__main__':print(json.dumps(run(Path(sys.argv[1]).resolve()),indent=2))
