"""Pinakes HTR: a second machine reading of the ProQuest scans whose text failed Pinakes's quality screen.

Pinakes (jobs/pinakes-proquest-ingest) gives every order a text: the PDF's own layer, or tesseract at 200 dpi.
About 310 orders still score `text_usable: no`, mostly handwritten originals, where tesseract writes word-shaped
nonsense. This job reads those scans again, on the owner's PC and nowhere else, two ways:

  tesseract300   pages rendered at 300 dpi, contrast-stretched and despeckled, read with tesseract's automatic
                 layout (--psm 3); rescues faint typewriting and carbon copies, not handwriting
  trocr          the same pages cut into text lines (tesseract's line boxes, or an ink projection profile where
                 tesseract finds too few) and read by Microsoft's TrOCR handwriting model on the GPU, with a
                 per-line confidence from the beam search

Nothing leaves the machine. Every text written here is a machine hypothesis to search and route by: it is not a
source text, it does not replace the Pinakes text, it is never a fragment the readiness tracker counts, and it does
not move the certified count. A handwriting model's decoder writes fluent English even where it misreads, so the
word-shape screen says little about TrOCR output; its confidence and a person's page check say more.
SAMPLE_FOR_PAGE_CHECK.csv names ten orders for that check.

Outputs (output/): HTR.csv (one row per order), texts/EO_<n>.<method>.txt, LINES.jsonl (every TrOCR line: page,
box, segmentation, confidence, text), PROVENANCE.json (programs, model revision, settings), SAMPLE_FOR_PAGE_CHECK.csv,
REPORT.md, SUMMARY.json. Reruns skip orders already read with the same settings (same PDF bytes, same method key).
"""
from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import eo_pdf  # noqa: E402

JOB = "pinakes-htr"
PINAKES_ORDERS = "jobs/pinakes-proquest-ingest/output/ORDERS.csv"
DPI = 300
MAX_PAGES = 40
MODEL_ID = os.environ.get("HTR_MODEL", "microsoft/trocr-large-handwritten")
METHOD_KEY = f"tess300-psm3+trocr:{MODEL_ID}:dpi{DPI}:v3"
LOW_CONF = 0.5          # a TrOCR line below this beam confidence is counted as doubtful
MIN_LINE_H, MIN_LINE_W, PAD = 14, 30, 6
MIN_TYPICAL_H, MAX_CUTS = 24, 6   # a handwritten line at 300 dpi is taller than 24 px; a band is cut into at most 6
MAX_ASPECT = 18         # wider lines are split at an ink gap so TrOCR's 384x384 input is not squashed flat
STATUS = {"status": "machine_hypothesis", "acceptable_as_source_text": False, "needs_page_check": True,
          "counts_toward_certification": False}

HTR_FIELDS = ["instrument_id", "year", "file", "folder", "sha256", "pages", "method_key",
              "prior_text_source", "prior_text_quality", "prior_common_share",
              "tess300_text_path", "tess300_chars", "tess300_quality", "tess300_common_share", "tess300_mean_word_conf",
              "tess300_passes_screen",
              "trocr_text_path", "trocr_lines", "trocr_chars", "trocr_quality", "trocr_common_share", "trocr_mean_conf",
              "trocr_doubtful_lines", "trocr_passes_screen", "segmentation", "error"]
SAMPLE_FIELDS = ["instrument_id", "year", "pages", "pdf_path", "pinakes_text_path", "tess300_text_path", "trocr_text_path",
                 "trocr_mean_conf", "checked_by", "page_kind (handwritten/typed/mixed/other)", "words_checked",
                 "words_wrong_trocr", "words_wrong_tess300", "notes"]


# ---------- images ----------

def otsu(gray):
    """Otsu threshold of a uint8 numpy array."""
    import numpy as np
    hist = np.bincount(gray.ravel(), minlength=256).astype(float)
    total = gray.size
    cum, cum_mean = np.cumsum(hist), np.cumsum(hist * np.arange(256))
    w0 = cum / total
    w1 = 1 - w0
    with np.errstate(divide="ignore", invalid="ignore"):
        m0 = cum_mean / np.maximum(cum, 1)
        m1 = (cum_mean[-1] - cum_mean) / np.maximum(total - cum, 1)
        between = w0 * w1 * (m0 - m1) ** 2
    return int(np.nanargmax(between))


def clean_page(src, dst):
    """Contrast-stretch and despeckle a rendered page; returns the path written."""
    from PIL import Image, ImageFilter, ImageOps
    with Image.open(src) as im:
        g = ImageOps.autocontrast(im.convert("L"), cutoff=1).filter(ImageFilter.MedianFilter(3))
        g.save(dst)
    return dst


def ink_mask(gray, t=None):
    t = otsu(gray) if t is None else t
    ink = gray <= t
    h, w = ink.shape
    mh, mw = int(h * 0.02), int(w * 0.02)  # scanner edges and binding shadow
    ink[:mh, :] = False
    ink[h - mh:, :] = False
    ink[:, :mw] = False
    ink[:, w - mw:] = False
    return ink


def projection_lines(gray, t=None):
    """Text-line boxes (x0, y0, x1, y1) from the row ink profile: crude, but works on handwriting."""
    import numpy as np
    ink = ink_mask(gray, t)
    h, w = ink.shape
    row = ink.sum(axis=1) / max(w, 1)
    k = 9
    row = np.convolve(row, np.ones(k) / k, mode="same")
    nz = row[row > 0]
    if not len(nz):
        return []
    thr = max(0.004, 0.25 * float(nz.mean()))
    on = row > thr
    bands, start = [], None
    for y, v in enumerate(on):
        if v and start is None:
            start = y
        elif not v and start is not None:
            bands.append([start, y])
            start = None
    if start is not None:
        bands.append([start, h])
    merged = []
    for b in bands:
        if merged and b[0] - merged[-1][1] < 8:
            merged[-1][1] = b[1]
        else:
            merged.append(b)
    heights = [b[1] - b[0] for b in merged if b[1] - b[0] >= MIN_LINE_H]
    typical = max(MIN_TYPICAL_H, int(statistics.median(heights))) if heights else 0
    out = []
    for y0, y1 in merged:
        if y1 - y0 < max(MIN_LINE_H, 0.5 * typical):
            continue
        parts = [(y0, y1)]
        if typical and y1 - y0 > 1.7 * typical:  # two lines touching: cut at the faintest rows
            n = min(MAX_CUTS, round((y1 - y0) / typical))
            cuts = [y0]
            for i in range(1, n):
                c = y0 + i * (y1 - y0) // n
                lo, hi = max(y0, c - typical // 3), min(y1, c + typical // 3)
                cuts.append(int(lo + np.argmin(row[lo:hi])) if hi > lo else c)
            cuts.append(y1)
            parts = list(zip(cuts[:-1], cuts[1:]))
        for a, b in parts:
            cols = np.where(ink[a:b].any(axis=0))[0]
            if len(cols) < MIN_LINE_W:
                continue
            x0, x1 = int(np.percentile(cols, 1)), int(np.percentile(cols, 99))
            if x1 - x0 >= MIN_LINE_W:
                out.append((max(0, x0 - PAD), max(0, a - PAD), min(w, x1 + PAD), min(h, b + PAD)))
    return out


def split_wide(gray, box, t):
    """Split a box wider than MAX_ASPECT at the emptiest ink column near its middle, recursively."""
    import numpy as np
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, max(1, y1 - y0)
    if bw / bh <= MAX_ASPECT:
        return [box]
    ink = gray[y0:y1, x0:x1] <= t
    col = ink.sum(axis=0)
    mid = bw // 2
    lo, hi = int(bw * 0.3), int(bw * 0.7)
    c = lo + int(np.argmin(col[lo:hi])) if hi > lo else mid
    if c <= 0 or c >= bw:
        return [box]
    return split_wide(gray, (x0, y0, x0 + c, y1), t) + split_wide(gray, (x0 + c, y0, x1, y1), t)


def ink_share(gray, box, t):
    x0, y0, x1, y1 = box
    crop = gray[y0:y1, x0:x1]
    return float((crop <= t).mean()) if crop.size else 0.0


# ---------- tesseract ----------

def parse_tsv(tsv):
    """tesseract TSV -> (text, mean word confidence, line boxes)."""
    lines, boxes, confs = {}, [], []
    rows = [r.split("\t") for r in (tsv or "").splitlines()[1:]]
    for r in rows:
        if len(r) < 12:
            continue
        level, block, par, line = r[0], r[2], r[3], r[4]
        left, top, width, height, conf, word = int(r[6]), int(r[7]), int(r[8]), int(r[9]), float(r[10]), r[11]
        key = (int(block), int(par), int(line))
        if level == "4":
            boxes.append((left, top, left + width, top + height))
        elif level == "5" and word.strip():
            lines.setdefault(key, []).append(word)
            if conf >= 0:
                confs.append(conf)
    text = "\n".join(" ".join(ws) for _, ws in sorted(lines.items()))
    return text, (round(sum(confs) / len(confs), 1) if confs else None), boxes


def tesseract_page(png, timeout=240):
    env = {**os.environ, "OMP_THREAD_LIMIT": "1"}
    r = subprocess.run(["tesseract", png, "stdout", "-l", "eng", "--psm", "3", "tsv"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
    return r.stdout if r.returncode == 0 else ""


def merge_rows(boxes):
    """Join boxes that sit on the same text row (tesseract breaks a handwritten line into word fragments), without
    letting a slanted line chain into the next: a join may not make the row taller than 1.6x its taller part."""
    rows, base = [], []   # base: the tallest single fragment in each row, so joins cannot chain a row down the page
    for b in sorted(boxes, key=lambda b: ((b[1] + b[3]) / 2, b[0])):
        bh = b[3] - b[1]
        for i, r in enumerate(rows):
            overlap = min(r[3], b[3]) - max(r[1], b[1])
            if overlap > 0.5 * min(r[3] - r[1], bh):
                u = (min(r[0], b[0]), min(r[1], b[1]), max(r[2], b[2]), max(r[3], b[3]))
                if u[3] - u[1] <= 1.6 * max(base[i], bh):
                    rows[i], base[i] = u, max(base[i], bh)
                    break
        else:
            rows.append(tuple(b))
            base.append(bh)
    if rows:
        typical = statistics.median(r[3] - r[1] for r in rows)
        rows = [r for r in rows if r[3] - r[1] >= 0.5 * typical]
    return sorted(rows, key=lambda r: (r[1], r[0]))


def line_boxes(gray, tess_boxes):
    """Use tesseract's lines where they cover most of the ink rows; otherwise the projection profile."""
    import numpy as np
    t = otsu(gray)
    ink = ink_mask(gray, t)
    ink_rows = ink.any(axis=1)
    covered = np.zeros(len(ink_rows), dtype=bool)
    good = merge_rows([b for b in tess_boxes if b[3] - b[1] >= MIN_LINE_H and b[2] - b[0] >= MIN_LINE_W])
    for _, y0, _, y1 in good:
        covered[y0:y1] = True
    share = (covered & ink_rows).sum() / max(1, ink_rows.sum())
    if good and share >= 0.6:
        h, w = gray.shape
        boxes, how = [(max(0, a - PAD), max(0, b - PAD), min(w, c + PAD), min(h, d + PAD)) for a, b, c, d in good], "tesseract"
    else:
        boxes, how = projection_lines(gray, t), "projection"
    out = []
    for b in boxes:
        out.extend(split_wide(gray, b, t))
    return [b for b in out if ink_share(gray, b, t) >= 0.005], how


# ---------- stage 1: render, clean, tesseract, segment (CPU, one process per order) ----------

def prepare_order(task):
    """Render and read one order's pages. Returns a dict; page images stay in task['work'] for stage 2."""
    import numpy as np
    from PIL import Image
    iid, pdf, work = task["instrument_id"], task["pdf"], task["work"]
    res = {"instrument_id": iid, "pages": [], "tess_text": "", "tess_conf": None, "segments": [], "segmentation": "", "error": ""}
    try:
        os.makedirs(work, exist_ok=True)
        r = subprocess.run(["pdftoppm", "-r", str(DPI), "-gray", "-l", str(MAX_PAGES), "-png", pdf, os.path.join(work, "raw")],
                           capture_output=True, text=True, timeout=600)
        if r.returncode:
            res["error"] = "pdftoppm: " + (r.stderr or "")[-200:]
            return res
        texts, confs, hows = [], [], []
        for i, raw in enumerate(sorted(f for f in os.listdir(work) if f.startswith("raw") and f.endswith(".png"))):
            page = clean_page(os.path.join(work, raw), os.path.join(work, f"page-{i:03d}.png"))
            os.remove(os.path.join(work, raw))
            text, conf, tboxes = parse_tsv(tesseract_page(page))
            texts.append(text)
            if conf is not None:
                confs.append(conf)
            with Image.open(page) as im:
                gray = np.asarray(im.convert("L"))
            boxes, how = line_boxes(gray, tboxes)
            hows.append(how)
            res["pages"].append(page)
            res["segments"].extend((i, b, how) for b in boxes)
        res["tess_text"] = "\n\f\n".join(texts).strip()
        res["tess_conf"] = round(sum(confs) / len(confs), 1) if confs else None
        res["segmentation"] = "/".join(sorted(set(hows)))
    except subprocess.TimeoutExpired:
        res["error"] = "timeout"
    except Exception as exc:
        res["error"] = f"{type(exc).__name__}: {exc}"[:200]
    return res


# ---------- stage 2: TrOCR on the GPU ----------

class TrOCR:
    def __init__(self, model_id=MODEL_ID, batch=32, beams=4):
        import torch
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.processor = TrOCRProcessor.from_pretrained(model_id)
        self.model = VisionEncoderDecoderModel.from_pretrained(model_id, torch_dtype=self.dtype).to(self.device).eval()
        self.batch, self.beams = batch, beams
        self.model_id = model_id

    def read(self, crops):
        """PIL images -> [(text, confidence 0-1)]."""
        out = []
        for i in range(0, len(crops), self.batch):
            chunk = [c.convert("RGB") for c in crops[i:i + self.batch]]
            px = self.processor(images=chunk, return_tensors="pt").pixel_values.to(self.device, self.dtype)
            with self.torch.inference_mode():
                g = self.model.generate(px, num_beams=self.beams, max_new_tokens=96, output_scores=True,
                                        return_dict_in_generate=True, early_stopping=True)
            texts = self.processor.batch_decode(g.sequences, skip_special_tokens=True)
            scores = g.sequences_scores.float().exp().tolist() if getattr(g, "sequences_scores", None) is not None else [None] * len(texts)
            out.extend((t.strip(), round(s, 3) if s is not None else None) for t, s in zip(texts, scores))
        return out

    def describe(self):
        info = {"model_id": self.model_id, "device": self.device, "dtype": str(self.dtype).replace("torch.", ""),
                "beams": self.beams, "torch": self.torch.__version__}
        try:
            import transformers
            info["transformers"] = transformers.__version__
            from huggingface_hub import snapshot_download
            path = snapshot_download(self.model_id, local_files_only=True)
            info["model_revision"] = os.path.basename(path)
        except Exception:
            pass
        if self.device == "cuda":
            info["gpu"] = self.torch.cuda.get_device_name(0)
            info["cuda"] = self.torch.version.cuda
        return info


def read_lines(prep, reader):
    from PIL import Image
    crops, meta, opened = [], [], {}
    for page_i, box, how in prep["segments"]:
        if page_i not in opened:
            opened[page_i] = Image.open(prep["pages"][page_i]).convert("L")
        crops.append(opened[page_i].crop(box))
        meta.append((page_i, box, how))
    results = reader.read(crops) if crops else []
    for im in opened.values():
        im.close()
    lines = [{"page": p + 1, "box": list(b), "segmentation": h, "text": t, "conf": c} for (p, b, h), (t, c) in zip(meta, results)]
    by_page = {}
    for ln in lines:
        if ln["text"]:
            by_page.setdefault(ln["page"], []).append(ln["text"])
    text = "\n\f\n".join("\n".join(by_page[p]) for p in sorted(by_page)).strip()
    return text, lines


# ---------- run ----------

def score(text):
    q = eo_pdf.text_quality(text) if text else 0.0
    c = eo_pdf.common_share(text) if text else 0.0
    return q, c, "yes" if eo_pdf.usable(len(text or ""), q, c) else "no"


def load_targets(root):
    path = os.path.join(root, PINAKES_ORDERS)
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [r for r in rows if r.get("text_usable") != "yes" and r.get("file")]


def load_done(out_dir):
    path = os.path.join(out_dir, "HTR.csv")
    if not os.path.exists(path):
        return {}
    with open(path, newline="", encoding="utf-8") as fh:
        return {(r["sha256"], r["method_key"]): r for r in csv.DictReader(fh) if not r.get("error")}


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def tool_version(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return ((r.stdout or "") + (r.stderr or "")).strip().splitlines()[0]
    except Exception:
        return ""


def pick_sample(rows, n=10):
    ok = sorted((r for r in rows if not r.get("error")), key=lambda r: (r.get("year") or "", r["instrument_id"]))
    if len(ok) <= n:
        return ok
    step = len(ok) / n
    return [ok[int(i * step)] for i in range(n)]


def run(root, out_dir, reader=None, prepare=prepare_order, workers=None, limit=None):
    started = time.time()
    os.makedirs(os.path.join(out_dir, "texts"), exist_ok=True)
    targets = load_targets(root)
    if limit:
        targets = targets[:limit]
    done = load_done(out_dir)
    lines_path = os.path.join(out_dir, "LINES.jsonl")
    prior_lines = []
    if os.path.exists(lines_path):
        with open(lines_path, encoding="utf-8") as fh:
            prior_lines = [json.loads(x) for x in fh if x.strip()]
    rows, todo = [], []
    for t in targets:
        key = (t["sha256"], METHOD_KEY)
        if key in done:
            rows.append(done[key])
        else:
            todo.append(t)
    keep_ids = {r["instrument_id"] for r in rows}
    all_lines = [ln for ln in prior_lines if ln.get("instrument_id") in keep_ids]
    print(f"HTR: {len(targets)} orders below the screen, {len(rows)} already read, {len(todo)} to read", flush=True)

    work_root = tempfile.mkdtemp(prefix="pinakes-htr-")
    tasks = [{"instrument_id": t["instrument_id"], "pdf": os.path.join(root, t["folder"], t["file"]),
              "work": os.path.join(work_root, hashlib.sha1(t["instrument_id"].encode()).hexdigest()[:12])} for t in todo]
    by_id = {t["instrument_id"]: t for t in todo}
    if todo and reader is None:
        reader = TrOCR()
    workers = workers or max(1, (os.cpu_count() or 2) - 1)
    n = 0
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(prepare, task) for task in tasks] if prepare is prepare_order else None
            results = (f.result() for f in futures) if futures else (prepare(task) for task in tasks)
            for prep in results:
                t = by_id[prep["instrument_id"]]
                stem = "texts/" + t["instrument_id"].replace(":", "_")
                row = {k: t.get(k, "") for k in ("instrument_id", "year", "file", "folder", "sha256", "pages")}
                row.update({"method_key": METHOD_KEY, "prior_text_source": t.get("text_source", ""),
                            "prior_text_quality": t.get("text_quality", ""), "prior_common_share": t.get("common_share", ""),
                            "segmentation": prep.get("segmentation", ""), "error": prep.get("error", "")})
                if not prep.get("error"):
                    tess = prep["tess_text"]
                    q, c, ok = score(tess)
                    if tess:
                        with open(os.path.join(out_dir, stem + ".tess300.txt"), "w", encoding="utf-8") as fh:
                            fh.write(tess)
                    row.update({"tess300_text_path": stem + ".tess300.txt" if tess else "", "tess300_chars": len(tess),
                                "tess300_quality": q, "tess300_common_share": c, "tess300_mean_word_conf": prep["tess_conf"],
                                "tess300_passes_screen": ok})
                    try:
                        text, lines = read_lines(prep, reader)
                    except Exception as exc:
                        text, lines = "", []
                        row["error"] = f"trocr: {type(exc).__name__}: {exc}"[:200]
                    q, c, ok = score(text)
                    confs = [ln["conf"] for ln in lines if ln["conf"] is not None and ln["text"]]
                    if text:
                        with open(os.path.join(out_dir, stem + ".trocr.txt"), "w", encoding="utf-8") as fh:
                            fh.write(text)
                    row.update({"trocr_text_path": stem + ".trocr.txt" if text else "", "trocr_lines": len(lines),
                                "trocr_chars": len(text), "trocr_quality": q, "trocr_common_share": c,
                                "trocr_mean_conf": round(statistics.mean(confs), 3) if confs else "",
                                "trocr_doubtful_lines": sum(1 for x in confs if x < LOW_CONF), "trocr_passes_screen": ok})
                    all_lines.extend({"instrument_id": t["instrument_id"], **ln} for ln in lines)
                shutil.rmtree(os.path.dirname(prep["pages"][0]) if prep.get("pages") else "", ignore_errors=True)
                rows.append(row)
                n += 1
                if n % 25 == 0 or n == len(todo):
                    print(f"HTR {n}/{len(todo)}", flush=True)
                    write_csv(os.path.join(out_dir, "HTR.csv"), HTR_FIELDS, sorted(rows, key=lambda r: r["instrument_id"]))
    finally:
        shutil.rmtree(work_root, ignore_errors=True)

    rows.sort(key=lambda r: r["instrument_id"])
    write_csv(os.path.join(out_dir, "HTR.csv"), HTR_FIELDS, rows)
    with open(lines_path, "w", encoding="utf-8") as fh:
        for ln in all_lines:
            fh.write(json.dumps(ln, ensure_ascii=False) + "\n")
    sample = []
    for r in pick_sample(rows):
        sample.append({"instrument_id": r["instrument_id"], "year": r.get("year", ""), "pages": r.get("pages", ""),
                       "pdf_path": f"{r['folder']}/{r['file']}",
                       "pinakes_text_path": "jobs/pinakes-proquest-ingest/output/texts/" + r["instrument_id"].replace(":", "_") + ".txt",
                       "tess300_text_path": f"jobs/{JOB}/output/{r['tess300_text_path']}" if r.get("tess300_text_path") else "",
                       "trocr_text_path": f"jobs/{JOB}/output/{r['trocr_text_path']}" if r.get("trocr_text_path") else "",
                       "trocr_mean_conf": r.get("trocr_mean_conf", "")})
    write_csv(os.path.join(out_dir, "SAMPLE_FOR_PAGE_CHECK.csv"), SAMPLE_FIELDS, sample)

    provenance = {"job": JOB, "method_key": METHOD_KEY, "dpi": DPI, "max_pages": MAX_PAGES, "low_conf": LOW_CONF, **STATUS,
                  "tesseract": tool_version(["tesseract", "--version"]), "pdftoppm": tool_version(["pdftoppm", "-v"]),
                  "trocr": reader.describe() if reader is not None and hasattr(reader, "describe") else {},
                  "machine": os.environ.get("COMPUTERNAME", ""), "ran_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "seconds": round(time.time() - started)}
    with open(os.path.join(out_dir, "PROVENANCE.json"), "w", encoding="utf-8") as fh:
        json.dump(provenance, fh, indent=2)
    summary = summarize(rows, len(todo), provenance)
    with open(os.path.join(out_dir, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    with open(os.path.join(out_dir, "REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write(report(summary))
    return summary


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def summarize(rows, read_now, provenance):
    ok = [r for r in rows if not r.get("error")]
    confs = sorted(c for c in (_num(r.get("trocr_mean_conf")) for r in ok) if c is not None)
    quart = (lambda p: round(confs[min(len(confs) - 1, int(p * len(confs)))], 3)) if confs else (lambda p: None)
    tess_ok = sum(r.get("tess300_passes_screen") == "yes" for r in ok)
    trocr_ok = sum(r.get("trocr_passes_screen") == "yes" for r in ok)
    return {"orders": len(rows), "read_this_run": read_now, "errors": len(rows) - len(ok),
            "tess300_passes_screen": tess_ok, "trocr_passes_screen": trocr_ok,
            "either_passes_screen": sum(r.get("tess300_passes_screen") == "yes" or r.get("trocr_passes_screen") == "yes" for r in ok),
            "trocr_lines": sum(int(_num(r.get("trocr_lines")) or 0) for r in ok),
            "trocr_doubtful_lines": sum(int(_num(r.get("trocr_doubtful_lines")) or 0) for r in ok),
            "trocr_conf_quartiles": [quart(0.25), quart(0.5), quart(0.75)],
            "trocr_conf_ge_0_8": sum(c >= 0.8 for c in confs),
            "segmentation": {k: sum(r.get("segmentation") == k for r in ok) for k in sorted({r.get("segmentation", "") for r in ok})},
            "pages": sum(int(_num(r.get("pages")) or 0) for r in ok), **STATUS,
            "model": (provenance.get("trocr") or {}).get("model_id", MODEL_ID), "gpu": (provenance.get("trocr") or {}).get("gpu", ""),
            "seconds": provenance["seconds"]}


def report(s):
    q = s["trocr_conf_quartiles"]
    lines = ["# Pinakes HTR: second reading of the scans below the quality screen", "",
             f"Generated {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} on the owner's PC "
             f"({s['gpu'] or 'CPU'}), in {s['seconds']} s. Nothing was sent off the machine.", "",
             f"**{s['orders']} orders** ({s['pages']} pages) whose Pinakes text failed the screen were read again; "
             f"{s['read_this_run']} this run, {s['errors']} with errors.", "",
             "| Reading | Orders passing the word-shape screen |", "|---|---:|",
             f"| tesseract, 300 dpi, cleaned, automatic layout | {s['tess300_passes_screen']} |",
             f"| TrOCR handwriting model ({s['model']}) | {s['trocr_passes_screen']} |",
             f"| Either | {s['either_passes_screen']} |", "",
             f"TrOCR read {s['trocr_lines']} lines; {s['trocr_doubtful_lines']} are below confidence {LOW_CONF}. "
             f"Mean line confidence per order, quartiles: {q[0]} / {q[1]} / {q[2]}; {s['trocr_conf_ge_0_8']} orders average 0.8 or more. "
             f"Line segmentation: " + ", ".join(f"{k or 'none'} {v}" for k, v in s["segmentation"].items()) + ".", "",
             "## What these texts are", "",
             "Machine hypotheses for searching and routing. They are not source texts, they do not replace the Pinakes texts, "
             "the readiness tracker does not read them, and they do not move the certified count "
             "(`acceptable_as_source_text: false`, `needs_page_check: true`, `counts_toward_certification: false`). "
             "A handwriting model writes fluent English even where it misreads, so passing the word-shape screen is weak "
             "evidence for TrOCR; its confidence is better, and a person's page check is what tells.", "",
             "## Next", "",
             "A person compares the ten orders in `SAMPLE_FOR_PAGE_CHECK.csv` against their PDFs and fills in the blank "
             "columns (page kind, words checked, words wrong per reading). That measures the error rate and says whether "
             "a model trained on these hands (eScriptorium/Kraken, local) is worth the effort.", ""]
    return "\n".join(lines)


def main():
    root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
    out_dir = os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output")
    limit = int(os.environ["HTR_LIMIT"]) if os.environ.get("HTR_LIMIT") else None
    if not eo_pdf.ocr_available():
        sys.exit("pdftoppm or tesseract not on PATH")
    s = run(root, out_dir, limit=limit)
    print(json.dumps({k: s[k] for k in ("orders", "read_this_run", "errors", "tess300_passes_screen", "trocr_passes_screen")}))


if __name__ == "__main__":
    main()
