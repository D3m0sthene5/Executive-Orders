"""The page readings for Pinakes HTR: two local vision-language models read each whole page, independently.

A bake-off on three sample pages (2026-10-21; see README) found tesseract and TrOCR get 50-88% of characters wrong on
these hands, while vision-language models get 0.2-6% wrong on clean handwriting. On faded pages every model invents
words where the ink fails (WildHandBench, 2026: 63-91% of model errors on handwriting come from language priors),
but different models invent different words. So two models from different lineages read every page:

  vlm_qwen3    Qwen/Qwen3-VL-8B-Instruct, 4-bit NF4 (about 7.6 GB): best recall on the faded page, fastest, and the
               readiest to write [illegible] instead of guessing; the backbone of the comparison
  vlm_chandra  datalab-to/chandra-ocr-2 (Qwen 3.5 based, OCR-trained, bf16, about 10 GB): the lowest character error
               on clean pages, but it invents signatures and dates; the cross-check

compare.py lines them up word by word: where they agree the reading is likelier right; where they disagree is exactly
where a person should look. Each model loads, reads every order, and is unloaded before the next loads. Where a model
loops, comments on the image, lists words or switches script, its reading is cut there with a visible note and the
page counted in cut_pages (a harsher-penalty retry was tried and produced word salad). Everything runs on the owner's
GPU; every text is a machine hypothesis.

Writes texts/EO_<n>.<reader>.txt and VLM.csv (one row per order and reader) into the same output folder as htr.py;
reruns skip what was already read with the same method key. VLM_READERS=vlm_qwen3 (comma list) runs a subset.
"""
from __future__ import annotations

import csv
import gc
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

DPI = 200
MAX_PIXELS = 2048 * 28 * 28   # about 1.6 MP per page after the processor's resize
MAX_NEW_TOKENS = 1536         # a handwritten page is 150-600 tokens; more than this is a loop
READERS = {
    "vlm_qwen3": {"model_id": "Qwen/Qwen3-VL-8B-Instruct", "quant": "nf4"},
    "vlm_chandra": {"model_id": "datalab-to/chandra-ocr-2", "quant": "bf16"},
}
PROMPT = ("Transcribe all the writing on this page of a historical United States government document exactly as written, "
          "line by line, top to bottom, including headings, dates, signatures and marginal notes. Keep the original spelling, "
          "capitalization, abbreviations and punctuation; do not correct, modernize, expand or summarize anything, and do not "
          "add words that are not on the page. Write [illegible] for any word you cannot read. Output only the transcription.")
VLM_FIELDS = ["instrument_id", "reader", "model_id", "sha256", "pages", "method_key", "text_path", "chars", "illegible_marks",
              "cut_pages", "cut_reasons", "seconds", "error"]


def method_key(reader):
    r = READERS[reader]
    return f"{reader}:{r['model_id']}:{r['quant']}:dpi{DPI}:px{MAX_PIXELS}:tok{MAX_NEW_TOKENS}:v4"


CUT_NOTE = "[model output cut here: it began to {why}]"
META = re.compile(r"\b(provided image|the image|this image|the scan|this scan|incomplete transcri\w*|the transcription)\b"
                  r"|\bI (cannot|can't|am unable)\b|\bas an AI\b", re.I)


def cut_runaway(text):
    """Where the ink fails, a model may loop, drift into commentary about the image, or wander into word lists and
    another script. Keep what it read before that and cut there, with a note: a retry with a harsher repetition penalty
    was tried and made it worse (word salad). Returns (text, why or '')."""
    cuts = []
    lines = text.splitlines()
    pos, seen = 0, {}
    for ln in lines:
        key = ln.strip()
        if len(key) > 3:
            seen.setdefault(key, []).append(pos)
            if len(seen[key]) == 3:
                cuts.append((seen[key][1], "repeat itself"))
        m = META.search(ln)
        if m and pos > 0:
            cuts.append((pos, "comment on the image instead of transcribing"))
        pos += len(ln) + 1
    m = re.search(r"(\S+)(?:\s+\1){4,}", text)
    if m:
        cuts.append((m.start() + len(m.group(1)), "repeat itself"))
    clauses = [(c.start(), c.group(0).strip()) for c in re.finditer(r"[^,;.\n]{12,}", text)]
    counts = {}
    for start, c in clauses:
        counts.setdefault(c, []).append(start)
    for c, starts in counts.items():
        if len(starts) >= 4:
            cuts.append((starts[1], "repeat itself"))
    m = re.search(r"[　-鿿가-힯Ѐ-ӿ]", text)   # CJK, Hangul, Cyrillic: not on these pages
    if m:
        cuts.append((m.start(), "write in another script"))
    # 40 lower-case words in a row with no punctuation and none of the, of, and, to, in: a word list, not prose
    m = re.search(r"(?:\b[a-z]{3,}\b ){40,}", text)
    if m and not re.search(r"\b(the|of|and|to|in)\b", m.group(0)):
        cuts.append((m.start(), "list words instead of transcribing"))
    if not cuts:
        return text, ""
    at, why = min(cuts)
    return text[:at].rstrip() + "\n" + CUT_NOTE.format(why=why), why


def plain(text):
    """Chandra answers in layout HTML; keep the words and line breaks, drop tags and image descriptions."""
    if "<" not in text:
        return text
    text = re.sub(r"<img[^>]*>", "", text)
    text = re.sub(r"<br\s*/?>|</(div|p|li|tr|h\d)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
    return "\n".join(ln.strip() for ln in text.splitlines() if ln.strip())


class VLM:
    def __init__(self, reader):
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
        self.torch, self.reader = torch, reader
        cfg = READERS[reader]
        self.model_id = cfg["model_id"]
        kw = {"device_map": "cuda"}
        if cfg["quant"] == "nf4":
            kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                           bnb_4bit_compute_dtype=torch.bfloat16)
        else:
            kw["dtype"] = torch.bfloat16
        self.model = AutoModelForImageTextToText.from_pretrained(self.model_id, **kw).eval()
        self.processor = AutoProcessor.from_pretrained(self.model_id, max_pixels=MAX_PIXELS)
        tok = self.processor.tokenizer
        self.stops = [i for i in {tok.eos_token_id, tok.convert_tokens_to_ids("<|im_end|>")} if isinstance(i, int) and i >= 0]

    def read_page(self, image):
        msgs = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": PROMPT}]}]
        inputs = self.processor.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True, return_dict=True,
                                                    return_tensors="pt").to(self.model.device)
        with self.torch.inference_mode():
            out = self.model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False, eos_token_id=self.stops,
                                      repetition_penalty=1.05)
        text = self.processor.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0]
        return plain(text.strip())

    def close(self):
        del self.model
        gc.collect()
        self.torch.cuda.empty_cache()

    def describe(self):
        info = {"reader": self.reader, "model_id": self.model_id, "quant": READERS[self.reader]["quant"], "torch": self.torch.__version__,
                "prompt": PROMPT, "max_pixels": MAX_PIXELS, "dpi": DPI, "max_new_tokens": MAX_NEW_TOKENS}
        try:
            import transformers
            from huggingface_hub import snapshot_download
            info["transformers"] = transformers.__version__
            info["model_revision"] = os.path.basename(snapshot_download(self.model_id, local_files_only=True))
            info["gpu"] = self.torch.cuda.get_device_name(0)
        except Exception:
            pass
        return info


def render(pdf, work):
    r = subprocess.run(["pdftoppm", "-r", str(DPI), "-gray", "-l", str(htr.MAX_PAGES), "-png", pdf, os.path.join(work, "p")],
                       capture_output=True, text=True, timeout=600)
    if r.returncode:
        raise RuntimeError("pdftoppm: " + (r.stderr or "")[-200:])
    return [os.path.join(work, f) for f in sorted(os.listdir(work)) if f.endswith(".png")]


def load_rows(out_dir):
    path = os.path.join(out_dir, "VLM.csv")
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r.get("reader") in READERS]


def read_order(t, root, out_dir, reader, key, pages_of):
    from PIL import Image
    started = time.time()
    stem = "texts/" + t["instrument_id"].replace(":", "_") + f".{key}.txt"
    row = {"instrument_id": t["instrument_id"], "reader": key, "model_id": READERS[key]["model_id"], "sha256": t["sha256"],
           "pages": t.get("pages", ""), "method_key": method_key(key), "text_path": "", "chars": 0, "illegible_marks": 0,
           "cut_pages": 0, "cut_reasons": "", "error": ""}
    work = tempfile.mkdtemp(prefix="pinakes-vlm-")
    try:
        texts = []
        for png in pages_of(os.path.join(root, t["folder"], t["file"]), work):
            with Image.open(png) as im:
                page, why = cut_runaway(reader.read_page(im.convert("RGB")))
            if why:
                row["cut_pages"] += 1
                row["cut_reasons"] = "; ".join(sorted(set(filter(None, [row["cut_reasons"], why]))))
            texts.append(page)
        text = "\n\f\n".join(texts).strip()
        if text:
            with open(os.path.join(out_dir, stem), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            row.update({"text_path": stem, "chars": len(text), "illegible_marks": text.count("[illegible]")})
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"[:200]
    finally:
        shutil.rmtree(work, ignore_errors=True)
    row["seconds"] = round(time.time() - started, 1)
    return row


def run(root, out_dir, readers=None, make_reader=None, pages_of=None, limit=None):
    os.makedirs(os.path.join(out_dir, "texts"), exist_ok=True)
    targets = htr.load_targets(root)
    if limit:
        targets = targets[:limit]
    wanted = {t["instrument_id"] for t in targets}
    readers = readers or [r for r in (os.environ.get("VLM_READERS") or ",".join(READERS)).split(",") if r]
    make_reader = make_reader or VLM
    pages_of = pages_of or render
    rows = [r for r in load_rows(out_dir) if r["instrument_id"] in wanted]
    done = {(r["reader"], r["sha256"], r["method_key"]) for r in rows if not r.get("error")}
    rows = [r for r in rows if (r["reader"], r["sha256"], r["method_key"]) in done]
    described, read_now = {}, 0
    for key in readers:
        todo = [t for t in targets if (key, t["sha256"], method_key(key)) not in done]
        print(f"{key}: {len(targets)} orders, {len(targets) - len(todo)} already read, {len(todo)} to read", flush=True)
        if not todo:
            continue
        reader = make_reader(key)
        try:
            for n, t in enumerate(todo, 1):
                rows.append(read_order(t, root, out_dir, reader, key, pages_of))
                read_now += 1
                if n % 10 == 0 or n == len(todo):
                    print(f"{key} {n}/{len(todo)}", flush=True)
                    htr.write_csv(os.path.join(out_dir, "VLM.csv"), VLM_FIELDS, sorted(rows, key=lambda r: (r["instrument_id"], r["reader"])))
            if hasattr(reader, "describe"):
                described[key] = reader.describe()
        finally:
            if hasattr(reader, "close"):
                reader.close()
    rows.sort(key=lambda r: (r["instrument_id"], r["reader"]))
    htr.write_csv(os.path.join(out_dir, "VLM.csv"), VLM_FIELDS, rows)
    by = {k: [r for r in rows if r["reader"] == k] for k in readers}
    return {"orders": len(targets), "read_this_run": read_now, "readers": readers,
            "errors": {k: sum(bool(r.get("error")) for r in v) for k, v in by.items()},
            "cut_orders": {k: sum(int(r.get("cut_pages") or 0) > 0 for r in v) for k, v in by.items()},
            "describe": described}


def main():
    import json
    root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
    out_dir = os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output")
    limit = int(os.environ["HTR_LIMIT"]) if os.environ.get("HTR_LIMIT") else None
    s = run(root, out_dir, limit=limit)
    prov_path = os.path.join(out_dir, "VLM_PROVENANCE.json")
    prov = json.load(open(prov_path, encoding="utf-8")) if os.path.exists(prov_path) else {}
    prov.setdefault("readers", {}).update(s.pop("describe"))
    prov.update({**s, **htr.STATUS})
    with open(prov_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(prov, fh, indent=2)
    print(json.dumps({k: s[k] for k in ("orders", "read_this_run", "errors", "cut_orders")}))


if __name__ == "__main__":
    main()
