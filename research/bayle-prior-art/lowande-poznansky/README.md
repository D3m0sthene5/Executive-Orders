# Bayle prior art: Lowande and Poznansky, "Executive Action That Lasts"

Stream: Encyclopedie campaign, prior-art ("Bayle"), Lowande-Poznansky half. Branch `enc/prior-art-lp`. Date: 2026-11-06.
Tier: lead. Secondary-source reading and recomputation from public replication data; no legal status, revocation fact
or count here is settled, and the project's 0 certified whole-lifecycle dossiers is unchanged.

## Citations (two separate works)

- **Dataset.** Lowande, Kenneth. 2023. "Replication Data for: Executive Action that Lasts." Harvard Dataverse, V1
  (released 2023-12-12). https://doi.org/10.7910/DVN/TZ2QKY. Licence CC0 1.0. Three public files: `readme.txt`,
  `figures.R`, `orders.Rda`. ZIP `dataverse_files.zip`, 12,943 bytes, SHA-256
  `7c51d513fe68ec0b8ca0843a2dd28ec053e03b0d7093e0174cd3fba99c7e8d41`; MD5s match Dataverse's listing, which I
  re-read through the public API on 2026-11-06 (no `codebook.pdf`, though the readme lists it).
- **Article.** Lowande, Kenneth, and Michael Poznansky. 2024. "Executive Action That Lasts." *Journal of Public Policy*
  44 (2): 344-365. https://doi.org/10.1017/S0143814X23000442. Open access, CC BY 4.0. Notes with pages in `ARTICLE.md`.
- **Comparison data used for the alignment test.** Thrower, Sharece. 2017. "To Revoke or Not Revoke? The Political
  Determinants of Executive Order Longevity." *American Journal of Political Science* 61 (3): 642-656. Replication file
  `eo_original_list.csv` (6,158 rows, 1937-2013), SHA-256
  `63175aa37c906c2b145baeb0cb0aa9306590ac0b4c7320dc2c1b994ca8e4012a`, supplied by the coordinator from an unpacked
  archive (zipB); I did not record where the archive was downloaded from.
- **Project register.** `jobs/domesday-register/output/REGISTER.csv` on origin/main at `57b814115b17`, git blob
  `58141602d4c805a6a0d3d5c0296e81420499dcc3`, SHA-256 `42880e1fe0c4b588fc255271abf8deb89be16faf886a828f6c4c1f38123803d9`.

## What is here

| File | Content |
|---|---|
| `ARTICLE.md` | What the article and SI say, with pages: never-revoked share, the 20 and 65 errors, coding of revocation, immutable, ceremonial, Chiou-Rothenberg |
| `BASELINE.md` | What L&P measure, recomputed headline numbers, what the project holds, what it would need |
| `CROSSWALK.csv`, `CROSSWALK.md` | L&P and Thrower variables against the frozen codebook 2.0.0 |
| `REQUEST_EMAIL.md` | Draft request to Kenneth Lowande; not sent |
| `NOTES.md` | Owner questions and notes for the coordinator |
| `CHECK_2026-11-07.md` | Independent check findings and how each was resolved |
| `output/` | `year_counts.csv`, `alignment_by_year.csv`, `alignment_summary.json`, `term_definition_check.csv`, `headlines.json`, `thrower_summary.json`, and `aligned_orders.csv` (hypothesis-labelled row-to-EO-number links for 22 years only); about 0.37 MB in total |
| `scripts/` | `lp_headlines.py`, `lp_alignment.py`, `thrower_summary.py` |

Run (Python with pandas, numpy, pyreadr; archive paths are arguments; the `.Rda` is untrusted data, only parsed):

```sh
PY="C:/Users/danie/eo-venvs/enc/Scripts/python.exe -I"
$PY scripts/lp_headlines.py   ORDERS.Rda output
$PY scripts/thrower_summary.py eo_original_list.csv output
$PY scripts/lp_alignment.py   ORDERS.Rda eo_original_list.csv REGISTER.csv output        # 2,000 permutations, seed 20261106
```

## Method of the alignment test

`orders.Rda` has 6,536 rows ordered by year descending and no EO number. Hypotheses, each labelled a hypothesis:
**CAL** (L&P `year` is the calendar year of signing), **ASC** (within a year, rows run in ascending EO-number order),
**DESC** (descending). Steps: (1) per-year row counts of L&P, Thrower and the register; (2) for years with equal L&P and
register counts, pair row k with the k-th smallest (ASC) or largest (DESC) EO number of that year, attach Thrower's flags
by EO number, and score agreement on two signals (not independent of Thrower, see below), L&P `ceremonial` against Thrower `ceremonial`, and L&P
`revoked_next_term` against "Thrower `revoke_year` is by the end of the following four-year block"; (3) compare the
score with 2,000 random pairings of L&P rows to EO numbers within the year (permutation p). The four-year-block rule
was inferred from the year-level pattern of `opposing_next` and chosen over the alternative (revocation inside the
following block only) by how well the per-year shares match L&P's, without any alignment: correlation 0.991, mean
absolute difference 0.66 pp over 72 years, versus 0.859 and 4.45 pp. A year is `STRONG_exact` if every row agrees on both
signals and p <= 0.01; `PARTIAL` if p <= 0.01 and the excess over chance is at least 0.5; `WEAK` if p <= 0.05;
`NONE` otherwise; `UNTESTABLE` if fewer than 3 positive signal values.

## Numbers (all from `output/`)

**Per-year counts, L&P vs the register vs Thrower** (`year_counts.csv`). The register has three known defects that
affect year counts (coordinator check, 2026-11-07): `EO:7700A` duplicates `EO:7700` (Thrower has only 7700), and
`EO:10276` carries a date typo (1961-07-31; it is a 1951 order, as its neighbours 10275 and 10277 are). With the raw
register, L&P equals it in 76 of 84 years 1937-2020; the three extra mismatches are 1937 (256 vs 257), 1951 (118 vs 117)
and 1961 (84 vs 85), and they vanish once those two defects are removed, which `lp_alignment.py` does (documented in the
script). After that, L&P equals the register in 79 of 84 years. The five remaining differences are each one order and
unresolved: 1945 (169 vs 168), 1948 (108 vs 109), 2009 (43 vs 44), 2010 (36 vs 35), 2019 (44 vs 45); 2021 is 64 vs 65
through 30 June. L&P equals Thrower in 54 of 77 years 1937-2013; the 23 differences are mostly Thrower's president-coded
years: in each of 1952/53, 1960/61, 1968/69, 1976/77, 1980/81, 1988/89, 1992/93, 2000/01 the inauguration-year pair
differs by plus or minus the number of January orders (10, 14, 9, 17, 26, 5, 6, 12), plus 2008/09 (-5/+4) and
single-order differences in 1941, 1945, 1946, 1948, 2010. 105 Thrower orders carry a year different from the register's
signing year (after the 10276 correction). L&P's year is the calendar year.

**Ceremonial.** The L&P and Thrower ceremonial counts per calendar year are equal in every year 1937-2013 (100 orders in
Thrower; L&P has 113: the extra 13 are in 2014-2021, where Thrower has no data).

**Alignment.** Count-matched and testable (Thrower joined): 73 years. Outcome under ASC: STRONG_exact 9 years (1942,
1943, 1944, 1947, 1959, 1960, 1982, 1987, 1988), PARTIAL 13 (1940, 1950, 1951, 1952, 1958, 1975, 1981, 1984, 1990, 1994,
1999, 2004, 2005), WEAK 6 (1938, 1961, 1964, 1986, 1996, 1997), NONE 38, UNTESTABLE 7 (1949, 2006-2008, 2011-2013).
DESC: 2 of 66 informative years have p < 0.05 (chance expects about 3); mean excess -0.011. ASC: 28 of 66 informative
years have p < 0.05; mean excess 0.35. The WEAK years (small excess over chance, below 0.5) are not used; with 66
informative years about 3 would reach p <= 0.05 by chance and 6 are seen, 4 of them at p < 0.01, so I neither call them
aligned nor call them noise.

How tight is the link in the 22 STRONG or PARTIAL years (1,937 rows)? The figure "1,899 of 1,937 rows agree on both
signals (98.0%)" is inflated, because most rows carry no positive signal (no ceremonial order, no revocation) and chance
alone gives about 1,495 agreements (77%) in those years. The honest figure is among rows with any positive signal: 246
of 284 agree (86.6%). (The checker found 231 of 268 on the earlier set of 21 years before the register defects were
removed.) The 38 disagreements are mostly adjacent pairs (for example 12457/12458, 12700/12701, 12891/12892,
12929/12930, 13362/13363) and the 1981 block 12263-12336, consistent with local swaps of same-day orders and with the
president-recoding the SI describes, though I did not test either explanation. The two signals are not independent of
Thrower: L&P's `ceremonial` is carried over from Thrower's (per-year counts equal in every year 1937-2013) and both
revocation variables come from the disposition tables. Agreement therefore tests row order, not the accuracy of either
file or the identity of any order.

**Does alignment hold?** Not as a general rule. ASC explains the within-year order in 22 of 73 testable years (about
30% of rows, 1,937 rows); in 38 testable years it does not beat chance although the year's counts of ceremonial orders
and next-term revocations match Thrower's. The within-year order in those years is some other order I could not
recover (I tried ascending and descending number, date and title in a few years). So the file is not in a single known
order, and a blanket assignment of EO numbers would be wrong for most rows. `output/aligned_orders.csv` therefore holds
only the 22 supported years, each row labelled with `year_alignment_class`, `year_p_ASC`, `year_excess_ASC`,
`row_signals_agree`, `row_has_positive_signal` and the hypothesis text. 2014-2021 are untestable (Thrower ends in 2013);
L&P `immutable` and `foreign` have no signal from Thrower at all, so even in supported years the link to those variables
rests on the ceremonial and revocation signals.

**Recomputed headline numbers** (`headlines.json`; full table in `BASELINE.md`): n = 6,536; ceremonial 113; non-ceremonial
6,423; revoked in the following term 11.44% (all) and 11.60% (non-ceremonial), article "11%"; immutable 41.4%, article "about
41%"; immutable share 19.4 pp lower under divided government, article 19; Table C.1 column 1 and column 3 reproduced
(n 6,373 and 6,486; AIC 4,221.076 and 4,268.891; all coefficients to three decimals; standard errors within 0.003); marginal effect of immutability -6.7 pp
against the article's 6.6; revoked-next-term 6.1% (immutable) against 15.6% (mutable) among non-ceremonial orders. The
article's "74% never revoked" and "30% vs 21% ever revoked" are not in `orders.Rda`; Thrower's list (1937-2013) gives
74.3% never revoked (74.0% non-ceremonial); but 426 of those 4,578 orders are coded superseded, so 67.4% are neither revoked nor superseded. "Never revoked" is not "formally still valid".

**Are the 20 missing revocations and 65 misattributions listed individually?** No. They appear only as counts in SI-2
and SI-3. The Dataverse deposit has three files and no list; the readme offers the underlying data on request.

## Limits

- The deposit has no codebook, so the term rule, the sample end date and ceremonial coding are reconstructed or taken from
  the article.
- The article says January 18, 2021 (p. 351); the SI says the first half of 2021 (SI-2); the data have 64 rows for 2021,
  matching the register through 30 June (65). I followed the data.
- The register's dates and numbers are the project's best index, not authenticated identities; a one-order difference in a
  year can be a register or L&P error or a date boundary. Three of the nine (1937, 1951, 1961) are the known register defects named above and are corrected in the script; I did not resolve the other six (1945, 1948, 2009, 2010, 2019, 2021).
- Alignment is a labelled hypothesis. It uses Thrower's revocation years, which L&P say were later corrected (20 missing
  revocations, 65 wrong presidents), so even a true alignment would not agree on every row.
- Not done: I did not contact Lowande, did not obtain the SI replication materials, did not read the figure values in
  Figure C.1, and did not test why the within-year order fails in 38 years.
- The ZIP and PDFs are not committed. Bytes added to the repository by this stream: see `NOTES.md` and the final report.
