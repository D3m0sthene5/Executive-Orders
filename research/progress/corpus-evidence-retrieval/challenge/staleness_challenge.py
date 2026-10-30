"""Independent black-box source-staleness challenge using temporary fixture corpora."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
from fixture_challenge import module, setup, run, projection, HERE

def main():
    ap=argparse.ArgumentParser();ap.add_argument("source",type=Path);ap.add_argument("--report",required=True,type=Path);args=ap.parse_args()
    started=time.monotonic();baseline=module(HERE/"BASELINE_CRUDEN.py","stale_baseline");candidate=module(args.source.resolve(),"stale_candidate");steps=[]
    with tempfile.TemporaryDirectory(prefix="cruden-staleness-") as td:
        root=Path(td);dossiers,_,packet=setup(root)
        def compare(label):
            old,_,_=run(baseline,root,dossiers,packet);new,_,_=run(candidate,root,dossiers,packet)
            steps.append({"label":label,"legacy_projection_equal":projection(old)==projection(new),"number_files":{iid:[x["file"] for x in row["number_citations"]] for iid,row in new["members"].items()},"metadata":{k:v for k,v in new.items() if k!="members"}})
        compare("cold")
        compare("unchanged_warm")
        added=root/"jobs/held/output/texts/added.txt";added.write_text("Executive Order No. 7777 newly added.")
        compare("add_file")
        added.unlink();compare("delete_file")
        p=root/"jobs/held/output/texts/01-base.txt";st=p.stat();old=p.read_bytes();new=old.replace(b"6242",b"7777");assert len(old)==len(new);p.write_bytes(new);os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns))
        compare("same_size_edit_preserved_mtime")
        p=root/"jobs/held/output/texts/12-crlf.txt";p.write_bytes(b"\xc4\xb0\xff\r\nExecutive Order No. 6242 references Code of Fair Competition for the Widget Industry.\r\n")
        compare("unicode_crlf_invalid_utf8")
        p.unlink();compare("delete_unicode_file")
    checks={"every_projection_equal":all(x["legacy_projection_equal"] for x in steps),"addition_detected":any(x.endswith("added.txt") for x in steps[2]["number_files"]["EO:7777"]),"deletion_detected":not steps[3]["number_files"]["EO:7777"],"same_size_edit_detected":any(x.endswith("01-base.txt") for x in steps[4]["number_files"]["EO:7777"]),"old_target_removed_after_edit":not any(x.endswith("01-base.txt") for x in steps[4]["number_files"]["EO:6242"])}
    report={"source_sha256":hashlib.sha256(args.source.read_bytes()).hexdigest(),"checks":checks,"all_checks_pass":all(checks.values()),"steps":steps,"elapsed_seconds":time.monotonic()-started,"scope":"Seven black-box fixture runs; source add/delete/same-length mtime-preserved edit and decoding edge cases; not an atomic filesystem-snapshot guarantee."}
    args.report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n");print(json.dumps({"report":str(args.report),"checks":checks,"elapsed_seconds":report["elapsed_seconds"]},indent=2))
if __name__=="__main__":main()
