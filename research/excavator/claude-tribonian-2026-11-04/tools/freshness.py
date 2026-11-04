"""Check that prepared Tribonian packets still pass claim-kit's freshness checks (coordinator tool, no judgment).

usage: python3 freshness.py BATCH [BATCH ...]   -> one line per batch: fresh, or the error claim-kit would raise.
"""
import sys
from pathlib import Path
REPO = Path('/home/claude/executive-orders')
sys.path.insert(0, str(REPO / 'jobs/claim-kit'))
import batch
for b in sys.argv[1:]:
    folder = REPO / f'research/excavator/claude-tribonian-2026-11-04/{b}/packet'
    try:
        batch.load_packet(folder, REPO, check_sources=True)
        print(b, 'fresh', flush=True)
    except Exception as e:
        print(b, 'STALE', str(e)[:200], flush=True)
