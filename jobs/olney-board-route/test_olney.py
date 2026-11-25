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
        self.assertEqual((span['letter']['letter_date_raw'], span['letter']['status']), ('MAY 3, 196~.', 'unreadable'))
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

    def test_undated_approval_is_an_exception(self):
        # Run v3: an extension printed without its approval date cannot be dated exactly, so the order is an
        # exception (run v2 wrote it as an undated source note).
        text = ('Before the hearings were closed the parties agreed to an extension to September 7 of the original '
                'time limit for the submission of the report of this Board, and in due course the President approved '
                'this extension of time.')
        events, problems = self.events(['Cover', text], signing='1952-07-20', report='1952-09-05')
        self.assertEqual((events, problems), ([], ['report_extension_approval_date_not_printed:p2']))
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
               'span': {'date': '1962-05-03', 'char_start': 0, 'char_end': 50, 'identity': 'order_number'},
               'savings_scan': {'instrument': 'EO:12553', 'text_path': 'EO_12553.txt', 'hits_in_table': 3,
                                'hits_outside_table': 0},
               'full_report_screen': {'pages': 9, 'tool': 'pdftotext', 'pages_without_text': 0,
                                      'held_text_pages': [1, 2, 3, 4], 'extension_pages': []}}
        eid = olney.base64.urlsafe_b64encode(b'ACT:EO:10999>EO:12553').decode().rstrip('=')
        claim = {'operative_clauses': [{'first_end': {'actor': 'EO:12553', 'date': '1986-02-25', 'mechanism': 'express_revocation',
                                                      'source': {'evidence_id': eid}}}],
                 'savings_residuals': {'state': 'none_after_bounded_search', 'reason': 'the order created a board for '
                                       'one dispute; no earlier end is claimed', 'source': {'evidence_id': eid}},
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
        # The savings reason is generated from this claim's ends and Olney's reading, never carried (o2/o3 review).
        self.assertNotIn('one dispute', row['savings_reason'])
        self.assertNotIn('no earlier end', row['savings_reason'])
        self.assertIn('the board clause on 1962-05-03 (completion of its task) and the no-change period on '
                      '1962-06-02 (its own terms)', row['savings_reason'])
        self.assertIn('found them only in the subject lines', row['savings_reason'])
        self.assertIn('It found no wording extending', row['earlier_end_check'])
        self.assertIn('none of the procedural wording', row['earlier_end_check'])

        # A dated extension is a later event of the board clause; the cover basis is disclosed under
        # D-20261125-board-cover-date and the unreadable letter line is quoted, never called absent.
        sel['span'].update(date_basis='cover', cover_date_raw='MAY 3, 1962', submission_offset=None,
                           letter={'status': 'unreadable', 'letter_date_raw': 'MAY 3, 196~.', 'legible_differences': []})
        sel['extensions'] = [
            {'approval_date': '1962-03-30', 'approval_year_inferred': False, 'approval_printed': True,
             'new_deadline': '1962-05-03', 'deadline_year_inferred': False, 'page': 4, 'char_start': 5, 'char_end': 40}]
        sel['full_report_screen'] = {'pages': 9, 'tool': 'pdftotext', 'pages_without_text': 0,
                                     'held_text_pages': [1, 2, 3, 4], 'extension_pages': [4]}
        row, clauses, problems = olney.fill_rows(sel, dossier, claim, {'instrument_id': 'EO:10999'}, searches)
        self.assertEqual(problems, [])
        board = json.loads(clauses[0]['later_events'])
        self.assertEqual([e['id'] for e in board], ['ACT:EO:10999>EO:12553', 'SUPPLEMENT:olney_ext1_10999'])
        self.assertEqual(board[1]['effective_date'], '1962-03-30')
        self.assertEqual(json.loads(clauses[0]['later_event_ids']), [e['id'] for e in board])
        self.assertEqual([e['id'] for e in json.loads(clauses[1]['later_events'])], ['ACT:EO:10999>EO:12553'])
        self.assertNotIn('source_notes', row)
        self.assertIn('D-20261125-board-cover-date', clauses[0]['reason'])
        self.assertIn("is in the held text but does not read cleanly as a date ('MAY 3, 196~.')", clauses[0]['reason'])
        self.assertNotIn('not found', clauses[0]['reason'])
        self.assertIn('records one extension', row['earlier_end_check'])
        aliases = [e['alias'] for e in olney.declaration([sel])['sources']]
        self.assertEqual(aliases, ['olney_board_10999', 'olney_standstill_10999', 'olney_ext1_10999'])
        # An undated extension can no longer reach the sheets: it blocks the order.
        sel['extensions'].append(dict(sel['extensions'][0], approval_date=None, new_deadline='1962-05-10'))
        self.assertEqual(olney.fill_rows(sel, dossier, claim, {'instrument_id': 'EO:10999'}, searches)[2],
                         ['extension_without_approval_date:SUPPLEMENT:olney_ext2_10999'])
        # Letter wording for the other statuses, each true of the held text.
        sel['span']['letter'] = {'status': 'not_found_before_address'}
        self.assertIn('has no date line before its address', olney.date_words(sel['span']))
        sel['span']['letter'] = {'status': 'unreadable', 'letter_date_raw': 'Marel~ 7~ 1968.', 'signing_date': '1969-01-13',
                                 'legible_differences': [('year', '1968', '1969')], 'legible_year_before_signing': True}
        self.assertIn("its legible year reads 1968 where the cover reads 1969, and that year is earlier than the "
                      "order's signing on 1969-01-13", olney.date_words(sel['span']))
        sel['span']['letter'] = {}
        with self.assertRaises(ValueError):
            olney.date_words(sel['span'])


class ReviewCasesV3(unittest.TestCase):
    """Regression cases from the o2/o3 blind reviews of run v2 (texts quoted from the held reports)."""

    def events(self, page, signing, report):
        return olney.extension_events(held('Cover', page), signing, report, ['Cover', page], '10999')

    def test_eo_10969_undated_presidential_extension_is_an_exception(self):
        page = ('The Board, therefore, deemed it advisable to await this ratification before making its report to the '
                'President. In consequence, with the concurrence of the parties, the President extended to December '
                '10, 1961 the date for the filing of this report. We are now informed that the agreement of Novem-\n'
                'ber 2, 1961 has been ratified.')
        self.assertEqual(olney.screen_full_report(['Cover', page]), {2: 1})
        self.assertEqual(self.events(page, '1961-10-11', '1961-12-05'),
                         ([], ['report_extension_approval_date_not_printed:p2']))

    def test_eo_10147_relative_extension_and_stipulation_are_exceptions(self):
        page = ('During the course of the hearings it became apparent that the Board would\nbe unable to conclude the '
                'investigation and render its report within 30 days of the Executive order and accordingly the parties '
                'stipulated and the President approved an extension of 30 days for the rendition of said report. The '
                'evidence indicates that the dispute had its inception in a disagreement.')
        events, problems = self.events(page, '1950-08-04', '1950-09-13')
        self.assertEqual((events, problems), ([], ['report_extension_deadline_not_printed:p2']))
        self.assertEqual(olney.procedural_problems(held('Cover', page), ['Cover', page], events, '1950-08-04',
                                                   '1950-09-13'), ['report_procedural_event:stipulation:p2'])

    EO_11445 = ('President Johnson appointed the following persons as members of the Board : Laurence E. Seibe], '
                'Chairman; and Roll VMtin, arbitrator from Washin~on, D.C., Member. Shortly after the appointment of '
                'the Board, the parties agreed to e~tend the time within which the Board must repor~ its findings to '
                'the President until March 7, 1969. On Feb-\nruary 6, 1969, this extension was approved by President '
                'Nixon. The Board convened in Washington, D.C., on February 6, 1969, to discuss procedural matters.')

    def test_eo_11445_ocr_damaged_extension_is_dated(self):
        events, problems = self.events(self.EO_11445, '1969-01-13', '1969-03-07')
        self.assertEqual(problems, [])
        (e,) = events
        self.assertEqual((e['approval_date'], e['new_deadline']), ('1969-02-06', '1969-03-07'))
        quoted = held('Cover', self.EO_11445)[e['char_start']:e['char_end']]
        self.assertTrue(quoted.startswith('Shortly after') and quoted.endswith('President \nNixon.'.replace(' \n', ' ')) or
                        quoted.endswith('Nixon.'), quoted)

    def test_eo_10760_stipulated_one_member_board_and_new_period_are_exceptions(self):
        page = ('The Board convened in Washington, D. C., on June 10, 1958. The pa~fies then executed a stipulation as '
                'follows:\nSTIPULATION\nIt is hereby stipulated by Trans World Airlines, Inc., that the Emergency Board '
                'proceedings instituted on March 27, 1958, be continued subject to the following modifications: 1. That '
                'the investigation and report be made by an Emergency Board consisting of one of the three Board members '
                'designated by the President namely, Dudley E. Whiting, in place of the three-man Board; 4. That the '
                'Board as thus constituted shall report its findings to the President within 30 days from June 23, '
                '1958.')
        self.assertEqual(self.events(page, '1958-03-27', '1958-07-25'), ([], []))
        problems = olney.procedural_problems(held('Cover', page), ['Cover', page], [], '1958-03-27', '1958-07-25')
        self.assertEqual(problems, ['report_procedural_event:reconstitution:p2', 'report_procedural_event:restarted_period:p2',
                                    'report_procedural_event:stipulation:p2'])
        # Off the held pages it is an exception too.
        self.assertEqual(olney.procedural_problems(held('Cover'), ['Cover', page], [], '1958-03-27', '1958-07-25'),
                         ['report_procedural_event_outside_held_text:reconstitution:p2',
                          'report_procedural_event_outside_held_text:restarted_period:p2',
                          'report_procedural_event_outside_held_text:stipulation:p2'])

    def test_stipulation_inside_a_dated_extension_is_that_extension(self):
        page = ('On April 6th, counsel for the parties entered a stipulation agreeing to extend until April 20, 1946 '
                'the date for the Board to submit its report to the President. The President, on April 8th, approved '
                "the Board's requested extension of time. The Board is indebted to the Secretary of Labor.")
        events, problems = olney.extension_events(held('Cover', page), '1946-03-08', '1946-04-18', ['Cover', page])
        self.assertEqual((problems, [e['approval_date'] for e in events]), ([], ['1946-04-08']))
        info = {}
        self.assertEqual(olney.procedural_problems(held('Cover', page), ['Cover', page], events, '1946-03-08',
                                                   '1946-04-18', info), [])
        self.assertEqual(info['covered_stipulation_pages'], [2])
        self.assertEqual(olney.procedural_problems(held('Cover', page), ['Cover', page], [], '1946-03-08',
                                                   '1946-04-18'), ['report_procedural_event:stipulation:p2'])

    def test_unrelated_extend_and_stipulation_wording_is_not_flagged(self):
        # The contractual stipulation is EO 10150's (report p. 31): the board is named only in the sentence after it.
        page = ('No conclusion was then reached on the retroactive increase. This issue was preserved by a contractual '
                'stipulation that "Any claim for back time will remain open." The carrier did not appear before this '
                'Board at the outset of the proceedings. The carrier extends a distance of 99.2 miles from McNeil to '
                'Chestnut. After extended hearings the Board reported to the President on October 29, 1938. Changes '
                'would be extended promptly to all employees of the agency. The agreement ran to a date which the '
                'parties extended to June 10, 1934.')
        self.assertEqual(olney.screen_full_report(['Cover', page]), {})
        self.assertEqual(olney.procedural_problems(held('Cover', page), ['Cover', page], [], '1950-08-11',
                                                   '1950-09-09'), [])

    def test_period_from_the_signing_date_is_not_a_restarted_period(self):
        page = 'The Board shall report to the President within thirty days from August 4, 1950, under the Executive order.'
        self.assertEqual(olney.procedural_hits(page, '1950-08-04', '1950-09-13'), [])
        self.assertTrue(olney.procedural_hits(page, '1950-08-01', '1950-09-13'))


def report(cover_block, letter_block):
    return ("REPORT TO THE PRESIDENT\nEMERGENCY BOARD\nAPPOINTED BY EXECUTIVE ORDER 10999\n" + cover_block +
            "\n(No. 145)\n=== PDF page 2 ===\n" + letter_block)


def cover_cand(text, kind='OBSERVED_BODY_ONLY'):
    return {'peb': 145, 'candidate': {'board_clause_end': {'date': '1962-05-03'}}, 'report_date_status': 'INVENTORY_AGREES',
            'cover': {'offset': text.index('MAY 3, 1962'), 'raw': 'MAY 3, 1962'},
            'transmittal': {'kind': kind, 'offset': None, 'raw': ''}}


class LetterLinesV3(unittest.TestCase):
    """The cover route says truly what the held letter shows (o2/o3 review: EO 10050, 10067, 9918, 10630, 11445)."""
    COVER = 'WASHINGTON, D.C.\nMAY 3, 1962'
    BODY = ("THE PRESIDENT,\nThe White House.\nMR. PRESIDENT: The Emergency Board appointed under Executive Order "
            "10999 has the honor to submit herewith its report.\nRespectfully submitted.\n")

    def span(self, letter, signing='1962-03-03'):
        text = report(self.COVER, letter)
        span, problems = olney.report_span(text, cover_cand(text), 'EO:10999', signing)
        return text, span, problems

    def test_eo_10050_date_line_present_but_unreadable(self):
        text, span, problems = self.span('LETTER OF TRANSMITTAL\nWASHINGTON, D. C., May 3, I$@\n' + self.BODY)
        self.assertEqual(problems, [])
        self.assertEqual((span['date_basis'], span['letter']['status'], span['letter']['letter_date_raw']),
                         ('cover', 'unreadable', 'WASHINGTON, D. C., May 3, I$@'))
        self.assertEqual(span['letter']['legible_differences'], [])
        self.assertTrue(span['char_start'] <= span['letter']['letter_date_offset'] < span['char_end'])
        words = olney.date_words(span)
        self.assertIn("is in the held text but does not read cleanly as a date ('WASHINGTON, D. C., May 3, I$@')", words)
        self.assertNotIn('not found', words)
        # A legible month and day that differ from the cover read as another day: a conflict, not 'unreadable'.
        self.assertEqual(self.span('LETTER OF TRANSMITTAL\nWASHINGTON, D. C., May 6, I$@\n' + self.BODY)[2],
                         ['letter_date_legible_part_conflicts'])

    def test_eo_10067_damaged_line_without_digits_is_a_date_line(self):
        _, span, problems = self.span('ST. LOUIS, MO., AW~US~ a, IQQ.\n' + self.BODY.replace('THE PRESIDENT,', 'THE PRESIDENT,'))
        self.assertEqual((problems, span['letter']['status']), ([], 'unreadable'))
        self.assertEqual(span['letter']['letter_date_raw'], 'ST. LOUIS, MO., AW~US~ a, IQQ.')

    def test_eo_11445_damaged_address_herewith_order_and_conflicting_year_disclosed(self):
        body = self.BODY.replace('THE PRESIDENT,', 'THE IORESIDENT,').replace(
            'has the honor to submit herewith', 'has the honor herewith to submit')
        _, span, problems = self.span('LETTER OF TRANSMITTAL\nWASHIN(]TON~ I).C.~ Marel~ 3~ 1961.\n' + body,
                                      signing='1962-03-03')
        self.assertEqual(problems, [])
        self.assertIsNotNone(span['submission_offset'])
        self.assertEqual(span['letter']['legible_differences'], [('year', '1961', '1962')])
        self.assertTrue(span['letter']['legible_year_before_signing'])
        self.assertIn("its legible year reads 1961 where the cover reads 1962, and that year is earlier than the "
                      "order's signing", olney.date_words(span))

    def test_letter_without_date_line_says_so_and_only_when_true(self):
        _, span, problems = self.span(self.BODY)
        self.assertEqual((problems, span['letter']['status']), ([], 'not_found_before_address'))
        self.assertIn('has no date line before its address', olney.date_words(span))
        other = self.BODY.replace('has the honor', 'on April 30, 1962 has the honor')
        self.assertIn('letter_date_line_status_uncertain', self.span(other)[2])

    def test_held_letter_without_submission_sentence_is_an_exception(self):
        body = self.BODY.replace('has the honor to submit herewith its report', 'reports as follows')
        self.assertEqual(self.span('LETTER OF TRANSMITTAL\nMay 3, 196~.\n' + body)[2], ['letter_held_submission_not_found'])

    def test_letter_line_reading_cleanly_as_another_date_is_a_conflict(self):
        self.assertEqual(self.span('LETTER OF TRANSMITTAL\nWASHINGTON, D. C., May 8, 1962.\n' + self.BODY)[2],
                         ['cover_date_differs_from_letter'])


class SavingsV3(unittest.TestCase):
    def claim(self, path):
        eid = olney.base64.urlsafe_b64encode(b'ACT:EO:10999>EO:12553').decode().rstrip('=')
        return {'operative_clauses': [{'first_end': {'actor': 'EO:12553', 'date': '1986-02-25', 'source': {'evidence_id': eid}}}],
                'savings_residuals': {'state': 'none_after_bounded_search', 'source': {'text_path': path}}}

    def test_savings_scan_reads_the_revoking_order(self):
        import tempfile
        body = ("Executive Order 12553 of February 25, 1986\nRevocation\nit is hereby ordered that the following "
                "Executive Orders are revoked:\nNo. Subject\n10999 Providing for a board\nTHE W HITE HOUSE,\n"
                "[FR Doc. 86-1]\n")
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'EO_12553.txt').write_text(body)
            scan, problem = olney.savings_scan(d, self.claim('EO_12553.txt'))
            self.assertEqual((problem, scan['hits_in_table'], scan['hits_outside_table']), (None, 1, 0))
            (Path(d) / 'EO_12553.txt').write_text(body.replace('Revocation', 'Nothing herein affects pending matters'))
            self.assertEqual(olney.savings_scan(d, self.claim('EO_12553.txt'))[1], 'savings_source_wording_outside_table')
            self.assertEqual(olney.savings_scan(d, self.claim('EO_10999.txt'))[1], 'savings_source_not_the_revoking_order')


class Selection(unittest.TestCase):
    def test_upheld_orders_are_not_rerun_and_10944_is(self):
        self.assertEqual(len(olney.UPHELD), 8)
        self.assertNotIn('EO:10944', olney.UPHELD)
        self.assertEqual(olney.UPHELD_V2, {'EO:10105', 'EO:9702'})

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
