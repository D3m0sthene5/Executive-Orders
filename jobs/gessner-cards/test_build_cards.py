import unittest

import build_cards as b


def reg(i, number, date="", president="", title="T", suffix=""):
    return {"instrument_id": i, "number": number, "suffix": suffix, "date": date, "president": president,
            "title": title, "era": "1907–1936", "best_held": "transcription_only"}


def ready_row(i, status="", ready="no", steps=None, blockers=""):
    row = {"instrument_id": i, "provisional_status": status, "ready_for_human_review": ready,
           "text_evidence_tier": "missing", "blockers": blockers, "original_copy_replacement_required": "no",
           "decision_origin": "jacquard-L1R-2026-10-31:ai_class_status (x)"}
    for s in b.STEPS:
        row["step_" + s] = (steps or {}).get(s, "n/a" if s in ("shared_sources", "opus_media") else "open")
    return row


class PresidentFromDate(unittest.TestCase):
    def test_full_dates(self):
        self.assertEqual(b.president_from_date("1933-03-05"), ("Franklin D. Roosevelt", "date"))
        self.assertEqual(b.president_from_date("1946-12-11"), ("Harry S. Truman", "date"))

    def test_transition_day_left_uncertain(self):
        self.assertEqual(b.president_from_date("1933-03-04")[1], "transition")

    def test_partial_dates(self):
        self.assertEqual(b.president_from_date("1905"), ("Theodore Roosevelt", "date"))
        self.assertEqual(b.president_from_date("1945")[1], "none")  # Truman took office in 1945
        self.assertEqual(b.president_from_date("1945-04")[1], "none")
        self.assertEqual(b.president_from_date("1945-05"), ("Harry S. Truman", "date"))
        self.assertEqual(b.president_from_date("")[1], "none")


class Build(unittest.TestCase):
    def test_counts_and_order(self):
        regs = [reg("EO:10", "10", "1933-05-01"), reg("EO:2", "2", "1862-02-27", "Abraham Lincoln"),
                reg("EO:2A", "2", "1862-03-01", "", suffix="A")]
        rows = [
            ready_row("EO:10", "no", "yes", {s: "done" for s in b.STEPS[:6]}),
            ready_row("EO:2"),
            ready_row("EO:2A", "yes", steps={"provisional_status": "done", "original_text": "provisional",
                                             "clause_inventory": "done", "ending_or_current_basis": "done",
                                             "savings_residuals": "done"},
                      blockers="NO_CLAUSE_INVENTORY|CLAIM_INCOMPLETE:counterevidence"),
        ]
        data, summary = b.build(regs, rows, {})
        self.assertEqual([r[0] for r in data["rows"]], ["2", "2A", "10"])
        self.assertEqual(summary["ready_for_human_review"], 1)
        self.assertEqual(summary["with_provisional_status"], 2)
        self.assertEqual(summary["one_step_from_ready"], 1)
        self.assertEqual(summary["human_certified"], 0)
        self.assertEqual(data["rows"][1][7], "dpdddo--")
        self.assertEqual(data["origins"][data["rows"][2][13]], "jacquard-L1R")
        codes = data["codes"]
        decoded = [codes[int(x.split(":")[0])] for x in data["rows"][1][11].split("|")]
        self.assertEqual(decoded, ["NO_CLAUSE_INVENTORY", "CLAIM_INCOMPLETE"])
        self.assertEqual(data["pres"][data["rows"][2][3]], "Franklin D. Roosevelt")
        self.assertEqual(data["rows"][2][4], 1)  # derived from date

    def test_missing_register_row_reported(self):
        _, summary = b.build([], [ready_row("EO:1")], {})
        self.assertEqual(summary["readiness_rows_missing_from_register"], ["EO:1"])


if __name__ == "__main__":
    unittest.main()
