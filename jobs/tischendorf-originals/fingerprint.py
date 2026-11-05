"""Text fingerprints: does a page hold the same order as a held transcription?

An order's fingerprint is the set of its three-word sequences (shingles) weighted by how rare each is across every
transcription the project holds. Boilerplate ("by virtue of the authority vested in me") and web-page furniture
appear in thousands of texts and weigh almost nothing; place names, persons, acreages and operative phrasing appear
in one or two and carry the score. A candidate page's score is the weighted share of the fingerprint it contains, so
OCR damage lowers it gradually and a different order on the same subject scores low.

Standard library only. Nothing here is an identity authentication or a legal finding.
"""
from __future__ import annotations

import math
import re
from collections import Counter

WORD = re.compile(r"[a-z0-9]+")
HYPHEN_BREAK = re.compile(r"(\w)-\s*\n\s*(\w)")
SHINGLE = 3
RARE_DF = 25          # a shingle in more than this many order texts is boilerplate for scoring purposes
MIN_RARE = 8          # fewer rare shingles than this: the text alone cannot tell this order from its neighbours


def tokens(text: str) -> list[str]:
    text = HYPHEN_BREAK.sub(r"\1\2", text or "").lower().replace("’", "'")
    return [t for t in WORD.findall(text) if len(t) > 1 or t.isdigit()]


def shingles(text: str, size: int = SHINGLE) -> set[tuple[str, ...]]:
    t = tokens(text)
    return {tuple(t[i:i + size]) for i in range(len(t) - size + 1)}


def document_frequency(texts_by_order: dict[str, str], keep: set | None = None) -> tuple[Counter, int]:
    """Count, for each shingle, how many orders' texts contain it. With keep, count only those shingles."""
    df = Counter()
    for text in texts_by_order.values():
        s = shingles(text)
        df.update(s & keep if keep is not None else s)
    return df, len(texts_by_order)


class Fingerprint:
    def __init__(self, text: str, df: Counter, n_docs: int):
        own = shingles(text)
        self.weights = {}
        for s in own:
            d = max(1, df.get(s, 1))
            if d <= RARE_DF:
                self.weights[s] = math.log((n_docs + 1) / d)
        self.total = sum(self.weights.values())
        self.rare = len(self.weights)

    @property
    def distinctive(self) -> bool:
        return self.rare >= MIN_RARE

    def score(self, candidate_text: str) -> float:
        """Weighted share of this fingerprint's rare shingles present in the candidate (0-1)."""
        if not self.total:
            return 0.0
        return self.score_set(shingles(candidate_text))

    def score_set(self, cand: set) -> float:
        if not self.total:
            return 0.0
        return sum(w for s, w in self.weights.items() if s in cand) / self.total

    def phrases(self, k: int = 3, length: int = 6, source_text: str = "") -> list[str]:
        """The k rarest non-overlapping word runs of the given length, for full-text search engines."""
        t = tokens(source_text)
        scored = []
        for i in range(len(t) - length + 1):
            run = t[i:i + length]
            if any(w.isdigit() and len(w) > 4 for w in run):
                continue  # long digit strings (page numbers, citations) OCR badly and over-constrain a search
            w = sum(self.weights.get(tuple(run[j:j + SHINGLE]), 0) for j in range(length - SHINGLE + 1))
            if w:
                scored.append((w, i))
        out, used = [], set()
        for w, i in sorted(scored, reverse=True):
            if any(j in used for j in range(i, i + length)):
                continue
            out.append(" ".join(t[i:i + length]))
            used.update(range(i, i + length))
            if len(out) == k:
                break
        return out
