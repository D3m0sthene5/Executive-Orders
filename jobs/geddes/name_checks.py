"""Literal-name counterexample search over the existing held-text scope.

The inventory is Git's exact jobs/*/output/texts/**/*.txt set excluding
clause-drafts, matching Cruden's declared held-text scope. Missing bytes cannot
establish a negative. A positive counterexample additionally needs an
unambiguous publisher identity; an unrelated filename is not one.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ASSERTION = re.compile(r"\bno\s+(?:other\s+)?(?:held\s+|saved\s+|executive\s+){0,2}orders?\b(?P<window>[^.!?\n]{0,120}?)\s+names?\s+(?P<name>[^.!?\n]{3,130})", re.I)
MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}"


class Snapshot:
    """One command's frozen search bytes, reverified before output is accepted."""
    def __init__(self, repo):
        self.repo = Path(repo).resolve()
        self.loaded = {}
        self.states = {}
        self.active = False
        try:
            self.head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            self.head = None

    def __enter__(self):
        self.active = True
        return {"_snapshot": self}

    def __exit__(self, kind, value, traceback):
        self.active = False
        if kind is None:
            if self.head is not None and subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo).strip() != self.head:
                raise ValueError("held corpus inventory commit changed during search")
            for rel, expected in self.states.items():
                path = (self.repo / rel).resolve()
                actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_relative_to(self.repo) and path.is_file() else None
                if actual != expected:
                    raise ValueError("held corpus changed during literal-name search: " + rel)

    def read(self, inventory, algorithm, conflicts):
        key = (algorithm, tuple(sorted(inventory.items())), tuple(sorted(conflicts)))
        if key not in self.loaded:
            self.loaded[key] = _read_inventory(self.repo, inventory, algorithm, conflicts)
            available, missing, bad = self.loaded[key]
            # Bind the exact bytes actually searched. A second read here
            # could accept B while the cached search still used verified A.
            for rel, (_, digest) in available.items():
                self.states[rel] = digest
            for rel in missing:
                self.states[rel] = None
        return self.loaded[key]


def _read_inventory(repo, inventory, algorithm, conflicts):
    available, missing, bad = {}, [], list(set(conflicts))
    for rel, expected in sorted(inventory.items()):
        path = (repo / rel).resolve()
        if rel in bad:
            continue
        if not path.is_relative_to(repo) or not path.is_file():
            missing.append(rel)
            continue
        raw = path.read_bytes()
        actual = (hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                  if algorithm == "git_blob_sha1" else hashlib.sha256(raw).hexdigest())
        if actual != expected:
            bad.append(rel)
            continue
        available[rel] = (raw.decode("utf-8", errors="replace"), hashlib.sha256(raw).hexdigest())
    return available, missing, bad


def _norm(s):
    return re.sub(r"[^\w]+", " ", str(s).casefold()).strip()


def _parts(claim):
    from citation_checks import _reason_parts
    return _reason_parts(claim)


def _inventory(repo, cache):
    # HEAD binds the set, not merely its count. No packet-only inventory is
    # presented as the full held corpus, and a changed packet cannot hide a file.
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, stderr=subprocess.DEVNULL).decode().strip()
        key = ("held-inventory", head)
        if key not in cache:
            raw = subprocess.check_output(["git", "ls-tree", "-rz", "HEAD", "jobs"], cwd=repo, stderr=subprocess.DEVNULL)
            rows = {}
            for record in raw.split(b"\0"):
                if not record:
                    continue
                meta, path = record.decode().split("\t", 1)
                if "/texts/" in path and path.endswith(".txt") and not path.startswith("jobs/clause-drafts/"):
                    rows[path] = meta.split()[2]
            cache[key] = rows
        return head, cache[key], None
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None, {}, "tracked_held_text_inventory_unavailable"


def _publisher_records(repo, cache):
    path = repo / "jobs/app-executive-orders/output/INDEX.jsonl"
    if not path.is_file():
        return {}, None
    raw = path.read_bytes()
    try:
        expected = subprocess.check_output(["git", "rev-parse", "HEAD:jobs/app-executive-orders/output/INDEX.jsonl"], cwd=repo, stderr=subprocess.DEVNULL).decode().strip()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual != expected:
            return {}, None
    except (OSError, subprocess.CalledProcessError):
        return {}, None
    digest = hashlib.sha256(raw).hexdigest()
    key = ("publisher-index", digest)
    if key not in cache:
        records = {}
        for line in raw.splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("path") and r.get("instrument_id"):
                records.setdefault(Path(r["path"]).name + ".txt", []).append(r)
        cache[key] = records
    return cache[key], digest


def scan_names(packet_path, names, repo, cache=None):
    repo = Path(repo).resolve()
    cache = {} if cache is None else cache
    head, inventory, issue = _inventory(repo, cache)
    algorithm = "git_blob_sha1"
    conflicts = []
    if issue:
        # Portable fixtures and exported packets may lack Git. This fallback
        # is explicitly packet-only; its size never proves full corpus scope.
        algorithm = "sha256"
        inventory = {}
        root = Path(packet_path).parent if packet_path else None
        if root and root.is_dir():
            for p in sorted(root.rglob("PACKET.json")):
                for rel, expected in json.loads(p.read_text()).get("held_text_file_pins", {}).items():
                    if rel in inventory and inventory[rel] != expected:
                        conflicts.append(rel)
                    inventory[rel] = expected
    snapshot = cache.get("_snapshot")
    if isinstance(snapshot, Snapshot) and snapshot.active and snapshot.repo == repo:
        available, missing, bad = snapshot.read(inventory, algorithm, conflicts)
    else:
        available, missing, bad = _read_inventory(repo, inventory, algorithm, conflicts)
    hits = {name: [] for name in names}
    for name in names:
        words = _norm(name).split()
        if not words:
            continue
        pattern = re.compile(r"\b" + r"[\W_]+".join(re.escape(w) for w in words) + r"\b", re.I)
        for rel, (text, digest) in available.items():
            match = pattern.search(text)
            if match:
                hits[name].append({"path": rel, "sha256": digest,
                                   "char_start": match.start(), "char_end": match.end(), "quote": match.group()})
    scope = {"inventory_commit": head, "inventory_kind": "tracked_jobs_texts" if not issue else "packet_pins_only",
             "inventory_sha256": hashlib.sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest(),
             "tracked_files": len(inventory), "verified_files": len(available),
             "missing_files": len(missing), "changed_files": bad,
             "full_discovered_corpus_covered": bool(inventory) and not issue and not missing and not bad,
             "detail": "Exact tracked path membership and source bytes define this search scope; a matching count is insufficient."}
    failures = [{"path": p, "reason": "file_unavailable"} for p in missing] + [{"path": p, "reason": "hash_or_pin_conflict"} for p in bad]
    return hits, failures, len(inventory), scope


def _date(window):
    m = re.search(r"\bafter\s+(" + MONTH + r"|\d{4}-\d{2}-\d{2})", window, re.I)
    if not m:
        return None
    for fmt in ("%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(m[1], fmt).date().isoformat()
        except ValueError:
            pass
    return None


def _aliases(name):
    name = re.sub(r"^the\s+", "", name.strip(" '\"“”"), flags=re.I)
    if re.match(r"(?:this|that|such|same|these|those|its|their)\b", name, re.I):
        return []
    base = re.sub(r"^(?:Codes?\s+of\s+Fair\s+Competition\s+for\s+(?:the\s+)?)", "", name, flags=re.I)
    base = re.sub(r"\s+(?:Industry\s+)?Codes?$|\s+Industry$", "", base, flags=re.I)
    return [n for n in dict.fromkeys((_norm(name), _norm(base))) if len(n.split()) >= 2 and not re.fullmatch(r"(?:executive order|eo) \d+", n)]


def check(claim, dossier, repo, packet_path=None, cache=None):
    repo = Path(repo).resolve()
    cache = {} if cache is None else cache
    requests = []
    unresolved = []
    for field, text in _parts(claim):
        for match in ASSERTION.finditer(text):
            aliases = _aliases(match["name"])
            if aliases:
                requests.append((field, match.group(), aliases, _date(match["window"])))
            else:
                unresolved.append({"code": "literal_name_unresolved", "field": field, "assertion": match.group(),
                                   "detail": "A deictic phrase such as 'this code' is not a proper-name query. Resolve its named antecedent before making a negative search claim."})
    if not requests:
        return {"flags": [], "coverage_gaps": unresolved}
    records, index_sha = _publisher_records(repo, cache)
    all_names = list(dict.fromkeys(a for _, _, aliases, _ in requests for a in aliases))
    matches, unavailable, _, scope = scan_names(packet_path, all_names, repo, cache)
    gaps = unresolved + [{"code": "literal_name_corpus_scope", **scope}]
    if index_sha is None:
        gaps.append({"code": "name_publisher_identity_index_unavailable_or_changed",
                     "detail": "Literal matches cannot be linked to another order without the retained publisher identity index."})
    flags = []
    for field, assertion, aliases, cutoff in requests:
        candidates = []
        local_hits = {}
        for alias in aliases:
            for hit in matches[alias]:
                local_hits.setdefault(hit["path"], (alias, hit))
        for rel, (needle, hit) in local_hits.items():
            rows = records.get(Path(rel).name, []) if rel.startswith("jobs/app-executive-orders/") else []
            ids = {r["instrument_id"] for r in rows}
            if len(ids) != 1 or claim.get("instrument_id") in ids:
                continue
            identity = rows[0]
            title_id = re.search(r"Executive Order\s+(\d+(?:[- ]?[A-Z])?)\b", str(identity.get("title") or ""), re.I)
            if not title_id or "EO:" + re.sub(r"[- ]", "", title_id[1]).upper() not in ids:
                continue
            if needle != aliases[0] and re.search(r"\bcodes?\b", aliases[0]):
                # An industry-name alias is a search lead, not proof that a
                # later labor/commerce order names the historical NRA code.
                raw = (repo / rel).read_bytes()
                if hashlib.sha256(raw).hexdigest() != hit["sha256"]:
                    gaps.append({"code": "name_alias_source_changed", "field": field, "path": rel,
                                 "detail": "Source changed after the literal hit; no identity counterexample is emitted from mixed versions."})
                    continue
                text = raw.decode("utf-8")
                context = text[max(0, hit["char_start"]-180):hit["char_end"]+180]
                if not re.search(r"\bcodes?\s+of\s+(?:fair\s+)?competition\b", context, re.I):
                    gaps.append({"code": "name_alias_entity_unverified", "field": field, "path": rel,
                                 "detail": "Industry words matched, but the source does not locally identify the asserted fair-competition code."})
                    continue
            date = identity.get("date")
            if cutoff and (not date or date <= cutoff):
                continue
            candidates.append({"instrument_id": identity["instrument_id"], "date": date,
                               "text_path": rel, "text_sha256": hit["sha256"],
                               "char_start": hit["char_start"], "char_end": hit["char_end"], "quote": hit["quote"],
                               "matched_literal_name": needle, "publisher_title": identity.get("title"),
                               "publisher_url": identity.get("url"), "publisher_index_sha256": index_sha})
        if candidates:
            flags.append({"code": "literal_name_counterexample", "field": field,
                          "assertion": assertion, "counterexamples": candidates,
                          "detail": "A distinct held publisher-identified order contains the asserted name; inspect the source before retaining this negative assertion."})
        gaps.append({"code": "literal_name_search_performed", "field": field, "names": aliases,
                     "after_date": cutoff, "counterexamples": len(candidates),
                     "negative_established": False,
                     "detail": "A name match is evidence to inspect, not a legal-effect conclusion. Missing files or unlinked identities prevent an all-held-text negative."})
    return {"flags": flags, "coverage_gaps": gaps}
