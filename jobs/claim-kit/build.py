"""One corpus pass; machine leads only. No fetching and no legal decisions."""
from __future__ import annotations
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import time

import act_overrides
from inputs import COMPILER_FILES, load_corpus
from current_evidence import enrich_current
from excavate import segment, own_terms, acting_provision, discover_mentions, chain, generic_reference_count, segmentation_code_sha256
from assemble import blank_sheet, canonical_sha, assemble
from lifecycle_obligations import obligations
import working_text as W
import fragment_cache

CUTOFF = '2026-10-14'

def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')

def line(fh, obj):
    fh.write(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))+'\n')

class ShardedJsonl:
    """Keep all corpus records in git; the runner moves files above 95 MB away."""
    def __init__(self,path,limit=75000000):
        self.path=Path(path);self.limit=limit;self.part=0;self.size=0;self.fh=None
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        # Only files with this exact managed stem belong to this writer.
        for old in self.path.parent.glob(self.path.stem+'.part*.jsonl'):old.unlink()
        self.fh=self.path.open('w',encoding='utf-8',newline='\n');return self
    def write(self,value):
        size=len(value.encode('utf-8'))
        if size>self.limit:raise ValueError('Single corpus record exceeds shard size: '+self.path.name)
        if self.size and self.size+size>self.limit:
            self.fh.close();self.part+=1;self.size=0
            path=self.path.with_name(self.path.stem+f'.part{self.part:04}.jsonl')
            self.fh=path.open('w',encoding='utf-8',newline='\n')
        self.fh.write(value);self.size+=size
    def __exit__(self,*args):
        if self.fh:self.fh.close()


def filename(iid):
    if not re.fullmatch(r'EO:[A-Za-z0-9_.-]+', iid):
        # Historical census identifiers can contain punctuation. Never conflate identities.
        return 'ID_'+hashlib.sha256(iid.encode()).hexdigest()[:24]
    return 'EO_'+iid[3:]

def text_tier(r, registered=None):
    """0: declared original candidate; 1: registered working text; 2: unverified lead.

    A lead (held_text_lead, derivative_lead, an ungraded text layer) never outranks
    a working text registered under the 2026-10-21 ruling: the assembler cannot
    cite a lead as an original, and a lead's identity is unconfirmed. `registered`
    holds (instrument_id, text_path, grade) of producer-registered working texts
    (inputs.load_corpus); without it a working-text grade label is taken as given."""
    if r.get('acceptable_as_original'):
        return 0
    if r.get('grade') in W.GRADES and (registered is None or
            (r.get('instrument_id'),r.get('text_path'),r.get('grade')) in registered):
        return 1
    return 2

def rank_text(r, registered=None):
    grade=str(r.get('grade') or '').lower()
    return (text_tier(r,registered), 'needs_page_check' in grade,
            'mirror' in grade or 'transcription' in grade, 'codification' in grade,
            r['text_path'])

# File names of statute, public-law, Code and court-report printings. Research on an
# order cites these, but none of them is an executive order's own printing.
LAW_PRINTING = re.compile(r'(?i)^(?:STATUTE-|STAT[-_]?\d|PLAW-|PUBL\d|USCODE-|USREPORTS-)')
# A first line that heads the text as a statute or public law. Only the first line is
# read: EO texts cite "Public Law ..." and "Act of Congress" throughout their bodies.
LAW_HEADING = re.compile(r'(?i)^(?:PUBLIC|PRIVATE)[ \t]+LAW[ \t]+\d|^[A-Z]+(?:-[A-Z]+)?[ \t]+CONGRESS\.?[ \t]+Sess|^\[[ \t]*(?:Public|Private),?[ \t]+No\.')
# Federal Register issue or page printings (a whole issue, a page range or a page citation).
FR_PRINTING = re.compile(r'(?i)(?:^|[/:])(?:FR-\d{4}-\d\d-\d\d|fr_\d{4}-\d\d-\d\d)|\b\d+[ \t]+FR[ \t]+\d+')

def _names(source):
    for key in ('url','archival_id','upstream_url'):
        value=source.get(key)
        if isinstance(value,str) and value:
            path=value.split('#')[0].split('?')[0].rstrip('/')
            yield path.rsplit('/',1)[-1]
            package=re.search(r'/pkg/([^/]+)/',path)  # govinfo package, e.g. /pkg/STATUTE-45/
            if package:yield package.group(1)

def _law_printing(source):
    return next((name for name in _names(source) if LAW_PRINTING.match(name)),None)

def _fr_printing(source):
    return any(FR_PRINTING.search(name) for name in _names(source)) or bool(
        FR_PRINTING.search(str(source.get('page_or_item') or '')))

_EXEC_ORDER=r'(?:E ?x ?e ?c ?u ?t ?i ?v ?e[ \t\n]+O ?r ?d ?e ?r|Exec\.[ \t]*Order|E\.[ \t]?O\.)'
# Producer header lines (source-ladder, fr-originals) name the wanted order; they are not printing.
# A mirror's statement that it holds no text, e.g. APP's "(this executive order was not published)".
_PLACEHOLDER=re.compile(r'(?is)\(?\s*this\s+executive\s+order\s+was\s+not\s+published\s*\.?\s*\)?\.?')
# A lone date line (a failed extraction that kept only the order's date).
_DATE_ONLY=re.compile(r'(?i)[A-Z][a-z]{2,8}\.?[ \t]+\d{1,2},?[ \t]+\d{4}\.?')
_PREAMBLE=re.compile(r'(?im)^(?:Wanted|Cited by|Instrument|Source|Location|SHA-256 of the downloaded file):[^\n]*$')

def prints_order(iid, text):
    """True when the text prints or names this order's number.

    Tolerates the OCR seen in held FR scans: letter-spaced words ("Executive O rder"),
    spaced digits, and a closing bracket read as a digit ("[No. 78571" for [No. 7857]).
    A producer's own "Instrument: EO:n" preamble does not count."""
    from excavate import _clause_locator
    loc=_clause_locator();number=iid[3:]
    try:
        if loc.locate_order(text,number):return True
    except re.error:
        return False
    digits='[ ]?'.join(re.escape(ch) for ch in number)
    body=_PREAMBLE.sub('',text)
    if re.search(r'(?i)'+_EXEC_ORDER+r'[ \t\n]*(?:N ?o ?s?\.?[ \t\n]*)?'+digits+r'(?![0-9])',body):
        return True
    if re.search(r'(?im)^[ \t]*[\[(|tJIl1]?[ \t]*N ?o ?[.,\'’]*[ \t]*'+digits+r'(?:\]|[1l3I|)\]]?[ \t]*$)',body):
        return True
    # FR issue OCR garbles headings ("Executive Urder 12500"); a four- or five-digit
    # order number standing alone (a heading, closing line or contents entry) is
    # enough not to contradict identity. Shorter numbers need an explicit form.
    return len(re.sub(r'\D','',number))>=4 and bool(re.search(r'(?<![\d:/.,-])'+digits+r'(?![\d])',body))

def identity_conflict(iid, r, text, registered=None):
    """Why this held text cannot be the dossier original of iid, or None.

    Only contradictions are tested; nothing here confirms identity. Every tier is
    refused for a text that prints no order at all (empty, a lone date line, or a
    mirror's "not published" placeholder), and every EO for a
    statute/public-law/Code printing, by file name or by the text's
    first line. An unverified lead from a Federal Register issue or page must, in
    addition, print or name the order: an extract that does not is other documents
    on a cited page (for example pages 1-6 of a 66-page issue)."""
    body=_PREAMBLE.sub('',text).strip()
    if not body or _PLACEHOLDER.fullmatch(body) or _DATE_ONLY.fullmatch(body):
        return 'held text prints no order ('+(body[:40] or 'empty')+'): placeholder or failed extraction'
    if not re.fullmatch(r'EO:\d+[A-Za-z]?',iid):
        return None
    source=r.get('source') or {}
    law=_law_printing(source)
    if law:
        return 'statute/public-law/Code printing ('+law+') is not an executive order'
    first=next((ln.strip() for ln in text.splitlines() if ln.strip()),'')
    if LAW_HEADING.search(first):
        return 'text is headed as a statute or public law ('+first[:40]+')'
    if text_tier(r,registered)==2 and _fr_printing(source) and not prints_order(iid,text):
        return 'unverified Federal Register lead does not print or name '+iid+' (other documents on the cited issue/pages)'
    return None

def safe_read(repo, rel):
    p=(repo/rel).resolve()
    if not p.is_relative_to(repo.resolve()):
        raise ValueError('text path escapes repository')
    return p.read_bytes().decode('utf-8')

PRINTED_REFERENCE_KIND='printed_reference_without_change_provision'
NAME_MATCH_MECHANISM='names_same_person'
TARGET_NOT_LOCATED='target provision not located'
CITED_NO_PROVISION='cited by number, no change provision located'
NAME_MATCH_LEAD='names the same person (name-match lead, read before use)'

def unlocated_reason(source_event):
    """How an unlocated known pair is reported: a plain number citation and a Namier name match are
    leads of different kinds from a provision the scanner expected and failed to find."""
    ev=source_event if isinstance(source_event,dict) else {}
    if ev.get('kind')==PRINTED_REFERENCE_KIND:return CITED_NO_PROVISION
    if ev.get('mechanism')==NAME_MATCH_MECHANISM:return NAME_MATCH_LEAD
    proposal=ev.get('proposal') if isinstance(ev.get('proposal'),dict) else {}
    if proposal.get('mechanism')==NAME_MATCH_MECHANISM:return NAME_MATCH_LEAD
    return TARGET_NOT_LOCATED

ACTING_ROLE='acting_instrument_text'
NON_CENSUS_ACTOR='non_census_instrument'
UNNAMED_ACTING='held acting text does not print this order\'s number; not routed (owner ruling D-20261021-unnamed-instruments)'
ACTOR_TEXT_LIMIT=50000
WINDOW_RADIUS=1500
WINDOW_CAP=12
# An executive-order citation that may precede the target's number: "Executive Order(s)", "Ex. Ord.", "E.O.", or a
# bare "Order(s)" right after punctuation or a function word (a strike-and-insert quote: '"Orders 13354 and 13355').
# "Public Land Order 2748" and "Secretary's Order 2748" are other instruments and never qualify.
_CUE=(r'(?:E[ ]?x[ ]?e[ ]?c[ ]?u[ ]?t[ ]?i[ ]?v[ ]?e[ \t\n]{1,3}O[ ]?r[ ]?d[ ]?e[ ]?r[ ]?s?|\bEx\.[ \t\n]{0,2}Ords?\.|\bE\.[ ]?O\.(?:\x27?s)?|\bEOs?'
      r'|(?:^|[^\w\s][ \t\n]{0,2}|\b(?:the|and|or|of|in|by|thereof|under)[ \t\n]{1,3})Orders?)')
_NUMWORD=r'(?:Nos?\.?|Numbers?|Numbered)'
_ITEM=(r'\d{1,5}[A-Z]?(?:,?[ \t\n]{1,3}(?:of|dated)[ \t\n]{1,3}[A-Z][a-z]{2,8}\.?[ \t\n]{1,3}\d{1,2},?[ \t\n]{1,3}\d{4})?'
       r'(?:,?[ \t\n]{1,3}as[ \t\n]{1,3}amended)?')
_SEP=r'[ \t\n]{0,3}[,;]?[ \t\n]{0,3}(?:(?:and|or|&)[ \t\n]{1,3})?'
_PRECEDES=re.compile(_CUE+r'[ \t\n]{0,3}(?:'+_NUMWORD+r'[ \t\n]{0,3})?(?:'+_ITEM+_SEP+r'(?:'+_NUMWORD+r'[ \t\n]{0,3})?){0,8}\Z',re.I)

def target_mentions(iid, text):
    """Exact spans where a held text prints the census order iid by number, as an executive-order citation.

    A lexical lead, never a finding: it only decides whether a held acting text names the order (owner ruling
    D-20261021-unnamed-instruments: an instrument that does not name the order does not end it)."""
    m=re.fullmatch(r'EO:(\d+)([A-Za-z]?)',iid or '')
    if not m or not isinstance(text,str):return []
    number=re.escape(m[1])+(re.escape(m[2]) if m[2] else '')
    found=[]
    for hit in re.finditer(r'(?<![\w.,/$\u00a7-])'+number+r'(?![\w]|[.,]\d)',text):
        a=max(0,hit.start()-220)
        # A word character stands in for the text cut off before the window, so '^' is only the text's start.
        before=('w' if a else '')+text[a:hit.start()]
        if _PRECEDES.search(before):found.append((hit.start(),hit.end()))
    return found

def context_windows(text, spans, radius=WINDOW_RADIUS):
    """Merged exact windows of text around spans, widened to whole lines; [(char_start, char_end)]."""
    windows=[]
    for start,end in sorted(spans):
        if type(start) is not int or type(end) is not int or not 0<=start<end<=len(text):continue
        a=max(0,start-radius);b=min(len(text),end+radius)
        line=text.rfind('\n',max(0,a-200),a)
        a=line+1 if line>=0 else a
        line=text.find('\n',b,min(len(text),b+200))
        b=line+1 if line>=0 else b
        if windows and a<=windows[-1][1]:windows[-1]=(windows[-1][0],max(b,windows[-1][1]))
        else:windows.append((a,b))
    return windows

def _actor_context(iid, actor, ar, acts, evidence, missing):
    """ACTOR_TEXT evidence for one held actor text: the whole text up to ACTOR_TEXT_LIMIT bytes, else exact windows
    around each printed mention of the target and each located provision. A non-census acting text is routed
    only when it prints the target's number. Returns the actor_contexts entry, or None when not routed."""
    text=ar['text'];acting=ar.get('role')==ACTING_ROLE
    mentions=target_mentions(iid,text)
    if acting and not mentions:
        missing.append(UNNAMED_ACTING+': '+actor)
        return None
    key='ACTOR_TEXT:'+actor
    base={'source':ar['source'],'actor_id':actor,'names_target':bool(mentions)}
    if acting:
        base.update(actor_kind=NON_CENSUS_ACTOR,grade=ar.get('grade'),acceptable_as_original=False,
                    notice='Held text of a later instrument outside the executive-order census, under its own identity. '
                           'It prints this order\'s number; exact span only, no legal effect asserted.')
    if len(text.encode('utf-8'))<=ACTOR_TEXT_LIMIT:
        evidence[key]=dict(base,id=key,text=text,char_start=0,char_end=len(text),role='actor_context')
        return {'actor_id':actor,'evidence_id':key,'names_target':bool(mentions)}
    spans=list(mentions)
    for a in acts:
        source=a.get('actor_source') if isinstance(a.get('actor_source'),dict) else {}
        if a.get('actor_id')==actor and source.get('text_sha256')==ar['source'].get('text_sha256'):
            spans.append((a.get('char_start'),a.get('char_end')))
    windows=context_windows(text,spans)
    entry={'actor_id':actor,'text_sha256':ar['source']['text_sha256'],'names_target':bool(mentions),
           'evidence_ids':[],'windows_omitted':max(0,len(windows)-WINDOW_CAP),'full_text_chars':len(text)}
    for start,end in windows[:WINDOW_CAP]:
        wid=key+'@'+str(start)
        evidence[wid]=dict(base,id=wid,text=text[start:end],char_start=start,char_end=end,role='actor_context_window',
                           names_target=any(s<end and e>start for s,e in mentions))
        entry['evidence_ids'].append(wid)
    if acting:
        # The held file itself is the full text; its hash is pinned through the window records.
        entry['held_text_path']=ar['text_path']
        if entry['windows_omitted']:
            missing.append('Large acting text of '+actor+' has '+str(len(windows))+' passages naming this order; '
                           'read the held text at '+ar['text_path']+' for the rest.')
    else:
        entry['overflow']='actor-texts/'+filename(actor)+'.json'
        missing.append('Large actor context must be read at '+entry['overflow']+' before deciding scope/savings.')
    return entry

def select_acting_texts(repo, rows, wanted):
    """{actor: held acting text record} for the wanted non-census actors; one text per actor, read and hashed.

    The first readable declaration wins in (graded first, text path) order; an empty or placeholder text is
    refused. Returns (selected, refused) where refused lists 'actor: reason' strings."""
    by_actor=collections.defaultdict(list)
    for r in rows:
        if r.get('instrument_id') in wanted and r.get('role')==ACTING_ROLE:by_actor[r['instrument_id']].append(r)
    selected={};refused=[]
    for actor,choices in sorted(by_actor.items()):
        for r in sorted(choices,key=lambda r:(r.get('grade') is None,r['text_path'])):
            try:text=safe_read(repo,r['text_path'])
            except (OSError,ValueError,UnicodeError) as e:
                refused.append(actor+': unreadable '+r['text_path']+' ('+type(e).__name__+')');continue
            digest=hashlib.sha256(text.encode()).hexdigest()
            if digest!=r['source'].get('text_sha256'):
                refused.append(actor+': text hash changed '+r['text_path']);continue
            conflict=identity_conflict(actor,r,text)
            if conflict:
                refused.append(actor+': '+conflict);continue
            selected[actor]=dict(r,source=dict(r['source'],text_path=r['text_path'],text_sha256=digest,signing_date=None,filing_date=None),text=text)
            break
    return selected,refused

def package(iid, corpus, selected, clause_rec, terms, acts, chain_rec, missing, known_actors=None, prior_confirmation=None):
    draft=corpus['drafts'].get(iid,{})
    d=draft.get('_draft',{})
    evidence={}
    clauses=[]
    rec=selected.get(iid)
    original_id=None
    if rec:
        original_id='ORIGINAL:'+iid
        evidence[original_id]={
            'id':original_id, 'source':rec['source'], 'text':rec['text'],
            'char_start':0, 'char_end':len(rec['text']),
            'acceptable_as_original':bool(rec.get('acceptable_as_original')),
            'grade':rec.get('grade'), 'requires_page_check':bool(rec.get('requires_page_check')),'location_confidence':rec.get('location_confidence'), 'actor_id':iid,
            'signing_date':rec.get('signing_date'), 'role':'original'}
    if clause_rec:
        for c in clause_rec.get('clauses',[]):
            v=dict(c,source=clause_rec['source'])
            v['id']='CLAUSES:'+v['scope_id']
            clauses.append(v)
            evidence[v['id']]=v
    for n,t in enumerate(terms):
        v=dict(t)
        eid=v.get('id') or f'TERM:{iid}#{n}'
        v.update(id=eid,actor_id=iid,effective_date=t.get('stated_end_date') or t.get('computed_end_candidate'),mechanism='own_terms_'+t['kind'])
        evidence[eid]=v
    for a in acts:
        v=dict(a)
        eid=v.get('id') or 'ACT:'+iid+'>'+a['actor_id']
        v.update(id=eid,source=a.get('actor_source'),text=a.get('provision_text',''))
        evidence[eid]=v
        for alt in a.get('alternative_provisions',[]):
            evidence[alt['id']]=dict(alt,source=alt.get('actor_source'),text=alt.get('provision_text',''))
        for n,e in enumerate(a.get('effective_wording',[])):
            if isinstance(e,dict) and e.get('text'):
                key=eid+f':effective#{n}'
                evidence[key]=dict(e, id=key, source=a['actor_source'],actor_id=a['actor_id'])
    actor_contexts=[]
    for actor in sorted({a['actor_id'] for a in acts}|set(known_actors or [])):
        ar=selected.get(actor)
        if not ar:continue
        context=_actor_context(iid,actor,ar,acts,evidence,missing)
        if context:actor_contexts.append(context)
    # Current-law evidence keeps exact held-text offsets. A citation alone cannot be a predicate.
    current=[]
    for n,frag in enumerate(corpus.get('current_law',{}).get(iid,[])):
        current.append(frag)
        if isinstance(frag,dict) and frag.get('evidence_gap'):
            missing.append(frag['evidence_gap'])
        if isinstance(frag,dict) and all(k in frag for k in ('text','char_start','char_end','source')):
            key=f'CURRENT:{iid}#{n}'
            evidence[key]=dict(frag,id=key)
    searches=[]
    for item in d.get('proposals',{}).get('later_source_search_machine',[]):
        sid=item.get('search_id')
        entry=corpus['machine_searches'].get(sid)
        if entry:
            searches.append(dict(item, **{k:v for k,v in entry.items() if k!='search_id'}))
    missing=list(missing)
    if clause_rec and clause_rec.get('method') == 'heading_and_operative_boundary_v3_trailing_number':
        missing.append(clause_rec['notes'])
    if rec and rec.get('requires_page_check'):missing.append('Official-source page location requires a separate page/image check before original confirmation.')
    if not rec: missing.append('No attributed held text located for this order.')
    elif not rec.get('acceptable_as_original'):
        if rec.get('grade') in W.GRADES:
            missing.append('Provisional working text requires identity, complete-text and any page-check confirmations; retain original-acquisition and quotation-recheck obligations.')
        else:
            missing.append('Held representation is a lead; complete official original requires confirmation/acquisition.')
    if not clauses: missing.append('No clause inventory extracted; do not submit an empty inventory.')
    if not searches: missing.append('No complete machine later-source search available.')
    if corpus['statuses'].get(iid)=='yes':
        missing.append('Current legal predicate and coverage through 2026-10-14 require judgment; a citation or 1989 snapshot cannot prove continuation.')
    dossier={'schema':'eo-claim-kit-dossier/v1','instrument_id':iid,
        'whole_order_status':corpus['statuses'].get(iid), 'legal_cutoff':CUTOFF,
        'original_source_id':original_id,'clauses':clauses,'evidence':evidence,
        'own_terms':[k for k in evidence if k.startswith('TERM:')],
        'actor_contexts':actor_contexts,
        'actor_provisions':[k for k in evidence if k.startswith('ACT:') and ':effective#' not in k],
        'chain':chain_rec,'current_law_leads':current,'machine_searches':searches,
        'draft_gate_errors':d.get('gate',{}).get('errors_now',[]),
        'conflicts':d.get('conflicts',[]),
        'draft_material_gaps':draft.get('claim',{}).get('unresolved_material_gaps',[]),
        'missing':sorted(set(missing)),
        'lifecycle_obligations':obligations(iid, clauses, terms, acts),
        'notice':'MACHINE LEADS ONLY. No segmentation, date, source grade, family or chain is a legal conclusion.'}
    if prior_confirmation is not None:
        dossier['working_text_confirmation']=prior_confirmation
    if iid in corpus.get('status_histories',{}):
        dossier['status_history']=corpus['status_histories'][iid]
    if corpus.get('factual_obligations',{}).get(iid):
        dossier['factual_obligations']=corpus['factual_obligations'][iid]
        for context in dossier['factual_obligations']:
            for event in context.get('citable_factual_events',[]):
                evidence[event['id']]=event
        dossier['factual_event_ids']=[eid for eid,record in evidence.items()
                                     if record.get('role')=='reviewed_factual_event']
        intervals = [eid for eid,record in evidence.items() if record.get('role')=='reviewed_occurrence_interval']
        if intervals:
            dossier['factual_interval_ids'] = intervals
    dossier['fingerprint']=canonical_sha(dossier)
    return dossier

def build(repo, out, cache=None):
    started=time.monotonic();repo=Path(repo).resolve();out=Path(out).resolve()
    if out==repo or not out.is_relative_to(repo):
        raise ValueError('OUTPUT_DIR must be a child of the repository')
    rel=out.relative_to(repo)
    if rel.parts[0] in {'research','progress','HANDOFF','.github'}:
        raise ValueError('OUTPUT_DIR overlaps protected project inputs')
    if rel.parts[0]=='jobs' and (len(rel.parts)<3 or rel.parts[1]!='claim-kit'):
        raise ValueError('OUTPUT_DIR cannot overwrite another source job')
    if rel.parts[0]=='jobs' and rel.parts[:3]!=('jobs','claim-kit','output'):
        raise ValueError('Claim-kit OUTPUT_DIR must be under jobs/claim-kit/output')
    corpus=load_corpus(repo)
    if any((repo/r['text_path']).resolve().is_relative_to(out) for r in corpus['texts']):
        raise ValueError('OUTPUT_DIR overlaps a held text input')
    out.mkdir(parents=True,exist_ok=True)
    universe=corpus['universe'];warnings=list(corpus.get('warnings',[]))
    law_keys=[];law_flat=[]
    for iid,leads in sorted(corpus.get('current_law',{}).items()):
        for lead in leads:law_keys.append(iid);law_flat.append(lead)
    law_enriched=enrich_current(repo,law_flat)
    corpus['current_law']={}
    for iid,lead in zip(law_keys,law_enriched):corpus['current_law'].setdefault(iid,[]).append(lead)
    selected={};segments={};terms={};primary_acts={};all_mentions=[];all_references=[];all_variants=collections.defaultdict(dict);all_terms=collections.defaultdict(dict);generic_refs=set();missing_by=collections.defaultdict(list)
    counts=collections.Counter(universe_orders=len(universe),decided_orders=len(corpus['statuses']))
    # Persistent cache is optional, never an output/provenance substitute. Hash includes parser code.
    code_hash=segmentation_code_sha256()
    cache_path=Path(cache).resolve() if cache else None
    if cache_path:cache_path.mkdir(parents=True,exist_ok=True)
    cache_hits=0
    registered={tuple(k) for k in corpus.get('registered_working_texts',[])}
    rank=lambda r:rank_text(r,registered)
    declared=sorted(corpus['texts'],key=lambda r:(rank(r),r['instrument_id']))
    text_records=[];seen_texts=set();refused=collections.defaultdict(list)
    # Clause-level citations often declare the same file hundreds of times with
    # different page labels. Preserve every declaration, parse each actual held
    # order/artifact/text once, and choose its best original/locator candidate.
    acting_rows=[r for r in corpus.get('acting_texts',[]) if r.get('instrument_id') not in universe]
    with ShardedJsonl(out/'TEXT_REPRESENTATIONS.jsonl') as fh:
        for r in declared:
            line(fh,r)
            key=(r['instrument_id'],r['text_path'],r['source'].get('sha256'),r['source'].get('text_sha256'))
            if key not in seen_texts:seen_texts.add(key);text_records.append(r)
        # Held texts of non-census acting instruments, under their own identity (role acting_instrument_text).
        # They are never scanned as orders; the status overlay selects them by their CLAUSES source.
        for r in acting_rows:line(fh,r)
    counts['acting_text_representations']=len(acting_rows)
    counts['declared_text_representations']=len(declared)
    counts['distinct_held_text_artifacts']=len(text_records)
    with ShardedJsonl(out/'TEXT_CLAUSES.jsonl') as all_clauses:
        for r in text_records:
            iid=r['instrument_id']
            if iid not in universe:continue
            try:text=safe_read(repo,r['text_path'])
            except (OSError,ValueError,UnicodeError) as e:
                missing_by[iid].append('Missing/unreadable held text: '+r['text_path']+' ('+type(e).__name__+')');counts['text_read_failures']+=1;continue
            if not text.strip():counts['empty_texts']+=1;continue
            source=dict(r['source'],text_path=r['text_path'],text_sha256=hashlib.sha256(text.encode()).hexdigest(),signing_date=r.get('signing_date'),filing_date=r.get('filing_date'))
            key=canonical_sha({'parser':code_hash,'iid':iid,'source':source,'signing':r.get('signing_date'),'filing':r.get('filing_date')})
            cp=cache_path/(key+'.json') if cache_path else None
            data=None
            if cp and cp.exists():
                try:data=json.loads(cp.read_text('utf-8'));cache_hits+=1
                except (ValueError,OSError):pass
            if data is None:
                c=segment(iid,text,source)
                ts=own_terms(iid,text,source,c.get('clauses',[]))
                ms,refs=discover_mentions(iid,text,source,r.get('signing_date'),r.get('filing_date'),with_references=True)
                data={'clauses':c,'terms':ts,'mentions':ms,'references':refs}
                if cp:dump(cp,data)
            line(all_clauses,data['clauses'])
            counts['held_texts_scanned']+=1
            if counts['held_texts_scanned']%250==0:print(f"claim-kit: scanned {counts['held_texts_scanned']}/{len(text_records)} held representations",flush=True)
            refusal=identity_conflict(iid,r,text,registered)
            if refusal:
                # Contradicted identity: keep the declaration and its inventory, but the text is
                # neither this order's original nor a source of its terms or acting provisions.
                refused[iid].append(r['text_path']+': '+refusal);counts['texts_refused_as_order_text']+=1
                continue
            for term in data['terms']:
                term=dict(term)
                term['id']=(term.get('id') or f'TERM:{iid}#'+str(term['char_start']))+'@'+source['text_sha256'][:16]
                all_terms[iid][term['id']]=term
            if generic_reference_count(text):generic_refs.add((iid,source['text_sha256'],generic_reference_count(text)))
            if iid not in selected:
                selected[iid]=dict(r,source=source,text=text)
                segments[iid]=data['clauses']
            all_mentions.extend(dict(a,_representation_rank=rank(r)) for a in data['mentions'])
            all_references.extend(dict(a,text_path=r['text_path'],text_sha256=source['text_sha256']) for a in data.get('references',[]))
    for iid,reasons in sorted(refused.items()):
        if iid not in selected:
            missing_by[iid].append('No held text accepted as this order\'s original; refused: '+'; '.join(sorted(set(reasons))))
    terms={iid:list(values.values()) for iid,values in all_terms.items()}
    for iid,rec in sorted(selected.items()):
        if len(rec['text'].encode('utf-8'))>50000:
            dump(out/'actor-texts'/(filename(iid)+'.json'),{'instrument_id':iid,'source':rec['source'],'text':rec['text'],'notice':'Shared full held text; lead only.'})
    # Every known target/actor pair, plus explicitly named changes discovered in every held text.
    pairs={(p['target_id'],p['actor_id'],p.get('parent_id')):p for p in corpus['pairs'] if p.get('target_id') in universe}
    for a in all_mentions:
        target,actor=a.get('target_id'),a.get('actor_id')
        if target not in universe or actor not in universe or target==actor:continue
        variant={k:v for k,v in a.items() if not k.startswith('_')}
        variant['id']='ACT:'+target+'>'+actor+'@'+canonical_sha(variant)[:16]
        all_variants[(target,actor)][variant['id']]=variant
        key=(target,actor,None);pairs.setdefault(key,{'target_id':target,'actor_id':actor})
        if key not in primary_acts or a['_representation_rank']<primary_acts[key]['_representation_rank']:
            primary_acts[key]=a
    # A printed reference with no located change provision still makes the citing order a known
    # actor: its text enters the target's packet, and the pair is reported as unlocated. Known
    # pairs from other producers keep their own source_event.
    for a in all_references:
        target,actor=a['target_id'],a['actor_id']
        if target not in universe or actor not in universe or target==actor:continue
        key=(target,actor,None)
        event={'kind':PRINTED_REFERENCE_KIND,'input_origin':'jobs/claim-kit (held-text scan)',**{k:a[k] for k in ('ref_char_start','ref_char_end','context','context_char_start','context_char_end','text_path','text_sha256','signing_date','filing_date','notes')}}
        if key in pairs:
            # A name-match lead for the same pair is weaker than the printed number: report the citation
            # and keep the name match beside it.
            if unlocated_reason(pairs[key].get('source_event'))==NAME_MATCH_LEAD:
                event['also_names_same_person']=pairs[key]['source_event']
                pairs[key]['source_event']=event
            continue
        pairs[key]={'target_id':target,'actor_id':actor,'source_event':event}
        counts['printed_reference_only_pairs']+=1
    generic_total=sum(n for _,_,n in generic_refs)
    # Parent-as-amended is a separately identified indirect LEAD, never a legal inference of target termination.
    parents=collections.defaultdict(set)
    for a in all_mentions:
        if a.get('verb')=='amend' and a.get('actor_id') in selected and a.get('target_id') in universe:
            parents[a['target_id']].add(a['actor_id'])
    for a in list(primary_acts.values()):
        if re.search(r'\bas\s+amended\b',a.get('provision_text',''),re.I):
            for child in parents.get(a.get('target_id'),set()):
                child_date=selected.get(child,{}).get('signing_date')
                actor_date=a.get('signing_date')
                if child_date and actor_date and actor_date<child_date:continue
                if child!=a['actor_id']:
                    pairs.setdefault((child,a['actor_id'],a['target_id']),{'target_id':child,'actor_id':a['actor_id'],'parent_id':a['target_id']})
    actors_by=collections.defaultdict(list);missing_sources=[];located_pairs={}
    acting_selected,acting_refused=select_acting_texts(repo,acting_rows,{a for _,a,_ in pairs if a not in universe})
    for reason in acting_refused:warnings.append('acting text refused: '+reason)
    unnamed_pairs=set();acting_used=set()
    for pair_no,(key,p) in enumerate(sorted(pairs.items(),key=lambda kv:(kv[0][1],kv[0][0],str(kv[0][2]))),1):
        if pair_no%2000==0:print(f'claim-kit: located {pair_no}/{len(pairs)} known provision pairs',flush=True)
        target,actor,parent=key
        if actor not in universe:
            ar=acting_selected.get(actor)
            if ar is None:
                missing_by[target].append('Acting identity absent from census: '+actor);continue
            if not target_mentions(target,ar['text']):
                # A held statute, rule or land order that does not print the order's number does not end it.
                unnamed_pairs.add((target,actor));missing_by[target].append(UNNAMED_ACTING+': '+actor);continue
            # Held and named: its exact text enters the target's dossier as ACTOR_TEXT. No ACT record is made.
            acting_used.add(actor);counts['acting_text_pairs_named']+=1;continue
        ar=selected.get(actor)
        # Explicit provisions were already located in the whole-text pass. Reuse
        # them; rescanning a shared parent for every amender creates a quadratic
        # CPU cost without adding evidence.
        a=primary_acts.get((target,actor,None))
        if a is None and parent:
            base=primary_acts.get((parent,actor,None))
            if base and re.search(r'\bas\s+amended\b',base.get('provision_text',''),re.I):
                a=dict(base,id='ACT:'+target+'>'+actor,target_id=target,names_target=False,
                       reaches_target_via=parent+' as amended',
                       scope='partial' if base.get('scope')=='partial' else 'whole_via_parent',
                       notes=base.get('notes','')+' Indirect parent membership is an unconfirmed lead.')
        if a and a.get('provision_text'):
            pair=(target,actor)
            a={k:v for k,v in a.items() if not k.startswith('_')}
            if pair not in located_pairs or (not parent and not a.get('reaches_target_via')):
                located_pairs[pair]=a
        else:
            row={'target_id':target,'actor_id':actor,'parent_id':parent,'reason':'acting text absent' if not ar else unlocated_reason(p.get('source_event')),'source_event':p.get('source_event')}
            missing_sources.append(row);missing_by[target].append(row['reason']+': '+actor)
    # Agent-located, independently upheld ACT records (research/readiness/act_overrides) fill only
    # pairs the scanner could not locate; act_overrides.verify refuses anything else.
    # With no override lines the build is unchanged: no report file and no extra counts.
    override_rows=act_overrides.load(repo)
    if override_rows:
        unlocated={(r['target_id'],r['actor_id']) for r in missing_sources if r['reason'] in (TARGET_NOT_LOCATED,CITED_NO_PROVISION) and not r.get('parent_id')}-set(located_pairs)
        ingested,override_report=act_overrides.ingest(repo,selected,universe,unlocated,override_rows)
        for (target,actor),a in ingested.items():
            located_pairs[(target,actor)]=a
            missing_by[target]=[m for m in missing_by[target] if m not in (TARGET_NOT_LOCATED+': '+actor,CITED_NO_PROVISION+': '+actor)]
        missing_sources=[r for r in missing_sources if (r['target_id'],r['actor_id']) not in ingested]
        counts['act_overrides_ingested']=len(ingested);counts['act_overrides_refused']=sum(r['status']=='refused' for r in override_report)
        dump(out/'ACT_OVERRIDES_REPORT.json',override_report)
    elif (out/'ACT_OVERRIDES_REPORT.json').exists():
        (out/'ACT_OVERRIDES_REPORT.json').unlink()
    for (target,actor),a in sorted(located_pairs.items()):
        a['alternative_provisions']=list(all_variants.get((target,actor),{}).values())
        actors_by[target].append(a)
    with ShardedJsonl(out/'ACTING_REPRESENTATIONS.jsonl') as fh:
        for pair,values in sorted(all_variants.items()):
            for variant in values.values():line(fh,variant)
    known_actors_by=collections.defaultdict(set)
    for target,actor,_ in pairs:
        if (target,actor) not in unnamed_pairs:known_actors_by[target].add(actor)
    counts['acting_text_pairs_unnamed']=len(unnamed_pairs);counts['acting_texts_selected']=len(acting_used)
    for actor in set(acting_selected)-acting_used:del acting_selected[actor]  # free texts that name no order
    # Decided dossiers see the same actor texts the overlay will select: census texts plus named acting texts.
    context_texts=dict(selected);context_texts.update({a:acting_selected[a] for a in acting_used})
    counts['known_pairs']=len({(t,a) for t,a,_ in pairs});counts['located_actor_pairs']=sum(map(len,actors_by.values()))
    counts['orders_with_held_text']=len(selected);counts['generic_references_excluded']=generic_total
    confirmation_records=W.load_confirmations(repo)
    confirmation_index=fragment_cache.shared(repo) if confirmation_records else None
    families=collections.defaultdict(set)
    index=[]
    with ShardedJsonl(out/'CLAUSES.jsonl') as cf, ShardedJsonl(out/'OWN_TERMS.jsonl') as tf, ShardedJsonl(out/'ACTING_PROVISIONS.jsonl') as af, ShardedJsonl(out/'CHAINS.jsonl') as chf, ShardedJsonl(out/'STATUS_LEADS.jsonl') as sf, ShardedJsonl(out/'OVERLAY_INPUTS.jsonl') as of:
        for iid in sorted(universe):
            c=segments.get(iid)
            if c:line(cf,c)
            ts=terms.get(iid,[])
            for t in ts:line(tf,t)
            acts=actors_by.get(iid,[])
            for a in acts:
                line(af,a)
                families['actor:'+a['actor_id']].add(iid)
                if a.get('reaches_target_via'):families['parent:'+str(a['reaches_target_via'])].add(iid)
            for t in ts:
                families['own_term:'+t['kind']].add(iid)
            if iid in selected:
                src=selected[iid]['source']
                families['source:'+str(src.get('sha256') or src.get('url'))].add(iid)
            chain_rec=chain(iid,acts,generic_refs_excluded=generic_total)
            line(chf,chain_rec)
            original=selected.get(iid,{}).get('source',{})
            prior=W.matching_confirmation(original,repo,confirmation_records,confirmation_index) if confirmation_records else None
            if iid not in corpus['statuses']:
                draft=corpus['drafts'].get(iid,{})
                search_ids={s.get('search_id') for s in draft.get('_draft',{}).get('proposals',{}).get('later_source_search_machine',[])}
                line(of,{'schema':'eo-claim-kit-overlay-input/v1','instrument_id':iid,
                         **({'working_text_confirmation':prior} if prior is not None else {}),
                         'selected':{k:v for k,v in selected[iid].items() if k!='text'} if iid in selected else None,
                         'draft':draft,'machine_searches':{k:v for k,v in corpus['machine_searches'].items() if k in search_ids},
                         'known_actor_ids':sorted(known_actors_by.get(iid,[]))})
                line(sf,{'instrument_id':iid,'status':None,'lead_actor_ids':sorted({a['actor_id'] for a in acts}),'own_terms':ts,'has_held_text':iid in selected,'current_law_leads':corpus.get('current_law',{}).get(iid,[]),'status_history':corpus.get('status_histories',{}).get(iid),**({'factual_obligations':corpus['factual_obligations'][iid]} if corpus.get('factual_obligations',{}).get(iid) else {}),'missing':missing_by[iid],'notice':'Separate status-lead queue. Does not decide or write a status.'})
                continue
            dossier=package(iid,corpus,context_texts,c,ts,acts,chain_rec,missing_by[iid],known_actors_by.get(iid),prior)
            name=filename(iid)
            dump(out/'dossiers'/(name+'.json'),dossier)
            dump(out/'sheets'/(name+'.decision.json'),blank_sheet(dossier))
            index.append({'instrument_id':iid,'status':corpus['statuses'][iid], 'dossier':'dossiers/'+name+'.json','clauses':len(dossier['clauses']),'actors':len(acts),'missing':len(dossier['missing']),'conflicts':len(dossier['conflicts']),'fingerprint':dossier['fingerprint']})
        for actor in sorted(acting_used):
            # Not a segmentation: the frozen overlay selects an actor's held text by its CLAUSES source.
            line(cf,{'instrument_id':actor,'source':acting_selected[actor]['source'],'clauses':[],'role':ACTING_ROLE,
                     'method':'acting_text_not_segmented',
                     'notes':'Held text of a non-census acting instrument; context only, never an order or a clause inventory.'})
    decided=set(corpus['statuses']);family_rows=[]
    for key,ids in families.items():
        ids=sorted(ids&decided)
        if ids:family_rows.append({'family_id':key,'orders_unlocked':len(ids),'instrument_ids':ids})
    family_rows.sort(key=lambda x:(-x['orders_unlocked'],x['family_id']))
    # Same-actor single-clause tables are review conveniences, with blank decisions.
    for fam in family_rows:
        if not fam['family_id'].startswith('actor:'):continue
        members=[iid for iid in fam['instrument_ids'] if len(segments.get(iid,{}).get('clauses',[]))==1]
        if len(members)<2:continue
        actor=fam['family_id'].split(':',1)[1]
        with (out/(filename(actor)+'_BATCH_REVIEW.csv')).open('w',encoding='utf-8',newline='') as fh:
            w=csv.writer(fh);w.writerow(['instrument_id','dossier','scope_id','actor_id','state','end_id','effective_date','savings','reason','reviewer_decision'])
            for iid in members:
                w.writerow([iid,'dossiers/'+filename(iid)+'.json',segments[iid]['clauses'][0]['scope_id'],actor,'','','','','',''])
    dump(out/'INDEX.json',index);dump(out/'FAMILIES.json',family_rows)
    with ShardedJsonl(out/'MISSING_SOURCES.jsonl') as fh:
        for row in missing_sources:line(fh,row)
    # Assemble committed producer decision sheets. Never writes claims/, statuses, or reviews.
    assembly=[];accepted=0
    with ShardedJsonl(out/'ASSEMBLED_CLAIMS.jsonl') as fh:
        for path in sorted((repo/'research/readiness/decisions').glob('*/*.json')):
            try:
                sheet=json.loads(path.read_text('utf-8'))
                if not isinstance(sheet,dict):raise ValueError('Decision sheet must be a JSON object')
                iid=sheet.get('instrument_id')
                if not isinstance(iid,str):raise ValueError('Decision instrument_id must be a string')
                if iid not in corpus['statuses']:raise ValueError('No current provisional status for '+str(iid))
                dp=out/'dossiers'/(filename(iid)+'.json')
                dossier=json.loads(dp.read_text('utf-8'))
                claim,errors=assemble(sheet,dossier,repo)
                assembly.append({'sheet':str(path.relative_to(repo)),'instrument_id':iid,'errors':errors})
                if not errors:line(fh,claim);accepted+=1
            except (ValueError,KeyError,TypeError,OSError) as e:
                assembly.append({'sheet':str(path.relative_to(repo)),'errors':[type(e).__name__+': '+str(e)]})
    dump(out/'ASSEMBLY_REPORT.json',assembly)
    counts.update(dossiers=len(index),status_leads=len(universe)-len(decided),families=len(family_rows),assembled_claims=accepted)
    summary={'schema':'eo-claim-kit-summary/v1','counts':dict(sorted(counts.items())), 'historical_baseline':{'universe':14972,'decided':3359},'population':{'universe':len(universe),'decided':len(decided),'identity_sha256':canonical_sha(sorted(universe)),'status_sha256':canonical_sha(corpus['statuses'])},'warnings':warnings,'input_commit':os.environ.get('GITHUB_SHA'),'jsonl_shards':sorted(p.name for p in out.glob('*.jsonl')),'lead_only':True,'legal_cutoff':CUTOFF}
    summary['overlay_input_schema']='eo-claim-kit-overlay-input/v1'
    summary['compiled_code_sha256']={p:hashlib.sha256((Path(__file__).parent/p).read_bytes()).hexdigest()
        for p in COMPILER_FILES}
    summary['jsonl_shard_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.jsonl'))}
    dump(out/'SUMMARY.json',summary)
    dump(out/'METRICS.json',{'wall_seconds':round(time.monotonic()-started,3),'cache_hits':cache_hits,'output_bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file())})
    print(json.dumps(summary['counts'],sort_keys=True))
    return summary
