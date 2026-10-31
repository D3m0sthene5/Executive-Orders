"""Fast historical manuscript reviewer workbench, using only preserved inputs.

This generates a static HTML interface with searchable transcriptions and
original-page gallery. It never admits a document into the EO universe and
cannot produce a human-certified lifecycle finding.
"""
import argparse,base64,csv,hashlib,html,json,mimetypes,os,re,subprocess,sys
import importlib.util
from pathlib import Path

ROOT=Path(os.environ.get("REPO_ROOT",Path(__file__).resolve().parents[2]))
OUT=Path(os.environ.get("OUTPUT_DIR",Path(__file__).parent/"output"))
META=ROOT/"jobs/early-ranger-original-items/output/PRIMARY_ITEM_METADATA.jsonl"
XML=ROOT/"jobs/early-ranger-transcriptions/output/TRANSCRIPTION_INVENTORY.jsonl"
TEXT=ROOT/"jobs/early-ranger-transcriptions/output/derived_text"
FAC=ROOT/"jobs/early-ranger-full-pages/output/PAGE_IMAGE_CUSTODY.csv"
CAND=ROOT/"research/stage22/CANDIDATE_DIRECTIVES.json"
_spec=importlib.util.spec_from_file_location("ranger_roundtrip",Path(__file__).with_name("roundtrip.py"))
rt=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(rt)
SOURCE_REF=os.environ.get("RANGER_SOURCE_REF") or subprocess.check_output(["git","rev-parse","HEAD"],cwd=Path(__file__).resolve().parents[2],text=True).strip()
GITHUB_RAW="https://raw.githubusercontent.com/D3m0sthene5/Executive-Orders/"+SOURCE_REF+"/"
def jlines(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def readcsv(p):
    with p.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def preview(root,path,expected):
    file=Path(root)/path
    if file.is_file() and file.suffix.lower() in (".jpg",".jpeg",".png"):
        raw=file.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("Source changed during preview generation")
        return "data:"+(mimetypes.guess_type(path)[0] or "application/octet-stream")+";base64,"+base64.b64encode(raw).decode("ascii")
    return ""


def make_case(meta,texts,images,candidates,root=None,retained=None,retained_path=None,retained_sha256=None):
    root=Path(root or ROOT)
    textbase=root/"jobs/early-ranger-transcriptions/output"
    sources=[];transcript=""
    id_=meta["catalog_item_id"]
    if meta["url"] not in ("https://www.loc.gov/item/"+id_+"/","https://loc.gov/item/"+id_+"/"):
        raise ValueError("Metadata item ID/URL conflict")
    textrows=[x for x in texts if x.get("catalog_item_id")==id_ and x.get("transcript_path")]
    textfile=textbase/(id_+".txt")
    if len(textrows)==1:textfile=textbase/textrows[0]["transcript_path"]
    elif len(textrows)>1:raise ValueError("Conflicting transcription representations for "+id_)
    sources.append(dict(role="candidate_metadata_record",path=str(META.relative_to(ROOT)),
                        sha256=rt.digest(meta),expected_sha256=None,present=True))
    if textrows or textfile.is_file():
        transcript_source=rt.artifact(root,str(textfile.relative_to(root)),"transcript")
        sources.append(transcript_source)
        if textfile.is_file():
            transcript_raw=textfile.read_bytes()
            if hashlib.sha256(transcript_raw).hexdigest()!=transcript_source["sha256"]:raise ValueError("Transcript changed during case generation")
            transcript=transcript_raw.decode("utf-8")
    for row in textrows:
        sources.append(dict(role="transcription_inventory_record",path=str(XML.relative_to(ROOT))+"#"+id_,sha256=rt.digest(row),expected_sha256=None,present=True))
        if row.get("item_url") and row["item_url"]!=meta["url"]:raise ValueError("Transcript item ID/URL conflict")
        if row.get("xml_path"):
            sources.append(rt.artifact(root,str((textbase/row["xml_path"]).relative_to(root)),"source_xml",row.get("sha256")))
    fac=images.get(id_,[])
    srcs=[]
    for r in fac:
        if r.get("item_url") and r["item_url"]!=meta["url"]:raise ValueError("Page item ID/URL conflict")
        if r.get("source_state")=="original_page_JPEG_bytes_acquired":
            sources.append(dict(role="page_custody_record",path=str(FAC.relative_to(ROOT))+"#"+id_+"/"+str(r["page_in_LOC_resource_sequence"]),sha256=rt.digest(r),expected_sha256=None,present=True))
            rel="jobs/early-ranger-full-pages/output/"+id_+"/page_"+str(int(r["page_in_LOC_resource_sequence"])).zfill(2)+".jpg"
            if r.get("stored_path"):rel="jobs/early-ranger-full-pages/output/"+r["stored_path"]
            source=rt.artifact(root,rel,"original_page",r.get("sha256"),url=r["source_URL"],page_sequence=int(r["page_in_LOC_resource_sequence"]))
            sources.append(source)
            srcs.append({"github_original_page":GITHUB_RAW+rel,"custody":source,"display_data_uri":preview(root,rel,source["sha256"]),
                        "LOC_original_image_url":r["source_URL"],
                        "source_sha256":r["sha256"],
                        "page_sequence":int(r["page_in_LOC_resource_sequence"])})
    note=candidates.get(meta["url"],{})
    entry={"id":id_,"url":meta["url"],
           "title":meta.get("official_item_title") or meta.get("original_title_from_prior_search"),
           "date_as_cataloged":meta.get("item_date") or meta.get("search_date_hint_unverified"),
           "creator_as_cataloged":meta.get("creator_names_from_catalog",""),
           "metadata_status":meta["status"],"metadata_hash":meta.get("source_metadata_sha256",""),
           "transcription":transcript,
           "transcription_status":"loc_XML_derived_unreviewed" if textfile.is_file() else "no_LOC_XML_text_obtained",
           "loc_source_resource_candidates":meta.get("media_resource_candidates",[]),
           "master_JPEG_pages_stored":srcs,
           "prior_stage22_research_candidate":note,
           "inclusion_state":"not_adjudicated",
           "independent_human_review_recorded":False}
    if retained is not None:
        if retained.get("id")!=id_ or retained.get("url")!=meta["url"]:
            raise ValueError("Retained representation belongs to another item")
        if not retained_path:raise ValueError("Retained representation needs a source path")
        source=rt.artifact(root,retained_path,"retained_workbench_snapshot",retained_sha256,embedded_case_sha256=rt.digest(retained))
        sources.append(source)
        entry["retained_source_snapshot"]={"path":retained_path,"case_sha256":rt.digest(retained),
            "notice":"Older retained workbench representation; current acquisition inventory does not authenticate it", "case":retained}
        if not entry["transcription"] and retained.get("transcription"):
            entry["transcription"]=retained["transcription"]
            entry["transcription_status"]="older_retained_workbench_transcript_UNVERIFIED"
    return rt.bind_case(entry,meta,sources)


def build_cases(root=ROOT,retained_workbench=None,include_facsimiles=False,facsimile_custodies=()):
    root=Path(root)
    metadata=jlines(root/META.relative_to(ROOT));xml=jlines(root/XML.relative_to(ROOT))
    scanned=readcsv(root/FAC.relative_to(ROOT));pilot=json.loads((root/CAND.relative_to(ROOT)).read_text())
    grouped={}
    for row in scanned:grouped.setdefault(row["catalog_item"],[]).append(row)
    old={};retained_sha256=None
    if retained_workbench:
        raw_bytes=(root/retained_workbench).read_bytes();raw=raw_bytes.decode("utf-8")
        retained_sha256=hashlib.sha256(raw_bytes).hexdigest()
        match=re.search(r'<script id="payload" type="application/json">(.*?)</script>',raw,re.S)
        if not match:raise ValueError("Retained workbench has no payload")
        retained_cases=json.loads(match.group(1))["cases"]
        old={c["id"]:c for c in retained_cases}
        if len(old)!=len(retained_cases):raise ValueError("Duplicate retained item IDs")
    cases=[make_case(m,xml,grouped,{x["item_url"]:x for x in pilot},root,
                     old.get(m["catalog_item_id"]),retained_workbench,retained_sha256) for m in metadata]
    if len({c["id"] for c in cases})!=len(cases):raise ValueError("Duplicate source metadata ID")
    custody_paths=list(facsimile_custodies)
    if include_facsimiles:custody_paths.insert(0,"jobs/early-ranger-facsimiles/output/FACSIMILE_CUSTODY.json")
    for custody_path in custody_paths:
        custody=json.loads((root/custody_path).read_text())
        by={c["id"]:c for c in cases}
        for record in custody:
            c=by.get(record["catalog_item_id"])
            if c is None:continue
            if record.get("item_url")!=c["url"]:raise ValueError("Facsimile belongs to another item")
            sources=list(c["source_binding"]["sources"])
            c.setdefault("retained_facsimiles",[])
            sources.append(dict(role="facsimile_custody_record",path=custody_path,sha256=rt.digest(record),expected_sha256=None,present=True))
            for f in record.get("facsimile_files",[]):
                if f.get("state")!="downloaded_exact_source_bytes":continue
                path=str(Path(custody_path).parent/f["stored_relpath"])
                src=rt.artifact(root,path,"retained_facsimile",f.get("sha256"),url=f.get("source_url"),representation_grade=f.get("representation_grade",f.get("service_representation","unreviewed_retained_facsimile")))
                sources.append(src);c["retained_facsimiles"].append(dict(src,display_data_uri=preview(root,path,src["sha256"])))
            meta_record=next(m for m in metadata if m["catalog_item_id"]==c["id"])
            rt.bind_case(c,meta_record,sources)
    for c in cases:c["source_health"]=rt.health(c["source_binding"])
    return cases

def make_html(cases,metric,worksheets=()):
    payload=json.dumps({"cases":cases,"metrics":metric,"worksheets":list(worksheets)},ensure_ascii=False,
                       separators=(",",":")).replace("<","\\u003c")
    page=r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>1789–1861 presidential instruction source-review workbench</title>
<style>body{margin:0;background:#f3f5f5;color:#1a3541;font:14px/1.45 system-ui,sans-serif}
header{background:#1e3b49;color:#fff;padding:15px 3vw}h1{font-size:23px;margin:0 0 6px}header p{max-width:1100px;margin:0}
main{max-width:1530px;margin:auto;padding:14px}.layout{display:grid;grid-template-columns:minmax(250px,310px) 1fr;gap:12px}
@media(max-width:850px){.layout{grid-template-columns:1fr}}aside,section{background:#fff;padding:12px;border:1px solid #d5e0e3;border-radius:6px}
input,select,textarea,button{font:inherit;padding:7px;box-sizing:border-box}input,select,textarea{width:100%}
input[type=checkbox]{width:auto}textarea{min-height:55px}
button{cursor:pointer;border:1px solid #b7c9d2;background:#f5f8fa;border-radius:4px}
button.item{width:100%;text-align:left;display:block;margin:4px 0;padding:9px}button:hover{background:#e6f1f6}
#menu{max-height:65vh;overflow-y:auto}.two{display:grid;grid-template-columns:1fr 1fr;gap:13px}
@media(max-width:1100px){.two{grid-template-columns:1fr}}
.transcript{max-height:750px;overflow:auto;background:#f5f7f8;padding:10px;white-space:pre-wrap;overflow-wrap:anywhere}
.gallery img{max-height:630px;max-width:100%;width:auto;object-fit:contain;border:1px solid #d3d9dd;background:white}
.imagebox{margin:10px 0;padding:6px;border:1px solid #e2e9ed}
.note{color:#744509}a{overflow-wrap:anywhere}.muted{color:#657983}
label{display:block;margin:8px 0}h2{font-size:20px}h3{font-size:16px}</style>
<header><h1>Early presidential directive · manuscript review</h1>
<p>Original page images and searchable LOC-derived transcripts together. Source recovery is complete for some cases; presidential-order identity and operative lifespan are not. Exported notes never count as independent legal certification.</p></header>
<main><p class="note">Do not admit catalog correspondence, person-of-interest letterbooks or reproduced editions as executive orders without assessing the actual directive and signer. Historical cutoff: October 14, 2026.</p>
<div class="layout"><aside><input id="search" type="search" placeholder="Search title, year, document text">
<select id="filter"><option value="">All candidate items</option><option value="images">Master manuscript images available</option><option value="text">Transcription available</option><option value="pilot">Stage22 substantive pilot</option></select>
<p id="count"></p><div id="menu"></div><hr><button id="export-all">Export all research notes</button>
<label>Resume saved review notes<input id="import" type="file" accept=".json"></label>
<p class="muted">Review state is in-memory until exported and imported; nothing silently writes to GitHub.</p></aside>
<section id="detail">Select a candidate.</section></div></main>
<script id="payload" type="application/json">%%DATA%%</script>
<script>
%%ROUNDTRIP%%
const db=JSON.parse(document.getElementById('payload').textContent),$=id=>document.getElementById(id);
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
const ids=new Set(db.cases.map(x=>x.id));
let active=null,notes={},unverified=[]; const noteKeys=['reviewer','issuer_capacity','date_verified','original_page_matches_text',
 'operative_clause_inventory','historical_inclusion_proposal','possible_first_cause','residuals_and_contrary_evidence','unresolved_gaps'];
function save(){
 if(!active)return;let t=notes[active.id]||{};
 for(const key of noteKeys){const field=$('n-'+key);if(field)t[key]=field.value}
 t.proposal={...(t.proposal||{}),disposition:$('n-disposition')?.value||'hold',reason:$('n-reason')?.value||'',attribution:'AI_research'};
 notes[active.id]=t;
}
function selectItem(c){
 save();active=c;const n=notes[c.id]||{};
let s='<h2>'+esc(c.title)+'</h2><p><a href="'+esc(c.url)+'" target="_blank" rel="noopener noreferrer">Official LOC item record</a> · '+esc(c.date_as_cataloged)+' · '+esc(c.creator_as_cataloged)+'</p>';
s+='<p class="muted">Catalog metadata state: '+esc(c.metadata_status)+' · transcription: '+esc(c.transcription_status)+' · retained original master pages: '+c.master_JPEG_pages_stored.length+'</p>';
if(c.prior_stage22_research_candidate&&c.prior_stage22_research_candidate.candidate_id){
 s+='<p class="note">Stage22 prior research proposal: '+esc(c.prior_stage22_research_candidate.candidate_id)+'; scope, date and historical inclusion remain undecided.</p>';
}
s+='<div class="two"><section><h3>Original manuscript images (unadjudicated)</h3><div class="gallery">';
if(!c.master_JPEG_pages_stored.length)s+='<p>Source page not locally recovered. Follow the official item link and resource candidates below.</p>';
for(const im of c.master_JPEG_pages_stored){s+='<div class="imagebox"><b>Source resource '+im.page_sequence+'</b> · <a href="'+esc(im.LOC_original_image_url)+'" target="_blank" rel="noopener noreferrer">LOC master image</a> · <a href="'+esc(im.github_original_page)+'" target="_blank" rel="noopener noreferrer">GitHub source bytes</a><img loading="lazy" src="'+esc(im.display_data_uri||'')+'" alt="Bound retained manuscript image"></div>';}
s+='</div><details><summary>Other LOC resource candidates</summary><ul>';
for(const im of c.loc_source_resource_candidates.slice(0,40)){s+='<li><a href="'+esc(im.url)+'" target="_blank" rel="noopener noreferrer">'+esc(im.link_role_as_metadata)+' — '+esc(im.url)+'</a></li>';}
for(const f of c.retained_facsimiles||[]){s+='<p><a href="'+esc(f.display_data_uri||f.url||db.metrics.github_source_prefix+f.path)+'" target="_blank" rel="noopener noreferrer">Retained facsimile: '+esc(f.path)+'</a> · '+esc(f.sha256)+' · '+esc(f.representation_grade)+'</p>';if(f.display_data_uri)s+='<img loading="lazy" style="max-width:100%" src="'+esc(f.display_data_uri)+'" alt="Exact retained facsimile bytes">';}
s+='</ul></details></section><section><h3>LOC-derived searchable transcript</h3><p class="note">Transcription is an editorial/encoded derivative. Verify operative passage and signature from the manuscript on the left.</p><p>Representation: '+esc(c.transcription_status)+'</p><div class="transcript">'+esc(c.transcription||'No LOC XML transcription available for this item.')+'</div></section></div>';
s+='<section><h3>Uncertified inclusion and scope worksheet</h3><p>Binding: '+esc(c.source_binding.fingerprint)+' · source health: '+esc(c.source_health||'unknown')+'</p>';
for(const old of unverified.filter(x=>x.item_id===c.id)){s+='<details><summary>Unverified retained notes: '+esc(old.validation)+'</summary><pre>'+esc(JSON.stringify(old,null,2))+'</pre></details>';}
s+='<label>AI research disposition<select id="n-disposition">'+['hold','recommend_inclusion','recommend_exclusion','possible_duplicate'].map(v=>'<option '+(n.proposal?.disposition===v?'selected':'')+'>'+v+'</option>').join('')+'</select></label><label>Reason<textarea id="n-reason">'+esc(n.proposal?.reason||'')+'</textarea></label>';
const fields=[
 ['reviewer','AI researcher name and model (never human certification)'],
 ['issuer_capacity','Who actually directed whom? Signer/capacity and document kind'],
 ['date_verified','Confirmed original issue date or date conflict'],
 ['original_page_matches_text','Exact page/folio and transcript discrepancy'],
 ['operative_clause_inventory','Potential mandatory clauses and relevant authority'],
 ['historical_inclusion_proposal','Proposal: include/hold/exclude under frozen EO codebook, with reasoning'],
 ['possible_first_cause','Any supported earlier effective cessation or current predicate'],
 ['residuals_and_contrary_evidence','Surviving rights, counterevidence and independent authority'],
 ['unresolved_gaps','Material outstanding questions']
];
for(const [key,label] of fields){s+='<label>'+esc(label)+'<textarea id="n-'+key+'">'+esc(n[key]||'')+'</textarea></label>';}
s+='</section><p class="note">All exports remain research-only, cannot create a whole-lifecycle claim or independent human certification record.</p>';
$('detail').innerHTML=s;
}
function matches(c){
const q=$('search').value.toLowerCase().trim(),f=$('filter').value;
if(f==='images'&&!c.master_JPEG_pages_stored.length)return false;
if(f==='text'&&!c.transcription)return false;
if(f==='pilot'&&!(c.prior_stage22_research_candidate&&c.prior_stage22_research_candidate.candidate_id))return false;
return !q||[c.title,c.id,c.date_as_cataloged,c.transcription,c.creator_as_cataloged].join(' ').toLowerCase().includes(q)}
function render(){const hits=db.cases.filter(matches);$('count').textContent=hits.length+' of '+db.cases.length+' LOC source items';
$('menu').replaceChildren();for(const x of hits){let b=document.createElement('button');b.className='item';b.textContent=x.id+' · '+x.title;b.onclick=()=>selectItem(x);$('menu').append(b)}}
function download(body){const blob=new Blob([JSON.stringify(body,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='EO-EARLY-REVIEW-DRAFTS.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),800)}
$('export-all').onclick=()=>{save();download(RangerRoundtrip.exportWorksheet(db.cases,notes,unverified))};
$('import').onchange=async()=>{try{
 const f=$('import').files[0];if(!f)return;
 const result=await RangerRoundtrip.validate(RangerRoundtrip.parse(await f.text()),db.cases);
 save();for(const r of result){if(r.validation==='unchanged_source')notes[r.item_id]=r.notes;else unverified.push(r);}
 if(active){let c=active;active=null;selectItem(c);}
 alert(result.map(r=>r.item_id+': '+r.validation).join('\n'));
}catch(e){alert('Import rejected: '+e.message)}};
['search','filter'].forEach(id=>$(id).addEventListener('input',render));
(async()=>{for(const d of db.worksheets||[]){for(const r of await RangerRoundtrip.validate(d,db.cases)){if(r.validation==='unchanged_source')notes[r.item_id]=r.notes;else unverified.push(r);}}render();if(db.cases.length)selectItem(db.cases[0]);})().catch(e=>{$('detail').textContent='Import rejected: '+e.message;});
</script></html>''';
    return page.replace("%%DATA%%",payload).replace("%%ROUNDTRIP%%",Path(__file__).with_name("roundtrip.js").read_text())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retained-workbench",help="Explicit older HTML snapshot, repository-relative; preserved as unverified representation")
    parser.add_argument("--include-retained-facsimiles",action="store_true",help="Bind and display the existing held facsimile inventory")
    parser.add_argument("--facsimile-custody",action="append",default=[],help="Explicit extra input in the existing facsimile custody format, paths relative to that inventory")
    parser.add_argument("--import-worksheet",action="append",default=[])
    args=parser.parse_args()
    cases=build_cases(ROOT,args.retained_workbench,args.include_retained_facsimiles,args.facsimile_custody)
    pilot=json.loads(CAND.read_text(encoding="utf-8"))
    metrics={"schema":"eo-early-source-workbench/v1",
        "source_items":len(cases),"github_source_prefix":GITHUB_RAW,"github_source_ref":SOURCE_REF,
        "with_transcriptions":sum(bool(c["transcription"]) for c in cases),
        "items_with_master_JPEGs":sum(bool(c["master_JPEG_pages_stored"]) for c in cases),
        "LOC_master_JPEGs_linked":sum(len(c["master_JPEG_pages_stored"]) for c in cases),
        "source_text_bytes":sum(len(c["transcription"].encode("utf-8")) for c in cases),
        "transcription_representation_states":{state:sum(c["transcription_status"]==state for c in cases) for state in sorted({c["transcription_status"] for c in cases})},
        "substantive_pilot_candidate_records":len(pilot),
        "new_historical_orders_admitted":0,
        "human_certified_lifecycles":0,
        "source_provenance_notice":"Candidates and text are available for review. Original manuscripts and legal statuses are not automatically authenticated."}
    OUT.mkdir(parents=True,exist_ok=True)
    case_manifest=json.loads(json.dumps(cases))
    for case in case_manifest:
        for image in case["master_JPEG_pages_stored"]+case.get("retained_facsimiles",[]):image.pop("display_data_uri",None)
    (OUT/"CASES.json").write_text(json.dumps(case_manifest,ensure_ascii=False,indent=2)+"\n")
    validations=[];worksheets=[]
    for path in args.import_worksheet:
        document=rt.read_worksheet(Path(path));worksheets.append(document)
        validations.append({"worksheet":path,"sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                            "records":rt.validate_worksheet(document,cases)})
    (OUT/"IMPORT_VALIDATION.json").write_text(json.dumps(validations,ensure_ascii=False,indent=2)+"\n")
    (OUT/"EARLY_SOURCE_REVIEW_WORKBENCH.html").write_text(make_html(cases,metrics,worksheets),encoding="utf-8")
    (OUT/"WORKBENCH_METRICS.json").write_text(json.dumps(metrics,indent=2)+"\n")
    (OUT/"WORKBENCH_REPORT.md").write_text(
        "# Early-order source workbench\n\nThe [HTML workbench](EARLY_SOURCE_REVIEW_WORKBENCH.html) brings "
        f"{len(cases)} LOC source items, {metrics['with_transcriptions']} transcribed items and "
        f"{metrics['LOC_master_JPEGs_linked']} preserved full-resolution page candidates together. "
        "The three case-study documents from Stage22 appear with their prior research questions. "
        "The interface exports and imports review *proposals*, preserving unknown inclusion and lifespan. "
        "No machine status changes or independent human approvals have been recorded.\n",encoding="utf-8")
    print(json.dumps(metrics,indent=2),flush=True)

if __name__=="__main__":main()
