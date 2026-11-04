#!/usr/bin/env python3
"""Validate read-only counts against the bundled native tracker with Node.js."""
import csv
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
payload = {
    'rows': list(csv.DictReader((root / 'orders.csv').open(encoding='utf-8'))),
    'summary': json.loads((root / 'snapshot.json').read_text())['summary'],
}
script = r'''
const assert=require('node:assert/strict'),fs=require('node:fs');
const flow=require(process.argv[1]),{rows,summary}=JSON.parse(fs.readFileSync(0,'utf8'));
const f=flow.analyze(rows), assigned=Object.values(f.buckets).flat();
assert.equal(rows.length,summary.orders_total);
assert.equal(new Set(rows.map(r=>r.instrument_id)).size,rows.length);
assert.equal(assigned.length,rows.length);
assert.equal(new Set(assigned.map(r=>r.instrument_id)).size,rows.length);
assert.equal(f.ready,summary.ready_for_human_review);
for(const row of f.buckets.gates){assert.notEqual(row.ready_for_human_review,'yes');for(const [k,v] of Object.entries(row))if(k.startsWith('step_'))assert.ok(['done','provisional','n/a'].includes(v));}
const base={ready_for_human_review:'no',...Object.fromEntries(['original_text','clause_inventory','provisional_status','ending_or_current_basis','savings_residuals','counterevidence','shared_sources','opus_media'].map(k=>['step_'+k,'done']))};
assert.equal(flow.analyze([{...base,step_original_text:'provisional',step_opus_media:'n/a'}]).buckets.gates.length,1);
assert.equal(flow.analyze([{...base,step_original_text:'',step_clause_inventory:'open'}]).buckets.text.length,1);
assert.equal(flow.analyze([{...base,step_original_text:'open',ready_for_human_review:'yes'}]).buckets.ready.length,1);
assert.deepEqual(flow.blockers([{blockers:'OPEN_SOURCE_AUDIT:abc|OPEN_SOURCE_AUDIT:abc|CLAIM_CHECK_FAILED:x'}]),[['OPEN_SOURCE_AUDIT:abc',1],['CLAIM_CHECK_FAILED:x',1]]);
console.log(JSON.stringify({result:'passed',first:Object.fromEntries(Object.entries(f.buckets).map(([k,v])=>[k,v.length])),overlapping:Object.fromEntries(Object.entries(f.remaining).map(([k,v])=>[k,v.length]))},null,2));
'''
subprocess.run(['node', '-e', script, str(root / 'flow-core.js')], input=json.dumps(payload), text=True, check=True)
