"""Build TRACE.jsonl and ORDER_OUTCOMES.csv for H4 from the launcher log, worker registry and recorded outcomes.
Coordinator tool; outcomes are those recorded with outcome.py (worker results read by the coordinator) plus the
deterministic coordinator outcomes defined in COORD below."""
import csv, json, re
from pathlib import Path
R=Path('/home/claude/executive-orders'); H=R/'research/herschel/H4'
S=Path('/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H4')
W=json.loads((S/'workers.json').read_text()); O=json.loads((S/'outcomes.json').read_text())
ORD={r['instrument_id']:r for r in csv.DictReader(open(R/'research/herschel/frame/ORDERS.csv',encoding='utf-8'))}
A=json.load(open(R/'research/herschel/frame/ASSIGNMENTS.json'))
mine=[c for c in A['coordinators'] if c['name']=='H4'][0]['orders']
STEP={'status_producer':'provisional_status','original_text':'original_text','producer':'lifecycle','producer_overlay':'lifecycle','status_reviewer':'review','reviewer':'review'}
MODEL={'status_producer':'sonnet','original_text':'sonnet','producer':'sonnet','producer_overlay':'sonnet','status_reviewer':'opus','reviewer':'opus'}
log=(H/'COORDINATOR_LOG.txt').read_text().splitlines()
ev={}
for l in log:
    m=re.match(r'(H4-w\d+)(-[a-z0-9]+)? (sonnet|opus) (?:resume \S+ )?launched (\S+) h4_concurrent=(\d+) claude_p_all=(\d+) memavail=(\d+)MB',l)
    if m:
        e=ev.setdefault(m.group(1),{'runs':[]}); e['runs'].append({'part':(m.group(2) or '-initial')[1:],'launched':m.group(4),'h4':int(m.group(5)),'all':int(m.group(6)),'mem':int(m.group(7))})
    m=re.match(r'(H4-w\d+)(-[a-z0-9]+)? done (\S+) rc=(\d+)',l)
    if m and m.group(1) in ev: ev[m.group(1)]['runs'][-1]['ended']=m.group(3); ev[m.group(1)]['runs'][-1]['rc']=int(m.group(4))
    m=re.match(r'(H4-w\d+)(-[a-z0-9]+)? (\S+) cost (\S+) turns (\S+)',l)
    if m and m.group(1) in ev and ev[m.group(1)]['runs']: ev[m.group(1)]['runs'][-1].update({'session':m.group(3),'cli_cost_usd_cumulative':float(m.group(4)),'turns':m.group(5)})
    m=re.match(r'MEMGUARD (H4-w\d+)(-[a-z0-9]+)? (\S+) h4_busy=(\d+) claude_p_all=(\d+) memavail=(\d+)MB',l)
    if m: ev.setdefault(m.group(1),{'runs':[]}).setdefault('memguard',[]).append(f"MEMGUARD {m.group(3)} {m.group(2) or ''} h4_busy={m.group(4)} claude_p_all={m.group(5)} memavail={m.group(6)}MB".replace('  ',' '))
REV=json.loads((S/'review_outcomes.json').read_text()) if (S/'review_outcomes.json').exists() else {}
trace=[]
for w in sorted(W,key=lambda x:int(x.split('w')[1])):
    t=W[w]['template']; e=ev.get(w,{'runs':[]}); runs=[r for r in e['runs'] if 'launched' in r and r['launched']>='2026-11-06T00:05:00Z']  # drop the 00:04 zero-token launch failures
    if not runs: continue
    outs=O.get(w,{}).get('outcomes',{})
    oc={}
    for k,v in outs.items():
        o=k.split('|')[0]
        if '|' in k:
            prev=oc.get(o,'done'); oc[o]=v if (prev=='done' and v!='done') else prev
        else: oc[o]=v
    oc.update(REV.get(w,{}))
    for o in W[w]['orders']: oc.setdefault(o,'not_recorded')
    trace.append({'worker':w,'step':STEP[t],'model':MODEL[t],'stratum':'|'.join(sorted({ORD[o]['stratum'] for o in W[w]['orders']})),
      'orders':W[w]['orders'],'started_utc':runs[0]['launched'],'ended_utc':runs[-1].get('ended'),
      'concurrent_workers_at_start':runs[0]['h4'],'machine_claude_p_at_start':runs[0]['all'],'memavail_mb_at_start':runs[0]['mem'],
      'limit_events':e.get('memguard',[]),'oom_rerun':False,
      'runs':[{k:r.get(k) for k in ('part','launched','ended','session','turns','cli_cost_usd_cumulative','h4','all')} for r in runs],
      'outcomes':oc})
with open(H/'TRACE.jsonl','w',encoding='utf-8') as f:
    for t in trace: f.write(json.dumps(t,ensure_ascii=False)+'\n')
# ORDER_OUTCOMES: one row per order and step
by={}  # (order,step) -> (outcome, worker)
for w,e in O.items():
    for k,v in e['outcomes'].items():
        if '|' in k: o,s=k.split('|')
        else: o,s=k,e['step']
        by[(o,s)]=(v,w)
for w,d in REV.items():
    for o,v in d.items(): by[(o,'review')]=(v,w)
C=json.loads((S/'coord_outcomes.json').read_text())
for k,v in C.items():
    if k.startswith('_'): continue
    o,s=k.split('|'); by.setdefault((o,s),(v,'H4-coordinator'))
rows=[]
for o in mine:
    steps=ORD[o]['open_steps'].split('|')+['review']
    if o in C.get('_replace',[]) or ORD[o]['transcription_dependent']=='True': steps.append('replace_original')
    for s in steps:
        v,w=by.get((o,s),('not_reached',''))
        rows.append({'instrument_id':o,'stratum':ORD[o]['stratum'],'step':s,'outcome':v,'worker':w})
with open(H/'ORDER_OUTCOMES.csv','w',newline='',encoding='utf-8') as f:
    x=csv.DictWriter(f,fieldnames=['instrument_id','stratum','step','outcome','worker']); x.writeheader(); x.writerows(rows)
print(len(trace),'trace lines;',len(rows),'outcome rows;',sum(r['outcome']=='not_reached' for r in rows),'not_reached')
