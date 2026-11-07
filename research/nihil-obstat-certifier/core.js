/* Nihil obstat core: hashing, byte spans, decision records. No DOM, no network, no storage.
 * Loaded by index.html (window.NihilCore) and by tests/test_core.html. */
(function (root) {
  "use strict";

  var VERSION = "0.1.0";
  var CARD_SCHEMA = "eo-nihil-obstat-card/v1";
  var DECISION_SCHEMA = "eo-nihil-obstat-decision/v1";

  // ------------------------------------------------------------ SHA-256
  // SubtleCrypto where the browser offers it (file:// is a secure context in current browsers);
  // otherwise this pure-JS FIPS 180-4 implementation, so the page still verifies hashes.
  var K = new Uint32Array([
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]);

  function sha256Fallback(bytes) {
    var H = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
    var n = bytes.length, padded = ((n + 9 + 63) >> 6) << 6;
    var buf = new Uint8Array(padded);
    buf.set(bytes);
    buf[n] = 0x80;
    var view = new DataView(buf.buffer);
    view.setUint32(padded - 8, Math.floor(n / 0x20000000), false);
    view.setUint32(padded - 4, (n << 3) >>> 0, false);
    var W = new Uint32Array(64);
    for (var off = 0; off < padded; off += 64) {
      for (var i = 0; i < 16; i++) W[i] = view.getUint32(off + i * 4, false);
      for (i = 16; i < 64; i++) {
        var a = W[i - 15], b = W[i - 2];
        var s0 = ((a >>> 7) | (a << 25)) ^ ((a >>> 18) | (a << 14)) ^ (a >>> 3);
        var s1 = ((b >>> 17) | (b << 15)) ^ ((b >>> 19) | (b << 13)) ^ (b >>> 10);
        W[i] = (W[i - 16] + s0 + W[i - 7] + s1) >>> 0;
      }
      var h0 = H[0], h1 = H[1], h2 = H[2], h3 = H[3], h4 = H[4], h5 = H[5], h6 = H[6], h7 = H[7];
      for (i = 0; i < 64; i++) {
        var S1 = ((h4 >>> 6) | (h4 << 26)) ^ ((h4 >>> 11) | (h4 << 21)) ^ ((h4 >>> 25) | (h4 << 7));
        var ch = (h4 & h5) ^ (~h4 & h6);
        var t1 = (h7 + S1 + ch + K[i] + W[i]) >>> 0;
        var S0 = ((h0 >>> 2) | (h0 << 30)) ^ ((h0 >>> 13) | (h0 << 19)) ^ ((h0 >>> 22) | (h0 << 10));
        var maj = (h0 & h1) ^ (h0 & h2) ^ (h1 & h2);
        var t2 = (S0 + maj) >>> 0;
        h7 = h6; h6 = h5; h5 = h4; h4 = (h3 + t1) >>> 0; h3 = h2; h2 = h1; h1 = h0; h0 = (t1 + t2) >>> 0;
      }
      H[0] += h0; H[1] += h1; H[2] += h2; H[3] += h3; H[4] += h4; H[5] += h5; H[6] += h6; H[7] += h7;
    }
    var hex = "";
    for (i = 0; i < 8; i++) hex += ("00000000" + H[i].toString(16)).slice(-8);
    return hex;
  }

  function toHex(buffer) {
    var u = new Uint8Array(buffer), s = "";
    for (var i = 0; i < u.length; i++) s += (u[i] < 16 ? "0" : "") + u[i].toString(16);
    return s;
  }

  var hashEngine = "unknown";
  function sha256Hex(bytes) {
    if (!(bytes instanceof Uint8Array)) bytes = new Uint8Array(bytes);
    var subtle = root.crypto && root.crypto.subtle;
    if (subtle && typeof subtle.digest === "function") {
      hashEngine = "SubtleCrypto";
      return subtle.digest("SHA-256", bytes).then(toHex);
    }
    hashEngine = "JavaScript fallback";
    return Promise.resolve(sha256Fallback(bytes));
  }

  // ------------------------------------------------------------ text, bytes
  var enc = new TextEncoder();
  var dec = new TextDecoder("utf-8");

  function b64ToBytes(b64) {
    var bin = atob(b64), out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  /** The exact bytes a card embeds for a source's saved text, or null when it is not embedded. */
  function textBytes(src) {
    if (typeof src.text === "string") return enc.encode(src.text);
    if (typeof src.text_b64 === "string") return b64ToBytes(src.text_b64);
    return null;
  }

  function rawBytes(src) {
    return typeof src.raw_b64 === "string" ? b64ToBytes(src.raw_b64) : null;
  }

  function decodeRange(bytes, a, b) {
    return dec.decode(bytes.subarray(Math.max(0, a), Math.max(0, b)));
  }

  /** Text around a byte span: {before, hit, after}. Cuts fall on UTF-8 character boundaries. */
  function context(bytes, start, end, pad) {
    var a = Math.max(0, start - pad), b = Math.min(bytes.length, end + pad);
    while (a > 0 && a < start && (bytes[a] & 0xc0) === 0x80) a++;
    while (b < bytes.length && b > end && (bytes[b] & 0xc0) === 0x80) b--;
    return { before: decodeRange(bytes, a, start), hit: decodeRange(bytes, start, end),
             after: decodeRange(bytes, end, b), cutStart: a > 0, cutEnd: b < bytes.length };
  }

  /** Split bytes into [{text, spanIds[]}] given [{id, start, end}] ranges (overlaps allowed). */
  function segments(bytes, ranges) {
    var cuts = {0: true};
    cuts[bytes.length] = true;
    ranges.forEach(function (r) { cuts[r.start] = true; cuts[r.end] = true; });
    var points = Object.keys(cuts).map(Number).filter(function (p) { return p <= bytes.length; })
      .sort(function (x, y) { return x - y; });
    var out = [];
    for (var i = 0; i + 1 < points.length; i++) {
      var a = points[i], b = points[i + 1];
      var ids = ranges.filter(function (r) { return r.start <= a && r.end >= b; }).map(function (r) { return r.id; });
      out.push({ start: a, end: b, text: decodeRange(bytes, a, b), ids: ids });
    }
    return out;
  }

  // ------------------------------------------------------------ canonical JSON and claim hash
  /** Python json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":")), as claim_gate.canonical. */
  function canonical(v) {
    if (v === null || typeof v !== "object") return JSON.stringify(v);
    if (Array.isArray(v)) return "[" + v.map(canonical).join(",") + "]";
    return "{" + Object.keys(v).sort().map(function (k) { return JSON.stringify(k) + ":" + canonical(v[k]); }).join(",") + "}";
  }

  function claimSha(claim) { return sha256Hex(enc.encode(canonical(claim))); }

  // ------------------------------------------------------------ source verification
  /**
   * Hash status of one card source.
   *  text:     'absent' | 'verified' (matches the hash the claim recorded for this text) |
   *            'export_only' (claim recorded none; matches the export manifest only) | 'mismatch'
   *  original: 'verified' (bytes whose SHA-256 is the claim's source hash are held in this page) |
   *            'unverified' (original not attached) | 'mismatch' (a file attached to this source differs)
   * attached: {sha256 -> {name, sha256}} of files the user supplied; slot: optional file forced to this source.
   */
  async function verifySource(src, attached, slot) {
    var out = { text: "absent", textSha: null, original: "unverified", originalSha: null, originalName: null, notes: [] };
    var tb = textBytes(src);
    if (tb) {
      out.textSha = await sha256Hex(tb);
      if (src.text_sha256_export && out.textSha !== src.text_sha256_export) {
        out.text = "mismatch"; out.notes.push("embedded text differs from the export manifest hash");
      } else if (src.text_sha256_claimed) {
        out.text = out.textSha === src.text_sha256_claimed ? "verified" : "mismatch";
        if (out.text === "mismatch") out.notes.push("embedded text differs from the text hash the claim recorded");
      } else {
        out.text = "export_only";
      }
      if (src.sha256 && out.textSha === src.sha256) { out.original = "verified"; out.originalSha = out.textSha; out.originalName = "embedded text"; }
    } else if (src.text_sha256_claimed && attached && attached[src.text_sha256_claimed]) {
      out.text = "verified"; out.textSha = src.text_sha256_claimed;
    }
    var rb = rawBytes(src);
    if (rb) {
      out.originalSha = await sha256Hex(rb);
      out.original = out.originalSha === src.sha256 ? "verified" : "mismatch";
      out.originalName = "embedded original";
    }
    if (out.original !== "verified" && attached && src.sha256 && attached[src.sha256]) {
      out.original = "verified"; out.originalSha = src.sha256; out.originalName = attached[src.sha256].name;
    }
    if (slot) {
      out.originalSha = slot.sha256; out.originalName = slot.name;
      out.original = slot.sha256 === src.sha256 ? "verified" : "mismatch";
      if (out.original === "mismatch") out.notes.push("attached file " + slot.name + " has SHA-256 " + slot.sha256 + ", not " + src.sha256);
    }
    return out;
  }

  /** Does the span's byte range hold the claim's quotation? (Only 'exact' spans are expected to.) */
  function spanCheck(span, bytes) {
    if (!bytes || span.byte_start == null) return "no_location";
    if (span.byte_end > bytes.length) return "out_of_range";
    if (span.status === "exact") return decodeRange(bytes, span.byte_start, span.byte_end) === span.quote ? "ok" : "differs";
    return "normalised";
  }

  // ------------------------------------------------------------ decision records
  function utcNow() { return new Date().toISOString().replace(/\.\d{3}Z$/, "Z"); }

  /** Build one decision record (without record_sha256). `d` holds the form state. */
  function buildDecision(card, cardFileSha, d) {
    var rec = {
      schema: DECISION_SCHEMA,
      page_version: VERSION,
      hash_engine: hashEngine,
      instrument_id: card.instrument_id,
      claim_sha256: card.claim_sha256,
      card_file_sha256: cardFileSha || null,
      reviewer: { name: d.reviewerName, independence_declared: !!d.independent },
      decided_utc: d.decidedUtc || utcNow(),
      overall: d.overall,
      elements: card.elements.map(function (e) {
        var x = (d.elements && d.elements[e.id]) || {};
        return { element: e.id, label: e.label, decision: x.decision || null, reason: (x.reason || "").trim() };
      }),
      notes: (d.notes || "").trim(),
      attestation: { read_original_pages: !!d.readOriginal },
      sources: (card.sources || []).map(function (s) {
        var v = (d.sourceStatus && d.sourceStatus[s.source_key]) || {};
        return { source_key: s.source_key, url: s.url || null, sha256: s.sha256 || null,
                 text_layer: v.text || "unknown", original: v.original || "unknown" };
      }),
      ai_reviews_seen: (card.ai_reviews || []).map(function (r) { return r.review_id || (r.file + ":" + r.line); }),
      active_seconds: Math.round(d.activeSeconds || 0)
    };
    if (rec.overall === "certify" && d.independent && d.readOriginal) {
      // A draft in the shape of research/stage19/CLAIM_SCHEMA.md's review object, for the owner's importer
      // to validate. This page imports nothing and changes no count.
      var urls = {};
      (card.sources || []).forEach(function (s) { if (s.url && /^https:\/\//.test(s.url)) urls[s.url] = true; });
      rec.lifecycle_review_draft = {
        schema: "eo-lifecycle-review/v1", instrument_id: card.instrument_id, claim_sha256: card.claim_sha256,
        reviewer: d.reviewerName, reviewer_role: "independent_human", decision: "uphold",
        rationale: rec.elements.map(function (e) { return e.label + ": " + (e.reason || "certified"); }).join(" | ")
          + (rec.notes ? " | " + rec.notes : ""),
        checked_source_urls: Object.keys(urls).sort(), reviewed_on: rec.decided_utc.slice(0, 10)
      };
    }
    return rec;
  }

  async function sealDecision(rec) {
    var copy = JSON.parse(JSON.stringify(rec));
    delete copy.record_sha256;
    rec.record_sha256 = await sha256Hex(enc.encode(canonical(copy)));
    return rec;
  }

  /** Why a decision cannot be recorded yet ([] when it can). */
  function validateDecision(card, d, sourceStatus) {
    var errs = [];
    if (!d.reviewerName || !d.reviewerName.trim()) errs.push("Enter your name at the top of the page.");
    if (!d.overall) errs.push("Choose an overall decision.");
    var mismatched = (card.sources || []).filter(function (s) {
      var v = sourceStatus && sourceStatus[s.source_key];
      return v && (v.text === "mismatch" || v.original === "mismatch");
    });
    card.elements.forEach(function (e) {
      var x = (d.elements && d.elements[e.id]) || {};
      if (!x.decision) errs.push("Decide '" + e.label + "'.");
      else if (x.decision !== "certify" && !(x.reason || "").trim()) errs.push("Give a reason for '" + e.label + "'.");
    });
    if (d.overall === "certify") {
      card.elements.forEach(function (e) {
        var x = (d.elements && d.elements[e.id]) || {};
        if (x.decision && x.decision !== "certify") errs.push("Overall cannot be certify while '" + e.label + "' is " + x.decision + ".");
      });
      if (mismatched.length) errs.push("A source hash does not match; certify is not possible.");
      if (!d.independent) errs.push("Certify requires you to declare independence (you did not produce this claim or take part in its AI review).");
      if (!d.readOriginal) errs.push("Certify requires you to attest that you read the cited pages of the originals.");
    } else if (d.overall && !(d.notes || "").trim() && !card.elements.some(function (e) {
      var x = (d.elements && d.elements[e.id]) || {}; return x.decision === d.overall && (x.reason || "").trim();
    })) {
      errs.push("Explain the overall " + d.overall + " in the notes or in an element reason.");
    }
    return errs;
  }

  function toJsonl(records) { return records.map(function (r) { return JSON.stringify(r); }).join("\n") + (records.length ? "\n" : ""); }

  function parseJsonl(text) {
    return text.split(/\r?\n/).filter(function (l) { return l.trim(); }).map(function (l) { return JSON.parse(l); });
  }

  function isCard(obj) {
    return obj && obj.schema === CARD_SCHEMA && typeof obj.instrument_id === "string" && obj.claim && Array.isArray(obj.sources);
  }

  root.NihilCore = {
    VERSION: VERSION, CARD_SCHEMA: CARD_SCHEMA, DECISION_SCHEMA: DECISION_SCHEMA,
    sha256Hex: sha256Hex, sha256Fallback: sha256Fallback, engine: function () { return hashEngine; },
    textBytes: textBytes, rawBytes: rawBytes, decodeRange: decodeRange, context: context, segments: segments,
    canonical: canonical, claimSha: claimSha, verifySource: verifySource, spanCheck: spanCheck,
    buildDecision: buildDecision, sealDecision: sealDecision, validateDecision: validateDecision,
    toJsonl: toJsonl, parseJsonl: parseJsonl, isCard: isCard, utcNow: utcNow
  };
})(typeof window !== "undefined" ? window : globalThis);
