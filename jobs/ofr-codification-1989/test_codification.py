import csv
import hashlib
import json
import pathlib
import tempfile
import unittest

import codification as c

HERE = pathlib.Path(__file__).resolve().parent


def chunk_page(page, chunks, printed=None):
    """A synthetic page of positioned chunks: [x, y, text]. Numbers sit at x=56, amendments at 126,
    dispositions at 266; rows are 7 pt apart."""
    ch = [list(x) for x in chunks]
    ch.append([182.0, 652.0, "Executive Orders"])           # running head, y > 625
    ch.append([67.0, 633.0, "Number or Date Amendments Disposition"])  # column heads
    if printed:
        ch.append([204.0, 97.0, str(printed)])
    return {"page": page, "w": 404.0, "h": 704.0, "chunks": ch}


def rows_of(pages, census=frozenset()):
    rows, orphans, _ = c.parse_table(pages, set(census))
    return {r["key"]: r for r in rows}, orphans


class SourceLines(unittest.TestCase):
    def facts(self, text):
        sq = c.squash(text)
        m = c.SOURCE_RE.search(sq)
        return m, c.parse_source_rest(sq[m.end():])

    def test_date_and_fr_citation_from_squashed_text(self):
        m, f = self.facts("SOURCE : The provisions of Executive Order 8248 of Sept. 8, 1939, appear at 4 FR\n"
                          "3864, 3 CFR , 1938-1943 Comp ., p . 576, unless otherwise noted .")
        self.assertEqual((c.doc_id(m.group(1), m.group(2)), c.iso(m.group(3), m.group(4), m.group(5))),
                         ("EO:8248", "1939-09-08"))
        self.assertEqual((f["fr_citation"], f["cfr_compilation"]), ("4 FR 3864", "3 CFR, 1938-1943 Comp., p. 576"))

    def test_fragmented_words_and_glued_months(self):
        m, _ = self.facts("SOURCE\n:\nThe provisions\nofExecutive Order\n11246 ofJuly\n24,\n1965 , appear at 30FR 12319")
        self.assertEqual(c.iso(m.group(3), m.group(4), m.group(5)), "1965-07-24")

    def test_no_date_not_in_fr_and_restated(self):
        m, f = self.facts("SOURCE: The provisions of Executive Order 10631, appear at 20 FR 6057, 3 CFR, 1954-1958 Comp., p. 266")
        self.assertEqual((m.group(2), m.group(3)), ("10631", None))
        _, f = self.facts("SOURCE: The provisions of Executive Order 1888 of Feb. 2, 1914, do not appear in the Federal "
                          "Register system. [Secs. 1-19 are obsolete")
        self.assertEqual((f["not_in_fr_system"], f["fr_citation"]), ("yes", ""))
        _, f = self.facts("SOURCE: The provisions of Executive Order 10879 of June 1, 1960, 25 FR 4893, 3 CFR, 1959-1963 "
                          "Comp., p. 411, were revised and restated in their entirety by Executive Order 11174 of Sept. 1, "
                          "1964. These provisions, as revised, appear at 29 FR 12547, 3 CFR, 1964-1965 Comp., p. 229, unless otherwise noted.")
        self.assertEqual((f["restated"], f["restated_by"], f["restated_by_date"], f["fr_citation"], f["codified_text_fr"]),
                         ("revised and restated", "EO:11174", "1964-09-01", "25 FR 4893", "29 FR 12547"))


BODY_A = """CHAPTER 3-EXECUTIVE OFFICE OF THE PRESIDENT
Executive Orders
8248 Establishing the divisions of the Executive Office
Executive Order 8248 -Establishing the divisions of the Executive
Office of the President
SOURCE : The provisions of Executive Order 8248 of Sept. 8, 1939, appear at 4 FR
3864, 3 CFR , 1938-1943 Comp ., p . 576, unless otherwise noted .
By virtue of the authority vested in me, see Executive Order No. 9397 of Nov. 22, 1943,
[Sec. 2 amended by EO 11000 of Feb. 16, 1962]
7"""
BODY_B = """Codification of Presidential Proclamations and Executive Orders
the text goes on.
Executive Order 10860 —Coat of arms
SOURCE : The provisions of Executive Order 10860 of Feb. 5, 1960, appear at 25 FR
1089, unless otherwise noted .
SEC. 1. Arms.
8"""
BODY_C = """Chapter 3- Executive Office of the President
SEC. 2.
Seal
shall be
used. The end
of it. Executive Order
12114 – Environmental
effects
abroad
SOURCE:
The
provisions of
Executive Order
12114 of
Jan. 4,
1979, appear
at 44 FR
1957,
unless otherwise noted
9"""
BODY_D = """Its last words.
CHAPTER 4- [ RESERVED ]
CHAPTER 5- FEDERAL CIVILIAN PERSONNEL
Executive Orders
9230 Something listed in the contents
10"""


class Body(unittest.TestCase):
    def setUp(self):
        self.pages = [(18, BODY_A), (19, BODY_B), (20, BODY_C), (21, BODY_D)]
        self.stream, self.stats = c.body_stream(self.pages, 18, 21, 11)
        self.docs, _ = c.find_documents(self.stream)
        self.by = {d["instrument_id"]: d for d in self.docs}

    def test_running_heads_and_printed_page_dropped(self):
        lines = [l for _, _, l in self.stream]
        self.assertNotIn("Codification of Presidential Proclamations and Executive Orders", lines)
        self.assertNotIn("Chapter 3- Executive Office of the President", lines)
        self.assertNotIn("8", lines)
        self.assertEqual(self.stats["printed_read"], 4)
        self.assertIn("CHAPTER 3-EXECUTIVE OFFICE OF THE PRESIDENT", lines)  # the chapter heading itself stays

    def test_documents_anchor_on_source_and_end_at_next_heading(self):
        self.assertEqual([d["instrument_id"] for d in self.docs], ["EO:8248", "EO:10860", "EO:12114"])
        a = self.by["EO:8248"]
        self.assertEqual((a["date"], a["chapter"], a["pdf_pages"], a["printed_pages"]), ("1939-09-08", "3", (18, 19), ("7", "8")))
        text = "\n".join(l for _, _, l in a["lines"])
        self.assertTrue(text.startswith("Executive Order 8248 -Establishing"))   # not the contents list above it
        self.assertIn("the text goes on.", text)                                  # runs over the page break
        self.assertNotIn("Coat of arms", text)
        self.assertEqual(a["heading_title"], "Establishing the divisions of the Executive Office of the President")
        self.assertEqual(self.by["EO:10860"]["heading_title"], "Coat of arms")    # em dash heading

    def test_heading_mid_line_on_a_fragmented_page_and_chapter_cut(self):
        d = self.by["EO:12114"]
        self.assertTrue(d["heading_found"])
        self.assertEqual(d["date"], "1979-01-04")
        self.assertIn(20, self.stats["fragmented"])
        text = "\n".join(l for _, _, l in d["lines"])
        self.assertIn("Its last words.", text)
        self.assertNotIn("CHAPTER 5", text)              # the next chapter heading ends the document
        self.assertNotIn("9230 Something", text)          # and its contents list is not part of it
        body = c.document_text(d["lines"], set(self.stats["fragmented"]))
        self.assertIn("SOURCE: The provisions of Executive Order 12114 of Jan. 4, 1979, appear", body.replace("\n", " "))
        self.assertIn("SEC. 1. Arms.", "\n".join(l for _, _, l in self.by["EO:10860"]["lines"]))

    def test_dated_references(self):
        refs, where = c.dated_references(self.stream)
        self.assertEqual(dict(refs["EO:9397"]), {"1943-11-22": 1})
        self.assertEqual(dict(refs["EO:11000"]), {"1962-02-16": 1})

    def test_amendment_notes_counted(self):
        body = c.document_text(self.by["EO:8248"]["lines"], set())
        self.assertEqual(len(c.AMEND_NOTE_RE.findall(body)), 1)


class DispositionTable(unittest.TestCase):
    def test_columns_pairing_and_wrapped_lines(self):
        page = chunk_page(1060, [
            [56.2, 617.2, "10047\n"], [266.1, 617.2, "Publiclands\n"],
            [56.1, 610.5, "10048\n"], [266.1, 609.6, "Revokedby EO 12553\n"],
            [55.9, 603.3, "10049\n"], [265.5, 603.4, "Authority repealedby act of Oct.\n"], [368.6, 602.2, "12,\n"],
            [272.0, 596.2, "1949\n"], [288.1, 596.2, "(63Stat\n"], [307.1, 596.2, ". 839\n"], [320.8, 596.0, ")\n"],
            [56.1, 589.4, "10057 Amendedby EO 10087\n"], [327.5, 590.2, ",\n"], [333.4, 590.2, "p. 756\n"],
            [265.7, 589.0, "Codified\n"], [295.1, 589.0, "atChapter36\n"],
            [55.7, 582.4, "10070 AmendedEO 9975 Revokedby EO 10810\n"],
            [56.0, 575.4, "10071\n"], [126.0, 575.0, "Amendedby EO 10100, 10101,\n"], [266.0, 575.0, "Codifiedat 5 CFR 2.1\n"],
            [132.0, 568.4, "10102.\n"],
            [56.0, 561.4, "10072\n"], [126.0, 561.0, "Revoked in part by EO 10500\n"], [266.0, 561.0, "Hortatory\n"],
            [56.0, 554.4, "10073\n"], [266.0, 554.0, "Temporary\n"],
        ], printed=1049)
        rows, orphans = rows_of([page])
        self.assertEqual(orphans, [])
        self.assertEqual(rows["EO:10047"]["category"], "public_lands")
        self.assertEqual(rows["EO:10047"]["group"], "excluded_not_ended")
        self.assertEqual(rows["EO:10049"]["disposition"], "Authority repealedby act of Oct. 12, 1949 (63Stat. 839)")
        self.assertEqual(rows["EO:10049"]["acting"], ["act of Oct. 12, 1949"])
        self.assertEqual((rows["EO:10057"]["category"], rows["EO:10057"]["codified_chapter"], rows["EO:10057"]["codified_page"]),
                         ("codified_here", "36", "756"))
        r = rows["EO:10070"]
        self.assertEqual((r["amendments"], r["disposition"], r["category"], r["acting"]),
                         ("AmendedEO 9975", "Revokedby EO 10810", "revoked", ["EO:10810"]))
        self.assertEqual((rows["EO:10071"]["category"], rows["EO:10071"]["group"]), ("codified_elsewhere", "in_force_1989"))
        self.assertEqual(rows["EO:10071"]["amendments"], "Amendedby EO 10100, 10101, 10102.")
        self.assertEqual(rows["EO:10072"]["disposition"], "Hortatory")             # 'Revoked in part by' is an amendment
        self.assertEqual(rows["EO:10073"]["printed"], "1049")
        self.assertNotIn("EO:1049", rows)                                            # the page number is not a row

    def test_free_text_stays_with_its_row(self):
        page = chunk_page(1059, [
            [56.0, 376.0, "10012\n"], [266.0, 376.0, "Revokedby EO 10200\n"],
            [56.0, 369.5, "10013\n"], [126.0, 369.4, "Amendedby EO 10043..\n"], [267.1, 369.3, "CommitteeterminatedFeb. 28, 1951\n"],
            [56.0, 362.5, "10014\n"], [266.0, 362.0, "Temporary\n"],
        ])
        rows, _ = rows_of([page])
        self.assertEqual(rows["EO:10013"]["disposition"], "CommitteeterminatedFeb. 28, 1951")
        self.assertEqual(rows["EO:10013"]["category"], "free_text_ended")
        self.assertEqual(rows["EO:10014"]["disposition"], "Temporary")

    def test_italic_affected_list_is_not_a_disposition(self):
        page = chunk_page(1061, [
            [56.0, 400.0, "10100 RevokedEO 9000"], [266.0, 400.0, "Supersededby EO 10200"],
            [56.0, 393.0, "10101 RevokesEO 2458"],
        ])
        rows, _ = rows_of([page])
        self.assertEqual((rows["EO:10100"]["amendments"], rows["EO:10100"]["category"]), ("RevokedEO 9000", "superseded"))
        self.assertEqual(rows["EO:10101"]["category"], "revokes_other_document")

    def test_glued_numbers(self):
        page = chunk_page(1032, [
            [182.0, 470.0, "Executive Orders"],
            [55.5, 450.0, "5924...........5925\n"], [266.0, 450.0, "Revokedby EO 9830"], [266.0, 443.0, "Tariff"],
            [56.1, 436.0, "589\n"], [266.4, 436.0, "Revokedby EO 9000\n"],
            [67.2, 429.8, ".\n"], [266.8, 429.0, "Revokedby EO 8036641\n"],
            [56.1, 422.0, "653\n"], [266.0, 422.0, "Temporary11383"],
            [56.1, 415.0, "12000\n"], [266.0, 415.0, "Hortatory"],
            [55.6, 408.0, "9979\n"], [266.5, 408.0, "Revokedby EO 11051\n"],
            [266.5, 401.0, "Supersededby EO 105909980\n"],
            [55.6, 394.0, "9981\n"], [266.5, 394.0, "Temporary\n"],
            [126.6, 387.0, "Continuedby EO 10348\n"], [194.5, 387.0, "...9989\n"], [266.8, 387.0, "Supersededby EO 11281\n"],
            [55.7, 380.0, "9990\n"], [266.8, 380.0, "Temporary\n"],
        ])
        page2 = chunk_page(1033, [[56.0, 600.0, "11382"], [266.0, 600.0, "Temporary"], [56.0, 586.0, "11384"],
                                  [266.0, 586.0, "Temporary"], [266.0, 593.0, "Temporary11383"]])
        rows, orphans = rows_of([page, page2])
        self.assertIn("EO:5924", rows)
        self.assertEqual(rows["EO:5925"]["disposition"], "Tariff")             # two numbers glued into one chunk
        self.assertEqual(rows["EO:641"]["disposition"], "Revokedby EO 8036")    # row number glued onto its disposition
        self.assertEqual(rows["EO:9980"]["disposition"], "Supersededby EO 10590")
        self.assertEqual(rows["EO:9989"]["disposition"], "Supersededby EO 11281")  # glued onto the amendments chunk
        self.assertEqual(rows["EO:9989"]["amendments"], "Continuedby EO 10348")
        self.assertEqual(rows["EO:11383"]["disposition"], "Temporary")
        # 'Temporary11383' on page 1032 sits between 653 and 12000: 11383 does not fit there, so nothing is split off
        self.assertEqual(rows["EO:653"]["disposition"], "Temporary11383")
        self.assertEqual(orphans, [])

    def test_number_normalisation(self):
        page = chunk_page(1033, [
            [56.0, 400.0, "2245\n"], [266.0, 400.0, "Temporary"],
            [56.0, 393.0, "22452\n"], [126.0, 393.0, "Extendedby EOs 2405A"], [266.0, 393.0, "Executedandobsolete"],
            [56.0, 386.0, "2246..........\n"], [266.0, 386.0, "Temporary"],
            [56.0, 379.0, "2656A\n"], [266.0, 379.0, "Temporary"],
            [56.0, 372.0, "9.............\n"], [266.0, 372.0, "Revokedby EO 11408"],
            [56.0, 365.0, "9-2 .......................\n"], [266.0, 365.0, "Revokedby EO 11408"],
        ])
        rows, _ = rows_of([page], {"EO:2245½"})
        self.assertEqual(rows["EO:2245½"]["category"], "executed_obsolete")
        self.assertIn("half_read_as_2", rows["EO:2245½"]["flags"])
        self.assertNotIn("EO:22452", rows)
        self.assertIn("EO:2656A", rows)
        self.assertIn("EO:9-2", rows)
        self.assertIn("EO:9", rows)
        rows, _ = rows_of([page])          # without the census identity the number is kept, not guessed
        self.assertIn("EO:22452", rows)

    def test_unnumbered_date_rows(self):
        page = chunk_page(1032, [
            [182.0, 470.0, "Executive Orders"],
            [55.7, 425.5, "Feb. 9, 1849.\n"], [266.1, 426.0, "Supersededby EO 9761\n"],
            [55.9, 418.0, "Oct.26\n"], [76.2, 419.4, ", 1874\n"], [266.4, 418.5, "Public lands\n"],
            [77.5, 412.5, ", 1896\n"], [266.3, 410.8, "Revokedby EO 9521Dec. 31\n"],
            [55.7, 404.8, "Aug.\n"], [76.8, 404.1, "12,1898\n"], [266.3, 404.0, "Revokedby EO 8168\n"],
            [56.0, 397.0, "108A..................\n"], [266.4, 397.0, "Revokedby EO 10077\n"],
        ])
        rows, orphans = rows_of([page])
        self.assertEqual(sorted(k for k in rows if k.startswith("date:")),
                         ["date:1849-02-09", "date:1874-10-26", "date:1896-12-31", "date:1898-08-12"])
        self.assertEqual(rows["date:1896-12-31"]["disposition"], "Revokedby EO 9521")
        self.assertIn("month_day_swallowed_by_disposition", rows["date:1896-12-31"]["flags"])
        self.assertEqual(rows["date:1874-10-26"]["category"], "public_lands")
        self.assertEqual(rows["EO:108A"]["disposition"], "Revokedby EO 10077")
        self.assertEqual(orphans, [])

    def test_table_starts_under_heading_and_continues_across_pages(self):
        p1 = chunk_page(1032, [
            [56.0, 560.0, "5934"], [266.0, 560.0, "Hortatory"],      # proclamations, above the heading
            [182.0, 470.0, "Executive Orders"],
            [56.0, 450.0, "12553"], [266.0, 450.0, "Revokes EOs 723, 3577,"], [272.0, 443.0, "5491, 5918,"],
        ])
        p2 = chunk_page(1033, [[272.0, 612.0, "6359, 6558."], [56.0, 605.0, "12554"], [266.0, 605.0, "Temporary"]])
        rows, orphans = rows_of([p1, p2])
        self.assertNotIn("EO:5934", rows)
        self.assertEqual(rows["EO:12553"]["disposition"], "Revokes EOs 723, 3577, 5491, 5918, 6359, 6558.")
        self.assertIn("continued_on_next_page", rows["EO:12553"]["flags"])
        self.assertEqual(orphans, [])

    def test_unpaired_items_are_reported_not_guessed(self):
        page = chunk_page(1035, [
            [56.0, 446.0, "3555 AmendedEO 2932."], [266.8, 446.2, "Supersededby EOS 4027, 4125"],
            [266.8, 439.3, "Supersededby EOS 4027, 4125"], [126.1, 438.7, "AmendedEO 2932."],
            [56.0, 432.0, "3577"],
        ])
        rows, orphans = rows_of([page])
        self.assertEqual(rows["EO:3577"]["category"], "MISSING")
        self.assertEqual(rows["EO:3577"]["pairing_confidence"], "none")
        self.assertEqual(sorted(o["text"].split(":")[0] for o in orphans), ["AMENDMENTS_START", "DISPOSITION_START"])

    def test_categories_and_acting_documents(self):
        self.assertEqual(c.categorise("Supersedebdy EO 10300")[0], "superseded")
        self.assertEqual(c.categorise("Codifiedat Chapter 22, p. 382"), ("codified_here", "in_force_1989"))
        self.assertEqual(c.categorise("Codified at 22 U.S.C. 2751 note"), ("codified_elsewhere", "in_force_1989"))
        self.assertEqual(c.categorise("Selective Service")[1], "excluded_not_ended")
        self.assertEqual(c.categorise("Executedandobsolete")[0], "executed_obsolete")
        self.assertEqual(c.categorise("Authority maintained at departmental level")[0], "authority_maintained")
        self.assertEqual(c.acting_documents("Revokedby EOs 9521, 10697 and Proc. 2318; PLO 4588; Pub. L. 87-649"),
                         ["EO:9521", "EO:10697", "Proc:2318", "PLO:4588", "Pub.L.87-649"])


class EndToEnd(unittest.TestCase):
    def build(self, td, pdf_bytes=None):
        job, repo, out = td / "job", td / "repo", td / "out"
        (job / "data").mkdir(parents=True)
        (repo / "census").mkdir(parents=True)
        pages = [(i, "front") for i in range(1, 18)] + [(18, BODY_A), (19, BODY_B), (20, BODY_C), (21, BODY_D)]
        (job / "data" / "p.jsonl").write_text("".join(json.dumps({"page": p, "text": t}) + "\n" for p, t in pages),
                                              encoding="utf-8", newline="\n")
        tpage = chunk_page(1032, [
            [182.0, 470.0, "Executive Orders"],
            [55.7, 450.0, "Feb. 9, 1849."], [266.0, 450.0, "Supersededby EO 10860"],
            [56.0, 443.0, "6585"], [266.0, 443.0, "Revokedby EO 9000"],
            [56.0, 436.0, "8248"], [266.0, 436.0, "Codified at Chapter 3, p. 7"],
            [56.0, 429.0, "9000"], [266.0, 429.0, "Revokedby EO 10860"],
            [56.0, 422.0, "10860"], [266.0, 422.0, "Codified at Chapter 3, p. 8"],
            [56.0, 415.0, "12114"], [266.0, 415.0, "Codified at Chapter 3, p. 9"],
        ])
        (job / "data" / "t.jsonl").write_text(json.dumps(tpage) + "\n", encoding="utf-8", newline="\n")
        with open(repo / "census" / "c.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["id", "date_effective"])
            w.writerows([["EO:8248", "1939"], ["EO:9000", "1941"], ["EO:10860", "1961"], ["EO:12114", "1979"],
                         ["EO:9397", "1943"], ["EO:UN:x:row:1", ""]])
        with open(repo / "census" / "un.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["instrument_id", "reference_date", "editorial_category"])
            w.writerow(["EO:UN:x:row:1", "1849-02-09", "superseded_by_later_instrument"])
        with open(repo / "census" / "r.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["instrument_id", "provisional_status", "step_original_text", "step_ending_or_current_basis"])
            w.writerows([["EO:8248", "no", "open", "open"], ["EO:9000", "yes", "done", "open"]])
        pdf_path = "missing.pdf"
        if pdf_bytes is not None:
            (repo / "book.pdf").write_bytes(pdf_bytes)
            pdf_path = "book.pdf"
        prov = {"census": "census/c.csv", "readiness": "census/r.csv", "unnumbered_rows": "census/un.csv",
                "lord_leads": "none.csv", "later_events_edges": "none.csv",
                "book": {"title": "t", "short": "T", "published": "p", "digitized_by": "d", "handle_url": "https://h",
                         "pdf": pdf_path, "pdf_sha256": hashlib.sha256(b"%PDF real").hexdigest(),
                         "text": "data/p.jsonl", "text_sha256": hashlib.sha256((job / "data" / "p.jsonl").read_bytes()).hexdigest(),
                         "table_chunks": "data/t.jsonl",
                         "table_chunks_sha256": hashlib.sha256((job / "data" / "t.jsonl").read_bytes()).hexdigest(),
                         "extractor": "x",
                         "layout": {"contents_pdf_pages": [8, 10], "body_pdf_pages": [18, 21], "printed_page_offset": 11,
                                    "complete_eo_run": [8248, 8248]}}}
        (job / "data" / "PROVENANCE.json").write_text(json.dumps(prov), encoding="utf-8")
        return job, repo, out, prov

    def test_small_book_against_a_small_census(self):
        with tempfile.TemporaryDirectory() as td:
            job, repo, out, prov = self.build(pathlib.Path(td))
            s = c.run(repo, job, out)
            self.assertEqual(s["pdf_check"], "pdf_not_checked_out")
            self.assertEqual(s["body"]["eo_source_lines"], 3)
            with open(out / "CODIFIED_1989.csv", encoding="utf-8") as fh:
                cod = {r["instrument_id"]: r for r in csv.DictReader(fh)}
            self.assertEqual(cod["EO:8248"]["checks"], "decided_NO_but_codified_in_force_1989")
            self.assertEqual(cod["EO:10860"]["census"], "YEAR_CONFLICT")
            text = (out / cod["EO:8248"]["text_path"]).read_text(encoding="utf-8")
            self.assertIn("NOT THE ORIGINAL TEXT", text)
            body = text.split("\n\n", 1)[1]
            self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), cod["EO:8248"]["text_sha256"])
            with open(out / "CENSUS_LEADS.csv", encoding="utf-8") as fh:
                leads = {(r["instrument_id"], r["lead"]) for r in csv.DictReader(fh)}
            self.assertIn(("EO:8248", "EXACT_DATE_FROM_SOURCE_LINE_CENSUS_YEAR_ONLY"), leads)
            self.assertIn(("EO:10860", "YEAR_CONFLICT_SOURCE_LINE"), leads)
            self.assertIn(("EO:6585", "NOT_IN_CENSUS_DISPOSITION_TABLE"), leads)
            self.assertIn(("EO:9397", "EXACT_DATE_FROM_DATED_REFERENCE_CENSUS_YEAR_ONLY"), leads)
            self.assertIn(("EO:UN:x:row:1", "UNNUMBERED_ROW_DATE_FOR_BLANK_CENSUS_DATE"), leads)
            with open(out / "STATUS_LEADS.csv", encoding="utf-8") as fh:
                st = {(r["census_id"], r["lead"]) for r in csv.DictReader(fh)}
            self.assertEqual(st, {("EO:8248", "DECIDED_NO_BUT_IN_FORCE_1989_NO_LATER_ENDING_IN_LATER_EVENTS"),
                                  ("EO:9000", "DECIDED_YES_BUT_ENDED_BY_1989"),
                                  ("EO:10860", "UNDECIDED_IN_FORCE_1989"), ("EO:12114", "UNDECIDED_IN_FORCE_1989"),
                                  ("EO:UN:x:row:1", "UNDECIDED_ENDED_BY_1989")})
            with open(out / "FRAGMENTS.jsonl", encoding="utf-8") as fh:
                frags = [json.loads(l) for l in fh]
            self.assertEqual({f["kind"] for f in frags}, {"later_event_candidates"})   # never original_representation
            self.assertEqual(sorted(f["instrument_id"] for f in frags), ["EO:9000", "EO:UN:x:row:1"])  # census ids only
            item = next(f for f in frags if f["instrument_id"] == "EO:9000")["data"][0]
            self.assertEqual((item["actor"], item["mechanism"], item["date_candidate"]), ("EO:10860", "revocation", "1960-02-05"))
            self.assertEqual(item["evidence_types"], ["ofr_codification_1989_table"])
            # a changed text layer stops the job
            prov["book"]["text_sha256"] = "f" * 64
            (job / "data" / "PROVENANCE.json").write_text(json.dumps(prov), encoding="utf-8")
            with self.assertRaises(SystemExit):
                c.run(repo, job, out)

    def test_pdf_checks(self):
        with tempfile.TemporaryDirectory() as td:
            job, repo, out, _ = self.build(pathlib.Path(td), b"version https://git-lfs.github.com/spec/v1\noid sha256:ab\n")
            self.assertEqual(c.run(repo, job, out)["pdf_check"], "pdf_is_lfs_pointer_text_layer_hash_verified")
        with tempfile.TemporaryDirectory() as td:
            job, repo, out, _ = self.build(pathlib.Path(td), b"%PDF real")
            self.assertEqual(c.run(repo, job, out)["pdf_check"], "match")
        with tempfile.TemporaryDirectory() as td:
            job, repo, out, _ = self.build(pathlib.Path(td), b"%PDF other")
            with self.assertRaises(SystemExit):
                c.run(repo, job, out)


class CommittedBook(unittest.TestCase):
    """Regression guard on the committed text layer and table chunks (measured 2026-10-17)."""

    @classmethod
    def setUpClass(cls):
        prov = json.loads((HERE / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
        b = cls.book = prov["book"]
        for key in ("text", "table_chunks"):
            assert hashlib.sha256((HERE / b[key]).read_bytes()).hexdigest() == b[key + "_sha256"]
        lay = b["layout"]
        stream, cls.stats = c.body_stream(c.load_pages(HERE / b["text"]), *lay["body_pdf_pages"], lay["printed_page_offset"])
        cls.docs, _ = c.find_documents(stream)
        with open(HERE / b["table_chunks"], encoding="utf-8") as fh:
            pages = [json.loads(l) for l in fh]
        rows, cls.orphans, _ = c.parse_table(pages, {"EO:2245½"}, lay["printed_page_offset"])
        cls.rows = rows
        cls.by = {}
        for r in rows:
            cls.by.setdefault(r["key"], r)

    def test_source_line_counts(self):
        eo = [d for d in self.docs if d["kind"] == "EO"]
        self.assertEqual((len(eo), len(self.docs) - len(eo)), (555, 47))
        self.assertEqual(len({d["instrument_id"] for d in eo}), 555)
        self.assertEqual([d["instrument_id"] for d in eo if not d["date"]], ["EO:10631"])
        self.assertTrue(all(d["heading_found"] for d in self.docs))
        by = {d["instrument_id"]: d for d in eo}
        self.assertEqual((by["EO:8248"]["date"], by["EO:8248"]["fr_citation"]), ("1939-09-08", "4 FR 3864"))
        self.assertEqual(by["EO:1888"]["not_in_fr_system"], "yes")
        self.assertEqual(by["EO:10879"]["restated"], "revised and restated")
        self.assertEqual(len(self.stats["fragmented"]), 151)

    def test_disposition_rows(self):
        self.assertEqual(len(self.rows), 4224)
        self.assertEqual(sum(1 for r in self.rows if r["key"].startswith("date:")), 18)
        self.assertEqual(sum(1 for r in self.rows if not r["disposition"]), 0)
        self.assertEqual(len(self.orphans), 2)
        self.assertEqual(self.by["EO:10047"]["category"], "public_lands")
        # The assessor's note put 'Codified at Chapter 36, p. 756' on 10059; the chunks and the body put it on 10057
        # (EO 10057's SOURCE line is on printed page 756). 10059's own row reads 'Authority repealed by act of Oct. 12, 1949'.
        self.assertEqual((self.by["EO:10057"]["codified_chapter"], self.by["EO:10057"]["codified_page"]), ("36", "756"))
        self.assertTrue(self.by["EO:10059"]["disposition"].startswith("Authority repealedby act of Oct. 12, 1949"))
        self.assertEqual(self.by["EO:10013"]["disposition"], "CommitteeterminatedFeb. 28, 1951")
        self.assertEqual(self.by["EO:10070"]["disposition"], "Revokedby EO 10810")
        self.assertEqual(self.by["EO:2245½"]["category"], "executed_obsolete")
        self.assertIn("EO:9-2", self.by)
        self.assertNotIn("EO:22452", self.by)

    def test_invariants(self):
        body = {d["instrument_id"] for d in self.docs}
        cod = {r["key"] for r in self.rows if r["category"] == "codified_here"}
        self.assertEqual(cod - body, set())
        nums = {c.key_number(r["key"]) for r in self.rows if r["key"].startswith("EO:")}
        # Four numbers are absent from the OCR of the table itself (their neighbours' rows are contiguous).
        self.assertEqual([n for n in range(9538, 12668) if n not in nums], [10217, 10275, 10288, 10595])
        keys = [r["key"] for r in self.rows if r["key"].startswith("EO:")]
        self.assertEqual(len(keys), len(set(keys)))


if __name__ == "__main__":
    unittest.main()
