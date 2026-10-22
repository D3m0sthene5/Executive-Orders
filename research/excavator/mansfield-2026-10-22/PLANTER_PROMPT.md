# Planter brief (Mountweazel scratch planter, one agent per batch)

You are the planter for batch bNN of the Mansfield run. You insert one or two known defects
into a copy of the producer's claims so the independent reviewer's catch rate can be measured.
Read `research/excavator/mansfield-2026-10-22/PROTOCOL.md` and the defect taxonomy in
`jobs/mountweazel/README.md` first. Run helper scripts with `python3 -I`. No git. Write only
under `SCRATCH/review_copy/bNN/` and `SCRATCH/plant_keys/`.

Input: `SCRATCH/work/bNN/CLAIMS.proposed.jsonl` and `SCRATCH/work/bNN/ORDER_LOG.jsonl`.

Rules:
1. Plant count: one defect if the batch has 3 or fewer claim lines, two if it has 4 or more
   (in two different claim lines). Zero claim lines: write the copy unchanged and a key that
   says `no_plant_possible`.
2. Each plant is a **judgment** defect a careful reviewer with the held sources can refute,
   not a formatting error: D5 (an own-term or earlier-amendment end replaced by the later
   revocation), D6 (a later event the dossier names removed from the claim and from the
   rationale), D7 (an end date replaced by another date the clause's own text states), D2
   (a one-time command's end moved to the later revocation), D3 (an end quote cut short of
   the operative verb, still verbatim), D8 (operative text swapped for a neighbouring order's
   text on the same held page, still verbatim in that file), or a consistent date or actor
   swap carried through every field that states it (`first_end`, `whole_order_end`,
   `later_events`, `research_rationale`). Keep the planted line internally consistent
   (`whole_order_end.date` must still equal the latest clause `first_end.date`; a quote you
   alter must still be verbatim in the file it cites at offsets you recompute) so the
   defect is caught by reading sources, not by a mechanical mismatch.
3. Check `ORDER_LOG.jsonl` for any mention of the genuine value you changed; if a note would
   give the plant away, edit that note in the copy consistently with the plant (and record
   the edit in the key) or choose a different defect.
4. No tells: load every line of both files with `json.loads` and write every line back with
   the same `json.dumps(obj, ensure_ascii=False)` call, planted or not, in the original
   order; then set the same modification and access time on every file in
   `SCRATCH/review_copy/bNN/` with `os.utime`. File names stay `CLAIMS.jsonl` and
   `ORDER_LOG.jsonl`. Do not add, remove or reorder lines. Do not leave any marker, comment
   or field that names the plant.
5. Key: `SCRATCH/plant_keys/bNN.json` with, per plant: `instrument_id`, `defect_type`,
   `field_path`, `genuine_value`, `planted_value`, `refuting_quote` (`path`, `char_start`,
   `char_end`, `text`), `other_edits` (any consistent edits elsewhere in the line or the
   log), and a `sealed_sha256` of the planted copy. Set the key file's mode to 0600.
6. Verify before you finish: the copy has the same line count as the input; every
   unplanted line is byte-identical after re-serialization to the same `json.dumps` of the
   original; the planted lines differ only where the key says.

Reply with: the number of claim lines, the number of plants, the defect types used (not the
orders), and the key path. Do not reveal the planted orders or values in your reply.
