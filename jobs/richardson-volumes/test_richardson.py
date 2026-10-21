import csv
import hashlib
import json
import pathlib
import shutil
import tempfile
import unittest

import richardson as R

HERE = pathlib.Path(__file__).resolve().parent
PROV = json.loads((HERE / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
REPO = HERE.parent.parent
CENSUS = REPO / PROV["census"]


def vol(**kw):
    v = {"key": "T", "volume": "IX", "short": "t", "title": "t", "published": "p", "digitized_by": "d", "handle_url": "u",
         "pdf": "missing.pdf", "pdf_sha256": "0" * 64, "extractor": "x", "years": [1889, 1897], "span": ["1889-03-04", "1897-03-04"],
         "president_heads": ["Benjamin Harrison", "Grover Cleveland"],
         "signatures": [{"name": "BENJ. HARRISON", "printed": [1, 386]}, {"name": "GROVER CLEVELAND", "printed": [387, 801]}],
         "page_offsets": [[1, 900, 23]], "order_sections": ["EXECUTIVE ORDER"], "contents_order_sections": []}
    v.update(kw)
    return v


def lines_of(text):
    return [l for l in text.strip("\n").split("\n")]


def units(text, v=None, printed=100):
    v = v or vol()
    lines = lines_of(text)
    sig = R.sig_regex(v, printed)
    out = []
    for u in R.segment(v, lines, sig):
        span = lines[u["start"]:u["end"]]
        date = R.date_document(span, dict(u, lines_all=span, dateline=None if u["dateline"] is None else u["dateline"] - u["start"],
                                         closings=[(c - u["start"], m) for c, m in u["closings"]]), sig)
        out.append({"lines": span, "date": date[0], "date_from": date[1], "nested": u["nested"]})
    return out


class PagesAndSections(unittest.TestCase):
    def test_running_heads_with_ocr_digits(self):
        v = vol()
        pages = [(124, "ΙΟΙ Messages and Papers ofthe Presidents\ntext"), (434, "4II Messages and Fapers of the Presidents\ntext"),
                 (754, "Grover Cleveland · 731\ntext"), (559, "5.36 Messages and Papers of the Presidents\ntext"),
                 (467, "444 . Messages and Papers ofthe Presidents\ntext"), (125, "Benjamin Harrison 999\ntext")]
        pm, st = R.page_map(v, pages)
        self.assertEqual((pm[124], pm[434], pm[754]), (101, 411, 731))
        self.assertEqual((st["heads_read"], st["heads_agree"], st["heads_disagree"]), (6, 5, 1))  # 999 is not 102

    def test_page_furniture(self):
        v = vol()
        page = ("Benjamin Harrison 27\nT\nAMENDMENT OF CIVIL - SERVICE RULES .\nApproved , May 5 , 1892 .\n"
                "M P-VOL IX-5\nBENJ . HARRISON .\n*\n27")
        stream, dropped = R.body_stream(v, [(50, page)], {50: 27})
        self.assertEqual([l for _, _, l in stream], ["AMENDMENT OF CIVIL - SERVICE RULES .", "Approved , May 5 , 1892 .", "BENJ . HARRISON ."])
        self.assertEqual(dropped["sheet_signature"], 1)

    def test_sections_title_page_and_in_section_heading(self):
        v = vol()
        text = ["PROCLAMATIONS .", "a proclamation", "EXECUTIVE ORDERS .", "EXECUTIVE MANSION , May 4 , 1892 .", "order one",
                "BENJ . HARRISON .", "BY THE PRESIDENT OF THE UNITED STATES .", "EXECUTIVE ORDER .", "order two", "BENJ . HARRISON .",
                "Grover Cleveland", "March 4 , 1893 , to March 4 , 1897", "INAUGURAL ADDRESS ."]
        stream = [(1, 10 + i, l) for i, l in enumerate(text)]
        secs = R.find_sections(v, stream)
        self.assertEqual([s["name"] for s in secs], ["PROCLAMATIONS", "EXECUTIVE ORDERS", "TITLE PAGE", "INAUGURAL ADDRESS"])
        eo = secs[1]
        self.assertEqual([l for _, _, l in stream[eo["start"]:eo["end"]]][-1], "BENJ . HARRISON .")  # stops at the title page

    def test_title_page_head_is_kept(self):
        stream, _ = R.body_stream(vol(), [(410, "Grover Cleveland\nMarch 4 , 1893 , to March 4 , 1897\n387")], {410: 387})
        self.assertEqual(stream[0][2], "Grover Cleveland")

    def test_fragmented_page_uses_the_raw_layer(self):
        broken = "Ulysses S. Grant 183\n" + "\n".join(["a", "b c"] * 15)
        self.assertTrue(R.is_fragmented(broken))
        raw = ("Ulysses S. Grant 183\nof the rules .\nEXECUTIVE MANSION\n,\nWashington\n,\nMay\n27\n,\n1872\n.\nSIR\n:\n"
               "The President directs me\nto\nsay that the Departments\nwill\nbe closed .\nDEPARTMENT OF STATE\n"
               ", Washington , October 11 , 1872 . The undersigned is charged\nby the President .")
        pages, used = R.best_layer([(208, broken)], [(208, raw)])
        self.assertEqual(used, [208])
        got = pages[0][1].split("\n")
        self.assertIn("DEPARTMENT OF STATE , Washington , October 11 , 1872 . The undersigned is charged by the President .", got)
        self.assertTrue(any(l.startswith("The President directs me to say that") for l in got))


class Documents(unittest.TestCase):
    def test_president_comma_president_ends_a_document(self):
        u = units("""AMENDMENT OF CIVIL- SERVICE RULES .
EXECUTIVE MANSION ,
Washington , D. C. , May 16 , 1895 .
Special Departmental Rule No. I is hereby amended as follows :
6. In the Department of Agriculture : The chief of the dairy division .
Approved , May 24 , 1895 .
GROVER CLEVELAND , President .
CIVIL SERVICE .-EXECUTIVE ORDER REVOKED .
EXECUTIVE MANSION , May 24 , 1895.
The Executive order heretofore issued is hereby revoked .
Approved : GROVER CLEVELAND .""", printed=612)
        self.assertEqual(len(u), 2)
        self.assertEqual((u[0]["date"], u[0]["date_from"]), ("1895-05-24", "approval"))  # approval beats the May 16 letterhead
        self.assertTrue(u[1]["lines"][0].startswith("CIVIL SERVICE"))

    def test_body_line_naming_a_secretary_does_not_end_a_document(self):
        u = units("""EXECUTIVE MANSION , June 7 , 1889 .
Funds will be paid on requisition by the Secretary of the Treasury.
The order takes effect at once .
BENJ . HARRISON .""", printed=29)
        self.assertEqual(len(u), 1)

    def test_letter_signed_by_a_cabinet_officer_ends_before_the_next_order(self):
        u = units("""DEPARTMENT OF STATE ,
Washington , January 30 , 1891 .
The President directs that the Departments be draped for Secretary Windom .
Very respectfully ,
JAMES G. BLAINE .
EXECUTIVE MANSION , February 13 , 1891 .
Admiral David D. Porter is dead ; the flags will be at half-mast .
BENJ . HARRISON .""", printed=164)
        self.assertEqual([x["date"] for x in u], ["1891-01-30", "1891-02-13"])

    def test_countersignature_is_absorbed_but_never_the_next_dateline(self):
        u = units("""EXECUTIVE MANSION , July 6 , 1891 .
It is ordered that the offices be closed .
BENJ . HARRISON .
By the President :
WILLIAM F. WHARTON ,
Acting Secretary of State.
EXECUTIVE MANSION , July 8 , 1891 .
Another order .
BENJ . HARRISON .""", printed=174)
        self.assertEqual(len(u), 2)
        self.assertEqual(u[0]["lines"][-1], "Acting Secretary of State.")

    def test_addressee_under_a_dateline_is_not_a_signature(self):
        u = units("""WAR DEPARTMENT , January 22 , 1862 .
EDWIN M. STANTON ,
Secretary of War .
The President directs that the armies move forward on the 22d of February next , and that every
commander be ready for the movement in time .
ABRAHAM LINCOLN .""", v=vol(signatures=[{"name": "ABRAHAM LINCOLN", "printed": [1, 297]}]), printed=100)
        self.assertEqual(len(u), 1)

    def test_ocr_day_and_bare_caps_date_after_a_signature(self):
        u = units("""CIVIL SERVICE .-REVOCATION OF PROMOTION REGULATIONS .
• DECEMBER II , 1893 .
The regulations are revoked .
GROVER CLEVELAND .
SEPTEMBER 16 , 1894 .
The Departments will be closed .
GROVER CLEVELAND .""", printed=513)
        self.assertEqual([x["date"] for x in u], ["1893-12-11", "1894-09-16"])

    def test_dates_inside_prose_and_weekdays_are_not_datelines(self):
        u = units("""GENERAL ORDERS , NO . 1 .
WAR DEPARTMENT ,
Washington , January 4 , 1870 .
The order dated
Washington , December 24 , 1869 .
is countermanded , and on
Thursday , June 13 , 1861 . the troops will parade .
By command of General Sherman :
E. D. TOWNSEND ,
Adjutant - General .""", printed=94)
        self.assertEqual(len(u), 1)
        self.assertEqual(u[0]["date"], "1870-01-04")

    def test_marcharch_and_a_dateline_after_an_ocr_speck(self):
        u = units("""SPECIAL ORDERS , NO . 55 .
HEADQUARTERS OF THE ARMY ,
ADJUTANT - GENERAL'S OFFICE ,
Washington , Marcharch 9 , 1869 .
6. By direction of the President , Brevet Major-General Ames is assigned to command .
E. D. TOWNSEND ,
Assistant Adjutant - General .
T
TREASURY DEPARTMENT , March 9 , 1875 .
The board of examiners is abolished .
B. H. BRISTOW , Secretary.""", printed=21)
        self.assertEqual([x["date"] for x in u], ["1869-03-09", "1875-03-09"])

    def test_the_civil_service_act_date_in_the_body_is_never_the_order_date(self):
        u = units("""AMENDMENT OF CIVIL - SERVICE RULES .
In pursuance of the act approved January 16 , 1883 , General Rule III is hereby amended .
BENJ . HARRISON .""", printed=30)
        self.assertEqual(u[0]["date"], "")

    def test_seal_inside_the_day_clause(self):
        u = units("""Major -General H. W. HALLECK ,
Commanding in the Department of the Missouri :
You are authorized to suspend the writ of habeas corpus .
Given under my hand , at the city of Washington , this 2d day of[SEAL .] December , A. D. 1861 .
ABRAHAM LINCOLN .""", v=vol(signatures=[{"name": "ABRAHAM LINCOLN", "printed": [1, 297]}]), printed=99)
        self.assertEqual((u[0]["date"], u[0]["date_from"]), ("1861-12-02", "day_of_clause"))

    def test_closing_approval_after_a_commission_signature_stays_with_it(self):
        u = units("""AMENDMENT OF CIVIL - SERVICE RULES .
UNITED STATES CIVIL SERVICE COMMISSION ,
Washington , D. C. , January 12 , 1892 .
The Commission recommends that Rule III be amended .
CHARLES LYMAN ,
THEODORE ROOSEVELT ,
Commissioners .
EXECUTIVE MANSION , January 25 , 1892 .
The foregoing amendment is approved .
BENJ . HARRISON .""", printed=302)
        self.assertEqual(len(u), 1)
        self.assertEqual(u[0]["date"], "1892-01-25")

    def test_bare_approval_date_followed_by_the_signature(self):
        u = units("""RULES GOVERNING APPOINTMENT AND PROMOTION IN THE NEW YORK POST - OFFICE .
I. Every application must be in writing .
THOMAS L. JAMES , Postmaster .
The foregoing rules are approved .
APRIL 3 , 1879 .
R. B. HAYES .""", v=vol(signatures=[{"name": "R. B. HAYES", "printed": [437, 640]}]), printed=555)
        self.assertEqual(len(u), 1)
        self.assertEqual((u[0]["date"], u[0]["date_from"]), ("1879-04-03", "approval"))

    def test_order_printed_inside_general_orders_is_flagged(self):
        u = units("""GENERAL ORDERS , NO . 4.
HEADQUARTERS OF THE ARMY ,
Washington , January 19 , 1893 .
I. The following proclamation [order ] has been received from the President :
EXECUTIVE MANSION ,
Washington , D. C. , January 18, 1893 .
The death of Rutherford B. Hayes is announced ; flags will be at half-mast .
BENJ . HARRISON .
II. On the day of the funeral the troops will parade .
By command of Major - General Schofield :
R. WILLIAMS , Adjutant- General .""", printed=383)
        self.assertEqual([x["date"] for x in u], ["1893-01-19", "1893-01-18", ""])
        self.assertTrue(u[1]["nested"])

    def test_rules_published_herewith_stay_with_the_order(self):
        u = units("""WASHINGTON , August 5, 1873 .
These rules as herewith published are approved .
U. S. GRANT .
By the President :
HAMILTON FISH ,
Secretary of State .
FURTHER RULES FOR PROMOTING THE EFFICIENCY OF THE CIVIL SERVICE .
Rule 1.-Recommendations must be in writing .
Rule 2.-No removal for the mere purpose of making a place .""",
                  v=vol(signatures=[{"name": "U. S. GRANT", "printed": [1, 436]}]), printed=230)
        self.assertEqual(len(u), 1)
        self.assertIn("Rule 2.-No removal for the mere purpose of making a place .", u[0]["lines"])


class OrdersOutsideSections(unittest.TestCase):
    def test_order_quoted_in_a_message(self):
        v = vol(page_offsets=[[1, 5, 0]])
        pages = [(3, "SPECIAL MESSAGES .\nEXECUTIVE MANSION , December 23 , 1891 .\nTo the Senate and House of Representatives :\n"
                     "My attention having been called to the spelling of geographic names , the following Executive order was issued on the 4th\n"
                     "day of September , 1890 :\nI hereby constitute a Board on Geographic Names .\nThe report is transmitted herewith .\n"
                     "BENJ . HARRISON .")]
        pm, _ = R.page_map(v, pages)
        docs, _, _, _ = R.volume_documents(v, pages, pm)
        q = [d for d in docs if d["kind"] == "in_message"]
        self.assertEqual(len(q), 1)
        self.assertEqual((q[0]["date"], q[0]["date_from"], q[0]["confidence"]), ("1890-09-04", "message_introduction", "medium"))


class Lists(unittest.TestCase):
    def test_wpa_merged_rows_are_split(self):
        rows = [{"id": "EO:28", "number": "28", "suffix": "", "year": "1890", "month_day": "Sept 4", "citations_joined": "IX R 164",
                 "text": "Board on Geographic Names established. 28-1:Jan. 30 * Mourning for William Windom. IX R 164."},
                {"id": "EO:35", "number": "35", "suffix": "", "year": "1894", "month_day": "Nov 2", "citations_joined": "IX R 519 | IX R 520",
                 "text": "Rule amended. IX R 519. 36, 37: Nov. 2 Rules amended. IX R 520. 92-92-3: Nov. 2 More rules. IX R 520. 40-42 : Nov. 2 x"}]
        rows.append({"id": "EO:9", "number": "9", "suffix": "", "year": "1873", "month_day": "Jan 17", "citations_joined": "VII R 219",
                     "text": "Federal employees may not hold State offices. VII E 218. 9-2: Jan. 28 Order of Jan. 17 clarified. VII R 219."})
        items = {i["entry"]: i for i in R.wpa_items(rows)}
        self.assertEqual((items["EO:9"]["cits"], items["EO:9-2"]["cits"]), ([("VII", 218, None)], [("VII", 219, None)]))
        self.assertEqual(items["EO:28"]["cits"], [])
        self.assertEqual(items["EO:28"]["moved"], [("IX", 164, "EO:28-1")])  # the parsed row gave 28-1's citation to EO 28
        self.assertEqual((items["EO:28-1"]["iso"], items["EO:28-1"]["cits"], items["EO:28-1"]["split"]), ("1890-01-30", [("IX", 164, None)], True))
        self.assertTrue({"EO:36", "EO:37", "EO:92", "EO:92-1", "EO:92-2", "EO:92-3", "EO:40", "EO:41", "EO:42"} <= set(items))
        self.assertEqual(items["EO:92-3"]["cits"], [("IX", 520, None)])

    def test_lord_citations_ocr_and_swallowed_rows(self):
        rows = [{"seq": "414", "year": "1872", "date": "May 27", "pairing": "paired", "page": "1", "citations_joined": "",
                 "summary": "Departments closed for Decoration Day . VII Richarăson 183", "citation_text": ""},
                {"seq": "142", "year": "1865", "date": "", "pairing": "uncertain", "page": "1", "citations_joined": "",
                 "summary": "Trade restrictions removed", "citation_text": "VI kichardson 335"},
                {"seq": "1014", "year": "1895", "date": "", "pairing": "uncertain", "page": "1", "citations_joined": "IX Richardson 612",
                 "summary": "Executive order on four clerks revoked . IX Richardson 612 Classified service in the Agriculture "
                            "Department amended to include microscopists and taggers", "citation_text": ""}]
        items = R.lord_items(rows)
        got = [(i["entry"], i["cits"][0][:2], i["iso"]) for i in items]
        self.assertEqual(got, [("Lord:414", ("VII", 183), "1872-05-27"), ("Lord:142", ("VI", 335), ""),
                               ("Lord:1014a", ("IX", 612), ""), ("Lord:1014b", ("IX", 612), "")])
        self.assertTrue(items[3]["summary"].startswith("Classified service"))


def doc(i, date, pages, text, signer="president", last=None, n=10, **kw):
    lines = text.split("\n")
    d = {"doc_id": i, "is_order": True, "date": date, "date_dateline": date, "date_approval": "", "datelines_all": date,
         "printed_first": pages[0], "printed_last": pages[1], "lines": lines, "signer": signer,
         "last_line": last or lines[-1], "n_lines": n}
    d.update(kw)
    return d


class Matching(unittest.TestCase):
    def setUp(self):
        docs = [doc("A", "1894-11-02", (519, 519), "Departmental Rule VIII is amended for messengers and watchmen"),
                doc("B", "1894-11-02", (519, 520), "Postal Rule IV is amended for railway clerks and firemen"),
                doc("C", "1875-11-22", (331, 331), "WAR DEPARTMENT\nthe following order of the President of the United States :", signer="by_direction_of_president", n=6),
                doc("D", "1875-11-22", (331, 331), "Henry Wilson , Vice-President , died ; mourning ordered", signer="department_or_other"),
                doc("E", "1894-07-09", (518, 518), "Fish culturists withdrawn from competitive examination"),
                doc("F", "1892-01-25", (302, 303), "Rule III amended for the Indian service"),
                doc("G", "1890-05-01", (400, 400), "board appointed for lighthouses"),
                doc("H", "1890-05-01", (400, 400), "board appointed for lighthouses and buoys")]
        self.m = R.Matcher(vol(), docs, (3, 801))

    def test_date_and_page(self):
        self.assertEqual(self.m.resolve(518, "1894-07-09", "")[:3], ("match", "date_and_page", ["E"]))

    def test_same_date_split_by_the_named_rule(self):
        self.assertEqual(self.m.resolve(519, "1894-11-02", "Postal Rule No. 4 amended")[:3], ("match", "date_page_and_subject", ["B"]))

    def test_general_orders_wrapper_loses_to_the_order(self):
        self.assertEqual(self.m.resolve(331, "1875-11-22", "Mourning for Henry Wilson")[2], ["D"])

    def test_never_forced(self):
        self.assertEqual(self.m.resolve(400, "1890-05-01", "board appointed")[0], "ambiguous")
        self.assertEqual(self.m.resolve(400, "", "")[0], "ambiguous")
        self.assertEqual(self.m.resolve(900, "1890-05-01", "")[:2], ("unmatched", "page_outside_volume"))

    def test_list_year_one_off_and_wrong_page(self):
        self.assertEqual(self.m.resolve(518, "1893-07-09", "fish culturists withdrawn from examination")[:3],
                         ("match", "subject_list_year_wrong", ["E"]))
        self.assertEqual(self.m.resolve(202, "1892-01-25", "")[:3], ("match", "date_on_other_page", ["F"]))


def write_fixture_repo(td):
    job, repo, out = td / "job", td / "repo", td / "out"
    (job / "data" / "lists").mkdir(parents=True)
    (repo / "census").mkdir(parents=True)
    page1 = ("27 Messages and Papers of the Presidents\nEXECUTIVE ORDERS .\nAMENDMENT OF CIVIL - SERVICE RULES .\n"
             "EXECUTIVE MANSION , April 17 , 1889 .\nSpecial Departmental Rule No. 1 is hereby amended for the inspector of furniture .\n"
             "BENJ . HARRISON .\nEXECUTIVE MANSION , May 29 , 1889 .\nThe several Executive Departments will be closed on the 30th instant "
             "to enable the employees to decorate the graves .\nBENJ . HARRISON .")
    page2 = "Benjamin Harrison 28\nPROCLAMATIONS .\nA proclamation ."
    pages = [(i, "front") for i in range(1, 50)] + [(50, page1), (51, page2)]
    (job / "data" / "v.jsonl").write_text("".join(json.dumps({"page": p, "text": t}) + "\n" for p, t in pages), encoding="utf-8", newline="\n")
    (job / "data" / "raw.jsonl").write_text("", encoding="utf-8")
    with open(job / "data" / "lists" / "NUMBERED_ENTRIES.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "number", "suffix", "year", "month_day", "page", "family_hint", "has_form_of_proclamation", "source_kinds_joined",
                    "citations_joined", "text"])
        w.writerow(["EO:30", "30", "", "1889", "Apr 17", "1", "", "", "R", "IX R 27", "Special Departmental Rule 1 amended. IX R 27."])
        w.writerow(["EO:31", "31", "", "1889", "Aug 1", "1", "", "", "R", "IX R 27", "Something else. IX R 27."])
    with open(job / "data" / "lists" / "UNNUMBERED_ENTRIES.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["seq", "year", "date", "pairing", "page", "family_hint", "source_kinds_joined", "citations_joined", "summary", "citation_text"])
        w.writerow(["900", "1889", "May 29", "paired", "1", "", "", "IX Richardson 27", "Departments closed for Decoration Day", ""])
    with open(repo / "census" / "c.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "date_effective"])
        w.writerows([["EO:30", "1889"], ["EO:32", "1889"]])
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    v = vol(text="data/v.jsonl", text_sha256=sha(job / "data" / "v.jsonl"), raw_text="data/raw.jsonl", raw_text_sha256=sha(job / "data" / "raw.jsonl"),
            page_offsets=[[26, 60, 23]], contents_order_sections=[[27, 27]], pdf="book.pdf")
    prov = {"census": "census/c.csv", "readiness": "none.csv", "wpa_lists": "nowhere",
            "lists_fallback": {"dir": "data/lists", "sha256": {n: sha(job / "data" / "lists" / n) for n in ("NUMBERED_ENTRIES.csv", "UNNUMBERED_ENTRIES.csv")}},
            "volumes": [v]}
    (job / "data" / "PROVENANCE.json").write_text(json.dumps(prov), encoding="utf-8")
    return job, repo, out, prov


class EndToEnd(unittest.TestCase):
    def test_small_volume_against_a_small_census(self):
        with tempfile.TemporaryDirectory() as td:
            job, repo, out, prov = write_fixture_repo(pathlib.Path(td))
            (repo / "book.pdf").write_text("version https://git-lfs.github.com/spec/v1\noid sha256:00\nsize 1\n", encoding="utf-8")
            s = R.run(repo, job, out)
            v = s["volumes"][0]
            self.assertEqual((v["orders"], v["pdf_check"], s["lists"]["source"]), (2, "pdf_is_lfs_pointer_text_layer_hash_verified",
                                                                                     "committed subset (wpa-lists output absent)"))
            with open(out / "CITATIONS.csv", encoding="utf-8") as fh:
                cites = {r["entry"]: (r["status"], r["doc_dates"]) for r in csv.DictReader(fh)}
            self.assertEqual(cites, {"EO:30": ("match", "1889-04-17"), "EO:31": ("unmatched", ""), "Lord:900": ("match", "1889-05-29")})
            with open(out / "CENSUS_LEADS.csv", encoding="utf-8") as fh:
                leads = {(r["instrument_id"], r["lead"]) for r in csv.DictReader(fh)}
            self.assertIn(("EO:30", "DATE_FILL"), leads)
            self.assertIn(("EO:32", "IN_CENSUS_NOT_FOUND_IN_VOLUME"), leads)
            self.assertIn(("", "NOT_IN_CENSUS_unnumbered"), leads)
            with open(out / "FRAGMENTS.jsonl", encoding="utf-8") as fh:
                frags = [json.loads(l) for l in fh]
            self.assertEqual([f["instrument_id"] for f in frags], ["EO:30"])  # census ids only
            self.assertFalse(frags[0]["data"]["location_verified"])
            self.assertIn("NOT the signed original", frags[0]["confidence_note"])
            body = (out / frags[0]["data"]["text_path"]).read_text(encoding="utf-8").split("\n\n", 1)[1]
            self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), frags[0]["data"]["body_sha256"])
            self.assertEqual(hashlib.sha256((out / frags[0]["data"]["text_path"]).read_bytes()).hexdigest(), frags[0]["data"]["text_sha256"])
            self.assertTrue((out / "pages" / "T" / "p027.txt").exists())
            prov["volumes"][0]["text_sha256"] = "f" * 64
            (job / "data" / "PROVENANCE.json").write_text(json.dumps(prov), encoding="utf-8")
            with self.assertRaises(SystemExit):
                R.run(repo, job, out)

    def test_wrong_pdf_bytes_stop_the_run(self):
        with tempfile.TemporaryDirectory() as td:
            job, repo, out, prov = write_fixture_repo(pathlib.Path(td))
            (repo / "book.pdf").write_bytes(b"%PDF-1.4 not the book")
            with self.assertRaises(SystemExit):
                R.run(repo, job, out)


def committed(key):
    v = next(x for x in PROV["volumes"] if x["key"] == key)
    pages, _ = R.best_layer(R.load_pages(HERE / v["text"]), R.load_pages(HERE / v["raw_text"]))
    return v, pages


class CommittedVolumes(unittest.TestCase):
    """Regression guard on the committed text layers of vols. VI, VII and IX."""

    def test_text_layers_and_page_maps(self):
        want = {"RICH_VI": (751, {61: 36, 147: 122, 362: 333, 787: 758}), "RICH_VII": (632, {100: 75, 469: 440}),
                "RICH_IX": (792, {26: 3, 824: 801})}
        v = next(x for x in PROV["volumes"] if x["key"] == "RICH_VII")
        _, used = R.best_layer(R.load_pages(HERE / v["text"]), R.load_pages(HERE / v["raw_text"]))
        self.assertEqual((len(used), 208 in used), (26, True))  # fragmented pages come from the pdftotext -raw layer
        for key, (agree, fixed) in want.items():
            v, pages = committed(key)
            self.assertEqual(hashlib.sha256((HERE / v["text"]).read_bytes()).hexdigest(), v["text_sha256"])
            pm, st = R.page_map(v, pages)
            self.assertEqual((st["heads_agree"], st["heads_disagree"]), (agree, 0), key)
            for pdf, printed in fixed.items():
                self.assertEqual(pm[pdf], printed)

    def test_sections_match_the_contents(self):
        for key, n in (("RICH_VI", 13), ("RICH_VII", 15), ("RICH_IX", 11)):
            v, pages = committed(key)
            pm, _ = R.page_map(v, pages)
            stream, _ = R.body_stream(v, pages, pm)
            got = [[s["printed_start"], s["printed_end"]] for s in R.find_sections(v, stream) if s["kind"] == "orders"]
            self.assertEqual(len(got), n)
            self.assertEqual(got, v["contents_order_sections"], key)

    def test_documents(self):
        found = {}
        for key in ("RICH_VI", "RICH_VII", "RICH_IX"):
            v, pages = committed(key)
            pm, _ = R.page_map(v, pages)
            docs, _, _, _ = R.volume_documents(v, pages, pm)
            found[key] = [d for d in docs if d["is_order"]]
        self.assertEqual({k: len(v) for k, v in found.items()}, {"RICH_VI": 213, "RICH_VII": 75, "RICH_IX": 154})
        vi = [(d["printed_first"], d["date"]) for d in found["RICH_VI"] if d["printed_first"] <= 19]
        self.assertEqual([d for _, d in vi], ["1861-04-25", "1861-04-27", "1861-04-30", "1861-05-07", "1861-06-20", "1861-07-02"])
        ix = found["RICH_IX"]
        self.assertFalse([d for d in ix if d["date"].startswith("1883")])
        self.assertIn("1893-01-18", [d["date"] for d in ix if d["printed_first"] == 383 and d["nested"]])  # Hayes, inside GO No. 4
        self.assertEqual([d["date"] for d in ix if d["kind"] == "in_message"], ["1890-09-04"])  # EO 28, p. 212
        self.assertEqual([d["date"] for d in ix if d["printed_first"] == 612], ["1895-05-24"] * 3)
        self.assertTrue({"1891-01-30", "1891-02-13"} <= {d["date"] for d in ix if d["printed_first"] in (164, 165)})  # Windom / Porter
        vi_all = found["RICH_VI"]
        self.assertEqual([d["date"] for d in vi_all if d["printed_first"] in (38, 39) and d["date_from"] == "dateline"][:2],
                         ["1861-07-31", "1861-08-07"])  # bare caps datelines
        self.assertIn("GENERAL ORDERS , NO . 13 .", [d["first_line"] for d in vi_all if d["date"] == "1861-04-30"])
        self.assertIn("1868-08-22", [d["date"] for d in vi_all if d["printed_first"] == 667])  # Sitka
        vii = found["RICH_VII"]
        self.assertIn("1869-03-09", [d["date"] for d in vii])  # "Marcharch 9"
        self.assertIn("1875-03-09", [d["date"] for d in vii if d["first_line"].startswith("TREASURY DEPARTMENT")])
        self.assertEqual([d["date"] for d in vii if d["kind"] == "configured"], ["1871-12-19"])
        self.assertEqual(sum(1 for d in vii if d["nested"]), 5)
        self.assertIn("1872-10-11", [d["date"] for d in vii if d["printed_first"] == 183])  # Seward, on a rejoined page

    @unittest.skipUnless(CENSUS.exists(), "census not checked out")
    def test_citations_and_census_leads(self):
        with tempfile.TemporaryDirectory() as td:
            s = R.run(REPO, HERE, td, HERE / PROV["lists_fallback"]["dir"])
            v = {x["volume"]: x for x in s["volumes"]}
            self.assertEqual(v["RICH_IX"]["wpa_status"], {"match": 72, "unmatched": 4})
            self.assertEqual(v["RICH_IX"]["wpa_methods"]["entry_year_outside_volume"], 4)
            self.assertEqual(v["RICH_VI"]["wpa_status"], {"match": 3})
            self.assertEqual(v["RICH_VII"]["wpa_status"], {"match": 11})  # EO 9 cited as "VII E 218"
            self.assertEqual(v["RICH_IX"]["lord_status"], {"match": 77, "ambiguous": 2})
            self.assertEqual((v["RICH_IX"]["census_leads"]["DATE_FILL"], v["RICH_IX"]["census_leads"]["NOT_IN_CENSUS_numbered"]), (52, 21))
            self.assertEqual(v["RICH_IX"]["census_ids_with_text"], 52)
            with open(pathlib.Path(td) / "CITATIONS.csv", encoding="utf-8") as fh:
                c = {(r["volume"], r["entry"]): r for r in csv.DictReader(fh)}
            self.assertEqual(c[("RICH_IX", "EO:29")]["doc_dates"], "1893-01-18")
            self.assertEqual(c[("RICH_IX", "EO:28-1")]["doc_dates"], "1891-01-30")
            self.assertEqual(c[("RICH_IX", "EO:28")]["method"], "date_only_no_citation")
            self.assertEqual(c[("RICH_VII", "Lord:414")]["doc_dates"], "1872-05-27")
            for eo in ("EO:1", "EO:3", "EO:4"):
                self.assertEqual(c[("RICH_VI", eo)]["status"], "match")
            with open(pathlib.Path(td) / "CENSUS_LEADS.csv", encoding="utf-8") as fh:
                missing = {r["instrument_id"] for r in csv.DictReader(fh) if r["lead"] == "IN_CENSUS_NOT_FOUND_IN_VOLUME" and r["volume"] == "RICH_VI"}
            self.assertEqual(missing, {"EO:6"})


if __name__ == "__main__":
    unittest.main()
