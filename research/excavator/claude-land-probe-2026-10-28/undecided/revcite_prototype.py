import re,sys,glob,os
root="/home/claude/d3m0sthene5/executive-orders"
targets={
 "6210":["July 22, 1933","6210"],"5511":["December 11, 1930","5511"],"5799":["February 15, 1932","February 13, 1932","5799"],
 "1237":["August 15, 1910","1237"],"2901":["July 2, 1918","2901"],"709":["November 9, 1907","November nine, nineteen hundred and seven"],
 "3853":["May 22, 1923","3853"],"7069":["June 11, 1935","7069","Power[- ]?Site Restoration No\\.? ?481"],"PSR325":["December 12, 1912","[Rr]eserve [Nn]o\\.? ?325"],
 "1304":["February 28, 1911","February 18, 1911","1304"],"1304parents":["February 27, 1874","June 12, 1900"],
 "6740":["June 15, 1934","6740","[Ww]ater [Rr]eserve [Nn]o\\.? ?155"],"4810":["February 14, 1928","4810"],"455":["June 6, 1906"]}
pats={k:[re.compile(p if not p.isdigit() else r"(?:No\.|Numbered|Order)\s*"+p+r"\b") for p in v] for k,v in targets.items()}
files=glob.glob(root+"/jobs/*/output/texts/**/*.txt",recursive=True)
for f in files:
    try: t=open(f,errors="ignore").read()
    except: continue
    t2=re.sub(r"\s+"," ",t)
    for k,ps in pats.items():
        for p in ps:
            for m in p.finditer(t2):
                print(k,"|",os.path.relpath(f,root),"|",t2[max(0,m.start()-120):m.end()+80])
                break
