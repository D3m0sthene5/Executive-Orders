"""Verify this frozen source addendum and evaluate its existing lifecycle checkpoint.

Run from any directory; missing sparse Git objects may be supplied from the
same commit with --request-contract, --queue, --original-pdf, --later-pdf.
This read-only command writes no source, claim, review, queue or status records.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess, tempfile

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "jobs/claim-kit").is_dir())
REL = HERE.relative_to(ROOT).as_posix()
def sha(b): return hashlib.sha256(b).hexdigest()
def readjson(p): return json.loads(p.read_bytes())
def pins(rel): return dict(path=rel, sha256=sha((ROOT / rel).read_bytes()))
def module(file, name):
    spec = importlib.util.spec_from_file_location(name, file)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def main(args):
    source = readjson(HERE / 'SOURCE_EXAM.json')
    ref = source['repository_commit']
    def get(p, supplied=None):
        data = supplied.read_bytes() if supplied else subprocess.check_output(['git','show',ref+':'+p],cwd=ROOT)
        want = subprocess.check_output(['git','rev-parse',ref+':'+p],cwd=ROOT,text=True).strip()
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==want,p
        return data
    for row in source['held_sources']:
        b=get(row['path']); assert len(b)==row['bytes'] and sha(b)==row['sha256']
    for role,row in readjson(HERE/'RAW_ORIGINAL_PINS.json').items():
        b=get(row['path'],args.original_pdf if role=='original' else args.later_pdf)
        assert len(b)==row['bytes'] and sha(b)==row['sha256']
    for w in readjson(HERE/'HELD_WITNESSES.json')['witnesses']:
        b=get(w['path']); assert sha(b)==w['text_sha256'] and b.decode()[w['char_start']:w['char_end']]==w['quote'],w['id']
    candidate=readjson(HERE/'CANDIDATE_V2.json')
    for k in [*candidate['dependencies'],candidate['previous_candidate'],candidate['revision_origin']]:
        assert sha((ROOT/k['path']).read_bytes())==k['sha256'],k['path']
    t=candidate['target']; b=get(t['path']); assert sha(b)==t['file_sha256']
    gate=module(ROOT/'research/stage19/code/claim_gate.py','sol_gate')
    assert gate.claim_sha(json.loads(b.splitlines()[t['line']-1]))==t['claim_sha256']
    qc=readjson(HERE/'QUEUE_COMPARISON.json'); q=get(qc['path'],args.queue)
    assert sha(q)==qc['file_sha256']
    rows=list(map(json.loads,q.splitlines()))
    proposals=list(map(json.loads,(HERE/'FETCH_PROPOSALS_V2.jsonl').read_bytes().splitlines()))
    for proposal in proposals:
        assert not any(set(proposal['urls']).intersection(x.get('urls') or []) for x in rows)
    contract_path='jobs/source-ladder/request_contract.py'
    contract=get(contract_path,args.request_contract)
    with tempfile.TemporaryDirectory() as tmp:
        f=Path(tmp)/'request_contract.py'; f.write_bytes(contract); request_contract=module(f,'sol_request_contract')
        normalized=[request_contract.normalize_request(x,line_number=n,source=REL+'/FETCH_PROPOSALS_V2.jsonl') for n,x in enumerate(proposals,1)]
    assert all(not r['errors'] and len(r['tasks'])==1 and r['tasks'][0]['status']=='valid' for r in normalized)
    lifecycle_path='jobs/claim-kit/lifecycle_obligations.py'
    lifecycle=module(ROOT/lifecycle_path,'sol_lifecycle')
    packet_path='research/progress/maitland/valla-audit/correction-packet-v1/PACKET.json'
    packet=json.loads(get(packet_path)); dossier_path='jobs/claim-kit/output/dossiers/EO_13792.json'
    d=json.loads(get(dossier_path)); assert d['fingerprint']==packet['dossiers']['EO:13792']['fingerprint']
    prior={'frozen_packet_prior_research':packet['prior_research'],'current_evidence_addendum':pins(REL+'/CANDIDATE_V2.json')}
    route=lifecycle.digest({contract_path:sha(contract),lifecycle_path:sha((ROOT/lifecycle_path).read_bytes())})
    held=[dict(path=x['path'],sha256=x['sha256'],status='verified_prior_held_bytes') for x in source['held_sources']]
    cp_path=HERE/'CHECKPOINT.json'
    requests=[r['tasks'][0] for r in normalized]
    reason='Factual submission evidence advances both report questions; exact version, routing, receipt and legal exhaustion remain unresolved. Later public congressional evidence is not a native acquisition.'
    result=[REL+'/CANDIDATE_V2.json',REL+'/HELD_WITNESSES.json',REL+'/FETCH_PROPOSALS_V2.jsonl']
    cp=lifecycle.blocked_checkpoint(d,requests,route,reason,result,held,prior)
    if args.emit_checkpoint: print(json.dumps(cp,ensure_ascii=False,indent=2)); return
    frozen=readjson(cp_path)
    decision=lifecycle.resume_decision(frozen,d,requests,route,held,prior)
    if args.source_results:
        extra=json.loads(args.source_results.read_bytes())
        if not isinstance(extra,list) or not all(isinstance(x,dict) for x in extra):raise ValueError('expected array of actual acquisition receipts')
        decision=lifecycle.resume_decision(frozen,d,requests,route,held+extra,prior)
    print(json.dumps(dict(verified_held_sources=len(held),verified_raw_order_pdfs=2,verified_exact_spans=9,
        validated_requests=len(requests),queue_rows=len(rows),checkpoint_matches_current=(cp==frozen),
        native_resume=decision,casework_closure='research only'),ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ('request-contract','queue','original-pdf','later-pdf','source-results'):p.add_argument('--'+flag,type=Path)
    p.add_argument('--emit-checkpoint',action='store_true',help='Print only the native checkpoint to stdout')
    main(p.parse_args())
