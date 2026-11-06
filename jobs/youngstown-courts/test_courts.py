"""Offline tests for Youngstown courts. No network, no tokens. Run: python -I test_courts.py"""
import bz2
import io
import json
import os
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import analyze  # noqa: E402
import bulk  # noqa: E402
import bz2seg  # noqa: E402
import controls  # noqa: E402
import courts  # noqa: E402
import scan  # noqa: E402

DATES, KEYS = analyze.load_register(HERE / "data" / "ORDER_DATES.csv")
PASSED = []


def test(fn):
    fn()
    PASSED.append(fn.__name__)
    return fn


class Mem:
    def __init__(self, b):
        self.b, self.size, self.url = b, len(b), "mem://x"
        self.etag = self.last_modified = None

    def read_range(self, a, b):
        return self.b[a:b + 1]

    def open_stream(self, a, b):
        for i in range(a, b + 1, 30000):
            yield self.b[i:min(b + 1, i + 30000)]


# ---- scan ---------------------------------------------------------------------------------------------------------

@test
def citation_shapes():
    got = lambda t: [m["number"] for m in scan.eo_mentions(t)]  # noqa: E731
    assert got("Executive Order No. 12,954, 60 Fed.Reg. 13,023 (1995)") == [12954]
    assert got("E.O. 11,246, 3 C.F.R. 339 (1964-65 Compilation); E.O. 11,141, 3 C.F.R. 179") == [11246, 11141]
    assert got("Executive Orders 10925 and 11246") == [10925, 11246]
    assert got("Executive Orders Nos. 10925, 11114 and 11246, 30 Fed. Reg. 12319") == [10925, 11114, 11246]
    assert got("Exec. Orders Nos. 12276-12285, 46 Fed.Reg. 7913") == list(range(12276, 12286))
    assert got("Executive Order No. 9066, 7 Fed.Reg. 1407") == [9066]
    assert got("EXECUTIVE ORDER 10340") == [10340]
    assert got("Executive Order\n10340") == [10340]
    assert got("pursuant to Exec. Order 13,769, 82 Fed. Reg. 8,977") == [13769]
    assert got("Proclamation No. 10340, Order No. 9066, 42 U.S.C. § 10340, 82 Fed. Reg. 13,769") == []
    assert got("the executive order of the Governor") == [] and got("Executive Order of February 19, 1942") == []
    ms = scan.eo_mentions("see E.O. 6980-C and Executive Order 2656A")
    assert [(m["number"], m["suffix"]) for m in ms] == [(6980, "C"), (2656, "A")]


@test
def derive_and_pick():
    html = '<p id="b1">Held that <em>the</em> Order&#8217;s &amp; scope</p>\n<p>Next</p>'
    d = scan.derive_text(html, "html_with_citations")
    assert d == "Held that the Order’s & scope\n\nNext", repr(d)
    assert scan.derive_text("a  b\n\n\n\nc", "plain_text") == "a b\n\nc"
    assert scan.pick_text({"plain_text": "", "html_with_citations": "x", "html": "y"}) == ("html_with_citations", "x")
    assert scan.pick_text({"plain_text": " "}) == (None, "")


@test
def sentence_bounds_ignore_abbreviations():
    t = "The Court so held. The President issued Executive Order No. 10340, 17 Fed. Reg. 2955, in 1952. Next sentence."
    s, e = scan.sentence_bounds(t, t.index("Executive"), t.index("Executive") + 25)
    assert t[s:e].startswith("The President issued") and t[s:e].endswith("in 1952."), t[s:e]
    t2 = "It was valid. And Executive Order No. 13,780 was\n\n166\n\nnot the first to be issued. Next."
    s, e = scan.sentence_bounds(t2, t2.index("Executive"), t2.index("Executive") + 25)
    assert t2[s:e].startswith("And Executive") and t2[s:e].endswith("issued."), t2[s:e]


@test
def class_rules():
    def cls(text):
        m = scan.eo_mentions(text)[0]
        return scan.classify_mention(text, m["start"], m["end"])
    assert cls("The District Court issued a preliminary injunction restraining the Secretary from acting under Executive Order No. 10340.")["class"] == "enjoined_vacated_invalidated"
    assert cls("We hold that Executive Order 11246 is valid and upheld the Plan.")["class"] == "upheld"
    assert cls("We approach the construction of Executive Order No. 9066 as we would legislation.")["class"] == "interpreted"
    assert cls("The President issued Executive Order 13769 on January 27.")["class"] == "mentioned"
    # a request or contention is not a holding
    r = cls("Plaintiffs moved for a preliminary injunction to enjoin Executive Order 13780.")
    assert r["class"] == "mentioned" and r["argument_frame"] and r["cue_family"] == "enjoined_vacated_invalidated"
    # negation: did not enjoin is a mention; not valid reads as the opposite
    assert cls("The court did not enjoin Executive Order 13780.")["class"] == "mentioned"
    assert cls("Executive Order 13780 is not valid under the statute.")["class"] == "enjoined_vacated_invalidated"
    # cues in the neighbouring sentence are reported but never the class
    r = cls("The court vacated the rule. See Executive Order 12954.")
    assert r["class"] == "mentioned" and r["adjacent_class"] == "enjoined_vacated_invalidated"
    ms = [scan.classify_mention("The first Executive Order 1 was enjoined. The second Executive Order 2 was upheld.", m["start"], m["end"])["class"]
          for m in scan.eo_mentions("The first Executive Order 1 was enjoined. The second Executive Order 2 was upheld.")]
    assert ms == ["enjoined_vacated_invalidated", "upheld"], ms
    assert scan.pair_class([{"class": "mentioned", "federal_signal": False}, {"class": "upheld", "federal_signal": True},
                            {"class": "interpreted", "federal_signal": True}]) == ("upheld", 1)


# ---- bzip2 segments -----------------------------------------------------------------------------------------------

def sample_csv(n=4000, seed=5):
    rng = random.Random(seed)
    words = ["".join(rng.choice("abcdefghijklmnopqrstuvwxyz ") for _ in range(rng.randint(3, 9))) for _ in range(2000)]
    rows = []
    for i in range(1, n):
        txt = " ".join(rng.choice(words) for _ in range(rng.randint(5, 300)))
        rows.append(f'"{i}","2022-01-01 00:00:00+00","{txt}\nline \\"two\\" {i}"\n')
    return ("id,date,text\n" + "".join(rows)).encode()


@test
def segments_reassemble_exactly():
    data = sample_csv()
    for level in (1, 9):
        comp = bz2.compress(data, level)
        src = Mem(comp)
        assert bz2seg.stream_level(src) == level
        bounds = bz2seg.block_boundaries(src, max(20000, len(comp) // 5), level)
        assert len(bounds) >= 2
        eos = bz2seg.end_of_stream_bit(src)
        assert eos is not None
        out = b""
        for k, sb in enumerate(bounds):
            last = k + 1 == len(bounds)
            dec = bz2seg.SegmentDecoder(src, sb, eos if last else bounds[k + 1], level, extra_bytes=10**9, final=last, eos_bit=eos)
            buf = b"".join(dec.chunks())
            out += buf[:int(dec.owned)]
        assert out == data, (level, len(out), len(data))


@test
def row_scanner_owns_each_row_once():
    data = sample_csv(3000)
    comp = bz2.compress(data, 1)
    src = Mem(comp)
    bounds = bz2seg.block_boundaries(src, max(20000, len(comp) // 4), 1)
    eos = bz2seg.end_of_stream_bit(src)
    header = bulk.decode_header(src, 1)
    assert header == ["id", "date", "text"]
    seen = []
    for k, sb in enumerate(bounds):
        last = k + 1 == len(bounds)
        bulk.scan_segment(src, 1, sb, eos if last else bounds[k + 1], last, bulk.id_select(set(range(1, 3000))),
                          lambda raw: seen.append(int(bulk.split_fields(raw.decode())[0])), extra_bytes=10**9, eos_bit=eos)
    assert sorted(seen) == list(range(1, 3000)), (len(seen), len(set(seen)))


@test
def csv_dialect_of_the_bulk_files():
    f = bulk.split_fields('"7","a \\"quoted\\" \\\\ word\nnext",,"",x')
    assert f == ["7", 'a "quoted" \\ word\nnext', "", "", "x"], f
    assert bulk.split_fields('"1","2"') == ["1", "2"] and bulk.split_fields('"1",') == ["1", ""]
    assert bulk.parse_table('"nc",,"a\\"b","x\ny"\n"mi",,,"z"\n') == [["nc", "", 'a"b', "x\ny"], ["mi", "", "", "z"]]
    row = bulk.parse_row(b'"9","d","t"', ["id", "date", "text"])
    assert row == {"id": "9", "date": "d", "text": "t"} and bulk.parse_row(b'"9","d"', ["id", "date", "text"]) is None


# ---- HTTP source --------------------------------------------------------------------------------------------------

class FakeBody(io.BytesIO):
    def __init__(self, data, break_after=None):
        super().__init__(data)
        self.break_after, self.sent = break_after, 0

    def read(self, n=-1):
        if self.break_after is not None and self.sent >= self.break_after:
            raise ConnectionResetError("reset")
        out = super().read(n if self.break_after is None else min(n, self.break_after - self.sent) if n > 0 else n)
        self.sent += len(out)
        return out


def make_transport(objects, listing=None, breaks=None, status=None):
    calls = []

    def transport(url, headers, timeout):
        calls.append((url, dict(headers)))
        if status:
            return status, {}, FakeBody(b"")
        if "/robots.txt" in url:
            return 404, {}, FakeBody(b"")
        if "?prefix=" in url:
            pre = url.split("prefix=")[1].split("&")[0]
            xml = "<ListBucketResult><IsTruncated>false</IsTruncated>" + "".join(
                f"<Contents><Key>{k}</Key><LastModified>2026-09-30T00:00:00.000Z</LastModified><ETag>\"e\"</ETag><Size>{len(v)}</Size></Contents>"
                for k, v in sorted(objects.items()) if k.startswith(pre)) + "</ListBucketResult>"
            return 200, {}, FakeBody(xml.encode())
        key = url.split(".amazonaws.com/")[1]
        data = objects[key]
        a, b = headers["Range"].split("=")[1].split("-")
        a, b = int(a), min(int(b), len(data) - 1)
        brk = None
        if breaks and breaks.pop(0 if len(breaks) else 0, None) if False else None:
            brk = None
        chunk = data[a:b + 1]
        body = FakeBody(chunk, break_after=(breaks.pop(0) if breaks else None))
        return 206, {"content-range": f"bytes {a}-{b}/{len(data)}", "etag": '"e"', "last-modified": "Wed, 30 Sep 2026 09:00:24 GMT"}, body
    transport.calls = calls
    return transport


@test
def http_source_resumes_and_counts_failures():
    data = bytes(range(256)) * 400
    t = make_transport({"bulk-data/x.csv.bz2": data}, breaks=[None, 5000, None])
    src = bulk.HttpSource(bulk.BUCKET + "/bulk-data/x.csv.bz2", t, "ua", sleep=lambda s: None)
    assert src.size == len(data)
    got = b"".join(src.open_stream(0, len(data) - 1, chunk=1000))
    assert got == data
    assert src.stats["failures"] >= 1, src.stats
    rng_calls = [c for c in t.calls if "Range" in c[1]]
    assert any(c[1]["Range"].startswith("bytes=5000-") for c in rng_calls), [c[1]["Range"] for c in rng_calls]
    # a forbidden object fails fast
    t2 = make_transport({}, status=403)
    try:
        bulk.HttpSource(bulk.BUCKET + "/bulk-data/x.csv.bz2", t2, "ua", sleep=lambda s: None)
        raise AssertionError("403 should raise")
    except bulk.BulkError:
        pass


@test
def listing_and_snapshot():
    objs = {"bulk-data/opinions-2026-06-30.csv.bz2": b"x" * 2000, "bulk-data/opinions-2026-09-30.csv.bz2": b"x" * 3000,
            "bulk-data/opinions-2022-08-03.csv.bz2": b"x" * 14}
    t = make_transport(objs)
    lst = bulk.list_objects(t, "bulk-data/opinions-", "ua")
    assert len(lst) == 3
    by = {k: lst for k in courts.TABLES}
    for k in courts.TABLES:
        by[k] = [(key.replace("opinions", courts.TABLES[k]), lm, sz) for key, lm, sz in lst]
    date, chosen = courts.pick_snapshot(by, "latest")
    assert date == "2026-09-30" and chosen["opinions"][2] == 3000


# ---- analysis -----------------------------------------------------------------------------------------------------

@test
def rows_dates_signals_selection():
    t_state = "The Governor's Executive Order No. 10340 was enjoined by the county court."
    t_fed = "The President issued Executive Order No. 10340, 17 Fed. Reg. 2955, and the court enjoined it."
    t_new = "Executive Order 13769 was challenged by the President's opponents."
    recs = []
    for oid, cid, text in ((1, 11, t_state), (2, 12, t_fed), (3, 13, t_new), (4, 12, t_fed)):
        orders, _ = analyze.analyze_text(text, KEYS)
        recs.append({"oid": oid, "cid": cid, "type": "020lead" if oid != 4 else "040dissent", "col": "plain_text",
                     "raw_sha256": "a" * 64, "raw_bytes": 10, "text_sha256": "b" * 64, "chars": len(text), "ocr": False, "orders": orders})
    clusters = {11: {"case_name": "A v. B", "date_filed": "1960-01-01", "slug": "a-v-b", "docket_id": 1},
                12: {"case_name": "C v. D", "date_filed": "1960-01-01", "slug": "c-v-d", "docket_id": 2},
                13: {"case_name": "E v. F", "date_filed": "1952-01-01", "slug": "e-v-f", "docket_id": 2}}
    dockets = {1: {"court_id": "ohioctapp", "docket_number": "1"}, 2: {"court_id": "ca6", "docket_number": "2"}}
    courts_ = {"ohioctapp": {"name": "Ohio App", "jurisdiction": "SA"}, "ca6": {"name": "Sixth Circuit", "jurisdiction": "F"}}
    stats = analyze.Counter()
    rows = analyze.build_rows(recs, clusters, dockets, courts_, {12: ["1 F.2d 1"]}, DATES, stats)
    assert stats["dropped_opinion_dated_before_the_order"] == 1, stats  # EO 13769 in a 1952 opinion
    by = {(r["eo"], r["cid"]): r for r in rows}
    assert not by[("EO:10340", 11)]["eligible"] and by[("EO:10340", 11)]["state_only"]
    r = by[("EO:10340", 12)]
    assert r["eligible"] and r["class"] == "enjoined_vacated_invalidated" and r["oids"] == [2, 4] and r["level"] == 1
    assert r["deciding"]["oid"] == 2  # the lead opinion decides a tie
    chosen, omitted, _ = analyze.select_rows(rows, {"hits": 10**9, "fragments": 10**9, "sources": 10**9, "mentions_per_order": 1,
                                                    "cost": lambda r, s: {"hits": 1, "fragments": 1, "sources": 1}})
    assert [(c["eo"], c["cid"]) for c in chosen] == [("EO:10340", 12)] and omitted["no_federal_signal"] == 1
    chosen, omitted, _ = analyze.select_rows(rows, {"hits": 0, "fragments": 10**9, "sources": 10**9, "mentions_per_order": 1,
                                                    "cost": lambda r, s: {"hits": 1, "fragments": 1, "sources": 1}})
    assert not chosen and omitted["byte_budget_enjoined_vacated_invalidated"] == 1


@test
def record_formats_match_the_claim_kit_conventions():
    text = "The President issued Executive Order No. 10340, 17 Fed. Reg. 2955, and the court enjoined it. Another sentence."
    orders, _ = analyze.analyze_text(text, KEYS)
    rec = {"oid": 7, "cid": 70, "type": "020lead", "col": "plain_text", "raw_sha256": "a" * 64, "raw_bytes": len(text),
           "text_sha256": analyze.sha256(text.encode()), "chars": len(text), "ocr": False, "orders": orders}
    row = {"eo": "EO:10340", "cid": 70, "oids": [7], "recs": [rec], "deciding": rec, "class": orders["EO:10340"]["class"],
           "fed": True, "court": "Sixth Circuit", "court_id": "ca6", "jurisdiction": "F", "date": "1960-01-01", "case_name": "C v. D",
           "slug": "c-v-d", "docket_number": "2", "cites": ["1 F.2d 1"], "n_mentions": 1, "url": "https://www.courtlistener.com/opinion/70/c-v-d/"}
    hit, quote, span, m = analyze.hit_record(row, text, {"date": "2026-09-30"})
    assert text[span[0]:span[1]] == quote and quote.startswith("The President issued")
    frag = analyze.fragment_record(row, hit, quote, span, m, "courtlistener:opinion:7")
    assert frag["kind"] == "court_decision_candidates" and frag["instrument_id"] == "EO:10340"
    d = frag["data"][0]
    assert d["text_path"] is None and d["acting_id"].startswith("CASE:") and d["target_id"] == "EO:10340"
    src = analyze.source_record(rec, [row], {"key": "bulk-data/opinions-2026-09-30.csv.bz2", "etag": "e", "last_modified": "x"}, "2026-11-06T00:00:00Z")
    assert src["instrument_ids"][0] == "COURT:cl-op-7" and "EO:10340" in src["instrument_ids"] and len(src["instrument_ids"]) >= 2
    assert src["acceptable_as_original"] is False and src["role"] == "court_opinion_text" and src["text_path"] is None
    assert set(hit) == set(analyze.HIT_COLUMNS)


# ---- controls -----------------------------------------------------------------------------------------------------

@test
def planted_controls():
    cases = controls.fixtures()
    assert len(cases) >= 6
    r = controls.locator_and_class_controls(cases, KEYS)
    assert r["locator"]["recall"] == 1.0 and r["locator"]["citations_marked_by_hand"] >= 50
    assert r["opinion_class"]["planted_positives"] >= 5
    ids = {row["eo"] for row in r["opinion_class"]["rows"]}
    assert "EO:10340" in ids  # Youngstown
    assert any(row["case"] == "youngstown" and row["agree"] for row in r["opinion_class"]["rows"])
    neg = controls.negative_controls(KEYS, DATES)
    assert neg["false_hits"] == 0 and neg["negatives"] >= 6
    st = controls.structure_controls(KEYS)
    assert st["wrong"] == 0, [x for x in st["rows"] if not x["ok"]]
    sm = controls.stream_controls(cases, KEYS)
    assert sm["recall"] == 1.0 and sm["false_rows"] == 0 and sm["row_start_lost"] == 0 and sm["rows_unparsed"] == 0, sm


# ---- the whole job on synthetic bulk files ------------------------------------------------------------------------

def synthetic_bulk():
    cases = controls.fixtures()
    opinions, expected, negatives = controls.build_stream(cases, KEYS, filler_rows=300)

    def table(header, rows, level=1):
        return bz2.compress((",".join(header) + "\n" + "".join(rows)).encode("utf-8"), level)
    oids = sorted({o for o in list(expected) + list(negatives)})
    cl_rows, dk_rows, ct_rows = [], [], []
    for oid in range(1001, 1001 + 300 + 30):
        cid = 50000 + oid
        cl_rows.append(f'"{cid}","2022-01-01 00:00:00+00","Case {cid} v. Test","2001-05-0{1 + oid % 9}","case-{cid}","{cid + 1}","Published"\n')
        dk_rows.append(f'"{cid + 1}","2022-01-01 00:00:00+00","{"scotus" if oid % 3 == 0 else "ca4"}","No. {oid}"\n')
        ct_rows.append(f'"{oid}","{100 + oid % 50}","F.3d","{oid}","1","{cid}","2022-01-01 00:00:00+00","2022-01-01 00:00:00+00"\n')
    objs = {
        "bulk-data/opinions-2026-09-30.csv.bz2": opinions,
        "bulk-data/opinion-clusters-2026-09-30.csv.bz2": table(["id", "date_created", "case_name", "date_filed", "slug", "docket_id", "precedential_status"], cl_rows),
        "bulk-data/dockets-2026-09-30.csv.bz2": table(["id", "date_created", "court_id", "docket_number"], dk_rows),
        "bulk-data/citations-2026-09-30.csv.bz2": table(["id", "volume", "reporter", "page", "type", "cluster_id", "date_created", "date_modified"], ct_rows),
        "bulk-data/courts-2026-09-30.csv.bz2": table(["id", "full_name", "short_name", "jurisdiction"],
                                                     ['"scotus","Supreme Court of the United States","SCOTUS","F"\n',
                                                      '"ca4","Court of Appeals for the Fourth Circuit","CA4","F"\n']
                                                     + [f'"c{i}","Pad court number {i} with a long name {i * 7919}","P{i}","SA"\n' for i in range(120)]),
    }
    return objs, expected


@test
def whole_job_offline():
    objs, expected = synthetic_bulk()
    t = make_transport(objs)
    with tempfile.TemporaryDirectory() as tmp:
        out, cache = Path(tmp) / "out", Path(tmp) / "cache"
        env = {"JOB_MODE": "full", "JOB_WORKERS": "1", "JOB_SEG_MB": "0.03", "JOB_TIME_BUDGET_MIN": "30"}
        s = courts.main(HERE.parent.parent, out, cache, env=env, transport=t)
        assert s["complete"] and s["opinions_segments_done"] >= 2, s
        assert s["opinions_printing_a_register_order"] >= len(expected) * 0.9
        assert s["second_source"]["robots"] in ("allowed", "unreachable", "blocked")
        for name in ("SOURCES.jsonl", "FRAGMENTS.jsonl", "COURT_HITS.csv", "ORDER_TALLY.csv", "CONTROLS.json", "SUMMARY.json", "BUDGET.json"):
            assert (out / name).is_file(), name
        b = json.loads((out / "BUDGET.json").read_text(encoding="utf-8"))
        assert b["within_budget"] and b["total_bytes"] < 20 * 1024 * 1024
        frags = [json.loads(x) for x in (out / "FRAGMENTS.jsonl").read_text(encoding="utf-8").splitlines()]
        srcs = [json.loads(x) for x in (out / "SOURCES.jsonl").read_text(encoding="utf-8").splitlines()]
        assert frags and srcs and all(f["kind"] == "court_decision_candidates" for f in frags)
        assert all(len(x["instrument_ids"]) >= 2 for x in srcs)
        by_src = {x["source_id"]: x for x in srcs}
        # every fragment quote is the exact span of the held text, whose hash is recorded
        for f in frags[:20]:
            d = f["data"][0]
            assert d["source_id"] in by_src and by_src[d["source_id"]]["sha256"] == d["source_sha256"]
            lo, hi = map(int, d["quote_span"].split("-"))
            oid = int(d["source_id"].rsplit(":", 1)[1])
            raw = analyze.gzip.open(cache / "texts" / f"{oid % 1000:03d}" / f"{oid}.txt.gz").read().decode()
            col = by_src[d["source_id"]]["text_column"]
            assert scan.derive_text(raw, col)[lo:hi] == d["quote"], (lo, hi, col, d["quote"][:80], scan.derive_text(raw, col)[lo:hi][:80])
        ctl = json.loads((out / "CONTROLS.json").read_text(encoding="utf-8"))
        assert ctl["measured_error_rate"]["stream_control_recall"] == 1.0
        assert ctl["api_crosscheck"]["ran"] is False
        # a second run reuses every finished segment
        out2 = Path(tmp) / "out2"
        s2 = courts.main(HERE.parent.parent, out2, cache, env=env, transport=t)
        assert s2["order_clusters_found"] == s["order_clusters_found"]
        assert s2["opinions_segments_from_cache"] == s2["opinions_segments_done"] >= 2 and s["opinions_segments_from_cache"] == 0


@test
def job_fails_when_requests_fail():
    for status in (403, 500):
        t = make_transport({}, status=status)
        with tempfile.TemporaryDirectory() as tmp:
            try:
                courts.main(HERE.parent.parent, Path(tmp) / "o", Path(tmp) / "c",
                            env={"JOB_MODE": "full", "JOB_WORKERS": "1"}, transport=t)
            except (SystemExit, bulk.BulkError):
                continue
            raise AssertionError("job must fail when every request fails")


@test
def token_is_never_written_down():
    secret = "tok_SECRET_VALUE_123"
    seen = []

    def t(url, headers, timeout):
        seen.append(headers)
        return 200, {}, FakeBody(json.dumps({"count": 7}).encode())

    class P:
        def allowed(self, url):
            return 0
    r = courts.api_crosscheck(P(), secret, [("EO:10340", 3)], 5, t, sleep=lambda s: None)
    assert r["ran"] and r["rows"][0]["search_index_count"] == 7 and r["rows"][0]["bulk_scan_clusters"] == 3
    assert secret not in json.dumps(r) and seen[0]["Authorization"] == "Token " + secret
    assert courts.api_crosscheck(P(), "", [("EO:1", 1)], 5, t)["ran"] is False


if __name__ == "__main__":
    print(f"{len(PASSED)} tests passed: " + ", ".join(PASSED))
