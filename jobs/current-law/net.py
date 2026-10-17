"""Polite, cached downloads with source custody (sha256, size, time, route).

* At most one request per ``min_interval`` seconds to each host.
* robots.txt is read once per host and obeyed; a disallowed URL is never
  fetched (the attempt is logged instead).
* 429 / 5xx answers are retried with back-off, honouring Retry-After.
* Every finished download is stored in the cache together with a small
  ``.meta.json`` file, so a rerun reuses the bytes and the original retrieval
  time instead of downloading again.
"""

import hashlib
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone

USER_AGENT = "EO-afterlife-research/1.0 (owner-run research; contact via repo)"


class RobotsDisallowed(Exception):
    pass


class FetchFailed(Exception):
    pass


class WrongContent(FetchFailed):
    pass


def check_content(path, expect):
    """Raise WrongContent unless the file at ``path`` looks like ``expect``.

    expect: None (no check), "zip", "xml", "json" or "html". An HTML error,
    maintenance or CAPTCHA page served with HTTP 200 fails every check except
    "html".
    """
    if not expect:
        return
    path = pathlib.Path(path)
    with open(path, "rb") as f:
        head = f.read(4096)
    lead = head.lstrip(b"\xef\xbb\xbf \t\r\n")
    low = lead[:2048].lower()
    if expect == "zip":
        import zipfile
        if not head.startswith(b"PK\x03\x04") or not zipfile.is_zipfile(path):
            raise WrongContent(f"not a ZIP file (starts {head[:40]!r})")
    elif expect == "xml":
        if not lead.startswith(b"<") or b"<html" in low or b"<!doctype html" in low:
            raise WrongContent(f"not an XML document (starts {lead[:60]!r})")
    elif expect == "json":
        try:
            json.loads(path.read_bytes().decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise WrongContent(f"not valid JSON ({str(exc)[:80]}; starts {lead[:60]!r})")
    elif expect == "html":
        if b"<" not in lead[:200]:
            raise WrongContent(f"not an HTML page (starts {lead[:60]!r})")
    else:
        raise ValueError(f"unknown expect={expect!r}")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


class Fetcher:
    def __init__(self, cache_dir, log_path=None, min_interval=1.1, retries=4, timeout=120, offline=False):
        self.cache = pathlib.Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.log_path = pathlib.Path(log_path) if log_path else None
        self.min_interval = min_interval
        self.retries = retries
        self.timeout = timeout
        self.offline = offline
        self._last = {}
        self._robots = {}
        self.robots_retry_wait = 5
        self.requests_made = 0
        self.cache_hits = 0

    # ----------------------------------------------------------- helpers --
    def _log(self, **row):
        if self.log_path:
            row.setdefault("time_utc", utc_now())
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _wait(self, host):
        gap = time.monotonic() - self._last.get(host, 0)
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self._last[host] = time.monotonic()

    def _open(self, url, headers=None):
        host = urllib.parse.urlsplit(url).netloc
        self._wait(host)
        self.requests_made += 1
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
        return urllib.request.urlopen(req, timeout=self.timeout)

    def _read_robots(self, robots_url):
        """Return a parser, or None when robots.txt could not be read (host skipped).

        Same convention as urllib.robotparser.read(): 401/403 -> disallow all,
        other 4xx (e.g. 404, no robots.txt) -> allow all. A 5xx answer or a
        network error is retried once; if it still fails, the host is skipped
        rather than assumed to permit crawling.
        """
        rp = urllib.robotparser.RobotFileParser()
        for attempt in (1, 2):
            try:
                with self._open(robots_url) as r:
                    rp.parse(r.read().decode("utf-8", "replace").splitlines())
                self._log(url=robots_url, outcome="robots_read", attempt=attempt)
                return rp
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 403):
                    rp.disallow_all = True
                    self._log(url=robots_url, outcome="robots_forbidden_disallow_all", code=exc.code)
                    return rp
                if 400 <= exc.code < 500:
                    rp.allow_all = True
                    self._log(url=robots_url, outcome="robots_absent_allow_all", code=exc.code)
                    return rp
                self._log(url=robots_url, outcome="robots_error", code=exc.code, attempt=attempt)
            except Exception as exc:
                self._log(url=robots_url, outcome="robots_error", error=str(exc)[:200], attempt=attempt)
            if attempt == 1:
                time.sleep(self.robots_retry_wait)
        self._log(url=robots_url, outcome="robots_unavailable_host_skipped")
        return None

    def allowed(self, url):
        parts = urllib.parse.urlsplit(url)
        host = parts.netloc
        if host not in self._robots:
            self._robots[host] = self._read_robots(f"{parts.scheme}://{host}/robots.txt")
        rp = self._robots[host]
        if rp is None:
            raise FetchFailed(f"robots.txt for {host} could not be read; host skipped: {url}")
        return rp.can_fetch(USER_AGENT, url)

    def _drop(self, target, meta_path):
        for p in (target, meta_path):
            try:
                p.unlink()
            except FileNotFoundError:
                pass

    # -------------------------------------------------------------- main --
    def get(self, url, rel_path, route, headers=None, refresh=False, expect=None):
        """Download ``url`` into ``<cache>/<rel_path>`` (or reuse it).

        ``expect`` ("zip", "xml", "json", "html") checks that the bytes are
        that kind of document; a wrong body (an error or CAPTCHA page sent
        with HTTP 200) is deleted, not cached, and raises WrongContent. A
        cached file that fails the check is deleted and fetched again.

        Returns a dict: url, final_url, sha256, bytes, content_type,
        retrieved_utc, route, cache_path (relative to the cache), path
        (absolute), from_cache, last_modified.
        """
        target = self.cache / rel_path
        meta_path = target.with_name(target.name + ".meta.json")
        if target.exists() and meta_path.exists() and not refresh:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("sha256") == sha256_file(target):
                try:
                    check_content(target, expect)
                except WrongContent as exc:
                    self._log(url=url, outcome="cache_wrong_content_deleted", error=str(exc)[:200], route=route)
                    self._drop(target, meta_path)
                else:
                    self.cache_hits += 1
                    meta.update(path=str(target), from_cache=True)
                    self._log(url=url, outcome="cache_hit", sha256=meta["sha256"], route=route)
                    return meta
        if self.offline:
            raise FetchFailed(f"offline mode and not cached: {url}")
        if not url.startswith("https://"):
            raise FetchFailed(f"refusing non-https url {url}")
        if not self.allowed(url):
            self._log(url=url, outcome="robots_disallowed", route=route)
            raise RobotsDisallowed(url)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".part")
        delay = 5
        last_error = None
        for attempt in range(1, self.retries + 1):
            try:
                with self._open(url, headers) as r:
                    h = hashlib.sha256()
                    size = 0
                    with open(tmp, "wb") as f:
                        for block in iter(lambda: r.read(1 << 20), b""):
                            f.write(block)
                            h.update(block)
                            size += len(block)
                    meta = {
                        "url": url,
                        "final_url": r.geturl(),
                        "sha256": h.hexdigest(),
                        "bytes": size,
                        "content_type": r.headers.get("Content-Type", ""),
                        "last_modified": r.headers.get("Last-Modified", ""),
                        "retrieved_utc": utc_now(),
                        "route": route,
                        "cache_path": str(pathlib.PurePosixPath(*pathlib.Path(rel_path).parts)),
                    }
                try:
                    check_content(tmp, expect)
                except WrongContent as exc:
                    tmp.unlink()
                    self._log(url=url, outcome="wrong_content", attempt=attempt, error=str(exc)[:200],
                              content_type=meta["content_type"], bytes=size, sha256=meta["sha256"], route=route)
                    last_error = f"wrong content: {exc}"
                    if attempt >= 2:  # one retry (maintenance pages pass); a CAPTCHA page will not
                        raise WrongContent(f"{url}: {exc}")
                    time.sleep(delay)
                    delay *= 2
                    continue
                tmp.replace(target)
                meta_path.write_text(json.dumps(meta, indent=1), encoding="utf-8")
                self._log(outcome="downloaded", attempt=attempt, **{k: meta[k] for k in ("url", "sha256", "bytes", "route")})
                meta.update(path=str(target), from_cache=False)
                return meta
            except WrongContent:
                raise
            except urllib.error.HTTPError as exc:
                last_error = f"HTTP {exc.code}"
                self._log(url=url, outcome="http_error", code=exc.code, attempt=attempt, route=route)
                if exc.code not in (408, 429, 500, 502, 503, 504):
                    break
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                wait = int(retry_after) if (retry_after or "").isdigit() else delay
                time.sleep(min(wait, 300))
                delay *= 2
            except Exception as exc:  # network trouble: retry
                last_error = str(exc)[:200]
                self._log(url=url, outcome="error", error=last_error, attempt=attempt, route=route)
                time.sleep(delay)
                delay *= 2
        if tmp.exists():
            tmp.unlink()
        raise FetchFailed(f"{url}: {last_error}")
