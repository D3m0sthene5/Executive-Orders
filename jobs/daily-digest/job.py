"""Daily bounded operational digest, generated without model calls."""
from __future__ import annotations
import datetime as dt, json, os, subprocess
from pathlib import Path

def load(p):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError):return {}
def previous(root,day):
    # Use the last committed snapshot before today's New York date; repeated runs are stable.
    cutoff=dt.datetime.combine(day,dt.time(),tzinfo=__import__('zoneinfo').ZoneInfo('America/New_York')).isoformat()
    r=subprocess.run(['git','log','-1','--format=%H','--before='+cutoff,'--','jobs/daily-digest/output/SNAPSHOT.json'],cwd=root,capture_output=True,text=True)
    if not r.stdout.strip():return {}
    p=subprocess.run(['git','show',r.stdout.strip()+':jobs/daily-digest/output/SNAPSHOT.json'],cwd=root,capture_output=True,text=True)
    try:return json.loads(p.stdout)
    except ValueError:return {}
def build(root,day,old):
    tracker=root/'jobs/readiness-tracker/output/TRACKER.md'
    headline=tracker.read_text(encoding='utf-8').splitlines() if tracker.exists() else ['Tracker unavailable.']
    summaries={p.parent.parent.name:load(p) for p in sorted((root/'jobs').glob('*/output/SUMMARY.json'))}
    snapshot={'date':day.isoformat(),'summaries':summaries}
    lines=['# Daily research digest', '',f'New York date: {day.isoformat()}. Generated mechanically; all findings remain provisional.','', '## Tracker headline','']
    lines+=headline[:18]
    lines+=['','## Changes since the previous day','']
    if not old:lines+=['No earlier daily snapshot is available; this run establishes the baseline.']
    else:
        lines += [f"Comparison snapshot: {old.get('date','unknown')}; intervening runs may be absent."]
        for name,new in summaries.items():
            prev=old.get('summaries',{}).get(name,{})
            changes=[f'{k}: {prev.get(k,"unavailable")} → {v}' for k,v in sorted(new.items()) if isinstance(v,(int,float)) and not isinstance(v,bool) and v!=prev.get(k) and not any(t in k for t in ('second','elapsed','time'))]
            if changes:lines.append(f'- {name}: '+ '; '.join(changes[:4]))
    import csv
    lines+=['','## Top shared unlocks','']
    p=root/'jobs/readiness-tracker/output/SHARED_UNLOCKS.csv'
    if p.exists():
        with p.open(encoding='utf-8',newline='') as f:
            for row in list(csv.DictReader(f))[:7]:lines.append('- '+'; '.join(f'{k}: {v}' for k,v in row.items()))
    lines+=['','## Open asks from the newest handoff entries','']
    for p in sorted((root/'HANDOFF').glob('notes-*.md')):
        text=p.read_text(encoding='utf-8');parts=text.split('\n## ')
        newest=parts[1] if len(parts)>1 else text
        asks=[];inside=False
        for line in newest.splitlines():
            if '**Asks:**' in line:inside=True
            elif line.startswith('- **'):inside=False
            if inside:asks.append(line.strip())
        lines.append(f'- {p.name}: '+(' '.join(asks)[:1100] or 'No open ask recorded in newest entry.'))
    lines+=['','## Published output status','',
        'A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.']
    failed=[]
    for p in sorted((root/'jobs').glob('*/output/STATUS.json')):
        s=load(p)
        if s.get('result')!='succeeded':failed.append(f"- {p.parent.parent.name}: {s.get('result','unknown')} ({s.get('run_url','no run link')})")
    lines+=failed or ['No failed canonical output status is recorded; inspect retained attempts for newer failures.']
    if os.environ.get('GITHUB_RUN_ID') and os.environ.get('GITHUB_REPOSITORY'):
        run_url=f"{os.environ.get('GITHUB_SERVER_URL','https://github.com')}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
        lines.append(f'[Current workflow status and retained attempt artifacts]({run_url})')
    if len(lines)>149:lines=lines[:148]+['Additional items omitted to keep this operational digest below 150 lines.']
    return '\n'.join(lines)+'\n',snapshot

def main():
    root=Path(os.environ['REPO_ROOT']);out=Path(os.environ['OUTPUT_DIR'])
    from zoneinfo import ZoneInfo
    day=dt.datetime.now(ZoneInfo('America/New_York')).date()
    text,snapshot=build(root,day,previous(root,day))
    out.mkdir(parents=True,exist_ok=True)
    (out/'DIGEST.md').write_text(text,encoding='utf-8',newline='\n')
    (out/'SNAPSHOT.json').write_text(json.dumps(snapshot,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
if __name__=='__main__':main()
