# Rubric: reading scanned pages to decide whether a document is an executive order

You will judge historical U.S. government documents from scanned page images. Most are handwritten, from 1789 to
1906. Read the handwriting as carefully as you can.

## Input

You get a list of documents, one per line, in this form:

`ACC|DATE|TITLE|PAGES|IMAGES`

- `ACC` is the accession number.
- `DATE` is ProQuest's date for the document.
- `TITLE` is ProQuest's title.
- `PAGES` is the number of pages in the document.
- `IMAGES` is a space-separated list of PNG files. Each file is one page: the first page of the document, and the
  last page if the document has more than one. Open each one with the Read tool.

Judge the document from what the pages show. Use the title only to understand the subject.

## kind: choose exactly one

- `land_order`: an order that withdraws, reserves, restores, vacates or sets apart public lands, islands, or a
  military, lighthouse or Indian reservation, or that changes a land office or land district.
- `operative_order`: an order, regulation or directive issued or approved by the President that governs part of the
  executive branch, the public, or a class of cases. Examples: closing or consolidating offices or districts, fixing
  rules, pay or allowances, and a general order with the President's approval written on it.
- `secretary_order`: an order or letter that a Secretary or other official signed while saying the President
  commanded it, with no signature or approval by the President himself.
- `letter_instruction`: a letter or telegram from the President giving instructions to one official about one
  matter.
- `letter_other`: any other letter, message or memorandum that orders nothing. This includes a recommendation or
  request addressed to the President when the pages show no action by him.
- `appointment`: an appointment, designation, nomination or promotion of a named person, including an acting
  secretary.
- `personal_action`: an action on one named person, such as a pass, permit, discharge, dismissal, removal,
  court-martial review, leave, release or claim.
- `pardon`: a pardon, commutation, remission, respite or stay of execution.
- `fund_approval`: an approval of an allotment, transfer, advance, payment or expenditure of money.
- `proclamation`: a proclamation, including the proclamation of a treaty.
- `treaty`: a treaty, convention or agreement text.
- `other`: anything else. Say what it is in `note`.
- `unreadable`: you cannot read enough of the pages to judge.

## presidential: choose exactly one

- `signed`: the President's signature appears on the order.
- `approved`: an approval note signed or initialed by the President appears, such as "Approved" with his name.
- `in_name`: the order is in the President's name, for example "The President directs" or "Executive Mansion",
  but no signature is visible.
- `secretary_only`: only an official signed it.
- `none_visible`: no presidential act is visible.
- `unreadable`: you cannot tell.

## Other fields

- `doc_date`: the date of the President's act as written on the pages, in YYYY-MM-DD form. Use an empty string if
  you cannot read it.
- `evidence`: up to 12 words you read on the page that support your choice of kind.
- `note`: up to 15 words, for anything a reviewer should know.

## Output

Write one JSON line per document, in input order, with the keys `acc`, `kind`, `presidential`, `doc_date`,
`evidence` and `note`. Do not skip documents.
