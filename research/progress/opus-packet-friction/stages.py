"""Time each load_packet stage independently on REPO code (no early exit on mismatch)."""
import sys,time,json
from pathlib import Path
repo=Path(sys.argv[1]).resolve();folder=Path(sys.argv[2]).resolve()
sys.path.insert(0,str(repo/'jobs/claim-kit'));import batch
out={}
def t(name,f):
    s=time.monotonic()
    try:r=f();ok='ok'
    except Exception as e:r=None;ok='ERR '+str(e)[:100]
    out[name]=[round(time.monotonic()-s,2),ok];return r
p,d=t('decode',lambda:batch.load_packet(folder,repo,check_sources=False))
if (folder/'SOURCE_SUPPLEMENT.json').exists():
    import source_supplement;t('source_supplement.verify',lambda:source_supplement.verify(repo,folder))
if p.get('undecided_evidence'):
    import status_overlay
    def und():
        for iid,e in p['undecided_evidence'].items():
            ev=json.loads(batch.safe(repo,e['path']).read_bytes());status_overlay.validate_evidence(repo,ev)
    t('undecided.validate_evidence x%d'%len(p['undecided_evidence']),und)
t('held_text_pins',lambda:[batch.file_sha(batch.safe(repo,r)) for r in p['held_text_file_pins']])
c=t('valla_context',lambda:batch.valla_context(repo,list(d)))
out['valla_equal']=c==p.get('valla_context')
from prior_research import collect
r=t('prior_research.collect',lambda:collect(repo,d,exclude=folder))
out['prior_equal']=r==p.get('prior_research')
print(json.dumps(out))
