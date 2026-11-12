"""Shard 3 of 5 of the Bodley web pass; the code is jobs/bodley-web-1/job.py (orders whose number mod 5 == 2)."""
import os, runpy
runpy.run_path(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bodley-web-1", "job.py"), run_name="__main__")
