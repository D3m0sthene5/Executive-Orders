"""Source-bound advisory checks for order identities and FR citations.

This module reads only a claim, its frozen dossier, packet lookup leads, and
held publisher records. A lookup hit is a candidate, never an identity by
itself: its text hash, publisher title/date and local claim context must bind.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

FR = re.compile(r"(?<!\w)(\d{1,3})\s+F\.?\s*R\.?\s+(\d+)(?!\d)", re.I)
EO = re.compile(r"\b(?:Executive\s+Orders?\s+(?:No\.?\s*)?|EO\s*:?[ \t]*)(\d{1,6}(?:[- ]?[A-Z])?)\b", re.I)
ISSUE = re.compile(r"\b(?:issue\s+(?:of\s+)?|published\s+(?:on\s+)?|publication\s+(?:date\s+)?)(\d{4}-\d{2}-\d{2})\b", re.I)
MONTH_DATE = re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b", re.I)
SOURCE_KEYS = ("page_or_item", "citation", "url", "title")
OWN_CUE = re.compile(r"\b(?:original|own\s+order|this\s+order|registered|both\s+orders\s+are\s+printed|same\s+Federal\s+Register\s+page)\b", re.I)
STOP = {"the", "and", "for", "code", "fair", "competition", "industry", "trade", "order", "executive", "amended", "amendment", "of", "to", "a", "an", "with", "under", "from", "this", "that"}


def _meta(source):
    return " ".join(str(source.get(key) or "") for key in SOURCE_KEYS)


def _source(dossier, cited):
    """The original/ACT record, rather than the claim's repeated metadata."""
    if not isinstance(cited, dict):
        return None
    evidence_id = cited.get("evidence_id")
    if cited.get("evidence_id_encoding") == "base64url-utf8":
        import base64
        try:
            evidence_id = base64.urlsafe_b64decode(evidence_id + "=" * (-len(evidence_id) % 4)).decode()
        except (TypeError, ValueError, UnicodeError):
            return None
    record = dossier.get("evidence", {}).get(evidence_id)
    if not isinstance(record, dict):
        return None
    return record.get("actor_source") or record.get("source")


def _verified(source, repo):
    if not isinstance(source, dict):
        return False
    path, expected = source.get("text_path"), source.get("text_sha256")
    if not path or not expected:
        return False
    root = Path(repo).resolve()
    file = (root / path).resolve()
    return file.is_relative_to(root) and file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest() == expected


def _reason_parts(claim):
    """Yield claim reasoning, including decoded embedded Member checks."""
    def visit(obj, path="claim"):
        if isinstance(obj, dict):
            for key, val in obj.items():
                p = f"{path}.{key}"
                if isinstance(val, str) and (key.endswith("reason") or key.endswith("rationale") or key in {"research_rationale", "savings_residuals", "current_legal_basis"}):
                    marker = re.search(r"Member checks:\s*", val, re.I)
                    if marker:
                        yield p, val[:marker.start()]
                        try:
                            member, end = json.JSONDecoder().raw_decode(val[marker.end():])
                        except ValueError:
                            member, end = None, 0
                        if isinstance(member, dict):
                            for subkey, subval in member.items():
                                if isinstance(subval, str):
                                    yield f"{p}.member_checks.{subkey}", subval
                            yield p, val[marker.end() + end:]
                        else:
                            yield p, val[marker.start():]
                    else:
                        yield p, val
                else:
                    yield from visit(val, p)
        elif isinstance(obj, list):
            for i, val in enumerate(obj):
                yield from visit(val, f"{path}[{i}]")
    yield from visit(claim)


def _lookup_candidates(dossier, packet_path, repo, cache):
    """Resolve member-specific lookup leads against held APP listing and bytes."""
    if not packet_path:
        return [], "packet_path_unavailable", set()
    folder = Path(packet_path).parent
    lookup = next((p for p in (folder / "LOOKUPS.details.json", folder.parent / "LOOKUPS.details.json") if p.is_file()), None)
    index = Path(repo) / "jobs/app-executive-orders/output/INDEX.jsonl"
    if lookup is None or not index.is_file():
        return [], "publisher_or_lookup_file_unavailable", set()
    raw_index = index.read_bytes()
    # A content digest, rather than size/mtime, guards against in-place data
    # replacement while this invocation is using a cached publisher index.
    key = (str(index.resolve()), hashlib.sha256(raw_index).hexdigest())
    git_dir = Path(repo) / ".git"
    if git_dir.exists():
        expected = cache.get(("git_index_blob", str(Path(repo).resolve())))
        if expected is None:
            result = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD:jobs/app-executive-orders/output/INDEX.jsonl"],
                                    capture_output=True, text=True, check=False)
            expected = result.stdout.strip() if result.returncode == 0 else "unavailable"
            cache[("git_index_blob", str(Path(repo).resolve()))] = expected
        actual = hashlib.sha1(b"blob " + str(len(raw_index)).encode() + b"\0" + raw_index).hexdigest()
        if expected != actual:
            return [], "publisher_index_git_blob_mismatch", set()
    if key not in cache:
        records = {}
        for line in raw_index.decode("utf-8").splitlines():
            row = json.loads(line)
            path = row.get("path")
            if isinstance(path, str) and path.startswith("/documents/") and row.get("instrument_id"):
                rel = "jobs/app-executive-orders/output/texts/" + Path(path).name + ".txt"
                records.setdefault(rel, []).append(row)
        cache[key] = records
    details = json.loads(lookup.read_text(encoding="utf-8"))
    member = details.get("members", {}).get(dossier.get("instrument_id"), {})
    candidates = []
    leads = member.get("code_mentions", []) + member.get("number_citations", [])
    lead_numbers = set()
    for lead in leads:
        path, sha = lead.get("file"), lead.get("raw_sha256")
        if not path or not sha:
            continue
        name_number = re.search(r"(?:^|/)executive-order-(\d+)(?:[-.]|$)", path, re.I)
        if name_number:
            lead_numbers.add(name_number.group(1))
        file = (Path(repo).resolve() / path).resolve()
        if not file.is_relative_to(Path(repo).resolve()) or not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != sha:
            continue
        for listing in cache[key].get(path, []):
            # Listing is publisher identity, lookup hash is the frozen text.
            heading = EO.search(listing.get("title", ""))
            listed_id = listing["instrument_id"].removeprefix("EO:")
            if heading and re.sub(r"[- ]", "", heading.group(1)).upper() == listed_id:
                candidates.append((listing, lead))
    return candidates, "publisher_record_not_bound_or_text_unverified" if leads and not candidates else None, lead_numbers


def _subject_overlap(sentence, listing, lead, dossier):
    # A dated citation alone is too weak. The publisher subject must identify
    # words in the sentence, or a code mention must match this member's title.
    words = lambda s: {w for w in re.findall(r"[a-z]{4,}", s.casefold()) if w not in STOP}
    title = re.sub(r"^Executive Order\s+[\d-]+[A-Z]?\s*[—:-]?", "", listing.get("title", ""), flags=re.I)
    if len(words(sentence) & words(title)) >= 2:
        return True
    original = dossier.get("evidence", {}).get(dossier.get("original_source_id"), {}).get("source", {})
    return (bool(re.search(r"\b(?:code|amendment|approval)\b", sentence, re.I))
            and len(words(lead.get("match", "")) & words(_meta(original))) >= 2)


def _identity_flags(claim, dossier, repo, packet_path, cache):
    flags, gaps = [], []
    candidates, lookup_issue, lead_numbers = _lookup_candidates(dossier, packet_path, repo, cache)
    for field, text in _reason_parts(claim):
        for match in EO.finditer(text):
            asserted = re.sub(r"[- ]", "", match.group(1)).upper()
            if asserted == dossier.get("instrument_id", "").replace("EO:", ""):
                continue
            # Bind only the local assertion and its own date/subject. An EO in
            # a quotation or a list elsewhere is not an identity assertion.
            tail = text[match.end():match.end() + 180]
            date_match = re.match(r"\s+(?:of|dated|signed)\s+(" + MONTH_DATE.pattern + r")", tail, re.I)
            if not date_match:
                continue
            asserted_base = re.match(r"\d+", asserted).group()
            if lookup_issue and (lookup_issue != "publisher_record_not_bound_or_text_unverified" or asserted_base in lead_numbers):
                gaps.append({"code": "reasoning_identity_lookup_unavailable", "field": field,
                             "reason": lookup_issue})
                continue
            try:
                date = datetime.strptime(date_match.group(1).title(), "%B %d, %Y").date().isoformat()
            except ValueError:
                continue
            context = text[max(0, match.start() - 60):match.end() + 220].split(".", 1)[0]
            bound = [(row, lead) for row, lead in candidates
                     if row.get("date") == date and re.match(r"\d+", row.get("instrument_id", "").removeprefix("EO:"))
                     and re.match(r"\d+", row["instrument_id"].removeprefix("EO:")).group() == asserted_base
                     and _subject_overlap(context, row, lead, dossier)]
            identities = {row["instrument_id"] for row, _ in bound}
            if len(identities) != 1:
                if bound:
                    gaps.append({"code": "later_order_identity_ambiguous", "field": field, "asserted": asserted, "candidates": sorted(identities)})
                continue
            actual = next(iter(identities)).removeprefix("EO:")
            if actual != asserted:
                flags.append({"code": "reasoning_order_identity_mismatch", "field": field,
                              "detail": f"reasoning identifies EO {asserted}; hash-verified lookup and APP publisher title/date identify EO {actual}",
                              "source_path": bound[0][1]["file"]})
    return flags, gaps


def _reason_citations(claim, dossier, repo):
    flags, gaps = [], []
    original = dossier.get("evidence", {}).get(dossier.get("original_source_id"), {}).get("source")
    own_ok = _verified(original, repo)
    for field, text in _reason_parts(claim):
        # Existing event-row checks bind event reasons separately. Skip these
        # here to avoid assigning actor references to the original source.
        if ".first_end." in field or ".later_events[" in field:
            continue
        for pattern, code in ((FR, "fr_citation_mismatch"), (ISSUE, "fr_issue_date_mismatch")):
            for match in pattern.finditer(text):
                nearby = text[max(0, match.start() - 160):match.start()]
                # Explicit local source role, including two orders printed on
                # the same page. Do not compare all citations in a rationale.
                if not OWN_CUE.search(nearby):
                    continue
                nearest = list(EO.finditer(nearby))
                if (nearest and re.sub(r"[- ]", "", nearest[-1].group(1)).upper() != dossier.get("instrument_id", "").removeprefix("EO:")
                        and not re.search(r"\b(?:both orders (?:are )?printed|same Federal Register page)\b", nearby, re.I)):
                    continue
                if not own_ok:
                    gaps.append({"code": "reasoning_citation_source_unverified", "field": field,
                                 "detail": "original source text unavailable or hash mismatch"})
                    continue
                if pattern is FR:
                    expected = set(FR.findall(_meta(original)))
                    actual = (match.group(1), match.group(2))
                    if not expected:
                        gaps.append({"code": "original_fr_locator_missing", "field": field})
                    elif actual not in expected:
                        flags.append({"code": code, "field": field,
                                      "detail": f"reasoning cites {actual[0]} FR {actual[1]}; pinned original cites {sorted(expected)}",
                                      "source_id": dossier.get("original_source_id")})
                else:
                    source_date = re.search(r"/FR-(\d{4}-\d{2}-\d{2})/", original.get("url", ""))
                    if not source_date:
                        gaps.append({"code": "original_fr_issue_date_missing", "field": field})
                    elif match.group(1) != source_date.group(1):
                        flags.append({"code": code, "field": field,
                                      "detail": f"reasoning says issue {match.group(1)}; pinned original issue is {source_date.group(1)}",
                                      "source_id": dossier.get("original_source_id")})
    return flags, gaps


def check(claim, dossier, repo, packet_path=None, cache=None):
    """Return source-bound advisory flags and separately disclosed gaps."""
    cache = {} if cache is None else cache
    a, b = _identity_flags(claim, dossier, repo, packet_path, cache)
    c, d = _reason_citations(claim, dossier, repo)
    return {"flags": a + c, "coverage_gaps": b + d}
