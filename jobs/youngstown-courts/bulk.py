"""CourtListener bulk files: HTTP range source, streaming row scanner, segment workers. Standard library only.

The bulk CSVs are public (S3 bucket com-courtlistener-storage, CC0 / Public Domain Mark) and need no account.
Rows are quoted CSV whose fields hold newlines, so rows are split on the one pattern that can only start a row:
a newline, a quote, the numeric id, a quote, a comma, a quote and a timestamp. Inside a quoted field a quote is
always doubled, so that pattern never occurs in text.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_lib"))
import bz2seg  # noqa: E402

csv.field_size_limit(min(2 ** 31 - 1, 10 ** 9))

BUCKET = "https://com-courtlistener-storage.s3-us-west-2.amazonaws.com"
MARK = re.compile(rb'\n"(\d+)","\d{4}-\d\d-\d\d \d\d:\d\d')
PREFILTER = re.compile(rb"xecutive|XECUTIVE|E\.\s?O\.|\bEOs?\b|Exec\.|Ex\.\s?Ord")
KEEP_BYTES = 64 * 1024 * 1024  # the longest CSV row the scanner can still find the start of
OVERLAP = 96


class BulkError(RuntimeError):
    pass


# ---- HTTP source --------------------------------------------------------------------------------------------------

class HttpSource:
    """Byte ranges of one object over HTTPS. `transport(url, headers, timeout)` returns (status, headers, body) as in
    jobs/_lib/fetch_pool.http_transport. A stream that breaks mid-way resumes from the last byte received."""

    def __init__(self, url, transport, user_agent, max_retries=6, timeout=120, sleep=time.sleep, stats=None,
                 known=None):
        self.url, self.transport, self.ua = url, transport, user_agent
        self.max_retries, self.timeout, self.sleep = max_retries, timeout, sleep
        self.stats = stats if stats is not None else {"requests": 0, "failures": 0}
        self.size = None
        self.etag = self.last_modified = None
        if known:
            self.size, self.etag, self.last_modified = known
        else:
            self._probe()

    def _get(self, a, b):
        self.stats["requests"] += 1
        return self.transport(self.url, {"User-Agent": self.ua, "Range": f"bytes={a}-{b}"}, self.timeout)

    def _probe(self):
        last = None
        for attempt in range(self.max_retries):
            try:
                status, hs, body = self._get(0, 0)
                try:
                    body.read(16)
                finally:
                    body.close()
                m = re.fullmatch(r"bytes 0-0/(\d+)", hs.get("content-range", ""))
                if status == 206 and m:
                    self.size, self.etag, self.last_modified = int(m.group(1)), hs.get("etag"), hs.get("last-modified")
                    return
                last = f"HTTP {status}"
                self.stats["failures"] += 1
                if status in (401, 403, 404):
                    break
            except Exception as e:  # network error
                last = type(e).__name__ + ": " + str(e)[:120]
                self.stats["failures"] += 1
            self.sleep(min(30, 2 ** attempt))
        raise BulkError(f"cannot read {self.url}: {last}")

    def read_range(self, a, b):
        out = b"".join(self.open_stream(a, b))
        return out

    def open_stream(self, a, b, chunk=1024 * 1024):
        pos, tries = a, 0
        if self.size:
            b = min(b, self.size - 1)
        while pos <= b:
            try:
                status, hs, body = self._get(pos, b)
                if status != 206:
                    self.stats["failures"] += 1
                    try:
                        body.close()
                    except Exception:
                        pass
                    raise BulkError(f"HTTP {status}")
                try:
                    while True:
                        data = body.read(chunk)
                        if not data:
                            break
                        pos += len(data)
                        tries = 0
                        yield data
                finally:
                    body.close()
                if pos <= b:
                    raise BulkError("short body")
            except Exception as e:
                self.stats["failures"] += 1
                tries += 1
                if tries > self.max_retries:
                    raise BulkError(f"stream failed at byte {pos} of {self.url}: {type(e).__name__}: {str(e)[:120]}")
                self.sleep(min(60, 2 ** tries))


# ---- streaming row scanner ----------------------------------------------------------------------------------------

class RowScanner:
    """Yield the raw bytes of each CSV row that contains a position chosen by `select(buf, lo, hi)` (which returns
    positions relative to buf). Only rows that START inside the segment's owned output are yielded; a row that
    straddles the end is finished from the extra bytes the decoder reads past it."""

    def __init__(self, select, keep=KEEP_BYTES):
        self.select, self.keep = select, keep
        self.buf = bytearray()
        self.base = 0          # absolute offset of buf[0]
        self.scanned = 0       # absolute offset up to which `select` has run
        self.pending = []      # absolute row-start offsets waiting for their row end
        self.last_row = -1     # last row start already queued
        self.trimmed = False
        self.owned = float("inf")
        self.head_skipped = 0
        self.start_lost = 0
        self.not_owned = 0
        self.unterminated = 0

    def _row_start(self, p):
        """Absolute offset of the '\\n' that starts the row holding relative position p, or None."""
        buf = self.buf
        i = buf.rfind(b'\n"', 0, p + 2)
        while i >= 0:
            if MARK.match(buf, i):
                return self.base + i
            i = buf.rfind(b'\n"', 0, i)
        return None

    def feed(self, chunk, owned=None):
        if owned is not None:
            self.owned = owned
        self.buf.extend(chunk)
        lo = max(0, self.scanned - self.base - OVERLAP)
        for p in self.select(self.buf, lo, len(self.buf)):
            rs = self._row_start(p)
            if rs is None:
                if not self.trimmed and self.base == 0:
                    self.head_skipped += 1
                else:
                    self.start_lost += 1
                continue
            if rs > self.last_row:
                self.last_row = rs
                self.pending.append(rs)
        self.scanned = self.base + len(self.buf)
        yield from self._resolve(final=False)
        first = (self.pending[0] - self.base) if self.pending else len(self.buf)
        cut = max(0, min(first, len(self.buf) - self.keep))
        if cut:
            del self.buf[:cut]
            self.base += cut
            self.trimmed = True

    def _resolve(self, final):
        buf = self.buf
        while self.pending:
            rs = self.pending[0] - self.base
            m = MARK.search(buf, rs + 2)
            terminated_by_eof = False
            if m:
                end = m.start()
            elif final:
                end = len(buf) - (1 if buf.endswith(b"\n") else 0)
                if end - rs < 2:
                    self.pending.pop(0)
                    continue
                terminated_by_eof = True
            else:
                break
            abs_start = self.pending.pop(0)
            if abs_start >= self.owned:
                self.not_owned += 1
                continue
            if terminated_by_eof and not self._ends_row(buf):
                self.unterminated += 1  # an owned row cut off by the end of the data: its tail may be missing
            yield bytes(buf[rs + 1:end])

    @staticmethod
    def _ends_row(buf):
        return buf.endswith(b'"\n') or buf.endswith(b'"')

    def finish(self):
        yield from self._resolve(final=True)


NEEDLES = (b"xecutive", b"XECUTIVE", b"Exec.", b"E.O.", b"E. O.", b"Ex. Ord")


def prefilter_select(buf, lo, hi):
    """Positions where an executive-order citation could start (plain substring searches, several GB/s)."""
    out = []
    for needle in NEEDLES:
        pos = buf.find(needle, lo, hi)
        while pos >= 0:
            out.append(pos)
            pos = buf.find(needle, pos + 1, hi)
    out.sort()
    return out


def id_select(wanted):
    """Positions of row starts whose numeric id is in `wanted` (a set of ints)."""
    def select(buf, lo, hi):
        out = []
        for m in MARK.finditer(buf, lo, hi):
            if int(m.group(1)) in wanted:
                out.append(m.start() + 1)
        return out
    return select


_FIELD = re.compile(r'"((?:[^"\\]+|\\.)*)"|([^,]*)', re.S)
_UNESCAPE = re.compile(r'\\(["\\])')


def split_fields(text: str):
    """Fields of one PostgreSQL COPY ... CSV row as CourtListener writes it: values in double quotes, a quote or a
    backslash inside a value written as backslash-quote or backslash-backslash (ESCAPE '\\'), an empty unquoted
    value for NULL. Returns None for a row that does not tokenize to the end."""
    out, pos, n = [], 0, len(text)
    while True:
        m = _FIELD.match(text, pos)
        if m is None:
            return None
        if m.group(1) is not None:
            out.append(_UNESCAPE.sub(r"\1", m.group(1)))
        else:
            out.append(m.group(2))
        pos = m.end()
        if pos >= n:
            return out
        if text[pos] != ",":
            return None
        pos += 1
        if pos >= n:
            out.append("")
            return out


def parse_row(raw: bytes, header):
    """dict of one CSV row (bytes, no trailing newline), or None when it does not fit the header."""
    fields = split_fields(raw.decode("utf-8", "replace"))
    if fields is None or len(fields) != len(header):
        return None
    return dict(zip(header, fields))


# ---- one segment --------------------------------------------------------------------------------------------------

def decode_header(src, level):
    """Column names: the first line of the file (decoded from the first block)."""
    dec = bz2seg.SegmentDecoder(src, 32, None, level)
    buf = b""
    for c in dec.chunks():
        buf += c
        if b"\n" in buf:
            break
    line = buf.split(b"\n", 1)[0].decode("utf-8")
    return next(csv.reader([line]))


def scan_segment(src, level, start_bit, end_bit, final, select, handle_row, extra_bytes=4 * 1024 * 1024, eos_bit=None):
    """Decode one segment and call handle_row(raw_row_bytes) for each selected owned row. Returns counters."""
    t0 = time.monotonic()
    dec = bz2seg.SegmentDecoder(src, start_bit, end_bit, level, extra_bytes=extra_bytes, final=final, eos_bit=eos_bit)
    sc = RowScanner(select)
    rows = 0
    offset = 0
    for chunk in dec.chunks():
        offset += len(chunk)
        for raw in sc.feed(chunk, owned=dec.owned if dec.owned is not None else None):
            handle_row(raw)
            rows += 1
    for raw in sc.finish():
        handle_row(raw)
        rows += 1
    return {"rows_selected": rows, "decoded_bytes": dec.decoded, "compressed_bytes": dec.compressed_read,
            "head_rows_skipped": sc.head_skipped, "row_start_lost": sc.start_lost, "rows_not_owned": sc.not_owned,
            "rows_unterminated": sc.unterminated, "seconds": round(time.monotonic() - t0, 1)}


# ---- cache of finished segments ----------------------------------------------------------------------------------

def seg_key(url, etag, start_bit, end_bit, tag):
    h = hashlib.sha256(f"{url}|{etag}|{start_bit}|{end_bit}|{tag}".encode()).hexdigest()[:20]
    return h


def seg_path(cache: Path, kind: str, idx: int, key: str):
    return cache / "seg" / f"{kind}-{idx:04d}-{key}.json.gz"


def save_json_gz(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def load_json_gz(path: Path):
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError, EOFError):
        return None


_FIELD_T = re.compile(r'"((?:[^"\\]+|\\.)*)"|([^,\n]*)', re.S)


def parse_table(text: str):
    """Rows (lists of fields) of a whole small COPY-CSV table whose rows may hold newlines inside quotes."""
    rows, row, pos, n = [], [], 0, len(text)
    while pos <= n:
        m = _FIELD_T.match(text, pos)
        if m is None:
            break
        row.append(_UNESCAPE.sub(r"\1", m.group(1)) if m.group(1) is not None else m.group(2))
        pos = m.end()
        if pos >= n:
            rows.append(row)
            break
        if text[pos] == ",":
            pos += 1
            continue
        if text[pos] == "\n":
            rows.append(row)
            row = []
            pos += 1
            continue
        break
    return [r for r in rows if r != [""]]


def list_objects(transport, prefix, user_agent, timeout=60):
    """[(key, last_modified, size)] under a prefix of the public bucket (S3 ListObjects v1, paged)."""
    out, marker = [], ""
    while True:
        url = f"{BUCKET}/?prefix={prefix}&max-keys=1000" + (f"&marker={marker}" if marker else "")
        status, hs, body = transport(url, {"User-Agent": user_agent}, timeout)
        try:
            xml = body.read(50_000_000).decode("utf-8", "replace")
        finally:
            body.close()
        if status != 200:
            raise BulkError(f"listing {prefix}: HTTP {status}")
        for blk in xml.split("<Contents>")[1:]:
            k = re.search(r"<Key>([^<]+)</Key>", blk)
            lm = re.search(r"<LastModified>([^<]+)</LastModified>", blk)
            sz = re.search(r"<Size>(\d+)</Size>", blk)
            if k and sz:
                out.append((k.group(1), lm.group(1) if lm else "", int(sz.group(1))))
        if "<IsTruncated>true</IsTruncated>" in xml and out:
            marker = out[-1][0]
        else:
            return out
