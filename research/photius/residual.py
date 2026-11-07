"""Photius lanes 7a and 7d: the residual hole and the HeinOnline block list for the owner.

Residual = every numbered order 1-7315 whose tracker original-text step is still open after tonight's merges, less the
orders that Photius lanes credited (a page-checked official printing or a checked replica). For each residual order:
Hein volume, block, page id and URL from the block map captured 2026-11-06. Writes:

  research/photius/RESIDUAL.csv, RESIDUAL.md   (by era and by what it waits on)
  research/photius/HEIN_BLOCKS.csv              (one row per residual order with its block)
  research/photius/HEIN_OWNER.md                (the owner's one page, User Rules first)

    python -I research/photius/residual.py [--tracker jobs/readiness-tracker/output/READINESS_BY_ORDER.csv]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "jobs" / "_lib"))
import eo_identity as ei  # noqa: E402

HERE = Path(__file__).resolve().parent
HANDLE = "https://heinonline.org/HOL/Page?handle=hein.presidents/prsexcuo000{vol}&id={page}&collection=presidents"

# Hein's table of contents, 2026-11-06: (volume, label, first page id, first number, last number). Volume 1 is by
# president before EO 405; those blocks take the numbered range from the WPA/APP dates (EO 1-404 by date).
BLOCKS_RAW = """
1|Polk 1845-1862|1|1|1
1|Lincoln|5|1|25
1|Johnson|11|26|65
1|Grant|41|66|330
1|Arthur|113|331|354
1|Cleveland|119|355|395
1|McKinley|271|396|404
1|T. Roosevelt 1901-02|358|-|-
1|1902-04|456|-|-
1|1904-05|572|-|-
1|1905-06|746|-|-
1|405-432|863|405|432
1|433-503|896|433|503
1|504-599|980|504|599
1|600-707|1083|600|707
2|708-778|1|708|778
2|779-836|151|779|836
2|837-878|299|837|878
2|879-923|452|879|923
2|925-987|600|924|987
2|988-1041|752|988|1041
2|1042-1050|902|1042|1050
2|1051-1116|927|1051|1116
2|1117-1177|1072|1117|1177
2|1178-1247|1201|1178|1247
2|1248-1347|1349|1248|1347
3|1348-1447|1|1348|1447
3|1448-1547|212|1448|1487
3|1488-1554|310|1488|1554
3|1555-1628|448|1555|1628
3|1629-1697|602|1629|1697
3|1698-1743|750|1698|1743
3|1744-1806|857|1744|1806
3|1807-1917|1001|1807|1917
3|1918-1980|1255|1918|1980
3|1981-2043|1401|1981|2043
3|2044-2125|1559|2044|2125
4|2126-2174|1|2126|2174
4|2175-2217|103|2175|2217
4|2218-2260|201|2218|2260
4|2261-2297|303|2261|2297
4|2298-2345|401|2298|2345
4|2346-2384|501|2346|2384
4|2385-2429|601|2385|2429
4|2430-2474|703|2430|2474
4|2475-2519|802|2475|2519
4|2520-2563|902|2520|2563
4|2564-2604|1002|2564|2604
4|2605-2652|1102|2605|2652
4|2653-2694|1204|2653|2694
4|2695-2741|1306|2695|2741
4|2742-2789|1403|2742|2789
4|2790-2826|1505|2790|2826
4|2827-2873|1601|2827|2873
4|2874-2891|1701|2874|2891
5|2892-2933|1|2892|2933
5|2934-2979|101|2934|2979
5|2979-A-3017|201|2979|3017
5|3018-3056|438|3018|3056
5|3057-3100|538|3057|3100
5|3101-3143|642|3101|3143
5|3144-3189|742|3144|3189
5|3190-3238|840|3190|3238
5|3239-3281|944|3239|3281
5|3282-3313-A|1042|3282|3313
5|3314-3359|1146|3314|3359
5|3360-3403|1246|3360|3403
5|3404-3416|1346|3404|3416
5|3417-3440|1393|3417|3440
5|3441-3488|1445|3441|3488
5|3489-3533|1545|3489|3533
5|3534-3579|1647|3534|3579
6|3580-3620|1|3580|3620
6|3621-3663|101|3621|3663
6|3664-3707|200|3664|3707
6|3708-3752|300|3708|3752
6|3753-3794|402|3753|3794
6|3795-3842|500|3795|3842
6|3843-3885-A|600|3843|3885
6|3886-3929|697|3886|3929
6|3930-3966|801|3930|3966
6|3967-4014|901|3967|4014
6|4015-4060|1001|4015|4060
6|4061-4101|1101|4061|4101
6|4102-4143|1201|4102|4143
6|4144-4179-A|1300|4144|4179
6|4180-4220|1402|4180|4220
6|4221-4257|1500|4221|4257
6|4258-4304|1608|4258|4304
7|4305-|1|4305|4305
"""
# Volume 1 president blocks for EO 1-404: Lincoln 1-25 (1862-65), Johnson 26-65, Grant 66-330 (1869-77), Arthur
# 331-354 (1881-85), Cleveland 355-395 (1885-89 and 1893-97), McKinley 396-404 (1897-1901); the T. Roosevelt blocks
# before EO 405 hold the retro-numbered 1901-1906 orders by date, which the numbered blocks from p.863 repeat by
# number. These president ranges are approximate (the series was numbered retroactively by date); the owner should
# confirm EO 1-404 against the volume's own page headers.
HEIN_RULES = """HeinOnline User Rules (help.heinonline.com/kb/heinonline-user-rules), as the owner read them on 2026-11-06:
saving and printing parts of the resource for education, research and private study is permitted; systematic
downloading "to stock or replace print holdings of a whole journal issue or book" is not; text and data mining is not;
distribution beyond authorized users is not; Hein enforces a 200-page limit per download. The owner decides how much
of the title to save with this text in front of him. No script, worker, fetcher or browser automation touches
heinonline.org; nothing saved from Hein is placed in the public repository (bytes stay in research/owner-inbox/hein/,
git-ignored); only hashes, page references and extracted facts go public. A Hein-dependent closure is never described
as public-domain custody; that label belongs to NARA M1118."""


def blocks():
    out = []
    rows = [l.split("|") for l in BLOCKS_RAW.strip().splitlines()]
    for i, (vol, label, page, lo, hi) in enumerate(rows):
        nxt = rows[i + 1] if i + 1 < len(rows) and rows[i + 1][0] == vol else None
        last_page = int(nxt[2]) - 1 if nxt else None
        out.append({"volume": int(vol), "label": label, "first_page": int(page), "last_page": last_page,
                    "lo": int(lo) if lo != "-" else None, "hi": int(hi) if hi != "-" else None,
                    "pages": (last_page - int(page) + 1) if last_page else None})
    return out


def block_for(num, bl):
    hits = [b for b in bl if b["lo"] is not None and b["lo"] <= num <= b["hi"]]
    if not hits:
        return None
    # prefer the numbered blocks over the president blocks when both cover (volume 1 overlap)
    hits.sort(key=lambda b: (0 if re.match(r"^\d", b["label"]) else 1, b["volume"], b["first_page"]))
    return hits[0]


def era_of(date):
    y = int(date[:4]) if date and date[:4].isdigit() else None
    if y is None:
        return "undated"
    if y <= 1906:
        return "1862-1906"
    if y <= 1925:
        return "1907-1925"
    if y <= 1936:
        return "1926-1936"
    return "1937-"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", default=str(REPO / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"))
    ap.add_argument("--label", default="after the Photius merges")
    a = ap.parse_args(argv)
    tracker = {r["instrument_id"]: r for r in csv.DictReader(open(a.tracker, encoding="utf-8"))}
    ident = {r["instrument_id"]: r for r in csv.DictReader(open(HERE / "IDENTITY_DATES.csv", encoding="utf-8"))}
    credited = {}
    for job, grade_ok in (("photius-gpo-volumes", {"official_printing"}), ("photius-csc-printings", {"official_printing"}),
                          ("photius-free-printings", {"official_printing"}), ("photius-replica-check", {"archival_replica_checked"})):
        p = REPO / "jobs" / job / "output" / "FRAGMENTS.jsonl"
        if p.exists():
            for line in open(p, encoding="utf-8"):
                f = json.loads(line)
                if f.get("grade") in grade_ok and f["data"].get("needs_page_check") is False:
                    credited.setdefault(f["instrument_id"], []).append(job)
    pq_replica = set()
    for line in open(REPO / "jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl", encoding="utf-8"):
        pq_replica.add(json.loads(line)["instrument_id"])
    bl = blocks()
    residual, rows = [], []
    for iid, t in tracker.items():
        p = ei.parse_eo_id(iid)
        if not p or not (1 <= p[0] <= 7315):
            continue
        open_step = t["step_original_text"] != "done"
        if not open_step or iid in credited:
            continue
        date = ident.get(iid, {}).get("date", "")
        waits_on = ("replica_check_failed_or_unread" if iid in pq_replica else "microfilm_pending (LC/NARA film: Hein by hand, or M1118)")
        b = block_for(p[0], bl)
        rows.append({"instrument_id": iid, "number": p[0], "suffix": p[1], "date": date, "era": era_of(date),
                     "blockers": t["blockers"], "waits_on": waits_on, "hein_volume": b["volume"] if b else "", "hein_block": b["label"] if b else "",
                     "hein_page_id": b["first_page"] if b else "", "hein_block_pages": b["pages"] if b else "",
                     "hein_url": HANDLE.format(vol=b["volume"], page=b["first_page"]) if b else ""})
    rows.sort(key=lambda r: (r["number"], r["suffix"]))
    with open(HERE / "HEIN_BLOCKS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["instrument_id"])
        w.writeheader()
        w.writerows(rows)
    with open(HERE / "RESIDUAL.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["instrument_id", "number", "suffix", "date", "era", "waits_on", "blockers"])
        w.writeheader()
        w.writerows([{k: r[k] for k in ("instrument_id", "number", "suffix", "date", "era", "waits_on", "blockers")} for r in rows])
    by_era = collections.Counter(r["era"] for r in rows)
    by_wait = collections.Counter((r["era"], r["waits_on"]) for r in rows)
    # block cover: smallest set of blocks covering the residual = every block that holds at least one residual order
    cover = collections.OrderedDict()
    for r in rows:
        if r["hein_block"]:
            k = (r["hein_volume"], r["hein_block"])
            cover.setdefault(k, {"volume": r["hein_volume"], "block": r["hein_block"], "page_id": r["hein_page_id"], "pages": r["hein_block_pages"],
                                 "url": r["hein_url"], "residual": 0})
            cover[k]["residual"] += 1
    blk_index = {(b["volume"], b["label"]): b for b in bl}
    ride_along = 0
    for k, c in cover.items():
        b = blk_index[k]
        c["orders_in_block"] = (b["hi"] - b["lo"] + 1) if b["lo"] is not None and b["hi"] is not None else ""
        if c["orders_in_block"]:
            ride_along += c["orders_in_block"] - c["residual"]
    cover_rows = sorted(cover.values(), key=lambda c: -c["residual"])
    lines = [f"# Residual hole, numbered orders 1-7315, {a.label}", "",
             f"Orders 1-7315 whose original-text step is open and that no Photius lane credited: **{len(rows)}**.", "",
             "| Era | Residual | of which replica check failed or unread | of which film-only (microfilm_pending) |", "|---|---:|---:|---:|"]
    for era in ("1862-1906", "1907-1925", "1926-1936", "1937-", "undated"):
        if by_era.get(era):
            lines.append(f"| {era} | {by_era[era]} | {by_wait.get((era, 'replica_check_failed_or_unread'), 0)} | {by_wait.get((era, 'microfilm_pending (LC/NARA film: Hein by hand, or M1118)'), 0)} |")
    lines += ["", f"Hein blocks that cover the residual: {len(cover_rows)}; residual orders they cover: {sum(c['residual'] for c in cover_rows)}; "
              f"non-residual orders riding along: {ride_along}.", "", "Blocks in order of residual orders covered:", "",
              "| Vol | Block | Page id | Block pages | Residual | Orders in block | URL |", "|---|---|---:|---:|---:|---:|---|"]
    for c in cover_rows:
        lines.append(f"| {c['volume']} | {c['block']} | {c['page_id']} | {c['pages'] or ''} | {c['residual']} | {c['orders_in_block']} | {c['url']} |")
    (HERE / "RESIDUAL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    owner = ["# HeinOnline: the owner's list (Photius lane 7a)", "", HEIN_RULES, "",
             f"Residual numbered orders 1-7315 with no official witness and no checked replica, {a.label}: **{len(rows)}** "
             f"(file: `research/photius/HEIN_BLOCKS.csv`, one row per order with volume, block, page id and URL).", "",
             f"Smallest block set covering them: **{len(cover_rows)} blocks**, covering **{sum(c['residual'] for c in cover_rows)}** residual orders, "
             f"with **{ride_along}** non-residual orders riding along. A block longer than 200 pages (vol. 5 \"2979-A-3017\" is 237) exceeds Hein's "
             "download limit and must be saved as two page ranges.", "",
             "Two ways to proceed, both by hand in your own browser, one block at a time:", "",
             "1. Save the block's PDF (click the block's PDF icon) into `research/owner-inbox/hein/<volume>-<block>.pdf`. The session hashes it, "
             "splits it, reads the text layer, aligns the tags and registers each order as `microfilm_witness` with bytes held privately (R38).",
             "2. Or view pages and record facts in `research/owner-inbox/hein-checks.csv` with columns number, date, signatory, first_words, "
             "last_words, page_id. R38 treats those as page-check facts, never as held bytes.", "",
             "Blocks, most residual orders first:", "",
             "| Vol | Block | Page id | Pages | Residual orders | Orders in block | URL |", "|---|---|---:|---:|---:|---:|---|"]
    for c in cover_rows:
        owner.append(f"| {c['volume']} | {c['block']} | {c['page_id']} | {c['pages'] or ''} | {c['residual']} | {c['orders_in_block']} | {c['url']} |")
    owner += ["", "Volume 1 before EO 405 is arranged by president and date, not by number; its president blocks above are approximate "
              "and the orders in them are retro-numbered. Confirm EO 1-404 against the volume's own page headers before saving.",
              "", "Volume 7 begins at EO 4305; the GPO HathiTrust volumes cover from 4306, so only EO 4305 itself may need volume 7."]
    (HERE / "HEIN_OWNER.md").write_text("\n".join(owner) + "\n", encoding="utf-8")
    print(json.dumps({"residual": len(rows), "by_era": dict(by_era), "blocks": len(cover_rows), "ride_along": ride_along}, indent=1))


if __name__ == "__main__":
    main()
