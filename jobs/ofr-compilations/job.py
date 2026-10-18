"""Run the tests, then split the OFR compilation volumes into one text per order. See README.md."""

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_ofr"], cwd=HERE).returncode:
    sys.exit("Tests failed; nothing built.")
sys.path.insert(0, str(HERE))
import ofr  # noqa: E402

s = ofr.run(os.environ.get("REPO_ROOT", "."), HERE, os.environ["OUTPUT_DIR"])
for v in s["volumes"]:
    print(f"{v['volume']}: {v['orders_printed']} orders printed (EO {v['printed_range'][0]}-{v['printed_range'][1]}; "
          f"lettered {', '.join(v['lettered_orders']) or 'none'}); confidence {v['confidence']}; PDF check: {v['pdf_check']}.")
    print(f"  Census: {v['census_ids_in_range_with_text']} of {v['census_ids_in_range']} census ids in range have a text here; "
          f"leads {v['census_leads']}.")
    print(f"  Decided orders with a text here: {v['decided_orders_with_text']} "
          f"({v['decided_orders_original_text_step_open']} had the original_text step open). Fragments: {v['fragments']}.")
    print(f"  Table 2: {v['table2_entries']} orders listed; month/day agrees with the heading for "
          f"{v['table2_month_day_agrees_with_heading']} of the {v['table2_day_read_for_printed_orders']} whose day was read. Table 3: {v['table3_paired_lines']} paired lines "
          f"({v['table3_executive_order_lines']} on executive orders), {v['table3_unpaired_number_lines']} unpaired.")
print("Leads only: nothing is admitted, merged, dated or changed.")
