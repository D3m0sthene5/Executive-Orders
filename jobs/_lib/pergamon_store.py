"""Pergamon: a content-addressed byte store keyed by SHA-256, with the bytes kept outside git.

Named for the Library of Pergamon, which rivalled Alexandria. The repository holds only small manifests
(SHA-256, size, extension, backend, locator); the bytes live in a backend chosen by configuration:

    PERGAMON_BACKEND=git      (default) write into a folder, the old behaviour
    PERGAMON_BACKEND=release  GitHub Release assets, sharded by hash prefix (interim store)
    PERGAMON_BACKEND=r2       S3-compatible bucket (Cloudflare R2), AWS SigV4 signed here, optional mirror

Whatever the backend, trust comes from one rule: `get_verified` returns bytes only if they hash exactly to the
recorded SHA-256, so a store is never an authority, only a place to find bytes. Moving from release assets to R2
is a change of environment variables; records written earlier keep working because each carries its backend and
locator, and `get_verified` also tries the configured backend and mirrors by the hash-derived key.

Standard library only. Offline tests: test_pergamon_store.py. Documentation: research/encyclopedie-campaign/storage/.

Environment
    PERGAMON_BACKEND             git | release | r2 (alias s3)
    GITHUB_TOKEN                 release backend upload only; downloads never send a token
    PERGAMON_GITHUB_TOKEN        same, and wins over GITHUB_TOKEN (a runner secret with contents: write)
    GITHUB_REPOSITORY            owner/repo for the release backend
    GITHUB_API_URL, GITHUB_SERVER_URL, PERGAMON_UPLOADS_URL   overrides (defaults: api.github.com, github.com,
                                 uploads.github.com)
    PERGAMON_TAG_PREFIX          default "pergamon-"; the tag is the prefix plus the first PERGAMON_SHARD_HEX
                                 (default 2) hex digits of the hash
    PERGAMON_S3_ENDPOINT, PERGAMON_S3_BUCKET, PERGAMON_S3_KEY_ID, PERGAMON_S3_SECRET, PERGAMON_S3_REGION
                                 (default "auto"), PERGAMON_S3_PUBLIC_BASE (optional tokenless read URL),
                                 PERGAMON_S3_PREFIX (optional key prefix)
    PERGAMON_MIRROR_*            same names, a second S3 endpoint (Backblaze B2) written on every put
    PERGAMON_WRITE_INTERVAL      seconds between release writes (8 keeps a bulk load under GitHub's 500 an hour)
    PERGAMON_GIT_DIR             folder for the git backend (default output/raw)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import hmac
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_MAX_GET_BYTES = 256 * 1024 * 1024   # a release asset may reach 2 GiB; refuse anything larger by default
GITHUB_ASSET_LIMIT = 1000                   # docs.github.com: "Up to 1000 release assets ... a single release"
GITHUB_FILE_LIMIT = 2 * 1024 ** 3 - 1       # docs.github.com: "Each file included in a release must be under 2 GiB"
KNOWN_EXTS = (".pdf", ".html", ".htm", ".txt", ".xml", ".json", ".bin")
USER_AGENT = "EO-Historical-Research/1.0 (https://github.com/D3m0sthene5/Executive-Orders; pergamon store)"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class PergamonError(Exception):
    """Any store failure."""


class NotFound(PergamonError):
    """The backend does not hold these bytes."""


class HashMismatch(PergamonError):
    """Bytes came back that do not hash to the recorded SHA-256. They are never returned."""


class Unavailable(PergamonError):
    """The backend is unreachable or refused after retries."""


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def norm_ext(ext) -> str:
    """'.pdf' for 'pdf', '.PDF' or '.pdf'; '.bin' for anything that is not a short alphanumeric extension."""
    e = (ext or "").strip().lower()
    if e and not e.startswith("."):
        e = "." + e
    return e if re.fullmatch(r"\.[a-z0-9]{1,8}", e) else ".bin"


def check_sha(sha) -> str:
    sha = (sha or "").strip().lower()
    if not SHA_RE.match(sha):
        raise PergamonError(f"not a 64-hex SHA-256: {str(sha)[:80]!r}")
    return sha


def verify_bytes(data: bytes, sha: str, where: str = "") -> bytes:
    got = sha256_hex(data)
    if got != sha:
        raise HashMismatch(f"bytes from {where or 'the store'} hash to {got}, not the recorded {sha}; refused")
    return data


# ---------------------------------------------------------------------------------------------------------
# HTTP with retry, rate-limit handling and no dependency beyond urllib
# ---------------------------------------------------------------------------------------------------------

class Http:
    """One place for retries: 5xx and network errors back off; 429 and GitHub's 403 rate limit wait as told."""

    def __init__(self, retries=4, timeout=120, sleep=time.sleep, max_sleep=120, backoff=2.0, write_interval=0.0):
        self.retries, self.timeout, self.sleep, self.max_sleep, self.backoff = retries, timeout, sleep, max_sleep, backoff
        self.write_interval, self._last_write = float(write_interval), 0.0   # GitHub: 80 writes a minute, 500 an hour
        self.waited = 0.0

    def _wait(self, seconds):
        seconds = max(0.0, min(float(seconds), self.max_sleep))
        self.waited += seconds
        if seconds:
            self.sleep(seconds)

    @staticmethod
    def _rate_limit_wait(status, headers, body=b""):
        """Seconds to wait if this response is a rate limit, else None."""
        h = {k.lower(): v for k, v in headers.items()}
        limited = status == 403 and (h.get("x-ratelimit-remaining") == "0" or "retry-after" in h
                                     or b"rate limit" in body[:2000].lower())
        if status == 429 or limited:
            if "retry-after" in h:
                try:
                    return float(h["retry-after"])
                except ValueError:
                    pass
            reset = h.get("x-ratelimit-reset")
            if reset and reset.isdigit():
                return max(1.0, int(reset) - time.time())
            return 60.0   # GitHub: with neither header, wait at least a minute
        return None

    def request(self, method, url, headers=None, data=None):
        """(status, headers, body); a 4xx other than a rate limit is returned, not raised."""
        last = None
        for attempt in range(self.retries + 1):
            if self.write_interval and method not in ("GET", "HEAD"):
                gap = self.write_interval - (time.monotonic() - self._last_write)
                if gap > 0:
                    self._wait(gap)
                self._last_write = time.monotonic()
            req = urllib.request.Request(url, data=data, method=method, headers=dict(headers or {}))
            req.add_header("User-Agent", USER_AGENT)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return r.status, dict(r.headers.items()), r.read()
            except urllib.error.HTTPError as e:
                status, hdrs = e.code, dict(e.headers.items()) if e.headers else {}
                try:
                    body = e.read()
                except Exception:  # noqa: BLE001
                    body = b""
                wait = self._rate_limit_wait(status, hdrs, body)
                if wait is not None and attempt < self.retries:
                    self._wait(wait)
                    last = f"HTTP {status} (rate limit)"
                    continue
                if status >= 500 and attempt < self.retries:
                    self._wait(self.backoff ** attempt)
                    last = f"HTTP {status}"
                    continue
                return status, hdrs, body
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                last = f"{type(e).__name__}: {e}"
                if attempt < self.retries:
                    self._wait(self.backoff ** attempt)
                    continue
        raise Unavailable(f"{method} {url.split('?')[0]} failed after {self.retries + 1} tries: {last}")


# ---------------------------------------------------------------------------------------------------------
# Backends. Each: put(raw, sha, ext) -> locator, has(sha, ext) -> bool, get(locator) -> bytes (unverified),
# locator_for(sha, ext) -> locator.
# ---------------------------------------------------------------------------------------------------------

class GitBackend:
    """A folder. `base` is what a locator is relative to (the job's output folder, so a locator is its cache_path)."""
    name = "git"

    def __init__(self, root, base=None):
        self.root = Path(root)
        self.base = Path(base) if base is not None else self.root

    def locator_for(self, sha, ext):
        return (self.root / (sha + ext)).relative_to(self.base).as_posix()

    def _path(self, locator):
        p = (self.base / locator).resolve()
        try:
            p.relative_to(self.base.resolve())
        except ValueError:
            raise PergamonError(f"locator escapes the store folder: {locator!r}")
        return p

    def has(self, sha, ext=None):
        if ext:
            return (self.root / (sha + ext)).is_file()
        return any((self.root / (sha + e)).is_file() for e in KNOWN_EXTS)

    def put(self, raw, sha, ext):
        self.root.mkdir(parents=True, exist_ok=True)
        dst = self.root / (sha + ext)
        if not (dst.is_file() and dst.stat().st_size == len(raw)):
            tmp = dst.with_name(dst.name + ".tmp")
            tmp.write_bytes(raw)
            os.replace(tmp, dst)
        return self.locator_for(sha, ext)

    def get(self, locator, max_bytes=DEFAULT_MAX_GET_BYTES):
        p = self._path(locator)
        if not p.is_file():
            raise NotFound(f"no file {locator}")
        if p.stat().st_size > max_bytes:
            raise PergamonError(f"{locator} exceeds {max_bytes} bytes")
        return p.read_bytes()


class ReleaseBackend:
    """GitHub Release assets: tag pergamon-<hash prefix>, asset <sha256><ext>.

    Limits (docs.github.com/en/repositories/releasing-projects-on-github/about-releases, checked 2026-11-06):
    up to 1000 assets per release, each file under 2 GiB, no limit on total size or bandwidth. Two hex digits give
    256 releases, so the store holds 256,000 files before any release is full; the average is about 4 per release
    at 1,000 files and about 43 at 11,000.
    """
    name = "release"

    def __init__(self, repo, token=None, api="https://api.github.com", uploads="https://uploads.github.com",
                 web="https://github.com", tag_prefix="pergamon-", shard_hex=2, prerelease=True,
                 release_name="Pergamon store shard {shard}", release_body=None, http=None):
        if not repo or "/" not in repo:
            raise PergamonError("release backend needs GITHUB_REPOSITORY as owner/repo")
        self.repo, self.token = repo, token
        self.api, self.uploads, self.web = api.rstrip("/"), uploads.rstrip("/"), web.rstrip("/")
        self.tag_prefix, self.shard_hex, self.prerelease = tag_prefix, int(shard_hex), prerelease
        self.release_name = release_name
        self.release_body = release_body or (
            "Content-addressed source bytes kept outside git by Pergamon. Each asset is named <sha256><ext>; "
            "the repository holds the SHA-256 manifest, and a file counts only if it hashes exactly as recorded. "
            "This release is a store, not a source of authority.")
        self.http = http or Http()
        self._releases, self._assets_cache = {}, {}

    # --- naming
    def tag_for(self, sha):
        return self.tag_prefix + sha[:self.shard_hex]

    def locator_for(self, sha, ext):
        tag = self.tag_for(sha)
        return f"{self.web}/{self.repo}/releases/download/{urllib.parse.quote(tag)}/{sha}{ext}"

    # --- API plumbing
    def _api(self, method, path, body=None, ok=(200, 201, 204)):
        if not self.token:
            raise PergamonError("release backend needs GITHUB_TOKEN to write")
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        status, hdrs, raw = self.http.request(method, self.api + path, headers, data)
        parsed = None
        if raw:
            try:
                parsed = json.loads(raw.decode("utf-8", "replace"))
            except ValueError:
                parsed = None
        return status, parsed

    def _release(self, tag, create=True):
        if tag in self._releases:
            return self._releases[tag]
        status, rel = self._api("GET", f"/repos/{self.repo}/releases/tags/{urllib.parse.quote(tag)}")
        if status == 404:
            if not create:
                return None
            shard = tag[len(self.tag_prefix):] if tag.startswith(self.tag_prefix) else tag
            status, rel = self._api("POST", f"/repos/{self.repo}/releases", {
                "tag_name": tag, "name": self.release_name.format(shard=shard), "body": self.release_body,
                "draft": False, "prerelease": bool(self.prerelease), "make_latest": "false"})
            if status == 422:  # created concurrently by another worker
                status, rel = self._api("GET", f"/repos/{self.repo}/releases/tags/{urllib.parse.quote(tag)}")
        if status not in (200, 201) or not isinstance(rel, dict) or "id" not in rel:
            raise PergamonError(f"cannot get or create release {tag}: HTTP {status}: {str(rel)[:200]}")
        self._releases[tag] = rel
        return rel

    def _assets(self, tag, refresh=False):
        """name -> asset dict for every asset of the release (all pages)."""
        if tag in self._assets_cache and not refresh:
            return self._assets_cache[tag]
        rel = self._release(tag, create=False)
        out = {}
        if rel is not None:
            page = 1
            while True:
                status, items = self._api("GET", f"/repos/{self.repo}/releases/{rel['id']}/assets?per_page=100&page={page}")
                if status != 200 or not isinstance(items, list):
                    raise PergamonError(f"cannot list assets of {tag}: HTTP {status}")
                out.update({a["name"]: a for a in items if isinstance(a, dict) and "name" in a})
                if len(items) < 100:
                    break
                page += 1
        self._assets_cache[tag] = out
        return out

    # --- the backend interface
    def has(self, sha, ext=None):
        assets = self._assets(self.tag_for(sha))
        if ext:
            a = assets.get(sha + ext)
            return bool(a and a.get("state", "uploaded") == "uploaded")
        return any(n.startswith(sha + ".") and a.get("state", "uploaded") == "uploaded" for n, a in assets.items())

    def put(self, raw, sha, ext):
        if len(raw) > GITHUB_FILE_LIMIT:
            raise PergamonError(f"{len(raw)} bytes exceeds GitHub's per-file release limit (under 2 GiB)")
        tag, name = self.tag_for(sha), sha + ext
        rel = self._release(tag, create=True)
        for attempt in range(3):
            assets = self._assets(tag, refresh=attempt > 0)
            a = assets.get(name)
            if a is not None:
                if a.get("state", "uploaded") == "uploaded" and a.get("size") == len(raw):
                    return a.get("browser_download_url") or self.locator_for(sha, ext)   # dedupe: already there
                self._api("DELETE", f"/repos/{self.repo}/releases/assets/{a['id']}")      # starter or wrong size
                assets.pop(name, None)
            if len(assets) >= GITHUB_ASSET_LIMIT:
                raise PergamonError(f"release {tag} already holds {len(assets)} assets (limit 1000); use PERGAMON_SHARD_HEX=3")
            url = f"{self.uploads}/repos/{self.repo}/releases/{rel['id']}/assets?name={urllib.parse.quote(name)}"
            status, hdrs, body = self.http.request("POST", url, {
                "Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                "Content-Type": "application/octet-stream", "X-GitHub-Api-Version": "2022-11-28"}, raw)
            if status == 201:
                asset = json.loads(body.decode("utf-8", "replace"))
                self._assets(tag)[name] = asset
                return asset.get("browser_download_url") or self.locator_for(sha, ext)
            if status == 422 or status >= 500:
                continue      # already exists (race or a half-finished upload): re-list and decide
            raise PergamonError(f"upload of {name} failed: HTTP {status}: {body[:200]!r}")
        raise PergamonError(f"upload of {name} did not complete after 3 attempts")

    def get(self, locator, max_bytes=DEFAULT_MAX_GET_BYTES):
        status, hdrs, body = self.http.request("GET", locator, {"Accept": "application/octet-stream"})
        if status == 404:
            raise NotFound(f"HTTP 404 for {locator}")
        if status != 200:
            raise Unavailable(f"HTTP {status} for {locator}")
        if len(body) > max_bytes:
            raise PergamonError(f"{locator} exceeds {max_bytes} bytes")
        return body


# --- AWS Signature Version 4, standard library only -------------------------------------------------------

def _hmac(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def sigv4_headers(method, url, headers, payload_hash, key_id, secret, region="auto", service="s3", now=None):
    """Headers to send, including Authorization, for an S3-style request.

    `headers` are the extra headers to sign (Host is taken from the URL, x-amz-content-sha256 and x-amz-date are
    added). Everything passed in is signed. Verified against the AWS documentation's published GET Object example.
    """
    now = now or _dt.datetime.now(_dt.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    day = amz_date[:8]
    parts = urllib.parse.urlsplit(url)
    hdrs = {k.lower(): " ".join(str(v).split()) for k, v in (headers or {}).items()}
    hdrs.setdefault("host", parts.netloc)
    hdrs["x-amz-content-sha256"] = payload_hash
    hdrs["x-amz-date"] = amz_date
    signed = ";".join(sorted(hdrs))
    canonical_headers = "".join(f"{k}:{hdrs[k]}\n" for k in sorted(hdrs))
    canonical_uri = urllib.parse.quote(urllib.parse.unquote(parts.path) or "/", safe="/-_.~")
    query = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    canonical_query = "&".join(f"{urllib.parse.quote(k, safe='-_.~')}={urllib.parse.quote(v, safe='-_.~')}"
                               for k, v in sorted(query))
    canonical_request = "\n".join([method, canonical_uri, canonical_query, canonical_headers, signed, payload_hash])
    scope = f"{day}/{region}/{service}/aws4_request"
    to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope, sha256_hex(canonical_request.encode())])
    k = _hmac(("AWS4" + secret).encode(), day)
    for part in (region, service, "aws4_request"):
        k = _hmac(k, part)
    signature = hmac.new(k, to_sign.encode(), hashlib.sha256).hexdigest()
    out = dict(hdrs)
    out.pop("host", None)   # urllib adds Host itself; the signature already covers it
    out["Authorization"] = (f"AWS4-HMAC-SHA256 Credential={key_id}/{scope}, SignedHeaders={signed}, "
                            f"Signature={signature}")
    return out


class S3Backend:
    """An S3-compatible bucket, path-style (Cloudflare R2, Backblaze B2, MinIO). Key: <prefix><hash[:2]>/<sha><ext>."""

    def __init__(self, endpoint, bucket, key_id, secret, region="auto", public_base=None, prefix="", name="r2",
                 http=None):
        if not (endpoint and bucket and key_id and secret):
            raise PergamonError(f"{name}: endpoint, bucket, key id and secret are all required")
        self.endpoint, self.bucket = endpoint.rstrip("/"), bucket
        self.key_id, self.secret, self.region = key_id, secret, region or "auto"
        self.public_base = public_base.rstrip("/") if public_base else None
        self.prefix, self.name = prefix, name
        self.http = http or Http()

    def key_for(self, sha, ext):
        return f"{self.prefix}{sha[:2]}/{sha}{ext}"

    def locator_for(self, sha, ext):
        return self.key_for(sha, ext)

    def _url(self, key):
        return f"{self.endpoint}/{self.bucket}/{urllib.parse.quote(key, safe='/-_.~')}"

    def _signed(self, method, key, data=None, extra=None):
        payload_hash = sha256_hex(data or b"")
        url = self._url(key)
        hdrs = sigv4_headers(method, url, extra or {}, payload_hash, self.key_id, self.secret, self.region)
        return self.http.request(method, url, hdrs, data)

    def has(self, sha, ext=None):
        exts = [ext] if ext else list(KNOWN_EXTS)
        for e in exts:
            status, _, _ = self._signed("HEAD", self.key_for(sha, e))
            if status == 200:
                return True
            if status not in (403, 404):
                raise Unavailable(f"{self.name}: HEAD returned HTTP {status}")
        return False

    def put(self, raw, sha, ext):
        key = self.key_for(sha, ext)
        status, hdrs, _ = self._signed("HEAD", key)
        if status == 200 and int({k.lower(): v for k, v in hdrs.items()}.get("content-length", -1)) == len(raw):
            return key   # dedupe
        status, _, body = self._signed("PUT", key, raw, {"content-type": "application/octet-stream"})
        if status not in (200, 201):
            raise PergamonError(f"{self.name}: PUT {key} failed: HTTP {status}: {body[:200]!r}")
        return key

    def get(self, locator, max_bytes=DEFAULT_MAX_GET_BYTES):
        if self.public_base:
            status, _, body = self.http.request("GET", f"{self.public_base}/{urllib.parse.quote(locator, safe='/-_.~')}")
        else:
            status, _, body = self._signed("GET", locator)
        if status in (403, 404) and self.public_base is None:
            raise NotFound(f"{self.name}: HTTP {status} for {locator}")
        if status == 404:
            raise NotFound(f"{self.name}: HTTP 404 for {locator}")
        if status != 200:
            raise Unavailable(f"{self.name}: HTTP {status} for {locator}")
        if len(body) > max_bytes:
            raise PergamonError(f"{locator} exceeds {max_bytes} bytes")
        return body


# ---------------------------------------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------------------------------------

class Store:
    """A primary backend, optional mirrors, and the hash discipline on top."""

    def __init__(self, primary, mirrors=()):
        self.primary, self.mirrors = primary, list(mirrors)

    @property
    def backend_name(self):
        return self.primary.name

    def _by_name(self, name):
        for b in [self.primary] + self.mirrors:
            if b.name == name:
                return b
        if name == "release":   # downloads need no token: a locator is a public URL
            return ReleaseBackend("none/none", token=None)
        return None

    def put(self, raw: bytes, ext=".bin", meta=None) -> dict:
        """Store the bytes (deduplicated) and return the manifest record that goes into git."""
        if not isinstance(raw, (bytes, bytearray)):
            raise PergamonError("put needs bytes")
        raw, ext = bytes(raw), norm_ext(ext)
        sha = sha256_hex(raw)
        locator = self.primary.put(raw, sha, ext)
        rec = {"sha256": sha, "bytes": len(raw), "ext": ext, "backend": self.primary.name, "locator": locator,
               "stored_utc": utc_now()}
        mirrors, errors = [], []
        for m in self.mirrors:
            try:
                mirrors.append({"backend": m.name, "locator": m.put(raw, sha, ext)})
            except PergamonError as exc:
                errors.append(f"{m.name}: {exc}"[:300])
        if mirrors:
            rec["mirrors"] = mirrors
        if errors:
            rec["mirror_errors"] = errors
        if meta:
            rec["meta"] = meta
        return rec

    def has(self, sha, ext=None) -> bool:
        return self.primary.has(check_sha(sha), norm_ext(ext) if ext else None)

    def _candidates(self, sha, rec, ext):
        seen, out = set(), []

        def add(backend_name, locator):
            if locator and (backend_name, locator) not in seen:
                seen.add((backend_name, locator))
                out.append((backend_name, locator))
        if rec:
            add(rec.get("backend"), rec.get("locator"))
            for m in rec.get("mirrors") or []:
                add(m.get("backend"), m.get("locator"))
        exts = [norm_ext(rec.get("ext"))] if rec and rec.get("ext") else ([norm_ext(ext)] if ext else list(KNOWN_EXTS))
        for b in [self.primary] + self.mirrors:   # the configured backends, by derived key
            for e in exts:
                add(b.name, b.locator_for(sha, e))
        return out

    def get_verified(self, sha_or_record, ext=None, max_bytes=DEFAULT_MAX_GET_BYTES) -> bytes:
        """The bytes, only if they hash exactly to the SHA-256. Tries the record's locator, its mirrors, then the
        configured backends. Raises HashMismatch if any copy came back wrong and none was right, NotFound if none
        holds it, Unavailable if the failures were network failures."""
        rec = sha_or_record if isinstance(sha_or_record, dict) else None
        sha = check_sha(rec.get("sha256") if rec else sha_or_record)
        errors, mismatch, unavailable = [], None, False
        for backend_name, locator in self._candidates(sha, rec, ext):
            backend = self._by_name(backend_name)
            if backend is None:
                errors.append(f"{backend_name}: not configured")
                continue
            try:
                data = backend.get(locator, max_bytes=max_bytes)
                return verify_bytes(data, sha, f"{backend_name}:{locator}")
            except HashMismatch as exc:
                mismatch = mismatch or exc
                errors.append(str(exc))
            except NotFound as exc:
                errors.append(str(exc))
            except Unavailable as exc:
                unavailable = True
                errors.append(str(exc))
            except PergamonError as exc:
                errors.append(str(exc))
        if mismatch:
            raise mismatch
        msg = f"{sha}: not retrievable ({'; '.join(errors[:4])})"
        raise (Unavailable(msg) if unavailable else NotFound(msg))

    @classmethod
    def from_env(cls, env=None, git_root=None, git_base=None, http=None):
        env = os.environ if env is None else env
        kind = (env.get("PERGAMON_BACKEND") or "git").strip().lower()

        def s3(prefix, name):
            return S3Backend(env.get(prefix + "ENDPOINT"), env.get(prefix + "BUCKET"), env.get(prefix + "KEY_ID"),
                             env.get(prefix + "SECRET"), env.get(prefix + "REGION") or "auto",
                             env.get(prefix + "PUBLIC_BASE"), env.get(prefix + "PREFIX") or "", name, http)
        if kind == "git":
            return cls(GitBackend(git_root or env.get("PERGAMON_GIT_DIR") or "output/raw", git_base))
        if kind == "release":
            primary = ReleaseBackend(
                env.get("GITHUB_REPOSITORY"), env.get("PERGAMON_GITHUB_TOKEN") or env.get("GITHUB_TOKEN"),
                api=env.get("GITHUB_API_URL") or "https://api.github.com",
                uploads=env.get("PERGAMON_UPLOADS_URL") or "https://uploads.github.com",
                web=env.get("GITHUB_SERVER_URL") or "https://github.com",
                tag_prefix=env.get("PERGAMON_TAG_PREFIX") or "pergamon-",
                shard_hex=int(env.get("PERGAMON_SHARD_HEX") or 2),
                http=http or Http(write_interval=float(env.get("PERGAMON_WRITE_INTERVAL") or 0)))
            return cls(primary)
        if kind in ("r2", "s3"):
            mirrors = [s3("PERGAMON_MIRROR_", "b2")] if env.get("PERGAMON_MIRROR_ENDPOINT") else []
            return cls(s3("PERGAMON_S3_", kind), mirrors)
        raise PergamonError(f"PERGAMON_BACKEND={kind!r}: expected git, release or r2")


# ---------------------------------------------------------------------------------------------------------
# Migration of files already committed to git (never deletes them)
# ---------------------------------------------------------------------------------------------------------

def migrate_dir(store, folder, manifest, limit=None, log=print):
    """Upload every <sha256>.<ext> file in `folder` whose bytes hash to its name; append one manifest record per
    file to `manifest` (JSONL). Files already in the manifest are skipped, so a run can be repeated or resumed."""
    folder, manifest = Path(folder), Path(manifest)
    done = set()
    if manifest.is_file():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            try:
                done.add(json.loads(line)["sha256"])
            except (ValueError, KeyError):
                pass
    counts = {"uploaded": 0, "skipped_in_manifest": 0, "bad_name_or_hash": 0, "failed": 0, "bytes": 0}
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("a", encoding="utf-8") as out:
        for p in sorted(folder.iterdir()):
            if not p.is_file() or p.suffix == ".tmp":
                continue
            sha = p.name.split(".")[0]
            if sha in done:
                counts["skipped_in_manifest"] += 1
                continue
            if limit is not None and counts["uploaded"] >= limit:
                break
            raw = p.read_bytes()
            if not SHA_RE.match(sha) or sha256_hex(raw) != sha:
                counts["bad_name_or_hash"] += 1
                log(f"skip {p.name}: name is not the SHA-256 of the bytes")
                continue
            try:
                rec = store.put(raw, p.suffix)
            except PergamonError as exc:
                counts["failed"] += 1
                log(f"FAILED {p.name}: {exc}")
                continue
            out.write(json.dumps(rec, sort_keys=True) + "\n")
            out.flush()
            counts["uploaded"] += 1
            counts["bytes"] += len(raw)
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pergamon content-addressed store (backend from PERGAMON_BACKEND)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("put", help="store a file; prints its manifest record")
    p.add_argument("file")
    p = sub.add_parser("get", help="fetch bytes by SHA-256 (verified) to a file")
    p.add_argument("sha256")
    p.add_argument("out")
    p.add_argument("--ext", default=None)
    p = sub.add_parser("has", help="exit 0 if the store holds the SHA-256")
    p.add_argument("sha256")
    p.add_argument("--ext", default=None)
    p = sub.add_parser("migrate", help="upload files named <sha256>.<ext> from a folder; never deletes them")
    p.add_argument("--dir", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--limit", type=int, default=None)
    a = ap.parse_args(argv)
    store = Store.from_env()
    if a.cmd == "put":
        f = Path(a.file)
        print(json.dumps(store.put(f.read_bytes(), f.suffix), indent=1, sort_keys=True))
    elif a.cmd == "get":
        Path(a.out).write_bytes(store.get_verified(a.sha256, ext=a.ext))
    elif a.cmd == "has":
        sys.exit(0 if store.has(a.sha256, a.ext) else 1)
    elif a.cmd == "migrate":
        print(json.dumps(migrate_dir(store, a.dir, a.manifest, a.limit), sort_keys=True))


if __name__ == "__main__":
    main()
