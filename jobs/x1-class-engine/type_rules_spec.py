"""Content of the X1 type rule book (one rule per repetitive pre-1937 type).

build_type_rules.py writes each rule to research/readiness/type-rules/<rule_id>.json
in the family-rule vocabulary (mechanism, effective_date_basis, exceptions_savings,
quoted_clause, source, scope, review_state, legal_effect), adding an exemplar
order's exact operative text from a held copy. The legal text below is a research
pattern written by Claude on 2026-10-19 for agents to test against each order;
it is not a finding about any order, and every rule is reviewed independently
before use (research/production/x1-2026-10-19/TYPE_RULES_REVIEW.json).
"""

COMMON_OUTLIERS = [
    "The order's own text (not only the WPA summary or APP title) does not match the type, or the held text is another order's.",
    "The order does more than the type's single act (a second operative clause of another kind).",
    "A later order or statute amends, extends, revokes or revives it before the candidate end.",
    "The order states its own effective date, duration, condition or termination that differs from the pattern.",
]

RULES = {
    "TR-CS-WAIVER": {
        "types": ["cs_waiver_individual"], "mechanism": "exhausted_on_performance",
        "title": "One-person civil-service waiver or eligibility order",
        "ending_pattern": "The order authorizes one action for named persons (appointment, reinstatement, transfer, retention or examination without regard to a civil-service rule). Its operative command is spent when the authorized action is taken, or lapses if never used. The resulting appointment survives as an accrued effect of the action, not of the order.",
        "effective_date_basis": "The date the authorized personnel action was taken, from an agency record or the Civil Service Commission annual report; if no record is held, the end date is unresolved and must be stated as a gap (a not-later-than bound is not an exact first end).",
        "savings": "The appointment or status conferred is an accrued effect that continues independently of the order (state transferred_or_accrued). Later service rights flow from civil-service statutes, not from the order.",
        "required_evidence": ["The order's own text naming the person and the rule waived.", "A record of the personnel action and its date (CSC annual report, agency register) or an explicit gap.", "A bounded later-law search for a revival or amendment naming the order."],
        "outliers": ["The order amends a Civil Service Rule or schedule for a class of positions (type cs_rules_amendment).", "The order names a class of persons or positions rather than individuals.", "The authority is continuing (for example 'may be appointed at any time')."],
    },
    "TR-RETIREMENT-EXEMPTION": {
        "types": ["retirement_exemption"], "mechanism": "own_terms_expiry_or_separation",
        "title": "Individual exemption from compulsory retirement",
        "ending_pattern": "The order exempts one named employee from the compulsory retirement provisions, usually until a stated date. It ends on that stated date, or earlier when the employee separates or dies; a later order may extend it.",
        "effective_date_basis": "The 'until' date in the order's own text; if none is stated, the employee's separation date from an agency record, otherwise a stated gap.",
        "savings": "Service performed under the exemption and resulting annuity rights are accrued effects (state transferred_or_accrued).",
        "required_evidence": ["The order's text with the exemption period.", "A search for later orders extending the same person's exemption (they are often serial).", "The separation date if the order states no end."],
        "outliers": ["An extension order exists (the later order, not this one, carries the end).", "No end date is stated and no separation record is held."],
    },
    "TR-FUND-ALLOTMENT": {
        "types": ["fund_allotment"], "mechanism": "exhausted_on_performance",
        "title": "Allocation, allotment or transfer of appropriated funds",
        "ending_pattern": "The order allocates or transfers a sum from an appropriation to an agency for a purpose. It is spent when the funds are obligated and expended, or lapses with the appropriation's period of availability.",
        "effective_date_basis": "The end of the appropriation's period of availability stated in the appropriation act, or the date of a later order rescinding the allocation; otherwise a stated gap.",
        "savings": "Obligations and expenditures made under the allocation are accrued effects.",
        "required_evidence": ["The order's text with amount, appropriation and purpose.", "The appropriation act's availability period (shared source via FETCH_QUEUE).", "A search for later orders amending or rescinding the allocation."],
        "outliers": ["The order creates a continuing program, agency or rule, not only a transfer of money.", "The appropriation is 'available until expended' with no end."],
    },
    "TR-CLOSING-MOURNING": {
        "types": ["closing_mourning"], "mechanism": "own_terms_expiry",
        "title": "Closing of offices, holiday, early dismissal, mourning or half-staff display",
        "ending_pattern": "The order closes offices or excuses employees on a stated day, or orders mourning or half-staff display for a stated period. It ends at the close of that day or period by its own terms.",
        "effective_date_basis": "The last day of the stated closing or mourning period in the order's own text.",
        "savings": "None ordinarily (state none_after_bounded_search) unless pay or leave was granted, which is an accrued effect.",
        "required_evidence": ["The order's text with the day or period."],
        "outliers": ["The order sets a recurring holiday or a standing rule (for example every Saturday afternoon).", "No day or period is stated."],
    },
    "TR-TAX-RETURN-INSPECTION": {
        "types": ["tax_return_inspection"], "mechanism": "exhausted_on_performance_or_own_terms",
        "title": "Tax returns opened to inspection by a committee or official",
        "ending_pattern": "The order opens returns to inspection by a named committee or official for an investigation. It ends when the inspection or the investigating body's authority ends, or on a date in its own text.",
        "effective_date_basis": "The date in the order, or the end of the committee's authorizing resolution or Congress; otherwise a stated gap.",
        "savings": "Information already inspected is an accrued effect.",
        "required_evidence": ["The order's text naming the body and returns.", "The committee's authorizing resolution or term (shared source)."],
        "outliers": ["The order prescribes general regulations for inspection rather than a single grant."],
    },
    "TR-ALIEN-PROPERTY-SALE": {
        "types": ["alien_property_sale"], "mechanism": "exhausted_on_performance",
        "title": "Alien Property Custodian authorized to sell, reject bids or resell specified property",
        "ending_pattern": "The order authorizes one disposition of specified property seized under the Trading with the Enemy Act. It is spent when the sale or disposition is completed.",
        "effective_date_basis": "The date of sale from the Custodian's reports; otherwise a stated gap.",
        "savings": "The transfer of title is an accrued effect; claims under later settlement acts are independent.",
        "required_evidence": ["The order's text naming the property.", "The Custodian's report of the sale or an explicit gap."],
        "outliers": ["The order prescribes general rules for the Custodian.", "Not mapped to the 1921 war-end resolution: the Trading with the Enemy Act is reported to be excepted from it."],
    },
    "TR-EIGHT-HOUR-SUSPENSION": {
        "types": ["labor_hours_suspension"], "mechanism": "exhausted_on_performance_or_own_terms",
        "title": "Eight-hour law suspended for specified work or contracts",
        "ending_pattern": "The order suspends the eight-hour law for named work or contracts. It ends when that work is completed, at a date in the order, or with the emergency it relies on.",
        "effective_date_basis": "The completion or stated date; for wartime suspensions check the 1921 war-end resolution (X1-E1) as a candidate.",
        "savings": "Work already performed is an accrued effect.",
        "required_evidence": ["The order's text with the work or contracts covered."],
        "outliers": ["The suspension is general, for all contracts of an agency without limit."],
    },
    "TR-PROPERTY-TRANSFER": {
        "types": ["property_transfer"], "mechanism": "exhausted_on_performance",
        "title": "Transfer of a vessel, records or equipment between agencies",
        "ending_pattern": "The order transfers specified property from one agency to another. It is spent on delivery; custody thereafter rests on the transfer, an accrued effect.",
        "effective_date_basis": "The delivery date from agency records, or the order's date if it effects the transfer itself; otherwise a stated gap.",
        "savings": "The receiving agency's custody is an accrued effect (state transferred_or_accrued).",
        "required_evidence": ["The order's text naming the property and agencies."],
        "outliers": ["The property is land (land types).", "The order transfers functions or personnel (organization)."],
    },
    "TR-OWN-TERMS-EXPIRY": {
        "types": ["own_terms_expiry"], "mechanism": "own_terms_expiry",
        "title": "Extension or continuation until a stated date",
        "ending_pattern": "The order continues a body or extends a time limit or effective date until a stated date. It ends on that date, unless a later order extends it again (serial extensions are common: each order ends when superseded by the next or on its own date, whichever is earlier).",
        "effective_date_basis": "The 'until' date in the order's text, or the date of the next extension order if earlier.",
        "savings": "Acts done under the extension are accrued effects.",
        "required_evidence": ["The order's text with the date.", "The next order in the series, if any."],
        "outliers": ["'Until further order' or no date."],
    },
    "TR-WATER-RESERVE": {
        "types": ["public_water_reserve"], "mechanism": "standing_until_revoked",
        "title": "Public water reserve (springs and water holes)",
        "ending_pattern": "Land withdrawal: continues in force until revoked or modified by a later order, Public Land Order or statute. Restoration orders ('Public Water Restoration No. ...') diminish it for described lands. Many reserves of this kind (for example under the order of April 17, 1926) are reported to remain in force.",
        "effective_date_basis": "For an end: the effective date of the revoking instrument for the lands described. For a continuing reserve: a current basis checked through 2026-10-14.",
        "savings": "Valid existing rights at the time of the withdrawal; later revocations usually restore lands subject to valid existing rights.",
        "required_evidence": ["The order's text with the lands described.", "Later restorations and Public Land Orders naming the reserve number (X2).", "A current-law search (FLPMA repealed the authority prospectively; existing withdrawals are reported to continue)."],
        "outliers": ["Partial revocations leave the rest in force: every described tract needs its own state."],
    },
    "TR-POWER-SITE": {
        "types": ["power_site_reserve"], "mechanism": "standing_until_revoked",
        "title": "Power site or reservoir site reserve",
        "ending_pattern": "Land withdrawal for water-power purposes: continues until revoked, modified or vacated by a later order, Public Land Order or Federal Power Commission action. Restoration orders diminish it.",
        "effective_date_basis": "Effective date of the revoking instrument per tract; or a current basis through 2026-10-14.",
        "savings": "Valid existing rights; licences issued under the Federal Power Act.",
        "required_evidence": ["The order's text and reserve number.", "Later restorations or PLOs naming the reserve (X2)."],
        "outliers": ["The order itself is a restoration (it ends a part of another order rather than creating a reserve)."],
    },
    "TR-STOCK-DRIVEWAY": {
        "types": ["stock_driveway"], "mechanism": "standing_until_revoked",
        "title": "Stock driveway withdrawal",
        "ending_pattern": "Land withdrawal for stock driveways: continues until revoked or modified by a later order or PLO.",
        "effective_date_basis": "Effective date of the revoking instrument, or a current basis.",
        "savings": "Valid existing rights.",
        "required_evidence": ["The order's text.", "Later revocations or PLOs (X2)."],
        "outliers": ["The order revokes a driveway (it ends another order)."],
    },
    "TR-BIRD-REFUGE": {
        "types": ["bird_refuge"], "mechanism": "standing_until_revoked",
        "title": "Bird reservation or wildlife refuge established, enlarged or diminished",
        "ending_pattern": "Reservation for birds or wildlife: continues until revoked; many became units of the National Wildlife Refuge System and may still be in force (a YES needing a current basis). Enlargements and diminutions change the area, not the reservation's existence.",
        "effective_date_basis": "A current basis checked through 2026-10-14 (refuge system records, later orders or PLOs), or the revoking instrument's date.",
        "savings": "Later statutes (for example the National Wildlife Refuge System Administration Act of 1966) may continue the area independently.",
        "required_evidence": ["The order's text and refuge name.", "Current refuge records or later instruments naming it."],
        "outliers": ["Withdrawal 'for classification' pending a refuge decision (temporary, ends on classification)."],
    },
    "TR-LIGHTHOUSE": {
        "types": ["lighthouse_reservation"], "mechanism": "standing_until_revoked_or_disposed",
        "title": "Lighthouse reservation",
        "ending_pattern": "Land reserved for lighthouse purposes: continues until revoked, transferred or disposed of as surplus; many stations were later transferred to the Coast Guard (1939) or disposed of.",
        "effective_date_basis": "Effective date of the revoking or disposing instrument, or a current basis.",
        "savings": "Transfers of jurisdiction carry the reservation forward rather than ending it.",
        "required_evidence": ["The order's text.", "Later disposals, PLOs or transfers naming the station."],
        "outliers": ["The order transfers a military reservation for lighthouse use (two orders' lifecycles)."],
    },
    "TR-NATIONAL-FOREST": {
        "types": ["national_forest_boundary"], "mechanism": "boundary_change_merged",
        "title": "National forest boundary change, administrative site or ranger station",
        "ending_pattern": "Boundary changes are usually effective on signing and then merged into the forest's current boundary; later proclamations and orders may move the boundary again. An administrative-site reservation continues until revoked.",
        "effective_date_basis": "For a boundary change: whether it remains part of the current boundary description, or the date of the later instrument that changed the same lands.",
        "savings": "Lands restored to entry are subject to valid existing rights.",
        "required_evidence": ["The order's text with the lands described.", "Later boundary instruments for the same forest."],
        "outliers": ["The order also creates a reservation for another agency.", "The order is a proclamation in form (check the form)."],
    },
    "TR-MINERAL-WITHDRAWAL": {
        "types": ["mineral_withdrawal"], "mechanism": "standing_until_revoked",
        "title": "Petroleum, coal, phosphate, potash, oil shale or helium withdrawal or restoration",
        "ending_pattern": "Mineral withdrawals continue until revoked, modified or superseded by statute (the Mineral Leasing Act of 1920 changed disposal of these minerals but did not by itself revoke withdrawals). Restoration orders end parts of earlier withdrawals.",
        "effective_date_basis": "Effective date of the revoking instrument per tract; or a current basis.",
        "savings": "Valid existing rights and leases.",
        "required_evidence": ["The order's text and withdrawal name or number.", "Later restorations or PLOs (X2)."],
        "outliers": ["Naval petroleum reserves, later governed by statute (independent basis)."],
    },
    "TR-MILITARY-RESERVATION": {
        "types": ["military_naval_reservation"], "mechanism": "standing_until_revoked_or_disposed",
        "title": "Military or naval reservation established, enlarged, diminished or transferred",
        "ending_pattern": "Continues until revoked, transferred or disposed of (often under surplus property acts). Diminutions restore part of the lands; transfers to another department change jurisdiction rather than end the reservation.",
        "effective_date_basis": "Effective date of the revoking or disposing instrument, or a current basis.",
        "savings": "Transfers and disposals carry valid existing rights.",
        "required_evidence": ["The order's text.", "Later orders, PLOs or disposal records naming the reservation."],
        "outliers": ["Reservations in the Philippines or Canal Zone (also mapped to X1-E3 or X1-E4)."],
    },
    "TR-INDIAN-RESERVATION": {
        "types": ["indian_reservation_trust"], "mechanism": "own_terms_or_standing",
        "title": "Indian reservation boundary or trust-period extension",
        "ending_pattern": "Trust-period extensions run for a stated number of years and were made indefinite by section 2 of the Indian Reorganization Act of June 18, 1934 for reservations covered by it; each extension order is superseded by the next or by that Act. Reservation boundary orders continue until changed by statute or order.",
        "effective_date_basis": "For trust extensions: the end of the stated period or the earlier superseding instrument. For boundaries: a current basis or the changing instrument.",
        "savings": "Allotments and trust title are accrued and statutory effects.",
        "required_evidence": ["The order's text.", "The Indian Reorganization Act (48 Stat. 984) as a shared source, and later extension orders for the same tribe."],
        "outliers": ["The order affects lands of a national forest or other reservation as well (two lifecycles)."],
    },
    "TR-LAND-WITHDRAWAL": {
        "types": ["land_withdrawal_general"], "mechanism": "standing_until_revoked",
        "title": "General land withdrawal, reservation or restoration (resurvey, classification, townsite, cemetery, administrative use)",
        "ending_pattern": "A withdrawal continues until revoked or modified. Temporary withdrawals 'pending resurvey' or 'for classification' end when the purpose is completed and the order is revoked; the revoking instrument, not the purpose, usually supplies the exact date. Restoration orders end parts of earlier withdrawals.",
        "effective_date_basis": "Effective date of the revoking instrument per tract, or a current basis.",
        "savings": "Valid existing rights.",
        "required_evidence": ["The order's text with the lands.", "Later revocations or PLOs (X2) naming the order by date or number."],
        "outliers": ["The order itself revokes or modifies another order (its lifecycle is spent on issue, and it is evidence for the other order's end)."],
    },
    "TR-NRA-CODE": {
        "types": ["nra_code_approval"], "mechanism": "event_swept",
        "title": "Approval of a code of fair competition or NRA agreement",
        "ending_pattern": "Candidate end: the code-making authority under NIRA Title I fell with Schechter (May 27, 1935) and the Title's expiry (June 16, 1935, as extended in skeleton form to April 1, 1936). See event X1-E2. The agent decides the date per order.",
        "effective_date_basis": "Event X1-E2's sources once held; or an earlier end (an amended or superseding code order).",
        "savings": "Penalties already incurred and actions taken are accrued effects; later statutes (for example the Bituminous Coal Act) are independent.",
        "required_evidence": ["The order's text.", "X1-E2 sources held with phrases found.", "Later amending orders for the same code."],
        "outliers": ["Administrative orders on NRA boards and personnel (not code approvals)."],
    },
    "TR-CANAL-ZONE": {
        "types": ["canal_zone"], "mechanism": "event_swept",
        "title": "Canal Zone government, regulation or personnel order",
        "ending_pattern": "Candidate end: the Canal Zone ceased on October 1, 1979 (event X1-E3), but most orders ended earlier by supersession, by the Canal Zone Code, or on their own terms. The earliest end controls.",
        "effective_date_basis": "The earliest of: a superseding order, the codifying statute, the order's own terms, X1-E3.",
        "savings": "Functions continued by the Panama Canal Commission after 1979 are savings, not ends.",
        "required_evidence": ["The order's text.", "Later orders on the same subject (Panama Canal Record).", "X1-E3 source."],
        "outliers": ["One-person appointments (spent on issue rather than swept)."],
    },
    "TR-PHILIPPINES": {
        "types": ["philippines"], "mechanism": "event_swept",
        "title": "Order concerning the Philippine Islands",
        "ending_pattern": "Candidate end: Philippine independence on July 4, 1946 (event X1-E4); some ended with the 1935 Commonwealth, and reservations retained under the 1947 bases agreement did not end in 1946.",
        "effective_date_basis": "The earliest of: own terms, a superseding order, the Commonwealth transition, X1-E4.",
        "savings": "Retained military reservations; property rights.",
        "required_evidence": ["The order's text.", "X1-E4 sources."],
        "outliers": ["Orders whose Philippine mention is incidental (for example a civil-service schedule covering many places)."],
    },
    "TR-WWI-EMERGENCY": {
        "types": ["wwi_emergency"], "mechanism": "event_swept",
        "title": "First World War emergency measure",
        "ending_pattern": "Candidate end: the joint resolution of March 3, 1921 (event X1-E1) for orders under the Acts it names; many ended earlier with demobilization or by revocation, and Trading with the Enemy Act orders are excepted.",
        "effective_date_basis": "The earliest of: own terms, revocation, X1-E1 when the order's authority is among those named.",
        "savings": "Contracts, claims and property transfers made during the war are accrued effects.",
        "required_evidence": ["The order's text and the statute it relies on.", "X1-E1 source with the named Acts."],
        "outliers": ["Orders under statutes not named in the resolution.", "Orders under the Trading with the Enemy Act."],
    },
}

# Round 2 (2026-10-19): changes required by the independent review in
# research/production/x1-2026-10-19/TYPE_RULES_REVIEW_R1.json. Rules not listed
# here (TR-CLOSING-MOURNING, TR-WATER-RESERVE) were approved and stay frozen.
REVISIONS = {'TR-CS-WAIVER': {'ending_pattern': 'The order authorizes one action for named persons (appointment, reinstatement, transfer, retention or examination without regard to a civil-service rule). Its operative command is spent when the authorized action is taken. If no use is recorded and the order states no time limit, the end is unresolved and must be stated as a gap (no source-backed lapse date exists). The resulting appointment survives as an accrued effect of the action, not of the order.', 'outliers_add': ['The waiver is conditional (for example on a noncompetitive examination or probation) or limited to a stated position or period.', 'The person is named again in a later waiver order (serial orders): read both.', 'A later general revocation or replacement of the Civil Service Rules and the orders under them: check it as a candidate express end.', "The held text is printed in a Civil Service Commission annual report, so the report's commentary or neighbouring orders can bleed into the slice."], 'exemplar': {'id': 'EO:1905', 'parts': [('Mr. Paul F. Myers, of Princeton', 'in Washington, D. C.')]}}, 'TR-RETIREMENT-EXEMPTION': {'ending_pattern': "The order exempts one named employee from the compulsory retirement provisions. Some exemptions run until a stated date and end on it; many are open-ended (the exemplar states no period), and then the end depends on the employee's separation or death, or on a change in the governing retirement statute. A later order may extend a dated exemption.", 'effective_date_basis': "The 'until' date in the order's own text when there is one; otherwise the separation or death date from an agency or Civil Service Commission record, or the date the governing statute changed; otherwise a stated gap.", 'required_evidence_add': ["The employee's separation or death date (agency or CSC record) or an explicit gap."], 'outliers_add': ['The exemption is open-ended (no stated period), as in the exemplar.', "The governing retirement statute was amended or repealed (later Civil Service Retirement Act amendments; the statutory abolition of mandatory federal retirement in 1978): the order's authority may lapse before separation."], 'exemplar': {'id': 'EO:5912', 'parts': [('By virtue of the authority vested in me by section 204', 'who has reached the retirement age prescribed for auto-'), ('matic separation from the service, is hereby exempted', 'from the provisions of that\nsection.')]}}, 'TR-FUND-ALLOTMENT': {'effective_date_basis': "The expenditure date is normally unavailable. The end of the appropriation's period of availability (from the appropriation act, fetched for each order) is only a not-later-than bound for the operative command, never an exact first end; obligated balances can still be paid after it (an accrued effect). A later order rescinding the allocation supplies an exact date; otherwise a stated gap.", 'outliers_add': ["The order only amends or modifies another order: its own operative effect merges into, and normally ends with, the parent order; read the parent's text and lifecycle. (The exemplar EO 6265 amends EO 6208, which made the allocation.)", 'A later statute or order rescinds, impounds or re-appropriates the unobligated balance.'], 'note': "The exemplar's authority is the Emergency Conservation Work act of March 31, 1933 (48 Stat. 22); each order's own appropriation must be fetched."}, 'TR-TAX-RETURN-INSPECTION': {'ending_pattern': "The order opens returns to inspection by a named committee or official for an investigation, under a specific Revenue Act section. It ends when the inspection or the investigating body's authority ends, or on a date in its own text; standing orders for a class of officials (for example State officers) are outliers.", 'required_evidence_add': ['The Revenue Act section the order relies on, and its later replacements.'], 'outliers_add': ['A standing class order (State officers, all years) rather than a single committee grant.', "The committee's authority was renewed in a later Congress, which extends the inspection.", 'Statutory replacement of the authority (IRC 1939 s.55; IRC 1954 s.6103; the Tax Reform Act of 1976 rewrite of s.6103): candidate authority-lapse ends, not presumed ends.'], 'exemplar': {'id': 'EO:6742', 'parts': [('By virtue of the authority vested in me by section 257 (a)', 'as further amended this date.')]}}, 'TR-ALIEN-PROPERTY-SALE': {'ending_pattern': 'The order authorizes one disposition of specified property seized under the Trading with the Enemy Act: a sale order is spent when the sale is completed; a rejection-of-bids order is spent when issued; a resale order is spent on the resale.', 'effective_date_basis': "The order's own date is its effective date. The date of sale is a separate end date, from the Custodian's reports; if no report is held the end is an explicit gap, and the order date or a report year is only a not-earlier or not-later bound.", 'savings': 'Title passed to the buyer is an accrued effect (state transferred_or_accrued). The proceeds stayed subject to the Settlement of War Claims Act of 1928 (the exemplar itself says so); treat that as a lead to check, not as independent of the order.', 'outliers_add': ['The authorized sale never took place, was cancelled, or was made at a different price or to a different buyer.', 'The property was returned to the claimant under the 1928 Act instead of being sold.', 'One order covers several properties sold on different dates: each needs its own end.']}, 'TR-EIGHT-HOUR-SUSPENSION': {'ending_pattern': 'The order suspends the eight-hour law for named work or contracts under a national-emergency suspension proviso (for the exemplar, the naval appropriation act of March 4, 1917). It ends when that work is completed, on a date in the order, or when the suspension authority itself ends. Whether the 1921 joint resolution (X1-E1) reaches a given authority must be shown: it reaches only provisions contingent on the war or the existing emergency.', 'effective_date_basis': 'The completion date of the work or contract, or a stated date; or the end of the suspension authority if shown to be war-contingent; otherwise a stated gap.', 'required_evidence_add': ['The suspension authority (statute and section) and whether its terms depend on the war or emergency.'], 'outliers_add': ['Peacetime suspensions (public works, Panama Canal, 1930s emergency orders) that the 1921 resolution cannot reach.', 'The work or contract was never completed, or was modified or extended.'], 'exemplar': {'id': 'EO:2656', 'parts': [('I do hereby suspend the provisions of law', 'This order shall take effect from and after this date.')]}}, 'TR-PROPERTY-TRANSFER': {'effective_date_basis': 'A stated effective date in the order, if any, over the signature date; then the delivery date from agency records if the order only directs a transfer; otherwise a stated gap.', 'outliers_add': ["Transfers 'for temporary use', with reversion or 'for the duration' terms: the property returns, so the order is not spent on delivery.", 'Vessels later re-transferred or sold: a chain of instruments is needed.', 'The order also transfers functions, offices or personnel (organization type).'], 'exemplar': {'id': 'EO:206', 'parts': [('The historical archives in the Department of State, known as the Revolutionary archives', 'hereby ordered to be transferred from the Department of State')]}}, 'TR-OWN-TERMS-EXPIRY': {'ending_pattern': "The order continues a body or extends a time limit or effective date until a stated or computable date. It ends on that date unless extended or replaced by a later order issued before expiry (which amends the date; it is not a revocation). When a deferral order expires, the deferred measure takes effect or is deferred again: that is the other order's event, not an end of this order's subject.", 'effective_date_basis': "The 'until' date in the order's text; for an event-relative date (the exemplar: sixty days after the convening of the second session of the 73rd Congress) the agent computes it from a cited source for the event and states the computation; or the date of the next extension if earlier.", 'outliers_add': ['Event-relative or contingent dates (the exemplar).', 'The deferred measure was later rescinded, so the deferral never matured.', "'Until further order' or no date."]}, 'TR-POWER-SITE': {'ending_pattern': 'Land withdrawal for water-power or reservoir purposes: continues until revoked, modified or vacated by a later order or Public Land Order, and, for lands reserved for power purposes, until otherwise directed by the Federal Power Commission or Congress (Federal Power Act s.24, 16 U.S.C. 818). Restoration orders diminish it.', 'savings': 'Valid existing rights; licences under the Federal Power Act. Federal Power Act s.24 is an independent statutory basis and limits what counts as an end (restoration needs a Commission determination and may reserve a right of re-entry). FLPMA (Pub. L. 94-579, Oct. 21, 1976) s.704(a) repealed the Pickett Act and implied withdrawal authority prospectively; s.701 saves existing withdrawals until modified under FLPMA or other law (IBLA, Grant L. Hacking, 1980). This is a continuity point, never an end; the s.204(l) review of withdrawals is a review lead, not an end.', 'outliers_add': ['Lands reserved automatically under FPA s.24 by a filed application, with no executive order.', 'Restoration subject to FPA s.24 conditions.', 'The order itself is a restoration (it ends part of another order rather than creating a reserve).'], 'exemplar': {'id': 'EO:6205', 'parts': [('Under and pursuant to the provisions of the act of Congress approved June 25,', 'reserved for reservoir sites:')]}}, 'TR-STOCK-DRIVEWAY': 'WITHDRAWN', 'TR-BIRD-REFUGE': {'savings': 'Later statutes (for example the National Wildlife Refuge System Administration Act of 1966) may continue the area independently. Transfer of the administering bureau (Biological Survey to Interior, Reorganization Plan No. II of 1939) and renaming (redesignation as National Wildlife Refuges in 1940; verify) are continuities, not ends.', 'outliers_replace': ["Lands acquired by purchase under the Migratory Bird Conservation Act ('acquired or to be acquired', as in the exemplar) are not public-domain withdrawals: their federal status rests on title, not on the order.", 'The refuge was later re-established, consolidated or absorbed under another name or statute (the order is superseded, the area continues).', 'The area was transferred to a state or another agency by statute or exchange.'], 'exemplar': {'id': 'EO:7292', 'parts': [('it is ordered that the following-described lands', 'as a refuge and breeding ground for migratory birds and other wildlife:')]}}, 'TR-LIGHTHOUSE': {'ending_pattern': 'Land reserved for lighthouse purposes: continues until revoked, transferred or disposed of as surplus. The consolidation of the Bureau of Lighthouses into the Coast Guard (Reorganization Plan No. II of 1939, s.2(a), effective July 1, 1939) is a continuity, not an end.', 'savings': 'Transfers of jurisdiction carry the reservation forward. FLPMA (Pub. L. 94-579, Oct. 21, 1976) s.704(a) repealed the Pickett Act and implied withdrawal authority prospectively; s.701 saves existing withdrawals until modified under FLPMA or other law (IBLA, Grant L. Hacking, 1980). This is a continuity point, never an end; the s.204(l) review of withdrawals is a review lead, not an end.', 'outliers_add': ["The order only amends or modifies another order: its own operative effect merges into, and normally ends with, the parent order; read the parent's text and lifecycle. (The exemplar EO 5458 amends the description in EO 4410.)", 'The station was disposed of under surplus-property or lighthouse-preservation statutes, or conveyed to a state or nonprofit: the deed date is the end, with reversionary clauses as residuals.', 'Alaska statehood or other statutory transfers of the site.']}, 'TR-NATIONAL-FOREST': {'outliers_add': ['Eliminations or additions in Oregon, Washington, Idaho, Montana, Colorado and Wyoming after March 4, 1907 (34 Stat. 1271 bars creating or enlarging national forests there except by Act of Congress): an authority question to flag.', 'The forest was renamed or consolidated: the boundary continues under another name.', 'Eliminated lands were later re-added by a later proclamation.'], 'exemplar': {'id': 'EO:1260', 'parts': [('Under authority of the act of Congress of June 4, 1897', 'not chiefly valuable for national-forest purposes:')]}}, 'TR-MINERAL-WITHDRAWAL': {'ending_pattern': 'Mineral withdrawals continue until revoked, modified or superseded by statute (the Mineral Leasing Act of 1920 changed disposal of these minerals but did not by itself revoke withdrawals). A modification that opens withdrawn lands to leasing does not end the withdrawal: it changes the disposal regime, and leases are accrued rights. Restoration orders end parts of earlier withdrawals.', 'savings': 'Valid existing rights and leases. FLPMA (Pub. L. 94-579, Oct. 21, 1976) s.704(a) repealed the Pickett Act and implied withdrawal authority prospectively; s.701 saves existing withdrawals until modified under FLPMA or other law (IBLA, Grant L. Hacking, 1980). This is a continuity point, never an end; the s.204(l) review of withdrawals is a review lead, not an end.', 'outliers_add': ["The order only amends or modifies another order: its own operative effect merges into, and normally ends with, the parent order; read the parent's text and lifecycle. (The exemplar EO 6016 modifies EO 5327, the 1930 oil-shale withdrawal, to allow oil and gas leasing.)", 'Coal, phosphate or potash lands later restored subject to a mineral reservation under the surface-entry acts of 1909, 1910 and 1914: the restoration ends the withdrawal but leaves a reserved mineral estate.', 'Helium reserves governed by the Helium Act.', 'Oil-shale reserves later placed under statutory naval-reserve management.'], 'exemplar': {'id': 'EO:6016', 'parts': [('Executive Order No.\n5327 of April 15, 1930', 'is hereby modified')]}}, 'TR-MILITARY-RESERVATION': {'outliers_add': ['The order keeps reversions, water rights or rights-of-way (the exemplar, paras 2-3): these residual interests outlive the restoration and need their own state.', 'Territorial lands (Hawaii, Alaska, Puerto Rico) subject to admission or organic acts; for Hawaii the Admission Act of 1959 s.5 is a lead on lands set aside for federal use, not an assumed end.', 'Disposal under the Surplus Property Act of 1944 or the Federal Property and Administrative Services Act of 1949: the deed date is the end.'], 'exemplar': {'id': 'EO:5637', 'parts': [('is, subject to the exception, reversion, and service of', 'Territory of Hawaii.')]}}, 'TR-INDIAN-RESERVATION': {'mechanism': 'own_terms_or_standing', 'ending_pattern': "Two sub-patterns. (a) Trust-period extensions (own terms): the order extends trust periods expiring in a stated year for a stated number of years, and ends on its own stated date; a later extension usually runs from that expiration and does not supersede the earlier order. Section 2 of the Indian Reorganization Act of June 18, 1934 (48 Stat. 984) extended existing trust periods 'until otherwise directed by Congress', but s.13 excludes listed Oklahoma tribes and s.18 makes the Act inapplicable to reservations that voted to exclude themselves; for those, the Act of June 15, 1935 s.3 extended trust periods to Dec. 31, 1936 (verify each). (b) Reservation or boundary orders (standing until revoked): continue until changed by statute or order.", 'effective_date_basis': "(a) The end of the stated trust period, or the earlier statutory extension that controls the order's subject (IRA s.2, or the 1935 Act for excluded reservations). (b) A current basis, or the changing instrument's date.", 'required_evidence_add': ['Whether the tribe or reservation was covered by IRA s.2, excluded by s.13, or opted out under s.18.'], 'outliers_add': ['Post-1919 orders creating or enlarging reservations: the Act of June 30, 1919 s.27 barred new executive-order Indian reservations without Congress, and the Act of March 3, 1927 limited later boundary changes (verify).', 'Termination acts (1950s), or later statutes confirming boundaries or restoring lands, as independent bases.', 'Reservations in Alaska or Oklahoma (IRA s.13).', 'Allotments inside a reservation have separate trust lifecycles.'], 'exemplar': {'id': 'EO:2747', 'parts': [('It is hereby ordered, under authority contained in the act of February 8, 1887', 'Lucy Bourbonny; 112, Oshie Bourbonny; 113, Alfred Bourbonny.')]}, 'exemplar2': {'id': 'EO:2550', 'parts': [('It is hereby ordered that two unsurveyed islands', 'existing valid rights in and to the same.')]}}, 'TR-LAND-WITHDRAWAL': {'ending_pattern': "A withdrawal continues until revoked or modified, or, for a tract, until it is patented or sold (townsite and cemetery withdrawals). Temporary withdrawals 'pending resurvey' or 'for classification' end when the purpose is completed and the order is revoked; the revoking instrument, not the purpose, usually supplies the exact date. Restoration orders end parts of earlier withdrawals.", 'savings': 'Valid existing rights. FLPMA (Pub. L. 94-579, Oct. 21, 1976) s.704(a) repealed the Pickett Act and implied withdrawal authority prospectively; s.701 saves existing withdrawals until modified under FLPMA or other law (IBLA, Grant L. Hacking, 1980). This is a continuity point, never an end; the s.204(l) review of withdrawals is a review lead, not an end.', 'outliers_add': ['Overlapping later blanket withdrawals (for example the 1934-35 general withdrawals pending Taylor Grazing Act classification, EO 6910 and EO 6964): a revocation of the earlier order may leave the land withdrawn under the later one.', 'Alaska lands affected by ANCSA, statehood selections and the Alaska Lands Act.', 'Stock driveways (the separate stock-driveway rule was withdrawn for lack of a held exemplar): withdrawn under s.10 of the Stock-Raising Homestead Act of 1916 (39 Stat. 862); apply this rule with that authority.'], 'exemplar': {'id': 'EO:3297', 'parts': [('Under the provisions of the act approved June 25, 1910', 'characteristic examples of paleobotany numerously found there.')]}}, 'TR-NRA-CODE': {'ending_pattern': "Candidate end: the code-making authority under NIRA Title I fell with Schechter (May 27, 1935) and the Title's original expiry (June 16, 1935, s.2(c)); S.J. Res. 113, approved June 14, 1935 (49 Stat. 375), extended Title I to April 1, 1936 without code-making or code enforcement, and the President treated the old code provisions as inoperative. The candidate end date for a code approval is a legal judgment between May 27, 1935 and June 16, 1935 that the agent makes and explains per order (event X1-E2).", 'outliers_add': ['Petroleum-code provisions under s.9(c), held invalid earlier in Panama Refining Co. v. Ryan (Jan. 7, 1935).', "The President's Reemployment Agreement and other s.4(a) agreements with their own terms.", 'Code approvals with conditions, exemptions or stays later modified by administrative order.', 'Codes later given statutory life (for example bituminous coal under the 1935 Guffey Act).']}, 'TR-CANAL-ZONE': {'ending_pattern': "Candidate end: the Canal Zone ceased on October 1, 1979 (event X1-E3), but most orders ended earlier: by supersession; by lapse or repeal of the specific statutory authority (the exemplar EO 5888 rests on a proviso to s.20 of the National Prohibition Act, so it is a candidate to have ended with Prohibition's repeal in 1933); or on their own terms. A codification (the Canal Zone Code) ends an order only where the Code or its enacting act expressly repeals or replaces it; otherwise it is a lead. The earliest end controls.", 'effective_date_basis': "The earliest of: a superseding order, lapse or repeal of the order's statutory authority, an express repeal by codification, the order's own terms, X1-E3.", 'outliers_add': ['The 30-month treaty transition (Panama Canal Treaty art. XI; Panama Canal Act of 1979): some U.S. jurisdiction and transitional courts continued past Oct. 1, 1979 (to about March 31, 1982), so orders on courts, police or criminal law may have a later end.', 'Panama Railroad / Panama Canal Company corporate matters resting on corporate statutes.']}, 'TR-PHILIPPINES': {'ending_pattern': 'Candidate ends, earliest first: the inauguration of the Commonwealth (Nov. 15, 1935, under the Tydings-McDuffie Act, 48 Stat. 456) for orders about the Governor General and insular administration; the transfer of the Bureau of Insular Affairs to Interior (Reorganization Plan No. II of 1939); and independence on July 4, 1946 (Proclamation 2695; event X1-E4). For reservations, the U.S.-sovereign status of an executive-order reservation is a candidate end on July 4, 1946; later U.S. use of bases rested on the 1946 treaty and the Military Bases Agreement of March 14, 1947, a new basis, not a continuation of the order.', 'savings': "Property the United States retained after 1946 (embassy, cemeteries, veterans' facilities) under later agreements: independent bases.", 'outliers_add': ['Wartime occupation 1942-45 (government in exile): not an end.', 'Orders whose Philippine mention is incidental (for example a civil-service schedule covering many places).', "The exemplar's date: the rule's source page and the held text disagree (September 16 vs September 19, 1916); settle from an official printing."], 'exemplar': {'id': 'EO:2456', 'parts': [('Under this provision hereafter all official reports', 'are placed in the jurisdiction of that department.')]}}, 'TR-WWI-EMERGENCY': {'ending_pattern': "Candidate end: the joint resolution of March 3, 1921 (Pub. Res. 64, 41 Stat. 1359-1360, event X1-E1) operates generally on any provision contingent on the duration or termination of the war or of the 'present or existing emergency', and on Acts in force only during the war; it names exceptions (among them the Trading with the Enemy Act, the District of Columbia rents title, the Liberty Bond Acts and parts of the War Finance Corporation Act). It ends the war-contingent statutory authority, not each order automatically. Other candidate dates: the Knox-Porter Resolution of July 2, 1921 (42 Stat. 105) and the peace treaties proclaimed in November 1921, for statutes keyed to them; Acts with their own termination clauses (for example the Overman Act, six months after the war). Many orders ended earlier by revocation or completion.", 'effective_date_basis': "The earliest of: own terms, revocation, completion, the end of the order's statutory authority under the 1921 resolution or the Knox-Porter / treaty dates (shown for that authority).", 'savings': "Contracts, claims and property transfers made during the war are accrued effects; corporations or agencies created under wartime orders may have continued under later liquidation statutes (the exemplar's United States Housing Corporation was a New York corporation).", 'outliers_add': ['Orders under the excepted statutes (the Trading with the Enemy Act among them).', 'Corporations or agencies created under wartime orders that continued under later liquidation statutes.'], 'exemplar': {'id': 'EO:2985A', 'parts': [("By  virtue  of  tlie  authoritj'", 'by  Executive  order  dated  .Time  IS,  1918.')]}}}
FROZEN = {'TR-CLOSING-MOURNING', 'TR-WATER-RESERVE'}

# Round 3 (2026-10-19): the five rules round 2 approved only with changes
# (research/production/x1-2026-10-19/TYPE_RULES_REVIEW_R2.json). The other rules
# are not rebuilt, so their reviewed bytes stay frozen.
ROUND3 = {
    "TR-CANAL-ZONE": {"ending_pattern": REVISIONS["TR-CANAL-ZONE"]["ending_pattern"].replace(
        "the exemplar EO 5888 rests on a proviso to s.20 of the National Prohibition Act, so it is a candidate to have ended with Prohibition's repeal in 1933",
        "the exemplar EO 5888 rests on the Canal Zone liquor provision added to the National Prohibition Act in 1932 (47 Stat. 579; 27 U.S.C. 63), which was repealed on June 19, 1934 (48 Stat. 1116, s.3); that Act also gave the President new liquor-rule authority for the Canal Zone, so a successor order may exist and must be checked")},
    "TR-POWER-SITE": {
        "ending_pattern": "Land withdrawal for water-power or reservoir purposes (the type includes reservoir site reserves made under the same 1910 withdrawal act, as in the exemplar; no numbered Power Site Reserve order that creates a reserve has a held text yet): continues until revoked, modified or vacated by a later order or Public Land Order. Under Federal Power Act s.24 (16 U.S.C. 818), lands reserved for power purposes may be opened to entry only on a Federal Power Commission determination, with a reserved right of re-entry; the 'until otherwise directed by the Commission or by Congress' wording of s.24 applies to lands in a filed project application. Restoration orders diminish a reserve.",
        "savings": "Valid existing rights; licences under the Federal Power Act. A restoration under FPA s.24 may reserve a right of re-entry for power purposes (a residual). FLPMA (Pub. L. 94-579, Oct. 21, 1976) s.704(a) repealed the Pickett Act and implied withdrawal authority prospectively; s.701 saves existing withdrawals until modified under FLPMA or other law (IBLA, Grant L. Hacking, 1980). This is a continuity point, never an end; the s.204(l) review of withdrawals is a review lead, not an end.",
        "outliers_replace": ["Lands reserved by a filed project application under FPA s.24, with no executive order.", "Restoration subject to FPA s.24 conditions (Commission determination, reserved right of re-entry).", "The order itself is a restoration (it ends part of another order rather than creating a reserve)."]},
    "TR-PROPERTY-TRANSFER": {
        "outliers_replace": ["The property is land (land types).", "The order also transfers functions, offices or personnel (organization type).",
                             "Transfers 'for temporary use', with reversion or 'for the duration' terms: the property returns, so the order is not spent on delivery.",
                             "Vessels later re-transferred or sold: a chain of instruments is needed."],
        "exemplar": {"id": "EO:206", "parts": [("The historical archives in the Department of State, known as the Revolutionary archives",
                                                "or as promptly thereafter as shall be found conveniently practicable")]}},
    "TR-OWN-TERMS-EXPIRY": {
        "effective_date_basis": "The 'until' date in the order's text; for an event-relative date (the exemplar: sixty days after the convening of the second session of the 73rd Congress) the agent computes it from a cited source for the event and states the computation. A later extension issued before expiry amends the date (the order then ends on the extended date, or the later order carries the subject forward); the issue date of an extension is never by itself this order's end.",
        "outliers_replace": ["Event-relative or contingent dates (the exemplar).", "The deferred measure was later rescinded, so the deferral never matured.", "'Until further order' or no date."]},
    "TR-WWI-EMERGENCY": {
        "ending_pattern": REVISIONS["TR-WWI-EMERGENCY"]["ending_pattern"].replace(
            "the peace treaties proclaimed in November 1921", "the peace treaties with Germany and Austria (proclaimed November 1921) and Hungary (proclaimed December 20, 1921)"),
        "outliers_replace": ["Orders under the excepted statutes (the Trading with the Enemy Act among them).",
                             "Orders whose authority is not contingent on the war or the existing emergency: the 1921 resolution does not reach them.",
                             "Corporations or agencies created under wartime orders that continued under later liquidation statutes."]},
}
for _k, _v in ROUND3.items():
    REVISIONS[_k] = {**REVISIONS[_k], **_v, "round": 3}
    if "outliers_replace" in _v:
        REVISIONS[_k].pop("outliers_add", None)

# Round 4: TR-PROPERTY-TRANSFER only (round 3 approved the other 21 as they stand).
REVISIONS["TR-PROPERTY-TRANSFER"] = {**REVISIONS["TR-PROPERTY-TRANSFER"], "round": 4,
    "effective_date_basis": "A stated effective date in the order, if any, over the signature date. A transfer date qualified by 'or as promptly thereafter as practicable' (the exemplar), or a partial transfer left to an official's discretion, is not a delivery date: the end is the delivery or accession record, otherwise a stated gap.",
    "required_evidence_add": ["The delivery or accession record (agency or receiving-institution record) with its date, or an explicit gap."],
    "outliers_replace": REVISIONS["TR-PROPERTY-TRANSFER"]["outliers_replace"] + [
        "The transfer date is qualified ('or as promptly thereafter as practicable') or the extent of the transfer is left to an official's discretion: the stated date is not the delivery date."],
    "exemplar": {"id": "EO:206", "parts": [
        ("The historical archives in the Department of State, known as the Revolutionary archives", "prescribed by the Librarian of Congress."),
        ("The transfer here directed shall be made", "to the Department of State and the Library of Congress.")]}}

# Round 4 for TR-CS-WAIVER (2026-10-28): the owner's ruling that evidence decides
# (research/readiness/owner_rulings/2026-10-28-evidence-not-convenience.md) and the research in
# research/excavator/claude-cs-waiver-research-2026-10-28/REPORT.md. The round-2 text treated every
# unrecorded use as an unresolved gap and named the CSC annual report as a source for the action date;
# the reports print and count the orders but never record whether an individual waiver was used.
REVISIONS["TR-CS-WAIVER"] = {**REVISIONS["TR-CS-WAIVER"], "round": 6,
    "ending_pattern": (
        "The order authorizes one personnel action for one named person (appointment, reinstatement, transfer, "
        "retention or examination without regard to a civil-service rule). Its permission is exhausted when the "
        "action is taken; the resulting appointment or status survives as an accrued effect of the action, not of "
        "the order, unless a later order revokes it. EO 6179-A (June 16, 1933) revoked, as 'appointments made by "
        "the President', ten waiver orders identified by their own dates; it ends any unused permission under them "
        "and any appointment made under them, and is not evidence that an appointment was made. Decide each order on the held evidence. (1) Exhausted on a date, when a dated record of "
        "the action is held. (2) Exhausted within the interval (order date, R], when a record shows the person in "
        "the authorized position at date R and not in it at the order date. (3) Not in force, use unknown, stated "
        "as the interval (order date, reason date], because a permission that was used ended earlier than the "
        "reason. Reasons: an express revocation, such as EO 3461 of May 16, 1921, which revoked 'all Executive "
        "orders and amendments to the civil service rules authorizing appointments, promotions, or removals without "
        "full compliance with the civil service laws and rules, because of war emergencies existing at the time' "
        "and lists the orders it revokes. A member in that list is expressly revoked; a member not in the list whose "
        "own text rests on the war emergency is covered only on a reading of the general clause (the list could "
        "instead be read as exhaustive), so state that reading as the basis. The held copy "
        "(jobs/csc-annual-reports/output/texts/EO_3461.txt) stops at item 27 of 45, so absence from the held list is "
        "not absence from the list. Other reasons: a 1900-1902 special rule that on reading names a person (EO 209 replaced the 1896 rules 'and the amendments thereof'); the named person's known death; or, as "
        "a bound only, the latest possible death. (4) Open, naming the records that would settle it. Whether the "
        "action happened is a separate question from when the permission ended: categories (3) and (4) keep the "
        "order open on use. The latest possible death is computed by subtracting a_min whole years from the order "
        "date and then adding 122 years 164 days (the longest authenticated life). a_min is 0 unless a quoted fact "
        "in the order or a held record fixes a minimum age, and then it is the lowest age that the quoted fact "
        "allows, not a typical age (for example, 'widow of' allows only the lowest lawful marriage age, not "
        "adulthood; dated earlier service fixes an age only if the earlier record states one); a position or "
        "professional title alone does not fix an adult age (the type includes a 'messenger boy', EO 2661). The bound counts only if it falls before the claim's legal cutoff date; state the a_min used "
        "and the smallest a_min at which the bound would fall before that cutoff. The later general rewrites of the "
        "Civil Service Rules (EO 7916 of 1938, EO 8743 of 1941, EO 9830 of 1947, EO 10577 of 1954) revoke only "
        "listed orders and schedules and list no one-person waiver, so they are not ends for these orders. EO 209 "
        "(1903) is a reason only for the special rules above, and a candidate only for other waivers issued before "
        "April 15, 1903."),
    "effective_date_basis": (
        "(1) The date of the action from a dated record: a NARA St. Louis service record card or personnel folder, "
        "an agency report, or a later order's recital that dates the action itself. A recital may give only the "
        "waiver order's own date (EO 6179-A does), which is not the date of the action. (2) The interval (order "
        "date, R], with the record that supplies R: the Official Register (all employees in odd years 1901-1921, "
        "dated July 1 according to a secondary index; postal employees omitted after 1911; officials only from "
        "1925), a later order naming the person in the authorized position, or an agency report. A match needs the "
        "full name, the office, and a position consistent with the order. Absence from the "
        "Register proves nothing; presence does not show which authority an appointment used, and does not show "
        "use of a retention or temporary-to-permanent order. (3) The interval (order date, reason date]: the "
        "revoking order's date (EO 3461: 1921-05-16), April 15, 1903, the death date, or the latest-possible-death "
        "bound, with 'use unknown' stated. The four Civil Service Commission annual reports read in full (FY1914, "
        "1915, 1918 and 1922) print and count the orders but do not record whether or when an individual waiver was "
        "used; the other reports have not been read in full, so a report is a source for the action date only if a "
        "reading finds such a record."),
    "savings": (
        "The appointment or status conferred is an accrued effect that continues independently of the order (state "
        "transferred_or_accrued), unless a later order revokes it: EO 6179-A (June 16, 1933) revoked ten waiver orders "
        "as 'appointments made by the President', ending any unused permission and any appointment made under them, "
        "without showing that an appointment was made. The Act of March "
        "27, 1922 and EO 9830 s.1.1(b) recognize competitive status granted by executive order, which supports the "
        "status surviving later rewrites of the Civil Service Rules. Later service rights flow from civil-service "
        "statutes, not from the order."),
    "required_evidence_replace": [
        "The order's own text naming the person, the action and the rule waived.",
        "A dated record of the action, a record bounding it, or a stated reason the permission ended; otherwise the "
        "order stays open, naming the records that would settle it (the Official Register for the next listing "
        "date; the NARA St. Louis card).",
        "A bounded later-law search for an order or statute naming this order or the person (revocation, including "
        "EO 3461's list; modification; confirmation; revocation of the appointment itself; or a later order showing "
        "the person in the position).",
    ],
    "outliers_replace": [
        "The order is not a one-person waiver on reading. Examples found so far (not a complete list): rule "
        "amendments (EO 60, 95, 123, 158, 164, 262, 332, 1582, 2121, 6043, 7137; type cs_rules_amendment); class "
        "orders and general authorities (EO 203, 222, about 30 others found in review; EO 715 on transfers and EO "
        "983 on fourth-class postmasters, both revoked by EO 9830 effective May 1, 1947); land orders (EO 395, "
        "3992); orders revoking other orders (EO 3461, 6179-A); and EO 2071 and 2284, found in review not to fit.",
        "A 1900-1902 'special rule' for a position rather than a person (EO 130, 141-143, 154, 174, 185, unless on "
        "reading one names a person).",
        "The order names several persons (EO 223, 226, 686, 1321, 3681): decide each person's permission separately; the order is spent only when every person's permission has "
        "ended, and its end is the latest of them.",
        "The authority is continuing (for example 'may be appointed at any time').",
        "The waiver is conditional (for example on a noncompetitive examination or probation) or limited to a "
        "stated position or period.",
        "The order rests on the war emergency (1917-1921): check EO 3461's list and text as an express end.",
        "The person is named again in a later order (serial waivers, retention or retirement orders, a later "
        "modification such as EO 7472 of EO 7140, or a revocation of the appointment such as EO 6179-A): read both; "
        "the later order may supply use evidence or an end.",
        "The order converts a temporary employee to permanent status or retains an employee: presence in the "
        "position is not evidence of use.",
        "The held text is printed in a Civil Service Commission annual report, so the report's commentary or "
        "neighbouring orders can bleed into the slice.",
    ],
}
REVISIONS["TR-CS-WAIVER"].pop("outliers_add", None)
