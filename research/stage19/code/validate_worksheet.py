"""Validate an exported lifecycle research worksheet against its source packet.

This validates freshness and required research fields only. It never creates a
whole-lifecycle claim or records an independent human certification.
"""

import argparse
import json
from pathlib import Path


FIELDS = ("original_source_and_page", "clause_inventory", "causal_or_continuing_predicate", "residuals_and_counterevidence", "unresolved_gaps")


def validate(packet, worksheet):
    errors=[]
    if worksheet.get("schema")!="eo-lifecycle-worksheet/v1":
        errors.append("schema")
    if worksheet.get("instrument_id")!=packet.get("instrument",{}).get("id"):
        errors.append("instrument_id")
    if worksheet.get("packet_fingerprint")!=packet.get("packet_fingerprint"):
        errors.append("stale_packet_fingerprint")
    if not isinstance(worksheet.get("reviewer"),str) or len(worksheet["reviewer"].strip())<3:
        errors.append("reviewer")
    if worksheet.get("disposition") not in ("hold","research_proposal"):
        errors.append("disposition")
    if worksheet.get("disposition")=="research_proposal":
        for field in FIELDS[:-1]:
            if not isinstance(worksheet.get(field),str) or len(worksheet[field].strip())<15:
                errors.append(field)
        if "https://" not in str(worksheet.get("original_source_and_page","")):
            errors.append("source_url_missing")
    return errors


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--packets",type=Path,required=True)
    p.add_argument("--worksheet",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    worksheet=json.loads(a.worksheet.read_text(encoding="utf-8"))
    packet=None
    for line in a.packets.read_text(encoding="utf-8").splitlines():
        item=json.loads(line)
        if item["instrument"]["id"]==worksheet.get("instrument_id"):
            packet=item
            break
    if packet is None:
        raise SystemExit("worksheet instrument not in prepared packet set")
    errors=validate(packet,worksheet)
    if errors:
        raise SystemExit("worksheet rejected: "+", ".join(errors))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("x",encoding="utf-8") as stream:
        json.dump({**worksheet,"validation_state":"fresh_research_worksheet_not_certification"},stream,indent=2,ensure_ascii=False)
        stream.write("\n")
    print("worksheet accepted as research material; lifecycle status unchanged")


if __name__=="__main__":
    main()
