"""Download the source PDFs named in plan.json, check each against its pinned SHA-256, and render
the cited PDF pages plus neighbours to JPEG (height 1800 px, quality 75, like research/montfaucon/images).

Writes OUTPUT_DIR/images/<source-id>/page-NNN.jpg and OUTPUT_DIR/MANIFEST.json. Makes no judgement about
page content. A source whose bytes do not match its pinned SHA-256 is NOT rendered; the actual hash is
recorded so the coordinator can decide.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

JOB_DIR = Path(os.environ.get("JOB_DIR", Path(__file__).parent))
OUT = Path(os.environ.get("OUTPUT_DIR", "output"))
REPO = Path(os.environ.get("REPO_ROOT", "."))
HEIGHT = 1800
QUALITY = 75
UA = "EO-Road-System/1.0 (+https://github.com/D3m0sthene5/Executive-Orders; research)"
sys.path.insert(0, str(REPO / "jobs" / "_lib"))
try:
    import runner_limits
except Exception:  # job still works without the shared helper
    runner_limits = None


def past_deadline():
    return bool(runner_limits and runner_limits.past_safe_stop())


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(src, dest, local_map):
    """Return (ok, error). Test hook: JOB_LOCAL_SOURCES is a JSON file {url_or_sha: local_path}."""
    if src.get("kind") == "lfs":
        rel = src["lfs_path"]
        subprocess.run(["git", "lfs", "pull", "--include", rel], cwd=REPO, check=False, capture_output=True)
        p = REPO / rel
        if not p.exists():
            return False, "lfs file missing"
        shutil.copyfile(p, dest)
        return True, ""
    local = local_map.get(src["url"]) or local_map.get(src["sha256"])
    if local:
        shutil.copyfile(local, dest)
        return True, ""
    err = ""
    for attempt in range(4):
        try:
            req = urllib.request.Request(src["url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
            return True, ""
        except Exception as e:  # network errors are recorded, never fatal
            err = f"{type(e).__name__}: {e}"
            time.sleep(5 * (attempt + 1))
    return False, err


def work(src, out_dir, local_map):
    import pypdfium2 as pdfium
    t0 = time.time()
    res = {"source_id": src["source_id"], "url": src["url"], "expected_sha256": src["sha256"],
           "orders": src["orders"], "images": [], "status": "", "error": ""}
    tmp = Path(tempfile.mkdtemp(prefix="m011-"))
    try:
        pdf = tmp / "src.pdf"
        ok, err = fetch(src, pdf, local_map)
        if not ok:
            res.update(status="download_failed", error=err)
            return res
        res["bytes"] = pdf.stat().st_size
        res["actual_sha256"] = sha_file(pdf)
        res["download_seconds"] = round(time.time() - t0, 1)
        if res["actual_sha256"] != src["sha256"]:
            res.update(status="sha_mismatch")
            return res
        doc = pdfium.PdfDocument(str(pdf))
        n = len(doc)
        res["pdf_pages"] = n
        dest = out_dir / "images" / src["source_id"]
        dest.mkdir(parents=True, exist_ok=True)
        t1 = time.time()
        for pno in sorted(set(src["pages"])):
            if pno < 1 or pno > n:
                res["images"].append({"pdf_page": pno, "error": "page outside PDF"})
                continue
            page = doc[pno - 1]
            w, h = page.get_size()
            scale = HEIGHT / h
            img = page.render(scale=scale).to_pil().convert("RGB")
            f = dest / f"page-{pno:03d}.jpg"
            dpi = round(72 * scale)
            img.save(f, "JPEG", quality=QUALITY, dpi=(dpi, dpi))
            res["images"].append({"pdf_page": pno, "path": f"images/{src['source_id']}/{f.name}",
                                  "sha256": sha_file(f), "bytes": f.stat().st_size,
                                  "width": img.size[0], "height": img.size[1],
                                  "image_url": f"{src['url']}#page={pno}"})
        res["render_seconds"] = round(time.time() - t1, 1)
        res["status"] = "ok"
        return res
    except Exception as e:
        res.update(status="error", error=f"{type(e).__name__}: {e}")
        return res
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    plan = json.loads((JOB_DIR / "plan.json").read_text())
    local_map = {}
    if os.environ.get("JOB_LOCAL_SOURCES"):
        local_map = json.loads(Path(os.environ["JOB_LOCAL_SOURCES"]).read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    workers = int(os.environ.get("JOB_WORKERS", "4"))
    sources = sorted(plan["sources"], key=lambda s: -(s.get("bytes") or 0))  # largest first balances workers
    results, t0 = [], time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {}
        for s in sources:
            if past_deadline():
                results.append({"source_id": s["source_id"], "status": "not_started_deadline", "orders": s["orders"]})
                continue
            futs[ex.submit(work, s, OUT, local_map)] = s
        for fu in as_completed(futs):
            r = fu.result()
            results.append(r)
            print(f"[{len(results)}/{len(sources)}] {r['source_id']} {r['status']} "
                  f"{r.get('bytes', '')} dl={r.get('download_seconds', '')}s render={r.get('render_seconds', '')}s "
                  f"{r.get('error', '')}", flush=True)
    results.sort(key=lambda r: r["source_id"])
    import PIL
    import pypdfium2
    manifest = {"schema": "montfaucon-m011-pages/v1", "batch": "m011", "height_px": HEIGHT, "jpeg_quality": QUALITY,
                "renderer": f"pypdfium2 {pypdfium2.version.PYPDFIUM_INFO}; Pillow {PIL.__version__}",
                "plan_sha256": hashlib.sha256((JOB_DIR / "plan.json").read_bytes()).hexdigest(),
                "elapsed_seconds": round(time.time() - t0, 1),
                "counts": {"sources": len(results), "ok": sum(r["status"] == "ok" for r in results),
                           "images": sum(len(r.get("images", [])) for r in results)},
                "sources": results}
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, sort_keys=True))
    bad = [r["source_id"] for r in results if r["status"] != "ok"]
    print("not ok:", bad)
    # Negative per-source statuses are recorded results, not job failures.


if __name__ == "__main__":
    main()
