# Producer report, packet o08 (Tribonian), producer: Claude (Sonnet 5.5)

Start UTC 2026-11-04T05:31:33Z. End UTC 2026-11-04T06:38:18Z (a usage-limit pause fell inside this span).
Final applied directory: research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v5 (applied-v1 to v4 are retained earlier versions; applied-v3 is an incomplete run killed by a tool timeout).

## Outcomes (30 orders: 26 submitted, 4 blocked)

Submitted (26): EO 8907, 8913, 8917, 8918, 8919, 8925, 8933, 8934, 8935, 8936, 8945, 8948, 8949, 8958, 8966, 8967, 8968, 8993, 8994, 8995, 8996, 8997, 9002, 9003, 9009, 9010. Each is a one-clause retirement exemption (section 204 of the act of June 30, 1932) for a stated term ("for a period of one year ending ..." or six months for EO 8935; class exemption for EO 8997). The first end is the order's own stated end date, recorded inclusive with the exclusive reading disclosed, end_id the order's own-term evidence. Savings: transferred_or_accrued (order text). Registered text is the APP mirror transcription (original not yet held). EO 8934: EO 10123 (1950) cites "Executive Order No. 8934 of December 18, 1941", a different date and subject (held EO 9635 names Executive Orders 8984 of December 18, 1941); rejected as a misnumbered reference and not an end; the exemption expired 1943-01-31 anyway. Serial exemptions (8917, 8919, 8967, 8995, 9002, 9009) recite earlier orders, which precede them and are not events.

Blocked (4):
- EO 8931: parent EO 1888 leave regime has no held end; EO 9467 restates paragraph 24 (amendment under the strike-and-insert ruling, not an end); EO 10263 revoked only section 17. Missing: instrument showing the end of EO 1888 sections 20 onward.
- EO 8978: EO 9650 (1945-10-29) is the likely express discontinuance of the five areas but its text is overflow only, not citable in the packet; the clause inventory also needs correction (registered span includes neighbouring orders). Missing: EO 9650 as a citable source supplement and an inventory correction.
- EO 8953: legal end identified (EO 9720, 1946-05-08, item 5, text held) plus a second one-time clause (supersession of EO 8403, exhausted 1941-11-27), but applied-v2 failed quote_verbatim on every quote because clause-drafts SOURCES.jsonl maps the FR PDF hash to EO 8952/8954 records, not EO 8953. Missing: a registered source record for the EO 8953 FR text.
- EO 8961: command (general revocation) spent on 1941-12-06; EO 10768 (1958) recites it and is a later event, not an end. The only registered end span is the whole FR page text, which brought in an OCR token from the next order that failed order_exists, and the clause-id span was refused as an end source. Missing: a registered span limited to the EO 8961 text.

## What took the time
- Submitted 26: reading all texts once, one generated sheet script; apply runs (3 to 7 minutes each) dominated.
- 8931: checking EO 1888 amendments and the 1989 codification for a parent end.
- 8978: reading the large EO 9650 actor context and the registered span.
- 8953 and 8961: two apply/check cycles to find the checker custody problems.
- 8934: tracing EO 10123 and EO 9635.

## Batch-check (applied-v5)
30 members; 26 assembled, 4 blocked. Strict claim pass 26, fail 0. Actual checker: 26 claims, 0 mechanical failures, 4 all-checks-passed, 22 mechanical_unverified, all only `source_held:custody_record_only` and the known `date_valid` verbatim-evidence note (coordinator is retaining those bytes). batch-check exits 1 because of the unverified results.

## Geddes
applied-v4 lint: 1 flag (EO 9009, reported_empty_search_has_hit: the catalog edge "See: EO 8615, December 18, 1940" was present). Fixed in applied-v5 (wording now reports the hit as the link to the earlier exemption). applied-v5 lint: 26 claims, 0 flags, 0 coverage gaps. Resolution recorded in applied-v5/GEDDES_RESOLUTIONS.json.

## Full-packet files opened beyond views
LOOKUPS.md (read), PACKET.json (loaded once via load_packet for TERM evidence spans and evidence ids), decisions.csv and clauses.csv (edited). READ.md and LOOKUPS.details.json not opened.

## Tool defects and notes
- `batch.load_packet` takes Path arguments and returns a (packet, extra) tuple.
- apply with a 590 s foreground timeout was killed once (exit 144); runs now go in the background.
- A shell variable P was observed pointing at o09 in one chained command (batch-check failed on an o09 path); I reran with literal o08 paths. No o09 files were written by me.
- The checker resolves a Federal Register issue-PDF hash to whichever order's clause-drafts record carries it first, which broke EO 8953 quotes.
- Scratch files: /tmp/claude-0/tribonian-work/o08/.
