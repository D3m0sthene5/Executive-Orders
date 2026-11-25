"""Decode browser chunk dumps (#BB k ... #EB k) into ProQuest replica PDFs; verify sha256; delete consumed dumps."""
import base64, glob, hashlib, json, os, re, sys, time
OUT = '/home/claude/d3m0sthene5/executive-orders/research/pre-1937-sources/ProQuest Pre-1937 Orders'
MAN = '/home/claude/bartolus-scr/hv/manifest.jsonl'
PARTS = '/home/claude/bartolus-scr/hv/parts'
os.makedirs(PARTS, exist_ok=True)
done = set()
if os.path.exists(MAN):
    for l in open(MAN): done.add(json.loads(l)['acc'])
def text_of(p):
    s = open(p, encoding='utf-8', errors='replace').read()
    try:
        d = json.loads(s)
        if isinstance(d, list): return ''.join(x.get('text', '') for x in d)
    except Exception: pass
    return s
def handle(p):
    s = text_of(p)
    got = 0
    for m in re.finditer(r'#BB (\d+)\n(.*?)\n#EB \1', s, re.S):
        body = m.group(2)
        for rec in re.finditer(r'@@PDF (\S+) ([0-9a-f]{64}) (\d+) (\d+)/(\d+)\n([A-Za-z0-9+/=\n]*)', body):
            acc, sha, ln, i, n, b64 = rec.groups()
            data = base64.b64decode(b64.replace('\n', ''))
            open(f'{PARTS}/{acc}.{i}', 'wb').write(data)
            parts = [f'{PARTS}/{acc}.{j}' for j in range(1, int(n) + 1)]
            if all(os.path.exists(x) for x in parts):
                raw = b''.join(open(x, 'rb').read() for x in parts)
                ok = hashlib.sha256(raw).hexdigest() == sha and len(raw) == int(ln)
                if ok and acc not in done:
                    y, _, num = acc.split('-', 2)
                    fn = f'PT1-{y}-EO-{num.upper()}.pdf'
                    open(f'{OUT}/{fn}', 'wb').write(raw)
                    open(MAN, 'a').write(json.dumps({'acc': acc, 'file': fn, 'sha256': sha, 'bytes': len(raw)}) + '\n')
                    done.add(acc)
                elif not ok:
                    open('/home/claude/bartolus-scr/hv/bad.txt', 'a').write(acc + '\n')
                for x in parts: os.remove(x)
            got += 1
    return got
loop = '--loop' in sys.argv
while True:
    for p in glob.glob('/tmp/claude-tool-results/*/*.txt'):
        try:
            if time.time() - os.path.getmtime(p) < 20: continue
            if '#BB ' not in open(p, errors='replace').read(2000): continue
        except Exception: continue
        try:
            n = handle(p)
            if n: os.remove(p)
        except Exception as e:
            print('ERR', p, e, flush=True)
    if not loop: break
    time.sleep(15)
    if os.path.exists('/home/claude/bartolus-scr/hv/STOP'): break
print('decoded', len(done))
