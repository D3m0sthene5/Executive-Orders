"""Which other jobs' held order texts later-events scans for revocation and amendment sentences.

later_events.py reads the list from LATER_EVENTS_TEXT_JOBS (default: its DEFAULT_TEXT_JOBS). This adds the
acting-instrument texts Selden publishes (jobs/selden-fr-acting: the Federal Register pages of executive orders
that act on other orders) without editing later_events.py, whose hash the claim kit pins. A job whose
output/SOURCES.jsonl is absent is skipped by later_events.py with a log line, so listing it is harmless.
later_events.py reads only SOURCES.jsonl records naming exactly one EO:<n> with a text_path, so statutes and
citing documents in other Selden jobs reach the claim kit through their FRAGMENTS.jsonl instead.
"""
import os

ACTING_TEXT_JOBS = ("selden-fr-acting",)


def text_jobs(default, environ=os.environ):
    """The comma-separated job list: an explicit LATER_EVENTS_TEXT_JOBS wins; otherwise default plus Selden."""
    if environ.get("LATER_EVENTS_TEXT_JOBS", "").strip():
        return environ["LATER_EVENTS_TEXT_JOBS"]
    jobs = [j for j in default.split(",") if j.strip()]
    return ",".join(jobs + [j for j in ACTING_TEXT_JOBS if j not in jobs])
