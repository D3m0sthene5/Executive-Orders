"""Retrieve LOC-provided transcriptions for early presidential source items.

Fetch only the fulltext_file URLs explicitly returned in the previously
preserved item metadata. No OCR pass, catalog search, or status adjudication.
Save raw XML bytes and searchable derived text with immutable link to source.
"""
from __future__ import annotations
import csv,gzip,hashlib,json,os,re,time,urllib.error,urllib.parse,urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
import sys

ROOT=Path(os.environ["REPO_ROOT"])
OUT=Path(os.environ["OUTPUT_DIR"])
SEEDS=ROOT/"jobs/early-ranger-original-items/output/PRIMARY_ITEM_METADATA.jsonl"
MAX=3_000_000
USER_AGENT="EO-Historical-Research-Transcription-Reuse/1.0"

sys.path.insert(0,str(ROOT/"jobs/_lib"))
from fetch_pool import FetchPool
POOL=FetchPool(Path(os.environ.get("JOB_CACHE_DIR",str(OUT.parent/"download-cache"))),max_bytes=MAX)

def sha(x):return hashlib.sha256(x).hexdigest()
def validate_url(url):
    p=urllib.parse.urlsplit(url)
    return p.scheme=="https" and p.hostname=="tile.loc.gov" and p.path.endswith(".xml") and p.path.startswith("/storage-services/")

def one_text(element):
    # XML may be TEI/PAGE/ALTO. Conservatively collect readable text; no
    # accuracy claim or semantic clause detection from markup is automatic.
    texts=[]
    for e in element.iter():
        local=e.tag.split("}")[-1].lower()
        # Loc transcription often uses XML METS/p/line; concatenate text
        # in document order, but preserve basic breaks to allow review.
        if e.text and e.text.strip():
            texts.append(e.text.strip())
        if e.tail and e.tail.strip():
            texts.append(e.tail.strip())
    normalized=re.sub(r"[\t ]+"," "," ".join(texts))
    return re.sub(r"\s*\n\s*","\n",normalized).strip()

def main():
    rows=[json.loads(x) for x in SEEDS.read_text(encoding="utf-8").splitlines() if x]
    plan=[]
    for record in rows:
        for x in record.get("media_resource_candidates",[]):
            if x.get("link_role_as_metadata")!="fulltext_file":continue
            url=x.get("url","")
            if not validate_url(url):raise ValueError("Unsafe XML source URL")
            plan.append((record,url))
    if len(plan)!=9:raise ValueError("LOC XML transcription availability changed")
    (OUT/"xml_original").mkdir(parents=True,exist_ok=True)
    (OUT/"derived_text").mkdir(parents=True,exist_ok=True)
    POOL.prefetch([u for _,u in plan])
    result=[]
    for record,url in plan:
        id_=record["catalog_item_id"]
        row={"catalog_item_id":id_,"item_url":record["url"],
             "official_source_XML_url":url,"source_page_metadata_sha256":record["source_metadata_sha256"],
             "metadata_title":record["official_item_title"],
             "download_state":"failed","sha256":None,"bytes":0,"transcript_chars":0,
             "transcript_word_count":0,"cue_phrases_NOT_authentication":[],
             "derivation":"XML_text_nodes_unreviewed","legal_directive_verified":False}
        try:
            fetched=POOL.fetch(url)
            if urllib.parse.urlsplit(fetched['final_url']).hostname!='tile.loc.gov':raise ValueError('Unexpected XML download redirect')
            raw=fetched['body']
            root=ET.fromstring(raw)
            plain=one_text(root)
            if len(plain)<25:raise ValueError("XML lacked usable text nodes")
            raw_path=OUT/"xml_original"/(id_+".xml")
            raw_path.write_bytes(raw)
            derived=OUT/"derived_text"/(id_+".txt")
            derived.write_text(plain+"\n",encoding="utf-8")
            cues=[]
            for rexp in [r"\b(?:I direct|You will|You shall|I have directed|I authorize|orders?)\b",
                         r"\b(?:military|Secretary|Congress|United States|President)\b"]:
                cues.extend(m.group(0) for m in list(re.finditer(rexp,plain,re.I))[:12])
            row.update({"download_state":"transcription_bytes_preserved_UNREVIEWED",
                "sha256":sha(raw),"bytes":len(raw),
                "transcript_chars":len(plain),
                "transcript_word_count":len(plain.split()),
                "transcript_path":str(derived.relative_to(OUT)),
                "xml_path":str(raw_path.relative_to(OUT)),
                "cue_phrases_NOT_authentication":cues})
        except Exception as exc:
            row["error"]=type(exc).__name__+": "+str(exc)[:250]
        result.append(row)
        print(id_,row["download_state"],row["transcript_word_count"],flush=True)

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"TRANSCRIPTION_INVENTORY.jsonl").write_text(
        "".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in result),encoding="utf-8")
    metrics={"schema":"eo-early-LOC-XML-reuse/v1",
             "LOC_item_XML_links_official_metadata":len(plan),
             "preserved_XML_transcriptions":sum(x["download_state"].startswith("transcription_bytes") for x in result),
             "failed_XML_acquisitions":sum(x["download_state"]=="failed" for x in result),
             "fulltext_words_in_unreviewed_derived_text":sum(x["transcript_word_count"] for x in result),
             "original_document_issuance_authenticated":0,
             "new_EO_identifications":0,"human_certified_lifecycle_histories":0}
    (OUT/"TRANSCRIPTION_METRICS.json").write_text(json.dumps(metrics,indent=2)+"\n")
    lines=["# Early historical document text, LOC transcription reuse","",
           "Text is the LOC-provided digital transcription and may contain errors. "
           "It is not a verified legal clause inventory. Source XML and item metadata are preserved.",""]
    for r in result:
        lines.append(f"- [{r['metadata_title']}]({r['item_url']}) — {r['download_state']}, "
                     f"{r['transcript_word_count']} words; "
                     f"raw XML SHA-256 {r.get('sha256')}.")
    lines+=["","## Useful follow-up","",
            "Read transcribed contents against the original manuscript images; "
            "extract issuer, addressee, directives, legal source, and precise dating into "
            "separate research proposals. For doubtful by-command and ambiguous historical "
            "orders, preserve unsettled inclusion and do not change census counts.",""]
    (OUT/"TRANSCRIPTION_REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps(metrics,indent=2),flush=True)

if __name__=="__main__":main()
