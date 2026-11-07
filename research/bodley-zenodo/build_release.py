#!/usr/bin/env python3
"""Bodley release builder: assemble the Zenodo release folder from one git commit, offline.

Named for Thomas Bodley, who arranged for a copy of every registered book to reach his library.

What it does (no network, standard library only):
  * resolves a commit of the Executive-Orders repository (default origin/main) and reads every input with
    `git show <commit>:<path>`, never from the working tree, so the sparse checkout does not matter;
  * reads CONTENTS.csv (one row per release file) and, for each row, measures the inputs with `git ls-tree -l`;
  * refuses any input that matches the exclusion list (PDFs, page images, archives, licensed or sealed material);
  * --dry-run (the default): lists and measures only, writes nothing, prints the estimated release size and
    checks the Zenodo limits (100 files, 50 GB per record, as documented at help.zenodo.org);
  * --build: writes the release folder (copies, derived tables, zips), then SHA256SUMS and MANIFEST.json.

The derived tables never contain verbatim source text. Every quotation in a filed claim is replaced by its
SHA-256 and length; the span (char_start/char_end), the source hash and the source URL stay, so a reader who
holds the source bytes (the Pergamon byte store, or a fresh download that hashes the same) re-verifies the span.

Usage:
  py -I build_release.py --repo C:/Users/danie/eo-wt/enc-zenodo --commit origin/main            # dry run
  py -I build_release.py --repo ... --commit <sha> --build --out C:/some/empty/dir               # real build

Exit status: 0 on success; 2 if an exclusion rule or a Zenodo limit is violated; 3 if a required input is missing.
"""
import argparse
import csv
import datetime
import fnmatch
import gzip
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENTS = os.path.join(HERE, "CONTENTS.csv")

ZENODO_MAX_FILES = 100            # help.zenodo.org/docs/deposit/manage-files/
ZENODO_MAX_BYTES = 50_000_000_000  # default 50 GB per record (manage-quota)

# An input path matching any of these is refused. The release carries hashes and URLs, never these bytes.
EXCLUDE = [
    r"\.pdf$", r"\.(png|jpe?g|tiff?|gif)$", r"\.(zip|tar|gz|tgz|7z|zst)$", r"\.part\d+$", r"\.sqlite3?$",
    r"^ProQuest Pre-1937", r"proquest[^/]*/output/(texts|pdfs?)/", r"(^|/)texts/", r"(^|/)blobs/", r"(^|/)raw/",
    r"(^|/)cache/",
    r"sealed", r"answer[_-]?key", r"BLIND.*ANSWER", r"HeinOnline", r"Westlaw", r"Lexis",
]
EXCLUDE_RE = [re.compile(p, re.I) for p in EXCLUDE]

# Text-bearing keys inside a filed claim; each is replaced by <key>_sha256 and <key>_len in the release.
TEXT_KEYS = {"quote", "excerpt", "quote_continuation", "original_operative_text", "before_text", "after_text",
             "source_context", "quoted_parts"}

# The SOURCES.jsonl files merged into source_manifest.csv.gz are the source_paths of its CONTENTS.csv row
# (metadata only: URL, sha256, bytes, retrieval time).


# ---------------------------------------------------------------- git helpers
class Repo:
    def __init__(self, path, commit):
        self.path = path
        self.commit = self._git("rev-parse", "--verify", commit + "^{commit}").decode().strip()

    def _git(self, *args, check=True):
        p = subprocess.run(["git", "-C", self.path, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if check and p.returncode != 0:
            raise FileNotFoundError(p.stderr.decode(errors="replace").strip())
        return p.stdout

    def show(self, path):
        return self._git("show", f"{self.commit}:{path}")

    def lines(self, path):
        return self.show(path).decode("utf-8").splitlines()

    def ls(self, path):
        """[(size, path)] for a file or every file under a directory at the commit."""
        out = self._git("ls-tree", "-r", "-l", self.commit, "--", path, check=False).decode("utf-8", "replace")
        rows = []
        for line in out.splitlines():
            meta, _, name = line.partition("\t")
            parts = meta.split()
            if len(parts) == 4 and parts[1] == "blob":
                rows.append((int(parts[3]), name))
        return rows


def sizes(repo, source_paths):
    total, files = 0, []
    for sp in source_paths:
        rows = repo.ls(sp)
        files.extend(rows)
        total += sum(s for s, _ in rows)
    return total, files


def refuse_excluded(rows):
    """rows: [(size, path)]. Return the paths that match an exclusion rule."""
    return [p for _, p in rows if any(rx.search(p) for rx in EXCLUDE_RE)]


# ---------------------------------------------------------------- CONTENTS.csv
def read_contents():
    with open(CONTENTS, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def split_paths(cell):
    return [x.strip() for x in cell.split(";") if x.strip()]


# ---------------------------------------------------------------- dry run
def dry_run(repo):
    rows = read_contents()
    problems, missing = [], []
    total_src = total_est = 0
    print(f"commit {repo.commit}")
    print(f"{'release_path':46} {'kind':20} {'inputs':>6} {'input MiB':>10} {'est. release MiB':>17}")
    for r in rows:
        kind = r["kind"]
        sps = split_paths(r["source_paths"])
        est = int(r["approx_bytes_release"] or 0)
        if kind == "local":
            nb = os.path.getsize(os.path.join(HERE, sps[0]))
            print(f"{r['release_path']:46} {kind:20} {1:6d} {nb / 2**20:10.2f} {est / 2**20:17.2f}")
            total_src += nb
            total_est += est
            continue
        if kind in ("pending", "generated") or not sps:
            print(f"{r['release_path']:46} {kind:20} {'-':>6} {'-':>10} {est / 2**20:17.2f}")
            total_est += est
            if kind == "pending":
                missing.append(r["release_path"])
            continue
        nbytes, files = sizes(repo, sps)
        bad = refuse_excluded(files)
        if bad:
            problems.append((r["release_path"], bad[:5]))
        if not files:
            missing.append(r["release_path"] + " (inputs not found at this commit)")
        print(f"{r['release_path']:46} {kind:20} {len(files):6d} {nbytes / 2**20:10.2f} {est / 2**20:17.2f}")
        total_src += nbytes
        total_est += est
    n_files = sum(1 for r in rows if r["release_path"] not in ("SHA256SUMS", "MANIFEST.json")) + 2
    print("-" * 100)
    print(f"files in release (with SHA256SUMS and MANIFEST.json): {n_files}  (Zenodo limit {ZENODO_MAX_FILES})")
    print(f"input bytes read: {total_src / 2**20:.1f} MiB;  estimated release: {total_est / 2**20:.1f} MiB "
          f"(Zenodo default quota {ZENODO_MAX_BYTES / 1e9:.0f} GB per record)")
    if missing:
        print("not yet buildable:", *missing, sep="\n  ")
    rc = 0
    if problems:
        print("EXCLUSION RULE VIOLATIONS:")
        for rp, bad in problems:
            print(" ", rp, "<-", bad)
        rc = 2
    if n_files > ZENODO_MAX_FILES or total_est > ZENODO_MAX_BYTES:
        print("ZENODO LIMIT EXCEEDED")
        rc = 2
    return rc


# ---------------------------------------------------------------- derived tables
def load_claim_gate(repo):
    """The project's own claim fingerprint, taken from the same commit."""
    src = repo.show("research/stage19/code/claim_gate.py")
    d = tempfile.mkdtemp(prefix="bodley_gate_")
    p = os.path.join(d, "claim_gate.py")
    with open(p, "wb") as fh:
        fh.write(src)
    spec = importlib.util.spec_from_file_location("claim_gate", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def strip_text(o):
    if isinstance(o, dict):
        d = {}
        for k, v in o.items():
            if k in TEXT_KEYS and isinstance(v, (str, list, dict)):
                blob = json.dumps(v, ensure_ascii=False, sort_keys=True) if not isinstance(v, str) else v
                d[k + "_sha256"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
                d[k + "_len"] = len(blob)
            else:
                d[k] = strip_text(v)
        return d
    if isinstance(o, list):
        return [strip_text(x) for x in o]
    return o


def walk_refs(o, path, out):
    if isinstance(o, dict):
        if "sha256" in o and ("url" in o or "evidence_id" in o or "char_start" in o):
            out.append((path, o))
        for k, v in o.items():
            walk_refs(v, f"{path}.{k}" if path else k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk_refs(v, f"{path}[{i}]", out)


def gz_bytes(data):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0, compresslevel=9) as g:  # mtime=0: reproducible
        g.write(data)
    return buf.getvalue()


def derive_claims(repo, readiness):
    """Latest filed claim per order (later file name, then later line, wins: research/readiness/README.md)."""
    gate = load_claim_gate(repo)
    names = sorted(p for _, p in repo.ls("research/readiness/claims") if p.endswith(".jsonl"))
    latest, superseded = {}, 0
    for name in names:
        for ln, line in enumerate(repo.show(name).decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            claim = json.loads(line)
            iid = claim["instrument_id"]
            if iid in latest:
                superseded += 1
            latest[iid] = (os.path.basename(name), ln, claim)
    claims_out, index_rows, ref_rows = io.StringIO(), [], []
    for iid in sorted(latest):
        fname, ln, claim = latest[iid]
        sha = gate.claim_sha(claim)  # fingerprint of the UNSTRIPPED claim, as the project computes it
        refs = []
        walk_refs(claim, "", refs)
        stripped = strip_text(claim)
        claims_out.write(json.dumps({"instrument_id": iid, "claim_sha256": sha, "claim_file": fname,
                                     "claim_line": ln, "claim": stripped}, ensure_ascii=False, sort_keys=True) + "\n")
        end = claim.get("whole_order_end") or {}
        rd = readiness.get(iid, {})
        index_rows.append({
            "instrument_id": iid, "claim_schema": claim.get("schema"), "claim_sha256": sha,
            "claim_file": fname, "claim_line": ln, "claim_status": claim.get("whole_order_status"),
            "ledger_status": rd.get("provisional_status", ""), "status_contested": rd.get("status_contested", ""),
            "whole_end_date": end.get("date", ""), "whole_end_date_kind": end.get("date_kind", ""),
            "whole_end_first_cause": end.get("first_cause", ""), "whole_end_mechanism": end.get("mechanism", ""),
            "n_clauses": len(claim.get("operative_clauses") or []), "n_source_refs": len(refs),
            "counted_ready_for_human_review": rd.get("ready_for_human_review", ""),
            "ready_tier": rd.get("ready_tier", ""), "text_evidence_tier": rd.get("text_evidence_tier", ""),
            "human_certified": "no",  # always; certified = 0 in this release
        })
        for path, ref in refs:
            q = ref.get("quote")
            ref_rows.append({
                "instrument_id": iid, "claim_sha256": sha, "ref_path": path, "url": ref.get("url", ""),
                "sha256": ref.get("sha256", ""), "text_sha256": ref.get("text_sha256", ""),
                "char_start": ref.get("char_start", ""), "char_end": ref.get("char_end", ""),
                "grade": ref.get("grade", "") or "unlabelled_in_claim",
                "acceptable_as_original": ref.get("acceptable_as_original", ""),
                "page_or_item": ref.get("page_or_item", ""), "requires_page_check": ref.get("requires_page_check", ""),
                "location_verified": ref.get("location_verified", ""),
                "quote_sha256": hashlib.sha256(q.encode("utf-8")).hexdigest() if isinstance(q, str) else "",
                "quote_len": len(q) if isinstance(q, str) else "",
            })
    return claims_out.getvalue().encode("utf-8"), index_rows, ref_rows, superseded


def csv_bytes(rows, fields=None):
    buf = io.StringIO()
    fields = fields or (list(rows[0].keys()) if rows else [])
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


REGISTER_KEEP = ["instrument_id", "number", "suffix", "era", "census_class", "date", "date_source", "title", "president",
                 "best_held", "official_sources", "archival_replica", "transcription_sources", "text_files",
                 "provisional_status", "original_text_step", "ready_for_human_review", "blockers",
                 "proquest_pdf_sha256", "proquest_text_usable"]


# decision_origin prefix -> evidence tier label added to the status ledger. All tiers are provisional and uncertified.
STATUS_TIERS = [
    ("inherited_legacy_v2", "S1_inherited_legacy_v2_ai_label"),
    ("opus_checkpoint2", "S2_ai_label_opus_overlay"),
    ("opus_complete_addition", "S2_ai_label_opus_overlay"),
    ("jacquard", "S3_ai_class_status_sampled_independent_ai_review"),
    ("sinclair", "S4_ai_proposal_cross_family_ai_review_owner_adopted"),
    ("bowditch", "S4_ai_proposal_ai_rereview_owner_adopted"),
    ("dorotheus", "S5_ai_sample_probe"),
]


def derive_ledger(repo):
    """The reconciled provisional-status ledger plus two columns: status_evidence_tier and human_certified."""
    rdr = csv.DictReader(io.StringIO(repo.show("research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv").decode("utf-8")))
    rows = []
    for r in rdr:
        origin = r.get("decision_origin", "")
        tier = next((t for pre, t in STATUS_TIERS if origin.startswith(pre)), "S0_unclassified_origin")
        r["status_evidence_tier"] = tier
        r["human_certified"] = "no"
        rows.append(r)
    fields = list(rows[0].keys())
    return csv_bytes(rows, fields)


def derive_register(repo):
    rdr = csv.DictReader(io.StringIO(repo.show("jobs/domesday-register/output/REGISTER.csv").decode("utf-8")))
    return csv_bytes(list(rdr), REGISTER_KEEP)


def derive_source_manifest(repo, cited_hashes, paths):
    """One row per (sha256, url) from the SOURCES.jsonl of the listed jobs. Metadata only."""
    fields = ["source_job", "url", "requested_url", "sha256", "bytes", "content_type", "retrieved_utc", "route", "grade",
              "acceptable_as_original", "instrument_ids", "page_or_item", "cited_by_a_filed_claim"]
    seen, rows = set(), []
    for path in paths:
        job = path.split("/")[1]
        for line in repo.show(path).decode("utf-8").splitlines():
            if not line.strip():
                continue
            s = json.loads(line)
            sha = s.get("sha256") or s.get("exact_source_text_sha256") or ""
            url = s.get("url") or s.get("requested_url") or s.get("archival_id") or ""
            key = (sha, url)
            if not sha or key in seen:
                continue
            seen.add(key)
            rows.append({
                "source_job": job, "url": url, "requested_url": s.get("requested_url", ""), "sha256": sha,
                "bytes": s.get("bytes", ""), "content_type": s.get("content_type", ""),
                "retrieved_utc": s.get("retrieved_utc", ""), "route": s.get("route", ""), "grade": s.get("grade", ""),
                "acceptable_as_original": s.get("acceptable_as_original", ""),
                "instrument_ids": "|".join(s.get("instrument_ids") or []),
                "page_or_item": (s.get("page_or_item") or "")[:300],
                "cited_by_a_filed_claim": "yes" if sha in cited_hashes else "no",
            })
    rows.sort(key=lambda r: (r["sha256"], r["url"]))
    return csv_bytes(rows, fields), rows


def zip_bytes(repo, source_paths):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for sp in source_paths:
            for _, p in sorted(repo.ls(sp), key=lambda x: x[1]):
                zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0))  # fixed timestamp: reproducible
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, repo.show(p))
    return buf.getvalue()


# ---------------------------------------------------------------- build
def check_universe(repo, readiness, allow_stale):
    """Every table must describe the same orders: census == readiness == register (owner rule: one denominator)."""
    census = {r["id"] for r in csv.DictReader(io.StringIO(
        repo.show("research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv").decode("utf-8")))}
    register = {r["instrument_id"] for r in csv.DictReader(io.StringIO(
        repo.show("jobs/domesday-register/output/REGISTER.csv").decode("utf-8")))}
    ready = set(readiness)
    problems = []
    for name, ids in (("register", register), ("readiness tracker", ready)):
        if ids != census:
            problems.append(f"{name} has {len(ids)} orders, census {len(census)}; "
                            f"only in census {len(census - ids)}, only in {name} {len(ids - census)}")
    for p in problems:
        print("UNIVERSE MISMATCH:", p, file=sys.stderr)
    if problems and not allow_stale:
        sys.exit("refusing to build: tables describe different universes (rebuild the stale job, or pass "
                 "--allow-stale-register and say so in RELEASE_NOTES.md)")


def build(repo, out, allow_stale=False):
    if os.path.exists(out) and os.listdir(out):
        sys.exit("output directory must be empty: " + out)
    os.makedirs(out, exist_ok=True)
    rows = read_contents()
    written = {}

    def put(rel, data):
        p = os.path.join(out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(data)
        written[rel] = data

    # the readiness table is both a release file and the join key for the claim index
    ready_csv = repo.show("jobs/readiness-tracker/output/READINESS_BY_ORDER.csv").decode("utf-8")
    readiness = {r["instrument_id"]: r for r in csv.DictReader(io.StringIO(ready_csv))}
    check_universe(repo, readiness, allow_stale)
    derived = {}
    for r in rows:
        kind, rel, sps = r["kind"], r["release_path"], split_paths(r["source_paths"])
        if kind == "copy":
            bad = refuse_excluded(sizes(repo, sps)[1])
            if bad:
                sys.exit(f"exclusion rule: {rel} <- {bad}")
            put(rel, repo.show(sps[0]))
        elif kind == "zip":
            bad = refuse_excluded(sizes(repo, sps)[1])
            if bad:
                sys.exit(f"exclusion rule: {rel} <- {bad}")
            put(rel, zip_bytes(repo, sps))
        elif kind == "derive:ledger":
            put(rel, derive_ledger(repo))
        elif kind == "derive:register":
            put(rel, derive_register(repo))
        elif kind == "derive:claims":
            if "claims" not in derived:
                derived["claims"] = derive_claims(repo, readiness)
            claims_jsonl, index_rows, ref_rows, superseded = derived["claims"]
            if rel.endswith("filed_claims.jsonl.gz"):
                put(rel, gz_bytes(claims_jsonl))
            elif rel.endswith("filed_claims_index.csv"):
                put(rel, csv_bytes(index_rows))
            elif rel.endswith("claim_source_refs.csv.gz"):
                put(rel, gz_bytes(csv_bytes(ref_rows)))
        elif kind == "derive:source_manifest":
            if "claims" not in derived:
                derived["claims"] = derive_claims(repo, readiness)
            cited = {x["sha256"] for x in derived["claims"][2]}
            data, mrows = derive_source_manifest(repo, cited, sps)
            put(rel, gz_bytes(data))
            have = {x["sha256"] for x in mrows}
            derived["coverage"] = (len(cited), len(cited & have))
        elif kind == "local":  # a file of this folder (the release carries the script that built it)
            with open(os.path.join(HERE, sps[0]), "rb") as fh:
                put(rel, fh.read())
        elif kind in ("pending", "generated"):
            continue
        else:
            sys.exit("unknown kind " + kind)

    summary = {"cited_source_hashes": None, "cited_hashes_in_manifest": None}
    if "coverage" in derived:
        summary["cited_source_hashes"], summary["cited_hashes_in_manifest"] = derived["coverage"]
    if "claims" in derived:
        summary["filed_claims_latest_per_order"] = len(derived["claims"][1])
        summary["superseded_claim_lines"] = derived["claims"][3]
    manifest = {
        "release": "bodley",
        "source_repository": "https://github.com/D3m0sthene5/Executive-Orders",
        "source_commit": repo.commit,
        "readiness_generation_id": next(iter(readiness.values()), {}).get("generation_id", ""),
        "built_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "human_certified_whole_lifecycle": 0,
        "files": {k: {"bytes": len(v), "sha256": hashlib.sha256(v).hexdigest()} for k, v in sorted(written.items())},
        "summary": summary,
    }
    put("MANIFEST.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    sums = "".join(f"{hashlib.sha256(v).hexdigest()}  {k}\n" for k, v in sorted(written.items()))
    put("SHA256SUMS", sums.encode("utf-8"))
    total = sum(len(v) for v in written.values())
    print(f"built {len(written)} files, {total / 2**20:.2f} MiB, into {out}")
    print(json.dumps(summary, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.abspath(os.path.join(HERE, "..", "..")))
    ap.add_argument("--commit", default="origin/main")
    ap.add_argument("--build", action="store_true", help="write the release folder (default is a dry run)")
    ap.add_argument("--out", help="empty output directory for --build")
    ap.add_argument("--allow-stale-register", action="store_true",
                    help="build although register/tracker/census row sets differ (must be disclosed in RELEASE_NOTES.md)")
    a = ap.parse_args()
    try:
        repo = Repo(a.repo, a.commit)
        if a.build:
            if not a.out:
                ap.error("--build needs --out")
            return build(repo, a.out, a.allow_stale_register)
        return dry_run(repo)
    except FileNotFoundError as e:
        print("missing input:", e, file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
