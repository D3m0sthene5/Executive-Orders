"""Render first, second (3+ pages) and last page of each replica in one Photius packet, on demand.

The PDFs live only in the partial clone's promisor remote; each is pulled with `git show`, rendered with pdftoppm
at 110 dpi grayscale, and deleted. Renders go to RENDERS/<packet>/EO_<n><suffix>_{first,second,last}.png.

    python3 render_packet.py PACKET_DIR RENDERS_ROOT
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CLONE = "/home/claude/peiresc-pc"


def pages(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    return 0


def main():
    pk = Path(sys.argv[1])
    out = Path(sys.argv[2]) / pk.name
    out.mkdir(parents=True, exist_ok=True)
    errs = []
    for line in open(pk / "ORDERS.jsonl", encoding="utf-8"):
        o = json.loads(line)
        stem = "EO_" + o["expected_number"]
        if (out / f"{stem}_first.png").exists():
            continue
        rel = o["pdf"].replace("\\", "/")
        with tempfile.TemporaryDirectory(dir="/home/claude") as td:
            pdf = os.path.join(td, "x.pdf")
            with open(pdf, "wb") as f:
                r = subprocess.run(["git", "-C", CLONE, "show", f"HEAD:{rel}"], stdout=f, stderr=subprocess.PIPE)
            if r.returncode:
                errs.append(f"{stem}: {r.stderr.decode()[:100]}")
                continue
            n = pages(pdf)
            want = {n: "last", 1: "first"} if n else {}
            if n >= 3:
                want[2] = "second"
            for i, tag in want.items():
                base = os.path.join(td, tag)
                subprocess.run(["pdftoppm", "-r", "110", "-gray", "-png", "-f", str(i), "-l", str(i), "-singlefile",
                                pdf, base], capture_output=True)
                if os.path.exists(base + ".png"):
                    os.replace(base + ".png", out / f"{stem}_{tag}.png")
                else:
                    errs.append(f"{stem}: page {i} not rendered")
    print(pk.name, "renders", len(list(out.glob("*.png"))), "errors", len(errs))
    for e in errs:
        print("  ", e)


if __name__ == "__main__":
    main()
