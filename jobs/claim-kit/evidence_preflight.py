"""Bounded checks on evidence already in a dossier; no acquisition or adjudication.

These checks expose preparation work before a producer is assigned a case. A
clean screen is not complete evidence, authentication, or a legal conclusion.
Source-custody and full claim checks still belong to the actual claim checker.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

from excavate import _clause_locator, _extent, _page, _sentence_spans, _trailing_extent


HEX64 = re.compile(r"[0-9a-f]{64}", re.I)
# Reading an OCR heading here never changes the underlying text or its offsets.
SECTION = re.compile(r"(?im)^[ \t]*(?:S[ \t]*e[ \t]*c(?:[ \t]*t[ \t]*i[ \t]*o[ \t]*n)?[ \t]*\.?)[ \t]+([0-9]+)[ \t]*[.)]")
UNNUMBERED_ORDER = re.compile(r"(?im)^[ \t]*EXECUTIVE[ \t]+ORDER[ \t]*$")
NUMBERED_ORDER = re.compile(r"(?im)^[ \t]*Executive[ \t]+Order[ \t]+(?:No\.?[ \t]+)?([0-9]+[A-Z]?)(?![\w])")
INSTRUMENT = re.compile(r"(?m)^Instrument:\s*(EO:[^\s]+)")
REPORT_SUNSET = re.compile(r"\b(?:shall\s+)?term\s*inate\b[^.;]{0,180}\b(?:after|upon)\b[^.;]{0,100}\breport\b", re.I | re.S)
# Signals for review, never a semantic clause inventory. Recitals, quotations,
# footnotes and extracted page layout can all affect the meaning of these words.
COMMAND = re.compile(
    r'\bshall\b|\bit\s+is\s+unlawful\b|\bI\s+(?:hereby\s+)?(?:order|direct|extend|establish|revoke|amend)\b|'
    r'\b(?:is|are)\s+(?:hereby\s+)?(?:ordered|directed|authorized|designated|'
    r'established|extended|revoked|amended|withdrawn|reserved)\b|'
    r'\bhereby\s+(?:order|direct|prescribe|establish|designate|authorize|declare|'
    r'extend|revoke|amend|exempt|withdraw|reserve)\b', re.I)


def _identity(number):
    return 'EO:' + re.sub(r'[ \t\-‐–]', '', number).upper().lstrip('0')


def _uncovered(a, b, ranges):
    """Subtract the union of sorted inventory spans; retain raw source offsets."""
    for start, end in ranges:
        if end <= a:
            continue
        if start >= b:
            break
        if a < start:
            yield a, start
        a = max(a, end)
    if a < b:
        yield a, b


def _inventory_ranges(dossier, source, body):
    ranges = []
    for clause in dossier.get('clauses', []):
        if not isinstance(clause, dict):
            continue
        a, b = clause.get('char_start'), clause.get('char_end')
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(body):
            continue
        declared = clause.get('source')
        if declared is not None and (not isinstance(declared, dict) or
                any(declared.get(k) != source.get(k) for k in ('text_path', 'text_sha256'))):
            continue
        if declared:
            raw = declared.get('sha256') or declared.get('local_file_sha256')
            expected_raw = source.get('sha256') or source.get('local_file_sha256')
            if raw and expected_raw and raw != expected_raw:
                continue
        quote = clause.get('text')
        if quote is not None and quote != body[a:b]:
            continue
        ranges.append((a, b))
    return sorted(ranges)


def _command_gaps(iid, body, source, ranges, locator, loc):
    """Review leads from existing segmentation, including suspicious recitals.

    A partition or a machine non-operative label is not semantic proof. Ordinary
    WHEREAS recitals are skipped; authority-led duty language stays a disclosed
    ambiguity. Annexes outside the located body need full-source review.
    """
    segmented = locator.segment(body, loc, iid)
    # Reuse the segmenter's OCR spacing convention for the modal in historical
    # held texts (e.g. EO7952's "sh all"); never rewrite the source itself.
    command = re.compile(r'\b' + locator.fuzzy('shall') + r'\b|' + COMMAND.pattern, re.I)
    candidates = [(c['start'], c['end'], 'clause_candidate') for c in segmented['clauses']
                  if c['clause_kind'] != 'annex_after_signature']
    candidates += [(c['start'], c['end'], 'machine_recital_with_command_signal')
                   for c in segmented['recitals']
                   if not re.match(r'\s*W[ ]?HEREAS\b', body[c['start']:c['end']], re.I)]
    gaps, seen = [], set()
    for start, end, classification in candidates:
        start, end = max(start, loc.body_start), min(end, loc.body_end)
        for pa, pb in locator.paragraphs(body, start, end):
            for sa, sb in _sentence_spans(body[pa:pb]):
                a, b = pa + sa, pa + sb
                text = body[a:b]
                # Ordinary WHEREAS recitals and bare enacting formulas are
                # not commands. Quoted material inside a body candidate may
                # be an amendment payload; expose it with qualified labeling.
                if re.match(r'\s*W[ ]?HEREAS\b', text, re.I) or locator.ENACTING_ONLY.fullmatch(' '.join(text.split())):
                    continue
                signals = list(command.finditer(text))
                if not signals:
                    continue
                formula = locator.OPERATIVE_PHRASE.search(text)
                if len(signals) == 1 and formula and locator.ENACTING_ONLY.fullmatch(' '.join(text[formula.start():].split())):
                    continue
                for ga, gb in _uncovered(a, b, ranges):
                    ga, gb = locator._trim(body, ga, gb)
                    # A skipped title/authority prefix before an otherwise
                    # covered command is not an omitted command. Retain a
                    # truncated command tail even when its modal is covered.
                    if gb <= a + signals[0].start():
                        continue
                    if (ga, gb) in seen or not re.search(r'[A-Za-z]{2}', locator.reading_text(body, ga, gb)):
                        continue
                    seen.add((ga, gb))
                    gaps.append({'char_start': ga, 'char_end': gb, 'text': body[ga:gb],
                                 'context_char_start': a, 'context_char_end': b,
                                 'signals': [m[0] for m in signals],
                                 'classification': 'quoted_command_candidate' if re.match(r'\s*["“]', body[ga:gb]) else classification,
                                 'reason': 'Command-like sentence has substantive text outside submitted inventory; verify its scope against the complete source pages.',
                                 'pdf_page': _page(body, ga, source),
                                 'line': body.count('\n', 0, ga) + 1})
    return gaps, segmented['warnings']


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
        locator = _clause_locator()
        numbered = [m for m in locator.GENERIC_HEADING.finditer(body) if locator._valid_generic(body, m)]
        bare_headers = [h for h in headers if not any(m.start() == h.start() for m in numbered)]
        loc = locator.locate_order(body, iid[3:]) if iid.startswith('EO:') else None
        if loc and loc.heading_style == 'trailing_number' and _trailing_extent(iid, body) is None:
            loc = None  # Preserve the existing intervening-numbered-document refusal.
        observed = [{'observed_identity': _identity(m[1] + (m[2] or m[3] or '')),
                     'char_start': m.start(), 'char_end': m.end(), 'text': m[0]}
                    for m in numbered]
        if loc is None and observed:
            if len(observed) == 1 and observed[0]['observed_identity'] != _identity(iid[3:]) and not bare_headers:
                add('original_identity', original_id,
                    'The only recognized document heading names another order. Confirm document/page boundaries; references and multi-order sources need source examination.',
                    'identity_requires_source_review', observed_identity=observed[0]['observed_identity'],
                    headings=observed, text_path=source['text_path'], text_sha256=source['text_sha256'])
            else:
                add('original_boundary', original_id,
                    'No unambiguous target document was located among the printed headings. Inspect complete source pages before aligning inventory spans.',
                    'neighboring_documents_require_page_review', headings=observed,
                    text_path=source['text_path'], text_sha256=source['text_sha256'])
        elif loc is None and len(headers) <= 1:
            # Attributed body-only / unnumbered text remains eligible for leads,
            # never for machine identity approval. Multiple bare headings remain
            # ambiguous rather than selecting the first neighboring instrument.
            loc = locator.locate_order(body, iid[3:], hint_unnumbered=True) if headers else locator.locate_body_only(body)
        if loc:
            gaps, warnings = _command_gaps(iid, body, source, _inventory_ranges(dossier, source, body), locator, loc)
            if gaps:
                add('inventory_command_coverage', original_id,
                    'Potentially omitted command-like regions in the located document require source/inventory comparison. Machine classifications and complete character coverage do not establish semantic completeness.',
                    'possible_omitted_command', text_path=source['text_path'],
                    text_sha256=source['text_sha256'], source_sha256=source.get('sha256'),
                    document_extent={'char_start': loc.doc_start, 'char_end': loc.doc_end,
                                     'body_start': loc.body_start, 'body_end': loc.body_end,
                                     'heading_style': loc.heading_style},
                    uncovered_regions=gaps, segmentation_warnings=warnings)
        # Preserve the existing heading-only diagnostic contract. The new
        # command diagnostic above additionally checks exact quoted coverage.
        ranges = [(c.get('char_start'), c.get('char_end')) for c in dossier.get('clauses', []) if isinstance(c, dict)]
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
