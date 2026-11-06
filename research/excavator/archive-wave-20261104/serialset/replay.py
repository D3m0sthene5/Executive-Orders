"""Reconstruct the held page PDFs/PNGs from exact public parent PDFs; no network.

Pass a directory holding the two complete GovInfo PDFs, named by
their SHA256 (optional .pdf suffix). The source sizes, images and parent hashes
come from the adjacent acquisition receipts and PAGE_PINS. Requires PyMuPDF
matching the version recorded there. Emit only in an empty output directory.
"""
import argparse,hashlib,json,pathlib
import fitz
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('parent_dir',type=pathlib.Path);a.add_argument('output',type=pathlib.Path);args=a.parse_args()
 src=pathlib.Path(__file__).resolve().parent; args.output.mkdir(parents=True,exist_ok=True)
 assert not any(args.output.iterdir()),'use empty output'
 pins=json.loads((src/'PAGE_PINS.json').read_text()); receipts=[json.loads(l) for l in (src/'SOURCE_ACQUISITION.jsonl').read_text().splitlines()]
 for r in receipts:
  parent=next((p for p in [args.parent_dir/r['sha256'],args.parent_dir/(r['sha256']+'.pdf')] if p.is_file()),None)
  if parent is None:raise FileNotFoundError(r['sha256'])
  raw=parent.read_bytes();assert len(raw)==r['bytes'] and sha(raw)==r['sha256']
  origin=fitz.open(stream=raw,filetype='pdf');frag=fitz.open()
  for row in (pin for pin in pins if pin['id']==r['id']):
   i=row['physical_page']-1;frag.insert_pdf(origin,from_page=i,to_page=i)
   out=args.output/row['filename'];origin[i].get_pixmap(matrix=fitz.Matrix(1.7,1.7)).save(out)
   assert sha(out.read_bytes())==row['sha256'],('renderer or source changed',out)
  name=r['id'].replace(':','_')+'_selected_pages.pdf';out=args.output/name;frag.save(out,garbage=4,deflate=True,no_new_id=True)
  assert out.read_bytes()==(src/name).read_bytes(),('PDF writer or source changed',out)
if __name__=='__main__':main()
