"""Restore temporary execution paths from the existing retained source store.

No download or source transformation. Renders only requested original PDF pages.
"""
import hashlib,json,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent
ROOT=R.parents[2]
def main():
    store=ROOT/'jobs/astra-source-retention/output'
    rows=[json.loads(x) for x in (R/'acquisition/SOURCES.jsonl').read_text().splitlines()]
    for d in rows:
        for k in ('cache_path','text_path'):
            src=store/d[k];dst=R/'acquisition'/d[k]
            dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists():
                if dst.read_bytes()!=src.read_bytes():raise ValueError('Refusing overwrite:'+str(dst))
            else:shutil.copyfile(src,dst)
    sample=json.loads((R/'SAMPLE_PAGE_MAP.json').read_text())
    for d in sample:
        image=ROOT/d['primary_page_png']
        page=int(image.stem.split('-')[-1])
        image.parent.mkdir(parents=True,exist_ok=True)
        if not image.exists():
            subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-r','120','-png','-singlefile',
                            str(store/'pdf'/(d['source_sha256']+'.pdf')),str(image.with_suffix(''))],check=True)
    print('Restored exact source paths and re-rendered page views. Pixel hashes may depend on renderer version.')
if __name__=='__main__':main()
