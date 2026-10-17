"""Verify the full Opus Stage 11 original-image companion against the research manifest.

Run: python verify_opus_media.py COMPLETE_OPUS.zip MEDIA_COMPANION.zip OUTPUT_DIR
Results prove bytes and archive-path associations, NOT legal authenticity,
completeness of the original instrument, or independent human review.
"""
import csv
import hashlib
import json
import sys
import zipfile
from pathlib import Path

MAIN_SHA = '1fbbd45e9a8846a955cbdcaa5bba2b0f138c10c80049c5bb6063197f6ac62d47'
MEDIA_SHA = '5ece42b87164b3d8422e53fba554a28b5f644362cea920b72c7996a8e0b88e9a'
PREFIX = 'OPUS_STAGE11_FINITE_STATUS_DELTA/'
MEDIA_SUFFIXES = ('.pdf', '.png', '.jpg', '.jpeg')


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def stream_digest(stream):
    h = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        h.update(block)
        size += len(block)
    return size, h.hexdigest()


def canonical_name(name):
    name = name.replace('\\', '/').replace('ΓÇô', '–')
    while name.startswith('./'):
        name = name[2:]
    return name


def verify(main_zip, media_zip, expected_missing=496):
    with zipfile.ZipFile(main_zip) as primary, zipfile.ZipFile(media_zip) as companion:
        manifest = json.loads(primary.read(PREFIX + 'MANIFEST.json'))
        accepted = [json.loads(r) for r in primary.read(PREFIX + 'STAGE11_STATUS_RECORDS.jsonl').splitlines() if r.strip()]
        if len(accepted) != 1155:
            raise ValueError('Unexpected primary record count')
        entries = {canonical_name(e['path']): e for e in manifest['files']}
        if len(entries) != len(manifest['files']):
            raise ValueError('Duplicate manifest paths')
        present = {canonical_name(n[len(PREFIX):]) for n in primary.namelist()
                   if n.startswith(PREFIX) and not n.endswith('/') and n != PREFIX + 'MANIFEST.json'}
        missing = sorted(set(entries) - present)
        if len(missing) != expected_missing or any(not x.lower().endswith(MEDIA_SUFFIXES) for x in missing):
            raise ValueError('Unexpected missing original-media footprint: ' + str(len(missing)))
        names = [canonical_name(n) for n in companion.namelist() if not n.endswith('/')]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate canonical media member names')
        underlying = {canonical_name(n): n for n in companion.namelist() if not n.endswith('/')}
        refs = []
        for record in accepted:
            dirname = (record.get('evidence_dir') or '').strip('/')
            if dirname:
                refs.append((record['instrument_id'], canonical_name(dirname) + '/'))
        matches, used = [], set()
        for path in missing:
            possible = [n for n in names if n == path or n.endswith('/' + path)]
            if len(possible) != 1:
                raise ValueError(f'Companion missing or ambiguously mapped for {path}: {len(possible)}')
            member = possible[0]
            if member in used:
                raise ValueError('One companion member matched multiple manifest files')
            used.add(member)
            with companion.open(underlying[member]) as fh:
                length, digest = stream_digest(fh)
            required = entries[path]
            if length != required['bytes'] or digest != required['sha256']:
                raise ValueError(f'Original media checksum/byte count mismatch: {path}')
            affected = sorted(x for x, prefix in refs if path.startswith(prefix))
            matches.append({
                'manifest_path': path, 'companion_member': member,
                'bytes': length, 'sha256': digest,
                'candidate_case_ids_from_directory_only': ' | '.join(affected),
                'source_bytes_verified': 'yes',
                'document_authority_and_page_verified': 'no',
                'human_legal_review': 'no',
            })
        return {
            'schema': 'eo-opus-companion-member-verification/v1',
            'manifest_media_missing_from_main': len(missing),
            'media_members_bytewise_verified': len(matches),
            'companion_unmatched_members': len(names) - len(used),
            'files_with_evidence_path_case_hint': sum(bool(x['candidate_case_ids_from_directory_only']) for x in matches),
            'all_media_hashes_match': True,
            'legal_source_authentication_inferred': False,
            'whole_lifecycle_dossiers_human_certified': 0,
            'qualification': ('Media bytes were independently compared to the accepted Opus manifest. '
                              'A shard-directory prefix is only a possible case association. '
                              'The presence of a PDF or image cannot establish presidential authorship, '
                              'the full operative footprint, the first effective end or saved consequences.'),
        }, matches


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    complete, media, out = map(Path, sys.argv[1:])
    if file_sha(complete) != MAIN_SHA or file_sha(media) != MEDIA_SHA:
        raise SystemExit('LFS payload absent or archive SHA-256 mismatch; do not mark media verified')
    report, rows = verify(complete, media)
    report['complete_archive_sha256'] = MAIN_SHA
    report['media_archive_sha256'] = MEDIA_SHA
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'OPUS_ORIGINAL_MEDIA_MEMBER_MAP.csv').open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    (out / 'OPUS_ORIGINAL_MEDIA_INTEGRITY.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
