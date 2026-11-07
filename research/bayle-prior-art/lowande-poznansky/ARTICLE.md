# What Lowande and Poznansky (2024) say, with page numbers

Reading notes on the open-access article and its Supplementary Information (SI). Lead tier: a published secondary
source, read once from public pages by Bayle (L&P stream), 2026-11-06. Nothing here is a project finding. Quotations are
short phrases; the rest is paraphrase. The PDFs are not in git.

## Sources held

| Item | URL | Bytes | SHA-256 | Retrieved |
|---|---|---:|---|---|
| Article PDF, J. Public Policy 44(2): 344-365 (22 PDF pages) | `https://www.cambridge.org/core/services/aop-cambridge-core/content/view/AABF3ACB297FA8B252507582A9B4B68E/S0143814X23000442a.pdf/executive-action-that-lasts.pdf` | 354,137 | `3582e2aa588c8ffe32883dd6748ac71323fe104a23a2db18e7f37abd2b55f780` | 2026-11-06 |
| Supplementary Information PDF (18 pages, numbered SI-1 to SI-18) | `https://static.cambridge.org/content/id/urn:cambridge.org:id:article:S0143814X23000442/resource/name/S0143814X23000442sup001.pdf` | 256,387 | `6f228e57a33214b5f3d533943f514b0ada3d6ae8cf7d16c9ba36806913791ba6` | 2026-11-06 |

Licence: Creative Commons Attribution 4.0 (stated on article p. 344). DOI of the article: 10.1017/S0143814X23000442; the
SI is announced at the same DOI (p. 362). Access: public pages only, no login. `www.cambridge.org/robots.txt` allows
`/core/services/aop-cambridge-core/content/view/` for all agents; `static.cambridge.org/robots.txt` returned 404 (no
restrictions published). One request per file. Page numbers below are the journal's printed pages (PDF page n is
journal page 343+n); SI pages are the SI's own "SI-n" numbers.

Where the text could not be checked: the SI marks a footnote "16" after the sentence about errors in the data (SI-2), but
no footnote text appeared in the extracted text layer, so I cannot say whether it lists anything. The Dataverse readme
says the replication materials for the SI and the underlying order dataset are "provided upon request", so the SI
tables are public but the order-level data behind them are not.

## 1. Share of orders never formally revoked

- Abstract (p. 344): "most executive actions are never formally revoked."
- Introduction (p. 345): "About 75% of all executive orders have never been revoked", and the stock of orders on the
  books has risen monotonically since the mid-20th century.
- Findings (p. 354): "The vast majority (74%) of executive actions are never revoked" in the non-ceremonial analysis
  population. The text then sets aside "a mass revocation of orders from 1986": without it the number of orders active
  "on paper" has risen monotonically.
- Same page: 30% of mutable and 21% of immutable orders are revoked (p < 0.001), "consistent across both ceremonial and
  non-ceremonial orders". These are ever-revoked shares; the deposited `orders.Rda` does not carry the ever-revoked
  variable, so BASELINE.md could not recompute them.
- Sample (p. 351): "nearly 6,500 executive orders issued between 1937 and January 18, 2021"; the SI (SI-7) says 6,536
  orders. See the cutoff discrepancy in README.md.
- Note 4 (p. 353): a majority of revoked orders were revoked by a president of the same party as the issuer, and "About
  29%" of revoked orders were revoked by the president who first signed them.

## 2. Errors in Thrower's data: 20 missing revocations, 65 wrong revoking presidents

These appear only in SI Section A ("Tracking Active Executive Orders", SI-2 to SI-4); the main text only says the
authors "updated the original data with the most up-to-date records" and that the coding of revoking and issuing
presidents differs, "which we detail in the SI" (pp. 351-352).

What the SI says, paraphrased with page numbers:

- SI-2: the analysis starts from "a version of the original dataset that has been corrected for errors" and extends it to
  the first half of 2021. There are "roughly 1,600 total revocations". The source is the National Archives Executive
  Orders Disposition Tables (to 2017) and the Federal Register (after 2017).
- SI-2: against recent versions of those tables, "20 revocations ... are missing from the original study"; another 30
  revocations since 2013 could not be in the original; the original codes one order as revoked that has not been. The
  authors suggest the tables themselves were revised after Thrower collected the data.
- SI-2: 8 further supersessions that the original dataset excludes, and a term "nullified" that the original excludes
  entirely, adding 37 cases. They note that nullification, revocation, amendment and supersession are terms presidents
  "adopt and apply ... at their discretion", and that no procedural rule requires an order to be formally ended for it to
  be inactive.
- SI-3: Thrower's unit is directive-year. Mid-year transitions (12) made 170 orders manually recoded to the previous
  president as issuer, but in the posted data this was not done for revoking presidents, so "65 orders were coded as being
  revoked by the incorrect president"; the L&P dataset recodes them. The SI also reports 212 orders issued after election
  day in an election year coded as before it, and errors in the war indicator.
- SI-3 again: EO 12553 (Reagan, 1986) revokes "over 360" orders, about 23% of all revocations in the original data.

**Are the individual cases listed anywhere?** Not in the article, the SI, or the public Dataverse deposit (three files:
`readme.txt`, `figures.R`, `orders.Rda`; `codebook.pdf` named in the readme is absent; the public file list was checked
through the Dataverse API on 2026-11-06). The readme says replication materials for the SI and the "underlying dataset of
executive orders" are provided upon request, contact lowande@umich.edu. So the 20 missing revocations, the one false
revocation, the 8 supersessions, the 37 nullifications and the 65 misattributions are counted but not enumerated in
anything I could reach. See REQUEST_EMAIL.md.

## 3. How revocation was coded

- Outcome (pp. 354-355): whether an order is "revoked in the following presidential term", a single cross-section of
  non-ceremonial orders issued 1937 to 2020; this covers "about 1-7 years, depending on what point in the initial term
  the order was issued" (p. 355). The deposited variable is `revoked_next_term` ("EO revoked by the end of the following
  presidential term").
- Source (SI-2): formal disposition tables, not the order text. L&P follow Thrower in analysing "formal revocation" and
  leave supersession and nullification out of the outcome although the tables treat them as interchangeable with
  revocation (SI-2). The method of reading the tables (human reading or string matching) is not described; the only
  string matching the SI documents is for immutability (below).
- Why a short window (p. 355): they say it "helps reduce the influence of 'housekeeping' orders that occur decades latter
  [sic], include mass revocations, and do not represent the kind of politically-motivated reversals of interest." That
  is their reason for the design: the window reduces the weight of such revocations in their estimates. It is not a
  finding about which long-lag revocations were housekeeping.
- SI-3: EO 12553 is read as evidence for their argument: "The vast majority" of the orders it revoked "had outlived the
  function they originally performed", "alive" on paper but spent, and the White House called them "obsolete or
  inactive" (SI-3, citing an Associated Press story, 1986). Their conclusion: mass revocation was not mass policy
  reversal. This is an assertion, not a measured share.

## 4. How "immutable" and "ceremonial" are defined and coded

Immutable (pp. 352-353; SI-5 to SI-10). Coded 1 if the order's function meets any of three conditions: (1) release of
non-recoverable assets or personnel (land sales, release of classified information, extension of Native American trust
periods, temporary opening or closing of government offices); (2) physical movement or alteration of property
(construction, relocating bureaus, disposal of property); (3) designation of assets or personnel for a specific purpose
(deploying troops, designating public land, pay raises, retirement exemptions). "We code orders based on their function,
not some continuous scale." Orders that create commissions or ask for recommendations are not coded immutable because
the order is not the proximate cause of the outcome (examples EO 11237, EO 12803; EO 8578 is the positive example).
It is an indirect measure: "we cannot actually observe a policy's effects on outcomes" (p. 353); the authors assume the
function was carried out. Procedure:

- Hand coding and dictionary string matching on titles together. 63% of orders were coded "without being read by a
  human" (p. 353); SI-7 says about 63% of the 6,536 orders were coded by title matching and the other 2,429 by hand by the
  authors, blind to the date and issuing president. If dictionaries conflicted or nothing matched, no code was assigned
  (SI-7). The dictionaries (immutable n-grams, paired n-grams, mutable n-grams, paired mutable n-grams) are printed in
  SI-7 to SI-10.
- Reliability (p. 353; SI-6, SI-7): a random 200-order sample coded independently by two raters; 88.5% agreement (the
  article rounds to 89%), Cohen's kappa 0.764; confusion matrix 105 / 8 / 15 / 72 (Table B.1).
- Result: about 41% of orders are immutable (p. 353); 19 percentage points less likely under divided government (p. 353);
  Table C.2 (SI-13) gives immutable and ceremonial shares by Comparative Agendas topic.

Ceremonial. No operational rule is given beyond examples. Main text (p. 354): the non-ceremonial restriction "excludes
policies like the creation of honorifics (i.e., service awards), the closing of offices on holidays, and the renaming of
federal facilities". Temporary closing of offices is coded ceremonial and immutable together (p. 352; note 5, p. 354).
Table C.2 reports a ceremonial share by topic (SI-13). The SI does not describe a separate ceremonial coding procedure,
and the deposited codebook that would define the variable is missing. L&P say they follow "others" (p. 354), meaning
Thrower. The alignment test in this stream found that the L&P `ceremonial` counts equal Thrower's `ceremonial` counts in
every year 1937 to 2013 (README.md), consistent with the variable being carried over for those years.

## 5. Significance scores (Chiou and Rothenberg)

- Main text (p. 354): Chiou and Rothenberg (2014) rated latent significance for orders issued 1947 to 2002; "3,512 orders
  rated by Chiou and Rothenberg in our dataset" were matched, and immutable orders "tended to be more significant"
  (Figure C.1, SI-12). The point is to answer the worry that durable orders are only routine or ceremonial.
- SI-12 (Figure C.1) cites the same source as "Chiou and Rothenberg (2013)" while the main text says 2014; check the
  reference list before citing. The figure plots the density of the score for all orders and for immutable orders; the
  legend as extracted reads "Immutable (Mean: 0.10, Median: 0.05)". Read the figure itself for the values.
- The scores are not in `orders.Rda`; no variable carries them, and no EO number is in the deposit to join them.

## 6. Other points that bear on the project

- L&P give prior art for the concern behind the project's thesis, in their words about the formal record: orders can be
  alive "on paper" (p. 354, SI-3), and nothing requires an inactive order to be revoked (SI-2). They treat this as a measurement caveat,
  not as a quantity, and do not date any order's real end.
- Their model reports four columns of results (Table C.1, SI-11); my replication from `orders.Rda` reproduces column 1
  and column 3 (n, AIC and all coefficients to 3 decimals; standard errors within 0.003), see BASELINE.md.
- Survival models were set aside because they are sensitive to specification and orders are not independent: orders
  revoke other orders, and chains of amendments imply joint revocation (p. 355; SI-4).
- Case studies (from p. 357): police-equipment transfers, Guantanamo, embassy locations. Not used here.
