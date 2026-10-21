"""The contextual reading for Pinakes HTR: a local vision-language model reads each whole page.

TrOCR and tesseract (htr.py) read what the ink shows, line by line; a vision-language model reads the page the way a
person does, using the sense of the sentence. Each fails differently, which is the point: compare.py lines the
readings up word by word, and where they agree the reading is likelier right; where they disagree is exactly where a
person should look. The model runs on the owner's GPU (default Qwen/Qwen2.5-VL-3B-Instruct, `VLM_MODEL` to change) and
nothing leaves the machine. Its text is a machine hypothesis like the others: it may supply plausible words where the
ink is illegible, which is why it is never used alone.

Writes texts/EO_<n>.vlm.txt and VLM.csv (one row per order: pages, characters, method key, seconds, error) into the
same output folder as htr.py; reruns skip orders already read with the same method key.
"""
from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import htr  # noqa: E402

MODEL_ID = os.environ.get("VLM_MODEL", "Qwen/Qwen2.5-VL-3B-Instruct")
DPI = 200
MAX_PIXELS = 2048 * 28 * 28   # about 1.6 MP per page after the processor's resize
METHOD_KEY = f"vlm:{MODEL_ID}:dpi{DPI}:px{MAX_PIXELS}:v2"
PROMPT = ("Transcribe all the writing on this page of a historical United States government document exactly as written, "
          "line by line, top to bottom, including headings, dates, signatures and marginal notes. Keep the original spelling, "
          "capitalization, abbreviations and punctuation; do not correct, modernize, expand or summarize anything, and do not "
          "add words that are not on the page. Write [illegible] for any word you cannot read. Output only the transcription.")
VLM_FIELDS = ["instrument_id", "sha256", "pages", "method_key", "vlm_text_path", "vlm_chars", "vlm_illegible_marks",
              "vlm_retried_pages", "vlm_degenerate_pages", "seconds", "error"]


def degenerate(text):
    """A small VLM sometimes loops: the same line, or the same word, over and over."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) >= 6 and max(lines.count(x) for x in set(lines)) / len(lines) > 0.5:
        return True
    toks, run = text.split(), 1
    for a, b in zip(toks, toks[1:]):
        run = run + 1 if a == b else 1
        if run >= 15:
            return True
    return False


def collapse(text):
    """Collapse runs of a repeated line or word to one copy plus a count, so a loop is visible and not mistaken for text."""
    out, prev, n = [], None, 0
    for ln in text.splitlines() + [None]:
        if ln is not None and prev is not None and ln.strip() == prev.strip():
            n += 1
            continue
        if prev is not None:
            out.append(prev if n == 1 else f"{prev} [repeated {n} times by the model]")
        prev, n = ln, 1
    text = "\n".join(out)
    return re.sub(r"(\S+)(?:\s+\1){4,}", lambda m: f"{m.group(1)} [repeated {len(m.group(0).split())} times by the model]", text)


class VLM:
    def __init__(self, model_id=MODEL_ID):
        import torch
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
        self.torch = torch
        self.model_id = model_id
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(model_id, torch_dtype=torch.bfloat16, device_map="cuda").eval()
        self.processor = AutoProcessor.from_pretrained(model_id, max_pixels=MAX_PIXELS)

    def read_page(self, image, retry=False):
        messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": PROMPT}]}]
        prompt = self.processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self.processor(text=[prompt], images=[image], return_tensors="pt").to(self.model.device)
        with self.torch.inference_mode():
            extra = {"repetition_penalty": 1.3, "no_repeat_ngram_size": 12} if retry else {"repetition_penalty": 1.05}
            out = self.model.generate(**inputs, max_new_tokens=2048, do_sample=False, **extra)
        return self.processor.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0].strip()

    def describe(self):
        info = {"model_id": self.model_id, "torch": self.torch.__version__, "prompt": PROMPT, "max_pixels": MAX_PIXELS, "dpi": DPI}
        try:
            import transformers
            from huggingface_hub import snapshot_download
            info["transformers"] = transformers.__version__
            info["model_revision"] = os.path.basename(snapshot_download(self.model_id, local_files_only=True))
        except Exception:
            pass
        return info


def render(pdf, work):
    r = subprocess.run(["pdftoppm", "-r", str(DPI), "-gray", "-l", str(htr.MAX_PAGES), "-png", pdf, os.path.join(work, "p")],
                       capture_output=True, text=True, timeout=600)
    if r.returncode:
        raise RuntimeError("pdftoppm: " + (r.stderr or "")[-200:])
    return [os.path.join(work, f) for f in sorted(os.listdir(work)) if f.endswith(".png")]


def load_done(out_dir):
    path = os.path.join(out_dir, "VLM.csv")
    if not os.path.exists(path):
        return {}
    with open(path, newline="", encoding="utf-8") as fh:
        return {(r["sha256"], r["method_key"]): r for r in csv.DictReader(fh) if not r.get("error")}


def run(root, out_dir, reader=None, pages_of=None, limit=None):
    from PIL import Image
    os.makedirs(os.path.join(out_dir, "texts"), exist_ok=True)
    targets = htr.load_targets(root)
    if limit:
        targets = targets[:limit]
    done = load_done(out_dir)
    rows, todo = [], []
    for t in targets:
        if (t["sha256"], METHOD_KEY) in done:
            rows.append(done[(t["sha256"], METHOD_KEY)])
        else:
            todo.append(t)
    print(f"VLM: {len(targets)} orders, {len(rows)} already read, {len(todo)} to read", flush=True)
    if todo and reader is None:
        reader = VLM()
    pages_of = pages_of or render
    for n, t in enumerate(todo, 1):
        started = time.time()
        stem = "texts/" + t["instrument_id"].replace(":", "_") + ".vlm.txt"
        row = {"instrument_id": t["instrument_id"], "sha256": t["sha256"], "pages": t.get("pages", ""), "method_key": METHOD_KEY,
               "vlm_text_path": "", "vlm_chars": 0, "vlm_illegible_marks": 0, "vlm_retried_pages": 0, "vlm_degenerate_pages": 0, "error": ""}
        work = tempfile.mkdtemp(prefix="pinakes-vlm-")
        try:
            texts, retried, bad = [], 0, 0
            for png in pages_of(os.path.join(root, t["folder"], t["file"]), work):
                with Image.open(png) as im:
                    page = reader.read_page(im.convert("RGB"))
                    if degenerate(page):
                        retried += 1
                        page = reader.read_page(im.convert("RGB"), retry=True)
                        if degenerate(page):
                            bad += 1
                            page = collapse(page)
                texts.append(page)
            row.update({"vlm_retried_pages": retried, "vlm_degenerate_pages": bad})
            text = "\n\f\n".join(texts).strip()
            if text:
                with open(os.path.join(out_dir, stem), "w", encoding="utf-8") as fh:
                    fh.write(text)
                row.update({"vlm_text_path": stem, "vlm_chars": len(text), "vlm_illegible_marks": text.count("[illegible]")})
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"[:200]
        finally:
            shutil.rmtree(work, ignore_errors=True)
        row["seconds"] = round(time.time() - started, 1)
        rows.append(row)
        if n % 10 == 0 or n == len(todo):
            print(f"VLM {n}/{len(todo)}", flush=True)
            htr.write_csv(os.path.join(out_dir, "VLM.csv"), VLM_FIELDS, sorted(rows, key=lambda r: r["instrument_id"]))
    rows.sort(key=lambda r: r["instrument_id"])
    htr.write_csv(os.path.join(out_dir, "VLM.csv"), VLM_FIELDS, rows)
    return {"orders": len(rows), "read_this_run": len(todo), "errors": sum(bool(r.get("error")) for r in rows),
            "degenerate_orders": sum(int(r.get("vlm_degenerate_pages") or 0) > 0 for r in rows),
            "model": MODEL_ID, "describe": reader.describe() if reader is not None and hasattr(reader, "describe") else {}}


def main():
    root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
    out_dir = os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output")
    limit = int(os.environ["HTR_LIMIT"]) if os.environ.get("HTR_LIMIT") else None
    s = run(root, out_dir, limit=limit)
    import json
    with open(os.path.join(out_dir, "VLM_PROVENANCE.json"), "w", encoding="utf-8") as fh:
        json.dump({**s, **htr.STATUS}, fh, indent=2)
    print({k: s[k] for k in ("orders", "read_this_run", "errors")})


if __name__ == "__main__":
    main()
