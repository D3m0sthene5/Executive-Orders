"""Dorotheus worker scheduler (coordinator tool). Keeps at most 8 headless workers running.
Reads /tmp/claude-0/dorotheus-wave/queue.txt lines 'NAME MODEL PROMPTFILE'; launches each once via launch.sh,
in queue order, when fewer than 8 are running and the logged spend is under the $400 cap. Writes
scheduler.state (launched names). Stops new dispatch (logging why) at the cap."""
import re, subprocess, time
from pathlib import Path
E = Path('/tmp/claude-0/dorotheus-wave'); L = Path(__file__).resolve().parent / 'launch.sh'
CAP, MAXW = 400.0, 8
running = {}
done = set((E / 'scheduler.state').read_text().split()) if (E / 'scheduler.state').exists() else set()
def spent():
    return sum(float(m) for m in re.findall(r' cost=([0-9.]+)', (E / 'COORDINATOR_LOG.txt').read_text()))
capped = False
while True:
    for n, p in list(running.items()):
        if p.poll() is not None: running.pop(n)
    log = (E / 'COORDINATOR_LOG.txt').read_text()
    live = set(re.findall(r'^LAUNCH (\S+)', log, re.M)) - set(re.findall(r'^DONE (\S+)', log, re.M))
    q = [l.split() for l in (E / 'queue.txt').read_text().splitlines() if l.strip()] if (E / 'queue.txt').exists() else []
    for name, model, prompt in q:
        if name in done or len(live | set(running)) >= MAXW: continue
        if spent() >= CAP:
            if not capped:
                with open(E / 'COORDINATOR_LOG.txt', 'a') as f: f.write(f'BUDGET CAP reached (${spent():.2f} >= ${CAP}); no new dispatches\n')
            capped = True; break
        running[name] = subprocess.Popen(['bash', str(L.parent / 'resume.sh'), name, model.split(':', 1)[1], prompt] if model.startswith('resume:') else ['bash', str(L), name, model, prompt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        live.add(name); done.add(name); (E / 'scheduler.state').write_text('\n'.join(sorted(done)) + '\n')
    (E / 'scheduler.running').write_text('\n'.join(sorted(running)) + '\n')
    if (E / 'scheduler.stop').exists() and not running: break
    time.sleep(15)
