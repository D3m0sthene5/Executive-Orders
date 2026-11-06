"""H6 apply queue (coordinator tool; no judgment): when a kit packet's last production worker is done, fill the
dispatch-blocked member's row as blocked, then run kit apply and batch-check, one packet at a time."""
import csv, json, subprocess, time
from pathlib import Path
T = Path(__file__).resolve().parent; R = T.parents[3]; E = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H6")
LAST = {"D1": "H6-w34", "D2": "H6-w36", "U4": "H6-w23"}
BL = {"D1": "EO:1834", "D2": "EO:13661", "U4": "EO:13821"}
RS = {"EO:1834": "Dispatch-check source custody block: the only original (Thirtieth Annual Report of the U.S. Civil Service Commission, 1913, SERIALSET-06727 PDF page 131) is not held; retain its bytes before production.",
      "EO:13661": "Dispatch-check source custody block: 79 FR 15535 (govinfo 2014-06141.pdf) is custody_record_only; retain the PDF bytes before production.",
      "EO:13821": "Dispatch-check source custody block: 83 FR 1507 (govinfo 2018-00553.pdf) is custody_record_only; retain the PDF bytes before production."}
log = lambda m: open(T.parent / "COORDINATOR_LOG.txt", "a").write(m + "\n")
def done(n):
    f = E / "run" / f"{n}.json"
    if (E / "run" / f"{n}.running").exists() or not f.exists(): return False
    try: return bool(json.loads(f.read_text()).get("session_id"))
    except Exception: return False
todo = [b for b in LAST if not (R / f"research/herschel/H6/packets/{b}/applied-v1").exists()]
while todo:
    for b in list(todo):
        if not done(LAST[b]): continue
        P = R / f"research/herschel/H6/packets/{b}"
        rows = list(csv.DictReader(open(P / "decisions.csv", newline="", encoding="utf-8"))); hdr = list(rows[0].keys())
        for r in rows:
            if r["instrument_id"] == BL[b]: r.update(outcome="blocked", approved="false", agent="claude", research_rationale=RS[BL[b]])
        with open(P / "decisions.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=hdr); w.writeheader(); w.writerows(rows)
        t0 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        a = subprocess.run(["python3", "jobs/claim-kit/kit.py", "apply", str(P), "--write", str(P / "applied-v1")], cwd=R, capture_output=True, text=True)
        (E / f"apply-{b}.log").write_text(a.stdout + a.stderr)
        c = subprocess.run(["python3", "jobs/claim-kit/kit.py", "batch-check", str(P), str(P / "applied-v1")], cwd=R, capture_output=True, text=True) if (P / "applied-v1").exists() else None
        if c: (E / f"batchcheck-{b}.log").write_text(c.stdout + c.stderr)
        log(f"APPLY {b} {t0} -> {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} apply_rc={a.returncode} batchcheck_rc={c.returncode if c else None}")
        todo.remove(b)
    time.sleep(30)
