import json,pathlib,hashlib,datetime
R=pathlib.Path('.');B=R/'research/excavator/machiavelli-modern-undecided-20261105/continuation-20261105/labor'
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def W(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
S=json.loads((B/'SOURCE_FINDINGS.v3.json').read_text()); checks=[]
for s in S['sources']:
 if s.get('text_path'):
  p=pathlib.Path(s['text_path']);t=p.read_text();assert H(p)==s['text_sha256']
  for q in s.get('excerpts',[]):assert t[q['char_start']:q['char_end']]==q['quote']
 if s.get('local_path'):assert H(pathlib.Path(s['local_path']))==s['sha256']
for eo in [13836,13837,13839,13925]:
 p=B/f'EO_{eo}';d=json.loads((p/'LIFECYCLE_PROPOSAL.v2.json').read_text());old=json.loads((p/'LIFECYCLE_PROPOSAL.json').read_text());a=json.loads((p/'LIFECYCLE_ANALYSIS.v2.json').read_text())
 assert not d['approved'] and not a['approved'];assert {x['scope_id'] for x in d['clauses']}=={x['scope_id'] for x in old['clauses']};assert len(d['clauses'])==len({x['scope_id'] for x in d['clauses']})
 assert a['source_findings']['sha256']==H(B/'SOURCE_FINDINGS.v3.json');assert all(c['reason'].strip() for c in d['clauses'])
 assert 'section 1(a)' not in json.dumps(d) if eo==13925 else True
 checks.append({'instrument_id':f'EO:{eo}','scope_count':len(d['clauses']),'scope_set_matches_frozen_prior':True,'approved':False,'native_exact_first_end_count':sum(bool(c.get('effective_date')) for c in d['clauses']),'later_formal_revocation_pinned':True,'analysis_source_binding_verified':True})
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
V={'schema':'eo-continuation-local-validation/v2','checked_utc':now,'checks':checks,'source_literal_spans_verified':sum(len(x.get('excerpts',[])) for x in S['sources']),'raw_hashes_rechecked':sum(bool(x.get('local_path')) for x in S['sources']),'text_hashes_rechecked':sum(bool(x.get('text_path')) for x in S['sources']),'unmatched_excerpt_needles':S['unmatched_excerpt_needles'],'assembly_run':False,'independent_review':False,'remaining_source_gaps':['actual Dkt57 injunction order','native FCC filing statement retention','native court-authored mandate retention and official custody'],'model':'Actual model identifier not exposed to worker','tokens':None,'cash':None,'active_compute_time':None,'timing_note':'File timestamps and this check time are available; no reliable session start or active compute telemetry. No invented cost/timing estimate.'}
W(B/'VALIDATION.v2.json',V)
D={'schema':'eo-continuation-case-dispositions/v1','producer':'continuation-labor','approved':False,'cutoff':'2026-10-14','cases':[]}
for c in checks:
 eo=c['instrument_id'].split(':')[1];D['cases'].append({'instrument_id':c['instrument_id'],'status_proposal':'no','lifecycle_proposal':f'EO_{eo}/LIFECYCLE_PROPOSAL.v2.json','analysis':f'EO_{eo}/LIFECYCLE_ANALYSIS.v2.json','scope_count':c['scope_count'],'formal_command_extinction':'2021-05-14' if eo=='13925' else '2021-01-22','whole_lifecycle_complete':False,'review_disposition':'ready for fresh bounded source/legal review, with explicit first-ending and residual gaps; no readiness or adoption conclusion','specific_remaining_gaps':json.loads((B/f'EO_{eo}/LIFECYCLE_ANALYSIS.v2.json').read_text())['remaining_gaps']})
W(B/'CASE_DISPOSITIONS.v2.json',D)
F=[B/'SOURCE_FINDINGS.v3.json',B/'RESEARCH.v2.md',B/'VALIDATION.v2.json',B/'CASE_DISPOSITIONS.v2.json',B/'SOURCE_REQUESTS.jsonl']
for eo in [13836,13837,13839,13925]:F += [B/f'EO_{eo}/LIFECYCLE_PROPOSAL.v2.json',B/f'EO_{eo}/LIFECYCLE_ANALYSIS.v2.json']
# Supporting extracted text is pinned in the source findings; raw objects remain root-owned.
M={'schema':'eo-continuation-proposal-manifest/v1','producer':'continuation-labor','version':'v2','created_utc':now,'approved':False,'scope':['EO:13836','EO:13837','EO:13839','EO:13925'],'frozen_input_packet_sha256':'4e4b8c8952d2f3664279d4d201e4ef9e0b79b3fd3aeb876310b53ef75446d637','files':[{'path':str(p),'sha256':H(p),'bytes':p.stat().st_size} for p in F],'limitation':'Producer package frozen for fresh review. New factual sources not integrated into frozen registry evidence. No assembly, filing, owner adoption, canonical or readiness changes.'}
W(B/'PROPOSAL_MANIFEST.v2.json',M)
W(B/'HANDOFF.v2.json',{'schema':'eo-continuation-worker-handoff/v1','producer':'continuation-labor','manifest_path':str(B/'PROPOSAL_MANIFEST.v2.json'),'manifest_sha256':H(B/'PROPOSAL_MANIFEST.v2.json'),'kean_registration_needed_by_coordinator':True,'reason':'Worker write authorization restricted to labor directory; no shared register edited.','results':['2018 injunction is scoped temporary implementation suspension; exactfirstdate Aug24–25 pending Dkt57.','July16 2019 jurisdictional vacatur distinct from Oct3 mandate, Oct4 OPM guidance, Oct11 conditional CBA amendment.','2021 revocations extinguish remaining commands; CBA/regulatory/litigation residue separate.','Actual NTIA filing July27 2020 includes all required topics. DOJ proposal development complete within May28–Sept23 2020.','EO14029 citation corrected to section1 unnumbered list, operative wording are revoked; §2 implementation rollback preserved.'],'questions_for_owner':[],'owner_decisions_added':[],'telemetry':{'model':'not exposed','tokens':None,'cash':None,'time':'check timestamp only; active compute unknown'}})
print(json.dumps({'manifest_sha256':H(B/'PROPOSAL_MANIFEST.v2.json'),'checks':checks,'exact_source_spans':V['source_literal_spans_verified']},indent=2))
