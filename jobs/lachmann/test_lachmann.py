import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lachmann as L  # noqa: E402

ORDER = {'instrument_id': 'EO:5077', 'number': '5077', 'suffix': '', 'date': '1929-03-07', 'date_kind': 'full',
         'ymd': (1929, 3, 7), 'title': 'Designating Viola B. Pugh to sign land patents'}

GOOD = ("Executive Order 5077. March 7, 1929\n\nMrs. Viola B. Pugh, of the District of Columbia, appointed by the Secretary of the "
        "Interior August 18, 1921, to the position of clerk to sign land patents, is hereby designated as required by law to "
        "sign my name to said patents.\n\nHERBERT HOOVER\n\nThe White House,\nMarch 7, 1929.\n[No. 5077]\n")


def witness(text, producer='p1', sha='a' * 64, tsha='b' * 64, grade='mirror_transcription', requires=True):
    rec = {'instrument_id': 'EO:5077', 'grade': grade, 'sha256': sha, 'text_sha256': tsha, 'text_path': f'jobs/{producer}/t.txt',
           'declaration_path': f'jobs/{producer}/output/FRAGMENTS.jsonl', 'requires_page_check': requires}
    return L.make_witness(rec, text, producer)


class StubIndex:
    def match(self, ref):
        return []


class NumberAndDate(unittest.TestCase):
    def test_number_forms(self):
        for text in ('Executive Order 5077.', 'EXECUTIVE ORDER NO. 5077', '[No. 5077]', 'Order No. 5077', 'Executive Order No 5077'):
            self.assertTrue(L.number_matches(text, '5077'), text)
        self.assertFalse(L.number_matches('Executive Order 5078', '5077'))
        self.assertFalse(L.number_matches('in the year 5077 there', '5077'))

    def test_ocr_noise_only_inside_number_tokens(self):
        self.assertTrue(L.number_matches('Executive Order 5O77', '5077'))
        self.assertTrue(L.number_matches('[No. 5l77]', '5177'))
        self.assertFalse(L.number_matches('Order Is hereby', '15'))   # a word, not a number
        self.assertFalse(L.number_matches('No. Sos', '505'))

    def test_letter_suffix(self):
        self.assertTrue(L.number_matches('Executive Order 6945-A', '6945', 'A'))
        self.assertTrue(L.number_matches('Executive Order 6945 A', '6945', 'A'))
        self.assertFalse(L.number_matches('Executive Order 6945-A', '6945', ''))
        self.assertFalse(L.number_matches('Executive Order 6945', '6945', 'A'))
        self.assertTrue(L.number_matches('No. 8', '8', '-1'))  # numeric register disambiguator is not printed

    def test_date_forms_and_noise(self):
        for text in ('March 7, 1929', 'Mar. 7th, 1929', '7 March 1929', '7th day of March, 1929', '1929-03-07', '3/7/1929', 'March 7,1929',
                     'March 7, l929', 'MARCH  7 ,\n1929'):
            self.assertTrue(L.date_matches(text, (1929, 3, 7)), text)
        self.assertFalse(L.date_matches('March 8, 1929', (1929, 3, 7)))
        self.assertFalse(L.date_matches('March 7, 1930', (1929, 3, 7)))

    def test_partial_register_dates(self):
        self.assertEqual(L.parse_register_date('1908')[0], 'partial')
        self.assertEqual(L.parse_register_date('1873-03')[0], 'partial')
        self.assertEqual(L.parse_register_date('')[0], 'missing')
        self.assertEqual(L.parse_register_date('1929-03-07'), ('full', (1929, 3, 7)))


class Completeness(unittest.TestCase):
    def test_complete_order_passes(self):
        ok, _, ev = L.end_test(GOOD, ORDER)
        self.assertTrue(ok, ev)
        self.assertTrue(L.start_test(GOOD, ORDER)[0])

    def test_text_running_into_next_order_fails(self):
        text = GOOD + "\nExecutive Order 5078. March 9, 1929\n\nSome other order begins here and goes on for a while.\n"
        ok, why, _ = L.end_test(text, ORDER)
        self.assertFalse(ok)
        self.assertEqual(why, 'runs_into_other_order')

    def test_next_order_far_below_signature_still_fails(self):
        text = GOOD + "\nExecutive Order 5078. March 9, 1929\n\n" + ("It is ordered that the land be withdrawn. " * 30) + "\nHERBERT HOOVER\n"
        self.assertFalse(L.end_test(text, ORDER)[0])

    def test_missing_closing_cue_fails(self):
        text = GOOD.split('HERBERT HOOVER')[0]
        ok, why, _ = L.end_test(text, ORDER)
        self.assertFalse(ok)
        self.assertEqual(why, 'no_closing_cue')

    def test_opening_dateline_is_not_a_closing_cue(self):
        text = "March 7, 1929.\nExecutive Order 5077\nPlease amend paragraph four of the rules."
        self.assertFalse(L.end_test(text, ORDER)[0])

    def test_own_bracket_tag_with_ocr_digit_is_not_another_order(self):
        text = GOOD.replace('[No. 5077]', '[No. 50771')
        self.assertTrue(L.end_test(text, ORDER)[0])

    def test_start_must_hold_number_date_or_title(self):
        self.assertFalse(L.start_test("sign my name to said patents.\nHERBERT HOOVER", ORDER)[0])

    def test_wrapper_is_not_evidence(self):
        wrapped = "# order: EO:5077 (1929)\n# source: x\n----- EXACT SOURCE TEXT -----\nsome body text only\n"
        self.assertEqual(L.body_of(wrapped), 'some body text only')


class Similarity(unittest.TestCase):
    def test_identical_and_noise(self):
        words = ' '.join(f'word{i % 37} alpha{i}' for i in range(200))
        self.assertTrue(L.similarity(words, words.upper() + ' ...')['agrees'])

    def test_jaccard_threshold(self):
        base = ' '.join(f'w{i}' for i in range(100))
        near = ' '.join(f'w{i}' if i % 20 else f'x{i}' for i in range(100))   # about 5 replaced words: Jaccard well under 0.80
        s = L.similarity(base, near)
        self.assertLess(s['jaccard'], 0.8)
        self.assertFalse(s['agrees'])
        close = ' '.join(f'w{i}' if i != 50 else 'zz' for i in range(100))
        s = L.similarity(base, close)
        self.assertGreaterEqual(s['jaccard'], 0.8)
        self.assertTrue(s['agrees'])

    def test_length_ratio_window(self):
        base = ' '.join(f'w{i}' for i in range(100))
        longer = base + ' ' + ' '.join(f'w{i}' for i in range(100, 130))   # contains every trigram of base, 30 percent longer
        s = L.similarity(base, longer)
        self.assertFalse(s['agrees'])
        self.assertLess(s['length_ratio'], 0.85)

    def test_agreeing_witness_supplies_identity(self):
        chosen_text = GOOD.replace('Executive Order 5077. March 7, 1929', 'Order. Mrs')   # no number or date in the chosen text
        chosen = witness(chosen_text.replace('[No. 5077]', '').replace('March 7, 1929.', ''), producer='p1', sha='c' * 64, tsha='d' * 64)
        other = witness(GOOD, producer='p2', sha='e' * 64, tsha='f' * 64)
        sim = L.similarity(chosen['body'], other['body'])
        ok, route, reasons, _ = L.identity_test(ORDER, chosen, [(other, dict(sim, agrees=True))])
        self.assertTrue(ok)
        self.assertTrue(route.startswith('c_'))
        ok, route, reasons, _ = L.identity_test(ORDER, chosen, [(other, dict(sim, agrees=False))])
        self.assertFalse(ok)

    def test_independence(self):
        a, b = witness(GOOD, 'p1', 's1' * 32, 't1' * 32), witness(GOOD, 'p2', 's2' * 32, 't2' * 32)
        self.assertTrue(L.independent(a, b))
        self.assertFalse(L.independent(a, witness(GOOD, 'p1', 's3' * 32, 't3' * 32)))   # same producer
        self.assertFalse(L.independent(a, witness(GOOD, 'p2', 's1' * 32, 't4' * 32)))   # same source hash
        self.assertFalse(L.independent(a, witness(GOOD, 'p2', 's5' * 32, 't1' * 32)))   # same text bytes


class Witnesses(unittest.TestCase):
    def test_hash_mismatched_witness_is_skipped_and_counted(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / 'jobs/p1').mkdir(parents=True)
            good, bad = GOOD.encode(), b'tampered after hashing'
            (root / 'jobs/p1/good.txt').write_bytes(good)
            (root / 'jobs/p1/bad.txt').write_bytes(bad)
            mk = lambda path, sha, tsha: {'instrument_id': 'EO:5077', 'grade': 'mirror_transcription', 'sha256': sha, 'text_sha256': tsha,
                                          'text_path': path, 'declaration_path': 'jobs/p1/output/FRAGMENTS.jsonl', 'requires_page_check': True}

            class Idx:
                by_sha = {'1' * 64: [mk('jobs/p1/good.txt', '1' * 64, hashlib.sha256(good).hexdigest())],
                          '2' * 64: [mk('jobs/p1/bad.txt', '2' * 64, hashlib.sha256(b'the original bytes').hexdigest())],
                          '3' * 64: [dict(mk('jobs/p1/missing.txt', '3' * 64, 'f' * 64))],
                          '4' * 64: [dict(mk('jobs/p1/good.txt', '4' * 64, hashlib.sha256(good).hexdigest()), grade='website_transcription')]}
            skipped = []
            held = L.collect_witnesses(root, Idx, ['EO:5077'], {}, skipped)
            self.assertEqual([w['sha256'] for w in held['EO:5077']], ['1' * 64])
            self.assertEqual(sorted(s['why'] for s in skipped), ['grade_not_in_working_text_policy', 'text_file_missing', 'text_hash_mismatch'])


class Choice(unittest.TestCase):
    def test_grade_order_then_longest(self):
        a = witness(GOOD, 'p1', grade='mirror_transcription')
        b = witness(GOOD, 'p2', 'x' * 64, 'y' * 64, grade='machine_read_government_printed_copy')
        c = witness(GOOD + ' extra words here ' * 5, 'p3', 'z' * 64, 'w' * 64, grade='mirror_transcription')
        self.assertIs(L.pick_chosen([a, b, c]), b)
        self.assertIs(L.pick_chosen([a, c]), c)


class Pages(unittest.TestCase):
    def test_pages_null_when_no_page_check_required(self):
        w = witness(GOOD, 'hathi-gpo-orders', grade='machine_read_government_printed_copy', requires=False)
        rec, _ = L.assess(ORDER, ['ONLY_COMPILED_TRANSCRIPTION_FOUND'], [w], L.Pinakes('/nonexistent'), {}, '/nonexistent', StubIndex())
        self.assertIsNone(rec['pages_confirmed'])
        self.assertFalse(rec['requires_page_check'])
        self.assertTrue(rec['confirmed'])
        self.assertFalse(rec['acceptable_as_original'])
        self.assertEqual(rec['method'], 'machine')

    def test_unpinned_page_check_blocks_confirmation(self):
        w = witness(GOOD, 'wikisource-texts', requires=True)
        rec, _ = L.assess(ORDER, ['ONLY_COMPILED_TRANSCRIPTION_FOUND'], [w], L.Pinakes('/nonexistent'), {}, '/nonexistent', StubIndex())
        self.assertIs(rec['pages_confirmed'], False)
        self.assertFalse(rec['confirmed'])
        self.assertIn('pages:no_page_record_rule_for_wikisource-texts', rec['reasons'])

    def _pinakes(self, usable='yes', pages='1', sha='a' * 64):
        p = L.Pinakes('/nonexistent')
        p.orders['EO:5077'] = {'sha256': sha, 'pages': pages, 'file': '1929-EO-5077.pdf', 'text_usable': usable, 'text_source': 'layer'}
        p.inventory['EO:5077'] = [{'sha256': sha, 'pages': pages, 'duplicate_of': '', 'pdf_error': ''}]
        return p

    def test_proquest_page_check(self):
        w = witness(GOOD, 'pinakes-proquest-ingest', grade='archival_replica_scan_pending_codebook')
        ok, why, _ = L.pages_test(ORDER, w, self._pinakes(), {}, '.')
        self.assertTrue(ok, why)
        self.assertFalse(L.pages_test(ORDER, w, self._pinakes(usable='no'), {}, '.')[0])
        self.assertFalse(L.pages_test(ORDER, w, self._pinakes(pages=''), {}, '.')[0])
        self.assertFalse(L.pages_test(ORDER, w, self._pinakes(sha='9' * 64), {}, '.')[0])
        far = witness(('filler words ' * 200) + GOOD, 'pinakes-proquest-ingest', grade='archival_replica_scan_pending_codebook')
        self.assertFalse(L.pages_test(ORDER, far, self._pinakes(), {}, '.')[0])

    def test_failed_page_check_means_not_confirmed(self):
        w = witness(GOOD, 'pinakes-proquest-ingest', grade='archival_replica_scan_pending_codebook')
        rec, _ = L.assess(ORDER, ['ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK'], [w], self._pinakes(usable='no'), {}, '.', StubIndex())
        self.assertTrue(rec['identity_confirmed'] and rec['complete_text_confirmed'])
        self.assertIs(rec['pages_confirmed'], False)
        self.assertFalse(rec['confirmed'])

    def test_app_page_record(self):
        w = witness(GOOD, 'app-executive-orders', sha='a' * 64, tsha='b' * 64)
        row = {'instrument_id': 'EO:5077', 'sha256': 'a' * 64, 'text_sha256': 'b' * 64, 'date': '1929-03-07',
               'heading': 'Executive Order 5077-Designating Viola Pugh to sign land patents'}
        self.assertTrue(L.pages_test(ORDER, w, L.Pinakes('/x'), {'a' * 64: [row]}, '.')[0])
        self.assertFalse(L.pages_test(ORDER, w, L.Pinakes('/x'), {'a' * 64: [dict(row, text_sha256='c' * 64)]}, '.')[0])
        self.assertFalse(L.pages_test(ORDER, w, L.Pinakes('/x'), {'a' * 64: [dict(row, date='1929-03-08')]}, '.')[0])
        self.assertFalse(L.pages_test(ORDER, w, L.Pinakes('/x'), {}, '.')[0])


class Unnumbered(unittest.TestCase):
    def test_unnumbered_needs_date_title_and_agreeing_witness(self):
        order = dict(ORDER, number='', title='Land patents signed by Viola Pugh')
        a = witness(GOOD, 'p1', 'a' * 64, 'b' * 64)
        b = witness(GOOD, 'p2', 'c' * 64, 'd' * 64)
        ok, route, _, _ = L.identity_test(order, a, [(b, L.similarity(a['body'], b['body']))])
        self.assertTrue(ok)
        self.assertTrue(route.startswith('b_'))
        self.assertFalse(L.identity_test(order, a, [])[0])


class Audit(unittest.TestCase):
    def test_audit_sample_blinds_and_plants(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / 'jobs/domesday-register/output').mkdir(parents=True)
            (root / 'jobs/p1/output').mkdir(parents=True)
            lines, regrows = [], ['instrument_id,number,suffix,date,title']
            for k in range(1, 41):
                iid = f'EO:{1000 + k}'
                text = f'Executive Order {1000 + k}. March {k % 28 + 1}, 1929\n' + ' '.join(f'term{k}x{j}' for j in range(40)) + \
                       f'\nHERBERT HOOVER\nThe White House,\nMarch {k % 28 + 1}, 1929.\n'
                p = root / f'jobs/p1/output/t{k}.txt'
                p.write_text(text, encoding='utf-8')
                lines.append(json.dumps({'instrument_id': iid, 'confirmed': True, 'grade': 'mirror_transcription', 'text_path': f'jobs/p1/output/t{k}.txt',
                                         'text_sha256': hashlib.sha256(text.encode()).hexdigest()}))
                regrows.append(f'{iid},{1000 + k},,1929-03-{k % 28 + 1:02d},Title {k}')
            (root / 'jobs/domesday-register/output/REGISTER.csv').write_text('\n'.join(regrows) + '\n')
            conf = root / 'c.jsonl'
            conf.write_text('\n'.join(lines) + '\n')
            out = root / 'packets'
            key = root / 'keys' / 'KEY.json'
            res = L.audit_sample(10, 'seed-x', conf, out, key, root)
            self.assertEqual((res['genuine'], res['defects'], res['swap'], res['cut_short']), (10, 4, 2, 2))
            self.assertEqual(len(list(out.glob('*.json'))), 14)
            self.assertEqual(L.check_packets(out, key), [])
            k = json.loads(key.read_text())['items']
            self.assertEqual(sum(1 for v in k.values() if v['kind'] == 'genuine'), 10)
            for p in out.glob('*.json'):
                doc = json.loads(p.read_text())
                self.assertEqual(set(doc), {'item_id', 'claimed_number', 'claimed_date', 'claimed_title', 'page_count', 'text'})
            res2 = L.audit_sample(10, 'seed-x', conf, root / 'packets2', root / 'keys' / 'KEY2.json', root)
            self.assertEqual(json.loads((root / 'keys' / 'KEY2.json').read_text()), json.loads(key.read_text()))
            with self.assertRaises(ValueError):
                L.audit_sample(10, 'seed-x', conf, out, out / 'KEY.json', root)





class NumberingGapTest(unittest.TestCase):
    def test_gap_in_numbered_courses_is_caught(self):
        import lachmann as L
        text = "1. 334 deg 240.8 feet to a pipe;\n2. 322 deg 942.9 feet;\n1,949.4 feet along\n7. Thence to the beginning."
        self.assertEqual(L.numbering_gaps(text), ['item:2->7'])

    def test_continuous_and_restarting_sequences_pass(self):
        import lachmann as L
        self.assertEqual(L.numbering_gaps("1. a\n2. b\n3. c\n1. d\n2. e"), [])
        self.assertEqual(L.numbering_gaps("Section 1. a\nSec. 2. b\nSec. 3. c"), [])
        self.assertEqual(L.numbering_gaps("no numbers here 762"), [])


class DanglingSignatureTest(unittest.TestCase):
    def test_list_cut_before_signature_fails(self):
        import lachmann as L
        self.assertTrue(L.dangling_before_signature("sec. 35, lots 3 to 6,\nsec. 36, lots 6 and 7,\nHERBERT HOOVER\nThe White House,"))

    def test_finished_sentence_passes(self):
        import lachmann as L
        self.assertFalse(L.dangling_before_signature("restored to the public domain.\nHERBERT HOOVER\nThe White House,"))


if __name__ == '__main__':
    unittest.main()
