#!/usr/bin/env python3
"""Test-only review transaction, idempotence, stale guard, no human approval forged."""
import json,sqlite3,shutil,tempfile,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from review_docket import dbopen,review_import
src=pathlib.Path(sys.argv[1]);root=pathlib.Path(sys.argv[2])
root.mkdir(parents=True,exist_ok=True);db=root/'stage17_test_review.sqlite';shutil.copy(src,db)
c=dbopen(db);r=c.execute("SELECT claim_id,fingerprint,policy_version,claim_scope FROM stage17_claim WHERE instrument_id='EO:10084' AND claim_kind='first_cause'").fetchone();assert r;c.close()
fixture={'schema':'eo-stage17-review-v1','instrument_id':'EO:10084','review_decisions':[{'claim_id':r[0],'claim_fingerprint':r[1],'codebook_version':r[2],'reviewer_name':'TEST_FIXTURE_NO_HUMAN', 'reviewed_at':'2026-10-17T00:00:00+00:00','decision':'hold','rationale':'TEST ONLY: historical complete original grants remain partly unresolved','new_claim_text':None,'source_gaps':'Original signed PDF image and statutory savings crosswalk','review_scope':r[3],'test_only':True}]}
f=root/'TEST_ONLY_REVIEW_DO_NOT_IMPORT_IN_PRODUCTION.json';f.write_text(json.dumps(fixture,indent=2)+'\n')
assert review_import(db,f,test_only=True)==1
assert review_import(db,f,test_only=True)==0
c=dbopen(db);assert c.execute('SELECT count(*) FROM stage17_review WHERE test_only=1').fetchone()[0]==1
assert c.execute('SELECT count(*) FROM stage17_review WHERE test_only=0').fetchone()[0]==0
# Change claim/source fingerprint, then demonstrate that previous human review would become stale.
c.execute('UPDATE stage17_claim SET fingerprint=? WHERE claim_id=?',('a'*64,r[0]));c.commit()
assert c.execute('SELECT still_current FROM stage17_current_reviews').fetchone()[0]==0;c.close()
try:review_import(db,f,test_only=True)
except ValueError as err:assert 'Stale' in str(err)
else:raise AssertionError('Stale review was wrongly accepted')
# test snapshot is separate from the unchanged production DB
p=dbopen(src);assert p.execute('SELECT count(*) FROM stage17_review').fetchone()[0]==0;p.close()
print(json.dumps({'test_only_decision_inserted':1,'second_import_new_rows':0,'source_change_stales_review':True,'production_reviews':0,'test_only_db':str(db)},indent=2))
