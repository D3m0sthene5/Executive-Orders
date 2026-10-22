"""Network-free tests for the Lewis/Clark web search layer (injected transport)."""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eo_websearch as w  # noqa: E402


class FakeWeb:
    """A transport: url -> (status, headers, body). Unknown URLs are 404. robots.txt is served per host."""

    def __init__(self):
        self.pages = {}
        self.robots = {}
        self.calls = []

    def __call__(self, url, headers, timeout):
        self.calls.append((url, dict(headers)))
        host = url.split("/")[2]
        if url.endswith("/robots.txt"):
            body = self.robots.get(host, "User-agent: *\nAllow: /\n").encode()
            return 200, {"content-type": "text/plain"}, io.BytesIO(body)
        if url in self.pages:
            status, ctype, body = self.pages[url]
            return status, {"content-type": ctype}, io.BytesIO(body)
        return 404, {}, io.BytesIO(b"")


TARGET = {"id": "EO:5862", "number": 5862, "suffix": "", "date": "1932-06-23",
          "title": "Executive Order 5862—Withdrawal of Public Lands for Resurvey, Colorado", "president": "Herbert Hoover", "kind": "number_gap"}

ENGINES = [
    {"name": "fake_html", "kind": "html", "url": "https://engine.test/search?q={q}"},
    {"name": "fake_json", "kind": "json", "url": "https://api.test/v1?q={q}",
     "json": {"items": "response.docs", "title": "title", "url": "identifier", "snippet": "description"}, "url_prefix": "https://archive.org/details/"},
    {"name": "fake_keyed", "kind": "json", "env": ["FAKE_KEY"], "url": "https://keyed.test/?key={ENV:FAKE_KEY}&q={q}",
     "json": {"items": "items", "title": "title", "url": "link", "snippet": "snippet"}},
    {"name": "fake_blocked", "kind": "html", "url": "https://blocked.test/search?q={q}"},
]


class SearchLayer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="websearch-")
        self.web = FakeWeb()
        self.web.robots["blocked.test"] = "User-agent: *\nDisallow: /\n"
        q = w.build_url(ENGINES[0], '"Executive Order No. 5862"', 1932)
        self.web.pages[q] = (200, "text/html", b"""<html><body>
            <a href="https://engine.test/settings">Settings</a>
            <a href="/l/?uddg=https%3A%2F%2Fdocs.test%2Feo5862.html">Executive Order 5862 of June 23, 1932 - full text</a>
            <p>By virtue of the authority ... Executive Order No. 5862, June 23, 1932, withdrawal of public lands Colorado</p>
            <a href="https://other.test/unrelated">Weather in Denver</a> nothing here
            </body></html>""")
        self.web.pages["https://docs.test/eo5862.html"] = (200, "text/html", b"""<html><head><title>EO 5862</title></head><body>
            <h1>Executive Order No. 5862</h1><p>June 23, 1932. By virtue of the authority vested in me, it is hereby ordered
            that the public lands in Colorado be withdrawn for resurvey. This modifies Executive Order No. 5853 and Executive Order 4000.</p>
            <a href="https://docs.test/eo5862.pdf">PDF scan</a><a href="https://docs.test/about">About</a></body></html>""")
        qj = w.build_url(ENGINES[1], '"Executive Order No. 5862"', 1932)
        self.web.pages[qj] = (200, "application/json", json.dumps({"response": {"docs": [
            {"identifier": "executiveorders1932", "title": "Executive orders, 1932", "description": "GPO compilation"}]}}).encode())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def searcher(self, env=None, max_requests=50):
        return w.Searcher(os.path.join(self.tmp, "cache"), max_requests=max_requests, transport=self.web, env=env or {},
                          engines=ENGINES, now=lambda: "2026-10-21T00:00:00Z")

    def test_strategies_escalate_and_use_date_and_title(self):
        labels = [s[0] for s in w.query_strategies(TARGET)]
        self.assertEqual(labels[:2], ["number_phrase", "number_bare"])
        self.assertIn("number_and_date", labels)
        self.assertIn("title_words", labels)
        q = dict((s[0], s[1]) for s in w.query_strategies(TARGET))
        self.assertEqual(q["number_phrase"], '"Executive Order No. 5862"')
        self.assertIn("June 23, 1932", q["number_and_date"])
        self.assertIn("Withdrawal Public Lands Resurvey Colorado", q["title_words"])
        half = w.query_strategies({"id": "EO:1182½", "number": 1182, "suffix": "½", "date": "", "title": ""})
        self.assertEqual(half[0][1], '"Executive Order No. 1182 1/2"')
        lettered = dict((s[0], s[1]) for s in w.query_strategies({"id": "EO:3016B", "number": 3016, "suffix": "B", "date": "", "title": ""}))
        self.assertEqual(lettered["suffix_attached"], '"Executive Order 3016B"')

    def test_html_results_unwrap_redirects_and_skip_engine_links(self):
        s = self.searcher()
        res = s.search(ENGINES[0], '"Executive Order No. 5862"', 1932)
        urls = [h["url"] for h in res["hits"]]
        self.assertIn("https://docs.test/eo5862.html", urls)
        self.assertNotIn("https://engine.test/settings", urls)
        self.assertEqual(res["error"], "")
        self.assertEqual(s.engine_status["fake_html"], "ok")

    def test_json_results_and_url_prefix(self):
        s = self.searcher()
        res = s.search(ENGINES[1], '"Executive Order No. 5862"', 1932)
        self.assertEqual(res["hits"][0]["url"], "https://archive.org/details/executiveorders1932")
        self.assertEqual(res["hits"][0]["title"], "Executive orders, 1932")

    def test_keyed_engine_waits_for_its_key_and_robots_blocks_are_named(self):
        s = self.searcher(env={})
        ready = [e["name"] for e in s.ready_engines()]
        self.assertNotIn("fake_keyed", ready)
        self.assertEqual(s.engine_status["fake_keyed"], "needs_key")
        s2 = self.searcher(env={"FAKE_KEY": "abc"})
        self.assertIn("fake_keyed", [e["name"] for e in s2.ready_engines()])
        self.assertIn("key=abc", w.build_url(ENGINES[2], "x", None, {"FAKE_KEY": "abc"}))
        res = s.search(ENGINES[3], "x")
        self.assertEqual(res["error"], "blocked_by_robots_txt")
        self.assertEqual(s.engine_status["fake_blocked"], "blocked_by_robots_txt")

    def test_scoring_prefers_number_date_and_order_wording(self):
        low, _ = w.score_hit({"title": "Weather in Denver", "url": "https://other.test/x", "snippet": ""}, TARGET)
        high, why = w.score_hit({"title": "Executive Order 5862 of June 23, 1932", "url": "https://docs.test/eo5862.pdf", "snippet": ""}, TARGET)
        self.assertLess(low, 20)
        self.assertGreaterEqual(high, 65)
        self.assertIn("number_named", why)
        self.assertIn("date_named", why)
        glued, _ = w.score_hit({"title": "Executive Order 58620", "url": "", "snippet": ""}, TARGET)
        self.assertLess(glued, 40, "58620 is not 5862")

    def test_unavailable_engine_is_only_probed_once_per_run(self):
        for status in (401, 403, 429):
            with self.subTest(status=status):
                engine = ENGINES[0]
                self.web.pages[w.build_url(engine, "first")] = (status, "text/html", b"blocked")
                s = self.searcher()
                first = s.search(engine, "first")
                before = (len(self.web.calls), s.reserved, len(s.sources))
                for n in range(99):
                    result = s.search(engine, "different query " + str(n))
                    self.assertIn("deferred_this_run", result["error"])
                self.assertEqual(first["status"], status)
                self.assertEqual((len(self.web.calls), s.reserved, len(s.sources)), before)
                self.assertEqual(s.deferred_queries[engine["name"]], 99)
                # Deferral doesn't disable a working catalog or survive a new run.
                self.assertEqual(s.search(ENGINES[1], '\"Executive Order No. 5862\"', 1932)["status"], 200)
                fresh = self.searcher()
                self.assertEqual(fresh.search(engine, "first")["status"], status)
                self.assertEqual(fresh.reserved, 1)

    def test_robots_block_does_not_consume_budget_for_every_target(self):
        s = self.searcher()
        self.assertEqual(s.search(ENGINES[3], "one")["error"], "blocked_by_robots_txt")
        used = s.reserved
        self.assertEqual(s.search(ENGINES[3], "two")["error"], "deferred_this_run:blocked_by_robots_txt")
        self.assertEqual(s.reserved, used)
        self.assertEqual(s.engine_status["fake_blocked"], "blocked_by_robots_txt")

    def test_deferred_queries_are_not_persisted_as_engine_attempts(self):
        s = self.searcher()
        engine = ENGINES[3]
        first = w.advance(s, TARGET, w.new_state(TARGET), [engine], max_pages=0)
        self.assertEqual(first["engines_tried"][engine["name"]], 1)
        # Simulate another target after this run has discovered a robots block.
        second = w.advance(s, TARGET, w.new_state(TARGET), [engine], max_pages=0)
        self.assertNotIn(engine["name"], second["engines_tried"])
        self.assertEqual(second["engines_deferred"][engine["name"]], 1)
        self.assertTrue(any("deferred_this_run:blocked_by_robots_txt" in note for note in second["notes"]))

    def test_advance_searches_reads_pages_harvests_numbers_and_carries_state(self):
        s = self.searcher()
        st = w.new_state(TARGET)
        st = w.advance(s, TARGET, st, s.ready_engines())
        self.assertEqual(st["strategy_index"], 1)
        self.assertEqual(st["steps"], 1)
        self.assertIn("fake_html", st["engines_tried"])
        page = next(h for h in st["hits"] if h["url"] == "https://docs.test/eo5862.html")
        self.assertGreaterEqual(page["page_score"], 60)
        self.assertIn("order_wording", page["page_why"])
        self.assertIn("5862", page["page_quote"])
        self.assertIn("EO:5853", page["page_numbers_named"])
        self.assertIn("EO:4000", page["page_numbers_named"])
        followed = [h for h in st["hits"] if h["engine"] == "followed_link"]
        self.assertTrue(any(h["url"] == "https://docs.test/eo5862.pdf" for h in followed))
        self.assertEqual(st["best_url"], "https://docs.test/eo5862.html")
        # second step: next strategy, page not re-read
        before = len(self.web.calls)
        st = w.advance(s, TARGET, st, s.ready_engines())
        self.assertEqual(st["strategy_index"], 2)
        self.assertNotIn(("https://docs.test/eo5862.html",), [(c[0],) for c in self.web.calls[before:]])

    def test_budget_stops_cleanly_and_is_recorded(self):
        s = self.searcher(max_requests=2)  # two fetches; robots.txt reads are extra
        st = w.advance(s, TARGET, w.new_state(TARGET), s.ready_engines())
        self.assertTrue(any("budget stopped" in n for n in st["notes"]))
        self.assertEqual(s.reserved, 2, "parallel engine queries cannot overrun the budget")
        self.assertLessEqual(s.requests_used, 2 + 2, "at most one robots.txt read per fetched host")
        self.assertFalse(s.budget_left())

    def test_campaign_writes_files_and_resumes_from_prior_state(self):
        root = os.path.join(self.tmp, "repo")
        out = os.path.join(root, "jobs", "x-job", "output")
        os.makedirs(out)
        t2 = {"id": "EO:92", "number": 92, "suffix": "", "date": "1896-11-02", "title": "", "president": ""}
        summ = w.run_campaign("x-job", root, out, [TARGET, t2], cache_dir=os.path.join(self.tmp, "c1"), max_requests=100,
                              max_targets=1, transport=self.web, env={}, engines=ENGINES, universe_ids={"EO:4000"},
                              now=lambda: "2026-10-21T00:00:00Z")
        self.assertEqual(summ["advanced_this_run"], 1)
        self.assertEqual(summ["never_searched"], 1)
        self.assertEqual(summ["targets_with_page_confirmed_lead"], 1)
        self.assertEqual(summ["numbers_named_not_in_census"], 2, "5853 and 5862 named; 4000 is in the census")
        for name in ("WEB_STATE.json", "WEB_HITS.csv", "WEB_LEADS.csv", "WEB_NUMBERS_NAMED.csv", "SOURCES.jsonl", "ENGINES.json"):
            self.assertTrue(os.path.exists(os.path.join(out, name)), name)
        self.assertEqual(summ["engines"]["fake_blocked"], "blocked_by_robots_txt")
        self.assertEqual(summ["engines"]["fake_keyed"], "needs_key")
        # second run resumes from the folder: the other target goes first, the first keeps its hits
        summ2 = w.run_campaign("x-job", root, out, [TARGET, t2], cache_dir=os.path.join(self.tmp, "c2"), max_requests=100,
                               max_targets=1, transport=self.web, env={}, engines=ENGINES, now=lambda: "2026-10-22T00:00:00Z")
        with open(os.path.join(out, "WEB_STATE.json"), encoding="utf-8") as fh:
            state = json.load(fh)["targets"]
        self.assertEqual(summ2["prior_state_from"], "folder")
        self.assertEqual(state["EO:92"]["steps"], 1)
        self.assertEqual(state["EO:5862"]["steps"], 1)
        self.assertTrue(state["EO:5862"]["hits"])

    def test_page_to_text_strips_scripts(self):
        self.assertEqual(w.page_to_text(b"<html><script>x()</script><p>Hello <b>there</b></p></html>"), "Hello there")

    def test_unwrap_redirects(self):
        self.assertEqual(w.unwrap_redirect("https://duckduckgo.com/l/?uddg=https%3A%2F%2Fa.test%2Fx&rut=1"), "https://a.test/x")
        self.assertEqual(w.unwrap_redirect("https://www.google.com/url?q=https://b.test/y&sa=U"), "https://b.test/y")
        self.assertEqual(w.unwrap_redirect("https://c.test/plain"), "https://c.test/plain")


if __name__ == "__main__":
    unittest.main()
