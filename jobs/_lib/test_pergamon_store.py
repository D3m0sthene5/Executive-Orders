"""Offline tests for Pergamon: every backend against local fake servers. No network beyond 127.0.0.1."""
import datetime as dt
import hashlib
import hmac
import http.server
import json
import pathlib
import re
import sys
import tempfile
import threading
import unittest
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pergamon_store as P  # noqa: E402

BODY = b"%PDF-1.4 a kept order\n" * 5
SHA = hashlib.sha256(BODY).hexdigest()


def no_sleep(_):
    pass


def fast_http(**kw):
    return P.Http(retries=3, sleep=no_sleep, **kw)


class Server:
    """A threaded http.server with a handler class; `state` is shared with the handler."""

    def __init__(self, handler_cls):
        self.state = {}
        handler_cls.state = self.state
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=lambda: self.httpd.serve_forever(poll_interval=0.02), daemon=True)
        self.thread.start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class QuietHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, status, body=b"", headers=None, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""


class FakeGitHub(QuietHandler):
    """Enough of the Releases API: releases by tag, paged asset listing, upload (422 on a duplicate name), delete,
    and public downloads. state: releases, assets, calls, faults."""
    repo = "owner/repo"

    def _auth_ok(self):
        return self.headers.get("Authorization") == "Bearer test-token"

    def _asset_json(self, a):
        return {"id": a["id"], "name": a["name"], "size": len(a["data"]), "state": a["state"],
                "browser_download_url": f"{self.state['base']}/{self.repo}/releases/download/{a['tag']}/{a['name']}"}

    def do_GET(self):
        s = self.state
        u = urllib.parse.urlsplit(self.path)
        q = urllib.parse.parse_qs(u.query)
        s["calls"].append(("GET", u.path))
        m = re.match(rf"^/{self.repo}/releases/download/([^/]+)/([^/]+)$", u.path)
        if m:  # public: must never carry a token
            s["download_auth"].append(self.headers.get("Authorization"))
            tag, name = urllib.parse.unquote(m.group(1)), m.group(2)
            for a in s["assets"].values():
                if a["tag"] == tag and a["name"] == name and a["state"] == "uploaded":
                    return self.send(200, s["corrupt"].get(name, a["data"]), ctype="application/octet-stream")
            return self.send(404, {"message": "Not Found"})
        if not self._auth_ok():
            return self.send(401, {"message": "Bad credentials"})
        if s["faults"].get("rate_limit_once"):
            s["faults"]["rate_limit_once"] = False
            return self.send(403, {"message": "rate limit"}, {"X-RateLimit-Remaining": "0", "Retry-After": "7"})
        m = re.match(rf"^/repos/{self.repo}/releases/tags/(.+)$", u.path)
        if m:
            rel = s["releases"].get(urllib.parse.unquote(m.group(1)))
            return self.send(200, rel) if rel else self.send(404, {"message": "Not Found"})
        m = re.match(rf"^/repos/{self.repo}/releases/(\d+)/assets$", u.path)
        if m:
            rid = int(m.group(1))
            per, page = int(q.get("per_page", ["30"])[0]), int(q.get("page", ["1"])[0])
            items = [self._asset_json(a) for a in s["assets"].values() if a["rid"] == rid]
            return self.send(200, items[(page - 1) * per: page * per])
        self.send(404, {"message": "unknown"})

    def do_POST(self):
        s = self.state
        u = urllib.parse.urlsplit(self.path)
        s["calls"].append(("POST", u.path))
        body = self.read_body()
        if not self._auth_ok():
            return self.send(401, {"message": "Bad credentials"})
        if u.path == f"/repos/{self.repo}/releases":
            req = json.loads(body)
            if req["tag_name"] in s["releases"]:
                return self.send(422, {"message": "Validation Failed"})
            rel = {"id": len(s["releases"]) + 100, "tag_name": req["tag_name"], "name": req["name"],
                   "prerelease": req["prerelease"], "draft": req["draft"], "make_latest": req.get("make_latest")}
            s["releases"][req["tag_name"]] = rel
            return self.send(201, rel)
        m = re.match(rf"^/repos/{self.repo}/releases/(\d+)/assets$", u.path)
        if m:
            rid = int(m.group(1))
            name = urllib.parse.parse_qs(u.query)["name"][0]
            tag = next(t for t, r in s["releases"].items() if r["id"] == rid)
            if any(a["rid"] == rid and a["name"] == name for a in s["assets"].values()):
                return self.send(422, {"message": "Validation Failed", "errors": [{"code": "already_exists"}]})
            s["uploads"].append(name)
            aid = s["next_id"] = s["next_id"] + 1
            if s["faults"].get("starter_502_once"):
                s["faults"]["starter_502_once"] = False   # GitHub: a 502 "may leave an empty asset with state starter"
                s["assets"][aid] = {"id": aid, "rid": rid, "tag": tag, "name": name, "data": b"", "state": "starter"}
                return self.send(502, {"message": "Bad Gateway"})
            s["assets"][aid] = {"id": aid, "rid": rid, "tag": tag, "name": name, "data": body, "state": "uploaded"}
            return self.send(201, self._asset_json(s["assets"][aid]))
        self.send(404, {"message": "unknown"})

    def do_DELETE(self):
        s = self.state
        s["calls"].append(("DELETE", self.path))
        m = re.match(rf"^/repos/{self.repo}/releases/assets/(\d+)$", self.path)
        if m and int(m.group(1)) in s["assets"]:
            del s["assets"][int(m.group(1))]
            return self.send(204)
        self.send(404, {"message": "Not Found"})


def github_server():
    srv = Server(FakeGitHub)
    srv.state.update(releases={}, assets={}, calls=[], uploads=[], faults={}, corrupt={}, download_auth=[],
                     next_id=1000, base=srv.url)
    return srv


def release_backend(srv, **kw):
    return P.ReleaseBackend("owner/repo", "test-token", api=srv.url, uploads=srv.url, web=srv.url,
                            http=fast_http(), **kw)


class FakeS3(QuietHandler):
    """Path-style S3. Recomputes the SigV4 signature independently of the code under test and refuses a bad one."""
    secret = "sekret"
    key_id = "KEYID"
    region = "auto"

    def _verify(self, body):
        auth = self.headers.get("Authorization", "")
        m = re.match(r"AWS4-HMAC-SHA256 Credential=([^/]+)/(\d{8})/([^/]+)/s3/aws4_request, "
                     r"SignedHeaders=([^,]+), Signature=([0-9a-f]{64})$", auth)
        if not m:
            return "no or malformed Authorization"
        key_id, day, region, signed, sig = m.groups()
        if key_id != self.key_id or region != self.region:
            return "wrong credential scope"
        amz_date = self.headers.get("x-amz-date", "")
        if not amz_date.startswith(day):
            return "x-amz-date does not match the credential date"
        payload = self.headers.get("x-amz-content-sha256", "")
        if payload != hashlib.sha256(body).hexdigest():
            return "x-amz-content-sha256 is not the body hash"
        names = signed.split(";")
        if "host" not in names or "x-amz-date" not in names or "x-amz-content-sha256" not in names:
            return "required headers not signed"
        u = urllib.parse.urlsplit(self.path)
        canon_h = "".join(f"{n}:{' '.join(self.headers.get(n, '').split())}\n" for n in names)
        creq = "\n".join([self.command, u.path, u.query, canon_h, signed, payload])
        sts = "\n".join(["AWS4-HMAC-SHA256", amz_date, f"{day}/{region}/s3/aws4_request",
                         hashlib.sha256(creq.encode()).hexdigest()])
        k = ("AWS4" + self.secret).encode()
        for part in (day, region, "s3", "aws4_request"):
            k = hmac.new(k, part.encode(), hashlib.sha256).digest()
        want = hmac.new(k, sts.encode(), hashlib.sha256).hexdigest()
        return None if hmac.compare_digest(want, sig) else "signature mismatch"

    def _handle(self):
        s = self.state
        body = self.read_body()
        s["calls"].append((self.command, self.path))
        bad = self._verify(body)
        if bad:
            s["rejected"].append(bad)
            return self.send(403, f"<Error>{bad}</Error>".encode(), ctype="application/xml")
        if not self.path.startswith("/bucket/"):
            return self.send(404, b"no bucket")
        key = urllib.parse.unquote(self.path[len("/bucket/"):])
        if self.command == "PUT":
            s["objects"][key] = body
            return self.send(200)
        if key not in s["objects"]:
            return self.send(404, b"<Error>NoSuchKey</Error>", ctype="application/xml")
        data = s["objects"][key]
        self.send(200, data, {"Content-Length": str(len(data))} if self.command == "HEAD" else None,
                  ctype="application/octet-stream")

    do_GET = do_PUT = do_HEAD = _handle

    def send(self, status, body=b"", headers=None, ctype="application/json"):
        if self.command == "HEAD":   # HEAD carries the object's Content-Length, not 0
            self.send_response(status)
            self.send_header("Content-Length", (headers or {}).get("Content-Length", "0"))
            self.end_headers()
            return
        super().send(status, body, headers, ctype)


def s3_server():
    srv = Server(FakeS3)
    srv.state.update(objects={}, calls=[], rejected=[])
    return srv


def s3_backend(srv, name="r2", **kw):
    return P.S3Backend(srv.url, "bucket", "KEYID", "sekret", "auto", name=name, http=fast_http(), **kw)


class Helpers(unittest.TestCase):
    def test_norm_ext_and_sha(self):
        self.assertEqual(P.norm_ext("PDF"), ".pdf")
        self.assertEqual(P.norm_ext(".html"), ".html")
        self.assertEqual(P.norm_ext("../x"), ".bin")
        self.assertEqual(P.norm_ext(None), ".bin")
        with self.assertRaises(P.PergamonError):
            P.check_sha("abc")

    def test_sigv4_matches_aws_documentation_vector(self):
        # "GET Object" example, Signature Version 4 header-based auth (docs.aws.amazon.com, sig-v4-header-based-auth)
        hdrs = P.sigv4_headers(
            "GET", "https://examplebucket.s3.amazonaws.com/test.txt", {"Range": "bytes=0-9"},
            hashlib.sha256(b"").hexdigest(), "AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1", now=dt.datetime(2013, 5, 24, tzinfo=dt.timezone.utc))
        self.assertIn("SignedHeaders=host;range;x-amz-content-sha256;x-amz-date", hdrs["Authorization"])
        self.assertTrue(hdrs["Authorization"].endswith(
            "Signature=f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41"))


class GitBackendTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = pathlib.Path(self.tmp.name) / "output"
        self.store = P.Store(P.GitBackend(self.out / "raw", base=self.out))

    def test_put_get_has_and_locator_is_the_cache_path(self):
        rec = self.store.put(BODY, "pdf", {"url": "https://x"})
        self.assertEqual(rec["sha256"], SHA)
        self.assertEqual(rec["backend"], "git")
        self.assertEqual(rec["locator"], f"raw/{SHA}.pdf")
        self.assertEqual((self.out / rec["locator"]).read_bytes(), BODY)
        self.assertEqual(set(rec) - {"meta"}, {"sha256", "bytes", "ext", "backend", "locator", "stored_utc"})
        self.assertTrue(self.store.has(SHA))
        self.assertTrue(self.store.has(SHA, ".pdf"))
        self.assertFalse(self.store.has("0" * 64))
        self.assertEqual(self.store.get_verified(rec), BODY)
        self.assertEqual(self.store.get_verified(SHA), BODY)

    def test_tampered_file_is_refused(self):
        rec = self.store.put(BODY, ".pdf")
        (self.out / rec["locator"]).write_bytes(b"tampered")
        with self.assertRaises(P.HashMismatch):
            self.store.get_verified(rec)

    def test_missing_and_escaping_locators(self):
        with self.assertRaises(P.NotFound):
            self.store.get_verified("1" * 64)
        with self.assertRaises(P.PergamonError):
            self.store.primary.get("../../etc/passwd")

    def test_from_env_defaults_to_git(self):
        s = P.Store.from_env({}, git_root=self.out / "raw", git_base=self.out)
        self.assertEqual(s.backend_name, "git")
        with self.assertRaises(P.PergamonError):
            P.Store.from_env({"PERGAMON_BACKEND": "floppy"})


class ReleaseBackendTests(unittest.TestCase):
    def setUp(self):
        self.srv = github_server()
        self.addCleanup(self.srv.close)
        self.state = self.srv.state
        self.store = P.Store(release_backend(self.srv))

    def test_put_creates_prerelease_shard_uploads_and_downloads_without_token(self):
        rec = self.store.put(BODY, ".pdf")
        tag = "pergamon-" + SHA[:2]
        self.assertEqual(rec["backend"], "release")
        self.assertEqual(rec["locator"], f"{self.srv.url}/owner/repo/releases/download/{tag}/{SHA}.pdf")
        rel = self.state["releases"][tag]
        self.assertTrue(rel["prerelease"])
        self.assertEqual(rel["make_latest"], "false")
        self.assertEqual(self.state["uploads"], [SHA + ".pdf"])
        self.assertEqual(self.store.get_verified(rec), BODY)
        self.assertEqual(self.state["download_auth"], [None])   # public download carried no token

    def test_dedupe_second_put_uploads_nothing(self):
        self.store.put(BODY, ".pdf")
        fresh = P.Store(release_backend(self.srv))              # a new process: no in-memory cache
        rec = fresh.put(BODY, ".pdf")
        self.assertEqual(self.state["uploads"], [SHA + ".pdf"])
        self.assertTrue(fresh.has(SHA, ".pdf"))
        self.assertTrue(fresh.has(SHA))
        self.assertFalse(fresh.has("f" * 64))
        self.assertEqual(rec["bytes"], len(BODY))

    def test_hash_mismatch_is_refused_and_never_returned(self):
        rec = self.store.put(BODY, ".pdf")
        self.state["corrupt"][SHA + ".pdf"] = b"swapped bytes"
        with self.assertRaises(P.HashMismatch):
            self.store.get_verified(rec)

    def test_get_by_sha_alone_finds_the_extension(self):
        self.store.put(BODY, ".html")
        self.assertEqual(self.store.get_verified(SHA), BODY)

    def test_missing_asset_is_not_found(self):
        with self.assertRaises(P.NotFound):
            self.store.get_verified("a" * 64)

    def test_rate_limit_waits_as_told_then_succeeds(self):
        waits = []
        backend = P.ReleaseBackend("owner/repo", "test-token", api=self.srv.url, uploads=self.srv.url, web=self.srv.url,
                                   http=P.Http(retries=3, sleep=waits.append))
        self.state["faults"]["rate_limit_once"] = True
        rec = P.Store(backend).put(BODY, ".pdf")
        self.assertEqual(waits[0], 7.0)
        self.assertEqual(rec["sha256"], SHA)

    def test_403_secondary_limit_without_headers_waits_a_minute(self):
        self.assertEqual(P.Http._rate_limit_wait(403, {}, b'{"message":"You have exceeded a secondary rate limit"}'), 60.0)
        self.assertIsNone(P.Http._rate_limit_wait(403, {}, b'{"message":"Resource not accessible"}'))
        self.assertIsNone(P.Http._rate_limit_wait(404, {}, b""))

    def test_write_interval_spaces_out_writes_not_reads(self):
        waits = []
        http = P.Http(sleep=waits.append, write_interval=5.0)
        backend = P.ReleaseBackend("owner/repo", "test-token", api=self.srv.url, uploads=self.srv.url, web=self.srv.url,
                                   http=http)
        P.Store(backend).put(BODY, ".pdf")                      # release POST then asset POST: two writes
        self.assertTrue(any(0 < w <= 5.0 for w in waits))
        self.assertEqual(P.Store.from_env({"PERGAMON_BACKEND": "release", "GITHUB_REPOSITORY": "o/r",
                                           "PERGAMON_WRITE_INTERVAL": "8"}).primary.http.write_interval, 8.0)

    def test_502_leaving_a_starter_asset_is_cleaned_and_retried(self):
        self.state["faults"]["starter_502_once"] = True
        rec = self.store.put(BODY, ".pdf")
        self.assertIn(("DELETE", self.state["calls"][[c[0] for c in self.state["calls"]].index("DELETE")][1]),
                      self.state["calls"])
        self.assertEqual(self.store.get_verified(rec), BODY)
        self.assertEqual(len([a for a in self.state["assets"].values() if a["state"] == "uploaded"]), 1)

    def test_422_already_exists_race_is_treated_as_dedupe(self):
        backend = release_backend(self.srv)
        backend._release("pergamon-" + SHA[:2])               # release exists; asset appears behind our back
        rid = backend._releases["pergamon-" + SHA[:2]]["id"]
        self.state["assets"][1] = {"id": 1, "rid": rid, "tag": "pergamon-" + SHA[:2], "name": SHA + ".pdf",
                                   "data": BODY, "state": "uploaded"}
        rec = P.Store(backend).put(BODY, ".pdf")                 # its asset cache is empty: sees the asset on listing
        self.assertEqual(self.state["uploads"], [])
        self.assertTrue(rec["locator"].endswith(SHA + ".pdf"))

    def test_assets_listing_follows_pages(self):
        backend = release_backend(self.srv)
        rel = backend._release("pergamon-aa")
        for i in range(130):
            self.state["assets"][2000 + i] = {"id": 2000 + i, "rid": rel["id"], "tag": "pergamon-aa",
                                              "name": f"n{i}.bin", "data": b"x", "state": "uploaded"}
        self.assertEqual(len(backend._assets("pergamon-aa")), 130)

    def test_shard_width_and_tag_prefix_are_configurable(self):
        backend = release_backend(self.srv, tag_prefix="pergamon-selftest", shard_hex=0)
        rec = P.Store(backend).put(BODY, ".txt")
        self.assertIn("/releases/download/pergamon-selftest/", rec["locator"])
        env = {"PERGAMON_BACKEND": "release", "GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "test-token",
               "PERGAMON_SHARD_HEX": "3"}
        self.assertEqual(P.Store.from_env(env).primary.tag_for(SHA), "pergamon-" + SHA[:3])

    def test_write_without_token_is_refused_but_read_needs_none(self):
        rec = self.store.put(BODY, ".pdf")
        ro = P.Store(P.ReleaseBackend("owner/repo", None, api=self.srv.url, uploads=self.srv.url, web=self.srv.url,
                                      http=fast_http()))
        self.assertEqual(ro.get_verified(rec), BODY)
        with self.assertRaises(P.PergamonError):
            ro.put(b"other", ".txt")

    def test_oversize_refused_before_any_request(self):
        class Big(bytes):
            def __len__(self):
                return P.GITHUB_FILE_LIMIT + 1
        with self.assertRaises(P.PergamonError):
            self.store.primary.put(Big(b""), "b" * 64, ".bin")
        self.assertEqual(self.state["calls"], [])


class S3BackendTests(unittest.TestCase):
    def setUp(self):
        self.srv = s3_server()
        self.addCleanup(self.srv.close)
        self.state = self.srv.state
        self.store = P.Store(s3_backend(self.srv))

    def test_put_get_has_with_valid_signatures(self):
        rec = self.store.put(BODY, ".pdf")
        self.assertEqual(rec["backend"], "r2")
        self.assertEqual(rec["locator"], f"{SHA[:2]}/{SHA}.pdf")
        self.assertEqual(self.state["objects"][rec["locator"]], BODY)
        self.assertEqual(self.store.get_verified(rec), BODY)
        self.assertTrue(self.store.has(SHA, ".pdf"))
        self.assertFalse(self.store.has("e" * 64, ".pdf"))
        self.assertEqual(self.state["rejected"], [])

    def test_dedupe_does_not_put_twice(self):
        self.store.put(BODY, ".pdf")
        self.store.put(BODY, ".pdf")
        self.assertEqual([c for c in self.state["calls"] if c[0] == "PUT"].__len__(), 1)

    def test_server_rejects_wrong_secret(self):
        bad = P.Store(P.S3Backend(self.srv.url, "bucket", "KEYID", "wrong", "auto", http=fast_http()))
        with self.assertRaises(P.PergamonError):
            bad.put(BODY, ".pdf")
        self.assertIn("signature mismatch", self.state["rejected"])

    def test_hash_mismatch_refused(self):
        rec = self.store.put(BODY, ".pdf")
        self.state["objects"][rec["locator"]] = b"corrupted"
        with self.assertRaises(P.HashMismatch):
            self.store.get_verified(rec)

    def test_mirror_is_written_and_used_when_primary_lacks_the_bytes(self):
        mirror_srv = s3_server()
        self.addCleanup(mirror_srv.close)
        store = P.Store(s3_backend(self.srv, "r2"), [s3_backend(mirror_srv, "b2")])
        rec = store.put(BODY, ".pdf")
        self.assertEqual(rec["mirrors"], [{"backend": "b2", "locator": rec["locator"]}])
        self.assertEqual(mirror_srv.state["objects"][rec["locator"]], BODY)
        self.state["objects"].clear()                           # primary loses it
        self.assertEqual(store.get_verified(rec), BODY)
        mirror_srv.state["objects"][rec["locator"]] = b"bad"     # now both are wrong
        self.state["objects"][rec["locator"]] = b"worse"
        with self.assertRaises(P.HashMismatch):
            store.get_verified(rec)

    def test_mirror_failure_is_recorded_not_fatal(self):
        dead = P.S3Backend("http://127.0.0.1:1", "bucket", "KEYID", "sekret", "auto", name="b2",
                           http=P.Http(retries=0, sleep=no_sleep, timeout=2))
        rec = P.Store(s3_backend(self.srv), [dead]).put(BODY, ".pdf")
        self.assertEqual(rec["sha256"], SHA)
        self.assertEqual(len(rec["mirror_errors"]), 1)
        self.assertNotIn("mirrors", rec)

    def test_from_env_builds_r2_with_mirror(self):
        env = {"PERGAMON_BACKEND": "r2", "PERGAMON_S3_ENDPOINT": self.srv.url, "PERGAMON_S3_BUCKET": "bucket",
               "PERGAMON_S3_KEY_ID": "KEYID", "PERGAMON_S3_SECRET": "sekret",
               "PERGAMON_MIRROR_ENDPOINT": self.srv.url, "PERGAMON_MIRROR_BUCKET": "bucket",
               "PERGAMON_MIRROR_KEY_ID": "KEYID", "PERGAMON_MIRROR_SECRET": "sekret"}
        store = P.Store.from_env(env, http=fast_http())
        self.assertEqual((store.primary.name, store.mirrors[0].name), ("r2", "b2"))
        self.assertEqual(store.primary.region, "auto")
        with self.assertRaises(P.PergamonError):
            P.Store.from_env({"PERGAMON_BACKEND": "r2"})


class SwitchTests(unittest.TestCase):
    """The point of the design: records written under one backend still verify after the configuration changes."""

    def test_release_records_survive_a_switch_to_r2_and_back(self):
        gh, s3 = github_server(), s3_server()
        self.addCleanup(gh.close)
        self.addCleanup(s3.close)
        old = P.Store(release_backend(gh))
        rec = old.put(BODY, ".pdf")
        new = P.Store(s3_backend(s3))                             # configuration now says r2
        self.assertEqual(new.get_verified(rec), BODY)             # the old record's own URL is still honoured
        self.assertEqual(new.put(BODY, ".pdf")["backend"], "r2")  # new writes go to r2
        gh.state["assets"].clear()                                # GitHub copy gone
        self.assertEqual(new.get_verified(rec), BODY)             # falls back to the configured backend by hash

    def test_reader_with_default_git_config_fetches_a_release_record_without_a_token(self):
        gh = github_server()
        self.addCleanup(gh.close)
        rec = P.Store(release_backend(gh)).put(BODY, ".pdf")
        with tempfile.TemporaryDirectory() as td:
            reader = P.Store.from_env({}, git_root=pathlib.Path(td) / "raw")   # what the claim checker will build
            self.assertEqual(reader.backend_name, "git")
            self.assertEqual(reader.get_verified(rec), BODY)
            self.assertEqual(gh.state["download_auth"], [None])

    def test_migrate_dir_uploads_verified_files_and_resumes(self):
        gh = github_server()
        self.addCleanup(gh.close)
        store = P.Store(release_backend(gh))
        with tempfile.TemporaryDirectory() as td:
            folder, manifest = pathlib.Path(td) / "raw", pathlib.Path(td) / "m" / "MANIFEST.jsonl"
            folder.mkdir()
            good = {hashlib.sha256(b).hexdigest(): b for b in (b"one", b"two", BODY)}
            for sha, b in good.items():
                (folder / (sha + ".pdf")).write_bytes(b)
            (folder / ("0" * 64 + ".pdf")).write_bytes(b"name does not match bytes")
            c1 = P.migrate_dir(store, folder, manifest, limit=2, log=lambda *_: None)
            self.assertEqual(c1["uploaded"], 2)
            c2 = P.migrate_dir(store, folder, manifest, log=lambda *_: None)
            self.assertEqual((c2["uploaded"], c2["skipped_in_manifest"], c2["bad_name_or_hash"]), (1, 2, 1))
            rows = [json.loads(x) for x in manifest.read_text().splitlines()]
            self.assertEqual({r["sha256"] for r in rows}, set(good))
            self.assertTrue(all((folder / (r["sha256"] + ".pdf")).is_file() for r in rows))   # nothing deleted
            self.assertEqual(len(gh.state["uploads"]), 3)


if __name__ == "__main__":
    unittest.main()
