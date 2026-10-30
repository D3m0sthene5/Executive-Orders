"""Independent final auxiliary-input/compiler/search contract challenges."""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import time
from fixture_challenge import module, setup, run


def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--report',required=True,type=Path);args=ap.parse_args()
    started=time.monotonic();candidate=module(args.source.resolve(),'contract_candidate');checks={};events=[]
    init=candidate.Snapshot.__init__
    for mutation in ('register','own','page','packet_add'):
        with tempfile.TemporaryDirectory(prefix='cruden-aux-') as td:
            root=Path(td);dossiers,_,packet=setup(root)
            page=root/'jobs/app-executive-orders/output/texts/page-fixture.txt'
            if mutation=='page':
                page.parent.mkdir(parents=True);page.write_text('Page check original text.')
                dossiers['EO:6242']['evidence']['ORIGINAL:EO:6242']['source']['sha256']='fixture-page-key'
                r={'sha256':'fixture-page-key','text_path':'texts/page-fixture.txt','text_sha256':hashlib.sha256(page.read_bytes()).hexdigest(),'heading':'Executive Order 6242','date':'1933-01-01'}
                (root/'jobs/app-executive-orders/output/DOCUMENTS.jsonl').write_text(json.dumps(r)+'\n')
            def changed(self,repo,discover):
                if mutation=='register':
                    p=root/'jobs/domesday-register/output/REGISTER.csv';p.write_bytes(p.read_bytes().replace(b'Widget',b'Gadget'))
                elif mutation=='own':
                    p=root/'jobs/held/output/texts/00-own.txt';p.write_bytes(p.read_bytes().replace(b'until',b'never'))
                elif mutation=='page':page.write_bytes(page.read_bytes().replace(b'original',b'modified'))
                else:(packet/'PACKET.json').write_text('{}')
                init(self,repo,discover)
            candidate.Snapshot.__init__=changed
            try:
                try:run(candidate,root,dossiers,packet)
                except RuntimeError as exc:
                    checks['aux_'+mutation+'_refused']=type(exc).__name__=='SnapshotChanged';events.append({'label':mutation,'error':str(exc)})
                else:checks['aux_'+mutation+'_refused']=False
            finally:candidate.Snapshot.__init__=init
    with tempfile.TemporaryDirectory(prefix='cruden-contract-') as td:
        root=Path(td);dossiers,_,packet=setup(root);run(candidate,root,dossiers,packet)
        cache=Path(candidate.LAST_DETAILS['corpus']['cache_path'])
        # Coherently hashed old-schema payload must still be rejected.
        envelope=json.loads(cache.read_text());envelope['payload']['schema']='cruden-features/obsolete'
        canonical=json.dumps(envelope['payload'],ensure_ascii=True,sort_keys=True,separators=(',',':')).encode();envelope['sha256']=hashlib.sha256(canonical).hexdigest();cache.write_text(json.dumps(envelope));run(candidate,root,dossiers,packet)
        checks['schema_mismatch_rebuild']=candidate.LAST_DETAILS['corpus']['timings']['cache_state']=='rebuild'
        envelope=json.loads(cache.read_text());envelope['payload']['algorithm']='different-algorithm';envelope['sha256']=hashlib.sha256(json.dumps(envelope['payload'],ensure_ascii=True,sort_keys=True,separators=(',',':')).encode()).hexdigest();cache.write_text(json.dumps(envelope));run(candidate,root,dossiers,packet)
        checks['algorithm_mismatch_rebuild']=candidate.LAST_DETAILS['corpus']['timings']['cache_state']=='rebuild'
        # Exact result bytes, compact stdout descriptor, duplicate-query semantics.
        destination=root/'number-results.json';buf=io.StringIO()
        with contextlib.redirect_stdout(buf):result=candidate.source_search('number',['EO:6242','EO:6242','EO:7777'],destination)
        summary=json.loads(buf.getvalue());raw=destination.read_bytes();saved=json.loads(raw)
        checks['write_compact_summary_hash_size']=summary['sha256']==hashlib.sha256(raw).hexdigest() and summary['bytes']==len(raw) and summary['result']==str(destination)
        checks['duplicate_queries_deduplicated']=list(saved['queries'])==['EO:6242','EO:7777']
        checks['negative_query_bound_to_exact_regex_and_snapshot']=saved['queries']['EO:7777']['matches']==0 and saved['queries']['EO:7777']['number_regex']==candidate.number_pattern('EO:7777').pattern and bool(saved['corpus']['snapshot_sha256']) and 'unreadable_sources' in saved['corpus']['coverage'] and 'tracked_not_discovered' in saved['corpus']['coverage']
        events.append({'label':'write_summary','summary':summary})
        # Expose a tracked but absent source without depending on a real git repository.
        helper=__import__(candidate.Snapshot.__module__,fromlist=['Snapshot']);oldrun=helper.subprocess.run
        class Completed:stdout=b'jobs/held/output/texts/absent-tracked.txt\0jobs/clause-drafts/output/texts/missing.txt\0'
        helper.subprocess.run=lambda *a,**kw:Completed()
        try:
            run(candidate,root,dossiers,packet);cov=candidate.LAST_DETAILS['corpus']['coverage'];checks['tracked_missing_disclosed']='jobs/held/output/texts/absent-tracked.txt' in cov['tracked_not_discovered'];checks['clause_drafts_missing_explicitly_excluded']='jobs/clause-drafts/output/texts/missing.txt' in cov['excluded_clause_drafts']
        finally:helper.subprocess.run=oldrun
        # Actual helper-byte fingerprint changes even for an unexecuted benign comment.
        copied=root/'compiler-copy.py';copied.write_bytes((args.source.parent/'cruden_cache.py').read_bytes());clone=module(copied,'compiler_challenge')
        old=clone.Snapshot(root,candidate.held_texts);old.verify();old_sha=old.compiler_sha256
        copied.write_bytes(copied.read_bytes()+b'\n# independent harmless compiler-byte change\n')
        new=clone.Snapshot(root,candidate.held_texts);new.verify()
        checks['compiler_bytes_invalidate_cache']=old_sha!=new.compiler_sha256 and new.stats['cache_state']=='rebuild' and any('compiler implementation changed' in x for x in new.stats['cache_errors'])
    report={'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'helper_sha256':hashlib.sha256((args.source.parent/'cruden_cache.py').read_bytes()).hexdigest(),'checks':checks,'all_checks_pass':all(checks.values()),'events':events,'elapsed_seconds':time.monotonic()-started,'scope':'Temporary synthetic corpus, same-family independent engineering; static/own/page/PACKET change refusal, schema/algorithm/compiler-byte invalidation, compact artifact descriptor and bounded missing-source disclosures.'}
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'report':str(args.report),'checks':checks,'elapsed_seconds':report['elapsed_seconds']},indent=2))
if __name__=='__main__':main()
