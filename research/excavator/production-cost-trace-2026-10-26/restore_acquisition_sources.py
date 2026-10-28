"""Restore execution-local PDF copies from the durable native primary store.

Sources are copied only after both exact hashes match; existing mismatches are
refused. This reconstructs custody paths, never research or a review verdict.
"""
from pathlib import Path
import hashlib,json,shutil
RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
count=0
for folder in ['acquisition-b1-8514','acquisition-b2-extra','acquisition-b2-july','acquisition-b2-april']:
    result=RUN/folder/'RESULTS.json'
    if not result.exists():continue
    for row in json.loads(result.read_bytes()):
        raw=row.get('sha256');rel=row.get('retained_pdf')
        if not raw or not rel:continue
        dest=(result.parent/rel).resolve();src=ROOT/'jobs/astra-source-retention/output/pdf'/(raw+'.pdf')
        if not dest.is_relative_to(ROOT):raise ValueError('unsafe execution path')
        if hashlib.sha256(src.read_bytes()).hexdigest()!=raw:raise ValueError('source hash mismatch')
        if dest.exists():
            if hashlib.sha256(dest.read_bytes()).hexdigest()!=raw:raise ValueError('refusing overwrite '+str(dest))
        else:dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
        count+=1
print(json.dumps({'exact_execution_pdf_copies_verified_or_restored':count}))
