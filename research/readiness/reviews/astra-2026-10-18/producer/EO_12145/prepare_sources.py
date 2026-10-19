from pathlib import Path
from pypdf import PdfReader
import hashlib,json,re
out=Path(__file__).resolve().parent
rows=[json.loads(l) for l in Path('jobs/astra-source-retention/output/SOURCES.jsonl').read_text(encoding='utf-8').splitlines()]
manifest=[]
for suffix,label in [('STATUTE-60-Pg999.pdf','act1946'),('STATUTE-94-Pg2071.pdf','act1980')]:
    r=next(r for r in rows if r['url'].endswith(suffix));p=Path('jobs/astra-source-retention/output')/r['cache_path'];h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==r['sha256']
    reader=PdfReader(p);texts=[];sub=out/label;sub.mkdir()
    for i,page in enumerate(reader.pages,1):
        t=page.extract_text();texts.append(f'=== PDF page {i} ===\n'+t+'\n');(sub/f'page-{i}.txt').write_text(t,encoding='utf-8',newline='\n')
    full='\n'.join(texts);(sub/'full.txt').write_text(full,encoding='utf-8',newline='\n')
    manifest.append({'label':label,'source':r,'retained_pdf_path':p.as_posix(),'rehashed_sha256':h,'pdf_pages':len(reader.pages),'extraction':'pypdf text extraction, all pages; extraction/search does not mean all pages read','extracted_text_path':(sub/'full.txt').as_posix(),'extracted_text_sha256':hashlib.sha256((sub/'full.txt').read_bytes()).hexdigest()})
    print(label,'PAGES',len(reader.pages))
    for i,t in enumerate(texts,1):
        if any(re.search(q,t,re.I) for q in [r'SEC\.\s*2403',r'SEC\.\s*2401',r'CONTINU',r'SAVING',r'SEC\.\s*2205',r'95-317',r'94-350',r'12145',r'SEC\.\s*805',r'SEC\.\s*806']):print(label,i,t[:95].replace('\n',' '),[m.group(0) for m in re.finditer(r'continu\w*|saving\w*|12145|94-350|95-317|SEC\.\s*(?:2401|2403|2205|805|806)',t,re.I)])
(out/'statutory-extraction-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
