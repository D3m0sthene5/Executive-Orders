"""Tesseract readings on the exact crop PNG. psm 6 is the project's own setting (jobs/_lib/eo_pdf.py); psm 3 is also run
(automatic page segmentation, the setting that can follow two columns). eng.traineddata as installed (tessdata, not fast)."""
import os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import readings as R

TESS = "C:/Users/danie/AppData/Local/Programs/Tesseract-OCR/tesseract.exe"
ver = subprocess.run([TESS, "--version"], capture_output=True, text=True).stdout.splitlines()[0]
done = R.done_keys()
for psm in (6, 3):
    eng = f"tesseract-psm{psm}"
    for p in R.passages():
        if (p["id"], eng) in done:
            continue
        t = time.time()
        r = subprocess.run([TESS, p["crop_png_path"], "stdout", "-l", "eng", "--psm", str(psm)], capture_output=True,
                           text=True, encoding="utf-8", env={**os.environ, "OMP_THREAD_LIMIT": "1"})
        rec = R.base(p, eng, ver, {"lang": "eng", "psm": psm, "dpi_of_image": 300})
        rec.update({"output_text": r.stdout.rstrip("\n"), "seconds": round(time.time() - t, 2), "gpu_mem_peak_mib": 0})
        R.append(rec)
print("tesseract done")
