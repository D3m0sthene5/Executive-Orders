# clause_inventory, worker H6-w13 (2026-11-05)

Sheets edited: decisions.csv (original_confirmed, original_pages_confirmed, inventory_confirmed, working_text) and clauses.csv (one row per clause, clause_id blank, inventory_source_id as FILE:path@start-end with absolute character offsets). No dossier exists, so the kit cannot apply or check these sheets. All other columns untouched. 4155's row is untouched.

original_confirmed is false everywhere: no held text is an acceptable original.

- EO:4309 done. Opened the ProQuest text and PDF PT1-1925-EO-4309.pdf (page image). One clause (withdrawal pending resurvey, with its duration). OCR says "September 24, 1926"; the image says 1925.
- EO:6798 done. Opened the APP live text and the DOCUMENTS.jsonl and MIRROR_DOCUMENTS.jsonl rows (heading, date and text_sha256 agree). One clause (temporary withdrawal for a lookout station; the "continue unless revoked" sentence is its duration).
- EO:4155 blocked: retain bytes of the CSC 42nd annual report PDF (SERIALSET-08663_00_00-002-0068-0000, PDF page 192). The held text is a report passage, possibly an abstract; the PDF is not held, so the page check cannot be done. The operative sentence is a permission to reinstate Mrs. Bowman and Mrs. Sullivan.
- EO:5615 done, on the APP mirror text. The OFR 1974 Hoover vol. II PDF is a Git LFS pointer (133 bytes), so the "official" text's source page cannot be inspected. The MIRROR_DOCUMENTS row (heading, date, text_sha256 80c5287e…) agrees. The OFR OCR text and the Hathi text read the same. One transfer clause.
- EO:2280 done. ProQuest text and page image. One withdrawal clause.
- EO:2491 done. ProQuest text and page image. OCR reads "[No. 2191.]"; the image reads 2491, and the text cites No. 2268 of Oct. 30, 1915. Two clauses: (a) withdrawal and reservation of the Idaho areas; (b) partial revocation of the 1915 withdrawal and restoration to the public domain.
- EO:660 done. Wikisource capture (revision 1873308). The held capture is the page record; no printed pages exist and there is no stated page-check rule for Wikisource, so pages_confirmed rests on the capture's title, revision, date and text matching the register. A reviewer may want to confirm that. Two clauses: (a) classification of the positions; (b) retention of present occupants and transfer eligibility after three years.
- EO:3804 done. ProQuest text and page image. Four clauses, one per numbered paragraph.

Tool defects: none used. The sample's clause counts (1) were wrong for 2491, 660 and 3804. status/ and original_text/ were empty, so there were no leads from earlier workers.
