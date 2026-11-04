"""Independently rerun the submitted codec harness without changing its frozen receipt."""
import contextlib, hashlib, io, json, importlib.util
from pathlib import Path
from unittest.mock import patch
exp = Path(__file__).resolve().parents[1]/'experiment'
spec = importlib.util.spec_from_file_location('codec_worker', exp/'replay.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
lines=[]
def intercept(self, content):
    assert self == exp/'RESULTS.json'
    lines.append(content); return len(content)
with patch.object(Path,'write_text',intercept), contextlib.redirect_stdout(io.StringIO()):
    module.main()
assert len(lines) == 1
replay=json.loads(lines[0])
def normalize(obj):
    if isinstance(obj,list):return [normalize(x) for x in obj]
    if isinstance(obj,dict):return {k:normalize(v) for k,v in obj.items() if k not in ('encode_seconds','decode_seconds','started_epoch','ended_epoch')}
    return obj
actual=normalize(replay); expected=normalize(json.loads((exp/'RESULTS.json').read_text()))
assert actual == expected
assert all(actual['probes'].values())
print(json.dumps(dict(agreement_excluding_timings=True,rerun_sha256_excluding_timings=hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest(), eight_probes=actual['probes'], encoded_bytes=actual['pooled']['encoded_bytes'], decoded_bytes=actual['pooled']['literal_bytes'], cold_encoded_bytes_sum=sum(r['encoded_bytes'] for r in actual['per_order_cold']),cold_literal_bytes_sum=sum(r['literal_bytes'] for r in actual['per_order_cold']),independent_source_checks=False),indent=2,sort_keys=True))
