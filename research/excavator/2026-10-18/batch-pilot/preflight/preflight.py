"""Read-only, bounded preflight of Sol's frozen fifty-order cohort.

Collect hashes/metadata once; render thereafter solely from the saved snapshot.
No network, queue mutation, claim assembly, legal finding or reservation occurs.
Python 3.10+, standard library only.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PILOT = 'research/production/claim-kit-pilot-2026-10-18'
SOL = '957c4a40a3967b174b8d0c7a97a920ba9927a176'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def now():
    return datetime.now(timezone.utc).isoformat()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').strip()

def write(name, obj):
    (HERE/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')

def collect():
    started = now()
    pins = {}
    def raw(path):
        p = ROOT/path
        b = p.read_bytes()
        pins[path] = {'sha256': sha(b), 'bytes': len(b)}
        return b
    def read(path):
        return json.loads(raw(path).decode('utf-8-sig'))
    def lines(path):
        return [json.loads(x) for x in raw(path).decode('utf-8-sig').splitlines() if x.strip()]
    def e_meta(e):
        # Do not duplicate dossiers or source bodies. Preserve exact text hashes.
        return {**{k:e[k] for k in ['id','actor_id','role','grade','acceptable_as_original',
                    'requires_page_check','location_verified','char_start','char_end','kind',
                    'source','source_id','source_sha256','text_sha256','scope_id'] if k in e},
                'embedded_chars':len(e.get('text','')),
                'embedded_utf8_sha256':sha(e.get('text','').encode('utf-8'))}
    def d_meta(d):
        law = []
        for x in d.get('current_law_leads',[]):
            meta=x.get('meta',{})
            law.append({k:v for k,v in {
                'where':x.get('where') or meta.get('where'),
                'system':x.get('system') or meta.get('system'),
                'source':x.get('source') or x.get('proposal',{}).get('source'),
                'checked_through':x.get('checked_through') or x.get('proposal',{}).get('checked_through'),
                'currency_code':x.get('currency_code') or meta.get('currency_code'),
                'mention_id':x.get('mention_id') or meta.get('mention_id'),
                'evidence_gap':x.get('evidence_gap'),
                'text_path':x.get('text_path') or meta.get('text_path'),
            }.items() if v is not None})
        return {'fingerprint':d['fingerprint'], 'original_source_id':d.get('original_source_id'),
                'evidence':{k:e_meta(v) for k,v in d.get('evidence',{}).items() if isinstance(v,dict)},
                'current_law_leads':law,'missing':d.get('missing',[]),'conflicts':d.get('conflicts',[]),
                'own_terms':d.get('own_terms',[]),'clauses_count':len(d.get('clauses',[])),
                'actor_contexts':d.get('actor_contexts',[])}
    freeze=read(PILOT+'/FREEZE_MANIFEST.json')
    recheck=read(PILOT+'/FULL_RECHECK_SUMMARY.json')
    old_tasks=lines(PILOT+'/SOURCES_NEEDED.jsonl')
    accepted={x['instrument_id']:x for x in freeze['accepted']}
    final={x['instrument_id']:x for x in recheck['records']}
    local_paths=sorted((ROOT/PILOT/'local-dossiers').glob('EO_*.json'))
    assert len(local_paths)==50, len(local_paths)
    families={}
    for p in sorted((ROOT/PILOT).glob('producer-*/OUTCOMES.json')):
        x=read(p.relative_to(ROOT).as_posix())
        for item in x.get('outcomes',[]):
            if isinstance(item,dict):
                eo=item.get('instrument_id') or item.get('target_id')
                if eo: families[eo]='EO:'+p.parent.name.split('-')[-1]
    cases=[]
    for p in local_paths:
        path=p.relative_to(ROOT).as_posix()
        initial=read(path)
        eo=initial['instrument_id']; fn=p.name
        full_path=PILOT+'/full-dossiers/'+fn
        if (ROOT/full_path).exists():
            full=read(full_path)
            full_origin=full_path
        else:
            # Final Sol HEAD has later machine outputs. The producer freeze is
            # specifically output commit 717e..., not the latest branch dossier.
            git_path='jobs/claim-kit/output/dossiers/'+fn
            b=subprocess.check_output(['git','show',freeze['output_commit']+':'+git_path],cwd=ROOT)
            full=json.loads(b)
            full_origin='git:'+freeze['output_commit']+':'+git_path
            pins[full_origin]={'sha256':sha(b),'bytes':len(b),'frozen_git_blob':git('rev-parse',freeze['output_commit']+':'+git_path)}
        current=read('jobs/claim-kit/output/dossiers/'+fn)
        fam=families.get(eo)
        if fam is None:
            matches=list((ROOT/PILOT).glob('producer-*/'+fn.replace('.json','.decision.json')))
            assert len(matches)==1,(eo,matches)
            fam='EO:'+matches[0].parent.name.split('-')[-1]
        decision=PILOT+'/producer-'+fam.split(':')[-1]+'/'+fn.replace('.json','.decision.json')
        sheet=read(decision)
        fr=final.get(eo,{})
        outcome='ai_accepted_frozen' if eo in accepted else 'unable'
        assert eo in accepted or fr.get('current_status')=='unable',eo
        gaps=fr.get('remaining_material_gaps_verbatim',sheet.get('unresolved_material_gaps',[]))
        # Summary and sheet differences are evidence, not silently reconciled away.
        cases.append({'instrument_id':eo,'family':fam,'outcome':outcome,
                      'frozen_acceptance':accepted.get(eo),'frozen_final':fr,
                      'decision_path':decision,'decision':{k:sheet.get(k) for k in [
                          'dossier_sha256','agent','approved','original_confirmed','original_pages_confirmed',
                          'inventory_confirmed','unresolved_material_gaps','pilot_review']},
                      'gaps_verbatim':gaps,'initial':d_meta(initial),'frozen_full':d_meta(full),'frozen_full_origin':full_origin,
                      'current':d_meta(current)})
    assert collections.Counter(c['outcome'] for c in cases)=={'unable':38,'ai_accepted_frozen':12}
    # Registry records are acquisition receipts; cache existence and hashes are tested separately.
    source_records=[]
    for job in ['fr-originals','source-ladder','current-law','official-compilations','ofr-codification-1989']:
        p='jobs/'+job+'/output/SOURCES.jsonl'
        if not (ROOT/p).exists(): continue
        for r in lines(p):
            source_records.append({**{k:v for k,v in r.items() if k not in ['instrument_ids','notes']},
                                   'registry':p,'instrument_ids':r.get('instrument_ids',[])})
    # Limit metadata snapshot to witnesses actually referenced by the fifty dossiers or old tasks.
    wanted=set()
    ids={c['instrument_id'] for c in cases}
    for c in cases:
        for state in ['initial','frozen_full','current']:
            for e in c[state]['evidence'].values():
                wanted.add(e.get('source',{}).get('sha256'))
            for l in c[state]['current_law_leads']: wanted.add(l.get('source',{}).get('sha256'))
    for t in old_tasks: wanted.add(t.get('known_source',{}).get('sha256'))
    wanted.discard(None)
    source_records=[r for r in source_records if r.get('sha256') in wanted]
    # Probe only exact registry paths, fr-originals aliases, and named source-library PDFs.
    # No scan of source-body contents and no remote download is performed.
    path_checks={}
    def check(path):
        path=path.replace('\\','/')
        if path not in path_checks:
            p=ROOT/path
            if p.is_file():
                b=p.read_bytes(); path_checks[path]={'exists':True,'bytes':len(b),'sha256':sha(b)}
            else: path_checks[path]={'exists':False}
        return path_checks[path]
    for c in cases:
        for st in ['initial','frozen_full','current']:
            for e in c[st]['evidence'].values():
                path=e.get('source',{}).get('text_path')
                if path and '#' not in path: check(path)
                actor=e.get('actor_id')
                if actor and re.fullmatch(r'EO:\d+[A-Z]?',actor):
                    check('research/stage21/original_sources/'+actor.replace(':','_')+'.pdf')
    for r in source_records:
        base=str(Path(r['registry']).parent).replace('\\','/')
        for k in ['cache_path','text_path']:
            rel=r.get(k)
            if not rel or '#' in rel:continue
            check(base+'/'+rel)
            if '/fr-originals/' in base:
                check('jobs/fr-originals/data/full_run/'+rel)
    for t in old_tasks:
        for p in t.get('known_locations',[]):
            if isinstance(p,str) and '#' not in p: check(p)
            elif isinstance(p,dict):
                for k in ['text_path','cache_path','path']:
                    if isinstance(p.get(k),str) and '#' not in p[k]:check(p[k])
    # Detect local claims and exact-line ownership. No claim contents copied.
    claims=[]
    for p in sorted((ROOT/'research/readiness/claims').glob('*.jsonl')):
        rel=p.relative_to(ROOT).as_posix()
        for n,x in enumerate(lines(rel),1):
            if x.get('instrument_id') in ids:
                claims.append({'instrument_id':x['instrument_id'],'path':rel,'line':n,
                               'canonical_claim_sha256':sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()),
                               'unresolved_gap_count':len(x.get('unresolved_material_gaps',[]))})
    lock='research/readiness/CLAIM_KIT_LOCK.json'
    lock_state=read(lock) if (ROOT/lock).exists() else {'local_lock_file_absent':True}
    queue=lines('research/readiness/FETCH_QUEUE.jsonl')
    relevant_queue=[x for x in queue if x.get('instrument_id') in ids or x.get('instrument_id') in {c['family'] for c in cases}]
    statuses={}
    for job in ['claim-kit','current-law','fr-originals','source-ladder','status-history','readiness-tracker']:
        p='jobs/'+job+'/output/STATUS.json'
        if (ROOT/p).exists():statuses[job]=read(p)
    # Git object identity confirms the copied pilot inputs match the frozen branch bytes.
    frozen_tree={}
    for line in git('ls-tree','-r',SOL,PILOT).splitlines():
        mode,typ,rest=line.split(' ',2);oid,path=rest.split('\t',1);frozen_tree[path]=oid
    for path,pin in pins.items():
        if path.startswith(PILOT+'/'):
            b=(ROOT/path).read_bytes()
            oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
            pin['frozen_git_blob']=frozen_tree.get(path)
            pin['frozen_blob_exact_match']=oid==frozen_tree.get(path)
            assert pin['frozen_blob_exact_match'],path
    snapshot={'schema':'eo-fifty-preflight-input/v1','collected_started_utc':started,'collected_finished_utc':now(),
              'repo_head':git('rev-parse','HEAD'),'origin_main_local':git('rev-parse','origin/main'),
              'sol_commit':SOL,'frozen_output_commit':freeze['output_commit'],'frozen_code_commit':freeze['input_code_commit'],
              'scope':'fifty frozen local-dossiers, with final recheck outcomes and current metadata; no new findings',
              'cases':cases,'historical_source_tasks':old_tasks,'source_records':source_records,
              'path_checks':path_checks,'claims':claims,'local_reservations':lock_state,'fetch_queue_relevant':relevant_queue,
              'job_statuses':statuses,'input_pins':pins,
              'limits':['Absence means absent from inspected local paths/evidence, never global source nonexistence.',
                        'Current-law title/USC cache paths may reside in remote runner artifacts; not asserted absent there.',
                        'Source bytes, OCR exactness and AI acceptance are separate from legal/human certification.',
                        'No source-image inspection, claim-checker or legal adjudication is performed by this preflight.',
                        'Current machine outputs precede root source-boundary/dedup integration rebuild; fingerprints must be repinned after rebuilding.',
                        'The final inability reasons are retrospective; no preflight recall or predictable-inability rate is measured.']}
    # Hash current inputs a second time to catch a concurrent output rewrite.
    changed=[p for p,x in pins.items() if not p.startswith('git:') and sha((ROOT/p).read_bytes())!=x['sha256']]
    snapshot['inputs_changed_during_collection']=changed
    assert not changed,changed
    write('INPUT_SNAPSHOT.json',snapshot)
    write('PINS.json',{'schema':'eo-fifty-preflight-pins/v1','sol_commit':SOL,
                       'snapshot_sha256':sha((HERE/'INPUT_SNAPSHOT.json').read_bytes()),'inputs':pins})
    return snapshot

# These are research navigation scopes, manually derived from final verbatim reasons.
# They do not assert that the requested facts occurred or establish a legal first end.
FACTS={
 'EO:10222':'Actual completion of paragraph 2 property/personnel/records transfers; paragraph 1 reorganization chain remains a separate judgment.',
 'EO:11860':'Actual completion of Committee work and dependent mission/support commands; the one-year direction is not event proof.',
 'EO:12462':'Actual report submission under EO12617 or evidence excluding an earlier 60-day trigger; preserve September 30, 1988 outside bound.',
 'EO:12521':'Actual first-report collection completion under d(2), separately from continuing d(1) OMB reporting and EO12649 substitution.',
 'EO:12592':'Actual report transmission/receipt; amended February 28, 1988 deadline is not occurrence.',
 'EO:12601':'Actual final-report submission and any Presidential extension, separate from deadline arithmetic.',
 'EO:12607':'Actual final-report submission for the 30-day trigger, after obtaining complete original; March 31 is only amended deadline.',
 'EO:12668':'Actual Commission report and any extension, plus separate Counsel implementation-report performance/cessation under section 4.',
 'EO:12751':'DOD request/activation and conditional Operation Desert Storm scope/earliest operation and cessation.',
 'EO:12792':'Actual submission after EO12827 deadline amendment; 30-day trigger cannot use January 20, 1993 deadline.',
 'EO:12898':'Actual completion of EO14096 section 4(e) satisfaction route, separately from current-law and residual review.',
 'EO:12961':'Actual final supplemental report submission under EO13034 section 3(a); October 31, 1997 is only deadline.',
 'EO:12975':'Actual section 1(a) review and 1(b) report completion; distinguish commission membership from independent section 2 education command.',
 'EO:13017':'Actual final-report submission for section 5 30-day trigger; compare two-year outside bound.',
 'EO:13075':'Actual final-report submission for section 4(b) 30-day trigger; EO13225 confirms prior termination without date.',
 'EO:13080':'Actual Presidential river designations/completion under section 2(a) and EO13093; independent Presidential instruction scope needs judgment.',
 'EO:13168':'Actual Commission final-report submission and any Presidential extension under section 6; compare stated outer bound.',
 'EO:13210':'Actual final-report submission/receipt for section 6 trigger; fall 2001 instruction is only report timing.',
 'EO:13214':'Actual submission/receipt for section 6 30-day trigger; May 28, 2003 is outside bound.',
 'EO:13227':'Actual submission/receipt for section 4(e) trigger and any extension; EO13255 July 1, 2002 deadline is not occurrence.',
 'EO:13278':'Actual submission/receipt for section 6(b) trigger; compare August 30, 2003 cap.',
 'EO:13326':'Actual report transmission plus actual Commission termination within 60 days; a within-window direction does not establish exact day.',
 'EO:13328':'Actual report submission/receipt, actual termination within 60 days, and separate Intelligence Community report use and Presidential consultation/proposal performance.',
 'EO:13583':'Actual EO14035 plan issuance/implementation where original duty changes depend on it; deadlines are not performance evidence.',
}
LAW_IDS={'EO:11179','EO:11246','EO:12722','EO:12724','EO:12898','EO:13101','EO:13123','EO:13134','EO:13148','EO:13149','EO:13583'}
IMAGE_MAP={
 'EO:12692':['EO:12462','EO:12528','EO:12592','EO:12601','EO:12607','EO:12668'],
 'EO:12919':['EO:10222','EO:11179','EO:11355','EO:12521','EO:12649'],
 'EO:11375':['EO:11246'], 'EO:12607':['EO:12607'], 'EO:12668':['EO:12668'],
 'EO:12696':['EO:12696'],'EO:12751':['EO:12751'], 'EO:13075':['EO:13075'],
 'EO:13080':['EO:13080'],'EO:13168':['EO:13168']}
SPECIAL={
 'EO:12852':'Evaluate June 29, 1997 EO12965 expiry against June 30 EO13053 extension with no retroactivity wording; do not assume uninterrupted continuity.',
 'EO:11355':'Review underlying EO10647, statutory reporting/appointment chain and already-executed predecessor revocation; partial OPM substitution is not whole cessation.',
 'EO:10222':'Trace intervening presidential/statutory reorganization and savings for paragraph 1 until-further-order condition.',
 'EO:11179':'Separate reserve membership/redesignation, continuing program, transitional execution, savings and complete statutory chain.',
 'EO:11246':'Obtain agency-specific OMB transfer schedules under EO12086 sections 1-301/1-302; map section 403(b), accrued contracts and EO14173 optional transition.',
 'EO:12521':'Shared offsets statutory/reporting chain with EO12649; distinguish actual completed first report from ongoing delegation.',
 'EO:12649':'Shared offsets statutory/reporting chain with EO12521; date executed amendment and continuing substituted collection separately.',
 'EO:13134':'Public Law 106-224 Title III section 306 and effective/transition provisions for earlier Biomass committee replacement.',
 'EO:12528':'Inventory original membership/sunset replacement by EO12604 separately from July 1, 1989 Board cessation; image check and residual judgment required.',
 'EO:12975':'Inventory 1996 and 1999 membership changes, renumbered extended Commission provisions and independent section 2 education command.',
}

def derive(s):
    cases=s['cases']; byid={c['instrument_id']:c for c in cases}; checks=s['path_checks']; tasks={}
    def add(key,kind,targets,objective,**extras):
        if key not in tasks:tasks[key]={'task_id':key,'kind':kind,'instrument_ids':[], 'objective':objective,
                                      'status':'proposed_not_queued','legal_finding':False,**extras}
        tasks[key]['instrument_ids']=sorted(set(tasks[key]['instrument_ids'])|set(targets))
        return tasks[key]
    def witnesses(source):
        expected=source.get('sha256'); textpath=source.get('text_path')
        rows=[r for r in s['source_records'] if expected and r.get('sha256')==expected]
        candidate_paths=[]
        if textpath and textpath in checks:candidate_paths.append(textpath)
        for r in rows:
            base=str(Path(r['registry']).parent).replace('\\','/')
            for k in ['cache_path','text_path']:
                p=r.get(k)
                if not p or '#' in p:continue
                candidate_paths.append(base+'/'+p)
                if 'fr-originals' in base:candidate_paths.append('jobs/fr-originals/data/full_run/'+p)
        # Byte-addressed discovery: a source-library file with another name is reusable.
        matching_binary=[p for p,x in checks.items() if x.get('exists') and x.get('sha256')==expected]
        textpaths=[{'path':p,**checks[p]} for p in sorted(set(candidate_paths)) if p in checks and checks[p].get('exists')]
        return {'source_sha256':expected,'indexed_receipts':[{k:r.get(k) for k in ['source_id','registry','url','cache_path','retrieved_utc']} for r in rows],
                'exact_original_byte_paths':matching_binary,'local_paths':textpaths,
                'original_byte_state':'held_exact_bytes' if matching_binary else 'indexed_receipt_only_local_original_bytes_absent' if rows else 'no_receipt_or_local_original_bytes_found_in_scope',
                'remote_runner_cache_state':'not_inspected'}
    # Materialize primary task metadata only: final reasons drive active tasks.
    for eo,obj in FACTS.items():
        add('FACT:'+eo,'fact_specific_research',[eo],obj,
            evidence_state='not_established_in_frozen_or_current_inspected_dossier; wider corpus search still required',
            acquisition_rule='Find dated primary implementation/transmission/receipt records, inspect existing corpus first; never guess a URL or use a deadline as occurrence.')
    for src,targets in IMAGE_MAP.items():
        sources=[]
        for c in cases:
            for state in ['frozen_full','current']:
                for e in c[state]['evidence'].values():
                    if e.get('actor_id')==src and e.get('source',{}).get('sha256'):sources.append(e['source'])
        unique={x['sha256']:x for x in sources}
        add('IMAGE:'+src,'primary_image_and_complete_extent_check',targets,
            'Inspect complete official '+src+' pages, source identity, original extent, OCR/inventory and effective provisions; preserve every unresolved legal/factual reason.',
            witnesses=[witnesses(x) for x in unique.values()],
            acquisition_rule='Reuse exact held bytes or runner cache first; otherwise request known official witness once through source-ladder. Retrieval is not image review.')
    for eo,obj in SPECIAL.items():
        key='JUDGMENT:offsets-chain' if eo in {'EO:12521','EO:12649'} else 'JUDGMENT:'+eo
        add(key,'scoped_legal_and_chain_research',[eo],obj,
            evidence_state='mixed_held_context_and_unestablished_facts; inspect case reasons',
            acquisition_rule='Resolve named source and scope gaps before choosing an end; no automatic legal conclusion.')
    # Unique law provisions, nested beneath shared original witness acquisition tasks.
    for eo in sorted(LAW_IDS):
        c=byid[eo]
        seen=set()
        for l in c['frozen_full']['current_law_leads']:
            where=l.get('where')
            if not where or where.startswith('OFR Codification'):continue
            source=l.get('source',{}); expected=source.get('sha256')
            if (where,expected) in seen:continue
            seen.add((where,expected))
            key='LAW:'+where
            t=add(key,'attributed_legal_text_and_context',[eo],
                  'Locate complete attributed operative text and surrounding context for '+where+'; assess independent command, saved consequence, historical reference or stale pointer through the cutoff.',
                  source_candidates=[],depends_on=[],evidence_state='pointer_only_in_frozen_dossier')
            if source and source not in t['source_candidates']:t['source_candidates'].append(source)
            navigation_artifact=bool(re.search(r'/api/search/|\.(?:json|jsonl)(?:\?|$)',source.get('url','')))
            if navigation_artifact:
                t.setdefault('navigation_artifact_sources',[])
                if source not in t['navigation_artifact_sources']:t['navigation_artifact_sources'].append(source)
            if expected and not navigation_artifact:
                container='WITNESS:'+expected
                add(container,'shared_original_witness_custody',[eo],
                    'Recover/cache and hash one exact original law witness; preserve edition/cutoff, then derive attributed legal-text slices for each dependent citation.',
                    witness=witnesses(source),source=source)
                if container not in t['depends_on']:t['depends_on'].append(container)
        if not seen:
            add('LAW-UNLOCATED:'+eo,'unknown_current_law_scope',[eo],
                'Final recheck identifies a current-law gap but no uniquely attributed citation was located in the frozen dossier; inspect producer record before acquisition.',
                evidence_state='unknown; do not fabricate citation')
    for t in list(tasks.values()):
        if t['kind']=='attributed_legal_text_and_context' and not t['depends_on']:
            key='DISCOVER-WITNESS:'+t['task_id'][4:]
            add(key,'authoritative_law_witness_discovery',t['instrument_ids'],
                'The recorded source is a search/navigation artifact. Identify an authoritative full legal-text witness for '+t['task_id'][4:]+', preserve date/version and exact provenance before deriving any legal evidence.',
                evidence_state='search_receipt_is_not_legal_text')
            t['depends_on'].append(key)
    add('LAW-UNLOCATED:EO:12592','unknown_current_law_scope',['EO:12592'],
        'Final reason mentions unprovided USC/eCFR hit contents, while the frozen/current dossier has no current-law leads. Reconcile this stale/unspecified assertion before requesting material.',
        evidence_state='unknown; keep reason blocked without inventing a citation')
    # Original and actor custody for accepted cases is an evidence readiness gate too.
    for c in cases:
        if c['outcome']!='ai_accepted_frozen':continue
        eo=c['instrument_id']; e=c['frozen_full']['evidence'].get(c['frozen_full'].get('original_source_id'),{})
        actor=c['frozen_full']['evidence'].get('ACTOR_TEXT:'+c['family'],{})
        add('MATCHED-CUSTODY:'+eo,'accepted_case_replay_precondition',[eo],
            'Verify original/actor custody and pin newly rebuilt dossier, retain Sol ownership, then independently replay the existing frozen case without changing its historical outcome.',
            original_witness=witnesses(e.get('source',{})),family_actor_witness=witnesses(actor.get('source',{})),requires_owner_coordination=True)
    # Preserve all fifty. Readiness concerns source evidence, not a forecast of judgment success.
    rows=[]
    for c in cases:
        eo=c['instrument_id']; accepted=c['outcome']=='ai_accepted_frozen'
        a=c['current']['evidence'].get(c['current'].get('original_source_id'),{})
        current_witness=witnesses(a.get('source',{}))
        actor=c['current']['evidence'].get('ACTOR_TEXT:'+c['family'],{})
        current_actor_witness=witnesses(actor.get('source',{}))
        initial_ev=c['initial']['evidence']; full_ev=c['frozen_full']['evidence']
        added=[k for k in full_ev if k not in initial_ev and k.startswith('ACTOR_TEXT:') and full_ev[k].get('embedded_chars',0)]
        held_not_loaded=[]
        for task in s['historical_source_tasks']:
            if eo not in task['instrument_ids'] or task['category'] not in ['local_hydration_artifact','earlier_amendment_or_actor_context']:continue
            m=re.search(r'EO:\d+',task['objective'])
            if not m:continue
            src=m.group(); evidence_id='ACTOR_TEXT:'+src
            # A current original is evidence of held text only, not its legal applicability.
            textpaths=[p for p,x in checks.items() if x.get('exists') and re.search(r'/EO_'+re.escape(src.split(':')[1])+r'(?:\.[^/]*)?\.txt$',p)]
            in_full=bool(full_ev.get(evidence_id,{}).get('embedded_chars'))
            held_not_loaded.append({'source_id':src,'historical_gap_id':task['gap_id'],
                                    'state':'loaded_in_frozen_full' if in_full else 'held_local_text_not_loaded_as_frozen_actor_context' if textpaths else 'not_located_in_inspected_local_paths',
                                    'text_paths':textpaths})
        tids=sorted(t['task_id'] for t in tasks.values() if eo in t['instrument_ids'])
        if accepted:
            gate='accepted_replay_original_bytes_held' if current_witness['exact_original_byte_paths'] else 'accepted_replay_requires_original_byte_recovery'
        elif eo in {'EO:12528','EO:12696'}: gate='image_extent_and_case_judgment_before_replay'
        elif eo in {'EO:12722','EO:12724','EO:13101','EO:13123','EO:13148','EO:13149'}: gate='attributed_current_law_before_replay'
        elif eo=='EO:12852': gate='difficult_continuity_control'
        else:gate='fact_or_chain_research_before_replay'
        owners=[x for x in s['claims'] if x['instrument_id']==eo]
        rows.append({'instrument_id':eo,'family':c['family'],'frozen_outcome':c['outcome'],
                     'preflight_gate':gate,'gaps_verbatim':c['gaps_verbatim'],
                     'frozen_gap_labels':c['frozen_final'].get('remaining_gap_classes',[]),
                     'current_original':{'evidence_id':c['current'].get('original_source_id'),
                                         'metadata':a,'witness':current_witness},
                     'current_family_actor':{'evidence_id':'ACTOR_TEXT:'+c['family'],'metadata':actor,'witness':current_actor_witness},
                     'target_and_family_actor_exact_bytes_held':bool(current_witness['exact_original_byte_paths'] and current_actor_witness['exact_original_byte_paths']),
                     'added_full_actor_contexts':added,'historical_context_reconciliation':held_not_loaded,
                     'current_fingerprint':c['current']['fingerprint'],'frozen_fingerprint':c['frozen_full']['fingerprint'],
                     'fingerprint_changed':c['current']['fingerprint']!=c['frozen_full']['fingerprint'],
                     'task_ids':tids,'local_claim_owners':owners,
                     'ownership':'Sol frozen acceptance; coordinate before replay/replacement' if accepted else 'No local claim found; historical Sol producer evaluation remains preserved' if not owners else 'Local claim conflict; coordinate',
                     'legal_ready':False,'human_certified':False,
                     'prediction_limit':'Retrospective navigation; does not prove this inability was detectable before source review.'})
    tasklist=sorted(tasks.values(),key=lambda t:(-len(t['instrument_ids']),t['task_id']))
    counts={'orders':len(rows),'frozen_outcomes':dict(collections.Counter(r['frozen_outcome'] for r in rows)),
            'preflight_gates':dict(collections.Counter(r['preflight_gate'] for r in rows)),
            'tasks':len(tasklist),'task_kinds':dict(collections.Counter(t['kind'] for t in tasklist)),
            'historical_source_tasks_preserved':len(s['historical_source_tasks']),
            'dossiers_changed_vs_frozen':sum(r['fingerprint_changed'] for r in rows),
            'original_bytes_held_cases':sum(bool(r['current_original']['witness']['exact_original_byte_paths']) for r in rows),
            'target_and_family_actor_exact_bytes_held_cases':sum(r['target_and_family_actor_exact_bytes_held'] for r in rows),
            'cases_with_new_full_actor_contexts':sum(bool(r['added_full_actor_contexts']) for r in rows),
            'local_claim_conflicts':len(s['claims']),
            'material_current_law_cases':len(LAW_IDS),'unknown_current_law_scope_cases':1,
            'fact_specific_research_cases':len(FACTS)}
    write('ORDERS.json',rows);write('TASKS.json',tasklist);write('SUMMARY.json',counts)
    out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=['instrument_id','family','frozen_outcome','preflight_gate','ownership','fingerprint_changed','task_ids'])
    writer.writeheader()
    for r in rows:writer.writerow({k:';'.join(r[k]) if isinstance(r[k],list) else r[k] for k in writer.fieldnames})
    (HERE/'ORDERS.csv').write_text(out.getvalue(),encoding='utf8')
    return counts

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--collect',action='store_true');ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    s=collect() if args.collect else json.loads((HERE/'INPUT_SNAPSHOT.json').read_text(encoding='utf8'))
    if args.verify:
        p=json.loads((HERE/'PINS.json').read_text(encoding='utf8'))
        assert p['snapshot_sha256']==sha((HERE/'INPUT_SNAPSHOT.json').read_bytes())
        assert all(r['outcome']=='unable' or r['frozen_acceptance'] for r in s['cases'])
        assert all(c['frozen_acceptance']['dossier_sha256']==c['frozen_full']['fingerprint'] for c in s['cases'] if c['frozen_acceptance'])
        mismatches=[c['instrument_id'] for c in s['cases'] if c['decision']['dossier_sha256']!=c['frozen_full']['fingerprint']]
        assert mismatches==['EO:11860'],mismatches # Explicit retained-unapproved-sheet history.
    counts=derive(s)
    if args.verify:
        orders=json.loads((HERE/'ORDERS.json').read_text(encoding='utf8'))
        tasks=json.loads((HERE/'TASKS.json').read_text(encoding='utf8'))
        ids={r['instrument_id'] for r in orders};tids={t['task_id'] for t in tasks}
        assert len(ids)==50 and len(tids)==len(tasks)
        assert sum(r['frozen_outcome']=='unable' for r in orders)==38
        assert all(r['gaps_verbatim'] for r in orders if r['frozen_outcome']=='unable')
        assert all(set(r['task_ids'])<=tids for r in orders)
        assert all(set(t['instrument_ids'])<=ids for t in tasks)
        assert all(set(t.get('depends_on',[]))<=tids for t in tasks)
        assert not any('/api/search/' in t.get('source',{}).get('url','') for t in tasks if t['kind']=='shared_original_witness_custody')
        assert all(not r['legal_ready'] and not r['human_certified'] for r in orders)
        assert all(r['gaps_verbatim']==next(c['gaps_verbatim'] for c in s['cases'] if c['instrument_id']==r['instrument_id']) for r in orders)
        hard=json.loads((HERE/'snapshots/PINS.json').read_text(encoding='utf8'))
        for x in hard['snapshots']:
            b=(HERE/x['snapshot_path']).read_bytes()
            assert sha(b)==x['sha256'] and json.loads(b)['fingerprint']==x['dossier_fingerprint']
    print(json.dumps(counts,sort_keys=True))

if __name__=='__main__':main()
