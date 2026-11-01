# Geddes source-content repair evidence

`CHECK.json` compares the exact 40 Apollo rejected claim versions (all 40
canonical claim hashes match the review inventory) and all 254 filed Apollo
claims against their batch's pinned dossier and hash-verified held text. The
new check alone flags 11 rejected versions and 16 filed versions. Ten of the
rejected flags align with the source-content defects examined here; the EO
6876 recommendation-line flag is additional and is not counted as a caught
review defect. This is a development-set source comparison, not a new legal
review or a whole-pipeline recall/precision measurement.

The repaired source check uses `segment.locate_order` and clause containment
for Federal Register page text, and requires an individually identified APP
node, a matching publisher INDEX URL/title/date/instrument row and an order
signature date for an unheaded APP item. The APP URL slug need not repeat the
full order suffix. It validates `claim_kit.inventory_overrides` with the existing
`assemble.derive_inventory` before deciding which clause spans belong to the
target. A page's neighboring order never supplies a target concept. It
includes actual recitals in a proven whole-order body. Coverage gaps decreased
from 81 to 10 and then to four after recognizing publisher slug and signature
date variants. The remaining EO 12176 and 12189 FR text layers have no
locatable order heading; the EO 6206A and 6964B APP items include appended
material past the order signature or no terminal signature. These remain
coverage gaps, not absence flags. It rehashes source and APP index bytes even
when a caller passes a cache. `INITIAL_CHECK.json` and `INTERIM_CHECK.json`
preserve the earlier comparisons.

The 16 filed source flags need independent substantive review. Five APP
claims assert an `Approval recommended` line absent from their identified
items; eleven others quote recommendation lines that are absent verbatim from
their held text. Quotation checks normalize whitespace only, preserving
case and punctuation. A filed claim is not assumed to be correct solely
because it was filed, and these flags must not be automatically labeled false
positives. Earlier preliminary flags against OCR-damaged section 10 standstill
clauses and later board-report hearing accounts were removed after inspection
of the bounded source and the claim's attribution. Original operative text,
first-ending sources and later-event citations are checked against their own
hash-verified exact spans; a bad source hash or span is a coverage gap.

No source acquisition, canonical claim edit, review verdict edit or status
promotion is made here. The prospective UTC and monotonic clock readings,
the exact paths/hashes, and the unknown token/model telemetry are recorded in
`CHECK.json`.
