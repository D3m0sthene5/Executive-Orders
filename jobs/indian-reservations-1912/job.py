"""Run the tests, then split the 1912 Indian Reservations volume into one text per act. See README.md."""

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_ir"], cwd=HERE).returncode:
    sys.exit("Tests failed; nothing built.")
sys.path.insert(0, str(HERE))
import ir  # noqa: E402

s = ir.run(os.environ.get("REPO_ROOT", "."), HERE, os.environ["OUTPUT_DIR"], ir.wpa_dir_from_env())
k, d = s["acts_by_kind"], s["dates"]
print(f"{s['volume']}: {s['acts']} presidential acts ({k.get('order', 0)} orders, {k.get('indorsement_or_approval', 0)} "
      f"indorsements or approvals, {k.get('proclamation', 0)} proclamations) under {s['states']} states and "
      f"{s['reservation_headings']} reservation headings; PDF check: {s['pdf_check']}.")
print(f"  Dates: {d['full']} full, {d['year_month']} month only, {d['year_only']} year only, {d['undated']} unread; "
      f"{d['repaired']} needed digit repair; {d['out_of_term']} fall outside the signer's term. {s['acts_before_1900']} acts are before 1900.")
if s["wpa_lists_read"]:
    print(f"  WPA numbered list: {s['numbered_matches']} acts paired ({s['numbered_match_level']}); "
          f"{len(s['numbered_ties_not_paired'])} ties left unpaired; {s['wpa_ir_citations']} IR page citations "
          f"({s['wpa_ir_citation_resolution']}).")
    print(f"  Lord's unnumbered list: {s['lord_ir_citations']} IR citations in {s['lord_rows_citing_ir']} rows "
          f"({s['lord_resolution']}).")
else:
    print(f"  WPA lists not found at {s['wpa_dir']}: no numbered pairing and no Lord crosswalk this run.")
print(f"  Census: {s['acts_by_census_state']}; leads {s['census_leads']}; fragments {s['fragments']}; "
      f"decided orders paired {s['decided_orders_matched']}.")
print(f"  Ending leads: {s['ending_lead_rows']} rows ({s['ending_targets']}).")
print("Leads only: nothing is admitted, merged, dated or changed.")
