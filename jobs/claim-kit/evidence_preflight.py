"""Bounded checks on evidence already in a dossier; no acquisition or adjudication.

These checks expose preparation work before a producer is assigned a case. A
clean screen is not complete evidence, authentication, or a legal conclusion.
Source-custody and full claim checks still belong to the actual claim checker.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

from excavate import _extent


HEX64 = re.compile(r"[0-9a-f]{64}", re.I)
# Reading an OCR heading here never changes the underlying text or its offsets.
SECTION = re.compile(r"(?im)^[ \t]*(?:S[ \t]*e[ \t]*c(?:[ \t]*t[ \t]*i[ \t]*o[ \t]*n)?[ \t]*\.?)[ \t]+([0-9]+)[ \t]*[.)]")
UNNUMBERED_ORDER = re.compile(r"(?im)^[ \t]*EXECUTIVE[ \t]+ORDER[ \t]*$")
NUMBERED_ORDER = re.compile(r"(?im)^[ \t]*Executive[ \t]+Order[ \t]+(?:No\.?[ \t]+)?([0-9]+[A-Z]?)(?![\w])")
INSTRUMENT = re.compile(r"(?m)^Instrument:\s*(EO:[^\s]+)")
REPORT_SUNSET = re.compile(r"\b(?:shall\s+)?term\s*inate\b[^.;]{0,180}\b(?:after|upon)\b[^.;]{0,100}\breport\b", re.I | re.S)


def inspect(dossier, repo):
    """Return deterministic tasks and exact held-text receipts for one dossier.

Only supplied evidence paths are read, once each. Alternate text comparisons
require the same declared source-byte hash and target identity. They flag a
possible omission; they never select a replacement or declare either complete.
    """
    repo = Path(repo).resolve()
    iid = dossier['instrument_id']
    evidence = dossier.get('evidence', {})
    tasks, seen, files, receipts = [], set(), {}, {}

    def add(kind, key, reason, state='research_required', **detail):
        marker = (kind, key)
        if marker in seen:
            return
        seen.add(marker)
        tasks.append({'kind': kind, 'shared_key': key, 'reason': reason,
                      'availability': state, **detail})

    def load(source, eid):
        rel = source.get('text_path')
        if not isinstance(rel, str) or not rel:
            add('citable_text_pointer', eid, 'Evidence has no held text path; a citation is not a citable text.', 'citation_or_pointer_only')
            return None
        if rel not in files:
            try:
                path = (repo / rel).resolve()
                if not path.is_relative_to(repo):
                    raise ValueError('path outside repository')
                if path.stat().st_size > 32_000_000:
                    raise ValueError('source exceeds bounded text check; use explicit full-source review')
                raw = path.read_bytes()
                files[rel] = (hashlib.sha256(raw).hexdigest(), raw.decode('utf-8'))
            except (OSError, ValueError, UnicodeError) as exc:
                files[rel] = None
                add('held_text_unavailable', rel, str(exc), 'absent_or_unreadable')
        loaded = files[rel]
        if loaded is None:
            return None
        expected = source.get('text_sha256')
        if not isinstance(expected, str) or not HEX64.fullmatch(expected) or loaded[0] != expected.lower():
            add('held_text_fixity', rel, 'Held text bytes do not match the declared SHA-256, or the declaration is absent.', 'hash_not_verified')
            return None
        raw_sha = source.get('sha256') or source.get('local_file_sha256')
        if not isinstance(raw_sha, str) or not HEX64.fullmatch(raw_sha):
            add('source_byte_hash', rel, 'Source-byte SHA-256 is missing or malformed; text fixity alone is not custody.', 'custody_not_established')
        receipts[rel] = {'text_sha256': loaded[0], 'characters': len(loaded[1]),
                         'source_sha256': raw_sha, 'raw_custody': 'requires_actual_claim_checker'}
        return loaded[1]

    verified = {}
    for eid, item in sorted(evidence.items()):
        if not isinstance(item, dict):
            continue
        source = item.get('source') or item.get('actor_source')
        quote = item.get('text', item.get('provision_text'))
        if not isinstance(source, dict) or not isinstance(quote, str):
            continue
        body = load(source, eid)
        if body is None:
            continue
        a = item.get('char_start', source.get('char_start'))
        b = item.get('char_end', source.get('char_end'))
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(body) or body[a:b] != quote:
            add('citable_span', eid, 'Quoted text is not an exact nonempty span of the held representation.', 'span_not_verified')
            continue
        verified[eid] = (item, source, body)

    original_id = dossier.get('original_source_id')
    original = verified.get(original_id)
    if original:
        item, source, body = original
        marker = INSTRUMENT.search(body)
        if marker and marker[1] != iid:
            add('original_identity', original_id, 'Held representation explicitly identifies a different order.', 'wrong_order', observed_identity=marker[1])
        headers = list(UNNUMBERED_ORDER.finditer(body))
        own_header = next((m for m in NUMBERED_ORDER.finditer(body) if 'EO:' + m[1].upper() == iid), None)
        if len(headers) > 1 and own_header is None:
            add('original_boundary', original_id,
                'Multiple unnumbered Executive Order headings occur on the held pages. Metadata identity does not establish which document supplies the inventory.',
                'neighboring_documents_require_page_review', heading_offsets=[m.start() for m in headers])
        ranges = [(c.get('char_start'), c.get('char_end')) for c in dossier.get('clauses', [])]
        uncovered = []
        body_start, body_end = _extent(iid, body)
        for match in SECTION.finditer(body, body_start, body_end):
            pos = match.start()
            if not any(type(a) is int and type(b) is int and a <= pos < b for a, b in ranges):
                uncovered.append({'section': match[1], 'char_start': pos})
        if uncovered:
            add('inventory_section_coverage', original_id, 'Numbered section headings in the selected original lie outside the proposed inventory.',
                'inventory_incomplete', uncovered_sections=uncovered)
        original_sections = {m[1] for m in SECTION.finditer(body, body_start, body_end)}
        checked = set()
        for _, alternate, other in verified.values():
            rel = alternate.get('text_path')
            if rel == source.get('text_path') or rel in checked:
                continue
            checked.add(rel)
            if alternate.get('sha256') != source.get('sha256'):
                continue
            explicit = INSTRUMENT.search(other)
            if not explicit or explicit[1] != iid:
                continue
            other_start, other_end = _extent(iid, other)
            extra = sorted({m[1] for m in SECTION.finditer(other, other_start, other_end)} - original_sections, key=int)
            if extra:
                add('alternate_text_section_coverage', original_id + '|' + rel,
                    'Another declared representation of the same source bytes contains numbered sections absent from the selected text. Inspect the source pages and correct the selected representation before inventory approval.',
                    'possible_truncation', alternate_text_path=rel, additional_sections=extra)

    for eid in dossier.get('actor_provisions', []):
        entry = verified.get(eid)
        if not entry:
            continue
        item, source, body = entry
        first = next(SECTION.finditer(body), None)
        if first and item.get('char_end', len(body)) <= first.end():
            add('acting_provision_scope', eid,
                'The located ACT quote ends before the acting instrument\'s numbered provisions. Read and cite the applicable operative provision; a heading or introductory amendment formula does not supply the later sections.',
                'header_or_preamble_only', first_section_offset=first.start())

    # Conditional sunsets require event research even if a report-deadline rule
    # exists. This is a scope warning, never an inference that the event occurred.
    for eid, (item, source, body) in verified.items():
        if item.get('actor_id') not in (None, iid) or (eid.startswith('ACT:') or eid.startswith('ACTOR_TEXT:')):
            continue
        for match in REPORT_SUNSET.finditer(item.get('text', '')):
            add('conditional_report_sunset', iid,
                'Express termination on/after a report is not merely a reporting deadline. Establish the triggering event and clause scope; do not apply the deadline ruling as an ending waiver.',
                'substantive_event_unresolved', evidence_id=eid, quote=match[0],
                owner_rule='research/readiness/owner_rulings/2026-10-21-report-deadline.md')

    return {'tasks': tasks, 'held_text_receipts': receipts,
            'custody_validation': 'required_from_actual_claim_checker',
            'notice': 'Diagnostic only: no source selected or authenticated, no inventory approved, no legal outcome inferred.'}
