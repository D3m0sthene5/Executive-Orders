"""Build a research-only, unreviewed factual proposal from a single retained witness.
Use existing source files or exact local base Git blobs; no network or writes to source registries.
Print the record for independent review. No reviewer, accepted answer or application is synthesized.
"""
from pathlib import Path
import json
import subprocess
import sys
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'jobs/norton'))
import model as M

BASE = 'c733e69dbd0fa1e57a1f2614a33d77bdd600f122'
PREFIX = 'research/production/astra-portfolio-repair-2026-10-20/panizzi/live-probe/'
RAW = PREFIX + 'files/5960e47c7c1e1dce79cf2ac8d55f26a9042e150f66a04443e7990678af82fc19.html'
TEXT = PREFIX + 'texts/queue_EO_13792_Astra_portfolio_DOI_congressional_testimony_concerning_EO_13792_b46d370fb0.txt'
PINS = {RAW:'5960e47c7c1e1dce79cf2ac8d55f26a9042e150f66a04443e7990678af82fc19',
        TEXT:'98f68af21a5735f965c77e58ccfb72060907c99bbd175a63a9936932714825c7'}

def run():
    with TemporaryDirectory() as tmp:
        root=Path(tmp)
        for path, digest in PINS.items():
            p=REPO/path
            raw=p.read_bytes() if p.is_file() else subprocess.check_output(
                ['git','--no-lazy-fetch','cat-file','blob',BASE+':'+path],cwd=REPO)
            if M.sha(raw) != digest:raise ValueError('source changed: '+path)
            dest=root/path
            dest.parent.mkdir(exist_ok=True,parents=True)
            dest.write_bytes(raw)
        text=(root/TEXT).read_bytes().decode('utf-8')
        source={'url':'https://www.doi.gov/node/26508','page_or_item':'H.R. 4532 testimony, Background',
                'sha256':PINS[RAW],'text_sha256':PINS[TEXT],'raw_path':RAW,'text_path':TEXT,
                'primary':True,'retrieved_utc':'2026-10-20T15:52:45Z','route':'given/given',
                'edition':'DOI January 30, 2018 written testimony, retained HTML'}
        def span(value):
            if text.count(value)!=1:raise ValueError('unique source quotation required')
            start=text.index(value)
            return {'source':source,'text':value,'char_start':start,'char_end':start+len(value)}
        passage=next(p for p in text.splitlines() if p.startswith('In response to strong local concerns'))
        q={'schema':'norton-question/v1','entity_id':'Secretary of the Interior acting pursuant to EO:13792',
           'object':'Final Report assessing 27 national monuments','scope':'submission for Presidential consideration',
           'origin':'machine_extracted',
           'interval_start':'2017-04-26','interval_end':M.CUTOFF,'event_kind':'report_delivery',
           'proposition':'Did the Secretary submit the Final Report identified in the DOI testimony for consideration to the President?'}
        q['question_key']=M.question_key(q)
        event={'schema':M.INTERVAL_SCHEMA,'question_key':q['question_key'],'entity_id':q['entity_id'],
               'event_kind':q['event_kind'],'event_date':None,**span(passage),
               'occurrence_interval':{'occurrence':'established','start':'2017-04-26','end':'2018-01-30',
                   'start_basis':{'witness':'occurrence_span','reason':'The same paragraph places the submission in accordance with this specific order, signed April 26, 2017. Issuance only bounds the event below.'},
                   'end_basis':{'witness':span('January 30, 2018'),'reason':'The dated testimony expressly describes the two submissions in the past tense. Its date bounds the fact above; it is not an observed date of delivery.'}}}
        event['id']='NE:'+M.fingerprint(event)
        errors=M.evidence_errors(root,q,event)
        if errors:raise ValueError(errors)
        # A weaker candidate recording nonoccurrence as unknown, or smuggling in the testimony date
        # as a known exact event, must not validate under the same route.
        assert M.evidence_errors(root,q,dict(event,event_date='2018-01-30'))
        unknown=dict(event,occurrence_interval=dict(event['occurrence_interval'],occurrence='unknown'))
        assert M.evidence_errors(root,q,unknown)
        return {'schema':'research-only-interval-candidate-replay/v1','source_commit':BASE,'question':q,
                'candidate':event,'producer':'sol-intervals','evidence_errors':errors,'independent_review':None,
                'legal_effect':'unresolved','whole_order_status_proposed':False,
                'source_qualified_scope':'Single retained witness; conservative inclusive bounds, not a representation of the narrowest bounds obtainable from other sources. Exact final transmission/receipt, version, routing, complete performance, savings, and first ending remain unestablished. Distinguish the interim report, which has separate leads.',
                'next_step':'Examine the exact final transmittal, recipient logs and transmitted version; see sibling casework comparison of the August 24 draft and December public release. Obtain independent question/answer and clause examination. Neither release alone dates final submission. The casework desk found Senate testimony stating December 2017: request exact official bytes and review that narrower factual interval; do not silently replace this single-witness candidate.'}

if __name__=='__main__':print(json.dumps(run(),indent=2,ensure_ascii=False))
