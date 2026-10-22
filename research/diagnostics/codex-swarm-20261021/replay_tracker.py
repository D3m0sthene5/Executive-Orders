import argparse,importlib.util,json,sys
from pathlib import Path
ap=argparse.ArgumentParser(description="Replay tracker with the exact two independently reviewed claim checks.")
ap.add_argument('--repo',type=Path,default=Path.cwd())
ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args()
root=a.repo.resolve()
out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
evidence=root/'research/diagnostics/codex-swarm-20261021' 
spec=importlib.util.spec_from_file_location('swarm_tracker',root/'jobs/readiness-tracker/tracker.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=json.loads((root/'jobs/claim-checker/output/PER_CLAIM.json').read_text())
new=json.loads((evidence/'final-claim-checker/PER_CLAIM.json').read_text())
old['by_instrument'].update(new['by_instrument'])
merged=out/'MERGED_CHECKER.json';merged.write_text(json.dumps(old))
m.J['checker']=str(merged)
orders,problems=m.build(str(root));summary=m.summarise(orders,problems)
(out/'TRACKER_AFTER_CLAIMS.json').write_text(json.dumps(summary,indent=2)+'\n')
before=json.loads((evidence/'TRACKER_BEFORE_CLAIMS.json').read_text())
result={'method':'tracker.build on unchanged prior outputs, merging exactly two current-hash mechanical checks into a scratch checker map; no canonical job output overwritten','before_ready':before['ready_for_human_review'],'after_ready':summary['ready_for_human_review'],'new_mechanically_checked_claims':list(new['by_instrument']),'input_problems':problems}
(out/'TRACKER_REPLAY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
