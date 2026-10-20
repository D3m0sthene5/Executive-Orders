"""Owner-seeded Valla rework hypothesis. No suspicious-claim count is a saving."""
import argparse
import hashlib
import json
from pathlib import Path
import time


def main():
    p = argparse.ArgumentParser(); p.add_argument('--data', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True); p.add_argument('--run-id', required=True)
    p.add_argument('--profiles'); a = p.parse_args(); start = time.monotonic()
    path = a.data / 'valla_rework_salvage.json'; data = json.loads(path.read_bytes())
    if data.get('origin') != 'owner_seeded' or data.get('saver_key') != 'valla_rework_salvage':
        raise ValueError('explicit owner-seeded hypothesis required')
    candidate = {'saver_key': 'valla_rework_salvage', 'origin': 'owner_seeded',
                 'title': 'Reuse explicitly reviewed unaffected preparation during corrections',
                 'targets': ['rework_preparation'], 'status': 'unverified', 'evidence': [],
                 'estimate': {'usd_per_session': None, 'basis': 'not estimated'},
                 'proposed_test': 'Matched correction tasks; count producer preparation, whole-case review, correction, coordination and integration in both arms. Keep failed attempts. Separate quality gains. Use measured session totals for Junto add-test.',
                 'measurement_status': data.get('measurement_status', 'pending'),
                 'limitations': 'Mechanical timing or matched-word counts cannot verify model-cost savings.'}
    a.out.write_text(json.dumps(candidate) + '\n')
    Path(str(a.out) + '.run.json').write_text(json.dumps({'data_digest': hashlib.sha256(path.read_bytes()).hexdigest(),
        'inputs': {'hypothesis': 'valla_rework_salvage', 'origin': 'owner_seeded'},
        'wall_seconds': time.monotonic() - start}))


if __name__ == '__main__':
    main()
