# Stage 21: reuse the previously captured official source index

Stage 14's immutable OFR metadata preserved 4,331 literal PDF/XML/HTML URLs corresponding to 1,546 executive-order identities. This stage crosswalks that manifest against all 3,359 provisional cases before any duplicate live source search.

The output OFFICIAL_SOURCE_CASE_CROSSWALK.csv tracks each prior provisional case and its literal document candidates. ORIGINAL_SOURCE_RETRIEVAL_QUEUE.csv proposes one original-source retrieval per matching case (PDF before XML/HTML); METRICS.json quantifies overlap and provenance hashes. The pipeline uses exactly the URLs already present in frozen government metadata; it does not manufacture links.

Run python research/stage21/code/attach_stage14_sources.py and rerun with --check. The GitHub Actions workflow tests and commits outputs.

The previously attempted live official bulk export was blocked at unblock.federalregister.gov in GitHub Actions. This stage avoids that route by reusing an existing properly acquired index. No site restriction is bypassed.

All retrieved URL candidates remain unverified original-document and legal-impact leads. Explicit source URLs are not themselves proof of content, original operative clauses, earliest cessation, residual effects or independent human certification. This script changes no case status.
