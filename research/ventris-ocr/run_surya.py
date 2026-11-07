"""Surya 2.5 (surya-ocr 0.23.0) full-page OCR on each crop via the local transformers backend (engines/surya_hf.py)."""
import html, os, re, sys, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engines"))
import torch
from PIL import Image
import readings as R
from surya_hf import make_manager
from surya.recognition import RecognitionPredictor
import surya, transformers


def html_to_text(h):
    h = re.sub(r"<br\s*/?>", "\n", h)
    h = re.sub(r"</(p|div|tr|h[1-6]|li|caption)>", "\n", h)
    h = re.sub(r"</t[dh]>", "\t", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h)
    return re.sub(r"\n{2,}", "\n", h).strip()


mgr = make_manager()
mgr.start()
rp = RecognitionPredictor(mgr)
ver = f"surya-ocr {__import__('importlib.metadata').metadata.version('surya-ocr')}; checkpoint datalab-to/surya-ocr-2.5; transformers {transformers.__version__}; torch {torch.__version__}"
done = R.done_keys()
peak = 0
for p in R.passages():
    if (p["id"], "surya") in done:
        continue
    img = Image.open(p["crop_png_path"]).convert("RGB")
    torch.cuda.reset_peak_memory_stats()
    t = time.time()
    res = rp([img])
    dt = time.time() - t
    peak = max(peak, torch.cuda.max_memory_allocated() / 2**20)
    blocks = [(b.label, b.html) for b in res[0].blocks]
    txt = "\n".join(html_to_text(h) for lab, h in blocks if lab not in ("PageHeader", "PageFooter") or True)
    rec = R.base(p, "surya", ver, {"mode": "full_page", "dtype": "bfloat16", "decoding": "greedy", "backend": "transformers (engines/surya_hf.py)"},
                 prompt="surya built-in full-page prompt (surya.inference.prompts)")
    rec.update({"output_text": txt, "raw_output": [{"label": l, "html": h} for l, h in blocks], "seconds": round(dt, 2),
                "gpu_mem_peak_mib": round(torch.cuda.max_memory_allocated() / 2**20), "gpu_mem_reserved_mib": round(torch.cuda.max_memory_reserved() / 2**20)})
    R.append(rec)
    print(p["id"], round(dt, 1), len(txt), flush=True)
print("surya done; peak allocated MiB", round(peak))
