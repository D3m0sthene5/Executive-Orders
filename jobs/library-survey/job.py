"""Measured legal-source PDF processing pilot; no original modified."""
import csv,hashlib,io,json,os,subprocess,sys
from pathlib import Path
from importlib import metadata
ROOT=Path(os.environ.get("REPO_ROOT",Path(__file__).resolve().parents[2]))
OUT=Path(os.environ.get("OUTPUT_DIR",Path(__file__).parent/"output"))
def sha(b):return hashlib.sha256(b).hexdigest()
def ocr_needed(a,b,image):return bool(image) and max(len((a or "").strip()),len((b or "").strip()))<80
def candidates(root,limit):
 a=sorted((root/"research/stage18/sources").glob("*.pdf"),key=lambda p:(not p.name.startswith("USREPORTS"),p.name))
 return (a+sorted((root/"research/stage21/original_sources").glob("EO_*.pdf")))[:limit]
def version(n):
 try:return metadata.version(n)
 except metadata.PackageNotFoundError:return "not_installed"
def run(root=ROOT,out=OUT,limit=20,pages_limit=2,ocr_limit=4):
 from pypdf import PdfReader,PdfWriter
 import pdfplumber
 from eyecite import get_citations,clean_text
 if limit<=0 or pages_limit<=0:raise ValueError("Positive bounds required")
 inputs=candidates(root,limit)
 if not inputs:raise RuntimeError("No authentic preserved Stage18/21 PDF files in checkout")
 out.mkdir(parents=True,exist_ok=True)
 for n in ("texts","ocr"): (out/n).mkdir(exist_ok=True)
 pages=[];citations=[];ocr=[];fail=[];sources=[]
 for i,path in enumerate(inputs):
  rel=path.relative_to(root).as_posix()
  try:
   orig=path.read_bytes()
   if not orig.startswith(b"%PDF-") or len(orig)>65_000_000:raise ValueError("Invalid or oversized original PDF")
   digest=sha(orig);reader=PdfReader(io.BytesIO(orig),strict=False)
   with pdfplumber.open(path) as book:
    for pi in range(min(len(reader.pages),len(book.pages),pages_limit)):
     page=reader.pages[pi];pl=book.pages[pi]
     text1=page.extract_text() or "";text2=pl.extract_text(layout=True) or ""
     txt=text2 if len(text2.strip())>len(text1.strip()) else text1
     reltxt="texts/"+str(i).zfill(3)+"_"+str(pi+1).zfill(3)+".txt"
     (out/reltxt).write_text(txt,encoding="utf-8")
     try:img=bool(page.images)
     except Exception:img=False
     needed=ocr_needed(text1,text2,img)
     pages.append(dict(file=rel,original_sha256=digest,page=pi+1,pypdf_characters=len(text1),
      pdfplumber_characters=len(text2),selected_text_path=reltxt,selected_text_sha256=sha(txt.encode()),
      word_boxes=len(pl.extract_words()),has_image=img,needs_ocr=needed,status="unverified_extraction"))
     cleaned=clean_text(txt,["inline_whitespace"])
     for cit in get_citations(cleaned):
      try:start,end=cit.span()
      except Exception:continue
      if 0<=start<end<=len(cleaned):
       citations.append(dict(file=rel,page=pi+1,source_sha256=digest,exact_text=cleaned[start:end],
        citation_type=type(cit).__name__,start=start,end=end,role="reporter_lead_not_legal_finding"))
     if needed and len(ocr)<ocr_limit:
      writer=PdfWriter();writer.add_page(page);buffer=io.BytesIO();writer.write(buffer)
      inp=out/"ocr"/("page_"+str(i)+"_"+str(pi+1)+".source.pdf")
      dst=out/"ocr"/("page_"+str(i)+"_"+str(pi+1)+".ocr.pdf")
      side=out/"texts"/("ocr_"+str(i)+"_"+str(pi+1)+".txt")
      inp.write_bytes(buffer.getvalue())
      try:
       args=["ocrmypdf","-l","eng","--skip-text","--output-type","pdf","--optimize","0","--sidecar",str(side),str(inp),str(dst)]
       p=subprocess.run(args,capture_output=True,text=True,timeout=180)
       success=p.returncode==0 and dst.is_file();error=p.stderr[-400:] if p.returncode else ""
      except (subprocess.TimeoutExpired,FileNotFoundError) as e:success=False;error=str(e)
      recovered=side.read_text(encoding="utf-8",errors="replace") if success and side.exists() else ""
      ocr.append(dict(file=rel,page=pi+1,original_sha256=digest,success=success,
       recovered_characters=len(recovered),ocr_derivative_sha256=sha(dst.read_bytes()) if success else "",
       derivative_path=dst.relative_to(out).as_posix() if success else "",error=error,original_unchanged=True))
      inp.unlink(missing_ok=True)
   sources.append(dict(path=rel,original_sha256=digest,bytes=len(orig),original_saved_in_project=True))
  except Exception as e:fail.append(dict(path=rel,error=type(e).__name__+": "+str(e)[:160]))
 def save_csv(n,rows,columns):
  with (out/n).open("w",encoding="utf-8",newline="") as f:
   w=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore");w.writeheader();w.writerows(rows)
 save_csv("PAGE_COMPARE.csv",pages,["file","original_sha256","page","pypdf_characters","pdfplumber_characters","selected_text_path","selected_text_sha256","word_boxes","has_image","needs_ocr","status"])
 save_csv("CITATION_LEADS.csv",citations,["file","page","source_sha256","exact_text","citation_type","start","end","role"])
 save_csv("OCR_DERIVATIVES.csv",ocr,["file","page","original_sha256","success","recovered_characters","ocr_derivative_sha256","derivative_path","error","original_unchanged"])
 (out/"SOURCE_CUSTODY.jsonl").write_text("".join(json.dumps(v,sort_keys=True)+"\n" for v in sources))
 summary=dict(input_PDFs=len(inputs),PDFs_processed=len(sources),pages_processed=len(pages),
  layout_method_longer_pages=sum(z["pdfplumber_characters"]>z["pypdf_characters"] for z in pages),
  pages_needing_OCR=sum(z["needs_ocr"] for z in pages),OCR_attempts=len(ocr),
  OCR_successes=sum(z["success"] for z in ocr),OCR_recovered_characters=sum(z["recovered_characters"] for z in ocr),
  reporter_citation_leads=len(citations),errors=fail,
  libraries={z:version(z) for z in ("pypdf","pdfplumber","eyecite","ocrmypdf")},original_PDFs_modified=0,
  legal_statuses_changed=0,independent_human_approvals=0)
 (out/"SUMMARY.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
 (out/"REPORT.md").write_text("# PDF and reporter-citation pilot\n\nOriginal PDFs processed: "+str(summary["PDFs_processed"])+
  "; pages compared: "+str(summary["pages_processed"])+
  "; layout method longer on "+str(summary["layout_method_longer_pages"])+
  " pages; OCR successful on "+str(summary["OCR_successes"])+"/"+str(summary["OCR_attempts"])+
  " pages with "+str(summary["OCR_recovered_characters"])+" recovered characters; "+
  str(summary["reporter_citation_leads"])+" reporter-citation leads. All machine findings are unverified.\n")
 print(json.dumps(summary,indent=2))
if __name__=="__main__":
 t=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(Path(__file__).parent),"-p","test_*.py"])
 if t.returncode:raise SystemExit("Library tests failed, no output promoted")
 run(limit=int(os.getenv("LIBRARY_PDF_LIMIT","20")),pages_limit=int(os.getenv("LIBRARY_MAX_PAGES","2")),ocr_limit=int(os.getenv("LIBRARY_OCR_MAX_PAGES","4")))
