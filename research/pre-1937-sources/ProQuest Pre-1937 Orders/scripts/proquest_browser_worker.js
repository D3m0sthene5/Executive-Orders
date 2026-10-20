/*
 * Portable single-order ProQuest worker; defining it does not browse or save.
 *
 * Before using this in a browser session, the resuming assistant must read the
 * CURRENT Browser skill and runtime API documentation and connect through that
 * authorized runtime. Supply its browser and a deliberately selected recordTab,
 * plus ROWS parsed from the unchanged original attachment. Do not reuse old tab
 * IDs, credentials, browser bindings, or computer-specific paths.
 *
 * const downloader = createProquestDownloader({browser, recordTab, rows});
 * downloader.state();             // starts paused; no browser action
 * downloader.resume();            // ONLY after the user says "go"
 * const result = await downloader.save(nextExactRow); // or save("EO:29")
 * downloader.pause();             // no further requests after await boundaries
 *
 * There is no automatic queue loop. Persist every returned per-order result
 * using proquest_progress.py record. A completed viewer Save command produces
 * saved_requested, never a claim that a file or repository copy was verified.
 * The caller should pause and handle results requiring browser/user attention.
 */

function createProquestDownloader({browser, recordTab, rows}) {
  if (!browser || !recordTab || !Array.isArray(rows) || rows.length === 0) {
    throw new TypeError("Supply browser, recordTab, and original nonempty ROWS.");
  }

  const sourceFields = Object.freeze(["id", "n", "y", "pdf", "rec"]);
  const originals = new Map();
  const frozenRows = Object.freeze(rows.map((input) => {
    if (!input || typeof input.id !== "string" || typeof input.n !== "string"
        || input.id !== "EO:" + input.n
        || !(input.y === null || Number.isInteger(input.y))) {
      throw new TypeError("Every original row needs its exact EO id, number, and year.");
    }
    if (originals.has(input.id)) {
      throw new TypeError("Duplicate original EO ID: " + input.id);
    }
    const row = Object.freeze(Object.fromEntries(sourceFields.map((key) => [key, input[key]])));
    for (const key of ["pdf", "rec"]) {
      if (row[key] === undefined || row[key] === null) continue;
      if (typeof row[key] !== "string" || new URL(row[key]).protocol !== "https:") {
        throw new TypeError("Original source links must be supplied HTTPS strings.");
      }
    }
    originals.set(row.id, row);
    return row;
  }));

  const minimumSpacingMs = 12000;
  let paused = true;
  let pauseReason = "Waiting for the user's go instruction";
  let pauseGeneration = 0;
  let inFlight = false;
  let currentId = null;
  let nextRecordAt = 0;
  let activePdfViewer;

  class PausedOperation extends Error {}

  function state() {
    return {
      paused,
      pause_reason: pauseReason,
      in_flight: inFlight,
      current_id: currentId,
      original_rows: frozenRows.length,
      minimum_spacing_ms: minimumSpacingMs,
      next_record_start_at: nextRecordAt ? new Date(nextRecordAt).toISOString() : null
    };
  }

  function resume() {
    paused = false;
    pauseReason = null;
    return state();
  }

  function pause(reason = "User requested pause") {
    paused = true;
    pauseReason = String(reason);
    pauseGeneration += 1;
    return state();
  }

  function entitlementKey(url) {
    try {
      return decodeURIComponent(String(url)).toLowerCase().split("|").pop().split(/[&#?]/)[0];
    } catch (_) {
      return null;
    }
  }

  function outcome(audit, status, stage, extra = {}) {
    const result = {
      ...audit,
      status,
      stage,
      timestamp: new Date().toISOString(),
      terminal: status === "saved_requested" || status === "link_unavailable",
      filesystem_verified: false,
      ...extra
    };
    if (typeof result.evidence !== "string" || !result.evidence.trim()) {
      result.evidence = "Observed at " + stage + ": " + (result.error || status);
    }
    return result;
  }

  function recordResponseOutcome(audit, dom) {
    const text = String(dom);
    if (/Access is denied/i.test(text)
        && /Your Library['’]s ProQuest Subscription needs to be updated/i.test(text)) {
      return outcome(audit, "link_unavailable", "record_content", {
        requires_attention: false,
        reason: "library_subscription_unavailable",
        evidence: "The exact supplied record link returned ProQuest: Access is denied. Your Library's ProQuest Subscription needs to be updated.",
        record_response: text.slice(0, 2400)
      });
    }
    if (/document (?:was |is )?not found|could not find (?:this|the) document|document is no longer available|404 Not Found/i.test(text)) {
      return outcome(audit, "link_unavailable", "record_content", {
        reason: "supplied_record_unavailable",
        evidence: text.slice(0, 2400)
      });
    }
    if (/captcha|verify you are human|sign in to access|log in to access|ERR_BLOCKED_BY_CLIENT|Access(?: is)? Denied/i.test(text)) {
      return outcome(audit, "error_unresolved", "record_content", {
        requires_attention: true,
        error: text.slice(0, 2400),
        evidence: "The supplied record displayed a browser, access, or sign-in obstacle: " + text.slice(0, 2400)
      });
    }
    return null;
  }

  async function save(input) {
    const id = typeof input === "string" ? input : input && input.id;
    const row = originals.get(id);
    // Unknown identities cannot form a valid audit event. Reject them before any
    // browser operation rather than inventing an ID or a source URL.
    if (!row) throw new RangeError("EO ID is absent from the frozen original source: " + String(id));

    const audit = {
      id: row.id,
      n: row.n,
      y: row.y,
      source_url: row.rec,
      supplied_pdf_url: row.pdf,
      started_at: new Date().toISOString()
    };
    if (typeof input !== "string" && sourceFields.some((key) => input[key] !== row[key])) {
      return outcome(audit, "error_unresolved", "source_validation", {
        requires_attention: true,
        evidence: "The supplied work row differs from the frozen original row; no browser request was made."
      });
    }
    if (paused) {
      return outcome(audit, "error_unresolved", "paused", {
        requires_attention: false,
        evidence: "The downloader is paused; no browser request was made. " + pauseReason
      });
    }
    if (inFlight) {
      return outcome(audit, "error_unresolved", "busy", {
        requires_attention: false,
        evidence: "Another order is still in progress; this order made no browser request."
      });
    }
    if (!row.rec || !row.pdf) {
      return outcome(audit, "link_unavailable", "source_validation", {
        evidence: "The original row has no supplied PDF or record link; no alternate URL was constructed."
      });
    }

    inFlight = true;
    currentId = row.id;
    const generation = pauseGeneration;
    let stage = "pace";
    let saveCompleted = false;
    const checkActive = () => {
      if (paused || generation !== pauseGeneration) {
        throw new PausedOperation(pauseReason || "A pause interrupted this attempt");
      }
    };

    try {
      checkActive();
      while (Date.now() < nextRecordAt) {
        await recordTab.playwright.waitForTimeout(Math.min(Math.max(0, nextRecordAt - Date.now()), minimumSpacingMs));
        checkActive();
      }
      stage = "close_previous_viewer";
      if (activePdfViewer) {
        const previousViewer = activePdfViewer;
        activePdfViewer = undefined;
        try {
          await previousViewer.close();
        } catch (error) {
          audit.previous_viewer_close_notice = String(error);
        }
        checkActive();
      }

      stage = "record_navigation";
      checkActive();
      nextRecordAt = Date.now() + minimumSpacingMs;
      audit.record_started_at = new Date().toISOString();
      try {
        await recordTab.goto(row.rec);
      } catch (error) {
        audit.navigation_notice = String(error);
      }
      checkActive();

      stage = "record_content";
      const recordDom = await recordTab.playwright.domSnapshot();
      checkActive();
      const recordObstacle = recordResponseOutcome(audit, recordDom);
      if (recordObstacle) return recordObstacle;
      await recordTab.playwright.locator('embed[type="application/pdf"]').waitFor({state: "attached", timeoutMs: 7000});
      checkActive();
      audit.title = await recordTab.title();
      checkActive();
      const embedded = await recordTab.playwright.locator('embed[type="application/pdf"]').getAttribute("src");
      checkActive();
      if (!embedded) {
        return outcome(audit, "error_unresolved", stage, {
          evidence: "The observed PDF embed has no source URL; no PDF viewer was opened."
        });
      }
      audit.observed_pdf_url = new URL(embedded, row.rec).href;
      const expectedKey = String(row.y) + "-eo-" + row.n.toLowerCase();
      const actualKey = entitlementKey(audit.observed_pdf_url);
      if (actualKey !== expectedKey) {
        return outcome(audit, "error_unresolved", "identity", {
          actual_key: actualKey,
          expected_key: expectedKey,
          evidence: "The record PDF entitlement differs from the supplied EO year and number; no Save command was issued."
        });
      }

      const before = new Set((await browser.tabs.list()).map((tab) => tab.id));
      checkActive();
      stage = "open_pdf_viewer";
      await recordTab.playwright.getByRole("button", {name: "PDF", exact: true}).click();
      checkActive();
      let popupInfo;
      for (let poll = 0; poll < 5; poll += 1) {
        const tabs = await browser.tabs.list();
        checkActive();
        popupInfo = tabs.find((tab) => !before.has(tab.id)
          && (tab.url || "").includes("/pdfViewer?")
          && entitlementKey(tab.url) === expectedKey);
        if (popupInfo) break;
        await recordTab.playwright.waitForTimeout(600);
        checkActive();
      }
      if (!popupInfo) {
        return outcome(audit, "error_unresolved", stage, {
          evidence: "The observed PDF control was clicked, but no new PDF viewer tab matching this EO appeared; no Save command was issued."
        });
      }
      activePdfViewer = await browser.tabs.get(popupInfo.id);
      checkActive();
      audit.viewer_url = popupInfo.url;

      stage = "pdf_render";
      await activePdfViewer.playwright.getByRole("button", {name: "Save", exact: true}).waitFor({state: "visible", timeoutMs: 6000});
      checkActive();
      await activePdfViewer.playwright.getByRole("region", {name: /^Page/}).first().waitFor({state: "attached", timeoutMs: 6000});
      checkActive();
      const pdfDom = await activePdfViewer.playwright.domSnapshot();
      checkActive();
      audit.pages = Number(pdfDom.replace(/[\u2066-\u2069]/g, "").match(/- generic: of (\d+)/)?.[1] || 0);
      if (audit.pages < 1) {
        return outcome(audit, "error_unresolved", stage, {
          evidence: "The PDF viewer has no confirmed page count; no Save command was issued. " + pdfDom.slice(0, 1800)
        });
      }

      stage = "save";
      await activePdfViewer.playwright.getByRole("button", {name: "Save", exact: true}).click();
      saveCompleted = true;
      audit.save_requested_at = new Date().toISOString();
      checkActive();
      stage = "save_observation";
      try {
        audit.save_control_enabled_after_click = await activePdfViewer.playwright.getByRole("button", {name: "Save", exact: true}).isEnabled();
      } catch (error) {
        audit.save_control_observation_error = String(error);
      }
      return outcome(audit, "saved_requested", "save", {
        evidence: "The expected PDF entitlement matched, the document rendered with a confirmed page count, and the viewer Save command completed; local filesystem completion was not independently observed."
      });
    } catch (error) {
      if (saveCompleted) {
        return outcome(audit, "saved_requested", "save", {
          paused_after_save: error instanceof PausedOperation,
          observation_notice: String(error),
          evidence: "The expected document rendered and the viewer Save command completed before the subsequent pause or observation error; local filesystem completion was not independently observed."
        });
      }
      if (error instanceof PausedOperation) {
        return outcome(audit, "error_unresolved", stage, {
          requires_attention: false,
          paused_during_attempt: true,
          evidence: "The attempt stopped after a pause request at " + stage + "; no completed Save command was confirmed."
        });
      }
      if (stage === "record_content" && !paused && generation === pauseGeneration) {
        try {
          const finalRecordDom = await recordTab.playwright.domSnapshot();
          checkActive();
          const finalObstacle = recordResponseOutcome(audit, finalRecordDom);
          if (finalObstacle) return finalObstacle;
          audit.record_response = String(finalRecordDom).slice(0, 2400);
        } catch (snapshotError) {
          audit.record_observation_error = String(snapshotError);
        }
      }
      return outcome(audit, "error_unresolved", stage, {
        error: String(error),
        save_may_have_been_requested: stage === "save",
        evidence: "Observed at " + stage + ": " + String(error)
          + (stage === "save" ? ". The Save command did not report completion; inspect file evidence before repeating it." : "")
      });
    } finally {
      inFlight = false;
      currentId = null;
    }
  }

  return Object.freeze({resume, pause, state, save});
}
