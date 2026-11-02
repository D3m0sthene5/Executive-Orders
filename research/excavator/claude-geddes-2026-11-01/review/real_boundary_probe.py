"""Real retained page-boundary engineering check, no legal verdict."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'jobs/geddes'));import geddes
p=ROOT/'research/excavator/claude-apollo-2026-10-31/g01/packet/supp/PACKET.json'
d=geddes.batch.decode(json.loads(p.read_text()))['EO:8129']
x=geddes.view(p,'EO:8129')
c={'instrument_id':'EO:8129','research_rationale':'This order states "Lake Oliver Migratory Waterfowl Refuge."','operative_clauses':[]}
r=geddes.lint_one(1,c,{'EO:8129':d},ROOT,p)
out={'implementation_sha256':hashlib.sha256((ROOT/'jobs/geddes/geddes.py').read_bytes()).hexdigest(),'packet_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_sha256':d['evidence'][d['original_source_id']]['source']['text_sha256'],'view_boundary':x.get('own_text_boundary'),'view_own_text_characters':len(x['own_original_text']),'view_excludes_previous_neighbor': 'Lake Oliver' not in x['own_original_text'],'view_retains_target_name':'Minnewastena' in x['own_original_text'],'attribution_flags':r['flags'],'attribution_rejects_neighbor':any('attributed' in z['code'] for z in r['flags']),'lookup_parent_matches':x.get('bounded_name_search')==json.loads((p.parent.parent/'LOOKUPS.details.json').read_text())['members']['EO:8129'],'scientific_review':False}
print(json.dumps(out,indent=2))
