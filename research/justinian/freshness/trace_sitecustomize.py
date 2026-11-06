import sys, os, atexit
_reads=set(); _lists=set()
def _hook(ev, args):
    try:
        if ev == 'open':
            p=args[0]
            if isinstance(p,(str,bytes,os.PathLike)) and not isinstance(p,int):
                mode=args[1] if len(args)>1 else 'r'
                _reads.add((os.fsdecode(p), str(mode)))
        elif ev in ('os.scandir','os.listdir'):
            p=args[0] if args else '.'
            if p is None: p='.'
            if not isinstance(p,int): _lists.add(os.fsdecode(p))
        elif ev == 'glob.glob':
            _lists.add('GLOB:'+str(args[0]))
    except Exception: pass
sys.addaudithook(_hook)
def _dump():
    t=os.environ.get('TRACE_FILE')
    if not t: return
    with open(t+f'.{os.getpid()}','w') as f:
        for p,m in sorted(_reads): f.write(f'R\t{m}\t{os.path.abspath(p)}\n')
        for p in sorted(_lists): f.write(f'L\t\t{p if p.startswith("GLOB:") else os.path.abspath(p)}\n')
atexit.register(_dump)
