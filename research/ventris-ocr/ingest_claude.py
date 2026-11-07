"""Record the Claude readings as derived artifacts in READINGS.jsonl.

The transcriptions were produced by claude-sonnet-5-5 (the session model) reading each crop PNG with the Read tool and
writing the text by hand; this script only hashes and stores them. The text file (CLAUDE_TRANSCRIPTS.txt) holds one
block per passage: a line '=== Pxxx' then the transcription.
No sampling parameters exist for this path (the Read tool shows the image to the session model, which answers in chat);
temperature and decoding were not under our control. Seconds are not recorded per crop (done in batches of up to five
crops per turn); the README gives the wall time of the whole Claude pass.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import readings as R

PROMPT = (
    "Transcribe all printed text in this image exactly as it appears, character for character, line by line. "
    "Keep each line break where the image breaks the line. Write fractions such as one-quarter as the single "
    "character ¼ (and ½, ¾); keep the section sign §, degree, minute and second marks, and the printed "
    "spelling, punctuation, capitalization and hyphenation. Do not correct errors, expand abbreviations or complete "
    "cut-off words. If a line is cut off at the top or bottom edge of the image, omit it; if a character cannot be read, "
    "write [illegible]. Write small capitals as capital letters and a row of leader dashes, underscores or dots as '...'. "
    "Where the image has several columns, transcribe the left column completely, then the next. A marginal note "
    "goes on its own line(s) just before the main-text line it sits beside. Output only the transcription."
)
SMOKE = {"P001", "P002", "P003", "P004", "P005"}


def blocks(path):
    cur, buf = None, []
    for line in open(path, encoding="utf-8"):
        m = re.match(r"=== (P\d{3})\s*$", line)
        if m:
            if cur:
                yield cur, "\n".join(buf).strip("\n")
            cur, buf = m.group(1), []
        elif cur:
            buf.append(line.rstrip("\n"))
    if cur:
        yield cur, "\n".join(buf).strip("\n")


def main(path):
    ps = {p["id"]: p for p in R.passages()}
    done = R.done_keys()
    n = 0
    for pid, text in blocks(path):
        if (pid, "claude") in done:
            continue
        rec = R.base(ps[pid], "claude", "claude-sonnet-5-5 (Claude Code session, image read via Read tool)",
                     {"model": "claude-sonnet-5-5", "access": "Read tool image view, transcription written by the model",
                      "sampling": "not controllable", "batch": "up to 5 crops per turn", "smoke_test": pid in SMOKE,
                      "refusal": False, "hedging": False}, prompt=PROMPT)
        rec.update({"output_text": text, "seconds": None, "gpu_mem_peak_mib": 0})
        R.append(rec)
        n += 1
    print("claude readings added:", n)


if __name__ == "__main__":
    main(sys.argv[1])
