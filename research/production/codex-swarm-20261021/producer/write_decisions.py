"""Reproduce explicit producer decisions, including three blocked members. No publication."""
from pathlib import Path
import csv,json,re,hashlib
ROOT=Path(__file__).resolve().parents[4]
BASE=Path(__file__).resolve().parent
AGENT='codex-swarm-producer'
def rows(p):return list(csv.DictReader(p.open()))
def write(p,rs):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
blocks={
 'EO:11088':'The complete original assigns Treasury narcotics administration in section 2(12) and Coast Guard functions in section 2(16). EO 11490 section 101 explicitly says assignments were adjusted for intervening organization changes, and section 301 no longer includes those functions. The exact earlier transfer instruments, savings, and effective dates must be examined before asserting a common 1969 first cessation. No transfer date is established in this pilot.',
 'EO:11090':'The complete original section 3(d) includes civil-aircraft accident investigation and section 1 includes that function. EO 11490 section 101 warns of intervening organization changes. The possible Department of Transportation/NTSB transfer is an unresolved earlier-end lead; acquire/read the controlling instrument and distinguish transfer of function from cessation of this order before assigning first ends. No transfer date is established here.',
 'EO:11092':'Original section 9 expressly keeps telecommunications orders issued under EO 10705, EO 10995 and EO 11051 or their predecessors in force, except inconsistencies. Their exact survival/independent authority and any earlier changes need source reconciliation. A common EO11490 revocation cannot by itself close this savings question.'}
for folder in ['packet-v1','packet-cab-v1','packet-fcc-v1']:
 p=BASE/folder; rs=rows(p/'decisions.csv'); old=rows(p/'clauses.csv'); cs=[]
 for r in rs:
  iid=r['instrument_id']; n=iid.split(':')[1]
  if iid in blocks:
   r.update(outcome='blocked',approved='false',research_rationale=blocks[iid],unresolved_material_gaps=json.dumps([blocks[iid]]))
   cs += [c for c in old if c['instrument_id']==iid];continue
  d=json.loads((ROOT/'jobs/claim-kit/output/dossiers'/f'EO_{n}.json').read_text())
  end_id=next(k for k,v in d['evidence'].items() if k.startswith('ACT:') and '@' in k and v['source'].get('text_path','').endswith('EO_11490_tail.txt'))
  own='State Department' if n=='11087' else 'Atomic Energy Commission'
  sections=8 if n=='11087' else 7
  r.update(outcome='submit',approved='true',original_confirmed='true',original_pages_confirmed='true',inventory_confirmed='true',
   research_rationale=f'Producer-reviewed proposal only, not independent or human certification. The complete official original for {iid} assigns ongoing {own} preparedness functions and supporting coordination, research/evaluation, limits, and delegation. Its full sections 1–{sections} are retained in exact, disjoint inventory corrections because OCR segmentation omitted sections. The assignments are continuing capabilities, not a finite report or task. EO 11490 section 3015 names this order and immediately revokes it on 1969-10-28; section 3014 expressly excepts section 3015. Comparable functions under the new order derive from its new assignment, not survival of the old EO. The bounded held-source later-event search disclosed no earlier ending, revival, or current predicate for this order; that is a bounded research conclusion, not an exhaustive proof of every legal event.',
   savings_state='none_after_bounded_search',savings_source_id=end_id,
   savings_reason=f'EO11490 section 3014 begins Except as provided in Section 3015, so its retained-authority rule does not save this named revoked order. Original {iid} contains continuing preparedness assignments and a prior-inconsistency priority rule, not an express accrued-right or continuing-independent savings clause. Similar preparedness functions reissued under EO11490 are separately authorized. Historical plans and completed steps are not asserted to disappear, but no independently enforceable residual attributable to this EO was located in the bounded sources.',
   search_ids=json.dumps(['current-law:usc','current-law:ecfr','later-events:ofr_catalog']),
   earlier_end_check=f'Inspected every original section and the applicable EO11490 parts/general provisions, and read both held OFR edge records for {iid}. Both identify only EO11490. No fixed sunset, performance-triggered whole-order end, or earlier actor appears. The source directs an integral part of continuing activities; completing a plan or an installment cannot discharge the standing readiness duty. The U.S.Code search stops at 2026-10-09 and is used only as corroborating bounded counterevidence, not a claimed YES predicate through the cutoff.',
   scope_check=f'All {sections} original sections are copied in full, including originally missed scope/evaluation/emergency-authority restrictions. EO11490 section 3015 contains no partial qualifier for {iid}. Section 3014 excludes the named revocations from retained authority.',
   independent_command_check=f'Original sections require continuing preparedness, research, coordination/evaluation and readiness, with delegation and implementation limits tied to those functions. None commands a one-off report or a completed event whose occurrence would establish an earlier independent first end. All subparts are included, not discarded as boilerplate.',
   savings_check='Read original prior-actions rule and EO11490 sections 3011–3015. Section 3014 does not override 3015. Separate statutory powers and functions newly assigned by EO11490 are distinguished from continued force of this order.')
  text=d['evidence'][d['original_source_id']]['text']
  # Boundaries manually selected from the complete originals and checked page images.
  starts=[text.index('S ectio n 1.') if n=='11087' else text.index('S ection  1.')]
  for s in range(2,sections+1):
   pattern=r'(?m)^(?:Sec\.|Sic\.) '+str(s)+r'\.'
   m=re.search(pattern,text);assert m,(iid,s);starts.append(m.start())
  last=text.index('J o h n F. K e n n e d y') if n=='11087' else text.index('J ohn F. Kennedy')
  ends=starts[1:]+[last]
  for s,(a,b) in enumerate(zip(starts,ends),1):
   c={k:'' for k in old[0]};c.update(instrument_id=iid,scope_id=f'{iid}#verified-section-{s}',state='terminated',end_id=end_id,effective_date='1969-10-28',effective_date_confirmed='true',later_event_ids='[]',later_events='[]',
    reason=f'Complete original section {s}, including its subparts and qualifications. This is part of the standing preparedness regime, not a finite completion obligation. Named whole-order revocation in EO11490 section 3015 ends this EO as source on signing; no deferred effective date or earlier cessation was found in the bounded sources. Continuing functions under EO11490 have a separate source.',
    inventory_source_id=d['original_source_id'],inventory_char_start=str(a),inventory_char_end=str(b),inventory_reason='Page-verified complete section inventory replaces incomplete OCR segmentation; exact held-text offsets preserve all operative section text and subparts.')
   cs.append(c)
 write(p/'decisions.csv',rs);write(p/'clauses.csv',cs)
