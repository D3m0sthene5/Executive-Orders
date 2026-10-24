"""Reconcile actual published checker/tracker outputs with the frozen exact cohort."""
import argparse,csv,hashlib,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path('.'));p.add_argument('--output',type=Path,required=True);p.add_argument('--write',type=Path,required=True);p.add_argument('--optional-media',action='store_true');a=p.parse_args();root=a.repo.resolve();out=a.output.resolve();here=Path(__file__).parent
 selected=json.loads((here/'SELECTED.json').read_text());base=root/'jobs/leverage-campaign-check/output';old=json.loads((base/'claim-checker/PER_CLAIM.json').read_text())['by_instrument'];new=json.loads((out/'claim-checker/PER_CLAIM.json').read_text())['by_instrument']
 def csvmap(path):return {r['instrument_id']:r for r in csv.DictReader(path.open())}
 before=csvmap(base/'readiness-tracker/READINESS_BY_ORDER.csv');after=csvmap(out/'readiness-tracker/READINESS_BY_ORDER.csv')
 cohort=[]
 for iid in selected['orders']:
  c=new[iid];assert c['claim_key']==old[iid]['claim_key'] and c['claim_sha256']==old[iid]['claim_sha256'],iid
  assert c['mechanical_result']=='pass',(iid,c['mechanical_result'])
  r=after[iid];cohort.append(dict(instrument_id=iid,claim_key=c['claim_key'],claim_sha256=c['claim_sha256'],mechanical=c['mechanical_result'],all_checks_passed=c['all_checks_passed'],before_ready=before[iid]['ready_for_human_review'],after_ready=r['ready_for_human_review'],ready_tier=r['ready_tier'],blockers=r['blockers'],steps={k:v for k,v in r.items() if k.startswith('step_')}))
 ready=lambda d:{i for i,r in d.items() if r['ready_for_human_review']=='yes'}
 restored=ready(after)-ready(before);lost=ready(before)-ready(after)
 assert not lost,sorted(lost)
 optional=set(json.loads((here/'OPTIONAL_MEDIA_COHORT.json').read_text())['eligible_orders']) if a.optional_media else set()
 assert restored==set(selected['prior_ready'])|optional,(sorted(restored),selected['prior_ready'])
 if optional:
  actual_optional={i for i,r in after.items() if r.get('opus_media_applicability_note')}
  assert actual_optional==optional,(actual_optional,optional)
  assert all(after[i]['step_opus_media']=='n/a' and after[i]['ready_for_human_review']=='yes' for i in optional)
 holds=['EO:13101','EO:13148','EO:13783','EO:13792','EO:13807','EO:9789'];assert all(after[i]['ready_for_human_review']=='no' for i in holds)
 summary=json.loads((out/'readiness-tracker/SUMMARY.json').read_text())
 result=dict(input_commit=json.loads((out/'VALIDATION.json').read_text())['input_commit'],cohort=cohort,selected=len(cohort),mechanically_passed=len(cohort),all_checks_passed=sum(c['all_checks_passed'] for c in cohort),before_ready=len(ready(before)),after_ready=len(ready(after)),restored=selected['prior_ready'],newly_ready_from_empty_matching_set=sorted(optional),newly_researched_histories=0,lost_ready=[],holds_preserved=holds,outside_previous_verification_gap=selected['prior_ready_outside'],remaining_selected=[c for c in cohort if c['after_ready']!='yes'],tracker_summary=summary,limits=['Unchanged claim versions and existing reviews; byte restoration is not a new legal conclusion.','No human certification or whole-campaign efficiency claim.'])
 a.write.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('cohort','tracker_summary','remaining_selected')}));print('Remaining selected:',[(c['instrument_id'],c['blockers']) for c in result['remaining_selected']])
if __name__=='__main__':main()
