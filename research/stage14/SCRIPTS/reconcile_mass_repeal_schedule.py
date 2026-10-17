#!/usr/bin/env python3
"""Independent schedule-to-relation reconciliation (not present-effect classification).
EO 12553 example: recover APP-transcribed order text from frozen Opus ZIP,
parse numbered revocation schedule and compare with government-source edge graph.
"""
import hashlib,json,pathlib,re,sqlite3,sys,zipfile
from io import BytesIO
root=zipfile.ZipFile(sys.argv[1]);op=zipfile.ZipFile(BytesIO(root.read('INPUTS/OPUS_STAGE9_STATUS_DELTA.zip')))
member='OPUS_STAGE9_STATUS_DELTA/evidence/reviews/V9_CB_REV/cache/rv_app_eo12553.txt'
b=op.read(member);raw=b.decode(errors='replace')
# Numeric schedule printed as one order per line. Title/preamble/footer ignored.
ids=re.findall(r'(?m)^(\d{3,5}[A-Za-z]?)\s+[A-Za-z]',raw)
if len(ids)!=len(set(ids)):raise AssertionError('schedule repeated labels, investigate')
if len(ids)!=386:raise AssertionError('schedule parser count changed; check official image')
c=sqlite3.connect(sys.argv[2]); graph={x[0].removeprefix('EO:') for x in c.execute("SELECT DISTINCT predecessor FROM relationships WHERE actor='EO:12553' AND quarantined=0")}
report={'actor':'EO:12553','document_source':'APP-hosted executive-order text cached in Opus review evidence','cached_repr_archive_member':member,'cached_text_sha256':hashlib.sha256(b).hexdigest(),'schedule_parser':'line-anchored 3-to-5-digit numbered schedule items followed by subject text','distinct_text_schedule_entries':len(set(ids)),'distinct_unquarantined_government_actor_targets':len(graph),'text_schedule_not_in_graph':sorted(set(ids)-graph),'graph_not_in_text_schedule':sorted(graph-set(ids)),'cross_source_exact_match':set(ids)==graph,'legal_status_promotions':0,'caveat':'Exact schedule matching checks identity/revocation discovery, not whole-order operative cessation, first cause, residual rights, or correctness of hosted transcript.'}
out=pathlib.Path(sys.argv[3]);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
