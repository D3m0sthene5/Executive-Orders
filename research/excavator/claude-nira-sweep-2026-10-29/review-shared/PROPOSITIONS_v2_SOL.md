# Different-family review: how NIRA code-approval executive orders ended (propositions, version 2)

You are Sol, an independent reviewer from the OpenAI GPT model family, on the GitHub repository D3m0sthene5/Executive-Orders (branch claude/schechter-nira-sweep or main once merged). A Claude producer wrote these propositions; a separate Claude reviewer has already reviewed version 1. You are the different-family check. Some propositions may be deliberately wrong. Read research/readiness/owner_rulings/2026-10-28-evidence-not-convenience.md first, then the held sources listed at the end; do not rely on these statements and do no new acquisition.

For each proposition return `upheld`, `upheld_with_correction` (exact corrected wording) or `rejected` (reason and the contradicting passage, under 25 words). Then answer: (A) is "first end June 14, 1935 by S.J. Res. 113 sec. 2, with Schechter (May 27, 1935) recorded as a validity characterization (void from issuance under then-prevailing doctrine), not an end date" the best supported answer for an order whose only operative command approves a section 3 code? If not, what is? (B) which categories must not receive this answer without separate analysis?

Write research/excavator/claude-nira-sweep-2026-10-29/review-shared/CROSS_FAMILY_REVIEW.json (reviewer "Sol / OpenAI GPT family", review_kind "independent_cross_family_source_review", propositions_sha256, verdicts, overall_A, overall_B, start_utc, end_utc) on a new branch sol/nira-shared-review and open a pull request. Do not edit any other file. Your verdicts are AI review, not human certification; the certified count stays 0.

P1. S.J. Res. 113 (Pub. Res. No. 26, 74th Cong.), printed at 49 Stat. 375 as chapter 246, was approved on
June 14, 1935. Section 1 amended NIRA section 2(c) by replacing "at the expiration of two years after the date
of enactment of this Act" with "on April 1, 1936".


P2. Section 2 of S.J. Res. 113 repealed all provisions of NIRA Title I "delegating power to the President to
approve or prescribe codes of fair competition and providing for the enforcement of such codes". The
resolution states no effective date other than its approval, so the repeal operated from June 14, 1935.


P3. Under NIRA as enacted, the legal consequences of a presidential code approval came from section 3: 3(b)
(the code's provisions become the standards of fair competition, and violations are unfair methods of
competition under the Federal Trade Commission Act), 3(c) (equity jurisdiction in the district courts to
restrain violations) and 3(f) (violations are misdemeanors). Section 3(d) let the President prescribe a code
with the same effect as an approved one.


P4. Because S.J. Res. 113 section 2 repealed the approval and enforcement provisions by name, it extinguished
the operative effect of every executive order whose only operative command approves, prescribes, amends,
modifies, stays or exempts from a section 3 code. It therefore supplies a reason (not merely a later date)
for recording June 14, 1935 as the end of such a command, unless the order ended earlier.


P5. Schechter Poultry Corp. v. United States, 295 U.S. 495, was decided May 27, 1935. The Court held the
code-making authority conferred by section 3 an unconstitutional delegation of legislative power and held
the Live Poultry Code provisions in question invalid.


P7. For codes other than the Live Poultry Code, the Schechter judgment did not itself vacate or withdraw the
approving order; its holding operated as precedent. Without a held record that the government withdrew or
suspended a given code between May 27 and June 14, 1935, June 14, 1935 is better supported than May 27, 1935
as the first end of a code approval, with May 27, 1935 stated as an earlier alternative and the view that the
approval never had valid force (an unconstitutional delegation confers no authority) stated as a further
alternative.


P8. NIRA section 5 exempted from the antitrust laws any code, agreement or license in effect under Title I,
and any action complying with it, while the title was in effect and for sixty days after. S.J. Res. 113's
proviso limited the continuing exemption to agreements and action under them that (1) put section 7(a)
requirements into effect or (2) prohibited practices unlawful under existing law. The exemption for action
already taken is an accrued effect and does not keep a code approval operative.


P9. EO 7075 (June 15, 1935) terminated the National Industrial Recovery Board and created the office of
Administrator of the National Recovery Administration; EO 7252 (December 21, 1935, effective January 1, 1936)
terminated the National Recovery Administration. Neither is the end of a code approval.


P10. The April 1, 1936 expiry of Title I ended what remained of Title I after S.J. Res. 113 (for example
section 4(a) agreement authority); it is a later event, not the end, for a code approval already repealed on
June 14, 1935.


P11. An order that only denies an application for exemption from a code (or dismisses a complaint) commands nothing after it issues; its command is exhausted on the date it is signed (or a later stated effective date). The applicant's continuing obligation is the code's own operation, which ended with the repeal, so the June 14, 1935 repeal is a later event for such an order, not its end. A stay or exception inside the same order is a separate clause with its own end.

P12. S.J. Res. 113's proviso continued every code approved before June 14, 1935 in effect, as a voluntary agreement, until Title I expired on April 1, 1936.

## Held sources (exact bytes in the repository)

- S.J. Res. 113, 49 Stat. 375: `jobs/astra-source-retention/output/pdf/98e35c567ea86208eadc55548eb7a5ea5f1edd92d8116c9e4c4847da1bab0305.pdf`; text `jobs/astra-source-retention/output/pages/98e35c567ea86208eadc55548eb7a5ea5f1edd92d8116c9e4c4847da1bab0305/d19d25fe35e98a1ade9b1fd03ed8751743502c5d1005a61ca97974657cf08386/selected-pages.txt`
- NIRA, 48 Stat. 195: `jobs/astra-source-retention/output/pdf/c9fcb1910615c2d9b677700a8fa96edc8da2cfdca204ed04f51e5f8dde99ebe7.pdf`; text `jobs/astra-source-retention/output/pages/c9fcb1910615c2d9b677700a8fa96edc8da2cfdca204ed04f51e5f8dde99ebe7/6fca72c4672ad8ad9a53ad398017a587b67e2950dd8f5bec674c7a0f3c25b446/selected-pages.txt`
- Schechter, 295 U.S. 495 (selected pages): `jobs/astra-source-retention/output/pdf/881859243da21bea9a6026dd5895230e0d8c3c4416afdbe41e50ad21eee10015.pdf`; text `jobs/astra-source-retention/output/pages/881859243da21bea9a6026dd5895230e0d8c3c4416afdbe41e50ad21eee10015/ad2b3136c546eeb5f588d031acb575049be56b5341b922af2fe2e152787e4fa2/selected-pages.txt`
- EO 7075 and EO 7252 (APP transcriptions): `jobs/app-executive-orders/output/texts/executive-order-7075-reorganizing-the-nra.txt`, `jobs/app-executive-orders/output/texts/executive-order-7252-terminating-the-national-recovery-administration-and-transferring.txt`
