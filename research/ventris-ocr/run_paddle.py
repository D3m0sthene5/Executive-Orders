"""PaddleOCR 3.x (PP-OCRv5, GPU) on each crop. Text is rec_texts in the order PaddleOCR returns, joined by newlines."""
import os, sys, time
# paddlepaddle-gpu bundles cuDNN 12 and torch (cu130) bundles cuDNN 13 under the same DLL names; importing both in one
# process fails (WinError 127). PaddleOCR only imports torch through modelscope for logging, so hide torch here.
sys.modules["torch"] = None
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import readings as R
import paddle, paddleocr
from paddleocr import PaddleOCR

ocr = PaddleOCR(lang="en", ocr_version="PP-OCRv5", device="gpu", use_doc_orientation_classify=False,
                use_doc_unwarping=False, use_textline_orientation=False)
ver = f"paddleocr {paddleocr.__version__}; paddlepaddle-gpu {paddle.__version__}; PP-OCRv5 lang=en"
done = R.done_keys()
for p in R.passages():
    if (p["id"], "paddleocr") in done:
        continue
    t = time.time()
    res = ocr.predict(p["crop_png_path"])
    dt = time.time() - t
    texts = res[0]["rec_texts"] if res else []
    mem = paddle.device.cuda.max_memory_reserved() / 2**20
    rec = R.base(p, "paddleocr", ver, {"pipeline": "PaddleOCR.predict", "ocr_version": "PP-OCRv5", "lang": "en", "device": "gpu",
                                       "orientation_classify": False, "unwarping": False, "textline_orientation": False})
    rec.update({"output_text": "\n".join(texts), "seconds": round(dt, 2), "gpu_mem_peak_mib": round(mem)})
    R.append(rec)
    print(p["id"], round(dt, 1), len(texts), flush=True)
print("paddle done")
