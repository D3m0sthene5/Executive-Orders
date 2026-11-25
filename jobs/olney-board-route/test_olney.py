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

    def test_garbled_letter_date_is_exception(self):
        bad = REPORT.replace('MAY 3, 1962.', 'MAY 3, 196~.')
        c = cand(transmittal={'kind': 'OBSERVED_DATELINE', 'offset': bad.index('MAY 3, 196~'), 'raw': 'MAY 3, 196~'})
        self.assertEqual(olney.report_span(bad, c, 'EO:10999', None)[1], ['letter_date_ocr_damaged_cover_clean'])

    def test_cover_reading_falls_back_to_letter_date(self):
        c = cand(transmittal={'kind': 'OBSERVED_NO_HEADING', 'offset': REPORT.index('May 3, 1962'), 'raw': 'May 3, 1962'})
        span, problems = olney.report_span(REPORT, c, 'EO:10999', None)
        self.assertEqual(problems, [])
        self.assertEqual(span['letter_date_offset'], REPORT.index('MAY 3, 1962'))

    def test_other_order_and_board_number_mismatch(self):
        span, problems = olney.report_span(REPORT, cand(peb=146), 'EO:10998', None)
        self.assertIn('board_number_mismatch:145', problems)
        self.assertIn('other_order_number_in_span:10999', problems)


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


if __name__ == '__main__':
    unittest.main()
