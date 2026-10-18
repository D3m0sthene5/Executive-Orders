"""Generate fail-closed family proof drafts from saved evidence; offline."""
import os
from pathlib import Path
from engine import run
from catalog import write_catalog
if __name__ == '__main__':
    run(Path(os.environ['REPO_ROOT']), Path(os.environ['OUTPUT_DIR']))
    write_catalog(Path(os.environ['REPO_ROOT']), Path(os.environ['OUTPUT_DIR']))
