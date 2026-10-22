# Verified existing frozen codebook

[CODEBOOK_2.0.0_UNCHANGED.json](CODEBOOK_2.0.0_UNCHANGED.json) contains the exact recovered bytes of the existing frozen version 2.0.0. This is an evidence copy, not a methodology revision or canonical overwrite. SHA-256: `a312fa9ccef9841da512307e567d200bc73d6fc2bd0132141e94a8aaca180b20`.

The pinned repository archive contains `history/EO_STAGE8_RECONCILED_HANDOFF_2026-10-16.zip`. Its complete 7,107,193 bytes were range-retrieved and hashed to `32af5f7e5f58d2ab03d9003025501b58f679d4560a931e116723704a6f011ff1`, matching [outer-manifest.json](outer-manifest.json). The extracted member matches [STAGE8_SHA256SUMS.txt](STAGE8_SHA256SUMS.txt), and the ZIP CRC was verified. [STAGE8_README_FIRST.md](STAGE8_README_FIRST.md) identifies it as unchanged version 2.0.0.

[MANIFEST.json](MANIFEST.json) supplies portable artifact pointers; [CODEBOOK_PROVENANCE.json](CODEBOOK_PROVENANCE.json) preserves the original recovery record. Its absolute local scratch path is historical metadata, not a link or required file location. [EO_STAGE8-full.receipt.json](EO_STAGE8-full.receipt.json) preserves the exact source URL, range and response headers. The full 3GB outer archive was not downloaded or independently rehashed; this limit is retained explicitly.

To reproduce without a multi-gigabyte download, retrieve bytes `140825250–147932442` of the exact URL in the receipt using HTTP Range. Verify the 7,107,193-byte nested ZIP's SHA-256 above, then extract only `CODEBOOK_2.0.0_UNCHANGED.json` with a standard ZIP reader and verify its member SHA-256. Do not treat a response lacking the expected `206`/`Content-Range` as an equivalent range receipt.
