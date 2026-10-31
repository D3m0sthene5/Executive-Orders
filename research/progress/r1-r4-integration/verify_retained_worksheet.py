"""Revalidate the original worksheet before replay can reconstruct anything."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[3]
base = root / 'research/progress/r3-ranger-roundtrip'
spec = importlib.util.spec_from_file_location('retained_r3_workbench', root / 'jobs/early-ranger-workbench/job.py')
workbench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workbench)
original = base / 'case-packets/UI_EXPORTED_WORKSHEET.v2.json'
old_receipt = json.loads((base / 'REPLAY_RECEIPT.json').read_bytes())
sha = hashlib.sha256(original.read_bytes()).hexdigest()
assert sha == old_receipt['UI_exported_worksheet_sha256'], 'Original worksheet was replaced'
custodies = [str((base / name).relative_to(root)) for name in (
    'research-polk/FACSIMILE_CUSTODY.json', 'independent-source-review/FACSIMILE_CUSTODY.json')]
cases = workbench.build_cases(root, 'jobs/early-ranger-workbench/output/EARLY_SOURCE_REVIEW_WORKBENCH.html', True, custodies)
records = workbench.rt.validate_worksheet(workbench.rt.read_worksheet(original), cases)
current = [r for r in records if r['validation'] == 'unchanged_source']
assert sorted(r['item_id'] for r in current) == old_receipt['selected_items'], records
result = {'original_worksheet_sha256': sha,
          'records': [{'item_id': r['item_id'], 'validation': r['validation']} for r in records],
          'scientific_approval': False, 'human_certification': False,
          'limit': 'Exact original bindings agree with current retained bytes. This verifies version identity only; historical embedded transcripts and partial worksheets retain their unverified representation labels.'}
Path(sys.argv[1]).write_text(json.dumps(result, indent=2) + '\n')
