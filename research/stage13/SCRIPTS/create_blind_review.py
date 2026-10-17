import json,pathlib
out=pathlib.Path('/mnt/data/EO_STAGE13_FOUNDATIONAL_VALIDATION_2026-10-16/AUDIT/INDEPENDENT_BLIND_FIRST_EIGHT.jsonl')
items=[
('BLIND-001','EO:6606A','no','indeterminate','medium','Title I NIRA code interpretation and an administrator grant; Title I industrial code regime lost legal footing and ceased in 1935; verify residual claims before any-effect NO; first mechanism unsettled.',
 ['https://www.presidency.ucsb.edu/documents/executive-order-6606-supplement-and-amplification-executive-order-no-6355-october-23-1933','https://supreme.justia.com/cases/federal/us/295/495/'],
 'The original concerns NIRA codes and administrator authority. No current code-based commands identified. This is a bounded provisional NO; current ancillary effect has not been excluded.'),
('BLIND-002','EO:14371','no','indeterminate','high for substantive','Closure only on December 24 and 26, 2025; possible EO-dependent pay/claims need separate review.',
 ['https://www.federalregister.gov/documents/2025/12/23/2025-23847/providing-for-the-closing-of-executive-departments-and-agencies-of-the-federal-government-on','https://www.archives.gov/federal-register/publications/presidential-compilation.html'],
 'Dated closures spent by 2026; other sections may authorize exceptions but not beyond named dates. Ancillary rights review incomplete.'),
('BLIND-003','EO:6877','no','indeterminate','high for substantive','Original Feb 1 1935 endpoint was EXTENDED on that date by EO6955-A to 30 days after board report; no naive Feb 1 cessation coding. Title I NIRA regime ended in 1935. Board record and residuals unresolved.',
 ['https://www.presidency.ucsb.edu/documents/executive-order-6877-creating-wool-textile-work-assignment-board-etc','https://www.presidency.ucsb.edu/documents/executive-order-6955-amending-executive-order-no-6877-providing-rules-and-regulations-for','https://ecommons.cornell.edu/bitstreams/e26b218e-c7f3-4ae9-a838-0d1cd5a096c8/download'],
 'Discovered substantive extension omitted by single-text expiry analysis; date of report and first ending still require primary proof.'),
('BLIND-004','EO:10746','no','indeterminate','medium-high for substantive','EO amends EO10560; EO10900 superseded earlier delegations on Jan 5 1961 WITH broad saving clause; EO12220 revoked EO10746 expressly in 1980. Ongoing contract effects may derive from later law or saved rights, thus any-effect not closed.',
 ['https://www.presidency.ucsb.edu/documents/executive-order-10746-further-providing-for-the-administration-the-agricultural-trade','https://www.presidency.ucsb.edu/documents/executive-order-10900-administration-the-agricultural-trade-development-and-assistance-act','https://www.archives.gov/federal-register/codification/executive-order/12220.html'],
 'Original amender footprint superseded 1961 and later expressly revoked 1980. The 1961 saving clause means there is a separate residual question.'),
('BLIND-005','EO:13286','indeterminate','indeterminate','low for final status; high for active-lineage lead','Mass amender with 2025 amendment to its own §88 and current US Code placement. Some host amendments likely persist, but exact 2026 surviving EO-attributable clause requires a host provision/version crosswalk. Mere modern listing is insufficient for YES.',
 ['https://www.govinfo.gov/content/pkg/FR-2003-03-05/pdf/03-5345.pdf','https://uscode.house.gov/view.xhtml?edition=prelim&f=treesort&fq=true&granuleId=USC-prelim-title6-section111&hl=true&num=605&req=21','https://www.presidency.ucsb.edu/documents/executive-order-14131-amendments-executive-orders-relating-certain-certificates-and-badges'],
 'Positive candidate: ongoing DHS transfer crosswalk. But amendments in EO14131 replaced text in one host previously touched by 13286; cannot assume all historical amendment effects continue.'),
('BLIND-006','EO:13284','yes','yes','medium-high','EO13284 §15 inserts DHS Secretary in EO10865 §1. Current codified 50 USC 3161 editorial note still prints EO10865 with EO13284 amendment and continuing requirements; no later terminating intervention identified in bounded review.',
 ['https://www.govinfo.gov/app/details/WCPD-2003-01-27/WCPD-2003-01-27-Pg101','https://www.law.cornell.edu/uscode/text/50/3161','https://www.presidency.ucsb.edu/documents/executive-order-13284-amendment-executive-orders-and-other-actions-connection-with-the'],
 'Specific attributed amended host clause appears in current codification, qualifying for YES under TC09. This is source-anchored but still needs independent complete later-change search to certify.'),
('BLIND-007','EO:12069','no','no','high for substantive; medium for any','One textual substitution into host EO11861; EO12076 on Aug 18 1978 revoked EO11861 as amended and replaced the schedule. No surviving authority under the earlier insertion has been identified.',
 ['https://archives.federalregister.gov/issue_slice/1978/7/5/28971-28975.pdf','https://www.presidency.ucsb.edu/documents/executive-order-12076-executive-schedule','https://www.archives.gov/federal-register/executive-orders/1978.html'],
 'Potential first cessation no later than Aug 18 1978; a first-cause adjudication must consider whether new EO12076 superseded the specific salary designation or there was an earlier underlying position change.'),
('BLIND-008','EO:8885','no','no','high for substantive under TC07','Pure revocation of previous EO7632 Peskan MT customs port designation. Completed repeal: NO under TC07; durable legal consequence (port ceases to be a port) would be YES in consequences-based alternative.',
 ['https://www.archives.gov/federal-register/executive-orders/1941.html','https://www.presidency.ucsb.edu/documents/app-categories/written-presidential-orders/presidential/executive-orders?items_per_page=60&page=92'],
 'Strong minimal pair for TC07: continuing repeal consequences vs continuing operative command. No additional operative clause identified.'),
]
with out.open('w') as f:
 for cid,i,s,a,g,mech,links,proof in items:
  item=dict(blind_case_id=cid,instrument_id=i,independent_substantive_assessment=s,independent_any_effect_assessment=a,assessment_grade=g,independent_legal_reasoning=proof,first_cause_flag=mech,independent_source_urls=links,provisional=True,source_completeness='targeted legal chain, NOT entire independent archive provenance')
  f.write(json.dumps(item,ensure_ascii=False)+'\n')
print(out,'8 reviews written without project review key accessed by this script')
