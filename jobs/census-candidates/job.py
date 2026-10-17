"""Integrate actual ranger sources into a separate candidate, never the EO census."""
import csv,hashlib,json,os,re,subprocess,sys
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(os.environ.get("REPO_ROOT",Path(__file__).resolve().parents[2]))
OUT=Path(os.environ.get("OUTPUT_DIR",Path(__file__).parent/"output"))
INPUTS={
 "curated":"research/stage22/CANDIDATE_DIRECTIVES.json",
 "item_metadata":"jobs/early-ranger-original-items/output/PRIMARY_ITEM_METADATA.jsonl",
 "transcriptions":"jobs/early-ranger-transcriptions/output/TRANSCRIPTION_INVENTORY.jsonl",
 "page_images":"jobs/early-ranger-full-pages/output/PAGE_IMAGE_CUSTODY.csv",
 "loc_reparse":"jobs/early-ranger-reparse/output/LOC_MANUSCRIPT_CANDIDATES.csv",
 "loc_triage":"jobs/early-ranger-triage/output/PRIORITIZED_PRESIDENTIAL_PERIOD_CANDIDATES.csv",
 "lord":"research/stage14/LORD/LORD_CHRONOLOGICAL_REVIEW_LEADS.csv",
 "lord19":"jobs/early-ranger-1862-1906/output/UNAUTHENTICATED_19C_LORD_DATE_LEADS.csv",
 "early_sources":"research/stage18/data/EARLY_SOURCE_CANDIDATES.csv",
 "census":"research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"}
def read_csv(path):
 with path.open(encoding="utf-8-sig",newline="") as f: yield from csv.DictReader(f)
def lines(path):
 for line in path.read_text(encoding="utf-8").splitlines():
  if line.strip():yield json.loads(line)
def hashfile(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def item_id(url):
 try:
  u=urlparse(url)
  if u.netloc.lower() not in ("www.loc.gov","loc.gov"):return None
  x=re.fullmatch(r"/item/([A-Za-z0-9_-]+)/?",u.path)
  return x.group(1).lower() if x else None
 except (TypeError,ValueError):return None
def build(root=ROOT,out=OUT):
 paths={k:root/v for k,v in INPUTS.items()}
 required=("curated","item_metadata","page_images","lord","early_sources","census")
 absent=[k for k in required if not paths[k].is_file()]
 if absent:raise RuntimeError("Required source inputs missing: "+",".join(absent))
 out.mkdir(parents=True,exist_ok=True)
 records={}
 def grab(key):
  if not key:return None
  return records.setdefault(key,dict(candidate_id="LOC:"+key,url="https://www.loc.gov/item/"+key+"/",titles=[],dates=[],source_paths=[],transcription=None,original_pages=[],research_cues=[],identity_status="not_reconciled",census_membership="NOT_ADMITTED",legal_inclusion="HOLD",human_certified=False))
 def put(row,origin,title="",date=""):
  if title and title not in row["titles"]:row["titles"].append(title)
  if date and date not in row["dates"]:row["dates"].append(date)
  if origin not in row["source_paths"]:row["source_paths"].append(origin)
 for k,colurl,coltitle,coldate in (("loc_reparse","loc_item_https","title","catalog_date"),("loc_triage","catalog_item_url","title_as_indexed","date_as_indexed")):
  if paths[k].is_file():
   for v in read_csv(paths[k]):
    row=grab(item_id(v.get(colurl,"")))
    if row:put(row,INPUTS[k],v.get(coltitle,""),v.get(coldate,""))
 for v in lines(paths["item_metadata"]):
  row=grab(v.get("catalog_item_id") or item_id(v.get("url","")))
  if row:
   put(row,INPUTS["item_metadata"],v.get("official_item_title",""),v.get("item_date",""))
   row["LOC_metadata_sha256"]=v.get("source_metadata_sha256","")
   row["item_metadata_retrieved"]=v.get("status")=="official_item_JSON_retrieved"
 for v in lines(paths["transcriptions"]) if paths["transcriptions"].is_file() else []:
  row=grab(v.get("catalog_item_id"))
  if row:
   row["transcription"]={"source_xml_sha256":v.get("sha256"),"repo_path":"jobs/early-ranger-transcriptions/output/"+str(v.get("transcript_path","")),"word_count":v.get("transcript_word_count"),"grade":"UNREVIEWED_XML_TRANSCRIPTION"}
   put(row,INPUTS["transcriptions"])
 for v in read_csv(paths["page_images"]):
  row=grab(v.get("catalog_item"))
  if row and v.get("source_state")=="original_page_JPEG_bytes_acquired":
   path="jobs/early-ranger-full-pages/output/"+v["stored_path"]
   row["original_pages"].append({"path":path,"sha256":v.get("sha256"),"url":v.get("source_URL"),"present":(root/path).is_file()})
   put(row,INPUTS["page_images"])
 for v in json.loads(paths["curated"].read_text(encoding="utf-8")):
  row=grab(item_id(v.get("item_url","")))
  if row:
   row["research_cues"].append(v.get("candidate_id"))
   put(row,INPUTS["curated"],date=v.get("date_as_cataloged",""))
 source_rep=[]
 for v in read_csv(paths["early_sources"]):
  row=grab(item_id(v.get("primary_source_url","")))
  if row: put(row,INPUTS["early_sources"],v.get("document_identity",""),v.get("date",""))
  else: source_rep.append({"source_candidate_id":v.get("candidate_id"),"url":v.get("primary_source_url"),"date_hint":v.get("date"),"status":"UNCROSSWALKED_DO_NOT_MERGE_BY_DATE"})
 lord_ids=set()
 for v in read_csv(paths["lord"]):lord_ids.add(v.get("candidate_id"))
 lord19=set(v.get("candidate_id") for v in read_csv(paths["lord19"])) if paths["lord19"].is_file() else set()
 items=sorted(records.values(),key=lambda r:r["candidate_id"])
 for a in items:
  a["titles"].sort();a["dates"].sort();a["source_paths"].sort()
  a["original_pages"].sort(key=lambda z:z["path"])
  a["grade"]="SAVED_MASTER_PAGES_UNREVIEWED" if a["original_pages"] else ("LOC_XML_TRANSCRIPTION_UNREVIEWED" if a["transcription"] else ("LOC_METADATA_UNREVIEWED" if a.get("item_metadata_retrieved") else "SEARCH_LEAD_ONLY"))
 (out/"ITEM_CANDIDATES.jsonl").write_text("".join(json.dumps(a,sort_keys=True,ensure_ascii=False)+"\n" for a in items),encoding="utf-8")
 with (out/"ITEM_CANDIDATES.csv").open("w",encoding="utf-8",newline="") as f:
  cols=["candidate_id","url","grade","date_hints","title_hints","transcribed","master_pages","legal_inclusion","human_certified"]
  w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
  for a in items:w.writerow({"candidate_id":a["candidate_id"],"url":a["url"],"grade":a["grade"],"date_hints":" | ".join(a["dates"]),"title_hints":" | ".join(a["titles"]),"transcribed":bool(a["transcription"]),"master_pages":len(a["original_pages"]),"legal_inclusion":"HOLD","human_certified":"no"})
 (out/"UNLINKED_EARLY_REPRESENTATIONS.json").write_text(json.dumps(source_rep,indent=2),encoding="utf-8")
 m={"schema":"eo-early-candidate-register/v1","input_hashes":{k:hashfile(p) for k,p in paths.items() if p.is_file()},"distinct_LOC_item_ID_candidates":len(items),"items_with_LOC_XML_transcript":sum(bool(x["transcription"]) for x in items),"items_with_saved_original_pages":sum(bool(x["original_pages"]) for x in items),"saved_original_pages_referenced":sum(len(x["original_pages"]) for x in items),"Lord_index_appearances_UNAUTHENTICATED":len(lord_ids),"Lord_19c_gap_rows":len(lord19),"Lord_19c_not_in_Lord_main":len(lord19-lord_ids),"uncrosswalked_historical_source_representations":len(source_rep),"newly_admitted_EOs":0,"independent_human_certifications":0,"no_date_only_identity_merges":True}
 (out/"SUMMARY.json").write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
 (out/"CENSUS_READINESS.md").write_text("# Candidate census separate from 14,972 working EOs\n\n"+str(len(items))+" distinct LOC item IDs; "+str(m["items_with_LOC_XML_transcript"])+" transcripts, "+str(m["saved_original_pages_referenced"])+" stored page-image links. "+str(len(lord_ids))+" Lord appearances remain unverified index entries.\n\n**Zero candidates admitted; zero independent certifications.** Same-day dates are never used as identity keys. Review signer, original pages, scope, duplicates and legal codebook 2.0.0 before admitting any instrument.\n")
 print(json.dumps(m,indent=2))
if __name__=="__main__":
 r=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(Path(__file__).parent),"-p","test_*.py"])
 if r.returncode:raise SystemExit("Tests failed, no output built")
 build()
