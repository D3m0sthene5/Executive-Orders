"""Producer B's bounded, source-read judgments; no canonical publication."""
import sys, json, pathlib, hashlib, datetime, re
sys.path.insert(0, 'jobs/claim-kit')
import batch

root = pathlib.Path.cwd()
folder = root / 'research/excavator/2026-10-18/batch-pilot/matched/B'
packet, dossiers = batch.load_packet(folder, root)
decisions = batch.rows(folder / 'decisions.csv')
old_clauses = batch.rows(folder / 'clauses.csv')
rationales = {}
clauses = []

def ref(key, value):
    rationales[key] = value
    return '@rationale:' + key

def inventory(iid, labels, final):
    d = dossiers[iid]; text = d['evidence'][d['original_source_id']]['text']
    starts = [(scope, text.index(marker)) for scope, marker in labels]
    return [(scope, start, starts[n+1][1] if n+1<len(starts) else text.index(final, start))
            for n,(scope,start) in enumerate(starts)]

inventories = {}
inventories['EO:12720'] = inventory('EO:12720', [
 ('sec1-a','Section 1.'),('sec1-b','(b) The President'),('sec2-a','Sec. 2.'),
 ('sec2-b','(b) In the performance'),('sec3-a','Sec. 3.'),('sec3-b','(b) Members'),
 ('sec3-c','(c) To the extent'),('sec3-d','•(d)'),('sec3-e','(e) The Council')], '[FR Doc.')
# Exclude the page furniture between section 3(d) and 3(e).
t = dossiers['EO:12720']['evidence']['ORIGINAL:EO:12720']['text']
inventories['EO:12720'][7] = ('sec3-d', inventories['EO:12720'][7][1], t.index('\n\n=== PDF page 166'))
inventories['EO:12813'] = inventory('EO:12813', [
 ('sec1','Section 1.'),('sec2','Sec. 2.'),('sec3-a','Sec. 3.'),('sec3-b','(b) Members'),
 ('sec3-c','(c) The Administrator'),('sec3-d','(d) To the extent'),('sec4-a','Sec. 4.'),
 ('sec4-b','(b) The Commission')], 'THE WHITE HOUSE')
inventories['EO:12817'] = inventory('EO:12817', [
 ('sec1','Section 1.'),('sec2','S ec. 2.'),('sec3','Sec. 3.'),('sec4','Sec. 4.'),
 ('sec5','Sec. 5.'),('sec6','Sec. 6.'),('sec7','Sec. 7.'),('sec8','Sec. 8.')], 'TH E W H ITE H OUSE')
inventories['EO:12722'] = inventory('EO:12722', [
 ('emergency-declaration','I, GEORGE BUSH'),('sec1','Section 1.'),('sec2-intro','Section 2.'),
 ('sec2-a','(a) The import'),('sec2-b','(b) The export'),('sec2-c','(c) Any transaction'),
 ('sec2-d','(d) The purchase'),('sec2-e','(e) The performance'),('sec2-f','(f) The grant'),
 ('sec2-g','(g) Any transaction'),('sec2-h-definition','(h) Any transaction'),
 ('sec3','Section 3.'),('sec4','Section 4.')], '[FR Doc.')
inventories['EO:12734'] = [('whole',707,1753)]
inventories['EO:12696'] = [(c['scope_id'].partition('#')[2],c['char_start'],c['char_end']) for c in dossiers['EO:12696']['clauses']]

checks = {
 'EO:12720': {
  'earlier_end_check': 'Original section 3(e) would terminate the Council after two years. EO12783 expressly substitutes termination on January 16, 1993; that fixed termination command controls, rather than the original 1992 anniversary or the later 1993 formal revocation. No amendment effective date is inferred from its signing date. EO12869 expressly recognizes EO12720 as amended by EO12783 and revokes it effective September 30, 1993.',
  'scope_check': 'The corrected nine-part inventory includes the original establishment, appointments, both advisory functions, information duty, compensation/travel, support/funding, FACA delegation, and sunset. The OCR joined section 3(d) into 3(c); exact disjoint original-source spans now separate them. The fixed sunset reaches the Council and its continuing institutional machinery; the later formal revocation reaches the entire order.',
  'independent_command_check': 'Each information, funding, support, appointment, and FACA instruction is expressly for this Council or its functions. None directs a separate post-Council program. The appropriation qualifier is not a cessation event. Travel rights for work already performed are accounted for as accrued effects rather than a continuing council mandate.',
  'savings_check': 'No express prospective saving appears in EO12783 or EO12869 for this Council. Section 3(b) nevertheless permits accrued statutory travel expenses, so the residual classification preserves possible accrued rights without asserting that any particular unpaid claim exists.'},
 'EO:12813': {
  'earlier_end_check': 'Original section 4(b) says the Commission shall terminate not later than September 30, 1992. EO12815 replaces only the date with December 31, 1992. This is a termination limit, unlike a report deadline, but the retained not-later-than wording and EO12869 description of committees terminated or work completed do not uniquely establish the actual first cessation date. I decline to convert that limit into an exact historical event.',
  'scope_check': 'The supplied machine whole clause is title text only. Corrected exact original spans cover section 1, section 2, section 3(a)-(d), and section 4(a)-(b). EO12815 changes only section 4(b); EO12869 section 4(b) subsequently revokes the amended order effective September 30, 1993.',
  'independent_command_check': 'Advising the AID Administrator, reporting progress to the Deputy Secretary, services, travel, procurement and FACA delegation are separately inventoried. Reporting to the Deputy Secretary is a function and supplies no automatic report-completion termination. The packet does not supply an actual termination/closeout record.',
  'savings_check': 'Travel and reimbursable service/procurement effects may accrue independently of the commission authority. No continuing commission program is saved in EO12869, but the first cessation issue prevents a complete claim.'},
 'EO:12734': {
  'earlier_end_check': 'The original makes the 10 USC2808 invocation available immediately under the EO12722 Iraq emergency. EO12722 and EO12724 precede EO12734, so missing machine target provisions for those actors cannot establish a later cessation of this order. EO12771 expressly leaves the Iraq emergency unaffected. EO13303 addresses selected property, and EO12817 transfer authority, rather than construction authority. No earlier cessation is identified in the held chain or selected bounded later-order search.',
  'scope_check': 'The original has one operative construction invocation plus effective/publication implementation. It invokes 10 USC2808 according to its terms, for Defense and military department Secretaries, and contains no finite project, report, fixed expiration, or separate independent program. EO13350 explicitly revokes EO12734 and terminates its underlying emergency; section 10 makes that action effective July 30, 2004 at 12:01 a.m. EDT, not July 29 signing.',
  'independent_command_check': 'The military department discretion is part of the single construction authority. Immediate commencement and transmission/publication implement that invocation and do not create separate continuing construction authority after emergency termination. No performance or congressional transmission date is asserted.',
  'savings_check': 'EO13350 section 1 preserves pending actions, pre-effective-date proceedings, matured rights/duties and penalties under NEA202(a). Such accrued effects are retained; it does not save a prospective EO12734 construction delegation or transfer it to the new Iraq emergency. Its property-blocking continuation is expressly limited to EO12722/12724.'},
 'EO:12817': {
  'earlier_end_check': 'Sections 1-3 establish continuing Treasury, bank-transfer and Federal Reserve authority with conditional transfers; an actual transfer does not exhaust the authority to address other assets or repayments. Neither an assumed transfer date nor UNSCR778 adoption is used as an end. The held chain identifies EO13350 as the express revocation, effective under its section 10 on July 30, 2004 at 12:01 a.m. EDT.',
  'scope_check': 'Corrected exact spans separate section 2 from the OCR section 1 block and combine the empty section 8 heading with its two implementation paragraphs. Sections 1-8, including section 4 acquittance/nonliability/pre-transfer rights and section 6 redelegation/all-agency duties, are retained. The whole order is expressly named in EO13350 revocation.',
  'independent_command_check': 'Treasury action, compelled bank transfers, Federal Reserve receiving/holding/investing/transferring, implementation, definitions, noncreation of enforceable rights and immediate/publication instructions were each considered. None supplies prospective independent transfer authority after express revocation. Section 4 protects qualifying historical conduct; its accrued effects are separately preserved. No actual administrative completion or congressional transmission event is inferred.',
  'savings_check': 'Original section 4 protects completed transfers, good-faith conduct, and pre-transfer rights/debts/claims. EO13350 section 1 additionally saves matured rights/duties and proceedings. These are accrued consequences, not continued authority for new transfers under EO12817; the separate blocking continuation names EO12722/12724.'},
 'EO:12696': {
  'earlier_end_check': 'Alternate cited OCR contains section 4(b) 24-month sunset; EO12756 section 1 continues the Council until November 13, 1993 and changes membership in section 2. EO12869 section 4(d), effective September 30, 1993 under section 6, is earlier than that extended limit. The parent original recheck omits the page12 provisions, so a complete original-based first-end assertion cannot be approved from the frozen source span.',
  'scope_check': 'The parent original stops after section 3(c), then a filing marker. The alternate held original OCR retains section 3(d), section 4(a) FACA delegation and section 4(b) sunset. Original-source overrides cannot lawfully add text beyond the pinned parent original span. The alternate source requires a page check, and no official page images have been inspected.',
  'independent_command_check': 'The original sections 1-3(c) advisory, reporting, compensation and staff functions were read, along with alternate page12 information and FACA duties. Reporting whenever requested is no deadline. Council-dependent machinery appears to end with the Council, but missing official complete original coverage prevents inventory confirmation.',
  'savings_check': 'Travel under section 3(b) may yield accrued effects. EO12756 is a continuation/membership amendment, and EO12869 contains no specific prospective saving for this Council. Complete original/page verification remains necessary before closing residuals.'},
 'EO:12722': {
  'earlier_end_check': 'EO12724 section 6 revokes EO12722 only to the extent inconsistent and continues administrative acts under the new order. EO12771 expressly does not terminate the Iraq emergency. EO12817 creates specific transfer mechanisms. EO13303 section 2(a) removes the orders from selected property, with section 2(b) savings. EO13350 revokes EO12722 but preserves blocked-property prohibitions and accrued effects. These are distinct partial transitions and cannot be replaced by one July30,2004 first-end date.',
  'scope_check': 'Original declaration, blocking, each transaction prohibition, definition, effective provision and Treasury/all-agency/publication directions were read and retained in corrected source spans. The machine lead-only clause omitted the emergency declaration. Determine exact inconsistent scope under EO12724, the selected-property reach of EO13303, and the operative currency of retained blocking before approving all clauses.',
  'independent_command_check': 'Treasury delegation, agency measures, emergency declaration and blocking are separately considered from import/export/travel/transport and other prohibitions. Completed transfers under EO12817 cannot by themselves establish a whole-order end. No Treasury determination, exhaustion, or signing-date effective event is inferred.',
  'savings_check': 'EO12724 section 6, EO13303 section 2(b), and EO13350 section 1 contain express savings/continuation. Current-law pointers to 31 CFR576.201(b) and the 50 USC1701 Iraq Sanctions note could explain continued effects, but full attributed legal-text slices and complete cutoff coverage are absent; the conflict remains unresolved.'}}

gaps = {
 'EO:12813': ['B-TASK-AID-FIRST-STOP: Obtain a dated commission termination/charter closeout or contemporaneous AID/FACA record establishing whether first cessation occurred before or on the amended not-later-than December 31, 1992 limit; do not infer an actual event from that limit.', 'B-TASK-AID-EXTENSION-EFFECT: Establish the legal effective timing of EO12815 amendment (issued on the original deadline) from an appropriate official record or governing rule, without treating signing date as automatic effectiveness.'],
 'EO:12696': ['B-TASK-12696-COMPLETE-ORIGINAL: Inspect official 54 FR47507-47508, PDF pages11-12, source SHA02105ade4671e8d0c6dd14c31a457eba501d45d946c9a28029781a89684aed3a; verify alternate OCR section3(d), section4(a)-(b), repair the truncated recheck and prepare a newly pinned full dossier. Current original overrides cannot reach those omitted provisions.'],
 'EO:12722': ['B-TASK-IRAQ-CURRENT-TEXT: Acquire or locate exact full attributed 31 CFR576.201 and 50 USC1701 Iraq Sanctions note text with original-source hashes and edition/cutoff evidence through2026-10-14 (USC119-121 stops2026-10-09). Resolve NO_ORDER_CITED_IN_CURRENT_LAW from those provisions.', 'B-TASK-IRAQ-PARTIAL-SCOPE: Map original prohibitions/delegations clause by clause to EO12724 section6 inconsistency/savings and EO13303 section2 selected-property exception; establish EO13303 actual effective timing without signing inference.', 'B-TASK-IRAQ-TRANSFER-FACTS: Locate Treasury determinations/directives under EO12817 and relevant blocking/transfer records to distinguish historical transfers, still-blocked property and continuing independent commands; no transaction event or exhaustion is inferred.', 'target provision not located: EO:12743 — full held source was read and invokes reserve/personnel authority in furtherance of the emergency; it is not an identified revocation, but any purported target transition must be located rather than guessed.']}

end_ids = {'EO:12720':'ACT:EO:12720>EO:12783', 'EO:12734':'ACT:EO:12734>EO:13350', 'EO:12817':'ACT:EO:12817>EO:13350'}
dates = {'EO:12720':'1993-01-16','EO:12734':'2004-07-30','EO:12817':'2004-07-30'}
submits = set(end_ids)
for r in decisions:
    iid=r['instrument_id']; d=dossiers[iid]
    for k,value in checks[iid].items(): r[k]=ref(iid+':'+k,value)
    r['research_rationale']=ref(iid+':research', 'Independent producer B review of the frozen full dossier and held original/actor source texts. '+ ' '.join(checks[iid].values()) +' Selected OFR later-order search is bounded to its reported catalog/saved-text scope; the eCFR search reaches2026-10-14. USC119-121 is only current through2026-10-09 and is not asserted as a complete cutoff predicate. No human approval or publication is asserted.')
    r['outcome']='submit' if iid in submits else 'blocked'
    r['approved']='true' if iid in submits else 'false'
    r['original_confirmed']='false' if iid=='EO:12696' else 'true'
    r['original_pages_confirmed']='false'
    r['inventory_confirmed']='false' if iid=='EO:12696' else 'true'
    r['unresolved_material_gaps']=batch.canon(gaps.get(iid,[]))
    r['search_ids']=batch.canon(['later-events:ofr_catalog','current-law:ecfr'] if iid in submits else [])
    r['conflict_resolutions']='{}'
    r['savings_state']='transferred_or_accrued'
    r['savings_source_id']={'EO:12720':'ORIGINAL:EO:12720','EO:12734':'ACTOR_TEXT:EO:13350','EO:12817':'ACTOR_TEXT:EO:13350'}.get(iid,'')
    r['savings_reason']=ref(iid+':savings',checks[iid]['savings_check'])
    for scope,a,b in inventories[iid]:
        c={k:'' for k in batch.CLAUSE_FIELDS}
        c.update(instrument_id=iid,scope_id=iid+'#'+scope,clause_id='',state='terminated' if iid in submits else '',
                 end_id=end_ids.get(iid,''),effective_date=dates.get(iid,''),effective_date_confirmed='true' if iid in submits else 'false',
                 later_event_ids='[]',later_events='[]',inventory_source_id=d['original_source_id'],inventory_char_start=a,inventory_char_end=b,
                 inventory_reason=ref(iid+':inventory','Complete operative source spans selected by independent comparison with the held original. '+checks[iid]['scope_check']),
                 reason=ref(iid+':clause:'+scope, checks[iid]['independent_command_check']+' '+checks[iid]['earlier_end_check']))
        if iid=='EO:12720':
            c['later_events']=batch.canon([{'id':'ACT:EO:12720>EO:12869','effective_date':'1993-09-30','effective_date_confirmed':True}])
        clauses.append(c)

batch.csv_write(folder/'decisions.csv',batch.ROW_FIELDS,decisions)
batch.csv_write(folder/'clauses.csv',batch.CLAUSE_FIELDS,clauses)
batch.dump(folder/'RATIONALES.json',rationales)
tasks=[]
for iid,values in gaps.items():
    for n,gap in enumerate(values,1): tasks.append({'task_id':iid+'-B-'+str(n),'affected_orders':[iid],'request':gap,'state':'shared_acquisition_or_fact_task_proposal','canonical_queue_written':False,'exhausted':False})
batch.dump(folder/'producer/TASKS.proposed.json',tasks)
batch.dump(folder/'producer/SOURCE_READING.json', {
 'packet_fingerprint':packet['fingerprint'],'legal_cutoff':'2026-10-14','read_method':'bounded shared-source text reads via batch.load_packet/decode and exact dossier metadata; no A or prior Sol decisions/reviews read',
 'primary_blocks_read':['Ta6fe1150cefeb3618107762c','T2d28591a1b6d98eeedbaeecd','Tf908cf962d08c104c47aecf7','Tda0d9944c4ca98e3c66abde0','Te6b3cfb11dc4d61235cfef69','Tad35f44883d379ecc4f148a6','T081bc156744ab18cc13a327d','T8701af7d4fc66e078e5f8b98','T237b95718d2b7c42b914b72a','T4c4fa0aaf8098459f8885326','Tb08796acefa1f9055d68d973','Tdd37fe4a2d8ec6c7031aa0d5','T447738c5ecee6b8099143759','T2abd4bfc9a387d9067ac73c5','T9bf91b73f2e9ab6a53329da3'],
 'additional_cited_held_text_read':'jobs/fr-originals/output/texts/EO_12696.txt',
 'page_images_inspected':False,'codec_issues':packet['codec_issues'],
 'warnings_preserved':['OCR remains unverified against images; original requires_page_check flags are false for all pinned original representations, while EO12696 alternate requires images.','EO12815 shared source contains neighboring tax rules; only the order page and closing White House line are relevant.','No known gap is not legal readiness.','Bounded search absence is not exhaustive all-law proof; no current predicate is inferred for a revoked authority.'],
 'failures_and_corrections':[{'stage':'initial combined reads','failure':'READ and git status output truncated; HANDOFF.md path absent; repeated later bounded reads cover the required sources; truncation is not evidence absence.'},{'stage':'first metadata read','failure':'35791-token metadata/source index display truncated; bounded follow-up reads used.'},{'stage':'EO12815 source read','failure':'Windows stdout cp1252 UnicodeEncodeError U+2666; reported immediately to root; exact source reread with UTF-8 stdout.'},{'stage':'second combined source read','failure':'Top-level tool output truncation removed part of EO12734/EO12817; both reread in full bounded call.'}],
 'scope_limits':'Only six frozen dossiers; no canonical claims/statuses/census/locks/HANDOFF modified; acquisition tasks remain proposals.'})
print(json.dumps({'outcomes':{r['instrument_id']:r['outcome'] for r in decisions},'clauses':len(clauses),'rationales':len(rationales),'tasks':len(tasks)}))
