"""Run the tests, then split the 1912 Indian Reservations volume into one text per act. See README.md."""

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = str(pathlib.Path(os.environ.get("REPO_ROOT", ".")).resolve())
# the tests run from this folder, so they get the repo root as an absolute path (for the census)
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_ir"], cwd=HERE,
                  env=dict(os.environ, REPO_ROOT=REPO_ROOT)).returncode:
    sys.exit("Tests failed; nothing built.")
sys.path.insert(0, str(HERE))
import ir  # noqa: E402

s = ir.run(REPO_ROOT, HERE, os.environ["OUTPUT_DIR"], ir.wpa_dir_from_env())
k, d, o = s["acts_by_kind"], s["dates"], s["order_dates"]
print(f"{s['volume']}: {s['acts']} printed presidential acts ({k.get('order', 0)} orders, {k.get('indorsement_or_approval', 0)} "
      f"indorsements or approvals, {k.get('proclamation', 0)} proclamations) under {s['states']} states and "
      f"{s['reservation_headings']} reservation headings; PDF check: {s['pdf_check']}.")
print(f"  Printings: {s['orders']} distinct orders; {s['reprints']} acts reprint an order printed elsewhere in the book "
      f"({s['orders_printed_more_than_once']} orders printed more than once; for {s['orders_whose_printings_disagree_on_the_date']} "
      f"the printings disagree on the date, and {s['printings_off_their_order_date']} printings differ from the date taken).")
print(f"  Dates (printings): {d['full']} full, {d['year_month']} month only, {d['year_only']} year only, {d['undated']} unread; "
      f"{d['repaired']} needed digit repair; {d['out_of_term']} fall outside the signer's term. Confidence {s['confidence']}.")
print(f"  Dates (orders): {o['full']} full, {o['year_month']} month only, {o['year_only']} year only, {o['undated']} unread; "
      f"{s['orders_before_1900']} orders before 1900, {s['orders_from_1900']} from 1900 ({s['orders_by_decade']}).")
if s["wpa_lists_read"]:
    print(f"  WPA numbered list: {s['numbered_matches']} orders paired ({s['numbered_match_level']}); "
          f"{len(s['numbered_ties_not_paired'])} ties left unpaired; {s['numbered_reprints_inheriting_pairing']} reprints carry "
          f"their order's pairing; {s['wpa_ir_citations']} IR page citations ({s['wpa_ir_citation_resolution']}).")
    print(f"  Lord's unnumbered list: {s['lord_ir_citations']} IR citations in {s['lord_rows_citing_ir']} rows "
          f"({s['lord_resolution']}).")
else:
    print(f"  WPA lists not found at {s['wpa_dir']}: no numbered pairing and no Lord crosswalk this run.")
print(f"  Census: orders {s['orders_by_census_state']}; leads {s['census_leads']}; fragments {s['fragments']}; "
      f"decided orders paired {s['decided_orders_matched']}.")
print(f"  Ending leads: {s['ending_lead_rows']} rows ({s['ending_targets']}).")
print("Leads only: nothing is admitted, merged, dated or changed.")
