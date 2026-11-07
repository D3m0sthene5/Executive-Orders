"""GPO text layer readings: copied unchanged from PASSAGES.csv (text layer inside the crop, pdfium bounded text)."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import json
import readings as R
import pypdfium2

done = R.done_keys()
for p in R.passages():
    if (p["id"], "gpo-layer") in done:
        continue
    rec = R.base(p, "gpo-layer", "pdfium " + pypdfium2.PDFIUM_INFO.version if hasattr(pypdfium2, "PDFIUM_INFO") else "pdfium",
                 {"method": "textpage.get_text_bounded over crop box"})
    rec.update({"output_text": json.loads(p["gpo_text_layer_json"]) if "gpo_text_layer_json" in p else p["gpo_text_layer"], "seconds": 0.0, "gpu_mem_peak_mib": 0})
    R.append(rec)
print("gpo done")
