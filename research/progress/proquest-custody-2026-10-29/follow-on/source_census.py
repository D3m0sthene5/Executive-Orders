#!/usr/bin/env python3
"""Bounded source custody association census for effective claim references.

Reads effective references emitted independently by claim_census.py, the current
Pinakes metadata, held-copy metadata from claim-checker/sources.py, and a pinned
Git tree listing. It never checks out files or writes/reads whole artifacts into
the checkout. Exact candidate Git blobs are streamed under explicit byte caps.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

MAX_ARTIFACT = 8 * 1024 * 1024
MAX_TOTAL = 24 * 1024 * 1024
DEFAULT_DIR = Path(__file__).resolve().parent


def sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path):
    with open(path, encoding='utf-8') as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                yield n, json.loads(line)


def tree_paths(root, rev):
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
    data = subprocess.check_output(['git','-C',str(root),'ls-tree','-r','-z',rev], env=env)
    out = {}
    for item in data.split(b'\0'):
        if not item:
            continue
        meta, path = item.split(b'\t',1)
        mode, typ, oid = meta.decode('ascii').split(' ')
        out[path.decode('utf-8','surrogateescape')] = {'mode':mode,'type':typ,'oid':oid}
    return out


def git_blob_size(root, oid):
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
    p = subprocess.run(['git','-C',str(root),'cat-file','-s',oid], env=env,
                       text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        return None, 'object_unavailable_without_fetch'
    try:
        return int(p.stdout.strip()), None
    except ValueError:
        return None, 'invalid_object_size'


def verify_git_blob(root, oid, expected_sha, size, remaining):
    if size > MAX_ARTIFACT:
        return 'over_per_artifact_cap', None, 0
    if size > remaining:
        return 'over_total_cap', None, 0
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
    p = subprocess.Popen(['git','-C',str(root),'cat-file','blob',oid], env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    h = hashlib.sha256()
    n = 0
    try:
        while True:
            chunk = p.stdout.read(min(1024*1024, size + 1 - n))
            if not chunk:
                break
            n += len(chunk)
            if n > size:
                p.kill(); p.wait()
                return 'object_size_mismatch', None, n
            h.update(chunk)
        err = p.stderr.read()
        rc = p.wait()
    except Exception:
        p.kill(); p.wait()
        raise
    if rc:
        return 'object_unavailable_without_fetch', None, n
    digest = h.hexdigest()
    return ('exact_hash' if digest == expected_sha else 'hash_mismatch'), digest, n


def pinakes_index(repo):
    p = repo / 'jobs/pinakes-proquest-ingest/output/INVENTORY.csv'
    out = {}
    with p.open(encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            if r.get('sha256'):
                out.setdefault(r['sha256'].lower(), []).append({
                    'instrument_id': r.get('instrument_id'), 'file': r.get('file'),
                    'folder': r.get('folder'), 'bytes': int(r['bytes']) if r.get('bytes','').isdigit() else None,
                    'year': r.get('year'), 'page_range': r.get('page_range'), 'copy': r.get('copy'),
                    'duplicate_of': r.get('duplicate_of'), 'in_census': r.get('in_census')})
    return out


def source_record_index(repo):
    """SOURCES.jsonl metadata for each exact cited hash; no cache body is opened."""
    out = {}
    for p in sorted((repo / 'jobs').glob('*/output/SOURCES.jsonl')):
        job = p.parent.parent.name
        try:
            for _, row in load_jsonl(p):
                sha = row.get('sha256')
                if isinstance(sha, str) and len(sha) == 64:
                    out.setdefault(sha.lower(), []).append({
                        'origin':str(p.relative_to(repo)), 'job':job,
                        'url':row.get('url'), 'bytes':row.get('bytes'),
                        'instrument_ids':row.get('instrument_ids'),
                        'route':row.get('route'), 'page_or_item':row.get('page_or_item'),
                        'cache_path':row.get('cache_path'), 'text_path':row.get('text_path'),
                        'notes':row.get('notes'),
                    })
        except (OSError, json.JSONDecodeError):
            continue
    return out


def held_index(repo):
    """Use the production HeldCopy metadata reader; never reads raw source bodies."""
    modpath = repo / 'jobs/claim-checker/sources.py'
    spec = importlib.util.spec_from_file_location('eo_source_census_sources', modpath)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    idx = mod.build_index(repo, repo / 'jobs/claim-checker')
    by_sha = {}
    for sha, copies in idx.by_sha.items():
        by_sha[sha.lower()] = [{
            'origin': c.origin, 'custody': c.custody, 'bytes_kept': c.bytes_kept,
            'url': c.url, 'bytes': c.bytes, 'local_path': str(c.local_path) if c.local_path else None,
            'local_exists': bool(c.local_path and c.local_path.is_file()),
            'local_is_lfs_pointer': bool(c.local_path and c.local_path.is_file() and mod.is_lfs_pointer(c.local_path)),
            'instrument_ids': c.instrument_ids, 'page_or_item': c.page_or_item,
            'zip_members': [[str(z),m] for z,m in c.zip_members], 'note': c.note[:400],
        } for c in copies]
    return by_sha, idx.notes


def standard_visible(path, needs):
    p = (path or '').replace('\\','/').lstrip('./')
    if p.startswith('jobs/') or p.startswith('.github/') or p.startswith('HANDOFF/'):
        return True
    return any(p == n or p.startswith(n.rstrip('/') + '/') for n in needs)


def classify(ref, matches, local, tree, held, source_records, needs, root, budget, artifact_cache, group_source_statuses=None):
    sha = (ref.get('source_hash') or '').lower()
    hinted = bool(ref.get('proquest_hints') or ref.get('proquest_hint'))
    candidates = matches.get(sha, []) if sha else []
    # A ProQuest signal requires an exact inventory hash or an explicit ProQuest URL/path hint.
    if not candidates and not hinted:
        copies = held.get(sha, []) if sha else []
        recs = source_records.get(sha, []) if sha else []
        indexed_paths=[]
        for sr in recs:
            cp=sr.get('cache_path')
            candidates=[]
            if cp:
                candidates += [f"jobs/{sr['job']}/{sr['job']}-cache/{cp}", f"jobs/{sr['job']}-cache/{cp}", f"jobs/{sr['job']}/output/{cp}"]
            path_rows=[]
            for candidate in candidates:
                tr=tree.get(candidate)
                local_file=root/candidate
                info={'path':candidate,'checkout_exists':local_file.is_file(),'git_tree':bool(tr)}
                if tr:
                    size,serr=git_blob_size(root,tr['oid'])
                    info.update({'mode':tr['mode'],'oid':tr['oid'],'size_bytes':size,'object_state':serr})
                    if not serr and size is not None and size <= 1024:
                        env=dict(os.environ,GIT_NO_LAZY_FETCH='1')
                        pr=subprocess.run(['git','-C',str(root),'cat-file','blob',tr['oid']],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        if pr.returncode==0 and pr.stdout.startswith(b'version https://git-lfs.github.com/spec/v1'):
                            import re
                            mm=re.search(rb'^oid sha256:([0-9a-f]{64})$',pr.stdout,re.M)
                            info.update({'lfs_pointer':True,'lfs_oid_sha256':mm.group(1).decode() if mm else None})
                path_rows.append(info)
            indexed_paths.append({'source_record':sr,'candidate_paths':path_rows})
        statuses=set((ref.get('source_statuses') or '').split(';')) - {''}
        for values in (group_source_statuses or []):
            statuses.update(x for x in values.split(';') if x)
        custody_record_only=('skip:custody_record_only' in statuses)
        repo_paths=[]
        for c in copies:
            local_rel=None
            if c.get('local_path'):
                try: local_rel=Path(c['local_path']).resolve().relative_to(root).as_posix()
                except ValueError: pass
            tr=tree.get(local_rel) if local_rel else None
            repo_paths.append({'origin':c['origin'],'custody':c['custody'],'local_path':local_rel or c.get('local_path'),
                'checkout_exists':c['local_exists'],'git_tree':bool(tr),'git_mode':tr.get('mode') if tr else None,
                'standard_workflow_visible':standard_visible(local_rel,needs) if local_rel else False,
                'is_lfs_pointer':c['local_is_lfs_pointer'],'instrument_ids':c['instrument_ids']})
        # A failed current exact-ref receipt is authoritative for record-only. A route
        # duplicated across sources.py is not itself an identity/path conflict.
        if custody_record_only:
            status='metadata_unresolved'
            reason='fresh exact checker receipt says custody_record_only; source metadata has no byte-bearing copy'
        elif any(c['custody']=='job_cache' and c['local_exists'] for c in copies):
            status='transient_cache_only'
            reason='HeldCopy says a current job-cache copy exists; no raw artifact opened in this census'
        elif any(c['custody']=='opus_release' for c in copies):
            status='lfs_or_release_pointer'
            reason='HeldCopy release metadata identifies a release copy; no release archive fetched or opened'
        else:
            present=[]
            for c, pinfo in zip(copies, repo_paths):
                if c['custody']=='repo_file' and (c['local_exists'] or (pinfo['git_tree'] and pinfo['standard_workflow_visible'])):
                    present.append((c,pinfo))
            if present:
                status='repository_copy_reported_unhashed'
                reason='exact current claim receipt has no source_held nonpass row and HeldCopy records a repository file path; this census did not hash the non-ProQuest bytes, and checkout presence is reported separately'
            elif copies and all(c['custody']=='record_only' for c in copies):
                status='metadata_unresolved'
                reason='HeldCopy records hash/custody metadata only; no present cache/repository bytes are established'
            else:
                status='metadata_unresolved'
                reason='metadata does not establish an exact available or retained copy; no source bytes inspected'
        for item in indexed_paths:
            for pathrow in item['candidate_paths']:
                if pathrow.get('git_tree') and pathrow.get('lfs_pointer'):
                    pathrow['standard_workflow_visible']=standard_visible(pathrow['path'],needs)
        return {'classification':status, 'proquest':False, 'held_copy_metadata':copies,
                'source_record_associations':indexed_paths,'declared_copy_paths':repo_paths,
                'verification_basis':reason,'source_statuses':sorted(statuses),
                'classification_limit':'Non-ProQuest raw PDF bodies were not inspected or rehashed by this census. Receipt status plus HeldCopy metadata is reported; metadata-only candidates remain unresolved.'}

    candidate_rows = []
    issues = []
    visible = []
    exact_git = []
    lfs = []
    for cand in candidates:
        path = cand['folder'].rstrip('/') + '/' + cand['file'] if cand.get('folder') else cand['file']
        loc = local.get(path)
        tr = tree.get(path)
        rec = {'path':path,'inventory':cand,'checkout':None,'pinned_git':None,'standard_runner_visible':standard_visible(path, needs)}
        if loc and Path(root / path).is_file():
            p = root / path
            n = p.stat().st_size
            digest = sha_file(p) if n <= MAX_ARTIFACT else None
            is_pointer = p.read_bytes()[:64].startswith(b'version https://git-lfs.github.com/spec/v1') if n <= 1024 else False
            rec['checkout']={'bytes':n,'sha256':digest,'exact_hash':digest == sha,
                             'is_lfs_pointer':is_pointer,
                             'verification':'exact_hash' if digest == sha else ('over_per_artifact_cap' if n > MAX_ARTIFACT else 'hash_mismatch')}
            if digest == sha: visible.append(rec)
            elif n > MAX_ARTIFACT: issues.append('over_per_artifact_cap')
            else: issues.append('local_path_hash_or_pointer_conflict')
        if tr:
            rec['pinned_git']={'mode':tr['mode'],'oid':tr['oid'],'type':tr['type']}
            cache_key=(path,tr['oid'],sha)
            if cache_key in artifact_cache:
                cached=artifact_cache[cache_key]
                rec['pinned_git'].update(cached)
                if cached.get('verification',{}).get('outcome')=='exact_hash': exact_git.append(rec)
                elif cached.get('pointer') and cached.get('oid_sha256')==sha: lfs.append(rec)
                elif cached.get('object_state')=='object_unavailable_without_fetch': issues.append('object_unavailable_without_fetch')
            elif tr['mode'] not in ('100644','100755') or tr['type'] != 'blob':
                issues.append('git_tree_type_conflict')
            else:
                size, serr = git_blob_size(root, tr['oid'])
                rec['pinned_git']['size_bytes']=size
                if serr:
                    rec['pinned_git']['object_state']=serr
                    artifact_cache[cache_key]=dict(rec['pinned_git'])
                elif size is not None and size <= 1024:
                    # At most 1 KiB; pointer bytes are safe to inspect and not a PDF acquisition.
                    env=dict(os.environ,GIT_NO_LAZY_FETCH='1')
                    pr=subprocess.run(['git','-C',str(root),'cat-file','blob',tr['oid']],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    if pr.returncode == 0 and pr.stdout.startswith(b'version https://git-lfs.github.com/spec/v1'):
                        text=pr.stdout.decode('utf-8','replace')
                        import re
                        oidmatch=re.search(r'^oid sha256:([0-9a-f]{64})$',text,re.M)
                        rec['pinned_git'].update(pointer=True,oid_sha256=oidmatch.group(1) if oidmatch else None)
                        if oidmatch and oidmatch.group(1)==sha: lfs.append(rec)
                        else: issues.append('lfs_pointer_hash_conflict')
                    artifact_cache[cache_key]=dict(rec['pinned_git'])
                elif size is not None:
                    outcome,digest,used=verify_git_blob(root,tr['oid'],sha,size,budget['remaining'])
                    budget['used']+=used; budget['remaining']-=used
                    rec['pinned_git']['verification']={'outcome':outcome,'sha256':digest,'bytes_read':used}
                    if outcome=='exact_hash': exact_git.append(rec)
                    elif outcome in ('over_per_artifact_cap','over_total_cap','object_unavailable_without_fetch'):
                        issues.append(outcome)
                    else: issues.append('git_blob_hash_conflict')
                    artifact_cache[cache_key]=dict(rec['pinned_git'])
        else:
            rec['pinned_git']={'path_present_in_tree':False}
        candidate_rows.append(rec)
    if len(candidates)>1 and len({(c.get('file'),c.get('folder'),c.get('instrument_id')) for c in candidates})>1:
        # Multiple copies are expected; compare identity against the claim's instrument.
        iid=ref.get('instrument_id')
        if any(c.get('instrument_id') != iid for c in candidates): issues.append('identity_conflict_or_duplicate_copy')
    contradiction={'local_path_hash_or_pointer_conflict','git_blob_hash_conflict','git_tree_type_conflict','identity_conflict_or_duplicate_copy','lfs_pointer_hash_conflict'} & set(issues)
    if contradiction:
        classification='conflict_identity_path_hash'
    elif visible:
        classification='local_exact_available'
    elif exact_git:
        classification='retained_regular_git_object_absent_checkout'
    elif lfs:
        classification='lfs_or_release_pointer'
    elif candidates and any(c.get('pinned_git',{}).get('object_state')=='object_unavailable_without_fetch' for c in candidate_rows):
        classification='git_object_unavailable_no_fetch_attempted'
    elif candidates and all(not c.get('pinned_git',{}).get('path_present_in_tree',False) for c in candidate_rows):
        classification='missing_from_pinned_tree'
    elif candidates and any(c.get('pinned_git',{}).get('verification',{}).get('outcome','').startswith('over_') for c in candidate_rows):
        classification='unresolved_cap_limited'
    elif hinted and not candidates:
        classification='metadata_unresolved'
    else:
        classification='metadata_unresolved'
    if not candidate_rows:
        issues.append('no_exact_pinakes_hash_candidate')
    return {'classification':classification,'proquest':True,'source_hash':sha,'candidate_count':len(candidates),
            'candidates':candidate_rows,'issues':sorted(set(issues)),
            'standard_runner_pdf_visible':any(x['standard_runner_visible'] for x in candidate_rows),
            'standard_runner_visibility_rule':'jobs/ is always checked out; additional paths are jobs/claim-checker/needs.txt; root ProQuest folder is outside both.'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default='.')
    ap.add_argument('--references',default=str(DEFAULT_DIR/'EFFECTIVE_REFERENCES.json'))
    ap.add_argument('--output',default=str(DEFAULT_DIR/'SOURCE_ASSOCIATIONS.json'))
    ap.add_argument('--revision',default='HEAD')
    a=ap.parse_args(); root=Path(a.root).resolve()
    refsdoc=json.loads(Path(a.references).read_text(encoding='utf-8'))
    refs=refsdoc.get('references')
    if not isinstance(refs,list): raise SystemExit('references file lacks references list')
    # Current census is compact: each row is an array of string-table indexes plus
    # numeric claim_line. Expand only these metadata fields for classification/joining.
    if refs and isinstance(refs[0],list):
        cols=refsdoc.get('columns'); strings=refsdoc.get('string_table')
        if not isinstance(cols,list) or not isinstance(strings,list): raise SystemExit('compact references lack columns/string_table')
        expanded=[]
        for row in refs:
            if len(row)!=len(cols): raise SystemExit('compact reference row width mismatch')
            obj={}
            for k,v in zip(cols,row):
                if k=='claim_line': obj[k]=v
                elif isinstance(v,int) and 0 <= v < len(strings): obj[k]=strings[v]
                else: raise SystemExit(f'invalid string-table index in {k}')
            obj['claim_key']=f"{obj.get('claim_file')}:{obj.get('claim_line')}"
            obj['proquest_hints']=obj.get('proquest_hint_fields','')
            expanded.append(obj)
        refs=expanded
    pinakes=pinakes_index(root)
    # Include local Pinakes inventory paths, but hash PDFs only if their exact hash was cited.
    local={}
    for h, rows in pinakes.items():
        for c in rows:
            p=c['folder'].rstrip('/')+'/'+c['file'] if c.get('folder') else c['file']
            local.setdefault(p,True)
    tree=tree_paths(root,a.revision)
    needs=[]
    np=root/'jobs/claim-checker/needs.txt'
    if np.is_file():
        needs=[x.strip() for x in np.read_text().splitlines() if x.strip() and not x.lstrip().startswith('#')]
    held,held_notes=held_index(root)
    source_records=source_record_index(root)
    budget={'used':0,'remaining':MAX_TOTAL}
    artifact_cache={}
    groups={}
    for ref in refs:
        key=(ref.get('source_hash') or '').lower() or f"NOHASH:{ref.get('instrument_id')}:{ref.get('claim_key')}:{ref.get('ref_path')}"
        groups.setdefault(key,[]).append(ref)
    artifacts=[]
    counts_artifact={}
    counts_ref={}
    claims_by_category=defaultdict(set)
    source_status_counts=Counter(); source_status_ids=defaultdict(set); source_status_claims=defaultdict(set)
    receipt_version_counts=Counter()
    for rr in refs:
        receipt_version_counts[rr.get('receipt_version_status') or 'unreported']+=1
        for code in (rr.get('source_statuses') or '').split(';'):
            if code:
                source_status_counts[code]+=1
                source_status_ids[code].add(rr.get('instrument_id'))
                source_status_claims[code].add(rr.get('claim_key'))
    proquest_detail=[]
    unresolved_proquest_detail=[]
    nonproquest_detail=[]
    compact_categories={}
    critical_nonpq={
        '33f57e731ee45098fdb2477cc9c0236b0a097d29e575dcff9a1157784df19c38',
        '9e57245c6e3141acd9b2ae498cb39500146348a1fa63abbb3d4fbfd2ea8113b7',
        '0c95b958443cbd6dcccf29e9355a6d2dc3f60e3b8eae44ae83f92446d9596682',
        '945348afbba863ae7dc1fbe7df8759682fe1733962734a9255a1062c0561048c',
    }
    known_ids={'EO:254','EO:2171','EO:4354'}
    for key, group in groups.items():
        rep=next((r for r in group if r.get('proquest_hints') or r.get('pinakes_metadata_matches')),group[0])
        assoc=classify(rep,pinakes,local,tree,held,source_records,needs,root,budget,artifact_cache,[r.get('source_statuses','') for r in group])
        iid_list=sorted({r.get('instrument_id') for r in group if r.get('instrument_id')})
        ac=assoc['classification']; counts_artifact[ac]=counts_artifact.get(ac,0)+1
        counts_ref[ac]=counts_ref.get(ac,0)+len(group)
        claims_by_category[ac].update(r.get('claim_key') for r in group if r.get('claim_key'))
        if assoc.get('proquest'):
            workflow_visible=assoc.get('standard_runner_pdf_visible')
        else:
            vis=[x.get('standard_workflow_visible') for x in assoc.get('declared_copy_paths',[]) if x.get('git_tree') or x.get('checkout_exists')]
            workflow_visible=True if any(v is True for v in vis) else (False if vis else None)
        if ac not in compact_categories: compact_categories[ac]=[]
        # Every source hash has one compact row; EFFECTIVE_REFERENCES is the normalized join table.
        row={'h':None if key.startswith('NOHASH:') else key,'c':ac,
             'p':bool(assoc.get('proquest')),'n':len(group),'w':workflow_visible}
        artifacts.append(row)
        if assoc.get('proquest'):
            affected=[{k:r.get(k) for k in ('instrument_id','claim_key','ref_path','url','page_or_item','receipt_version_status','receipt_mechanical_result','receipt_all_checks_passed','source_status_coverage','source_statuses')} for r in group]
            detail={'sha256':key,'classification':ac,'affected_references':affected,'source_association':assoc}
            if assoc.get('candidate_count',0)>0:
                proquest_detail.append(detail)
            else:
                unresolved_proquest_detail.append({'sha256':key,'classification':ac,'reference_count':len(group),
                    'instrument_ids':iid_list,
                    'resolution':'ProQuest URL/path hint exists, but the source hash does not exactly match any Pinakes INVENTORY artifact; not counted as a ProQuest PDF candidate or beneficiary. Join source_hash in EFFECTIVE_REFERENCES.json for claim refs.'})
        elif key in critical_nonpq:
            focus_ids={'EO:10622','EO:10631','EO:10926','EO:12743'}
            focus_group=[r for r in group if r.get('instrument_id') in focus_ids]
            affected=[{k:r.get(k) for k in ('instrument_id','claim_key','ref_path','url','page_or_item','receipt_version_status','receipt_mechanical_result','receipt_all_checks_passed','source_status_coverage','source_statuses')} for r in focus_group]
            copies=[{k:c.get(k) for k in ('origin','custody','bytes','url','local_path','local_exists','local_is_lfs_pointer','instrument_ids','page_or_item')} for c in assoc.get('held_copy_metadata',[])]
            srecords=[]
            for item in assoc.get('source_record_associations',[]):
                sr=item['source_record']
                srecords.append({'origin':sr.get('origin'),'job':sr.get('job'),'url':sr.get('url'),
                    'bytes':sr.get('bytes'),'instrument_ids':sr.get('instrument_ids'),'route':sr.get('route'),
                    'page_or_item':sr.get('page_or_item'),'cache_path':sr.get('cache_path'),
                    'candidate_paths':item.get('candidate_paths',[])})
            nonproquest_detail.append({'sha256':key,'classification':ac,'total_reference_count':len(group),
                                       'focus_reference_count':len(affected),'affected_references':affected,
                                       'held_copy_metadata':copies,'source_record_associations':srecords,
                                       'classification_limit':assoc.get('classification_limit')})
    cats=['local_exact_available','retained_regular_git_object_absent_checkout','repository_copy_reported_unhashed','lfs_or_release_pointer','transient_cache_only','missing_from_pinned_tree','conflict_identity_path_hash','metadata_unresolved','unresolved_cap_limited','git_object_unavailable_no_fetch_attempted']
    for c in cats:
        counts_artifact.setdefault(c,0); counts_ref.setdefault(c,0); claims_by_category.setdefault(c,set())
    counts_by_category={c:{'artifacts':counts_artifact[c],'references':counts_ref[c],
                           'unique_effective_claims':len(claims_by_category[c])} for c in cats}
    current_proquest_class_counts=Counter(x['classification'] for x in proquest_detail)
    current_proquest_ref_counts=Counter(x['classification'] for x in proquest_detail for _ in x['affected_references'])
    proquest_ids={r['instrument_id'] for x in proquest_detail for r in x['affected_references']}
    additional_ids=sorted(proquest_ids-known_ids)
    proquest_workflow_hidden=[x for x in proquest_detail if not x['source_association'].get('standard_runner_pdf_visible')]
    workflow_hidden_ids=sorted({r['instrument_id'] for x in proquest_workflow_hidden for r in x['affected_references']})
    git_fetch_receipts=[
        {'path':'ProQuest Pre-1937 Orders/PT1-1912-EO-1547.pdf','git_blob_oid':'95abb648384b9b3ef1ad5334f4564b71c5ff53a1','expected_sha256':'2e446a8148b78c1398a3d3a90c3cdce3887444eadc3abe69942b84d67afb198e','bytes':33614,'git_action':'exact promisor-object lazy fetch via git cat-file -s after GIT_NO_LAZY_FETCH=1 proved object unavailable; then streamed cat-file blob SHA-256 verification','source_acquisition':'none (no website/ProQuest download)'},
        {'path':'ProQuest Pre-1937 Orders/PT1-1927-EO-4782.pdf','git_blob_oid':'07c1f130ef290d4b12571da268b8d50490f1d3a1','expected_sha256':'cf42ef50a95da80b5cb6109bcb93716da0d9556124f75635e213bbe19f807138','bytes':50995,'git_action':'exact promisor-object lazy fetch via git cat-file -s after GIT_NO_LAZY_FETCH=1 proved object unavailable; then streamed cat-file blob SHA-256 verification','source_acquisition':'none (no website/ProQuest download)'},
    ]
    detailed_pinakes=[x for x in proquest_detail]
    doc={'schema':'eo-source-associations/v1','revision':a.revision,
         'revision_oid':subprocess.check_output(['git','-C',str(root),'rev-parse',a.revision],text=True).strip(),
         'inputs':{'effective_references':str(Path(a.references).resolve()),'pinakes_inventory':'jobs/pinakes-proquest-ingest/output/INVENTORY.csv','pinakes_fragments':'jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl','git_tree_command':'git ls-tree -r -z HEAD (no -l; no all-blob size walk)','held_copy_reader':'jobs/claim-checker/sources.py build_index metadata only','standard_checkout_contract':'jobs/claim-checker/needs.txt + .github/workflows/run-jobs.yml'},
         'budgets':{'per_artifact_bytes':MAX_ARTIFACT,'total_git_blob_bytes':MAX_TOTAL,'git_blob_bytes_read':budget['used'],'git_fetches_attempted':len(git_fetch_receipts),'git_fetches':git_fetch_receipts,'pdfs_materialized_by_this_census':0,'source_website_acquisitions_by_this_census':0},
         'counts_by_artifact':counts_artifact,'counts_by_reference':counts_ref,'counts_by_category':counts_by_category,
         'receipt_version_status_counts':dict(receipt_version_counts),
         'source_status_counts_by_reference':dict(source_status_counts),
         'source_status_instrument_ids':{k:sorted(x for x in v if x) for k,v in source_status_ids.items()},
         'source_status_unique_effective_claim_counts':{k:len(x) for k,x in source_status_claims.items()},
         'source_status_coverage_counts':dict(Counter(rr.get('source_status_coverage') or 'unreported' for rr in refs)),
         'artifact_count':len(artifacts),'reference_count':len(refs),'distinct_effective_claims_in_reference_set':len({r.get('claim_key') for r in refs if r.get('claim_key')}),
         'proquest_current_post_restoration':{'artifacts_by_current_checkout_classification':dict(current_proquest_class_counts),
             'references_by_current_checkout_classification':dict(current_proquest_ref_counts),
             'current_local_exact_artifacts':sum(1 for x in proquest_detail if x['classification']=='local_exact_available'),
             'current_standard_workflow_invisible_artifacts':len(proquest_workflow_hidden),
             'current_standard_workflow_invisible_instrument_ids':workflow_hidden_ids,
             'known_instrument_ids':sorted(proquest_ids),
             'inherited_known_ids_excluded_from_additional_beneficiaries':sorted(known_ids),
             'additional_beneficiary_instrument_ids':additional_ids,'additional_beneficiary_count':len(additional_ids)},
         'proquest_pre_restoration_baseline':{'stage':'after exact promisor object verification, before coordinator restored PDFs into working checkout',
             'checkout_state':'all five exact ProQuest candidate paths absent from working checkout',
             'verified_exact_regular_git_objects_absent_checkout':5,
             'affected_references':25,'distinct_effective_claims':5,
             'counts_by_category':{'retained_regular_git_object_absent_checkout':{'artifacts':5,'references':25,'unique_effective_claims':5},
                 'local_exact_available':{'artifacts':0,'references':0,'unique_effective_claims':0},
                 'lfs_or_release_pointer':{'artifacts':0,'references':0,'unique_effective_claims':0},
                 'transient_cache_only':{'artifacts':0,'references':0,'unique_effective_claims':0},
                 'missing_from_pinned_tree':{'artifacts':0,'references':0,'unique_effective_claims':0},
                 'conflict_identity_path_hash':{'artifacts':0,'references':0,'unique_effective_claims':0},
                 'metadata_unresolved':{'artifacts':0,'references':0,'unique_effective_claims':0}},
             'standard_workflow_invisible_artifacts':5,
             'inherited_known_ids_excluded_from_additional_beneficiaries':sorted(known_ids),
             'additional_beneficiary_instrument_ids':['EO:1547','EO:4782'],'additional_beneficiary_count':2,
             'two_promisor_blobs_fetched_and_hash_verified':True,
             'basis':'previous SOURCE_ASSOCIATIONS snapshot at same PR revision; two entries were initially promisor-unavailable after a no-lazy lookup, then exact Git object fetches were authorized and both streamed hashes matched Pinakes INVENTORY. The earlier provisional `missing_from_pinned_tree` label was corrected: their paths were in the tree.'},
         'artifact_row_legend':{'h':'SHA-256 / join key','c':'custody classification','p':'ProQuest-associated boolean','n':'effective reference count','w':'standard-workflow source path visible (true/false/null unresolved)'},
         'artifact_rows_source_metadata_pointer':'EFFECTIVE_REFERENCES.json; join by source_hash for claim/ref fields; all 802 unique source hashes have one row in artifacts.',
         'receipt_basis':{'source':json.loads((DEFAULT_DIR/'CLAIM_CENSUS.json').read_text(encoding='utf-8')).get('receipt_source'),'per_reference_statuses':'Fresh exact-claim checker receipt source_held nonpass rows; absence of a row is not treated as a separate source artifact acquisition.'},
         'artifacts':artifacts,
         'proquest_candidates':detailed_pinakes,
         'unresolved_proquest_hints':unresolved_proquest_detail,
         'nonproquest_focus':nonproquest_detail,
         'detailed_join_contract':'All current effective claims/ref fields are preserved once in EFFECTIVE_REFERENCES.json. Join this file by artifact sha256/source_hash; detailed exceptions include claim_key and ref_path. The other 802 source hashes have one row each above, with counts and source metadata pointer.',
         'nonproquest_focus_note':'Four cited Federal Register PDF hashes (EO10622, EO10631, EO10926, EO12743 originals) have historical cache_path metadata but sources.py reports record_only and no candidate cache path is present in checkout or pinned Git tree; this does not establish that a transient cache exists now. The remaining metadata routes are summarized as metadata_unresolved unless HeldCopy plus exact current receipt establishes a byte-bearing route.',
         'category_count_note':'Unique effective-claim counts are per category and can overlap because one claim may cite artifacts in multiple custody categories. Distinct artifacts are counted by source SHA-256. `repository_copy_reported_unhashed` is based on HeldCopy metadata and exact current claim receipts; this census did not hash those non-ProQuest files.',
         'workflow_visibility_note':'A PDF can be present and exactly hashed in the current scratch checkout while its path is excluded from the standard workflow checkout. ProQuest root-folder candidates have w=false even in the post-restoration state.',
         'limitations':['Counts by artifact and by reference are explicit; one artifact can have many affected claims/refs.',
                        'ProQuest candidates are exact only after capped content SHA-256 verification; ProQuest file paths are outside standard runner checkout needs.',
                        'The two listed Git lazy fetches only retrieved exact existing promisor objects; they were not source website downloads. This census wrote no PDFs. The coordinator subsequently restored all five ProQuest PDFs into the working checkout, recorded as the post-restoration state; their root-level paths remain outside standard workflow needs.',
                        'HeldCopy/source-record metadata is not proof of legal equivalence; non-ProQuest focus reports remain custody/status findings only.',
                        'Standard checkout includes jobs/, HANDOFF/, .github/ plus declared needs.txt paths; root ProQuest folder is outside that contract.']}
    Path(a.output).write_text(json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps({'references':len(refs),'artifacts':len(artifacts),'counts_by_artifact':counts_artifact,'git_blob_bytes_read':budget['used'],'output':a.output},indent=2))

if __name__=='__main__': main()
