"""Deterministic, offline discovery of the claim kit's held evidence.

The census and provisional-status table are authoritative inputs. Evidence never
adds identities or decides a status. Text records contain pointers, not bodies;
the excavators can therefore read one representation at a time.

New producers need no registration here. They may write FRAGMENTS*.jsonl and
SOURCES.jsonl in their output directory, or declare attributed text records at
any nesting in data/PROVENANCE.json. An attributed declaration has
``instrument_id``, ``text_path`` (``path`` is also accepted in provenance), and a
``source`` containing the original URL/hash/page. Use ``grade`` and
``acceptable_as_original`` to distinguish an original candidate from a derivative.
Per-volume page dumps without an order identity are never order texts.
"""

import csv
import hashlib
import json
import pathlib
import re
from collections import defaultdict


UNIVERSE = "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"
COMPILER_FILES = ("build.py", "inputs.py", "excavate.py", "current_evidence.py",
                  "assemble.py", "act_overrides.py", "lifecycle_obligations.py")
STATUSES = "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv"
HEX64 = re.compile(r"^[a-fA-F0-9]{64}$")
LFS_MAGIC = b"version https://git-lfs.github.com/spec/v1"
EVENT_KINDS = {"later_event_candidates", "whole_order_end_candidates"}
CURRENT_KINDS = {"current_predicate_candidates", "current_law", "current_law_candidates"}


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _jsonl(path, warnings):
    """Stream large machine outputs; malformed records remain visible as warnings."""
    try:
        with path.open(encoding="utf-8") as fh:
            for number, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except (ValueError, RecursionError):
                    warnings.append(f"{path.name}:{number}: malformed JSON; skipped")
                    continue
                if isinstance(row, dict):
                    yield row
                else:
                    warnings.append(f"{path.name}:{number}: non-object JSON; skipped")
    except (OSError, UnicodeError) as exc:
        warnings.append(f"{path.name}: unreadable ({type(exc).__name__}); skipped")


def _json(path, warnings):
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError, UnicodeError) as exc:
        warnings.append(f"{path.name}: unreadable ({type(exc).__name__}); skipped")
        return {}


def _csv(path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        yield from csv.DictReader(fh)


def _path(repo, base, raw):
    """Resolve declared paths inside the repo, including safe cross-output links.

    Output-relative paths are the producer convention. Already repo-relative
    paths remain so. Absolute paths, Windows paths, URLs, and symlink escapes
    cannot turn a declaration into a read outside the checkout.
    """
    if not isinstance(raw, str) or not raw.strip():
        return None
    raw = raw.replace("\\", "/")
    if raw.startswith("/") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", raw):
        return None
    parts = pathlib.PurePosixPath(raw).parts
    anchor = repo if parts and parts[0] in {"jobs", "research", "progress", "releases"} else base
    try:
        candidate = (anchor / raw).resolve()
        candidate.relative_to(repo)
    except (OSError, ValueError, RuntimeError):
        return None
    return candidate


def _source(node, inherited=None):
    """Take the citation from this declaration, preserving archival identifiers."""
    src = dict(inherited or {})
    for key in ("ref", "source", "original_source"):
        if isinstance(node.get(key), dict):
            src.update(node[key])
    for key in ("url", "sha256", "page_or_item", "text_sha256", "archival_id", "local_file_sha256"):
        if node.get(key) is not None:
            src[key] = node[key]
    if not src.get("url") and node.get("handle_url"):
        src["url"] = node["handle_url"]
    if not src.get("sha256") and node.get("pdf_sha256"):
        src["sha256"] = node["pdf_sha256"]
    for key in ("sha256", "text_sha256", "local_file_sha256"):
        if isinstance(src.get(key), str) and HEX64.fullmatch(src[key]):
            src[key] = src[key].lower()
    return src


def _boolean(value):
    if value is True or value == "true":
        return True
    if value is False or value == "false":
        return False
    return None


def _grade(node, inherited_grade, original_context, origin):
    grade = node.get("grade") or node.get("source_grade") or inherited_grade
    hints = " ".join(str(node.get(k) or "") for k in
                     ("flags", "confidence_note", "representation_type", "why", "notes"))
    hints = (str(grade or "") + " " + hints + " " + origin).lower()
    derivative = any(word in hints for word in (
        "compiled_transcription", "richardson", "as_amended_editorial",
        "as amended editorial", "ofr-codification", "derivative", "mirror_transcription"))
    if not grade:
        grade = "derivative_lead" if derivative else (
            "original_representation_unverified" if original_context else "held_text_lead")
    acceptable = _boolean(node.get("acceptable_as_original"))
    if derivative:
        acceptable = False
    elif acceptable is None:
        acceptable = bool(original_context)
    return grade, acceptable, derivative


def _quality(node, inherited=None):
    """Carry locator warnings through wrappers; a weak locator cannot self-upgrade."""
    quality = dict(inherited or {})
    declared = []
    for key in ("ref", "source", "original_source"):
        if isinstance(node.get(key), dict):
            declared.append(node[key])
    if isinstance(node.get("sources"), list) and len(node["sources"]) == 1:
        if isinstance(node["sources"][0], dict):
            declared.append(node["sources"][0])
    declared.append(node)
    requires_check = quality.get("requires_page_check", False)
    for declaration in declared:
        requires_check = requires_check or any(
            _boolean(declaration.get(key)) is True
            for key in ("needs_page_check", "requires_page_check"))
        location = declaration.get("location_confidence")
        if location is not None:
            quality["location_confidence"] = location
            requires_check = requires_check or str(location).lower() != "high"
        if declaration.get("confidence") is not None:
            quality["confidence"] = declaration["confidence"]
        verified = _boolean(declaration.get("location_verified"))
        if verified is not None:
            quality["location_verified"] = verified
    quality["requires_page_check"] = bool(requires_check)
    return quality


class _Collector:
    def __init__(self, repo, universe, warnings):
        self.repo = repo
        self.universe = universe
        self.warnings = warnings
        self.texts = []
        self.pairs = []
        self.current = defaultdict(list)
        self.status_histories = {}
        self.factual_obligations = defaultdict(list)
        self.factual_inputs_checked = {}
        self.hashes = {}
        self.text_keys = set()
        self.pair_keys = set()

    def identity(self, value):
        # Exact census forms only; never rewrite suffixes or infer identities.
        return value if isinstance(value, str) and value in self.universe else None

    def add_text(self, iid, node, base, source, grade, acceptable, dates, origin,
                 provenance=False, quality=None):
        declared_source = node.get("source") if isinstance(node.get("source"), dict) else {}
        raw = (node.get("text_path") or declared_source.get("text_path") or
               (node.get("path") if provenance else None))
        if not raw:
            return
        path = _path(self.repo, base, raw)
        if path is None:
            self.warnings.append(f"{origin}: unsafe text path {raw!r}; skipped")
            return
        rel = path.relative_to(self.repo).as_posix()
        if not path.is_file():
            self.warnings.append(f"{origin}: held text missing: {rel}")
            return
        if not iid:
            # Shared-volume dumps and a list of orders cited by a source do not
            # establish an order-specific text representation.
            return
        if not (HEX64.fullmatch(str(source.get("sha256") or "")) or
                HEX64.fullmatch(str(source.get("local_file_sha256") or ""))):
            self.warnings.append(f"{origin}: {iid} text lacks original-byte sha256: {rel}")
            return
        if not source.get("url") and not source.get("archival_id"):
            self.warnings.append(f"{origin}: {iid} text lacks source URL/archive id: {rel}")
            return
        if rel not in self.hashes:
            try:
                with path.open("rb") as fh:
                    first = fh.read(65536)
                    if first.startswith(LFS_MAGIC):
                        self.hashes[rel] = None
                    else:
                        digest = hashlib.sha256(first)
                        for block in iter(lambda: fh.read(1024 * 1024), b""):
                            digest.update(block)
                        self.hashes[rel] = digest.hexdigest()
            except OSError:
                self.hashes[rel] = None
        actual = self.hashes[rel]
        if actual is None:
            self.warnings.append(f"{origin}: text unavailable (LFS pointer or unreadable): {rel}")
            return
        expected = source.get("text_sha256")
        if expected and expected != actual:
            self.warnings.append(f"{origin}: text_sha256 mismatch: {rel}; skipped")
            return
        ref = {key: source.get(key) for key in ("url", "sha256", "page_or_item")}
        ref.update({key: source[key] for key in ("archival_id", "local_file_sha256") if source.get(key)})
        ref.update(text_path=rel, text_sha256=actual)
        quality = dict(quality or {})
        quality.setdefault("requires_page_check", False)
        ref.update(quality)
        row = {"instrument_id": iid, "text_path": rel, "source": ref,
               "grade": grade, "acceptable_as_original": acceptable,
               "signing_date": dates.get("signing_date"), "filing_date": dates.get("filing_date"),
               **quality}
        # Preserve each distinct citation/representation/grade. Repeated clause
        # offsets in the same exact text are one representation.
        key = _canonical(row)
        if key not in self.text_keys:
            self.text_keys.add(key)
            self.texts.append(row)

    def walk_texts(self, node, base, origin, iid=None, source=None, grade=None,
                   original_context=False, dates=None, acceptable=None, provenance=False,
                   quality=None):
        if isinstance(node, list):
            for item in node:
                self.walk_texts(item, base, origin, iid, source, grade, original_context,
                                dates, acceptable, provenance, quality)
            return
        if not isinstance(node, dict):
            return
        declared_iid = node.get("instrument_id")
        if declared_iid is not None:
            iid = self.identity(declared_iid)
        elif isinstance(node.get("instrument_ids"), list):
            # Only a singleton source attribution is order-specific. A shared
            # issue/volume with many instrument_ids must first be segmented.
            ids = node["instrument_ids"]
            iid = self.identity(ids[0]) if len(ids) == 1 else None
        local_source = _source(node, source)
        sources = node.get("sources")
        if isinstance(sources, list) and len(sources) == 1 and isinstance(sources[0], dict):
            local_source = _source(sources[0], local_source)
        original_context = original_context or node.get("kind") == "original_representation"
        local_grade, local_acceptable, derivative = _grade(node, grade, original_context, origin)
        local_quality = _quality(node, quality)
        if "needs_page_check" in str(local_grade):
            local_quality["requires_page_check"] = True
        if local_quality["requires_page_check"] and "needs_page_check" not in str(local_grade):
            local_grade = str(local_grade) + "_needs_page_check"
        explicit = _boolean(node.get("acceptable_as_original"))
        if acceptable is False or explicit is False:
            local_acceptable = False
        inherited_acceptable = False if acceptable is False or explicit is False or derivative else explicit
        local_dates = dict(dates or {})
        for key in ("signing_date", "filing_date"):
            if node.get(key):
                local_dates[key] = node[key]
        # A text_offsets declaration and its original_source are siblings in
        # clause-drafts. Join the pointer without inventing a new text file.
        if isinstance(node.get("text_offsets"), dict):
            pointer = node["text_offsets"]
            self.add_text(iid, pointer, base, local_source, local_grade,
                          local_acceptable, local_dates, origin, provenance, local_quality)
        self.add_text(iid, node, base, local_source, local_grade, local_acceptable,
                      local_dates, origin, provenance, local_quality)
        for key, child in node.items():
            if key in {"source", "original_source", "ref", "sources", "text_offsets"}:
                continue
            if isinstance(child, (dict, list)):
                self.walk_texts(child, base, origin, iid, local_source, local_grade,
                                original_context, local_dates, inherited_acceptable, provenance,
                                local_quality)

    def add_pair(self, target, event, origin):
        if not isinstance(event, dict):
            return
        proposal = event.get("proposal") if isinstance(event.get("proposal"), dict) else event
        meta = event.get("meta") if isinstance(event.get("meta"), dict) else event
        target = self.identity(proposal.get("target_id") or event.get("target_id") or target)
        actor = self.identity(proposal.get("actor_id") or proposal.get("actor") or
                              proposal.get("acting_id") or meta.get("acting_instrument_id"))
        if not target or not actor or actor == target:
            return
        row = {"target_id": target, "actor_id": actor,
               "source_event": dict(event, input_origin=origin)}
        parent = self.identity(event.get("parent_id") or meta.get("parent_id") or
                               meta.get("reaches_target_via"))
        if parent:
            row["parent_id"] = parent
        key = _canonical(row)
        if key not in self.pair_keys:
            self.pair_keys.add(key)
            self.pairs.append(row)

    def fragment(self, frag, base, origin):
        iid = self.identity(frag.get("instrument_id"))
        kind, data = frag.get("kind"), frag.get("data")
        rows = data if isinstance(data, list) else [data]
        if kind == 'shared_factual_obligations':
            # Factual answers and clause applicability are distinct from original
            # texts, legal events and current predicates. Never walk their text.
            try:
                status = base / 'STATUS.json'
                if status.exists() and json.loads(status.read_bytes()).get('result') != 'succeeded':
                    raise ValueError('NORTON run did not succeed')
                if base not in self.factual_inputs_checked:
                    pins = json.loads((base / 'INPUTS.json').read_bytes())
                    for name, digest in pins.get('consumer_sha256', pins['sha256']).items():
                        p = _path(self.repo, self.repo, name)
                        if p is None or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
                            raise ValueError('NORTON input changed: ' + name)
                    for name, digest in pins.get('code_sha256', {}).items():
                        p = _path(self.repo, self.repo / 'jobs/norton', name)
                        if p is None or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
                            raise ValueError('NORTON code changed: ' + name)
                    self.factual_inputs_checked[base] = True
                if iid and isinstance(data, dict) and data.get('legal_effect') == 'unresolved':
                    self.factual_obligations[iid].append(dict(data, input_origin=origin, machine_lead=True))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                self.warnings.append(f'{origin}: factual obligation rejected: {exc}')
            return
        if kind == 'status_history_candidates':
            if not iid or not isinstance(data,dict):return
            path=_path(self.repo,base,data.get('history_path'))
            try:
                if path is None:raise ValueError('unsafe history pointer')
                raw=path.read_bytes();history=json.loads(raw)
                if hashlib.sha256(raw).hexdigest()!=data.get('history_sha256') or history.get('instrument_id')!=iid:
                    raise ValueError('changed history or wrong identity')
                if (base/'FAILED.json').exists():raise ValueError('status-history run failed; outputs stale')
                status=base/'STATUS.json'
                if status.exists() and json.loads(status.read_bytes()).get('result')!='succeeded':
                    raise ValueError('status-history runner did not succeed')
                self.status_histories[iid]=dict(data,input_origin=origin,machine_lead=True)
            except (OSError,ValueError,UnicodeError) as exc:
                self.warnings.append(f'{origin}: status history rejected for {iid}: {exc}')
            return  # A status observation must never become an original or legal event.
        # These instrument_ids name the affected/cited order, not the author
        # of the evidence. Their statute/actor text must never become a text
        # representation of the target order.
        if kind not in EVENT_KINDS | CURRENT_KINDS | {"family_rule_checks"}:
            self.walk_texts(frag, base, origin)
        if kind in EVENT_KINDS:
            for event in rows:
                self.add_pair(iid, event, origin)
        if kind in CURRENT_KINDS and iid:
            for row in rows:
                if isinstance(row, dict):
                    lead = dict(row, instrument_id=iid, input_origin=origin,
                                fragment_kind=kind, machine_lead=True)
                    # A producer may provide exact spans in a held plain-text
                    # law source. Preserve those as evidence pointers without
                    # making that statute an original text of this order.
                    ref = _source(row)
                    raw = ref.get("text_path") or row.get("text_path")
                    if raw and "#" not in raw:
                        path = _path(self.repo, base, raw)
                        if path is not None and path.is_file():
                            ref["text_path"] = path.relative_to(self.repo).as_posix()
                            lead["text_path"] = ref["text_path"]
                    if ref:
                        lead["source"] = ref
                    self.current[iid].append(lead)


def _declared_files(node, repo, base):
    """Optional provenance file pointers; schema is semantic, never producer-specific."""
    if isinstance(node, list):
        for value in node:
            yield from _declared_files(value, repo, base)
    elif isinstance(node, dict):
        for key, value in node.items():
            if key in {"fragments", "fragments_path", "fragment_files", "sources_path", "source_files"}:
                values = value if isinstance(value, list) else [value]
                for raw in values:
                    path = _path(repo, base, raw)
                    if path and path.suffix == ".jsonl" and path.is_file():
                        yield path
            if isinstance(value, (dict, list)):
                yield from _declared_files(value, repo, base)


def load_corpus(repo):
    """Return census, explicit statuses, drafts and lazy machine-evidence records.

    No network, writes, legal inference, identity admission, or status inference.
    The sole required input is the census. Optional missing inputs are reported.
    """
    repo = pathlib.Path(repo).resolve()
    census = repo / UNIVERSE
    if not census.is_file():
        raise FileNotFoundError(f"missing authoritative census {UNIVERSE}; add it to needs.txt")
    universe = {}
    for row in _csv(census):
        iid = row.get("id") or row.get("instrument_id")
        if iid and row.get("included_in_bibliography", "1") == "1":
            if iid in universe:
                raise ValueError(f"duplicate census identity {iid}")
            universe[iid] = row
    if not universe:
        raise ValueError(f"empty authoritative census {UNIVERSE}")
    warnings, statuses, drafts, searches = [], {}, {}, {}
    status_path = repo / STATUSES
    authoritative_statuses = status_path.is_file()
    if authoritative_statuses:
        for row in _csv(status_path):
            iid = row.get("instrument_id") or row.get("id")
            status = row.get("provisional_substantive_status")
            if iid in universe and status in {"yes", "no"}:
                if iid in statuses and statuses[iid] != status:
                    raise ValueError(f"conflicting provisional statuses for {iid}")
                statuses[iid] = status
    else:
        warnings.append(f"{STATUSES}: missing; only explicit draft provisional statuses used")
    collector = _Collector(repo, universe, warnings)
    files = set()
    jobs = repo / "jobs"
    # full_run is another held representation, not a replacement for output.
    # Generic discovery also covers future producers' nested data packs.
    for folder in sorted(jobs.glob("*")):
        if not folder.is_dir() or folder.name == "claim-kit":
            continue
        output = folder / "output"
        files.update(output.glob("FRAGMENTS*.jsonl"))
        if (output / "SOURCES.jsonl").is_file():
            files.add(output / "SOURCES.jsonl")
        data = folder / "data"
        if data.is_dir():
            files.update(data.rglob("FRAGMENTS*.jsonl"))
            files.update(data.rglob("SOURCES.jsonl"))
        prov = data / "PROVENANCE.json"
        if prov.is_file():
            declarations = _json(prov, warnings)
            origin = prov.relative_to(repo).as_posix()
            collector.walk_texts(declarations, folder, origin, provenance=True)
            files.update(_declared_files(declarations, repo, folder))
    for path in sorted(files):
        origin = path.relative_to(repo).as_posix()
        for record in _jsonl(path, warnings):
            if path.name.startswith("FRAGMENTS") or record.get("kind"):
                collector.fragment(record, path.parent, origin)
            else:
                collector.walk_texts(record, path.parent, origin)
    # Keep actual catalog dates, not a publication date recast as filing date.
    catalog_dates = {}
    for path in sorted(jobs.glob("*/output/CATALOG_INDEX.csv")):
        for row in _csv(path):
            iid = collector.identity(row.get("id") or row.get("instrument_id"))
            if iid:
                catalog_dates[iid] = {k: row[k] for k in ("signing_date", "filing_date") if row.get(k)}
    for path in sorted(jobs.glob("*/output/EDGES.csv")):
        for row in _csv(path):
            collector.add_pair(row.get("target_id"), row, path.relative_to(repo).as_posix())
    for path in sorted((jobs / "claim-drafts" / "output").glob("DRAFT_CLAIMS*.jsonl")):
        origin = path.relative_to(repo).as_posix()
        for row in _jsonl(path, warnings):
            iid = collector.identity(row.get("instrument_id"))
            if not iid:
                continue
            claim = row.get("claim") if isinstance(row.get("claim"), dict) else {}
            draft = row.get("_draft") if isinstance(row.get("_draft"), dict) else {}
            drafts[iid] = {"claim": claim, "_draft": draft}
            explicit = draft.get("provisional_status")
            if not authoritative_statuses and explicit in {"yes", "no"}:
                statuses[iid] = explicit
            elif explicit in {"yes", "no"} and iid in statuses and explicit != statuses[iid]:
                warnings.append(f"{iid}: draft status {explicit} differs from authoritative {statuses[iid]}")
            proposals = draft.get("proposals") or {}
            for candidate in proposals.get("original_representation") or []:
                if not isinstance(candidate, dict):
                    continue
                producer = candidate.get("from") or ""
                base = None
                if "@" in producer:
                    base = _path(repo, repo, producer.split("@", 1)[1])
                elif producer.startswith("jobs/"):
                    base = _path(repo, repo, producer)
                if base:
                    collector.walk_texts(candidate, base, origin, iid=iid, original_context=True)
            # Draft clause pointers name their producing output folder.
            clause_info = draft.get("clause_inventory_info") or {}
            producer = clause_info.get("from") or ""
            base = _path(repo, repo, producer.split("@", 1)[-1]) if producer else None
            if base:
                clauses = draft.get("clauses") or []
                claim_clauses = {c.get("scope_id"): c for c in claim.get("operative_clauses") or []
                                 if isinstance(c, dict)}
                for clause in clauses:
                    if not isinstance(clause, dict):
                        continue
                    joined = dict(clause)
                    joined["original_source"] = claim_clauses.get(clause.get("scope_id"), {}).get("original_source")
                    collector.walk_texts(joined, base, origin, iid=iid,
                                         grade=clause_info.get("source_grade"))
            for key in ("whole_order_end", "later_events"):
                for event in proposals.get(key) or []:
                    collector.add_pair(iid, event, origin)
            for clause in draft.get("clauses") or []:
                if not isinstance(clause, dict):
                    continue
                for related in clause.get("related_orders") or []:
                    if isinstance(related, dict) and related.get("role") == "target_candidate":
                        collector.add_pair(related.get("instrument_id"), {
                            "actor": iid, "scope_id": clause.get("scope_id"),
                            "kind": clause.get("clause_kind"), "related_order": related}, origin)
            for candidate in proposals.get("current_predicate") or []:
                collector.current[iid].append(candidate)
    for path in sorted(jobs.glob("*/output/SUMMARY.json")):
        summary = _json(path, warnings)
        if not isinstance(summary, dict):
            continue
        for record in summary.get("machine_searches") or []:
            if isinstance(record, dict) and isinstance(record.get("search_id"), str):
                sid = record["search_id"]
                if sid in searches and searches[sid] != record:
                    warnings.append(f"{sid}: conflicting machine search declarations; first retained")
                else:
                    searches[sid] = record
    for record in collector.texts:
        dates = catalog_dates.get(record["instrument_id"], {})
        for key in ("signing_date", "filing_date"):
            record[key] = record.get(key) or dates.get(key)
    collector.texts.sort(key=lambda r: (r["instrument_id"], r["text_path"], _canonical(r)))
    collector.pairs.sort(key=lambda r: (r["target_id"], r["actor_id"], _canonical(r)))
    return {"universe": universe, "statuses": statuses, "drafts": drafts,
            "texts": collector.texts, "pairs": collector.pairs,
            "current_law": dict(collector.current), "machine_searches": searches,
            "status_histories": collector.status_histories,
            "factual_obligations": dict(collector.factual_obligations),
            "warnings": sorted(set(warnings))}
