"""Offline tests for Olney's mechanical steps (synthetic texts; no repository data needed)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import olney  # noqa: E402

ORDER = ("EXECUTIVE ORDER 10999\nCreating an Emergency Board\nWHEREAS a dispute exists;\n"
         "NOW, THEREFORE, I hereby create a board of three members to investigate the said dispute.\n"
         "The board shall report its findings to the President within thirty days from the date of this order.\n"
         "As provided by section 10 of the Rail­\nway Labor Act, from this date and for thirty days after the board "
         "has made its re-\nport to the President, no change, except by agreement, shall be made in the conditions out "
         "of which the dispute arose.\nJohn F. Kennedy\nThe White House,\nMarch 3, 1962.")

REPORT = ("REPORT TO THE PRESIDENT\nEMERGENCY BOARD\nAPPOINTED BY EXECUTIVE ORDER 10999\nWASHINGTON, D.C.\n"
          "May 3, 1962\nEmergency Board No. 145\n=== PDF page 2 ===\nLETTER OF TRANSMITTAL\nMAY 3, 1962.\n"
          "THE PRESIDENT,\nThe White House.\nSIR: The Emergency Board appointed under your Executive Order No. 10999 "
          "has the honor to submit herewith its report and recommendations.\nRespectfully, X, Chairman.\n")


def cand(**kw):
    c = {'peb': 145, 'candidate': {'board_clause_end': {'date': '1962-05-03'}},
         'cover': {'offset': REPORT.index('May 3, 1962'), 'raw': 'May 3, 1962'},
         'transmittal': {'kind': 'OBSERVED_DATELINE', 'offset': REPORT.index('MAY 3, 1962'), 'raw': 'MAY 3, 1962'}}
    c.update(kw)
    return c


class Dates(unittest.TestCase):
    def test_clean_dates_only(self):
        self.assertEqual(olney.parse_date('MAY 3, 1962.'), '1962-05-03')
        self.assertEqual(olney.parse_date('July 29,1949.'), '1949-07-29')
        self.assertIsNone(olney.parse_date('ApraT 18, 1946'))
        self.assertIsNone(olney.parse_date('May 1, 136~'))

    def test_thirtieth_day_inclusive_and_exclusive(self):
        self.assertEqual(olney.plus_days('1946-04-18', 30), '1946-05-18')
        self.assertEqual(olney.plus_days('1949-07-29', 30), '1949-08-28')
        self.assertEqual(olney.plus_days('1960-02-10', 30), '1960-03-11')  # leap year


class Clauses(unittest.TestCase):
    def test_split_board_and_standstill_skips_signature(self):
        board, standstill, problems = olney.split_clause(ORDER, 100)
        self.assertEqual(problems, [])
        self.assertTrue(ORDER[board[1] - 100 - len('this order.'):board[1] - 100] == 'this order.')
        text = ORDER[standstill[0] - 100:standstill[1] - 100]
        self.assertTrue(text.startswith('As provided') and text.endswith('dispute arose.'), text)

    def test_other_command_after_standstill_is_doubt(self):
        extra = ORDER.replace('John F. Kennedy', 'In performing its functions the Board shall comply with section 502.')
        self.assertTrue(any(p.startswith('text_after_standstill') for p in olney.split_clause(extra, 0)[2]))

    def test_no_standstill_is_board_only(self):
        short = ORDER.split('As provided')[0]
        board, standstill, problems = olney.split_clause(short, 0)
        self.assertIsNone(standstill)
        self.assertEqual(problems, [])

    def test_ocr_damaged_standstill_words_are_tolerated(self):
        damaged = ORDER.replace('the board "\n', '').replace('the board has made', 'thff board nas made').replace(
            'no change', 'no ehange')
        board, standstill, problems = olney.split_clause(damaged, 0)
        self.assertEqual(problems, [])
        self.assertTrue(damaged[standstill[0]:standstill[1]].endswith('dispute arose.'))
        self.assertIn('standstill_sentence_lacks_no_change_or_agreement',
                      olney.split_clause(damaged.replace('except by agreement', 'except as agreed'), 0)[2])

    def test_wrong_document_has_no_board_creation(self):
        self.assertIn('board_creation_sentences:0', olney.split_clause('A PROCLAMATION designating Red Cross Month.', 0)[2])


class Spans(unittest.TestCase):
    def test_span_runs_from_cover_to_submission(self):
        span, problems = olney.report_span(REPORT, cand(), 'EO:10999', '1962-03-03')
        self.assertEqual(problems, [])
        text = REPORT[span['char_start']:span['char_end']]
        self.assertTrue(text.startswith('EMERGENCY BOARD') or text.startswith('APPOINTED'), text)
        self.assertTrue(text.endswith('recommendations.'))
        self.assertEqual(span['identity'], 'order_number')

    def test_garbled_letter_date_with_clean_cover_uses_the_cover(self):
        # D-20261125-board-cover-date: an unreadable letter date line, a clean cover date.
        bad = REPORT.replace('MAY 3, 1962.', 'MAY 3, 196~.')
        c = cand(transmittal={'kind': 'OBSERVED_DATELINE', 'offset': bad.index('MAY 3, 196~'), 'raw': 'MAY 3, 196~'})
        span, problems = olney.report_span(bad, c, 'EO:10999', None)
        self.assertEqual(problems, [])
        self.assertEqual((span['date_basis'], span['date'], span['cover_date_raw']), ('cover', '1962-05-03', 'May 3, 1962'))
        self.assertEqual(span['letter']['letter_date_raw'], 'MAY 3, 196~')
        self.assertTrue(bad[span['char_start']:span['char_end']].endswith('recommendations.'))

    def test_garbled_letter_and_unclean_cover_stays_exception(self):
        bad = REPORT.replace('MAY 3, 1962.', 'MAY 3, 196~.').replace('May 3, 1962', 'May 3, 19@2')
        c = cand(transmittal={'kind': 'OBSERVED_DATELINE', 'offset': bad.index('MAY 3, 196~'), 'raw': 'MAY 3, 196~'},
                 cover={'offset': bad.index('May 3, 19@2'), 'raw': 'May 3, 19@2'})
        self.assertEqual(olney.report_span(bad, c, 'EO:10999', None)[1], ['letter_date_ocr_damaged'])

    def test_uncorroborated_report_date_never_uses_the_cover(self):
        bad = REPORT.replace('MAY 3, 1962.', 'MAY 3, 196~.')
        c = cand(transmittal={'kind': 'OBSERVED_DATELINE', 'offset': bad.index('MAY 3, 196~'), 'raw': 'MAY 3, 196~'},
                 report_date_status='CONFLICT_IMAGE_CHECK_NEEDED')
        self.assertEqual(olney.report_span(bad, c, 'EO:10999', None)[1], ['letter_date_ocr_damaged_cover_clean'])

    def test_letter_reading_cleanly_as_another_date_is_a_conflict(self):
        bad = REPORT.replace('MAY 3, 1962.', 'MAY 8, 1962.')
        c = cand(transmittal={'kind': 'OBSERVED_DATELINE', 'offset': bad.index('MAY 8, 1962'), 'raw': 'MAY 8, 1962'})
        self.assertEqual(olney.report_span(bad, c, 'EO:10999', None)[1], ['cover_date_differs_from_letter'])

    def test_no_letter_found_span_is_the_cover_through_the_board_number(self):
        text = ("REPORT TO THE PRESIDENT\nEMERGENCY BOARD\nAPPOINTED FEBRUARY 4,1950, BY EXECUTIVE\nORDER 10999\n"
                "DENVER, COLORADO\nFEBRUARY 28, 1950 \n(No. 79) \n=== PDF page 2 ===\n\n=== PDF page 3 ===\n"
                "The Executive order is as follows:\nThe board shall report within thirty days.\n")
        c = {'peb': 79, 'candidate': {'board_clause_end': {'date': '1950-02-28'}}, 'report_date_status': 'INVENTORY_AGREES',
             'cover': {'offset': text.index('FEBRUARY 28'), 'raw': 'FEBRUARY 28, 1950'},
             'transmittal': {'kind': 'NO_TRANSMITTAL_MARKER', 'offset': None, 'raw': ''}}
        span, problems = olney.report_span(text, c, 'EO:10999', '1950-02-03')
        self.assertEqual(problems, [])
        self.assertEqual(span['submission_offset'], None)
        self.assertTrue(text[span['char_start']:span['char_end']].endswith('(No. 79)'))
        self.assertEqual(span['letter']['reason'], 'letter_date_not_located:NO_TRANSMITTAL_MARKER')

    def test_cover_appointment_date_names_the_order_only_with_its_board_number(self):
        text = ("REPORT TO THE PRESIDENT\nEMERGENCY BOARD\nAPPOINTED FEBRUARY 15, 1949\nWASHINGTON\n"
                "SEPTEMBER 19, 1949\n(No. 70)\n")
        c = {'peb': 70, 'candidate': {'board_clause_end': {'date': '1949-09-19'}},
             'cover': {'offset': text.index('SEPTEMBER'), 'raw': 'SEPTEMBER 19, 1949'},
             'transmittal': {'kind': 'ABSENT', 'offset': None, 'raw': ''}}
        self.assertEqual(olney.report_span(text, c, 'EO:10038', '1949-02-15')[0]['identity'], 'appointment_date')
        self.assertIn('order_identity_not_in_span', olney.report_span(text.replace('(No. 70)', ''), c, 'EO:10038',
                                                                      '1949-02-15')[1])

    def test_submission_sentence_runs_past_abbreviations(self):
        self.assertEqual(olney.sentence_stop('created by Executive Order No. 10147 of the Railroad Co. and others.', 0),
                         len('created by Executive Order No. 10147 of the Railroad Co. and others'))

    def test_cover_reading_falls_back_to_letter_date(self):
        c = cand(transmittal={'kind': 'OBSERVED_NO_HEADING', 'offset': REPORT.index('May 3, 1962'), 'raw': 'May 3, 1962'})
        span, problems = olney.report_span(REPORT, c, 'EO:10999', None)
        self.assertEqual(problems, [])
        self.assertEqual(span['letter_date_offset'], REPORT.index('MAY 3, 1962'))

    def test_other_order_and_board_number_mismatch(self):
        span, problems = olney.report_span(REPORT, cand(peb=146), 'EO:10998', None)
        self.assertIn('board_number_mismatch:145', problems)
        self.assertIn('other_order_number_in_span:10999', problems)


def held(*pages):
    return ''.join(f'=== PDF page {n} of 9 ===\n{body}\n' for n, body in enumerate(pages, 1))


class Extensions(unittest.TestCase):
    DATED = ("The hearings closed. During the hearings the parties entered into a stipulation to extend the time for "
             "the Board to submit its report to the President until December 17. The stipulation was approved by "
             "the President on November 9. The record consists of 26 volumes.")

    def events(self, pages, full=None, signing='1948-10-20', report='1948-12-10'):
        return olney.extension_events(held(*pages), signing, report, full if full is not None else list(pages), '10999')

    def test_no_extension_wording(self):
        self.assertEqual(self.events(['Cover', 'Letter of transmittal']), ([], []))

    def test_dated_extension_with_years_resolved_by_the_report_window(self):
        events, problems = self.events(['Cover', self.DATED])
        self.assertEqual(problems, [])
        (e,) = events
        self.assertEqual((e['approval_date'], e['new_deadline'], e['page']), ('1948-11-09', '1948-12-17', 2))
        self.assertTrue(e['approval_year_inferred'] and e['deadline_year_inferred'])
        text = held('Cover', self.DATED)
        quoted = text[e['char_start']:e['char_end']]
        self.assertTrue(quoted.startswith('During the hearings') and quoted.endswith('November 9.'), quoted)

    def test_extension_outside_the_held_pages_is_an_exception(self):
        full = ['Cover', 'Letter', 'Intro', 'The National Mediation Board recommends that the extension of time be '
                'approved, permitting this Emergency Board to file its report not later than July 19, 1961.']
        events, problems = self.events(['Cover', 'Letter'], full=full)
        self.assertEqual(problems, ['report_extension_outside_held_text:p4'])

    def test_several_extensions_are_an_exception(self):
        text = ('Since the creation of the Board, the President has on two occasions extended the time limit stated in '
                'the Executive order, the last extension being to May 24, 1961.')
        self.assertEqual(self.events(['Cover', text], report='1961-05-20')[1], ['report_extension_multiple:p2'])

    def test_undated_approval_is_kept_only_when_no_other_date_is_printed(self):
        text = ('Before the hearings were closed the parties agreed to an extension to September 7 of the original '
                'time limit for the submission of the report of this Board, and in due course the President approved '
                'this extension of time.')
        events, problems = self.events(['Cover', text], signing='1952-07-20', report='1952-09-05')
        self.assertEqual(problems, [])
        self.assertEqual((events[0]['approval_date'], events[0]['new_deadline'], events[0]['approval_printed']),
                         (None, '1952-09-07', True))
        other = text.replace('in due course', 'on August 20 at the request of the parties')
        self.assertEqual(self.events(['Cover', other], signing='1952-07-20', report='1952-09-05')[1],
                         ['report_extension_approval_date_unparsed:p2'])

    def test_report_after_the_extended_deadline_is_an_exception(self):
        self.assertEqual(self.events(['Cover', self.DATED], report='1948-12-20')[1],
                         ['report_after_extended_deadline:p2'])

    def test_modal_wording_in_a_report_within_thirty_days_is_no_extension(self):
        text = ('We recognize that under certain conditions the time for our report can be extended beyond the 30-day '
                'time provided in the Executive order herein set out.')
        self.assertEqual(self.events(['Cover', text], signing='1950-02-03', report='1950-02-28'), ([], []))
        self.assertTrue(self.events(['Cover', text], signing='1950-01-03', report='1950-02-28')[1])

    def test_spaced_letters_of_a_damaged_text_layer_are_screened(self):
        page = ('The p a r t i e s have entered into a stipulation providing f o r a n extension of time w i t h i n '
                'which this emergency board shall r e p o r t its findings to the President.')
        self.assertEqual(olney.screen_full_report(['x', page]), {2: 1})

    def test_unreadable_pdf_is_an_exception(self):
        self.assertEqual(olney.extension_events(held('x'), '1950-01-01', '1950-02-01', None), ([], ['report_pdf_text_unreadable']))


class Sheets(unittest.TestCase):
    def test_rows_follow_the_rule(self):
        sel = {'instrument_id': 'EO:10999', 'peb': 145, 'report_sha256': 'a' * 64, 'report_local_path': 'x.pdf',
               'report_text_path': 't.txt', 'report_text_sha256': 'b' * 64, 'report_url': 'https://nmb.gov/x.pdf',
               'report_page_or_item': 'p1', 'claim_file': 'c.jsonl', 'board_range': [0, 10], 'standstill_range': [11, 20],
               'span': {'date': '1962-05-03', 'char_start': 0, 'char_end': 50, 'identity': 'order_number'}}
        eid = olney.base64.urlsafe_b64encode(b'ACT:EO:10999>EO:12553').decode().rstrip('=')
        claim = {'operative_clauses': [{'first_end': {'actor': 'EO:12553', 'date': '1986-02-25', 'mechanism': 'express_revocation',
                                                      'source': {'evidence_id': eid}}}],
                 'savings_residuals': {'state': 'none_after_bounded_search', 'reason': 'none', 'source': {'evidence_id': eid}},
                 'later_source_search': [{'repository': 'R'}], 'claim_kit': {'original_pages_confirmed': False}}
        dossier = {'evidence': {'ACT:EO:10999>EO:12553': {}}, 'original_source_id': 'ORIGINAL:EO:10999'}
        searches = [{'search_id': 's1', 'complete': True, 'entry': {'repository': 'R'}}]
        row, clauses, problems = olney.fill_rows(sel, dossier, claim, {'instrument_id': 'EO:10999'}, searches)
        self.assertEqual(problems, [])
        self.assertEqual([c['effective_date'] for c in clauses], ['1962-05-03', '1962-06-02'])
        self.assertEqual(json.loads(clauses[0]['later_events'])[0]['effective_date'], '1986-02-25')
        self.assertEqual(row['search_ids'], '["s1"]')
        self.assertEqual(row['original_pages_confirmed'], 'false')
        decl = olney.declaration([sel])
        self.assertEqual([e['alias'] for e in decl['sources']], ['olney_board_10999', 'olney_standstill_10999'])
        self.assertNotIn('source_notes', row)

        # A dated extension is a later event of the board clause; an undated one a source note; the cover basis
        # is disclosed under D-20261125-board-cover-date.
        sel['span'].update(date_basis='cover', cover_date_raw='MAY 3, 1962', letter={'letter_date_raw': 'MAY 3, 196~'},
                           submission_offset=None)
        sel['extensions'] = [
            {'approval_date': '1962-03-30', 'approval_year_inferred': False, 'approval_printed': True,
             'new_deadline': '1962-05-03', 'deadline_year_inferred': False, 'page': 4, 'char_start': 5, 'char_end': 40},
            {'approval_date': None, 'approval_year_inferred': False, 'approval_printed': True,
             'new_deadline': '1962-05-10', 'deadline_year_inferred': True, 'page': 4, 'char_start': 41, 'char_end': 60}]
        sel['full_report_screen'] = {'pages': 9, 'tool': 'pdftotext', 'pages_without_text': 0,
                                     'held_text_pages': [1, 2, 3, 4], 'extension_pages': [4]}
        row, clauses, problems = olney.fill_rows(sel, dossier, claim, {'instrument_id': 'EO:10999'}, searches)
        self.assertEqual(problems, [])
        board = json.loads(clauses[0]['later_events'])
        self.assertEqual([e['id'] for e in board], ['ACT:EO:10999>EO:12553', 'SUPPLEMENT:olney_ext1_10999'])
        self.assertEqual(board[1]['effective_date'], '1962-03-30')
        self.assertEqual(json.loads(clauses[0]['later_event_ids']), [e['id'] for e in board])
        self.assertEqual([e['id'] for e in json.loads(clauses[1]['later_events'])], ['ACT:EO:10999>EO:12553'])
        (note,) = json.loads(row['source_notes'])
        self.assertEqual(note['id'], 'SUPPLEMENT:olney_ext2_10999')
        self.assertIn('prints no date', note['date_qualification'])
        self.assertIn('D-20261125-board-cover-date', clauses[0]['reason'])
        self.assertIn("'MAY 3, 196~'", clauses[0]['reason'])
        self.assertIn('records 2 extension', row['earlier_end_check'])
        aliases = [e['alias'] for e in olney.declaration([sel])['sources']]
        self.assertEqual(aliases, ['olney_board_10999', 'olney_standstill_10999', 'olney_ext1_10999', 'olney_ext2_10999'])


class Selection(unittest.TestCase):
    def test_upheld_orders_are_not_rerun_and_10944_is(self):
        self.assertEqual(len(olney.UPHELD), 8)
        self.assertNotIn('EO:10944', olney.UPHELD)

    def test_pergamon_route_follows_the_checkout_kit(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / olney.SUPPLEMENT
            path.parent.mkdir(parents=True)
            path.write_text('def derive(): pass\n')
            self.assertFalse(olney.kit_supports_pergamon(d))
            path.write_text('def held_bytes(repo, source): pass\n')
            self.assertTrue(olney.kit_supports_pergamon(d))

    def test_primary_reasons_and_needs(self):
        self.assertEqual(olney.primary(['report_extension_multiple:p6']), 'report_extension_not_scriptable')
        self.assertEqual(olney.primary(['cover_date_differs_from_letter']), 'letter_and_cover_dates_conflict')
        self.assertEqual(olney.primary(['report_bytes_pergamon_only_kit_gap']), 'report_bytes_pergamon_only_kit_gap')
        self.assertEqual(olney.primary(['report_bytes_pergamon_only_kit_gap', 'order_identity_not_in_span']),
                         'report_identity_doubt')
        for k in ('report_extension_not_scriptable', 'letter_and_cover_dates_conflict', 'follow_on_order'):
            self.assertTrue(olney.NEEDS[k])


if __name__ == '__main__':
    unittest.main()
