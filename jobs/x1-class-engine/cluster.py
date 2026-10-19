"""X1 step 4: look-alike clusters of pre-1937 texts, exemplars, diffs, cloned clauses.

Each order's document is the union of its own machine clause spans
(claim-kit TEXT_CLAUSES, one segmentation per held text), read back from the
held text file at those offsets; this keeps neighbouring orders printed on the
same page out of the comparison. Documents are compared on word 3-gram
shingles with MinHash (64 hashes, 16 bands of 4) and confirmed by exact Jaccard.

Cloning: the exemplar's clause inventory is mapped onto each member through a
word alignment. A cloned clause is kept only if
  1. no word that differs inside the clause is an operative or qualifying word
     (LEGAL_WORDS: revoke, except, subject, not, until, valid existing rights...);
  2. the member's own segmentation has the same number of clauses; and
  3. the member's own clause spans reproduce, from its own file, the clause text
     claim-kit recorded (re-read and hashed here).
Any failure drops the whole order out of the clone, to individual review.
A cloned clause is a lead for the agent's inventory, never a decided inventory.
"""
import collections, difflib, hashlib, json, re, zlib

import numpy as np

NUM_HASH, BANDS = 64, 16
ROWS = NUM_HASH // BANDS
JACCARD_MIN = 0.5
MAX_TOKENS = 1500
MONTHS = {"january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec"}
TOKEN = re.compile(r"[A-Za-z0-9]+")
_P = (1 << 61) - 1
_rng = np.random.RandomState(20261019)
_A = _rng.randint(1, 1 << 31, size=NUM_HASH).astype(np.uint64)
_B = _rng.randint(0, 1 << 31, size=NUM_HASH).astype(np.uint64)


def load_documents(repo, ids, files=("TEXT_CLAUSES.jsonl", "TEXT_CLAUSES.part0001.jsonl")):
    """{iid: {"path", "sha", "clauses": [...], "tokens": [(word, start, end)], "spans_ok"}}"""
    docs = {}
    for name in files:
        p = repo / "jobs/claim-kit/output" / name
        if not p.exists():
            continue
        for line in open(p):
            x = json.loads(line)
            iid = x.get("instrument_id")
            if iid not in ids or iid in docs or not x.get("clauses"):
                continue
            src = x.get("source") or {}
            path = src.get("text_path")
            if not path or not (repo / path).exists():
                continue
            raw = (repo / path).read_text(encoding="utf-8", errors="replace")
            clauses, toks, ok = [], [], True
            for c in sorted(x["clauses"], key=lambda c: c["char_start"]):
                s, e = c["char_start"], c["char_end"]
                if raw[s:e] != c.get("text", raw[s:e]):
                    ok = False
                clauses.append({"scope_id": c["scope_id"], "label": c.get("label", ""), "kind": c.get("kind", ""),
                                "char_start": s, "char_end": e, "tok_from": len(toks)})
                for m in TOKEN.finditer(raw, s, e):
                    toks.append((m.group(0), m.start(), m.end()))
                clauses[-1]["tok_to"] = len(toks)
            if not toks:
                continue
            docs[iid] = {"path": path, "text_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                         "source": src, "clauses": clauses, "tokens": toks[:MAX_TOKENS], "spans_ok": ok,
                         "truncated": len(toks) > MAX_TOKENS, "raw": raw}
    return docs


def skeleton(tokens):
    """The template words: names (capitalised), numbers and months removed."""
    return [t[0].lower() for t in tokens
            if not (any(ch.isdigit() for ch in t[0]) or t[0][:1].isupper() or t[0].lower() in MONTHS)]


def shingles(tokens):
    w = skeleton(tokens) or [t[0].lower() for t in tokens]
    return {zlib.crc32(" ".join(w[i:i + 3]).encode()) for i in range(max(1, len(w) - 2))}


def minhash(sh):
    x = np.fromiter(sh, dtype=np.uint64, count=len(sh))
    h = (np.outer(x, _A) + _B) % np.uint64(_P)
    return h.min(axis=0)


def find(parent, i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def cluster(docs, key=lambda i: ""):
    """key: only documents with the same key (the X1 type) are compared."""
    ids = sorted(docs)
    sh = {i: shingles(docs[i]["tokens"]) for i in ids}
    sig = {i: minhash(sh[i]) for i in ids}
    buckets = collections.defaultdict(list)
    for i in ids:
        for b in range(BANDS):
            buckets[(b, sig[i][b * ROWS:(b + 1) * ROWS].tobytes())].append(i)
    pairs = set()
    for members in buckets.values():
        if 1 < len(members) <= 400:
            for a in range(len(members)):
                for b in range(a + 1, len(members)):
                    pairs.add((members[a], members[b]))
    parent = {i: i for i in ids}
    jac = {}
    for a, b in pairs:
        if key(a) != key(b):
            continue
        j = len(sh[a] & sh[b]) / len(sh[a] | sh[b])
        if j >= JACCARD_MIN:
            jac[a, b] = jac[b, a] = j
            ra, rb = find(parent, a), find(parent, b)
            if ra != rb:
                parent[ra] = rb
    comps = collections.defaultdict(list)
    for i in ids:
        comps[find(parent, i)].append(i)
    # Split each connected component into exemplar-centred groups: every member
    # must itself be similar to its exemplar, not only to a neighbour in a chain.
    out = []
    for comp in comps.values():
        left = set(comp)
        while len(left) > 1:
            pool = sorted(left)
            j = lambda a, b: jac.get((a, b)) if (a, b) in jac else _j(sh[a], sh[b])
            score = {a: sum(1 for b in pool if b != a and j(a, b) >= JACCARD_MIN) for a in pool}
            ex = max(pool, key=lambda a: (score[a], a))
            g = [ex] + [b for b in pool if b != ex and j(ex, b) >= JACCARD_MIN]
            if len(g) < 2:
                break
            for b in g:
                if b != ex:
                    jac[ex, b] = jac[b, ex] = j(ex, b)
            out.append(sorted(g))
            left -= set(g)
    return sorted(out, key=lambda g: (-len(g), g[0])), sh, jac


def _j(a, b):
    return len(a & b) / len(a | b)


# Words that change what an order does. A difference touching one of these
# inside a clause drops the order out of the clone, whatever the cluster shares.
LEGAL_WORDS = set("""
not no nor never except excepting exception excluded excluding exclude unless provided proviso subject notwithstanding
revoke revoked revoking revocation rescind rescinded modify modified modifying modification amend amended amending amendment
supersede superseded suspend suspended suspending restore restored restoring restoration withdraw withdrawn withdrawal withdrawing
reserve reserved reserving reservation reserves establish established abolish abolished terminate terminated termination expire expires
expired expiration continue continued continuing extend extended extension until unto temporary temporarily permanent permanently
pending hereafter heretofore thereafter shall may must authorized authorize authorizing directed prohibited forbidden waive waived
valid existing rights right claims prior subsequent only also additional entire entirely all any portion part partially
increase increased decrease decreased diminish diminished enlarge enlarged transfer transferred eliminate eliminated
""".split())


def is_slot(word, template=None):
    """A word that may differ between look-alikes without dropping the clone: any
    word except the operative and qualifying words above. Names, numbers, land
    descriptions and OCR noise are slots; the agent still reads the diff."""
    return word.lower() not in LEGAL_WORDS


def cluster(docs, key=lambda i: ""):
    """key: only documents with the same key (the X1 type) are compared."""
    ids = sorted(docs)
    sh = {i: shingles(docs[i]["tokens"]) for i in ids}
    sig = {i: minhash(sh[i]) for i in ids}
    buckets = collections.defaultdict(list)
    for i in ids:
        for b in range(BANDS):
            buckets[(b, sig[i][b * ROWS:(b + 1) * ROWS].tobytes())].append(i)
    pairs = set()
    for members in buckets.values():
        if 1 < len(members) <= 400:
            for a in range(len(members)):
                for b in range(a + 1, len(members)):
                    pairs.add((members[a], members[b]))
    parent = {i: i for i in ids}
    jac = {}
    for a, b in pairs:
        if key(a) != key(b):
            continue
        j = len(sh[a] & sh[b]) / len(sh[a] | sh[b])
        if j >= JACCARD_MIN:
            jac[a, b] = jac[b, a] = j
            ra, rb = find(parent, a), find(parent, b)
            if ra != rb:
                parent[ra] = rb
    comps = collections.defaultdict(list)
    for i in ids:
        comps[find(parent, i)].append(i)
    # Split each connected component into exemplar-centred groups: every member
    # must itself be similar to its exemplar, not only to a neighbour in a chain.
    out = []
    for comp in comps.values():
        left = set(comp)
        while len(left) > 1:
            pool = sorted(left)
            j = lambda a, b: jac.get((a, b)) if (a, b) in jac else _j(sh[a], sh[b])
            score = {a: sum(1 for b in pool if b != a and j(a, b) >= JACCARD_MIN) for a in pool}
            ex = max(pool, key=lambda a: (score[a], a))
            g = [ex] + [b for b in pool if b != ex and j(ex, b) >= JACCARD_MIN]
            if len(g) < 2:
                break
            for b in g:
                if b != ex:
                    jac[ex, b] = jac[b, ex] = j(ex, b)
            out.append(sorted(g))
            left -= set(g)
    return sorted(out, key=lambda g: (-len(g), g[0])), sh, jac


def _j(a, b):
    return len(a & b) / len(a | b)


VOCAB = set()      # words in at least VOCAB_MIN_DOCS documents; set by build()
VOCAB_MIN_DOCS = 5


def clone(ex, mem, template):
    """Map the exemplar's clauses onto a member. Returns (clauses, diffs, dropout_reason)."""
    a = [t[0].lower() for t in ex["tokens"]]
    b = [t[0].lower() for t in mem["tokens"]]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ops = sm.get_opcodes()
    diffs = [{"op": op, "exemplar": " ".join(ex["tokens"][k][0] for k in range(i1, i2))[:120],
              "member": " ".join(mem["tokens"][k][0] for k in range(j1, j2))[:120]}
             for op, i1, i2, j1, j2 in ops if op != "equal"]
    if ex["truncated"] or mem["truncated"]:
        return [], diffs, "text_longer_than_compared_window"
    if len(ex["clauses"]) != len(mem["clauses"]):
        return [], diffs, f"own_segmentation_has_{len(mem['clauses'])}_clauses_exemplar_{len(ex['clauses'])}"
    if not mem["spans_ok"]:
        return [], diffs, "member_clause_text_does_not_match_its_file"
    out = []
    for c, own in zip(ex["clauses"], mem["clauses"]):
        f, t = c["tok_from"], c["tok_to"]
        for op, i1, i2, j1, j2 in ops:
            if op == "equal":
                continue
            inside = (i1 < t and i2 > f) if op != "insert" else (f <= i1 < t)
            if not inside:
                continue
            words = [ex["tokens"][k][0] for k in range(max(i1, f), min(i2, t))] + [mem["tokens"][k][0] for k in range(j1, j2)]
            bad = [w for w in words if not is_slot(w, template)]
            if bad:
                return [], diffs, f"non_slot_difference_in_{c['scope_id'].split('#')[-1]}:{' '.join(bad[:6])}"
        # The cloned clause is the member's own machine span, re-read from its own file.
        s0, e0 = own["char_start"], own["char_end"]
        span = mem["raw"][s0:e0]
        if not span.strip() or [m.group(0) for m in TOKEN.finditer(span)][:1] != [mem["tokens"][own["tok_from"]][0]]:
            return [], diffs, "span_recheck_failed"
        out.append({"scope_id": own["scope_id"], "exemplar_scope_id": c["scope_id"], "text_path": mem["path"],
                    "char_start": s0, "char_end": e0, "span_sha256": hashlib.sha256(span.encode("utf-8")).hexdigest(),
                    "text_sha256": mem["text_sha256"]})
    return out, diffs, ""


def build(repo, ids, types):
    """Clusters, member rows and cloned clauses. types: {iid: row from classify}."""
    docs = load_documents(repo, ids)
    groups, sh, jac = cluster(docs, key=lambda i: types.get(i, {}).get("type", "unknown"))
    clusters, members, cloned = [], [], []
    for n, g in enumerate(groups, 1):
        cid = f"X1C{n:04d}"
        score = {i: sum(_j(sh[i], sh[j]) for j in g if j != i) for i in g}
        ex_id = max(g, key=lambda i: (score[i], -len(docs[i]["tokens"]), i))
        template = None
        tcount = collections.Counter(types.get(i, {}).get("type", "unknown") for i in g)
        clusters.append({"cluster_id": cid, "size": len(g), "exemplar": ex_id, "members": g,
                         "types": dict(tcount.most_common()), "exemplar_clauses": len(docs[ex_id]["clauses"]),
                         "min_jaccard_to_exemplar": round(min([1.0] + [_j(sh[ex_id], sh[i]) for i in g if i != ex_id]), 3)})
        for i in g:
            if i == ex_id:
                members.append({"instrument_id": i, "cluster_id": cid, "role": "exemplar", "jaccard_to_exemplar": 1.0,
                                "type": types.get(i, {}).get("type", ""), "clone_status": "exemplar", "dropout_reason": "",
                                "differences": 0, "diff_preview": ""})
                continue
            cl, diffs, why = clone(docs[ex_id], docs[i], template)
            j = len(sh[i] & sh[ex_id]) / len(sh[i] | sh[ex_id])
            members.append({"instrument_id": i, "cluster_id": cid, "role": "member", "jaccard_to_exemplar": round(j, 3),
                            "type": types.get(i, {}).get("type", ""), "clone_status": "dropped_out" if why else "cloned",
                            "dropout_reason": why, "differences": len(diffs),
                            "diff_preview": " | ".join(f"{d['exemplar']} -> {d['member']}" for d in diffs[:6])[:500]})
            for c in cl:
                cloned.append(dict(c, instrument_id=i, cluster_id=cid, exemplar=ex_id))
    return clusters, members, cloned, {"documents": len(docs), "clusters": len(groups),
                                       "orders_in_clusters": sum(len(g) for g in groups),
                                       "clusters_5_plus": sum(1 for g in groups if len(g) >= 5)}


def modern_families(repo, min_size=5):
    """Claim-kit actor/parent families of 5+ (modern look-alikes), as X1 clusters without diffs."""
    out = []
    for f in json.load(open(repo / "jobs/claim-kit/output/FAMILIES.json")):
        if f["family_id"].split(":")[0] in ("actor", "parent") and len(f["instrument_ids"]) >= min_size:
            out.append({"cluster_id": "FAM:" + f["family_id"], "size": len(f["instrument_ids"]),
                        "members": sorted(f["instrument_ids"])})
    return sorted(out, key=lambda c: -c["size"])
