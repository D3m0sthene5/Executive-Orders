#!/usr/bin/env python3
"""Verify explicit blinded cards and their declared source bytes; no legal verdict.

No discovery, registry lookup, dossier comparison, control scoring or network I/O.
The caller supplies the coordinate root and a narrow allowlist of source trees.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import stat
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('blind_verify_assemble', HERE / 'assemble.py')
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
SCHEMA = 'eo-blind-byte-verification/v1'
RAW_KEYS = ('local_path', 'local_file', 'download_path', 'raw_path')
SOURCE_KEYS = ('source', 'original_source', 'original_representation')


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical_sha(value):
    return _sha(json.dumps(value, sort_keys=True, ensure_ascii=False,
                           separators=(',', ':'), allow_nan=False).encode('utf-8'))


def _pairs(pairs):
    value = {}
    for key, child in pairs:
        if key in value:
            raise ValueError('duplicate_json_key')
        value[key] = child
    return value


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('nonfinite_json')
    return result


def _json(text):
    return json.loads(text, object_pairs_hook=_pairs, parse_float=_float,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_json')))


def _inside(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _path(root, name, allowed):
    # Reject traversal even when '..' would resolve back inside the root. Reject
    # Windows spellings on Unix too, so a report has the same portable policy.
    if (not isinstance(name, str) or not name or '\\' in name or '\x00' in name or
            PurePosixPath(name).is_absolute() or PureWindowsPath(name).drive or
            any(part in ('..', '.') for part in name.split('/'))):
        raise ValueError('unsafe_source_path')
    path = root / name
    try:
        resolved = path.resolve(strict=True)
    except RuntimeError as exc:
        raise ValueError('source_symlink_loop') from exc
    if not _inside(resolved, root) or not any(_inside(resolved, p) for p in allowed):
        raise ValueError('source_outside_allowlist')
    # Symlinks are refused outright, including in-root links. This is stricter
    # than assembly and makes the declared source location unambiguous.
    current = root
    for part in Path(name).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('source_symlink')
    if not resolved.is_file():
        raise ValueError('source_not_regular_file')
    return resolved


def _read(root, name, allowed):
    path = _path(root, name, allowed)
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    if os.open in os.supports_dir_fd and hasattr(os, 'O_NOFOLLOW'):
        # Anchor every component to a descriptor: a concurrent parent symlink
        # replacement cannot redirect a source read outside the allowed tree.
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            components = PurePosixPath(name).parts
            for part in components[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                os.close(directory)
                directory = child
            fd = os.open(components[-1], flags | getattr(os, 'O_NONBLOCK', 0), dir_fd=directory)
        finally:
            os.close(directory)
    else:
        fd = os.open(path, flags)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('source_not_regular_file')
        raw = stream.read()
        after = os.fstat(stream.fileno())
    # Reading may update access time without changing the source. Preserve all
    # other identity, ownership, mode, link and content-version observations.
    stamp = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_uid, s.st_gid,
                       s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if stamp(before) != stamp(after) or stamp(_path(root, name, allowed).stat()) != stamp(after):
        raise ValueError('source_changed_during_read')
    return raw


def _references(value, path='$', emit_self=True):
    if isinstance(value, dict):
        if emit_self and 'text_path' in value:
            yield path, value, None
        for key in sorted(value):
            child = value[key]
            label = path + '.' + key
            if key in SOURCE_KEYS or key.endswith('_source'):
                # NORTON witnesses keep text/offsets on the surrounding record;
                # lifecycle source references keep quote/offsets inside source.
                span = value if key == 'source' and any(k in value for k in ('text', 'char_start', 'char_end')) else None
                yield label, child, span
                yield from _references(child, label, emit_self=False)
            elif key in ('sources', 'source_refs'):
                if isinstance(child, list):
                    for n, ref in enumerate(child):
                        yield f'{label}[{n}]', ref, None
                        yield from _references(ref, f'{label}[{n}]', emit_self=False)
                else:
                    yield label, child, None
            else:
                yield from _references(child, label)
    elif isinstance(value, list):
        for n, child in enumerate(value):
            yield from _references(child, f'{path}[{n}]')


def _source(source, root, allowed, require_raw, record_span=None):
    result = {'errors': [], 'unresolved': [], 'text_verified': False,
              'raw_verified': False, 'files': []}
    errors = result['errors']
    if not isinstance(source, dict):
        errors.append('missing_source')
        return result
    if record_span is not None:
        source = dict(source)
        for target, origin in (('quote', 'text'), ('char_start', 'char_start'), ('char_end', 'char_end')):
            if target in source and source[target] != record_span.get(origin):
                errors.append('conflicting_record_span')
            source[target] = record_span.get(origin)
    declared = [k for k in RAW_KEYS if k in source]
    if not declared:
        (errors if require_raw else result['unresolved']).append('raw_path_missing')
    raw_sha = source.get('sha256')
    if not raw_sha and source.get('archival_id'):
        raw_sha = source.get('local_file_sha256')
    raw_pin_present = raw_sha is not None
    if declared or require_raw or raw_pin_present:
        if not isinstance(raw_sha, str) or not A.SHA.fullmatch(raw_sha):
            errors.append('source_sha256')
    # Prevalidate ALL paths before the existing routine is allowed to read any.
    names = [('text_path', source.get('text_path'))] + [(k, source[k]) for k in declared]
    held = {}
    for key, name in names:
        try:
            _path(root, name, allowed)
        except (OSError, ValueError, TypeError):
            errors.append(key + ':unavailable_or_unsafe')
    if any('unavailable_or_unsafe' in e for e in errors):
        return result
    for key, name in names:
        try:
            raw = _read(root, name, allowed)
            held[name] = raw
            if raw.startswith(b'version https://git-lfs.github.com/spec/v1'):
                errors.append('text_lfs_pointer' if key == 'text_path' else 'original_lfs_pointer')
            result['files'].append({'field': key, 'path': name, 'sha256': _sha(raw), 'bytes': len(raw)})
        except (OSError, ValueError, TypeError):
            errors.append(key + ':unavailable_or_changed')
    if any('unavailable_or_changed' in e for e in errors):
        return result
    # Reuse the production exact UTF-8/no-newline-conversion and offset/hash
    # checks. Calling check_claim would inspect nonblind dossiers/registries;
    # this deliberately calls ONLY the exact-byte helper.
    for key in declared:
        if _sha(held[source[key]]) != raw_sha:
            errors.append('original_hash_mismatch')
    native = A._source_errors(source, source.get('quote'), root, 'source', source_reader=held.__getitem__)
    native = [e.removeprefix('source:') for e in native]
    if not require_raw and not declared and not raw_pin_present:
        native = [e for e in native if e != 'source_sha256']
    errors.extend(native)
    # Rehash after the reused routine; a changed source never earns a pass.
    for name, raw in held.items():
        try:
            if _read(root, name, allowed) != raw:
                errors.append('source_changed_during_verification')
        except (OSError, ValueError, TypeError):
            errors.append('source_changed_during_verification')
    text_errors = ('text_', 'quote_', 'source_changed')
    result['text_verified'] = 'conflicting_record_span' not in errors and not any(e.startswith(text_errors) for e in errors)
    result['raw_verified'] = bool(declared) and not any(
        e == 'source_sha256' or e.startswith(('original_', 'source_changed')) for e in errors)
    result['errors'] = sorted(set(errors))
    return result


def _cards(value):
    if isinstance(value, list) and value:
        return value
    if isinstance(value, dict):
        if 'records' in value:
            if not isinstance(value['records'], list) or not value['records']:
                raise ValueError('records_nonempty_list_required')
            return value['records']
        return [value]
    raise ValueError('cards_nonempty_objects_required')


def verify_files(cards, source_root, allowed_source_roots, expected_card_sha256=None):
    """Return a deterministic report; inspect only explicit cards + cited files.

    Source paths are relative to source_root. allowed_source_roots are explicit
    absolute paths or paths relative to source_root, never inferred from cards.
    No filesystem writes are performed. False/unknown is never scientific failure.
    """
    report = {'schema': SCHEMA, 'scope': 'mechanical_bytes_only', 'ok': False,
              'errors': [], 'inputs': [], 'cards': []}
    try:
        root = Path(source_root).resolve(strict=True)
        allowed = tuple(sorted({(root / p).resolve(strict=True) for p in allowed_source_roots}))
        if not root.is_dir() or not allowed or any(not p.is_dir() or not _inside(p, root) for p in allowed):
            raise ValueError('invalid_source_roots')
    except (OSError, ValueError, TypeError, RuntimeError):
        report['errors'].append('invalid_source_roots')
        return report
    if not cards:
        report['errors'].append('explicit_cards_required')
        return report
    if expected_card_sha256 is not None and (
            len(expected_card_sha256) != len(cards) or any(not isinstance(pin, str) or
            not A.SHA.fullmatch(pin) for pin in expected_card_sha256)):
        report['errors'].append('expected_card_hashes_must_match_input_count')
        return report
    for file_index, filename in enumerate(cards):
        entry = {'input_index': file_index, 'errors': []}
        report['inputs'].append(entry)
        try:
            path = Path(filename)
            if path.is_symlink() or not path.is_file():
                raise ValueError('card_not_regular_file')
            parent = path.parent.resolve(strict=True)
            raw = _read(parent, path.name, (parent,))
            entry['sha256'] = _sha(raw)
            entry['bytes'] = len(raw)
            entry['input_pin_checked'] = expected_card_sha256 is not None
            if expected_card_sha256 is not None:
                entry['expected_sha256'] = expected_card_sha256[file_index]
                if entry['sha256'] != entry['expected_sha256']:
                    entry['errors'].append('card_hash_mismatch')
                    continue
            text = raw.decode('utf-8')
            if path.suffix.lower() == '.jsonl':
                parsed = [_json(line) for line in text.splitlines() if line.strip()]
            else:
                parsed = _json(text)
            values = _cards(parsed)
        except (OSError, ValueError, TypeError, UnicodeError, RecursionError, RuntimeError):
            entry['errors'].append('card_unavailable_or_malformed')
            continue
        for card_index, card in enumerate(values):
            item = {'input_index': file_index, 'card_index': card_index, 'errors': [], 'sources': []}
            report['cards'].append(item)
            if not isinstance(card, dict):
                item['errors'].append('card_object_required')
                continue
            try:
                item['card_sha256'] = _canonical_sha(card)
            except (ValueError, UnicodeError, RecursionError):
                item['errors'].append('card_not_canonical_json')
                continue
            payload = card.get('claim', card)
            if not isinstance(payload, dict):
                item['errors'].append('claim_object_required')
                continue
            require_raw = payload.get('schema') == 'eo-lifecycle-claim/v1'
            item['payload_sha256'] = _canonical_sha(payload)
            try:
                references = list(_references(payload))
            except RecursionError:
                item['errors'].append('card_nesting_too_deep')
                continue
            for label, source, span in references:
                result = _source(source, root, allowed, require_raw, span)
                result['locus'] = label
                item['sources'].append(result)
            if not item['sources']:
                item['errors'].append('no_source_references')
            item['text_checks_passed'] = bool(item['sources']) and not item['errors'] and all(
                s['text_verified'] for s in item['sources'])
            item['ok'] = bool(item['sources']) and not item['errors'] and all(
                not s['errors'] and not s['unresolved'] and s['raw_verified'] for s in item['sources'])
    report['ok'] = bool(report['cards']) and not report['errors'] and all(
        not i['errors'] for i in report['inputs']) and all(c.get('ok', False) for c in report['cards'])
    return report


def add_arguments(parser):
    parser.add_argument('--card', required=True, action='append', help='Explicit blinded JSON/JSONL file; repeat, no directories/globs')
    parser.add_argument('--expected-card-sha256', action='append', help='Expected exact file SHA-256, in --card order; if supplied, required for every card')
    parser.add_argument('--source-root', required=True, type=Path, help='Coordinate root for paths already declared in cards')
    parser.add_argument('--allow-source-root', required=True, action='append', help='Narrow source directory under source-root; repeat')


def run(args):
    report = verify_files(args.card, args.source_root, args.allow_source_root, args.expected_card_sha256)
    print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
    return 0 if report['ok'] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    return run(parser.parse_args(argv))


if __name__ == '__main__':
    raise SystemExit(main())
