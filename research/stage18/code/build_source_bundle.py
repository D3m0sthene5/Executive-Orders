"""Build the Stage 18 source bundle from independently downloaded official bytes.

Usage (from repository root):
  python research/stage18/code/build_source_bundle.py --input-root PATH

PATH must contain fr_issues/, loc_early/, American_State_Papers_Indian_Affairs_1.pdf,
STATUTE-1-Pg95-3.pdf, and Burke_v_Miltenberger_86US519.pdf.
The script never changes the Stage 17 canonical database or any legal labels.
"""

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from pypdf import PdfReader, PdfWriter


FR = [
    ("1947-10-04", ["9896"], [0], [6565]),
    ("1949-02-11", ["10035"], [0], [619]),
    ("1949-10-14", ["10084"], [0], [6245]),
    ("1950-01-27", ["10097", "10098"], [0], [461]),
    ("1950-03-30", ["10118"], [0], [1767]),
    ("1950-07-04", ["10136"], [0, 2], [4239, 4241]),
    ("1950-09-01", ["10158"], [0], [5927]),
    ("1950-10-26", ["10174"], [0], [7165]),
    ("1950-12-08", ["10188"], [0], [8709]),
    ("1951-12-12", ["10310"], [0], [12449]),
    ("1954-02-12", ["10517"], [0], [815]),
    ("1955-03-16", ["10599"], [0], [1569]),
    ("1969-09-11", ["11481"], [12], [14277]),
]

LOC = [
    ("mgw2-028-0210001.jpg", "https://tile.loc.gov/storage-services/master/mss/mgw/mgw2/028/0210001.jpg", "1789-06-08 Washington letterbook copy"),
    ("rbpe21201200-001dr.jpg", "https://tile.loc.gov/storage-services/service/rbc/rbpe/rbpe21/rbpe212/21201200/001dr.jpg", "1789-10-13 contemporary pension broadside: Knox signs by command of the President"),
    ("mgw2-031-3600336.jpg", "https://tile.loc.gov/storage-services/master/mss/mgw/mgw2/031/3600336.jpg", "1790-08-28 Washington borrowing instructions, page 1"),
    ("mgw2-031-3610337.jpg", "https://tile.loc.gov/storage-services/master/mss/mgw/mgw2/031/3610337.jpg", "1790-08-28 Washington borrowing instructions, page 2"),
    ("mgw2-031-3620338.jpg", "https://tile.loc.gov/storage-services/master/mss/mgw/mgw2/031/3620338.jpg", "1790-08-28 Washington borrowing instructions, page 3"),
    ("mgw2-031-3630339.jpg", "https://tile.loc.gov/storage-services/master/mss/mgw/mgw2/031/3630339.jpg", "1790-08-28 Washington borrowing commission, distinct document"),
    ("mal4245100-001.jpg", "https://tile.loc.gov/image-services/iiif/service:mss:mal:424:4245100:001/full/pct:50/0/default.jpg", "1862-11-13 Lincoln order, secretarial copy, page 1"),
    ("mal4245100-002.jpg", "https://tile.loc.gov/image-services/iiif/service:mss:mal:424:4245100:002/full/pct:50/0/default.jpg", "1862-11-13 Lincoln order, secretarial copy, page 2"),
    ("statutes14-p344.jpg", "https://tile.loc.gov/image-services/iiif/service:ll:llsalvol:llsal_014:03760344/full/pct:100/0/default.jpg", "14 Stat. 344, 1866-07-28, chapter 310"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = root / "sources"
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"release": "stage18", "retrieval_date_utc": "2026-10-17", "source_grade_note": "Federal Register excerpts are contemporaneous printed-publication scans, not signed presidential originals. LOC Washington images are letterbook copies; the pension broadside is a contemporary printed copy signed by Knox by command, not a Washington autograph; the Lincoln images are a secretarial copy. The Supreme Court, Statutes at Large, and American State Papers PDFs are official historical reproductions.", "federal_register": [], "library_of_congress": [], "american_state_papers": None, "statute_1789": None, "supreme_court": None}

    for date, orders, indexes, printed_pages in FR:
        original = args.input_root / "fr_issues" / f"FR-{date}.pdf"
        reader = PdfReader(original)
        text = (reader.pages[indexes[0]].extract_text() or "").upper()
        for number in orders:
            if not re.search(r"EXECUTIVE\s+ORDER\s+" + number + r"\b", text):
                raise ValueError(f"EO {number} not on expected source page of {original}")
        writer = PdfWriter()
        for index in indexes:
            writer.add_page(reader.pages[index])
        target = out / f"FR-{date}_EO-{'-'.join(orders)}_pages.pdf"
        with target.open("wb") as stream:
            writer.write(stream)
        manifest["federal_register"].append({
            "executive_orders": orders,
            "issue_date": date,
            "issue_url": f"https://www.govinfo.gov/content/pkg/FR-{date}/pdf/FR-{date}.pdf",
            "issue_sha256": sha256(original),
            "issue_bytes": original.stat().st_size,
            "issue_pdf_page_indexes_zero_based": indexes,
            "printed_register_pages": printed_pages,
            "local_excerpt": target.relative_to(root).as_posix(),
            "local_excerpt_sha256": sha256(target),
            "local_excerpt_bytes": target.stat().st_size,
        })

    for name, url, description in LOC:
        original = args.input_root / "loc_early" / name
        target = out / name
        shutil.copyfile(original, target)
        manifest["library_of_congress"].append({
            "description": description,
            "source_url": url,
            "local_file": target.relative_to(root).as_posix(),
            "sha256": sha256(target),
            "bytes": target.stat().st_size,
        })

    original = args.input_root / "American_State_Papers_Indian_Affairs_1.pdf"
    reader = PdfReader(original)
    indexes = [97, 98]
    selected_text = " ".join(reader.pages[index].extract_text() or "" for index in indexes)
    if "INSTRUCTIONS FROM THE PRESIDENT" not in selected_text.upper() or "ST. CLAIR" not in selected_text.upper():
        raise ValueError("Washington/St. Clair instruction not found on expected American State Papers pages")
    writer = PdfWriter()
    for index in indexes:
        writer.add_page(reader.pages[index])
    target = out / "ASP-Indian-Affairs-I-96-97_1789-10-06-StClair.pdf"
    with target.open("wb") as stream:
        writer.write(stream)
    manifest["american_state_papers"] = {
        "work": "American State Papers, Indian Affairs, volume I",
        "source_url": "https://tile.loc.gov/storage-services/service/ll/llscd/llsp007/llsp007.pdf",
        "source_sha256": sha256(original),
        "source_bytes": original.stat().st_size,
        "source_pdf_page_indexes_zero_based": indexes,
        "printed_pages": [96, 97],
        "local_excerpt": target.relative_to(root).as_posix(),
        "local_excerpt_sha256": sha256(target),
        "local_excerpt_bytes": target.stat().st_size,
    }

    original = args.input_root / "STATUTE-1-Pg95-3.pdf"
    text = " ".join(page.extract_text() or "" for page in PdfReader(original).pages)
    if "INVALID PENSIONERS" not in text.upper() or "SEPTEMBER 29, 1789" not in text.upper():
        raise ValueError("1789 pension statute or date missing from official page")
    target = out / "STATUTE-1-Pg95-3_1789-pension-act.pdf"
    shutil.copyfile(original, target)
    manifest["statute_1789"] = {
        "work": "1 Stat. 95, chapter XXIV, pension act",
        "source_url": "https://www.govinfo.gov/content/pkg/STATUTE-1/pdf/STATUTE-1-Pg95-3.pdf",
        "local_file": target.relative_to(root).as_posix(),
        "sha256": sha256(target),
        "bytes": target.stat().st_size,
        "printed_page": 95,
        "enactment_date": "1789-09-29",
        "source_conflict": "The contemporaneous October 13 pension broadside printed the act's approval date as September 25, 1789; the official Statutes at Large page records September 29. This does not alter the broadside's October 13 date."
    }

    original = args.input_root / "Burke_v_Miltenberger_86US519.pdf"
    target = out / "USREPORTS-86-519_Burke-v-Miltenberger.pdf"
    shutil.copyfile(original, target)
    manifest["supreme_court"] = {
        "case": "Burke v. Miltenberger, 86 U.S. 519",
        "source_url": "https://www.govinfo.gov/content/pkg/USREPORTS-86/pdf/USREPORTS-86-519.pdf",
        "local_file": target.relative_to(root).as_posix(),
        "sha256": sha256(target),
        "bytes": target.stat().st_size,
        "pages": len(PdfReader(target).pages),
    }

    (root / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(manifest['federal_register'])} FR excerpts, {len(LOC)} LOC images, 1 American State Papers excerpt, 1 statute page, and 1 opinion")


if __name__ == "__main__":
    main()
