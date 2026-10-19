"""Full exact-field QA and a paired repeated-source verification benchmark.

This measures deterministic I/O and source preparation, not model billing or
substantive legal review speed. It writes only the named research pilot folder.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
import time

from history import ROOT,show,validate_packet,canon,dump,compact


def source_stats(root,cache):
    keys=[k for k in cache if isinstance(k,tuple) and len(k)==2 and k[1] in ('pages','gzip')]
    return {'source_file_reads':len(keys),'source_bytes_read':sum((root/k[0]).stat().st_size for k in keys)}


def run(root,out):
    root=root.resolve();out=out.resolve()
    if not out.is_relative_to(root/'research/excavator'):raise ValueError('research output required')
    src=root/'jobs/status-history/output';index=json.loads((src/'INDEX.json').read_bytes())
    prespec=json.loads((out/'PRESPEC.json').read_bytes());sample=prespec['sample']
    records={};source_cache={};errors=[];sizes=[];starts=[];counts=Counter();started=time.monotonic()
    for row in index:
        if not row['history']:continue
        packet=show(src,row['instrument_id'],index,records)
        problems=validate_packet(root,packet,source_cache)
        errors.extend({'instrument_id':row['instrument_id'],'error':p} for p in problems)
        counts['histories_checked']+=1;counts['observation_references_checked']+=len(packet['observations'])+len(packet['supporting_observations'])
        counts['candidate_event_references_checked']+=len(packet['events'])
        sizes.append(len(canon(packet).encode()))
        startup=compact(packet);starts.append(len(canon(startup).encode()))
        counts['packets_with_disclosed_event_overflow']+=bool(startup['omitted_event_records'])
    qa={'schema':'eo-status-history-exact-source-QA/v1',**dict(counts),'errors':errors,
        'wall_seconds':round(time.monotonic()-started,4),**source_stats(root,source_cache),
        'packet_utf8_bytes':{'median':statistics.median(sizes),'p90':sorted(sizes)[int(.9*(len(sizes)-1))],'maximum':max(sizes)},
        'compact_startup_utf8_bytes':{'median':statistics.median(starts),'p90':sorted(starts)[int(.9*(len(starts)-1))],'maximum':max(starts),'sum':sum(starts),'cap':18000},
        'full_packet_utf8_bytes_sum':sum(sizes),
        'legal_correctness_is_not_tested':True,'human_certifications':0}
    dump(out/'FULL_SOURCE_QA.json',qa)
    # Same accepted packets and exact checks in both arms. Baseline opens source
    # objects separately for each order; reuse arm verifies each shared object once.
    packets=[show(src,r['instrument_id'],index,records) for r in sample if not r.get('absent_history')]
    start=time.monotonic();fresh_reads=0;fresh_bytes=0
    for packet in packets:
        fresh={};problems=validate_packet(root,packet,fresh)
        if problems:raise ValueError(problems)
        stats=source_stats(root,fresh);fresh_reads+=stats['source_file_reads'];fresh_bytes+=stats['source_bytes_read']
    fresh_seconds=time.monotonic()-start
    start=time.monotonic();shared={}
    for packet in packets:
        if validate_packet(root,packet,shared):raise ValueError('reuse validation failed')
    shared_seconds=time.monotonic()-start
    bench={'schema':'eo-status-history-reuse-benchmark/v1','sample_orders':len(packets),
       'separate_order_source_verification':{'file_reads':fresh_reads,'bytes_read':fresh_bytes,'seconds':round(fresh_seconds,6)},
       'batch_shared_source_verification':dict(source_stats(root,shared),seconds=round(shared_seconds,6)),
       'file_reads_avoided':fresh_reads-source_stats(root,shared)['source_file_reads'],
       'source_bytes_avoided':fresh_bytes-source_stats(root,shared)['source_bytes_read'],
       'billed_tokens':None,'agent_minutes_saved':None,'reviewer_minutes_saved':None,
       'limits':['I/O benchmark only; OS disk cache uncontrolled; no end-to-end agent-cost conclusion.',
                 'Both arms verify the same evidence. Shared validation is safe only for this frozen immutable batch.']}
    dump(out/'REUSE_BENCHMARK.json',bench)
    return qa,bench


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,default=ROOT);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();qa,bench=run(a.repo,a.out);print(canon({'qa':qa,'benchmark':bench}))
