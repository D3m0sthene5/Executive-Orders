"""Independent cache/coverage/span/race challenge; all corpus/cache writes temporary."""
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import time
from fixture_challenge import module, setup, run


def normalized(raw):
    return raw.decode('utf-8',errors='replace').replace('\r\n','\n').replace('\r','\n')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--report',required=True,type=Path);args=ap.parse_args()
    started=time.monotonic();candidate=module(args.source.resolve(),'deep_candidate');checks={};events=[]
    with tempfile.TemporaryDirectory(prefix='cruden-deep-') as td:
        root=Path(td);dossiers,_,packet=setup(root)
        run(candidate,root,dossiers,packet);details=candidate.LAST_DETAILS
        valid=[]
        for iid,row in details['members'].items():
            for kind in ('number_citations','code_mentions'):
                for hit in row[kind]:
                    raw=Path(hit['full_text_path']).read_bytes();text=normalized(raw)
                    valid.append(hit['raw_sha256']==hashlib.sha256(raw).hexdigest() and hit['raw_bytes']==len(raw) and text[hit['char_start']:hit['char_end']]==hit['match'])
        checks['all_source_hashes_sizes_spans_match']=bool(valid) and all(valid)
        hit=next(x for x in details['members']['EO:6242']['code_mentions'] if x['file'].endswith('11-unicode-prefix.txt'))
        checks['unicode_lower_expansion_span_mapped']=hit['char_start']==101 and hit['match']=='Code of Fair Competition for the Widget'
        cache=Path(details['corpus']['cache_path'])
        mutations=[('changed_digit_features',lambda e:e['payload']['sources'][1].update(digits=[])),('omitted_record',lambda e:e['payload']['sources'].pop(1)),('fabricated_prefix',lambda e:e['payload']['sources'][1].update(code_prefix=True))]
        for label,mutate in mutations:
            envelope=json.loads(cache.read_text());mutate(envelope);cache.write_text(json.dumps(envelope));old,_md,_stdout=run(candidate,root,dossiers,packet);meta=candidate.LAST_DETAILS['corpus']['timings']
            checks['cache_'+label+'_rejected']=meta['cache_state']=='rebuild' and any('digest mismatch' in x for x in meta['cache_errors'])
            events.append({'label':label,'timings':meta})
        cache.write_text('{"payload":');run(candidate,root,dossiers,packet)
        checks['cache_truncation_rebuild']=candidate.LAST_DETAILS['corpus']['timings']['cache_state']=='rebuild'
        cache.unlink();run(candidate,root,dossiers,packet)
        checks['cache_deletion_rebuild']=candidate.LAST_DETAILS['corpus']['timings']['cache_state']=='miss'
        # Root may bypass filesystem permission bits; use deterministic I/O exception.
        original=candidate.Snapshot.read_raw
        def unreadable(self,path):
            if path.name=='01-base.txt':raise PermissionError('independent fixture unreadable')
            return original(self,path)
        candidate.Snapshot.read_raw=unreadable
        try:
            output,_,_=run(candidate,root,dossiers,packet);meta=candidate.LAST_DETAILS['corpus']['coverage']
            rows=meta['unreadable_sources'];checks['unreadable_preserved']=any(x['path'].endswith('01-base.txt') and 'PermissionError: independent fixture unreadable'==x['error'] for x in rows)
            checks['unreadable_not_emitted']=not any(x['file'].endswith('01-base.txt') for x in output['members']['EO:6242']['number_citations'])
            events.append({'label':'unreadable','coverage':meta})
        finally:candidate.Snapshot.read_raw=original
    # A file already read as irrelevant changes before matching and final verification.
    for mutation in ('edit','add','delete'):
        with tempfile.TemporaryDirectory(prefix='cruden-race-') as td:
            root=Path(td);dossiers,_,packet=setup(root)
            quiet=root/'jobs/held/output/texts/00-quiet.txt';quiet.write_text('Nothing relevant here. ' * 8)
            trigger=root/'jobs/zz/output/texts/zz-trigger.txt';trigger.parent.mkdir(parents=True);trigger.write_text('Trigger only.')
            fired=[False]
            def racing(self,path):
                raw=original(self,path)
                if path==trigger and not fired[0]:
                    fired[0]=True
                    if mutation=='edit':quiet.write_text('E.O.7777'+(' '*(quiet.stat().st_size-8)))
                    elif mutation=='add':(quiet.parent/'new-race.txt').write_text('E.O.7777')
                    else:quiet.unlink()
                return raw
            candidate.Snapshot.read_raw=racing
            try:
                try:run(candidate,root,dossiers,packet)
                except RuntimeError as exc:
                    checks['construction_'+mutation+'_refused']=type(exc).__name__=='SnapshotChanged';events.append({'label':'race_'+mutation,'error':str(exc)})
                else:checks['construction_'+mutation+'_refused']=False
            finally:candidate.Snapshot.read_raw=original
    report={'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'helper_sha256':hashlib.sha256((args.source.parent/'cruden_cache.py').read_bytes()).hexdigest(),'checks':checks,'all_checks_pass':all(checks.values()),'events':events,'elapsed_seconds':time.monotonic()-started,'scope':'Independent engineering fixture challenge; cache corruption means accidental edit without coherent malicious digest rewrite; no filesystem atomicity or legal inference.'}
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'report':str(args.report),'checks':checks,'elapsed_seconds':report['elapsed_seconds']},indent=2))
if __name__=='__main__':main()
