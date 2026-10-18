"""Run the tests, then find the executive orders printed in Richardson's Messages and Papers and locate every WPA and
Lord citation into each volume. See README.md."""

import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_richardson"], cwd=HERE).returncode:
    sys.exit("Tests failed; nothing built.")
sys.path.insert(0, str(HERE))
import richardson  # noqa: E402

s = richardson.run(os.environ.get("REPO_ROOT", "."), HERE, os.environ["OUTPUT_DIR"], os.environ.get("WPA_LISTS_DIR") or None)
print(f"WPA and Lord lists: {s['lists']['source']} ({s['wpa_entries_parsed']} numbered entries parsed, "
      f"{s['lord_entries_citing_richardson']} Lord entries citing Richardson).")
for v in s["volumes"]:
    print(f"{v['volume']}: {v['orders']} orders in {v['order_sections']} executive-order sections (contents agree) "
          f"plus {v['residue_units']} fragments; confidence {v['confidence']}; undated {v['orders_undated']}; PDF check: {v['pdf_check']}.")
    print(f"  Page map: {v['page_map']['heads_agree']} of {v['page_map']['heads_read']} running heads agree; "
          f"{v['pages_rejoined_from_pdftotext_raw']} fragmented pages taken from the pdftotext layer.")
    print(f"  WPA citations: {v['wpa_citations']} {v['wpa_status']}; Lord citations: {v['lord_citations']} {v['lord_status']}; "
          f"WPA orders with no Richardson citation, matched on date and subject: {v['wpa_date_only_candidates']}.")
    print(f"  {v['wpa_numbers_located']} WPA numbers located in {v['orders_with_wpa_number']} orders; {v['unnumbered_orders']} unnumbered orders "
          f"({v['unnumbered_orders_cited_by_lord']} cited by Lord, {v['orders_cited_by_neither_list']} by neither list).")
    print(f"  Census: {v['census_ids_with_text']} census orders get a text (fragments {v['fragments']}); "
          f"decided orders among them {v['decided_orders_with_text']}; leads {v['census_leads']}; ending leads {v['ending_leads']}.")
print(f"Citations into volumes this job does not hold yet: {s['citations_to_volumes_not_in_job']}.")
print("Leads only: nothing is admitted, merged, dated or changed. Richardson is a printed compilation, not the signed originals.")
