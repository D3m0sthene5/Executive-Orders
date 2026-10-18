"""Run the tests, then read the OFR 1989 Codification: codified texts, SOURCE-line dates and the disposition table. See README.md."""

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_codification"], cwd=HERE).returncode:
    sys.exit("Tests failed; nothing built.")
sys.dont_write_bytecode = True   # no __pycache__ inside the job folder
sys.path.insert(0, str(HERE))
import codification  # noqa: E402

s = codification.run(os.environ.get("REPO_ROOT", "."), HERE, os.environ["OUTPUT_DIR"])
b, t = s["body"], s["disposition_table"]
print(f"{s['book']}. PDF check: {s['pdf_check']}.")
print(f"Codified texts: {b['eo_source_lines']} Executive Orders and {b['proclamation_source_lines']} proclamations found by their SOURCE lines; "
      f"{b['eo_with_exact_date']} EOs have an exact date (no date: {', '.join(b['eo_without_date']) or 'none'}); "
      f"confidence {b['eo_confidence']}; {b['fragmented_pages']} body pages came out a few words per line.")
print(f"  Census state: {b['census_state']}. Provisional status: {b['provisional_status']}. Checks: {b['checks']}.")
print(f"Disposition table: {t['rows']} rows ({t['numbered_rows']} numbered, {t['date_rows']} dated unnumbered); "
      f"{t['rows_without_disposition']} without a disposition; {t['orphan_fragments']} unpaired fragments; pairing {t['pairing_confidence']}.")
print(f"  Groups: {t['groups']}.")
print(f"  Rows split from one OCR piece: {[m['second_row'] for m in t['merged_row_splits']]}; stray digit pieces dropped: "
      f"{[(d['page'], d['text']) for d in t['stray_digit_pieces_dropped']]}; acting EOs rejected: {t['rejected_acting_documents'] or 'none'}.")
print(f"  EO {t['complete_eo_run'][0]}-{t['complete_eo_run'][1]} numbers not read: {t['complete_eo_run_gaps']}. "
      f"Numbered rows in the census: {t['numbered_keys_in_census']} of {t['distinct_numbered_keys']}.")
print(f"  Against the OFR online data read by later-events (revoked/superseded rows): {t['later_events_check_on_revoked_superseded']}.")
print(f"Unnumbered rows: {s['unnumbered_rows']}. Dated references: {s['reference_dates']}.")
print(f"Status leads: {s['status_leads']}.")
print(f"Census leads: {s['census_leads']}.")
print(f"Fragments (later_event_candidates only): {s['fragments']}.")
print("Leads only: nothing is admitted, merged, dated or changed. The codified texts are as amended to 1989-01-20, not originals.")
