"""Bounded source-ladder request for two missing high-reuse acting instruments."""
import os, runpy, sys
from pathlib import Path
root=Path(os.environ['REPO_ROOT'])
sys.path.insert(0,str(root/'jobs/source-ladder'))
os.environ['JOB_ONLY']='queue:EO:12379:,queue:EO:11490:'
os.environ['JOB_MAX_REQUESTS']='120'
runpy.run_path(str(root/'jobs/source-ladder/job.py'),run_name='__main__')
