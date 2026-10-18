"""Run the tests, then index the 1911 Isthmian Canal Commission compilation. See README.md."""

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_canal"], cwd=HERE).returncode:
    sys.exit("Tests failed; nothing built.")
sys.path.insert(0, str(HERE))
import canal  # noqa: E402

s = canal.run(os.environ.get("REPO_ROOT", "."), HERE, os.environ["OUTPUT_DIR"])
cats = s["categories"]
print(f"{s['contents_entries']} contents entries: {cats.get('presidential_order', 0)} orders of the President, "
      f"{cats.get('secretary_of_war_order', 0)} of the Secretary of War, {cats.get('presidential_letter', 0)} letters of the President, "
      f"{cats.get('secretary_of_war_letter', 0)} of the Secretary, {cats.get('proclamation', 0)} proclamation, "
      f"{cats.get('commission_action', 0)} commission action, {cats.get('war_department_circular', 0)} circular. PDF check: {s['pdf_check']}.")
print(f"  Dates: {s['presidential_order_dates_confirmed']} of {cats.get('presidential_order', 0)} presidential orders confirmed by a "
      f"closing dateline ({s['presidential_order_date_check']}); needs page check: {s['presidential_orders_needs_page_check']}.")
print(f"  Boundaries: {s['boundaries']}. Running heads stripped: {s['running_heads_stripped']}; head numbers that disagree "
      f"with PDF-{s['page_offset']}: {s['head_number_mismatches_pdf_page_and_number']}.")
print(f"  Crosswalk: {s['crosswalk_eo_ids']} EO ids for {s['crosswalk_seqs']} entries; WPA date check {s['wpa_date_check']}; "
      f"Lord matches {s['lord_matches']}; presidential orders with no EO id: {s['presidential_orders_without_eo_id']}.")
print(f"  Census: {s['census_state_of_eo_ids']}; readiness {s['readiness_provisional_status']}; decided orders with the "
      f"original_text step open: {s['decided_orders_original_text_step_open']}. Fragments: {s['fragments']}.")
print(f"  Secretary of War orders: {s['secretary_of_war_orders']}. Leads: {s['census_leads']}. "
      f"Amend/revoke leads: {s['affected_document_leads']} ({s['affected_targets_resolved']} with a target in the volume).")
print("Leads only: nothing is admitted, merged, dated or changed.")
