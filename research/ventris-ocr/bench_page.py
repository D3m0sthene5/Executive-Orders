"""Seconds per full page per engine (one 300-DPI Federal Register page, FR-1949-03-10 PDF page 8, 2574x3368 px), run one
engine at a time so the GPU is not shared. Writes BENCH.json. GPO's layer is read from the PDF, no OCR.
Run (ocr venv): python -I bench_page.py <engine>  with engine in tesseract6 tesseract3 surya paddle gpo ; merge by hand.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engines"))
PAGE = "C:/Users/danie/eo-ocr-work/test_p8.png"
TESS = "C:/Users/danie/AppData/Local/Programs/Tesseract-OCR/tesseract.exe"
eng = sys.argv[1]
res = {"engine": eng, "page_png": PAGE}
if eng.startswith("tesseract"):
    psm = eng[-1]
    t = time.time()
    subprocess.run([TESS, PAGE, "stdout", "-l", "eng", "--psm", psm], capture_output=True, env={**os.environ, "OMP_THREAD_LIMIT": "1"})
    res["seconds"] = round(time.time() - t, 2)
    res["note"] = "single thread (OMP_THREAD_LIMIT=1, as the project runs it)"
elif eng == "gpo":
    import pagetools as P
    import json as _j
    m = [_j.loads(l) for l in open(os.path.join(HERE, "SOURCES_MANIFEST.jsonl"))]
    sha = [x for x in m if x["key"] == "FR-1949-03-10"][0]["sha256"]
    pdf = P.open_pdf(sha)
    t = time.time()
    txt = pdf[7].get_textpage().get_text_range()
    res["seconds"] = round(time.time() - t, 3)
    res["chars"] = len(txt)
elif eng == "paddle":
    sys.modules["torch"] = None
    import paddle
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(lang="en", ocr_version="PP-OCRv5", device="gpu", use_doc_orientation_classify=False,
                    use_doc_unwarping=False, use_textline_orientation=False)
    ocr.predict(PAGE)  # warm-up
    t = time.time()
    r = ocr.predict(PAGE)
    res["seconds"] = round(time.time() - t, 2)
    res["gpu_mem_reserved_mib"] = round(paddle.device.cuda.max_memory_reserved() / 2**20)
    res["note"] = "after one warm-up call"
elif eng == "surya":
    import torch
    from PIL import Image
    from surya_hf import make_manager
    from surya.recognition import RecognitionPredictor
    m = make_manager()
    m.start()
    rp = RecognitionPredictor(m)
    img = Image.open(PAGE).convert("RGB")
    torch.cuda.reset_peak_memory_stats()
    t = time.time()
    rp([img])
    res["seconds"] = round(time.time() - t, 2)
    res["gpu_mem_allocated_peak_mib"] = round(torch.cuda.max_memory_allocated() / 2**20)
    res["gpu_mem_reserved_peak_mib"] = round(torch.cuda.max_memory_reserved() / 2**20)
    res["note"] = "full-page mode, transformers backend, reference PyTorch kernels for the linear-attention layers"
print(json.dumps(res))
with open(os.path.join(HERE, "BENCH.jsonl"), "a", encoding="utf-8", newline="\n") as fh:
    fh.write(json.dumps(res) + "\n")
