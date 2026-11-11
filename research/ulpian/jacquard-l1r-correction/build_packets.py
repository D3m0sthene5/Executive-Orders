"""Build the blind reading packets for the Jacquard L1R correction (D-20261110-ulpian-l1r-correction).

Members: the wave-2 L1R provisional NO statuses with no exact date or dated on or after 1904-05-03 (553), plus the
three undated wave-1 L1 rows (EO 940, 1596, 1604): 556 orders. They are shuffled with a fixed seed and split into
six batches of at most 93 orders; three planted controls are added to each batch (at most 96 items). Controls are
undecided one-person waivers from Ulpian tier 2 whose held text contains no year before 1905 (so the base text
cannot already settle the question), each with one appended sentence of a known kind.

    python -I research/ulpian/jacquard-l1r-correction/build_packets.py --key-out <path outside the worktree>

Writes PACKET_B1.jsonl .. PACKET_B6.jsonl here and the control key to --key-out (copied here after both arms of
every batch have finished).
"""
import argparse
import csv
import hashlib
import json
import random
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(REPO / "jobs" / "ulpian-outer-bound"))
sys.path.insert(0, str(REPO / "jobs" / "_lib"))
import ulpian as U  # noqa: E402
import eo_identity as E  # noqa: E402

SEED = "ulpian-jacquard-l1r-correction-2026-11-10"
BATCH = 93
W1 = "research/excavator/jacquard-2026-10-31/"
W2 = "research/excavator/jacquard-2026-10-31-w2/"
WAVE1_UNDATED = ["EO:940", "EO:1596", "EO:1604"]
CONTROL_SENTENCES = {
    "fact_about_another_person": [
        " {pron} late husband entered the service of the Government on March 1, 1889.",
        " {pron} father served in the Navy Department from 1871 to 1899.",
        " {pron} late husband was appointed a letter carrier on May 12, 1890.",
    ],
    "fact_too_late": [
        " {t} {s} has been employed temporarily since July 1, 1907.",
        " {t} {s} entered the service as a laborer on September 3, 1908.",
        " {t} {s} served as a temporary clerk from 1906 to 1911.",
    ],
    "genuine_sufficient_fact": [
        " {t} {s} was appointed a copyist in the War Department on June 15, 1893, and served until 1905.",
        " {t} {s} has been employed in the Government Printing Office since April 2, 1898.",
        " {t} {s} served as a clerk in the Treasury Department from 1896 to 1903.",
    ],
}
EXPECTED = {"fact_about_another_person": "RETURN", "fact_too_late": "RETURN", "genuine_sufficient_fact": "KEEP"}


def text_of(rel):
    return re.sub(r"\s+", " ", (REPO / rel).read_text(encoding="utf-8", errors="replace")).strip()


def sha_file(rel):
    return hashlib.sha256((REPO / rel).read_bytes()).hexdigest()


def members():
    dates = E.load_dates(str(REPO))
    namier = {l["instrument_id"]: l.get("date") for l in U.read_jsonl(U.NAMIER_LINKS)}
    w2 = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / (W2 + "LOTS.csv"), encoding="utf-8", newline=""))}
    w1 = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / (W1 + "LOTS.csv"), encoding="utf-8", newline=""))}
    out = []
    for r in csv.DictReader(open(REPO / (W2 + "PROPOSED_STATUS_ROWS.csv"), encoding="utf-8", newline="")):
        if not r["decision_origin"].startswith("jacquard-L1R"):
            continue
        iid = r["instrument_id"]
        date = namier.get(iid) or (dates.get(iid) or {}).get("date") or ""
        day = U.parse_day(date)
        if day and day < U.date_threshold(0):
            continue
        out.append({"instrument_id": iid, "date": date, "wave": 2, "text_path": w2[iid]["text_path"]})
    for iid in WAVE1_UNDATED:
        out.append({"instrument_id": iid, "date": (dates.get(iid) or {}).get("date") or "", "wave": 1,
                    "text_path": w1[iid]["text_path"]})
    assert len(out) == 556, len(out)
    return out


def control_bases(exclude):
    """Tier-2 one-person waivers, not in L1/L1R, whose text has no year before 1905 and a titled surname."""
    members_ = {m["instrument_id"]: m for m in U.read_jsonl(U.POTHIER_MEMBERS)}
    bases = []
    for r in csv.DictReader(open(REPO / "research/ulpian/CLASS.csv", encoding="utf-8", newline="")):
        iid = r["instrument_id"]
        if r["tier"] != "required_age_reading" or iid in exclude:
            continue
        text = text_of(r["text_path"])
        if any(int(y) < 1905 for y in re.findall(r"(?<!\d)(1[89]\d\d)(?!\d)", text)):
            continue
        persons = U.as_list(members_.get(iid, {}).get("named_persons"))
        name = (persons[0].get("name") if persons and isinstance(persons[0], dict) else "") or ""
        surname = (re.findall(r"[A-Za-z][A-Za-z'’-]+", name) or [""])[-1]
        m = re.search(r"\b(Mr|Mrs|Miss)\.?\s+(?:[A-Z][\w.]*\s+){0,3}" + re.escape(surname) + r"\b", text) if surname else None
        if not m:
            continue
        bases.append({"instrument_id": iid, "date": r["date"], "text_path": r["text_path"], "title": m.group(1),
                      "surname": surname, "text": text})
    return bases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key-out", required=True)
    args = ap.parse_args()
    rng = random.Random(SEED)
    rows = members()
    exclude = {r["instrument_id"] for r in rows} | {"EO:1854", "EO:2077", "EO:2102"}   # wave-1 correction controls
    bases = control_bases(exclude)
    rng.shuffle(rows)
    rng.shuffle(bases)
    mrs = [b for b in bases if b["title"] in ("Mrs", "Miss")]
    batches = [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]
    used, key = set(), {"seed": SEED, "batches": {}}
    for n, batch in enumerate(batches, 1):
        items = []
        for r in batch:
            items.append({"instrument_id": r["instrument_id"], "date": r["date"], "wave": r["wave"],
                          "text_path": r["text_path"], "text_sha256": sha_file(r["text_path"]),
                          "text": text_of(r["text_path"]), "control": None})
        for kind in ("fact_about_another_person", "fact_too_late", "genuine_sufficient_fact"):
            pool = [b for b in (mrs if kind == "fact_about_another_person" else bases) if b["instrument_id"] not in used]
            base = pool[0]
            used.add(base["instrument_id"])
            pron = "Her" if base["title"] in ("Mrs", "Miss") else "His"
            if kind == "fact_about_another_person" and base["title"] == "Miss":
                sentence = CONTROL_SENTENCES[kind][1]          # a father, not a husband, for "Miss"
            else:
                sentence = CONTROL_SENTENCES[kind][(n - 1) % 3]
            sentence = sentence.format(pron=pron, t=base["title"] + ("" if base["title"] == "Miss" else "."),
                                       s=base["surname"])
            items.append({"instrument_id": base["instrument_id"], "date": base["date"], "wave": None,
                          "text_path": base["text_path"], "text_sha256": sha_file(base["text_path"]),
                          "text": base["text"] + sentence,
                          "control": {"kind": kind, "expected": EXPECTED[kind], "appended": sentence}})
        rng.shuffle(items)
        packet, bkey = [], []
        for m, item in enumerate(items, 1):
            pid = f"B{n}-{m:02d}"
            packet.append({"item": pid, "order_date": item["date"] or "(no exact date)", "text": item["text"]})
            bkey.append({k: item[k] for k in ("instrument_id", "date", "wave", "text_path", "text_sha256", "control")}
                        | {"item": pid})
        path = HERE / f"PACKET_B{n}.jsonl"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for p in packet:
                fh.write(json.dumps(p, ensure_ascii=False) + "\n")
        key["batches"][f"B{n}"] = {"packet_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "items": bkey}
        print(f"B{n}: {len(batch)} orders + 3 controls")
    Path(args.key_out).write_text(json.dumps(key, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
