#!/usr/bin/env python3
"""Regenerate the complete Stage14 enabling research infrastructure offline.

Usage:
 python run_stage14_all.py --stage11-compact STAGE11.zip --stage11-full FULL_HANDOFF.zip \\
   --stage13-overlay STAGE13_OVERLAY.jsonl --importer GOVERNMENT_IMPORT.zip \\
   --blind-sample STAGE12_BLIND_60.csv --lord-pdf LORD.pdf --output STAGE14_FOLDER

SHA verification occurs in the individual module builds. No external network is
required and no accepted present-substantive-status classifications are changed.
"""
import argparse,pathlib,subprocess,sys,shutil
p=argparse.ArgumentParser();
for k in ['stage11-compact','stage11-full','stage13-overlay','importer','blind-sample','lord-pdf','lord-stage13-leads','output']:
 p.add_argument('--'+k,required=True)
a=p.parse_args();o=pathlib.Path(a.output);o.mkdir(exist_ok=True,parents=True);scripts=pathlib.Path(__file__).parent
(o/'SCRIPTS').mkdir(exist_ok=True)
for script in scripts.glob('*.py'):
    target=o/'SCRIPTS'/script.name
    if script.resolve()!=target.resolve():shutil.copy2(script,target)
for name in ('README_FIRST.md','PRIORITIZATION_CONTRACT.md'):
    origin=scripts.parent/name
    if origin.exists() and (scripts.parent/name).resolve()!=(o/name).resolve():shutil.copy2(origin,o/name)

def run(script,*args):
 print('RUN',script,flush=True);subprocess.run([sys.executable,str(scripts/script),*map(str,args)],check=True)
run('eo_leverage_engine.py','build','--stage11',a.stage11_compact,'--stage13',a.stage13_overlay,'--importer',a.importer,'--stage12-sample',a.blind_sample,'--output',o)
run('build_official_source_manifest.py',a.importer,o/'DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite',o/'QUEUES')
run('build_reusable_source_vault.py',a.stage11_full,o/'DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite',o/'QUEUES')
run('compile_dependency_actions.py',o)
run('rebuild_workpacks_from_vault.py',o)
run('build_lord_review_workbench.py',a.lord_pdf,a.lord_stage13_leads,o/'LORD')
run('reconcile_mass_repeal_schedule.py',a.stage11_full,o/'DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite',o/'REPORTS/EO12553_INDEPENDENT_SCHEDULE_CROSSWALK.json')
run('verify_stage14.py',o)
print('Stage14 offline recreation succeeded; no legal statuses promoted.')
