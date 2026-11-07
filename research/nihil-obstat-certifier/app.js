/* Nihil obstat page logic. Reads cards the user selects; never writes to the repository or the network.
 * All data goes in through textContent, never innerHTML. */
(function () {
  "use strict";
  var C = window.NihilCore;
  var $ = function (id) { return document.getElementById(id); };

  var state = {
    cards: [],          // {card, fileName, fileSha, claimOk, status: {source_key: verification}}
    attached: {},       // sha256 -> {name, sha256, file}   (every non-card file the user supplied)
    slots: {},          // claim_sha256 + "|" + source_key -> {name, sha256, file}
    drafts: {},         // claim_sha256 -> form state
    decisions: [],      // recorded decision records (append-only in this session)
    selected: -1,
    bytes: {},          // claim_sha256 + "|" + source_key -> Uint8Array | null
    lastActive: Date.now()
  };

  // ------------------------------------------------------------ small helpers
  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === "class") el.className = attrs[k];
      else if (k.slice(0, 2) === "on") el.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] !== false && attrs[k] != null) el.setAttribute(k, attrs[k] === true ? "" : attrs[k]);
    });
    for (var i = 2; i < arguments.length; i++) add(el, arguments[i]);
    return el;
  }
  function add(el, c) {
    if (c == null || c === false) return;
    if (Array.isArray(c)) c.forEach(function (x) { add(el, x); });
    else el.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(String(c)) : c);
  }
  function chip(kind, text, title) { return h("span", { class: "chip " + kind, title: title || null }, text); }
  function short(url, n) { url = url || ""; return url.length > (n || 70) ? url.slice(0, n || 70) + "…" : url; }
  function storeGet(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
  function storeSet(k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* private window: fine */ } }
  function setStatus(msg) { $("loadStatus").textContent = msg; }

  function bytesFor(entry, src) {
    var key = entry.card.claim_sha256 + "|" + src.source_key;
    if (key in state.bytes) return Promise.resolve(state.bytes[key]);
    var b = C.textBytes(src);
    if (b) { state.bytes[key] = b; return Promise.resolve(b); }
    var f = src.text_sha256_claimed && state.attached[src.text_sha256_claimed];
    if (f) {
      return f.file.arrayBuffer().then(function (buf) { state.bytes[key] = new Uint8Array(buf); return state.bytes[key]; });
    }
    state.bytes[key] = null;
    return Promise.resolve(null);
  }

  // ------------------------------------------------------------ loading
  async function hashFile(file) {
    var buf = await file.arrayBuffer();
    return C.sha256Hex(new Uint8Array(buf));
  }

  async function loadFiles(fileList) {
    var files = Array.prototype.slice.call(fileList);
    var cards = 0, others = 0, skipped = 0;
    for (var i = 0; i < files.length; i++) {
      var f = files[i];
      setStatus("Reading " + (i + 1) + " of " + files.length + ": " + f.name);
      var isJson = /\.json$/i.test(f.name) && f.size < 40e6;
      if (isJson) {
        var parsed = null, raw = null;
        try { raw = await f.arrayBuffer(); parsed = JSON.parse(new TextDecoder("utf-8").decode(raw)); } catch (e) { parsed = null; }
        if (C.isCard(parsed)) {
          var entry = { card: parsed, fileName: f.name, fileSha: await C.sha256Hex(new Uint8Array(raw)), claimOk: null, status: {} };
          var at = state.cards.findIndex(function (x) { return x.card.claim_sha256 === parsed.claim_sha256; });
          if (at >= 0) state.cards[at] = entry; else state.cards.push(entry);
          cards++; continue;
        }
        if (parsed !== null) { skipped++; continue; }   // manifest.json and other JSON that is not a card
      }
      if (f.size > 400e6) { skipped++; continue; }
      var sha = await hashFile(f);
      state.attached[sha] = { name: f.webkitRelativePath || f.name, sha256: sha, file: f };
      others++;
    }
    state.cards.sort(function (a, b) { return a.card.instrument_id.localeCompare(b.card.instrument_id, undefined, { numeric: true }); });
    for (var j = 0; j < state.cards.length; j++) await verifyCard(state.cards[j]);
    setStatus(cards + " card(s) loaded; " + others + " other file(s) hashed" + (skipped ? "; " + skipped + " ignored" : "") +
      ". Hashing by " + C.engine() + ".");
    $("engine").textContent = C.engine();
    renderList();
    if (state.selected < 0 && state.cards.length) select(0); else if (state.selected >= 0) renderCard();
  }

  async function verifyCard(entry) {
    var card = entry.card;
    entry.claimOk = (await C.claimSha(card.claim)) === card.claim_sha256;
    for (var i = 0; i < card.sources.length; i++) {
      var s = card.sources[i];
      entry.status[s.source_key] = await C.verifySource(s, attachedMap(), state.slots[card.claim_sha256 + "|" + s.source_key]);
    }
  }
  function attachedMap() {
    var m = {};
    Object.keys(state.attached).forEach(function (k) { m[k] = state.attached[k]; });
    return m;
  }

  // ------------------------------------------------------------ list
  function cardState(entry) {
    var bad = !entry.claimOk || Object.keys(entry.status).some(function (k) {
      var v = entry.status[k]; return v.text === "mismatch" || v.original === "mismatch";
    });
    return bad ? "bad" : "ok";
  }

  function renderList() {
    var ul = $("cards");
    ul.textContent = "";
    state.cards.forEach(function (e, i) {
      var rec = lastDecision(e.card.claim_sha256);
      var b = h("button", { class: i === state.selected ? "sel" : "", onclick: function () { select(i); } },
        h("strong", null, e.card.instrument_id), " ",
        chip(e.card.claim.whole_order_status === "yes" ? "neutral" : "neutral", "claim: " + e.card.claim.whole_order_status),
        cardState(e) === "bad" ? chip("bad", "HASH FAIL") : null,
        rec ? chip(rec.overall === "certify" ? "ok" : rec.overall === "reject" ? "bad" : "warn", rec.overall) : null);
      ul.appendChild(h("li", null, b));
    });
    var n = state.decisions.length;
    $("exportBtn").disabled = !n;
    $("exportInfo").textContent = n ? n + " decision record(s) in this session." : "No decisions recorded yet.";
  }

  function lastDecision(sha) {
    for (var i = state.decisions.length - 1; i >= 0; i--) if (state.decisions[i].claim_sha256 === sha) return state.decisions[i];
    return null;
  }

  function select(i) { state.selected = i; renderList(); renderCard(); }

  // ------------------------------------------------------------ card
  function draftFor(card) {
    var sha = card.claim_sha256;
    if (!state.drafts[sha]) {
      var saved = storeGet("nihil-draft-" + sha), d = null;
      try { d = saved ? JSON.parse(saved) : null; } catch (e) { d = null; }
      state.drafts[sha] = d || { elements: {}, overall: null, notes: "", readOriginal: false, activeSeconds: 0 };
    }
    return state.drafts[sha];
  }
  function saveDraft(card) { storeSet("nihil-draft-" + card.claim_sha256, JSON.stringify(state.drafts[card.claim_sha256])); }

  function statusChips(v) {
    if (!v) return [];
    var out = [];
    out.push(v.text === "verified" ? chip("ok", "text layer hash verified", "SHA-256 of the saved text equals the text hash the claim recorded")
      : v.text === "export_only" ? chip("warn", "text hash: export only", "the claim recorded no hash for this text; it matches the export manifest only")
      : v.text === "absent" ? chip("warn", "text not embedded")
      : chip("bad", "TEXT HASH DIFFERS"));
    out.push(v.original === "verified" ? chip("ok", "original verified: " + (v.originalName || ""), "bytes with the claim's source SHA-256 are held in this page")
      : v.original === "mismatch" ? chip("bad", "ORIGINAL HASH DIFFERS")
      : chip("warn", "original not attached", "attach the original file to verify the claim's source hash"));
    return out;
  }

  function findSource(card, ref) {
    var sha = ref.sha256 || ref.local_file_sha256, tp = ref.text_path || "";
    return card.sources.find(function (s) { return s.sha256 === sha && (s.text_path || "") === (tp || ""); }) ||
           card.sources.find(function (s) { return s.sha256 === sha; });
  }

  var HIDDEN = { evidence_id: 1, evidence_id_encoding: 1, claim_kit: 1, location_confidence: 1, location_verified: 1, text_sha256: 1,
                 char_start: 1, char_end: 1, filing_date: 1, signing_date: 0 };

  function isRef(o) { return o && typeof o === "object" && !Array.isArray(o) && (o.url || o.archival_id) && (o.sha256 || o.local_file_sha256); }

  function renderValue(v, entry) {
    if (v == null) return "—";
    if (typeof v === "string") {
      if (v.length > 500) return h("details", null, h("summary", null, v.slice(0, 140) + "…"), h("div", { class: "ctx" }, v));
      return v;
    }
    if (typeof v !== "object") return String(v);
    if (Array.isArray(v)) return v.length ? h("ul", null, v.map(function (x) { return h("li", null, renderValue(x, entry)); })) : "(none)";
    if (isRef(v)) {
      var s = findSource(entry.card, v), st = s && entry.status[s.source_key];
      return h("span", null, h("span", { class: "mono" }, short(v.url || v.archival_id, 80)), " · ", v.page_or_item || "", " ", statusChips(st));
    }
    var dl = h("dl", { class: "kv" });
    Object.keys(v).forEach(function (k) {
      if (HIDDEN[k] || k === "quote") return;
      if (/(^|_)(quote|excerpt)s?$/.test(k)) return;      // quotations appear as located spans below
      dl.appendChild(h("dt", null, k));
      dl.appendChild(h("dd", null, renderValue(v[k], entry)));
    });
    return dl;
  }

  function claimFor(card, id) {
    var c = card.claim;
    if (id === "original") return c.original_representation;
    var m = /^clause:(\d+)$/.exec(id);
    if (m) { var cl = Object.assign({}, c.operative_clauses[+m[1]]); return cl; }
    if (id === "ending") return { whole_order_status: c.whole_order_status, whole_order_end: c.whole_order_end, formal_disposition: c.formal_disposition };
    if (id === "savings") return c.savings_residuals;
    if (id === "search") return { later_source_search: c.later_source_search, counterevidence_checked: c.counterevidence_checked, source_notes: c.source_notes };
    return null;
  }

  function spanBlock(entry, span) {
    var card = entry.card;
    var src = card.sources.find(function (s) { return s.source_key === span.source_key; });
    var st = src && entry.status[src.source_key];
    var wrap = h("div", { class: "span" });
    var head = h("div", null, h("span", { class: "mono" }, span.claim_path), " ",
      span.status === "exact" ? chip("ok", "exact match") : span.status === "normalised" ? chip("warn", "match after whitespace/hyphen normalisation")
      : chip("bad", span.status === "no_text" ? "no saved text to check" : span.status === "no_source" ? "no source cited" : "NOT FOUND in saved text"),
      span.occurrences > 1 ? chip("warn", span.occurrences + " occurrences") : null,
      span.in_declared_span === false ? chip("warn", "outside the claim's declared span") : null, " ",
      src ? chip("neutral", short(src.url || src.archival_id, 60), src.page_or_item || "") : null,
      src ? statusChips(st) : null);
    wrap.appendChild(head);
    wrap.appendChild(h("div", { class: "q" }, "Claim quotes: “" + (span.quote.length > 700 ? span.quote.slice(0, 700) + "…" : span.quote) + "”"));
    var ctx = h("div", { class: "ctx" }, "Loading source text…");
    wrap.appendChild(ctx);
    if (src) {
      bytesFor(entry, src).then(function (bytes) {
        ctx.textContent = "";
        if (!bytes) { ctx.textContent = "The saved text is not embedded in this card; attach it (matched by SHA-256) to see it here."; return; }
        var check = C.spanCheck(span, bytes);
        if (span.byte_start != null && check !== "out_of_range") {
          var c = C.context(bytes, span.byte_start, span.byte_end, 260);
          ctx.appendChild(document.createTextNode((c.cutStart ? "… " : "") + c.before));
          ctx.appendChild(h("mark", null, c.hit));
          ctx.appendChild(document.createTextNode(c.after + (c.cutEnd ? " …" : "")));
          if (check === "differs") wrap.insertBefore(h("div", { class: "fail" }, "The bytes at this span do not equal the quotation: the card or the text was altered."), ctx);
        } else if (span.declared) {
          var d = C.context(bytes, span.declared.byte_start, span.declared.byte_end, 100);
          ctx.appendChild(document.createTextNode(d.before));
          ctx.appendChild(h("mark", { class: "decl" }, d.hit));
          ctx.appendChild(document.createTextNode(d.after));
          wrap.insertBefore(h("div", { class: "fail" }, "Quotation not found in the saved text; the blue region is where the claim says it is."), ctx);
        } else ctx.textContent = "Quotation not located.";
      });
      wrap.appendChild(h("button", { onclick: function () { openViewer(entry, src, span.span_id); } }, "Open whole source text"));
    }
    return wrap;
  }

  function openViewer(entry, src, focusId) {
    bytesFor(entry, src).then(function (bytes) {
      if (!bytes) { alert("The saved text for this source is not embedded or attached."); return; }
      var ranges = entry.card.spans.filter(function (s) { return s.source_key === src.source_key && s.byte_start != null; })
        .map(function (s) { return { id: s.span_id, start: s.byte_start, end: s.byte_end }; });
      var body = $("vbody");
      body.textContent = "";
      C.segments(bytes, ranges).forEach(function (seg) {
        if (!seg.ids.length) { body.appendChild(document.createTextNode(seg.text)); return; }
        var m = h("mark", { "data-ids": seg.ids.join(" ") }, seg.text);
        if (seg.ids.indexOf(focusId) >= 0) m.id = "focus-mark";
        body.appendChild(m);
      });
      $("vtitle").textContent = (src.url || src.archival_id || "source") + "  ·  " + bytes.length + " bytes";
      var d = $("viewer");
      if (d.showModal) d.showModal(); else d.setAttribute("open", "");
      var f = document.getElementById("focus-mark");
      if (f) f.scrollIntoView({ block: "center" });
    });
  }

  function renderSources(entry) {
    var card = entry.card, wrap = h("div", null);
    card.sources.forEach(function (s) {
      var st = entry.status[s.source_key];
      var input = h("input", { type: "file", onchange: async function (ev) {
        var f = ev.target.files[0]; if (!f) return;
        var sha = await hashFile(f);
        state.slots[card.claim_sha256 + "|" + s.source_key] = { name: f.name, sha256: sha, file: f };
        state.attached[sha] = { name: f.name, sha256: sha, file: f };
        await verifyCard(entry); renderList(); renderCard();
      } });
      var open = null;
      var f = st && st.original === "verified" && Object.keys(state.attached).map(function (k) { return state.attached[k]; })
        .find(function (a) { return a.sha256 === s.sha256; });
      if (f) open = h("button", { onclick: function () { window.open(URL.createObjectURL(f.file), "_blank"); } }, "Open original");
      wrap.appendChild(h("div", { class: "review" },
        h("div", null, h("strong", { class: "mono" }, short(s.url || s.archival_id, 100)), " ", statusChips(st)),
        h("div", { class: "small" }, s.page_or_item || ""),
        h("div", null, s.grade ? chip("neutral", "grade: " + s.grade) : null,
          s.acceptable_as_original === true ? chip("ok", "marked original") : s.acceptable_as_original === false ? chip("warn", "not an original") : null,
          s.requires_page_check ? chip("warn", "page check required") : null),
        h("dl", { class: "kv" },
          h("dt", null, "Source file SHA-256 (claimed)"), h("dd", { class: "mono hash" }, s.sha256 || "none",
            s.raw_in_repo ? " (a committed copy exists in the repository: " + s.raw_bytes + " bytes, too big to embed)" : ""),
          h("dt", null, "Saved text"), h("dd", null, s.text_embedded ? (s.text_bytes + " bytes, SHA-256 recomputed here: ") : (s.text_note || "none"),
            h("span", { class: "mono hash" }, st && st.textSha ? st.textSha : ""))),
        st && st.notes.length ? h("div", { class: "fail" }, st.notes.join("; ")) : null,
        h("div", { class: "row" }, h("label", null, "Attach the original file to verify its hash: ", input), open)));
    });
    return wrap;
  }

  function renderChecker(entry) {
    var ch = entry.card.checker, sum = ch.summary || {};
    var out = h("div", null);
    out.appendChild(h("p", null, "Mechanical result: ", chip(sum.mechanical_result === "pass" ? "ok" : "warn", sum.mechanical_result || "?"),
      "gate passed: ", chip(sum.gate_passed ? "ok" : "bad", String(sum.gate_passed)), " all checks passed: ", chip(sum.all_checks_passed ? "ok" : "warn", String(sum.all_checks_passed))));
    var steps = sum.steps || sum.steps_checker_passed;
    if (steps) {
      var t = h("table", null, h("tr", null, h("th", null, "Step"), h("th", null, "Checker passed")));
      Object.keys(steps).forEach(function (k) {
        var v = steps[k]; var ok = typeof v === "object" ? v.checker_passed : v;
        t.appendChild(h("tr", null, h("td", null, k), h("td", null, chip(ok ? "ok" : "warn", String(ok)))));
      });
      out.appendChild(t);
    }
    if (sum.check_counts) {
      var t2 = h("table", null, h("tr", null, h("th", null, "Check"), h("th", null, "Counts")));
      Object.keys(sum.check_counts).forEach(function (k) { t2.appendChild(h("tr", null, h("td", null, k), h("td", null, JSON.stringify(sum.check_counts[k])))); });
      out.appendChild(h("h3", null, "Check counts")); out.appendChild(t2);
    }
    out.appendChild(h("h3", null, "Rows that did not pass (" + ch.non_passing_rows.length + ")"));
    if (ch.non_passing_rows.length) {
      var t3 = h("table", null, h("tr", null, ["step", "check", "field", "result", "status", "detail"].map(function (x) { return h("th", null, x); })));
      ch.non_passing_rows.forEach(function (r) { t3.appendChild(h("tr", null, ["step", "check", "field", "result", "status", "detail"].map(function (x) { return h("td", null, r[x] || ""); }))); });
      out.appendChild(t3);
    } else out.appendChild(h("p", { class: "small" }, "None."));
    var g = entry.card.checker_generation;
    out.appendChild(h("p", { class: "small" }, ch.note + (g ? " Checker run " + (g.finished_utc || "") + " " + (g.run_url || "") : "")));
    return out;
  }

  function renderReviews(entry) {
    var card = entry.card, gate = card.ai_review_gate || {};
    var out = h("div", null, h("p", null, "AI review gate (information only): ",
      chip(gate.met ? "ok" : "warn", gate.distinct_upholding_reviewers + " distinct upholding reviewer(s); rule: " + (gate.rule || "")),
      gate.rejecting_reviewers && gate.rejecting_reviewers.length ? chip("bad", "rejected by " + gate.rejecting_reviewers.join(", ")) : null));
    if (!card.ai_reviews.length) out.appendChild(h("p", { class: "fail" }, "No AI review record names this exact claim hash."));
    card.ai_reviews.forEach(function (r) {
      var v = String(r.verdict || r.decision || "");
      var box = h("div", { class: "review" },
        h("div", null, chip(/^uphe?ld|uphold/.test(v) ? "ok" : "bad", v), chip("neutral", r.phase), chip("neutral", r.model_family || "family ?"),
          h("span", { class: "mono" }, r.reviewer || r.review_id || ""), " ", h("span", { class: "small" }, (r.file || "") + ":" + r.line)));
      if (r.defects && r.defects.length) box.appendChild(h("details", { open: true }, h("summary", null, r.defects.length + " defect(s) recorded"),
        h("pre", null, JSON.stringify(r.defects, null, 1))));
      box.appendChild(h("details", null, h("summary", null, "Reasoning and evidence checked"),
        h("pre", null, r.reasoning || r.rationale || "(none)"),
        r.evidence_checked ? h("ul", null, r.evidence_checked.map(function (x) { return h("li", null, x); })) : null));
      out.appendChild(box);
    });
    return out;
  }

  function elementStatusSources(entry, id) {
    var card = entry.card, keys = {};
    card.spans.filter(function (s) { return s.element === id && s.source_key; }).forEach(function (s) { keys[s.source_key] = 1; });
    return Object.keys(keys);
  }

  function renderElement(entry, e, draft, refresh) {
    var card = entry.card;
    var sec = h("section", { class: "sec", id: "el-" + e.id }, h("h2", null, e.label));
    var claimPart = claimFor(card, e.id);
    if (claimPart) sec.appendChild(renderValue(claimPart, entry));
    var spans = card.spans.filter(function (s) { return s.element === e.id; });
    sec.appendChild(h("h3", null, "Quoted spans (" + spans.length + ")"));
    if (!spans.length) sec.appendChild(h("p", { class: "small" }, "No quotation in this part of the claim."));
    spans.forEach(function (s) { sec.appendChild(spanBlock(entry, s)); });

    var cur = draft.elements[e.id] || (draft.elements[e.id] = { decision: null, reason: "" });
    var blocked = elementStatusSources(entry, e.id).some(function (k) {
      var v = entry.status[k]; return v && (v.text === "mismatch" || v.original === "mismatch");
    }) || !entry.claimOk;
    var box = h("div", { class: "decide" }, h("strong", null, "Your decision on this part: "));
    [["certify", "Certify", "cert"], ["reject", "Reject", "rej"], ["needs_more", "Needs more", ""]].forEach(function (o) {
      var r = h("input", { type: "radio", name: "d-" + e.id, value: o[0], disabled: o[0] === "certify" && blocked,
        onchange: function () { cur.decision = o[0]; saveDraft(card); refresh(); } });
      if (cur.decision === o[0]) r.checked = true;
      box.appendChild(h("label", { class: "opt " + o[2] }, r, h("span", null, " " + o[1])));
    });
    if (blocked) box.appendChild(h("span", { class: "small" }, " (certify disabled: a hash does not match)"));
    var ta = h("textarea", { rows: 2, placeholder: "Reason (required for reject and needs more; say what you read for certify)",
      oninput: function () { cur.reason = ta.value; saveDraft(card); } });
    ta.value = cur.reason || "";
    box.appendChild(h("div", null, ta));
    sec.appendChild(box);
    return sec;
  }

  function renderOverall(entry, draft, errsBox, recordBtn) {
    var card = entry.card;
    var sec = h("section", { class: "sec", id: "overall" }, h("h2", null, "Overall decision and record"));
    sec.appendChild(h("h3", null, "Research rationale in the claim"));
    sec.appendChild(h("div", { class: "ctx" }, String(card.claim.research_rationale || "(none)")));
    var box = h("div", { class: "decide" }, h("strong", null, "Overall: "));
    [["certify", "Certify the claim", "cert"], ["reject", "Reject", "rej"], ["needs_more", "Needs more work", ""]].forEach(function (o) {
      var r = h("input", { type: "radio", name: "overall", value: o[0], onchange: function () { draft.overall = o[0]; saveDraft(card); updateErrors(entry, draft, errsBox, recordBtn); } });
      if (draft.overall === o[0]) r.checked = true;
      box.appendChild(h("label", { class: "opt " + o[2] }, r, h("span", null, " " + o[1])));
    });
    sec.appendChild(box);
    var notes = h("textarea", { rows: 3, placeholder: "Notes (anything a second reader needs; required if the overall decision is not backed by an element reason)",
      oninput: function () { draft.notes = notes.value; saveDraft(card); updateErrors(entry, draft, errsBox, recordBtn); } });
    notes.value = draft.notes || "";
    sec.appendChild(h("div", null, notes));
    var att = h("input", { type: "checkbox", onchange: function () { draft.readOriginal = att.checked; saveDraft(card); updateErrors(entry, draft, errsBox, recordBtn); } });
    att.checked = !!draft.readOriginal;
    sec.appendChild(h("label", { class: "check" }, att, "I read the cited pages of the original sources (not only the extracts on this page). Required to certify."));
    sec.appendChild(errsBox);
    sec.appendChild(recordBtn);
    var hist = state.decisions.filter(function (d) { return d.claim_sha256 === card.claim_sha256; });
    if (hist.length) sec.appendChild(h("p", { class: "small" }, "Recorded in this session: " +
      hist.map(function (d) { return d.overall + " by " + d.reviewer.name + " at " + d.decided_utc; }).join("; ")));
    return sec;
  }

  function currentForm(entry, draft) {
    return { reviewerName: $("reviewer").value, independent: $("independent").checked, overall: draft.overall, elements: draft.elements,
             notes: draft.notes, readOriginal: draft.readOriginal, sourceStatus: entry.status, activeSeconds: draft.activeSeconds };
  }

  function updateErrors(entry, draft, errsBox, recordBtn) {
    var errs = C.validateDecision(entry.card, currentForm(entry, draft), entry.status);
    if (!entry.claimOk) errs.unshift("The claim in this card does not hash to its claim SHA-256; do not certify it.");
    errsBox.textContent = "";
    if (errs.length) errsBox.appendChild(h("ul", { class: "errs" }, errs.map(function (x) { return h("li", null, x); })));
    recordBtn.disabled = errs.length > 0;
  }

  function renderCard() {
    var entry = state.cards[state.selected], root = $("card");
    root.textContent = "";
    if (!entry) { root.appendChild(h("p", { class: "empty" }, "Load a card to begin.")); return; }
    var card = entry.card, draft = draftFor(card);
    var errsBox = h("div", null), recordBtn = h("button", { class: "primary", disabled: true }, "Record this decision");
    var refresh = function () { updateErrors(entry, draft, errsBox, recordBtn); };
    var readiness = card.readiness || {};

    root.appendChild(h("section", { class: "sec" },
      h("h2", null, card.instrument_id + " · claim says whole order status: " + card.claim.whole_order_status),
      entry.claimOk ? chip("ok", "claim hash recomputed here matches") : h("div", { class: "fail" }, "CLAIM HASH DIFFERS: the claim in this card does not hash to the SHA-256 it is filed under."),
      readiness.ready_for_human_review === "yes" ? chip("ok", "machines finished: ready for human review") : chip("warn", "not marked ready for human review"),
      chip("neutral", "text evidence: " + (readiness.text_evidence_tier || "?")),
      readiness.original_copy_replacement_required === "yes" ? chip("warn", "original copy must replace a transcription") : null,
      readiness.quotation_recheck_required === "yes" ? chip("warn", "quotation recheck required") : null,
      h("dl", { class: "kv" },
        h("dt", null, "Claim SHA-256"), h("dd", { class: "mono hash" }, card.claim_sha256),
        h("dt", null, "Filed at"), h("dd", { class: "mono" }, card.claim_key),
        h("dt", null, "Card file SHA-256"), h("dd", { class: "mono hash" }, entry.fileSha),
        h("dt", null, "Exported"), h("dd", null, card.exported_utc + " by exporter " + card.exporter_version))));
    root.appendChild(h("section", { class: "sec" }, h("h2", null, "Checker results"), renderChecker(entry)));
    root.appendChild(h("section", { class: "sec" }, h("h2", null, "AI reviews of this exact claim hash"), renderReviews(entry)));
    root.appendChild(h("section", { class: "sec" }, h("h2", null, "Sources and hashes"),
      h("p", { class: "small" }, "The saved text each quotation was checked against is embedded; this page hashes it with " + (C.engine() || "SHA-256") +
        ". The claim's source hash covers the original file (usually a PDF): attach it here or drop it with the folder to verify it."), renderSources(entry)));
    card.elements.forEach(function (e) { root.appendChild(renderElement(entry, e, draft, refresh)); });
    root.appendChild(renderOverall(entry, draft, errsBox, recordBtn));

    recordBtn.addEventListener("click", async function () {
      var form = currentForm(entry, draft);
      var rec = C.buildDecision(card, entry.fileSha, form);
      await C.sealDecision(rec);
      state.decisions.push(rec);
      storeSet("nihil-decisions", C.toJsonl(state.decisions));
      renderList(); renderCard();
    });
    refresh();
    window.scrollTo(0, 0);
  }

  // ------------------------------------------------------------ export / resume
  function exportDecisions() {
    var name = ($("reviewer").value || "reviewer").replace(/[^A-Za-z0-9_-]+/g, "_");
    var blob = new Blob([C.toJsonl(state.decisions)], { type: "application/x-ndjson" });
    var a = h("a", { href: URL.createObjectURL(blob), download: "nihil-obstat-decisions-" + name + "-" + C.utcNow().slice(0, 10) + ".jsonl" });
    document.body.appendChild(a); a.click(); a.remove();
  }

  async function resume(file) {
    var recs = C.parseJsonl(await file.text()).filter(function (r) { return r.schema === C.DECISION_SCHEMA; });
    recs.forEach(function (r) {
      state.decisions.push(r);
      var d = state.drafts[r.claim_sha256] = { elements: {}, overall: r.overall, notes: r.notes || "", readOriginal: !!(r.attestation && r.attestation.read_original_pages), activeSeconds: r.active_seconds || 0 };
      r.elements.forEach(function (e) { d.elements[e.element] = { decision: e.decision, reason: e.reason }; });
    });
    if (recs.length && recs[0].reviewer) $("reviewer").value = recs[0].reviewer.name;
    setStatus(recs.length + " decision record(s) restored from " + file.name + ".");
    renderList(); if (state.selected >= 0) renderCard();
  }

  // ------------------------------------------------------------ wiring
  function tick() {
    var e = state.cards[state.selected];
    if (e && !document.hidden && Date.now() - state.lastActive < 60000) draftFor(e.card).activeSeconds += 1;
  }

  function init() {
    $("ver").textContent = "v" + C.VERSION; $("ver2").textContent = C.VERSION;
    $("pickDir").addEventListener("change", function (e) { loadFiles(e.target.files); });
    $("pickFiles").addEventListener("change", function (e) { loadFiles(e.target.files); });
    $("pickDecisions").addEventListener("change", function (e) { if (e.target.files[0]) resume(e.target.files[0]); });
    $("exportBtn").addEventListener("click", exportDecisions);
    var drop = $("drop");
    ["dragenter", "dragover"].forEach(function (t) { drop.addEventListener(t, function (e) { e.preventDefault(); drop.classList.add("over"); }); });
    ["dragleave", "drop"].forEach(function (t) { drop.addEventListener(t, function (e) { e.preventDefault(); drop.classList.remove("over"); }); });
    drop.addEventListener("drop", function (e) { loadFiles(e.dataTransfer.files); });
    ["mousemove", "keydown", "scroll", "click"].forEach(function (t) { document.addEventListener(t, function () { state.lastActive = Date.now(); }, { passive: true }); });
    ["reviewer", "independent"].forEach(function (id) {
      $(id).addEventListener("input", function () { storeSet("nihil-" + id, id === "independent" ? String($(id).checked) : $(id).value); if (state.selected >= 0) renderCard(); });
      $(id).addEventListener("change", function () { storeSet("nihil-" + id, id === "independent" ? String($(id).checked) : $(id).value); if (state.selected >= 0) renderCard(); });
    });
    var n = storeGet("nihil-reviewer"); if (n) $("reviewer").value = n;
    $("independent").checked = storeGet("nihil-independent") === "true";
    var prior = storeGet("nihil-decisions");
    if (prior) { try { state.decisions = C.parseJsonl(prior); } catch (e) { state.decisions = []; } }
    setInterval(tick, 1000);
    $("engine").textContent = (window.crypto && window.crypto.subtle) ? "SubtleCrypto" : "JavaScript fallback (no SubtleCrypto in this context)";
    // Served over http(s) (for example for the test run): ?manifest=manifest.json fetches the cards listed there.
    var m = /[?&]manifest=([^&]+)/.exec(location.search);
    if (m && location.protocol !== "file:") autoload(decodeURIComponent(m[1]));
    renderList();
  }

  async function autoload(manifestUrl) {
    try {
      var man = await (await fetch(manifestUrl)).json(), base = manifestUrl.replace(/[^/]*$/, ""), files = [];
      for (var i = 0; i < man.cards.length; i++) {
        var r = await fetch(base + man.cards[i].file), blob = await r.blob();
        files.push(new File([blob], man.cards[i].file.split("/").pop(), { type: "application/json" }));
      }
      await loadFiles(files);
    } catch (e) { setStatus("Could not load " + manifestUrl + ": " + e.message); }
  }

  window.NihilApp = { loadFiles: loadFiles, state: state, select: select };
  init();
})();
