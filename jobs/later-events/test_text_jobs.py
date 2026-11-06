import unittest

from text_jobs import text_jobs


class TextJobsTests(unittest.TestCase):
    def test_default_gains_selden_acting_texts_once(self):
        self.assertEqual(text_jobs("fr-originals,app-transcriptions", {}),
                         "fr-originals,app-transcriptions,selden-fr-acting")
        self.assertEqual(text_jobs("fr-originals,selden-fr-acting", {}), "fr-originals,selden-fr-acting")

    def test_explicit_environment_wins(self):
        self.assertEqual(text_jobs("fr-originals", {"LATER_EVENTS_TEXT_JOBS": "fr-originals"}), "fr-originals")


if __name__ == "__main__":
    unittest.main()
