import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import sys
import subprocess
import os
from unittest.mock import patch
import page_check as M


class Checks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        folder = self.root / 'jobs/ofr-compilations/output'
        folder.mkdir(parents=True)
        (folder / 'text.txt').write_bytes(b'held text')
        data = dict(sha256='a'*64, url='https://example.gov/book', page_or_item='p. 12',
                    text_path='text.txt', text_sha256=hashlib.sha256(b'held text').hexdigest(),
                    grade='official_printing', needs_page_check=True, location_verified=False)
        self.source = dict(instrument_id='EO:1', kind='original_representation', data=data,
                           grade='official_printing', acceptable_as_original=False)
        self.fragment = folder / 'FRAGMENTS.jsonl'
        self.fragment.write_text(json.dumps(self.source)+'\n', encoding='utf-8')
        target = dict(data)
        target = {key: target[key] for key in ('sha256', 'url', 'page_or_item', 'text_path', 'text_sha256')}
        target.update(fragment_path='jobs/ofr-compilations/output/FRAGMENTS.jsonl', fragment_sha256=M.digest(self.source))
        (folder / 'page.png').write_bytes(b'page image fixture')
        target['page_images'] = [dict(url='https://example.gov/page.png', page_or_item='p. 12',
            source_url=data['url'],
            path='jobs/ofr-compilations/output/page.png',
            sha256=hashlib.sha256(b'page image fixture').hexdigest(), provenance='official_government_printing', cited_scope=data['page_or_item'])]
        self.record = dict(schema='montfaucon-page-check/v1', instrument_id='EO:1', lane='official',
                           final='pass', target=target, reviews=[])
        for context in ('one', 'two'):
            review = dict(context_id=context, reviewer='model', verdict='pass', target_sha256=M.digest(target))
            review.update({key:'observed' for key in ('evidence','number_seen','date_seen','signature_seen','first_words','last_words')})
            review.update({key:True for key in ('identity_confirmed','complete_start_and_closing',
                                              'cited_pages_confirmed','wording_compared',
                                              'image_source_and_page_confirmed')})
            review['substantive_differences'] = []
            self.record['reviews'].append(review)

    def test_pass_preserves_grade_and_source(self):
        before = self.fragment.read_bytes()
        lane, derived = M.validate(self.root, self.record)
        self.assertEqual(lane, 'official')
        self.assertEqual(derived['grade'], self.source['grade'])
        self.assertFalse(derived['data']['location_verified'])
        self.assertFalse(derived['data']['needs_page_check'])
        self.assertEqual(before, self.fragment.read_bytes())

    def test_stale_pins(self):
        for key in ('sha256', 'page_or_item', 'url', 'text_sha256', 'text_path', 'fragment_sha256'):
            with self.subTest(key=key):
                record = copy.deepcopy(self.record)
                record['target'][key] += 'changed'
                with self.assertRaises(ValueError):
                    M.validate(self.root, record)
        (self.fragment.parent / 'text.txt').write_bytes(b'changed text')
        with self.assertRaises(ValueError):
            M.validate(self.root, self.record)

    def test_fail_unsure_independence_and_lane(self):
        for field, value in [('final','fail'), ('final','unsure'), ('lane','replica')]:
            record = copy.deepcopy(self.record)
            record[field] = value
            with self.assertRaises(ValueError):
                M.validate(self.root, record)
        self.record['reviews'][1]['context_id'] = 'one'
        with self.assertRaises(ValueError):
            M.validate(self.root, self.record)

    def test_lead_grades_and_image_bytes_rejected(self):
        for grade in ('csc_report_lead', 'official_printing_lead', 'mirror_transcription'):
            source = copy.deepcopy(self.source)
            source['grade'] = source['data']['grade'] = grade
            self.fragment.write_text(json.dumps(source)+'\n', encoding='utf-8')
            record = copy.deepcopy(self.record)
            record['target']['fragment_sha256'] = M.digest(source)
            with self.assertRaises(ValueError):
                M.validate(self.root, record)
        self.fragment.write_text(json.dumps(self.source)+'\n', encoding='utf-8')
        (self.fragment.parent / 'page.png').write_bytes(b'changed image')
        with self.assertRaises(ValueError):
            M.validate(self.root, self.record)

    def test_duplicates_and_live_revalidation(self):
        records = self.root / 'research/montfaucon/CHECKS.jsonl'
        records.parent.mkdir(parents=True)
        records.write_text(json.dumps(self.record)+'\n', encoding='utf-8')
        out, _ = M.assemble(self.root)
        fragment = out['official'][0]
        self.assertTrue(M.validated_output(self.root, fragment, 'official'))
        negative = dict(self.record, final='fail')
        records.write_text(json.dumps(self.record)+'\n'+json.dumps(negative)+'\n', encoding='utf-8')
        self.assertEqual(M.assemble(self.root)[0]['official'], [])
        self.assertFalse(M.validated_output(self.root, fragment, 'official'))

    def test_tracker_rejects_stale_generated_output(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'readiness-tracker'))
        import tracker
        records = self.root / 'research/montfaucon/CHECKS.jsonl'
        records.parent.mkdir(parents=True)
        records.write_text(json.dumps(self.record)+'\n', encoding='utf-8')
        fragment = M.assemble(self.root)[0]['official'][0]
        output = self.root / 'jobs/montfaucon-page-check/output/FRAGMENTS_OFFICIAL.jsonl'
        output.parent.mkdir(parents=True)
        output.write_text(json.dumps(fragment)+'\n', encoding='utf-8')
        jobs, _ = tracker.load_job_outputs(str(self.root))
        self.assertTrue(any(d.get('montfaucon_page_check') for d in jobs['official']['EO:1']))
        (self.fragment.parent / 'page.png').write_bytes(b'changed page image')
        jobs, problems = tracker.load_job_outputs(str(self.root))
        self.assertFalse(any(d.get('montfaucon_page_check') for d in jobs['official']['EO:1']))
        self.assertIn('INVALID_MONTFAUCON_OFFICIAL_FRAGMENT', problems)

    def test_legacy_official_only_exact_route(self):
        for value in (self.source, self.source['data']):
            del value['grade']
        self.source['data']['route'] = M.LEGACY_OFFICIAL['ofr-compilations']
        del self.source['data']['text_sha256']
        self.fragment.write_text(json.dumps(self.source)+'\n', encoding='utf-8')
        self.record['target']['fragment_sha256'] = M.digest(self.source)
        for review in self.record['reviews']:
            review['target_sha256'] = M.digest(self.record['target'])
        self.assertEqual(M.validate(self.root, self.record)[1]['grade'], 'official_printing')
        self.source['data']['route'] = 'official/unqualified'
        self.fragment.write_text(json.dumps(self.source)+'\n', encoding='utf-8')
        self.record['target']['fragment_sha256'] = M.digest(self.source)
        with self.assertRaises(ValueError):
            M.validate(self.root, self.record)

    def test_replica_separate_lane(self):
        folder = self.root / 'jobs/photius-replica-check/output'
        folder.mkdir(parents=True)
        for name in ('text.txt', 'page.png'):
            (folder/name).write_bytes((self.fragment.parent/name).read_bytes())
        self.source['grade'] = self.source['data']['grade'] = 'archival_replica_checked'
        (folder/'FRAGMENTS.jsonl').write_text(json.dumps(self.source)+'\n', encoding='utf-8')
        target = self.record['target']
        target['fragment_path'] = 'jobs/photius-replica-check/output/FRAGMENTS.jsonl'
        target['fragment_sha256'] = M.digest(self.source)
        target['page_images'][0]['path'] = 'jobs/photius-replica-check/output/page.png'
        target['page_images'][0]['provenance'] = 'proquest_replica'
        self.record['lane'] = 'replica'
        for review in self.record['reviews']:
            review['target_sha256'] = M.digest(target)
        lane, fragment = M.validate(self.root, self.record)
        self.assertEqual(lane, 'replica')
        self.assertEqual(fragment['grade'], 'archival_replica_checked')
        self.source['grade'] = self.source['data']['grade'] = 'archival_replica_check_failed_or_pending'
        (folder/'FRAGMENTS.jsonl').write_text(json.dumps(self.source)+'\n', encoding='utf-8')
        target['fragment_sha256'] = M.digest(self.source)
        self.record['adjudication'] = 'new_independent_page_check'
        for review in self.record['reviews']:
            review['target_sha256'] = M.digest(target)
        self.assertEqual(M.validate(self.root, self.record)[1]['grade'], 'archival_replica_checked')
        self.assertEqual(self.source['grade'], 'archival_replica_check_failed_or_pending')

    def test_negative_outcomes_and_batch_file_not_ingested(self):
        directory = self.root / 'research/montfaucon'
        directory.mkdir(parents=True)
        (directory / 'BATCHES.jsonl').write_text('not a check or even JSON', encoding='utf-8')
        for verdict in ('fail', 'unsure'):
            record = copy.deepcopy(self.record)
            record['final'] = record['reviews'][0]['verdict'] = verdict
            record['reviews'][1]['verdict'] = verdict
            del record['target']['page_images']
            for review in record['reviews']:
                review['target_sha256'] = M.digest(record['target'])
            (directory / 'CHECKS.jsonl').write_text(json.dumps(record)+'\n', encoding='utf-8')
            outcomes = []
            lanes, rejected = M.assemble(self.root, outcomes)
            self.assertEqual(lanes, {'official': [], 'replica': []})
            self.assertEqual(rejected, [])
            self.assertEqual(outcomes[0]['final'], verdict)
        output = self.root / 'result'
        run = subprocess.run([sys.executable, str(Path(__file__).with_name('job.py'))],
            env={**os.environ, 'REPO_ROOT': str(self.root), 'OUTPUT_DIR': str(output)},
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual((output/'FRAGMENTS_OFFICIAL.jsonl').read_text(), '')
        self.assertEqual(json.loads((output/'REJECTIONS.json').read_text()), [])
        self.assertEqual(json.loads((output/'OUTCOMES.json').read_text())[0]['final'], 'unsure')

    def test_unhashed_lead_retains_failed_page_and_blocked_missing_text_without_credit(self):
        folder = self.root / 'jobs/photius-free-printings/output'
        folder.mkdir(parents=True)
        source = dict(instrument_id='EO:1419', kind='original_representation',
            grade='official_printing_lead', data=dict(
                route='free/internet_archive_official_publication', sha256='',
                url='https://archive.org/details/panama/page/n121',
                page_or_item='GPO Panama volume, leaf 121',
                grade='official_printing_lead', needs_page_check=True))
        fragment = folder / 'FRAGMENTS.jsonl'
        fragment.write_text(json.dumps(source)+'\n', encoding='utf-8')
        image = folder / 'page.png'
        image.write_bytes(b'wrong cited page image')
        pdf_url = 'https://archive.org/download/panama/panama.pdf'
        target = dict(fragment_path='jobs/photius-free-printings/output/FRAGMENTS.jsonl',
            fragment_sha256=M.digest(source), sha256='', url=source['data']['url'],
            page_or_item=source['data']['page_or_item'], text_path=None, text_sha256=None,
            page_images=[dict(path='jobs/photius-free-printings/output/page.png',
                sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                url=pdf_url+'#page=122', source_url=source['data']['url'],
                page_or_item='PDF page 122', cited_scope=source['data']['page_or_item'],
                provenance='official_government_printing')])
        record = dict(schema='montfaucon-page-check/v1', instrument_id='EO:1419',
            lane='official', final='fail', target=target,
            missing=dict(item='immutable held original text', reason='source fragment names no held text'),
            inspection_source=dict(url=pdf_url, sha256='b'*64), reviews=[])
        for context in ('first', 'second'):
            record['reviews'].append(dict(context_id=context, reviewer='model', verdict='fail',
                target_sha256=M.digest(target), evidence='the cited image is a different order',
                number_seen='not on cited page', date_seen='not on cited page',
                signature_seen='not on cited page', first_words='different order',
                last_words='different order'))
        self.assertEqual(M.validate(self.root, record), ('official', None))
        blocked = copy.deepcopy(record)
        blocked['final'] = 'blocked'
        for review in blocked['reviews']:
            review['verdict'] = 'blocked'
        self.assertEqual(M.validate(self.root, blocked), ('official', None))
        checks = self.root / 'research/montfaucon/CHECKS.jsonl'
        checks.parent.mkdir(parents=True)
        checks.write_text(json.dumps(blocked)+'\n', encoding='utf-8')
        outcomes = []
        lanes, rejected = M.assemble(self.root, outcomes)
        self.assertEqual((lanes, rejected, outcomes[0]['final']),
                         ({'official': [], 'replica': []}, [], 'blocked'))
        output = self.root / 'negative-output'
        run = subprocess.run([sys.executable, str(Path(__file__).with_name('job.py'))],
            env={**os.environ, 'REPO_ROOT': str(self.root), 'OUTPUT_DIR': str(output)},
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual((output/'FRAGMENTS_OFFICIAL.jsonl').read_text(), '')
        self.assertEqual(json.loads((output/'OUTCOMES.json').read_text())[0]['final'], 'blocked')
        for change in ('missing', 'image', 'inspection', 'fragment', 'pass'):
            with self.subTest(change=change):
                bad = copy.deepcopy(record)
                if change == 'missing':
                    del bad['missing']
                elif change == 'image':
                    bad['target']['page_images'] = []
                elif change == 'inspection':
                    bad['inspection_source']['sha256'] = 'not-a-sha'
                elif change == 'fragment':
                    bad['target']['fragment_sha256'] = 'a'*64
                else:
                    bad['final'] = 'pass'
                    for review in bad['reviews']:
                        review.update(verdict='pass', identity_confirmed=True,
                            complete_start_and_closing=True, cited_pages_confirmed=True,
                            wording_compared=True, image_source_and_page_confirmed=True,
                            substantive_differences=[])
                with self.assertRaises(ValueError):
                    M.validate(self.root, bad)

    def test_pass_requires_explicit_checks_and_no_differences(self):
        for field in ('identity_confirmed', 'complete_start_and_closing', 'cited_pages_confirmed', 'wording_compared', 'image_source_and_page_confirmed'):
            record = copy.deepcopy(self.record)
            record['reviews'][0][field] = False
            with self.assertRaises(ValueError):
                M.validate(self.root, record)
        self.record['reviews'][0]['substantive_differences'] = ['omitted operative clause']
        with self.assertRaises(ValueError):
            M.validate(self.root, self.record)

    def test_disagreement_and_unrelated_image_rejected(self):
        record = copy.deepcopy(self.record)
        record['reviews'][0]['verdict'] = record['final'] = 'fail'
        with self.assertRaisesRegex(ValueError, 'disagreement'):
            M.validate(self.root, record)
        for field in ('source_url', 'cited_scope'):
            record = copy.deepcopy(self.record)
            record['target']['page_images'][0][field] = 'unrelated'
            with self.assertRaises(ValueError):
                M.validate(self.root, record)

    def test_all_page_images_pinned(self):
        target = self.record['target']
        second = copy.deepcopy(target['page_images'][0])
        second['path'] = 'jobs/ofr-compilations/output/page2.png'
        second['page_or_item'] = 'p. 13'
        second['url'] = 'https://example.gov/page2.png'
        (self.fragment.parent/'page2.png').write_bytes(b'page two fixture')
        second['sha256'] = hashlib.sha256(b'page two fixture').hexdigest()
        target['page_images'].append(second)
        for review in self.record['reviews']:
            review['target_sha256'] = M.digest(target)
        self.assertEqual(M.validate(self.root, self.record)[0], 'official')
        (self.fragment.parent/'page2.png').write_bytes(b'changed second page')
        with self.assertRaises(ValueError):
            M.validate(self.root, self.record)

    def test_source_index_once_per_assembly_and_never_cross_run(self):
        second_source = copy.deepcopy(self.source)
        second_source['instrument_id'] = 'EO:2'
        second = copy.deepcopy(self.record)
        second['instrument_id'] = 'EO:2'
        second['target']['fragment_sha256'] = M.digest(second_source)
        for review in second['reviews']:
            review['target_sha256'] = M.digest(second['target'])
        self.fragment.write_text(json.dumps(self.source)+'\n'+json.dumps(second_source)+'\n', encoding='utf-8')
        directory = self.root / 'research/montfaucon'
        directory.mkdir(parents=True)
        (directory/'CHECKS.jsonl').write_text(json.dumps(self.record)+'\n'+json.dumps(second)+'\n', encoding='utf-8')
        original = Path.read_text
        calls = []
        def reading(path, *args, **kwargs):
            if path == self.fragment:
                calls.append(path)
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', reading):
            self.assertEqual(len(M.assemble(self.root)[0]['official']), 2)
            self.assertEqual(len(calls), 1)
            self.fragment.write_text('', encoding='utf-8')
            self.assertEqual(M.assemble(self.root)[0]['official'], [])
            self.assertEqual(len(calls), 2)

    def test_disagreement_third_context_adjudicates_exact_target(self):
        self.record['reviews'][0]['verdict'] = 'fail'
        third = copy.deepcopy(self.record['reviews'][1])
        third['context_id'] = 'third-independent-context'
        self.record['adjudicator'] = third
        lane, fragment = M.validate(self.root, self.record)
        self.assertEqual(lane, 'official')
        self.assertEqual(fragment['data']['montfaucon_page_check']['record']['reviews'][0]['verdict'], 'fail')
        for invalid in ('context_id', 'target_sha256'):
            record = copy.deepcopy(self.record)
            record['adjudicator'][invalid] = ('one' if invalid == 'context_id' else 'changed')
            with self.assertRaises(ValueError):
                M.validate(self.root, record)
        self.record['final'] = 'fail'
        with self.assertRaises(ValueError):
            M.validate(self.root, self.record)

    def test_different_source_same_order_can_coexist(self):
        negative_source = copy.deepcopy(self.source)
        negative_source['data']['sha256'] = 'b'*64
        negative = copy.deepcopy(self.record)
        negative['final'] = 'fail'
        negative['target']['sha256'] = 'b'*64
        negative['target']['fragment_sha256'] = M.digest(negative_source)
        for review in negative['reviews']:
            review['verdict'] = 'fail'
            review['target_sha256'] = M.digest(negative['target'])
        self.fragment.write_text(json.dumps(self.source)+'\n'+json.dumps(negative_source)+'\n', encoding='utf-8')
        directory = self.root / 'research/montfaucon'
        directory.mkdir(parents=True)
        (directory/'CHECKS.jsonl').write_text(json.dumps(self.record)+'\n'+json.dumps(negative)+'\n', encoding='utf-8')
        outcomes = []
        lanes, rejected = M.assemble(self.root, outcomes)
        self.assertEqual(len(lanes['official']), 1)
        self.assertEqual(rejected, [])
        self.assertEqual({row['final'] for row in outcomes}, {'pass', 'fail'})

    def test_extra_fr_routes_and_qualified_gpo(self):
        for job, route, grade in (
                ('fr-originals', 'official/govinfo_link_fr', None),
                ('fr-originals', 'official/ofr_index_pdf_url', None),
                ('tischendorf-originals', 'official/ia_fulltext', 'machine_read_government_printed_copy')):
            folder = self.root / 'jobs' / job / 'output'
            folder.mkdir(parents=True, exist_ok=True)
            source = copy.deepcopy(self.source)
            source['data']['route'] = route
            source['data']['match'] = {'source_kind': 'government-printed compilation of executive orders'}
            if grade:
                source['grade'] = source['data']['grade'] = grade
                del source['data']['grade']  # Actual Tischendorf legacy shape.
            else:
                del source['grade']
                del source['data']['grade']
            (folder/'FRAGMENTS.jsonl').write_text(json.dumps(source)+'\n', encoding='utf-8')
            for name in ('text.txt', 'page.png'):
                (folder/name).write_bytes((self.fragment.parent/name).read_bytes())
            record = copy.deepcopy(self.record)
            target = record['target']
            target['fragment_path'] = f'jobs/{job}/output/FRAGMENTS.jsonl'
            target['fragment_sha256'] = M.digest(source)
            target['page_images'][0]['path'] = f'jobs/{job}/output/page.png'
            for review in record['reviews']:
                review['target_sha256'] = M.digest(target)
            self.assertEqual(M.validate(self.root, record)[1]['grade'], 'official_printing')
            if grade:
                source['data']['match']['source_kind'] = 'non-government publication'
                (folder/'FRAGMENTS.jsonl').write_text(json.dumps(source)+'\n', encoding='utf-8')
                target['fragment_sha256'] = M.digest(source)
                with self.assertRaises(ValueError):
                    M.validate(self.root, record)

    def test_tischendorf_govinfo_fr_issue_qualification_is_narrow(self):
        folder = self.root / 'jobs/tischendorf-originals/output'
        folder.mkdir(parents=True, exist_ok=True)
        source = copy.deepcopy(self.source)
        source['grade'] = 'machine_read_government_printed_copy'
        del source['data']['grade']  # Actual Tischendorf legacy shape.
        source['data']['route'] = 'official/fr_issue_by_date'
        source['data']['match'] = {'source_kind': 'govinfo scan of the printed Federal Register daily issue'}
        source['data']['url'] = 'https://www.govinfo.gov/content/pkg/FR-1936-12-22/pdf/FR-1936-12-22.pdf'
        source['data']['page_or_item'] = 'Federal Register 1936-12-22; PDF pages 1-1'
        fragment = folder / 'FRAGMENTS.jsonl'
        for name in ('text.txt', 'page.png'):
            (folder/name).write_bytes((self.fragment.parent/name).read_bytes())
        record = copy.deepcopy(self.record)
        target = record['target']
        target.update(fragment_path='jobs/tischendorf-originals/output/FRAGMENTS.jsonl',
                      url=source['data']['url'], page_or_item=source['data']['page_or_item'])
        target['page_images'][0].update(path='jobs/tischendorf-originals/output/page.png',
                                        source_url=target['url'], cited_scope=target['page_or_item'])

        def run(candidate):
            fragment.write_text(json.dumps(candidate)+'\n', encoding='utf-8')
            target['fragment_sha256'] = M.digest(candidate)
            target['url'] = candidate['data']['url']
            target['page_images'][0]['source_url'] = target['url']
            for item in record['reviews']:
                item['target_sha256'] = M.digest(target)
            return M.validate(self.root, record)

        lane, derived = run(source)
        self.assertEqual(lane, 'official')
        self.assertEqual(derived['grade'], 'official_printing')
        self.assertFalse(derived['data']['location_verified'])
        self.assertEqual(source['grade'], 'machine_read_government_printed_copy')
        for field, value in (
                ('route', 'lead/ia_fulltext'),
                ('url', 'https://example.org/FR-1936-12-22.pdf'),
                ('kind', 'non-government publication'),
                ('grade', 'csc_report_lead')):
            with self.subTest(field=field):
                changed = copy.deepcopy(source)
                if field == 'kind':
                    changed['data']['match']['source_kind'] = value
                elif field == 'grade':
                    changed['grade'] = value
                else:
                    changed['data'][field] = value
                with self.assertRaises(ValueError):
                    run(changed)

    def test_mabillon_body_hash_and_govinfo_qualification_are_narrow(self):
        folder = self.root / 'jobs/mabillon-held-printings/output'
        folder.mkdir(parents=True, exist_ok=True)
        full = b'Mabillon source metadata\n\nheld text'
        body = b'held text'
        (folder / 'text.txt').write_bytes(full)
        (folder / 'page.png').write_bytes((self.fragment.parent / 'page.png').read_bytes())
        source = copy.deepcopy(self.source)
        source['grade'] = 'machine_read_government_printed_copy'
        del source['data']['grade']
        source['data'].update(
            route='held/govinfo_fr',
            match={'source_kind': 'govinfo scan of the printed Federal Register daily issue'},
            url='https://www.govinfo.gov/content/pkg/FR-1936-06-25/pdf/FR-1936-06-25.pdf',
            page_or_item='Federal Register 1936-06-25; PDF pages 1-1',
            text_sha256=hashlib.sha256(body).hexdigest())
        fragment = folder / 'FRAGMENTS.jsonl'
        record = copy.deepcopy(self.record)
        target = record['target']
        target.update(fragment_path='jobs/mabillon-held-printings/output/FRAGMENTS.jsonl',
                      sha256=source['data']['sha256'], url=source['data']['url'],
                      page_or_item=source['data']['page_or_item'],
                      text_sha256=source['data']['text_sha256'],
                      text_hash_scope='body_after_first_blank_line',
                      text_file_sha256=hashlib.sha256(full).hexdigest())
        target['page_images'][0].update(path='jobs/mabillon-held-printings/output/page.png',
                                        source_url=target['url'], cited_scope=target['page_or_item'])

        def run(candidate, checked=record):
            fragment.write_text(json.dumps(candidate) + '\n', encoding='utf-8')
            checked['target']['fragment_sha256'] = M.digest(candidate)
            for review in checked['reviews']:
                review['target_sha256'] = M.digest(checked['target'])
            return M.validate(self.root, checked)

        lane, derived = run(source)
        self.assertEqual(lane, 'official')
        self.assertEqual(derived['grade'], 'official_printing')
        self.assertFalse(derived['data']['location_verified'])
        self.assertEqual(source['grade'], 'machine_read_government_printed_copy')

        negative = copy.deepcopy(record)
        negative['final'] = 'fail'
        for review in negative['reviews']:
            review['verdict'] = 'fail'
        self.assertIsNone(run(source, negative)[1])

        for field, value in (
                ('route', 'held/commons_gpo_volume'),
                ('url', 'https://example.org/FR-1936-06-25.pdf'),
                ('kind', 'non-government publication'),
                ('grade', 'csc_report_lead')):
            with self.subTest(field=field):
                changed = copy.deepcopy(source)
                if field == 'kind':
                    changed['data']['match']['source_kind'] = value
                elif field == 'grade':
                    changed['grade'] = value
                else:
                    changed['data'][field] = value
                with self.assertRaises(ValueError):
                    run(changed)

        for field, value in (
                ('text_hash_scope', 'whole_file'),
                ('text_file_sha256', '0' * 64),
                ('text_sha256', '0' * 64)):
            with self.subTest(field=field):
                changed = copy.deepcopy(record)
                changed['target'][field] = value
                with self.assertRaises(ValueError):
                    run(source, changed)
        (folder / 'text.txt').write_bytes(b'Changed header\n\nheld text')
        with self.assertRaisesRegex(ValueError, 'held text file changed'):
            run(source)
        (folder / 'text.txt').write_bytes(b'header without delimiter')
        with self.assertRaisesRegex(ValueError, 'body delimiter missing'):
            run(source)

    def test_mabillon_passage_alone_still_verifies_header_era_pins(self):
        """Papebroch (2026-11-09): Mabillon now writes the passage alone. A record pinned while the file carried the
        provenance header still validates only if the rebuilt header plus the held bytes is the pinned full file."""
        folder = self.root / 'jobs/mabillon-held-printings/output'
        folder.mkdir(parents=True, exist_ok=True)
        body = b'held text\n\nsecond paragraph'
        (folder / 'page.png').write_bytes((self.fragment.parent / 'page.png').read_bytes())
        source = copy.deepcopy(self.source)
        source['grade'] = 'machine_read_government_printed_copy'
        del source['data']['grade']
        source['data'].update(
            route='held/govinfo_fr',
            match={'source_kind': 'govinfo scan of the printed Federal Register daily issue'},
            url='https://www.govinfo.gov/content/pkg/FR-1936-06-25/pdf/FR-1936-06-25.pdf',
            page_or_item='Federal Register 1936-06-25; PDF pages 1-1',
            text_sha256=hashlib.sha256(body).hexdigest())
        full = M.mabillon_legacy_header(source) + body
        self.assertTrue(full.startswith(b'Instrument: ' + source['instrument_id'].encode() + b'\nSource: https://www.govinfo'))
        fragment = folder / 'FRAGMENTS.jsonl'
        record = copy.deepcopy(self.record)
        target = record['target']
        target.update(fragment_path='jobs/mabillon-held-printings/output/FRAGMENTS.jsonl',
                      sha256=source['data']['sha256'], url=source['data']['url'],
                      page_or_item=source['data']['page_or_item'], text_sha256=source['data']['text_sha256'],
                      text_hash_scope='body_after_first_blank_line', text_file_sha256=hashlib.sha256(full).hexdigest())
        target['page_images'][0].update(path='jobs/mabillon-held-printings/output/page.png',
                                        source_url=target['url'], cited_scope=target['page_or_item'])

        def run(candidate=source, checked=record):
            fragment.write_text(json.dumps(candidate) + '\n', encoding='utf-8')
            checked['target']['fragment_sha256'] = M.digest(candidate)
            for review in checked['reviews']:
                review['target_sha256'] = M.digest(checked['target'])
            return M.validate(self.root, checked)

        (folder / 'text.txt').write_bytes(full)           # the file as it was when the pages were checked
        self.assertEqual(run()[0], 'official')
        (folder / 'text.txt').write_bytes(body)           # the passage alone, as Mabillon now writes it
        self.assertEqual(run()[0], 'official')
        (folder / 'text.txt').write_bytes(body + b' ')    # a changed passage fails both readings
        with self.assertRaises(ValueError):
            run()
        (folder / 'text.txt').write_bytes(body)
        moved = copy.deepcopy(source)                      # the rebuilt header binds the fragment's own fields
        moved['data']['page_or_item'] = 'Federal Register 1936-06-25; PDF pages 2-2'
        changed = copy.deepcopy(record)
        changed['target']['page_or_item'] = moved['data']['page_or_item']
        changed['target']['page_images'][0]['cited_scope'] = moved['data']['page_or_item']
        with self.assertRaisesRegex(ValueError, 'held text file changed'):
            run(moved, changed)


if __name__ == '__main__':
    unittest.main()
