# Rubric: is this ProQuest document an executive order?

Each input line is one JSON object with these fields:

- `acc`: the CIS accession number.
- `date`: ProQuest's date for the document.
- `title`: ProQuest's title.
- `pages`: the number of pages.
- `text`: the document's own words as read by optical character recognition (OCR). The OCR text has errors, and
  long documents are cut in the middle at "[...]".

Judge the document from `text`. Use `title` only to understand what the text is about.

## kind: choose exactly one

- `land_order`: an order that withdraws, reserves, restores, vacates, modifies or sets apart public lands or
  islands. This includes power-site, coal, petroleum, phosphate, potash, public-water and reservoir withdrawals and
  restorations, lighthouse and military reservations, Indian reservation boundaries, and land offices and districts.
  The text must contain the order itself, for example "it is hereby ordered", "is hereby withdrawn", "Order of
  Restoration" or "the following lands are reserved". It may sit inside a file with the transmittal letters.
- `operative_order`: an order, regulation, rule or directive issued by the President or approved by him that
  governs the executive branch, the public or a class of cases.
  - Examples: establishing a commission, consolidating revenue districts, prescribing regulations, closing offices,
    fixing pay or allowances, and a general order approved by the President.
  - A letter from the President that directs a department to take a general action counts here only if it is
    written as an order, for example "it is hereby ordered" or "I hereby direct", or if it was published as an order.
- `secretary_order`: an order or letter that a Secretary or other official signed while saying the President
  commanded it ("by command of the President", "it is the order of the President"), with no signature or approval by
  the President himself on the document.
- `letter_instruction`: a letter or telegram from the President giving instructions to one official about one
  matter.
- `letter_other`: any other letter, message or memorandum, from or to the President, that orders nothing. This
  includes a recommendation or request addressed to the President when the document shows no presidential action on
  it.
- `appointment`: an appointment, designation, nomination or promotion of a named person, including an acting
  secretary.
- `personal_action`: an action on one named person, such as a pass, permit, discharge, dismissal, a court-martial
  review, leave, release, or a claim.
- `pardon`: a pardon, commutation, remission, respite or stay of execution.
- `fund_approval`: an approval of an allotment, transfer, advance, payment or expenditure of money.
- `proclamation`: a proclamation, including the proclamation of a treaty.
- `treaty`: a treaty, convention or agreement text.
- `other`: anything else. Say what it is in `note`.
- `illegible`: the OCR text is too garbled to judge.

## presidential: choose exactly one

- `signed`: the President's signature or name appears under the order. The text may show "(Signed)", "Sgd." or a
  typed name.
- `approved`: there is an approval note such as "Approved: [President]" or "The within action is approved.
  [President]".
- `in_name`: the order is issued in the President's name or from the Executive Mansion or White House, but no
  signature is visible. A signature line reading only "President" with no name counts here.
- `secretary_only`: only an official signed it.
- `none_visible`: no presidential act is visible.
- `illegible`: the text is too garbled to tell.

## Other fields

- `doc_date`: the date of the President's act as the text gives it, in YYYY-MM-DD form. If there is none, give the
  date of the main document. If the text shows no date, use an empty string.
- `evidence`: up to 12 words copied from the text that support your choice of kind.
- `note`: up to 15 words. Mention it here if the main document is only a recommendation or a draft and the order
  itself is not in the text.

## Output

Return exactly one line of JSON for each input, in the input's order, with these keys: `acc`, `kind`,
`presidential`, `doc_date`, `evidence`, `note`. Do not skip any input and do not add commentary.
