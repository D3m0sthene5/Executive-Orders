# Stage 21: bulk authoritative-index acquisition before mass legal review

**Goal:** acquire the Office of the Federal Register's entire numbered executive-order index since 1937 once, reuse its catalog information across all 3,359 provisionally classified cases and 73 high-fanout shared executive-order authority references, and distinguish candidate source links from authenticated original documents and lawful cessation.

The [OFR official EO bulk download page](https://www.federalregister.gov/presidential-documents/executive-orders) links to a JSON export with pre-1994 results enabled. Our tool requests that exact collection and the stated set of metadata fields, including signing/publication dates, volume/page citations, document URLs, and **editorial disposition notes**.

Run from repository root: \`python -m unittest discover -s research/stage21/code -p 'test_ofr_bulk_excavator.py' -v\`, then \`python research/stage21/code/ofr_bulk_excavator.py --fetch\` and \`python research/stage21/code/ofr_bulk_excavator.py --check\`. Or trigger the [GitHub Actions workflow](../../.github/workflows/stage21-ofr-bulk.yml); it will fetch, test, and preserve a losslessly compressed copy of the original response in \`sources/OFR_BULK_RESPONSE.json.gz\` with a custody SHA-256 and retrieval timestamp.

Expected outputs under \`output/\`:

* \`OFR_PROVISIONAL_CASE_CROSSWALK.csv\`: all 3,359 provisional cases, official-index matches (if unique), possible signing-date conflicts, bibliographic URLs, and unverified disposition notes.
* \`OFR_SHARED_EO_FAMILIES.csv\`: the 73 cited-EO source families representing 269 case–source research links. Acquire matched original text once; evaluate case-specific clause impacts separately.
* \`OFR_EDITORIAL_DISPOSITION_LEADS.csv\`: full editorial note text, for reverse-ending research. **No note is an established legal ending date.**
* \`METRICS.json\`: actual match/missing/conflict counts and the source SHA-256.

Scientific safeguards: the original response and input CSVs are cryptographically bound to the output; partial, unusually small or oversized feeds are rejected; order-number collisions and signing-date conflicts are quarantined. Only pre-cutoff signed instruments can match. Catalog/HTML links are bibliographic leads and FederalRegister.gov explains that its online XML is not yet an official legal edition; legal verification must consult original signed instruments or official GovInfo images where available. Human reviewers must still evaluate the complete original clause inventory, earliest cessation versus later formal revocation, surviving rights, counterevidence, and independent source-checked claims. **This stage issues zero legal certifications and never modifies an earlier status or population ledger.**
