"""Independent, synthetic Cruden black-box challenge. No production corpus writes.

Run: python3 fixture_challenge.py PATH_TO_CRUDEN.py --report report.json
Baseline comparison preserves legacy member fields; additional coverage is reported.
"""
import argparse
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import time

HERE = Path(__file__).resolve().parent
LEGACY_FIELDS = ("register", "wpa", "original", "page_check", "own_text_signals", "number_citations", "code_mentions")

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

def setup(root):
    paths = {}
    def text(rel, body):
        p=root/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(body, encoding="utf-8"); paths[rel]=body
    text("jobs/held/output/texts/00-own.txt", "Executive Order No. 6242 approves the Code of Fair Competition for the Widget Industry until further order.")
    text("jobs/held/output/texts/01-base.txt", "Executive Order No. 6242 supersedes a prior direction. 3 F.R. 1234 is the Federal Register citation.")
    text("jobs/held/output/texts/02-suffix-c.txt", "Executive Order No. 6242-C concerns a different approval.")
    text("jobs/held/output/texts/03-suffix-d.txt", "Executive Order No. 6242 D concerns another approval.")
    text("jobs/held/output/texts/04-code.txt", "Code of Fair Competition for the Widget Industry is stayed. Later: Executive Order No. 6242.")
    text("jobs/held/output/texts/05-duplicate.txt", paths["jobs/held/output/texts/04-code.txt"])
    text("jobs/held/output/texts/06-neighbor.txt", "Executive Order No. 6242. Text for target.\nExecutive Order No. 9999. The neighboring order is revoked.")
    text("jobs/held/output/texts/07-continuation.txt", "Executive Orders Nos. 6242-C and 6242-D are listed together.")
    text("jobs/held/output/texts/08-spaces.txt", "Executive\nOrder No. 6242-C and Code of Fair Competition for the Widget Industry.")
    text("jobs/held/output/texts/09-no-the.txt", "Code of Fair Competition for Widget Industry.")
    text("jobs/held/output/texts/11-unicode-prefix.txt", "İ" * 100 + " Code of Fair Competition for the Widget Industry. Executive Order No. 6242.")
    text("jobs/held/output/texts/nested/10-noise.txt", "No. 6242; 1234; code widget; unanchored numbers are not EO citations.")
    text("jobs/clause-drafts/output/texts/excluded.txt", "Executive Order No. 6242 and Code of Fair Competition for the Widget Industry.")
    text("outside/texts/excluded.txt", "Executive Order No. 6242.")
    rows=[];dossiers={}
    for iid in ("EO:6242", "EO:6242C", "EO:6242D", "EO:1234", "EO:9999", "EO:7777"):
        rows.append({"instrument_id":iid,"title":"Code of Fair Competition for the Widget Industry" if iid=="EO:6242" else "Test order", "date":"1933-01-01","president":"Fixture","best_held":"fixture","provisional_status":""})
        dossiers[iid]={"evidence":{"ORIGINAL:"+iid:{"source":{"text_path":"jobs/held/output/texts/00-own.txt"}}}} if iid=="EO:6242" else {"evidence":{}}
    for rel, fields, data in (("jobs/domesday-register/output/REGISTER.csv", list(rows[0]), rows),("jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv", ["id","year","month_day","page","citations_joined","text"],[])):
        p=root/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
    for name in ("MIRROR_DOCUMENTS.jsonl","DOCUMENTS.jsonl"):
        p=root/"jobs/app-executive-orders/output"/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text("")
    packet=root/"packet";packet.mkdir()
    return dossiers, paths, packet

def run(obj, root, dossiers, packet):
    obj.REPO=root
    os.environ["CRUDEN_CACHE_DIR"]=str(root/"cache")
    obj.load_members=lambda _:dossiers
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):obj.lookups(packet)
    return json.loads((packet/"LOOKUPS.json").read_text()),(packet/"LOOKUPS.md").read_text(),buf.getvalue()

def regex_output(obj, patterns):
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf): obj.search(patterns)
    return buf.getvalue()

def projection(result):
    return {iid:{k:entry[k] for k in LEGACY_FIELDS} for iid,entry in result["members"].items()}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("source",type=Path);ap.add_argument("--report",type=Path,required=True);ap.add_argument("--overflow-files",type=int,default=0);args=ap.parse_args()
    started=time.monotonic();baseline=module(HERE/"BASELINE_CRUDEN.py","baseline_challenge");candidate=module(args.source.resolve(),"candidate_challenge")
    with tempfile.TemporaryDirectory(prefix="cruden-independent-") as td:
        root=Path(td);dossiers,paths,packet=setup(root)
        for i in range(args.overflow_files):
            rel=f"jobs/overflow/output/texts/{i:04d}.txt"; body="Executive Order No. 6242 cites the Code of Fair Competition for the Widget Industry. " * 5
            p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body);paths[rel]=body
        old,oldmd,oldstdout=run(baseline,root,dossiers,packet)
        oldraw=(packet/"LOOKUPS.json").read_bytes()
        new,markdown,stdout=run(candidate,root,dossiers,packet)
        oldp,newp=projection(old),projection(new)
        regex_patterns=[r"executive\s+order",r"(?<=No\. )6242",r"Widget|1234",r"unmatched7777"]
        old_search=regex_output(baseline,regex_patterns);new_search=regex_output(candidate,regex_patterns)
        checks={"legacy_json_bytes_equal":oldraw==(packet/"LOOKUPS.json").read_bytes(),"legacy_markdown_bytes_equal":oldmd.encode("utf-8")==markdown.encode("utf-8"),"lookup_stdout_equal":oldstdout==stdout,"regex_search_output_equal":old_search==new_search,"member_ids_preserved":set(oldp)==set(newp),"legacy_projection_equal":oldp==newp,"fr_citation_not_eo1234":not newp["EO:1234"]["number_citations"],"negative_query_empty":not newp["EO:7777"]["number_citations"],"suffix_c_not_d":not any(x["file"].endswith("03-suffix-d.txt") for x in newp["EO:6242C"]["number_citations"]),"base_not_suffix_c":not any(x["file"].endswith("02-suffix-c.txt") for x in newp["EO:6242"]["number_citations"]),"own_text_excluded":not any(x["file"].endswith("00-own.txt") for x in newp["EO:6242"]["number_citations"]),"duplicate_paths_retained":all(any(x["file"].endswith(s) for x in newp["EO:6242"]["number_citations"]) for s in ("04-code.txt","05-duplicate.txt")),"clause_drafts_excluded":not any("clause-drafts" in x["file"] for e in newp.values() for x in e["number_citations"])}
        candidate_details=getattr(candidate,"LAST_DETAILS",None)
        if candidate_details:
            expected_counts={}
            for iid,entry in old["members"].items():
                np=baseline.number_pattern(iid);code=baseline.code_name(entry["register"]["title"]);own=entry["original"]["text_path"]
                eligible=[body for rel,body in paths.items() if rel.startswith("jobs/") and "/output/texts/" in rel and not rel.startswith("jobs/clause-drafts/") and rel!=own]
                n=sum(bool(np.search(body)) for body in eligible) if np else 0
                c=sum(("code of fair competition for the "+code).lower() in body.lower() for body in eligible) if code else 0
                expected_counts[iid]={"number_matching_files":n,"code_matching_files":c}
            checks["actual_document_totals_exact"]=all(all(candidate_details["members"][iid][k]==v for k,v in counts.items()) for iid,counts in expected_counts.items())
            checks["truncation_flags_exact"]=all(candidate_details["members"][iid]["number_truncated"]==(counts["number_matching_files"]>40) and candidate_details["members"][iid]["code_truncated"]==(counts["code_matching_files"]>60) for iid,counts in expected_counts.items())
        if args.overflow_files >= 61:
            checks["legacy_number_limit_40"]=len(newp["EO:6242"]["number_citations"])==40
            checks["legacy_code_limit_60"]=len(newp["EO:6242"]["code_mentions"])==60
        report={"source":str(args.source.resolve()),"source_sha256":hashlib.sha256(args.source.read_bytes()).hexdigest(),"baseline_sha256":hashlib.sha256((HERE/"BASELINE_CRUDEN.py").read_bytes()).hexdigest(),"checks":checks,"all_checks_pass":all(checks.values()),"overflow_files":args.overflow_files,"fixture_files":len(paths),"legacy_result":old,"candidate_result":new,"candidate_details":candidate_details,"candidate_markdown":markdown,"candidate_stdout":stdout,"regex_patterns":regex_patterns,"legacy_regex_stdout":old_search,"candidate_regex_stdout":new_search,"elapsed_seconds":time.monotonic()-started,"scope":"Synthetic fixture coverage; same-family separate-context engineering only; no corpus-wide/legal inference."}
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n");print(json.dumps({"report":str(args.report),"checks":checks,"elapsed_seconds":report["elapsed_seconds"]},indent=2))
if __name__=="__main__":main()
