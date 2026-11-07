"""Block-aligned bzip2 segments: decode any byte range of a huge .bz2 without reading what precedes it.

CourtListener's bulk opinion file is one bzip2 stream of about 55 GB (several hundred GB of CSV). A bzip2 stream is a
run of independent blocks (900 kB of input each at level 9), each starting with the 48-bit magic 0x314159265359 at
ANY bit offset, so a reader can seek to a byte, find the next block start, and decode from there. This module finds
block starts, cuts a file into segments at them, and decodes one segment as a stream, so several worker processes
can each take a slice, and a stopped run resumes at a segment.

A segment decodes blocks from its start bit to the next segment's start bit (the segment "owns" that output) and then
`extra_bytes` more of compressed data, so a CSV row that begins inside the segment and ends inside the next one can
be finished. `SegmentDecoder.owned` becomes the number of decoded bytes the segment owns once it is known.

Standard library only. The byte source is injected (an object with `size`, `read_range(a, b)` and
`open_stream(a, b)`), so tests run on an in-memory bz2 file.
"""
from __future__ import annotations

import bz2

MAGIC = bytes.fromhex("314159265359")
EOS_MAGIC = bytes.fromhex("177245385090")  # end of stream; followed by a 32-bit CRC of the whole stream
WINDOW = 2 * 1024 * 1024  # block starts are searched in this many bytes; one 900 kB block compresses to well under it


class SegmentError(RuntimeError):
    pass


def find_block_start(window: bytes, min_bit: int = 0, magic: bytes = MAGIC, tail_room: int = 10):
    """Bit offset (from the window's first bit) of the first block magic at or after min_bit, else None. The match
    must leave room for a block header after it (48 magic bits + 32 CRC bits)."""
    n = len(window)
    if n < 16:
        return None
    v = int.from_bytes(window, "big")
    mask = (1 << (8 * n)) - 1
    best = None
    for s in range(8):
        shifted = ((v << s) & mask).to_bytes(n, "big")
        start = max(0, (min_bit - s + 7) // 8)
        p = shifted.find(magic, start)
        while p >= 0:
            bit = p * 8 + s
            if bit >= min_bit and p + tail_room <= n:
                if best is None or bit < best:
                    best = bit
                break
            p = shifted.find(magic, p + 1)
    return best


def shift_bits(raw_chunks, s: int):
    """The byte stream with its first s bits (0-7) dropped. Yields chunks; the final partial byte is zero padded."""
    if s == 0:
        yield from raw_chunks
        return
    pending = b""
    for raw in raw_chunks:
        pending += raw
        if len(pending) < 2:
            continue
        n = len(pending) - 1
        v = int.from_bytes(pending, "big")
        out = ((v << s) & ((1 << (8 * (n + 1))) - 1)).to_bytes(n + 1, "big")[:n]
        pending = pending[-1:]
        yield out
    if pending:
        yield bytes([(pending[0] << s) & 0xFF])


def _feed(d, part: bytes, drain: bool = False) -> bytes:
    """Decompress `part`. CPython's decompress() stops when the input is used up even if libbz2 still holds decoded
    output (it hands back at most one output buffer, 32 kB, per call then); `drain` keeps calling with no input
    until nothing more comes, so the decoded length at a block boundary is exact."""
    out = d.decompress(part)
    if not drain or d.eof:
        return out
    pieces = [out]
    while True:
        more = d.decompress(b"")
        if not more:
            break
        pieces.append(more)
    return b"".join(pieces)


class SegmentDecoder:
    """Decode blocks from start_bit up to end_bit (owned) plus extra_bytes of compressed data beyond it.

    end_bit None means "to the end of the file" (the last segment). `chunks()` yields decoded byte strings; when the
    chunk that ends exactly at end_bit has been yielded, `owned` equals the total number of decoded bytes yielded so
    far. A source that fails mid-stream is the caller's concern (the source's open_stream may resume itself)."""

    def __init__(self, src, start_bit: int, end_bit, level: int, extra_bytes: int = 4 * 1024 * 1024,
                 read_chunk: int = 1024 * 1024, final: bool = False, eos_bit=None):
        self.src, self.start_bit, self.end_bit, self.level = src, start_bit, end_bit, level
        self.extra_bytes, self.read_chunk, self.final = extra_bytes, read_chunk, final
        self.eos_bit = eos_bit  # never read into the stream trailer: its whole-stream CRC cannot verify a slice
        self.owned = float("inf") if end_bit is None else None
        self.compressed_read = 0
        self.decoded = 0
        self.truncated = False
        self.tail_error = None

    TAIL = 64  # the last bytes of the fed data go in one at a time: a cut stream ends in bits that are not a valid header

    def chunks(self):
        byte0, s = divmod(self.start_bit, 8)
        if self.end_bit is None:
            hi = self.src.size - 1
            need = None
        else:
            hi = min(self.src.size - 1, self.end_bit // 8 + (1 if self.final else self.extra_bytes))
            if self.eos_bit is not None:
                hi = min(hi, self.eos_bit // 8)
            need = (self.end_bit - self.start_bit + 7) // 8
        d = bz2.BZ2Decompressor()
        d.decompress(b"BZh" + str(self.level).encode())
        state = {"fed": 0}
        raw = self.src.open_stream(byte0, hi)

        def counted():
            for c in raw:
                self.compressed_read += len(c)
                yield c

        def feed(part, tolerant):
            """([decoded chunks], stop) after feeding part, splitting at the owned boundary."""
            outs = []
            while part:
                if d.eof:
                    return outs, True
                at_boundary = need is not None and self.owned is None and state["fed"] + len(part) >= need
                piece = part[:need - state["fed"]] if at_boundary else part
                part = part[len(piece):]
                try:
                    out = _feed(d, piece, drain=at_boundary)
                except (OSError, EOFError) as e:
                    if tolerant:
                        self.tail_error = str(e)
                        return outs, True
                    raise SegmentError(f"bzip2 data error near compressed byte {byte0 + self.compressed_read}: {e}")
                state["fed"] += len(piece)
                self.decoded += len(out)
                if out:
                    outs.append(out)
                if at_boundary:
                    self.owned = self.decoded
                    if self.final:
                        return outs, True
            return outs, False

        held = b""
        stopped = False
        for chunk in shift_bits(counted(), s):
            buf = held + chunk
            held, ready = buf[-self.TAIL:], buf[:-self.TAIL]
            if not ready:
                continue
            outs, stopped = feed(ready, False)
            yield from outs
            if stopped:
                break
        if not stopped and held:
            for i in range(len(held)):
                outs, stopped = feed(held[i:i + 1], True)
                yield from outs
                if stopped:
                    break
        if not d.eof and not stopped or (not d.eof and stopped and self.final):
            try:
                tail = _feed(d, b"", drain=True)
            except (OSError, EOFError):
                tail = b""
            self.decoded += len(tail)
            if tail:
                yield tail
        if need is not None and self.owned is None:
            self.owned = self.decoded  # the file ended before the boundary: everything decoded is owned
        self.truncated = not d.eof and self.end_bit is None


def block_boundaries(src, seg_bytes: int, level: int = 9, window: int = WINDOW):
    """Bit offsets of segment starts: [first block, ...], one per seg_bytes of compressed data, each at a verified
    block start; strictly increasing. The first is bit 32 (right after the 4-byte stream header)."""
    starts = [32]
    pos = seg_bytes
    while pos < src.size:
        lo = pos
        found = None
        while lo < src.size and found is None:
            hi = min(src.size - 1, lo + window - 1)
            win = src.read_range(lo, hi)
            rel = find_block_start(win)
            if rel is not None and lo * 8 + rel > starts[-1] and _probe(src, lo * 8 + rel, level):
                found = lo * 8 + rel
            elif rel is not None:
                lo += rel // 8 + 6  # a false match: look further on
            else:
                lo += window - 16
        if found is None:
            break
        if found > starts[-1]:
            starts.append(found)
        pos = max(pos + seg_bytes, found // 8 + 1)
    return starts


def block_at(src, pos: int, level: int = 9, window: int = WINDOW):
    """Bit offset of the first verified block start at or after byte `pos`, else None."""
    lo = pos
    while lo < src.size:
        hi = min(src.size - 1, lo + window - 1)
        win = src.read_range(lo, hi)
        rel = find_block_start(win)
        if rel is not None and _probe(src, lo * 8 + rel, level):
            return lo * 8 + rel
        lo += (rel // 8 + 6) if rel is not None else window - 16
    return None


def _probe(src, bit: int, level: int, size: int = 64 * 1024) -> bool:
    """True when a short decode from this bit start yields data (or simply needs more input) without raising. Near the
    end of the file the decode may run into the stream trailer and fail its whole-stream CRC after producing data:
    that still proves a real block start."""
    byte0, s = divmod(bit, 8)
    data = src.read_range(byte0, min(src.size - 1, byte0 + size))
    raw = b"".join(shift_bits([data], s))
    d = bz2.BZ2Decompressor()
    got = 0
    try:
        d.decompress(b"BZh" + str(level).encode())
        for i in range(0, len(raw), 4096):
            got += len(d.decompress(raw[i:i + 4096]))
            if d.eof:
                break
    except (OSError, EOFError):
        return got > 0
    return True


def end_of_stream_bit(src):
    """Bit offset of the end-of-stream marker (the last 80 bits of the file hold marker + whole-stream CRC), so the
    last segment can stop before the CRC that only a whole-stream decode can satisfy."""
    n = min(src.size, 16)
    tail = src.read_range(src.size - n, src.size - 1)
    rel = find_block_start(tail, 0, EOS_MAGIC, tail_room=4)
    return None if rel is None else (src.size - n) * 8 + rel


def stream_level(src) -> int:
    head = src.read_range(0, 3)
    if len(head) < 4 or head[:3] != b"BZh" or not (49 <= head[3] <= 57):
        raise SegmentError("not a bzip2 stream")
    return head[3] - 48
