"""Run the tests, then parse both WPA lists and cross-check the census. See README.md."""

import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_wpa"], cwd=HERE).returncode:
    sys.exit("Tests failed; nothing built.")
sys.path.insert(0, str(HERE))
import wpa  # noqa: E402

s = wpa.run(os.environ.get("REPO_ROOT", "."), HERE, os.environ["OUTPUT_DIR"])
n, u = s["numbered"], s["unnumbered"]
print(f"Numbered list: {n['entries']} entries; {n['census_found_in_list']} of the census's {n['census_numbered_1_8030']} "
      f"numbered orders 1-8030 found ({n['coverage_pct']}%); {n['year_disagreements']} year disagreements; "
      f"{n['list_orders_not_in_census']} listed orders not in the census.")
print(f"Unnumbered list: {u['entries']} entries ({u['years']}); {u['paired_with_date']} with a confidently paired date; "
      f"the census holds {u['census_identities_unnumbered_today']} unnumbered identities today.")
print("Census leads only: nothing is admitted, merged or changed.")
