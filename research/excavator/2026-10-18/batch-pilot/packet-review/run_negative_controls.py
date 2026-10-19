"""Deliberate evidence-loss controls for the independent auditor, not arm inputs."""
import copy
import json
from pathlib import Path
from audit_packet import audit,canonical,digest,HERE,MATCHED,dump

initial=HERE/'initial';controls=HERE/'negative-controls';controls.mkdir(exist_ok=True)
packet=json.loads((initial/'PACKET.json').read_bytes());read=(initial/'READ.md').read_text(encoding='utf8')
eo='EO:12722';baseline=json.loads((MATCHED/'A/dossiers/EO_12722.json').read_bytes())
cases=[]

# Remove the complete first source block, while retaining its heading and bounds.
first=next(iter(packet['text_blocks'].values()))
cases.append(('drop_source_body',read.replace(first['text'],'[deliberately omitted source body]',1),packet,'readable_source_text_exact'))

# Preserve evidence record identity but remove a material exception list.
recordid=next(k for k,v in baseline['evidence'].items() if v.get('exceptions_text'))
meta={k:v for k,v in baseline['evidence'][recordid].items() if k not in ['text','source','actor_source','provision_text','alternative_provisions']}
badmeta={**meta,'exceptions_text':[]}
assert canonical(meta) in read
cases.append(('drop_exception_metadata',read.replace(canonical(meta),canonical(badmeta),1),packet,'readable_evidence_metadata_exact'))

# Keep the heading but suppress all attributed current-law lead metadata.
needle='### current_law_leads\n\n'+canonical(baseline['current_law_leads'])
assert needle in read and baseline['current_law_leads']
cases.append(('drop_current_law_leads',read.replace(needle,'### current_law_leads\n\n[]',1),packet,'readable_material_section_exact'))

# Remove a decoded original while recomputing the wrapper hash: deeper equality
# and dossier fingerprint checks must detect loss independently of envelope hash.
bad=copy.deepcopy(packet);del bad['dossiers']['EO:12696']['evidence']['ORIGINAL:EO:12696']
bad['fingerprint']=digest(canonical({k:v for k,v in bad.items() if k!='fingerprint'}).encode())
cases.append(('drop_original_from_codec',read,bad,'independent_json_value_roundtrip'))

results=[]
for name,body,p,expected in cases:
    rp=controls/(name+'.READ.md');pp=controls/(name+'.PACKET.json')
    rp.write_bytes(body.encode('utf8'));dump(pp,p)
    result=audit(pp,rp,'negative-controls/'+name+'.review')
    detected=expected in {x['kind'] for x in result['failures']}
    assert detected,(name,sorted({x['kind'] for x in result['failures']}))
    results.append({'control':name,'deliberate_mutation':True,'expected_failure':expected,
                    'detected':detected,'verdict':result['verdict'],'failures':result['failures']})
dump(HERE/'NEGATIVE_CONTROLS.json',{'schema':'eo-independent-auditor-negative-controls/v1','all_detected':all(x['detected'] for x in results),'controls':results})
print(json.dumps({'deliberate_controls':len(results),'all_detected':all(x['detected'] for x in results)}))
