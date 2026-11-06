import subprocess,csv,sys,collections
R='/home/user/Executive-Orders'; O=sys.argv[1]
def g(*a,inp=None): return subprocess.run(['git','-C',R,*a],input=inp,capture_output=True,check=True).stdout
ls=g('ls-files','-s','-z').split(b'\0')
rows=[]
for l in ls:
    if not l: continue
    meta,path=l.split(b'\t',1); mode,blob,_=meta.split()
    p=path.decode('utf8','surrogateescape')
    if p.lower().endswith('.pdf') and mode!=b'160000': rows.append((blob.decode(),p))
bl=sorted({b for b,_ in rows})
out=g('cat-file','--batch-check','--buffer',inp=('\n'.join(bl)+'\n').encode()).decode().split('\n')
size={}
for o in out:
    if o.strip():
        s=o.split(); size[s[0]]=int(s[2]) if s[1]=='blob' else -1
# LFS pointer detection for small blobs
ptr=set(); small=[b for b in bl if 0<=size[b]<300]
if small:
    d=g('cat-file','--batch','--buffer',inp=('\n'.join(small)+'\n').encode())
    import re
    for b in small:
        pass
    pos=0
    while pos<len(d):
        nl=d.index(b'\n',pos); h=d[pos:nl].split(); n=int(h[2]); body=d[nl+1:nl+1+n]; pos=nl+1+n+1
        if body.startswith(b'version https://git-lfs'): ptr.add(h[0].decode())
real=[(b,p) for b,p in rows if b not in ptr]
bydir=collections.defaultdict(lambda:[0,0]); alld=collections.defaultdict(lambda:[0,0])
for b,p in real:
    parts=p.split('/'); k='/'.join(parts[:2]) if len(parts)>2 else (parts[0] if len(parts)==2 else '(root)')
    bydir[k][0]+=1; bydir[k][1]+=size[b]
    d='/'.join(parts[:-1]) or '(root)'; alld[d][0]+=1; alld[d][1]+=size[b]
with open(O+'/PDF_BYTES_BY_DIR.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['kind','dir','pdf_files','bytes'])
    for k,v in sorted(bydir.items(),key=lambda x:-x[1][1]): w.writerow(['top2',k,*v])
    for k,v in sorted(alld.items(),key=lambda x:-x[1][1])[:30]: w.writerow(['top30_exact_dir',k,*v])
grp=collections.defaultdict(list)
for b,p in real: grp[b].append(p)
dups=[(b,size[b],len(ps),sorted(ps)) for b,ps in grp.items() if len(ps)>1]
dups.sort(key=lambda x:-(x[2]-1)*x[1])
with open(O+'/DUPLICATE_PDFS.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['blob','size','copies','redundant_bytes','paths'])
    for b,s,c,ps in dups: w.writerow([b,s,c,(c-1)*s,' | '.join(ps)])
tot=sum(size[b] for b,_ in real); red=sum((c-1)*s for _,s,c,_ in dups)
print('pdf entries',len(rows),'lfs ptr',len(ptr),'real',len(real),'bytes',tot,'unique blobs',len(grp),'unique bytes',sum(size[b] for b in grp))
print('dup groups',len(dups),'redundant files',sum(c-1 for _,_,c,_ in dups),'redundant bytes',red)
for pre in ['research/excavator/','jobs/astra-source-retention/']:
    n=[d for d in dups if any(p.startswith(pre) for p in d[3])]
    print(pre,'groups touching',len(n),'redundant',sum((c-1)*s for _,s,c,_ in n))
# cross-dir pattern: groups with copies in multiple top2
mix=collections.Counter()
for b,s,c,ps in dups:
    mix[tuple(sorted({'/'.join(p.split('/')[:2]) for p in ps}))]+=(c-1)*s
for k,v in mix.most_common(12): print(v,k)
print(sorted(set(size[b] for b in ptr)) if ptr else 'no ptr', 'zero/neg',[b for b in bl if size[b]<=0][:3])
