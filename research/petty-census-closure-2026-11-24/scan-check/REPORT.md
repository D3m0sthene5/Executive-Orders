# Reading the documents behind a random sample of the missing orders (2026-11-24)

Coordinator: Claude (Opus 5.5), in the owner's Chrome through NYU's ProQuest subscription, at the owner's request.

## Conclusion

About half of the 3,941 signed ProQuest records that the census lacks are executive orders on the face of the
document. The land orders hold up: 19 of the 20 sampled land records that were read are presidential land orders or
operative orders. Most of the records sorted as "other orders" do not: only 6 of 28 are operative orders. The rest
are letters, appointments, personal actions, fund approvals, proclamations, and orders that a Secretary issued in the
President's name without his signature. Scaled by kind, the collection adds about **2,100 executive orders** to the
census: about 1,600 land orders (95% interval 1,300 to 1,700) and about 500 other orders (95% interval 230 to 890).

## Method

Fifty records were drawn at random, with seed 202611242, from the 3,941 signed records in
`../proquest-scan/CANDIDATES_MISSING.csv` (`SAMPLE_50.csv`). Each record's PDF was fetched in the browser from
ProQuest's own document link.

- **Printed and typed documents (34).** ProQuest's PDFs carry an invisible text layer made by optical character
  recognition. A script extracted it in the browser, and the text was read.
- **Handwritten and illegible documents (16).** The text layer is unreadable for these. For 14 of them, and for 4
  typed land orders whose signatures the text layer cannot show, the PDF bytes were copied into the workspace and
  their pages rendered as images and read. Two large handwritten scans (2.1 and 2.8 MB) were not copied and are not
  read.

Each document was judged on four questions:

- What kind of document it is.
- Whether it is an executive order in the census's sense, meaning a land order or an operative order.
- What presidential act appears on it.
- Whether its date matches ProQuest's date.

The results are in `RESULTS.csv`.

## Results

| Kind of document | Sampled records |
|---|---:|
| Land order | 17 |
| Operative order | 8 |
| Personal action on one person (a promotion claim, a court-martial, a pass) | 5 |
| Order signed by a Secretary "by command of the President" | 3 |
| Appointment or designation | 3 |
| Letter of instruction | 3 |
| Other letter | 3 |
| Fund approval | 2 |
| Proclamation (coinage; a treaty) | 2 |
| Pardon or clemency | 1 |
| Departmental regulation without visible presidential approval | 1 |
| Not read | 2 |

| Kind from the title rules | Read | Executive orders |
|---|---:|---:|
| Land order (L) | 20 | 19 |
| Other order (O) | 28 | 6 |

Examples of genuine orders the census lacks:

- Van Buren's authorization to move $500,000 from the Treasury to the Mint (July 20, 1838).
- Arthur's order consolidating North Carolina's revenue districts (January 2, 1885).
- Taft's Coal Land Restoration, Washington No. 6 (October 8, 1912).
- Harding's order vacating Alaskan Withdrawal No. 1 (May 19, 1921).
- Roosevelt's letter ordering the Treasury to stop applying proclaimed duties to Australian goods (June 26, 1936).

**Presidential act.** ProQuest flags every sampled record "signed by the President," but the flag means that the
document records a presidential act. It does not mean the President's signature is on the page. Three records are
Navy Department orders signed by the Secretary "by command of the President." Others carry a clerk's "approved by the
President" or a Secretary's note that the President approved. Among the 17 land orders, 9 show the President's
signature, his name or an order in his name. The other 8 show the standard order form with a signature line, but the
signature cannot be read in the text layer.

**Dates.** ProQuest's date matches the document for 44 of the 48 read records. Where it differs, ProQuest gives the
department's date rather than the President's. The Sanitary Commission order is dated June 9, 1861 by the Secretary
of War and was approved by Lincoln on June 13. The other differences are one day, or a date that is hard to read.

## Limits

- Fifty records give wide intervals, especially for the "other orders."
- Two documents are unread.
- The judgments are one reader's. A second reader, or the owner's ruling on which kinds count (Kean A-20261124-3),
  could move letters of instruction, appointments or approved fund allotments into the count.
- Navigating a browser tab to a ProQuest PDF link makes Chrome download the file, because Chrome's built-in PDF
  viewer is turned off. One file, `PT1-1838-12-25.pdf` (46 KB), was downloaded that way to the owner's computer
  before this was noticed. After that, PDFs were fetched inside the page script only.
