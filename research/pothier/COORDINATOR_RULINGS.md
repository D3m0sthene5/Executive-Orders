# Pothier coordinator rulings: one rule for every family

The doctrine authors met the same legal questions in different families. The coordinator (Pothier session, Opus)
settles each once, from the owner's standing decisions, so the eleven doctrines agree. The owner's decisions bind;
where they leave a question open, the owner told agents to work the distinction out themselves (D-20261028-evidence-decides)
and the owner still adopts or rejects each family doctrine.

## P1. Orders that only revoke, restore or relinquish

An order whose only operative content revokes another order, restores land to the public domain, or relinquishes a
reservation for disposal does one thing and does it on issue. Its command is exhausted on its effective date; its
consequence (the other order's end, the land's new status) belongs to the other order's lifecycle or the land's
history. Lead: `no`, basis `TERM`, date the order's own date (or its stated effective date), kind
`spent_on_issue`. A restoration that keeps a reversion, a retained tract, a reserved right or a purpose restriction
is not only a restoration and stays `open`.

## P2. Orders that only amend another order or rule

Under the owner's strike-and-insert ruling (D-20261021-strike-and-insert) the amended clause **continues, amended,
until the parent order ends**, and the amendment is a later event of the parent. The amending order therefore has no
command of its own after issue: its text merges into the parent (the ordinary rule for amending instruments) and
lives or ends with the parent. Lead: `no`, basis `TERM`, date the amending order's date, kind
`merged_into_parent_on_issue`, and every such lead carries the disclosure "its text continues as part of the parent
until the parent ends; the parent's lifecycle carries it". This applies only when the member's own text shows that
amending is its only operative content. If the owner prefers to treat an amending order as living as long as the
amended text lives, these leads become `open` pending the parent; the family adoption asks name this choice.

## P3. Later instruments that do not name the member

Under D-20261021-unnamed-instruments (option C) and D-20261028-evidence-decides, a later instrument ends a member
only if its words reach the member: by the member's number, or by an **express description of a class** that the
member's own text, date or authority places it in ("all Executive Orders heretofore issued under Title I", "the
rules of May 6, 1896, and all amendments thereof are revoked"). The doctrine must quote those words and the member
test. Implied displacement does not end a member: an "inconsistent herewith" clause, a whole-text restatement "to
read as follows", a lapse or repeal of the authority (FLPMA sec. 704(a) is the standing example), decontrol, or a
statute occupying the field. Such an event is recorded as a disclosed earlier candidate end, and the lead stays
`open` unless an instrument that does reach the member is held. Lead kind for express class ends:
`ended_by_express_class_instrument`.

## P4. Named persons

An order whose operative content is one act for one named person (appointment, reinstatement, transfer, retirement
or exemption, designation to act) follows PD-CS-ONE-PERSON in every family (Canal Zone appointments included).

## P5. Territories that left United States sovereignty

The end of United States sovereignty or jurisdiction over a place (Philippine independence, the Canal Zone under the
1977 treaty) ends an order only through an instrument whose words reach it (P3), and the date is the date the
instrument's terms fix. Where a statute or treaty expressly excepts a class of property from the transfer, or
lets the United States keep using it under a new instrument (bases retained by agreement), members of that class need
the instrument that disposes of the excepted property, or an upper bound that the last such instrument fixes (the
termination of the 1977 Panama Canal Treaty at noon on 1999-12-31 is the latest bound for Canal Zone orders). Families that share a place use the same instrument and date.

## P6. The member's own text as a source

A doctrine cites the member's own order text as source kind `member_text` (`"member_text": true`, no `held_path`):
the engine records the member's own held text path, sha256 and grade on every lead.
