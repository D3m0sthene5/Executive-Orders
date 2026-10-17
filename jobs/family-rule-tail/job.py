"""Recover EO 11490's revocation section after a bounded extract stopped too early."""
import hashlib,json,os,runpy,sys
from pathlib import Path
root=Path(os.environ['REPO_ROOT']);out=Path(os.environ['OUTPUT_DIR'])
sys.path.insert(0,str(root/'jobs/source-ladder'))
os.environ.update(JOB_ONLY='queue:EO:11490:',JOB_MAX_REQUESTS='10',JOB_CARRY_FORWARD='0')
runpy.run_path(str(root/'jobs/source-ladder/job.py'),run_name='__main__')
from pypdf import PdfReader
cache=Path(os.environ.get('JOB_CACHE_DIR') or out.parent/(os.environ['JOB_NAME']+'-cache'))
sources=[json.loads(s) for s in (out/'SOURCES.jsonl').read_text().splitlines() if s]
for s in sources:
    pdf=cache/s['cache_path']
    if hashlib.sha256(pdf.read_bytes()).hexdigest()!=s['sha256']:raise ValueError('PDF custody hash mismatch')
    reader=PdfReader(pdf)
    text='\n'.join(f'=== PDF page {i+1} of {len(reader.pages)} ===\n'+(reader.pages[i].extract_text() or '') for i in range(62,len(reader.pages)))
    if '3015' not in text or 'revoked' not in text.lower():raise ValueError('Revocation section not recovered')
    rel='texts/EO_11490_tail.txt';(out/rel).write_text(text,encoding='utf-8',newline='\n')
    s.update(text_path=rel,page_or_item='34 FR 17567 onward, PDF pages 63-96; includes Section 3015 and any following material',notes='Full remaining issue extract; boundaries need review; source PDF SHA-256 verified by job')
(out/'SOURCES.jsonl').write_text(''.join(json.dumps(s,sort_keys=True)+'\n' for s in sources),encoding='utf-8',newline='\n')
