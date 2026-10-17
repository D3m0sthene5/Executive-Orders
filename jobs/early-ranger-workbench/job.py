"""Fast historical manuscript reviewer workbench, using only preserved inputs.

This generates a static HTML interface with searchable transcriptions and
original-page gallery. It never admits a document into the EO universe and
cannot produce a human-certified lifecycle finding.
"""
import csv,html,json,os,re
from pathlib import Path

ROOT=Path(os.environ["REPO_ROOT"])
OUT=Path(os.environ["OUTPUT_DIR"])
META=ROOT/"jobs/early-ranger-original-items/output/PRIMARY_ITEM_METADATA.jsonl"
XML=ROOT/"jobs/early-ranger-transcriptions/output/TRANSCRIPTION_INVENTORY.jsonl"
TEXT=ROOT/"jobs/early-ranger-transcriptions/output/derived_text"
FAC=ROOT/"jobs/early-ranger-full-pages/output/PAGE_IMAGE_CUSTODY.csv"
CAND=ROOT/"research/stage22/CANDIDATE_DIRECTIVES.json"
GITHUB_RAW="https://raw.githubusercontent.com/D3m0sthene5/Executive-Orders/main/"
def jlines(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def readcsv(p):
    with p.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def make_case(meta,texts,images,candidates):
    id_=meta["catalog_item_id"]
    textfile=TEXT/(id_+".txt")
    fac=images.get(id_,[])
    srcs=[]
    for r in fac:
        if r.get("source_state")=="original_page_JPEG_bytes_acquired":
            rel="jobs/early-ranger-full-pages/output/"+id_+"/page_"+str(int(r["page_in_LOC_resource_sequence"])).zfill(2)+".jpg"
            srcs.append({"github_original_page":GITHUB_RAW+rel,
                        "LOC_original_image_url":r["source_URL"],
                        "source_sha256":r["sha256"],
                        "page_sequence":int(r["page_in_LOC_resource_sequence"])})
    note=candidates.get(meta["url"],{})
    entry={"id":id_,"url":meta["url"],
           "title":meta.get("official_item_title") or meta.get("original_title_from_prior_search"),
           "date_as_cataloged":meta.get("item_date") or meta.get("search_date_hint_unverified"),
           "creator_as_cataloged":meta.get("creator_names_from_catalog",""),
           "metadata_status":meta["status"],"metadata_hash":meta.get("source_metadata_sha256",""),
           "transcription":textfile.read_text(encoding="utf-8") if textfile.is_file() else "",
           "transcription_status":"loc_XML_derived_unreviewed" if textfile.is_file() else "no_LOC_XML_text_obtained",
           "loc_source_resource_candidates":meta.get("media_resource_candidates",[]),
           "master_JPEG_pages_stored":srcs,
           "prior_stage22_research_candidate":note,
           "inclusion_state":"not_adjudicated",
           "independent_human_review_recorded":False}
    return entry

def make_html(cases,metric):
    payload=json.dumps({"cases":cases,"metrics":metric},ensure_ascii=False,
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
const db=JSON.parse(document.getElementById('payload').textContent),$=id=>document.getElementById(id);
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
const ids=new Set(db.cases.map(x=>x.id));
let active=null,notes={}; const noteKeys=['reviewer','issuer_capacity','date_verified','original_page_matches_text',
 'operative_clause_inventory','historical_inclusion_proposal','possible_first_cause','residuals_and_contrary_evidence','unresolved_gaps'];
function save(){
 if(!active)return;let t=notes[active.id]||{};
 for(const key of noteKeys){const field=$('n-'+key);if(field)t[key]=field.value}
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
for(const im of c.master_JPEG_pages_stored){s+='<div class="imagebox"><b>Source resource '+im.page_sequence+'</b> · <a href="'+esc(im.LOC_original_image_url)+'" target="_blank" rel="noopener noreferrer">LOC master image</a> · <a href="'+esc(im.github_original_page)+'" target="_blank" rel="noopener noreferrer">GitHub source bytes</a><img loading="lazy" src="'+esc(im.github_original_page)+'" alt="LOC digitized manuscript image"></div>';}
s+='</div><details><summary>Other LOC resource candidates</summary><ul>';
for(const im of c.loc_source_resource_candidates.slice(0,40)){s+='<li><a href="'+esc(im.url)+'" target="_blank" rel="noopener noreferrer">'+esc(im.link_role_as_metadata)+' — '+esc(im.url)+'</a></li>';}
s+='</ul></details></section><section><h3>LOC-derived searchable transcript</h3><p class="note">Transcription is an editorial/encoded derivative. Verify operative passage and signature from the manuscript on the left.</p><div class="transcript">'+esc(c.transcription||'No LOC XML transcription available for this item.')+'</div></section></div>';
s+='<section><h3>Uncertified inclusion and scope worksheet</h3>';
const fields=[
 ['reviewer','Reviewer name'],
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
$('export-all').onclick=()=>{save();download({schema:'eo-early-source-worksheet/v1',
      review_state:'research_only_never_certification',source_cohort:db.metrics,per_case:notes})};
$('import').onchange=async()=>{try{const f=$('import').files[0];if(!f)return;const d=JSON.parse(await f.text());if(d.schema!=='eo-early-source-worksheet/v1'||d.review_state!=='research_only_never_certification')throw Error('Unrecognized worksheet');
if(Object.keys(d.per_case||{}).some(id=>!ids.has(id)))throw Error('Unknown catalog item');notes={...notes,...d.per_case};
if(active){let saved=active;active=null;selectItem(saved);}alert('Uncertified research notes restored.');}catch(e){alert('Import rejected: '+e.message)}};
['search','filter'].forEach(id=>$(id).addEventListener('input',render));render();if(db.cases.length)selectItem(db.cases[0]);
</script></html>''';
    return page.replace("%%DATA%%",payload)

def main():
    metadata=jlines(META)
    xml=jlines(XML)
    scanned=readcsv(FAC)
    pilot=json.loads(CAND.read_text(encoding="utf-8"))
    pilotByURL={x["item_url"]:x for x in pilot}
    grouped={}
    for x in scanned:grouped.setdefault(x["catalog_item"],[]).append(x)
    if len(metadata)!=21 or len(xml)!=9 or len(scanned)!=10 or len(pilot)!=3:
        raise ValueError("Source documents drifted; don't silently drop cases")
    cases=[make_case(x,xml,grouped,pilotByURL) for x in metadata]
    if len({x["id"] for x in cases})!=21:raise ValueError("Duplicate source metadata ID")
    metrics={"schema":"eo-early-source-workbench/v1",
        "source_items":len(cases),
        "with_transcriptions":sum(bool(c["transcription"]) for c in cases),
        "items_with_master_JPEGs":sum(bool(c["master_JPEG_pages_stored"]) for c in cases),
        "LOC_master_JPEGs_linked":sum(len(c["master_JPEG_pages_stored"]) for c in cases),
        "source_text_bytes":sum(len(c["transcription"]) for c in cases),
        "substantive_pilot_candidate_records":len(pilot),
        "new_historical_orders_admitted":0,
        "human_certified_lifecycles":0,
        "source_provenance_notice":"Candidates and text are available for review. Original manuscripts and legal statuses are not automatically authenticated."}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"EARLY_SOURCE_REVIEW_WORKBENCH.html").write_text(make_html(cases,metrics),encoding="utf-8")
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
