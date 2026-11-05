#!/usr/bin/env python3
"""Build bounded, unapproved research proposals; never write canonical state."""
import copy
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
import fitz

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1] / 'b02' / 'packet-v1'
CUTOFF = '2026-10-14'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()
sources = []
requests = [json.loads(x) for x in (HERE/'SOURCE_REQUESTS.jsonl').read_text().splitlines()]

def source(num, issuer, date, pages, quote, findings, limits, events=None, read_state='primary_full_text_browser_read'):
    req = requests[num-1]
    sid = f'HEALTH:S{num:02}'
    sources.append(dict(source_id=sid, instrument_id=req['instrument_id'], request_id=req['request_id'],
                        title=req['citation'], urls=req['urls'], issuer=issuer, date=date,
                        page_pin=pages, quoted_passage=quote, findings=findings, limits=limits,
                        events=events or [], read_state=read_state, sha256=None,
                        retention_state='requested_from_root_native_acquisition; hash not asserted here'))
    return sid

source(1, 'HHS Secretary designation; Federal Register notice signed Wilma M. Robinson, Deputy Executive Secretary', '2020-03-25',
       'PDF 1-2 = printed 85 FR 17592-17593; duration and beginning of designation PDF 1; list/signatory PDF 2',
       'This designation is not a ‘‘regulation’’ under the Act.',
       ['HHS actually exercised the delegated scarce-material designation power shortly after EO13910.',
        'The temporary designation has its own 120-day period measured from publication, not a sunset of the delegation.',
        'Embedded designation refers to Executive Order 13190; surrounding explanatory text identifies 13910. Preserve the source error.'],
       ['Does not itself prove every FEMA consultation, any separate rulemaking, or completion of the continuing periodic-review duty.'],
       [dict(kind='designation', signed='2020-03-25', published='2020-03-30', period='120 days from publication unless superseded; no hour/timezone specified')])
source(2, 'HHS Secretary Xavier Becerra', '2021-06-30',
       'PDF 1-3 = printed 86 FR 35810-35812; DATES PDF 1; review and removals PDF 2; four-category designation PDF 3',
       'This action took effect on July 1, 2021, and terminates on November 15, 2021.',
       ['HHS performed an actual review and substantially narrowed the scarce-material list.',
        'Remaining categories cover specified gowns/apparel, laboratory reagents/testing materials, NIH-recommended drug products, and vaccination needles/syringes.',
        'The final located designation therefore ended by its own terms on November 15, 2021; the delegation and duty to reconsider future designations were not textually revoked.'],
       ['No next extension was located in this bounded investigation; that is not proof of an exhaustive absence.',
        'Cannot treat all earlier categories as continuously designated through November 2021.'],
       [dict(kind='modified_extension', signed='2021-06-30', effective_date='2021-07-01', end_date='2021-11-15', time=None, timezone=None)])
source(3, 'OMB Executive Associate Director Aviva Aron-Dine; Task Force and OMB', '2021-01-24',
       '8 PDF pages: cover memo PDF 1-2; model principles PDF 3-8 (appendix printed 1-6); testing PDF 5',
       'the Safer Federal Workforce Task Force and OMB are providing agencies with model safety principles',
       ['Actual issuance of initial agency safety guidance supplies affirmative performance evidence for EO13991 section 2(b).',
        'Task Force was functioning by January 24; guidance expressly anticipates updates.',
        'Testing discussion says CDC is developing/submitting a federal testing plan, so this memo does not establish final submission of the section 5 plan.'],
       ['Initial guidance is not completion of ongoing compliance, later guidance, all consultations, or all agency reports.'],
       [dict(kind='initial_guidance_issued', date='2021-01-24', time=None, timezone=None)])
source(4, 'OMB, OPM and GSA (M-21-25)', '2021-06-10',
       '20 PDF pages; agency performance and continuing plans PDF 1-3, especially PDF 2',
       'agencies have completed and implemented those plans',
       ['Affirmatively corroborates completed and implemented agency safety plans by June 10, 2021.',
        'Existing safety plans and Task Force updates continue; the return-to-work planning process is not a revocation of EO13991.'],
       ['Does not identify each agency submission date or establish every distinct section 4(f) report, section 5 testing-plan submission, or section 6 OSTP assessment.'],
       [dict(kind='performance_corrobation', latest_date='2021-06-10', earliest_known_issuance='2021-01-24')])
source(5, 'CDC Director, Division of Global Migration and Quarantine', '2021-01-29',
       '6 PDF pages = 86 FR 8025-8030; effective-date and termination provisions PDF 6 / printed 8030; scope/exceptions PDF 4-6',
       'This Order shall enter into effect on February 1, 2021, at 11:59 p.m.',
       ['Actual federal mask requirement covers transportation conveyances and hubs, with exceptions and preservation of more protective local requirements.',
        'Order invokes Public Health Service Act section 361 and regulations, as well as implementation context of EO13998.',
        'Its own duration is tied to modification/rescission or the section 319 public health emergency, unlike the parent EO.'],
       ['Not proof that every relevant agency completed every required implementing action or all section 2(b) consultations/reports.',
        'The quoted effective hour has no timezone in the quoted sentence; do not substitute a timezone.'],
       [dict(kind='mask_order', issued='2021-01-29', effective_date='2021-02-01', time='23:59', timezone='not specified in effective sentence')])
source(6, 'CDC Director; Federal Register transmission dated January26 signed Sherri Berger, Acting Chief of Staff', '2021-01-25',
       '5 PDF pages = 86 FR 7387-7391; reasons and revisions PDF 1-2; operative terms PDF 3-5',
       'supersedes the previous Order signed by the CDC Director on January 12, 2021.',
       ['Actual revision of the January 12 international air-testing order took effect January 26, 2021.',
        'Revisions include federal law-enforcement/Defense and humanitarian exceptions; regulatory action followed EO13998.'],
       ['A revised order alone does not establish a completed assessment of all four considerations in section 5(b)(i), required interagency coordination, or submission of the separate quarantine plan.'],
       [dict(kind='superseding_air_test_order', issued='2021-01-25', effective_date='2021-01-26', time=None, timezone=None)])
source(7, 'CDC; Federal Register notice signed Sherri Berger, Chief of Staff', '2022-06-10',
       '3 PDF pages = 87 FR 36129-36131; notice begins PDF 1-2; operative departure-based effective clause PDF 3 /36131',
       'effective for all aircraft departing their point of origin on or after June 12, 2022, at 12:01 a.m. EDT.',
       ['Rescinds the testing/recovery-documentation condition for inbound international air passengers, on a departure-based trigger.',
        'CDC continued to recommend testing; this rescission did not revoke EO13998 or all other international-travel instruments.'],
       ['June 15 publication is not the operative ending date; do not apply the June 12 condition indiscriminately to every flight arrival.'],
       [dict(kind='air_test_rescission', signed='2022-06-10', effective_date='2022-06-12', time='00:01', timezone='EDT', application='aircraft departing point of origin at/after trigger')])
source(8, 'CDC Port Health', '2025-12-01',
       'HTML headings: Requirement for Persons to Wear Masks; negative test/recovery; Requirement for Airlines and Operators to Collect Contact Information',
       'The order was rescinded on November 21, 2025.',
       ['Agency history distinguishes April 18, 2022 unenforceability from May 11, 2023 own-terms expiration of the mask order.',
        'Contact-information order issued October 25, 2021, effective November 8, 2021, persisted beyond EO13998 revocation until its reported November 21, 2025 rescission.',
        'Later China/HongKong/Macau/designated-airports testing condition began January5,2023 00:01EST and ended for specified departures March10,2023 15:00ET; June2022 general rescission did not prevent later narrower testing rules.',
        'Cruise no-sail/conditional-sailing history is separately described, not proof of EO-required Presidential sea-port plan delivery.'],
       ['HTML agency summary is a residual-authority lead; underlying China-test and November2025 rescission instruments should be retained before approving exact instrument-specific legal endings.',
        'The existence of a separate data-collection rule does not keep EO13998 itself in force.'])
source(9, 'United States Congress; approved January 13, 2021', '2021-01-13',
       'Public Law 116-334, full act; section 2 amendments to FAA section 641',
       'USAID Branding Modernization Act',
       ['Separate statute authorizes USAID identity and additional/substitute markings, including the United States flag, and directs an Inspector General audit.',
        'Statutory branding authority survives EO13964 revocation unless separately changed.'],
       ['Not a presidential selection under EO13964 section 2(b)(i), not section 2(a) notice-and-comment implementation, and not the section 3 report to the President.'])
source(10, 'United States Court of Appeals for the Eleventh Circuit', '2023-06-22',
       '11 PDF pages, printed court pages 1-11; procedural history PDF 2-4; mootness and disposition PDF 7-11',
       'the order and judgment of the district court are VACATED',
       ['CDC mask order expired under its own terms when the public health emergency ended May 11, 2023.',
        'Appeal was dismissed as moot, with vacatur of district judgment; no appellate decision of the merits or revival of an expired mandate.'],
       ['June 22 is the opinion filing date, not an independently verified appellate mandate issuance date.',
        'Court did not revoke EO13998; its decision concerns the CDC mandate.'],
       [dict(kind='appellate_mootness_opinion', filed='2023-06-22', mandate_date=None, district_merits_judgment='vacated in disposition; mandate timing not verified')])
source(11, 'Federal Transit Administration', '2022-04-19',
       'HTML official FTA bulletin, opening paragraphs and TSA withdrawal paragraph',
       'will not enforce its mask-related Security Directives.',
       ['Contemporaneous executive-branch response to April 18 district vacatur: CDC order no longer in effect/enforced; TSA ceased enforcement.',
        'FTA says TSA withdrew the coming SD1582/84-21-01E, scheduled to take effect April 19.'],
       ['Withdrawal of a proposed extension differs from court vacatur of every distinct TSA directive.',
        'A bulletin is not the source of the judicial vacatur or whole-EO termination.'])
source(12, 'USAID Office of Inspector General', '2021-07-23',
       'PDF 5-8 = report printed 1-4; 241/251 finding PDF 6 /printed2; sample interval PDF 10 /printed6; detailed marking PDF 12 /printed8',
       '241 (96 percent) were marked with the USAID identity as required.',
       ['Audit under the January 2021 statute examined preexisting ADS320 (February 5, 2020) and 2 CFR 700 requirements.',
        'Of 251 sampled items, 241 displayed USAID identity; this is actual branding performance under identified rules. Awards sampled were dated January2018-May2020, before this EO.'],
       ['The audit to Congress is not EO13964 section 3 implementation report to the President.',
        'Sampling existing USAID identity does not establish the President selected the EO single logo or other agencies implemented its marking directives.'])
source(13, 'United States Department of Transportation', '2023-08-24',
       '13 PDF pages; PDF 4 = printed 3 (introduction), PDF 6-7 = printed 5-6 (mask/testing/travel); preserve page images to confirm footer mapping',
       'Executive Order 13991 currently remains in effect',
       ['Department expressly treated EO13991 as continuing after May 2023 vaccination revocations and public health emergency ending.',
        'Plan retained safety coordination, CDC-responsive masking and other workplace measures while changing screening testing and travel restrictions.'],
       ['Department-specific practice does not prove performance by every agency or final submission of separate CDC/OSTP assessments.',
        'A public-health condition may change specific precautions without ending the EO source of future safety duties.'])
source(14, 'United States Department of Transportation', '2023-07',
       'PDF page pin not established: browser open failed; exact URL queued for native acquisition',
       None,
       ['Search discovery returned a 24-month EO implementation report with an EO13998 entry described as ongoing.'],
       ['Discovery-only lead. Not used as evidence of a completed report, a specific action, or current legal status until the underlying report is read.'],
       read_state='discovery_only; full report not read')
source(15, 'Transportation Security Administration', '2022-03-19',
       'TSA Emergency Amendment 1546-21-01D, effective/expiration fields and foreign air-carrier requirements',
       'Expiration Date: April 18, 2022',
       ['Foreign air-carrier amendment carried a specific March 19-April 18, 2022 effective period.',
        'Confirms a distinct TSA instrument with its own duration rather than automatic duration of EO13998.'],
       ['Cannot generalize one emergency amendment to all aviation and surface security directives.',
        'An expired directive differs from an order temporarily unenforceable by a district judgment.',
        'Native acquisition failed due to robots restriction; indexed primary excerpt only, not authenticated full-text evidence.'],
       read_state='indexed primary PDF excerpt only; full native acquisition blocked')
source(16, 'President Joseph R. Biden Jr.', '2021-09-09',
       '2 PDF pages = 86 FR 50989-50990; section 1 PDF 1',
       'has issued important guidance to protect the Federal workforce and individuals interacting with the Federal workforce.',
       ['Later presidential instrument corroborates actual Task Force guidance under EO13991.',
        'Adds federal employee vaccination requirements; it does not expressly revoke or amend EO13991.'],
       ['Vaccination-specific later court litigation or revocation cannot be transplanted as whole-EO13991 ending.'])
source(17, 'President Joseph R. Biden Jr.', '2023-05-09',
       '2 PDF pages = 88 FR 30891-30892; sections 2-3 PDF 1',
       'Executive Order 14042 and Executive Order 14043 are revoked.',
       ['Revocation and nonenforcement/rescission direction target 14042/14043 and policies only to the extent premised on them.',
        'Effective at 12:01 a.m. eastern daylight time May 12, 2023; EO13991 is not listed.'],
       ['Does not end all workforce safety measures or EO13991; distinguish vaccine-only restraints.'],
       [dict(kind='vaccination_orders_revoked', signed='2023-05-09', effective_date='2023-05-12', time='00:01', timezone='EDT')])
source(18, 'HHS Acting Secretary Norris Cochran; no signature date stated for this notice', '2021-02-01',
       '2 PDF pages = 86 FR 7731-7732; dates PDF 1; updated list PDF 2',
       'This action took effect February 1, 2021 and terminates on June 30, 2021.',
       ['Explicit February 1-June 30, 2021 designation period and addition of syringes/needles used for vaccination.',
        'Compared with the corrected January 19 expiry, these express dates reveal a potential January 20-31 gap in designation coverage.'],
       ['Calling this an extension does not silently fill that gap; locate any intervening valid instrument before asserting continuity.',
        'Agency list duration does not end the original delegated power.'],
       [dict(kind='designation_extension', effective_date='2021-02-01', end_date='2021-06-30', time=None, timezone=None)])
source(19, 'HHS notice signed Ann C. Agnew, Executive Secretary', '2020-07-23',
       '3 PDF pages = 85 FR 45895-45897; changes PDF 1-3; read with December correction S20',
       'This action took effect July 23, 2020 and terminates January 19, 2021.',
       ['Updates and extends the designation rather than exhausts the delegated power.',
        'Narrative identifies prior June 30 removal of chloroquine/hydroxychloroquine (85 FR 40667, July 7, 2020), another concrete withdrawal lead.'],
       ['The retained July notice already gives January19 in DATES but its Summary says additional120days; December23 correction fixes the Summary, not a new later extension. Do not calculate an end from the inconsistent 120-day sentence.'],
       [dict(kind='designation_extension',signed='2020-07-23',effective_date='2020-07-23',end_date='2021-01-19',time=None,timezone=None)])
source(20, 'HHS correction signed Wilma Robinson, Deputy Executive Secretary', '2020-12-23',
       '1 PDF page = 85 FR 83975; correction text refers to July30 notice and substitutes January19,2021',
       'January 19, 2021',
       ['Correction replaces the July2020 Summary final sentence with January19,2021 and explains that this is not120days; retained July DATES already gives January19.',
        'The correction prints a 48596 page reference while the original extension is on 45895-45897; preserve, do not silently rewrite.'],
       ['Corrected expiry plus later February 1 effective date creates an unresolved designation interval; not a delegated-authority interval.'])
source(21, 'U.S. District Court for the Middle District of Florida; Judge Kathryn Kimball Mizelle', '2022-04-18',
       '59 PDF pages = court printed pages 1-59; introduction PDF 1-5; final disposition PDF 58-59, Document 53',
       'The Court DECLARES UNLAWFUL and VACATES the Mask Mandate',
       ['District court vacated the CDC mask mandate under the APA; contemporaneous agencies ceased enforcement.',
        'The President was terminated as a defendant, not subjected to a whole-EO13998 revocation decree.'],
       ['District judgment was later vacated on mootness, S10; do not present it as surviving appellate merits precedent.',
        'It is a judicial restraint/vacatur of an implementing instrument, not extinguishment of every EO13998 command.'],
       [dict(kind='district_vacatur', entered='2022-04-18', time=None, timezone='court local timing not specified in researched disposition', scope='CDC mask mandate')],
       read_state='official raw PDF retained; dispositive page images58-59 read; browser primary opinion consulted; body largely scanned')
source(22, 'Acting DHS Secretary David P. Pekoske', '2021-01-27',
       '3 PDF pages =86 FR8217-8219; agency summary PDF1; embedded signed determination PDF2-3 (image pages)',
       'do hereby determine that a national emergency exists',
       ['Full embedded determination personally read as page images: January27 signature; directs TSA to implement EO13998 and assist CDC using specified49USC114 and ATSA powers.',
        'Directs interagency cooperation and countermeasures, to extent appropriate/consistent with law; no fixed expiration stated in the embedded two-page determination.',
        'This is actual exercise/implementation byJanuary27, independently corroborated by TSOB notice S23.'],
       ['Has its own statutory basis; its existence is not proof of every EO13998 deliverable or a whole-order sunset.'],
       [dict(kind='dhs_emergency_determination',signed='2021-01-27',time=None,timezone=None)],
       read_state='complete retained agency summary text and embedded determination page images personally read')
source(23, 'DHS Transportation Security Oversight Board; David P. Pekoske', '2021-04-20',
       '2 PDF pages = 86 FR 26825-26826; directive history PDF 1; scope/exceptions/ratification PDF 2',
       'The ratification was executed on April 20, 2021, and took effect on that date.',
       ['Actual aviation directives and emergency amendment issued January 31, effective February 1, 2021; Board ratified them April 20.',
        'Ratification confirms limited exemptions, retention of more protective state/local rules, and possible bounded extensions.',
        'This is concrete implementation evidence under EO13998 sections 2(a), 2(c) and 2(d).'],
       ['Does not prove all required agency consultations, written alternative safeguards, or recurring reports to the Coordinator.'],
       [dict(kind='ratification', effective_date='2021-04-20', time=None, timezone=None)])
source(24, 'FRA Acting Administrator Amitabha Bose', '2021-02-24',
       '4 PDF pages = 86 FR 11888-11891; DATES PDF 1; authority PDF 1-2; duration/signature PDF 4',
       'This emergency order is effective March 1, 2021.',
       ['FRA actually ordered mask compliance for freight and passenger rail operations using independent 49 USC 20104 emergency safety authority.',
        'Text identifies a February 12 DOT Secretary Action Memorandum and January 31 surface-transport TSA directive.',
        'Final paragraph says effective upon issuance and bears February 24 signature, while front DATES says March 1. Both must be preserved.',
        'Own duration depends on CDC order/PHE or FRA rescission/extension; does not determine whole-EO duration.'],
       ['Exact first effective date needs resolution of conflicting operative/publication wording; use February24-March1 interval for actual issuance/implementation evidence.',
        'Congressional hearing discovery references FRA enforcement cessation after district decision; no underlying FRA rescission retained here.'],
       [dict(kind='rail_mask_emergency_order', signed='2021-02-24', effective_date_front='2021-03-01', effective_wording_final='upon issuance', date_conflict=True)])
source(25, 'President Joseph R. Biden Jr.', '2023-05-09',
       '2 PDF pages = 88 FR 30889-30890; partial revocation PDF 1; effective date PDF 2',
       'Proclamation 10294, except sections 1, 6, 7, and 8 thereof, is revoked.',
       ['Ends specified parts of the separate international-air vaccination proclamation effective May12 2023 12:01a.m.EDT.',
        'Preserves enumerated sections and directs review, rather than automatically repealing all agency actions.'],
       ['Separate vaccination framework is not proof of completion of EO13998 ICVP feasibility assessment.',
        'Does not revoke EO13998.'],
       [dict(kind='partial_proclamation_revocation', effective_date='2023-05-12', time='00:01', timezone='EDT', preserved_sections=[1,6,7,8])])

# Bind immutable custody objects supplied by the root; this does not admit sources
# to the canonical registry or turn a producer proposal into a reviewed decision.
repo = HERE.parents[4]
maps=[]
for path in sorted(HERE.parent.glob('SOURCE_MAP_*.json')):
    value=json.loads(path.read_text())
    maps.extend(value.get('sources',[]))
by_url={s['url']:s for s in maps}
normalize=lambda s: re.sub(r'\s+',' ',s).strip().casefold()
for s in sources:
    item=by_url.get(s['urls'][0])
    if item:
        raw=repo/item['raw_path']
        if not raw.exists():
            # SOURCE_MAP paths are repository-relative, not research-relative.
            raw=Path.cwd()/item['raw_path']
        assert hashlib.sha256(raw.read_bytes()).hexdigest()==item['sha256']
        pdf=fitz.open(raw)
        texts=[page.get_text() for page in pdf]
        is_pdf=raw.read_bytes()[:5]==b'%PDF-'
        s.update(sha256=item['sha256'],raw_path=item['raw_path'],raw_bytes=raw.stat().st_size,
                 representation_page_count=len(pdf),raw_format='PDF' if is_pdf else 'HTML',
                 retention_state='root native acquisition custody object; locally rehashed; not registry admission',
                 text_read_state='retained text layer read; scanned-body exceptions explicitly noted in read_state; HTML pagination is a local MuPDF view, not publisher pages',
                 source_map_selected_texts=item.get('selected_texts',[]))
        if s['quoted_passage']:
            quote_key='quoted_passage_pdf_pages' if is_pdf else 'quoted_passage_local_rendered_pages'
            s[quote_key]=[i+1 for i,t in enumerate(texts) if normalize(s['quoted_passage']) in normalize(t)]
        (HERE/'texts').mkdir(exist_ok=True)
        tp=HERE/'texts'/f"{s['source_id'].replace(':','_')}.txt"
        page_label='PDF page' if is_pdf else 'Local MuPDF HTML-rendered page (not publisher pagination)'
        tp.write_text('\n\n'.join(f'=== {page_label} {i+1} ===\n{t}' for i,t in enumerate(texts)))
        s['research_text_path']=str(tp.relative_to(HERE))
        s['research_text_sha256']=hashlib.sha256(tp.read_bytes()).hexdigest()
        if s['source_id']=='HEALTH:S21':
            s['quoted_passage_pdf_pages']=[58]
            s['quote_verification']='visually transcribed from retained scanned page58; text layer has only court footer'
        if s['source_id']=='HEALTH:S22':
            s['quoted_passage_pdf_pages']=[2]
            s['quote_verification']='visually transcribed from embedded determination image PDF2'
    else:
        if s['source_id'] in ('HEALTH:S14','HEALTH:S15'):
            s['retention_state']='native acquisition attempted and failed; no raw bytes retained'
            s['acquisition_failure']=dict(reason='http_404' if s['source_id']=='HEALTH:S14' else 'blocked_by_robots_txt',
                receipt='research/excavator/machiavelli-modern-undecided-20261105/continuation-20261105/acquisition-v1/pdf-run-1/RESULTS.json')

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')

held = []
for n in (13910,13964,13991,13998):
    d=json.loads((BASE/f'overlay/v1/EO_{n}/DOSSIER.json').read_text())
    s=d['clauses'][0]['source']
    held.append(dict(source_id=f'HEALTH:ORIGINAL:{n}', instrument_id=f'EO:{n}', **s,
                     inspected='complete held original text and all PDF-page images',
                     rendered_contact_sheet=f'pages/EO_{n}_all_pages.png'))
for n,sha,url in [
    (14122,'d9a37da2e35b80bba55663d0fb093f89c380b06b4409d0f7d419de7c1118b0b7','https://www.govinfo.gov/content/pkg/FR-2024-04-17/pdf/2024-08332.pdf'),
    (14029,'eb3d5e1b1d96e89e74cac80c628b3cb98b0b92c67cc0624794cb1995e3fcb909','https://www.govinfo.gov/content/pkg/FR-2021-05-19/pdf/2021-10691.pdf'),
    (14148,'d658f5158a27f6d4a220ce2ec854bdbd596ecc841fb16884954a2e2ee39ab072','https://www.govinfo.gov/content/pkg/FR-2025-01-28/pdf/2025-01901.pdf')]:
    held.append(dict(source_id=f'HEALTH:ACTOR:{n}', instrument_id=f'EO:{n}', sha256=sha,url=url,
                     inspected='complete held text and all PDF-page images',
                     rendered_contact_sheet=f'pages/EO_{n}_all_pages.png'))

SEARCHES = [
    dict(id='health-search-hhs', subject='EO13910', queries=['site.federalregister.gov "13910" "designation"', 'HHS scarce materials extension November15 2021', 'HHS July23 2020 designation correction January19 2021'], result='Initial, modified/extended, correction and 2021 notice located; no later extension located; not exhaustive absence.'),
    dict(id='health-search-branding', subject='EO13964', queries=['site.state.gov "13964" logo', '"13964" "single logo" selection', '"13964" "report" implementation', 'site.usaid.gov "13964" marking rule'], result='Separate statutory branding act and OIG audit found; actual presidential logo selection, rulemaking initiation and EO report transmittal not located.'),
    dict(id='health-search-workforce', subject='EO13991', queries=['site.bidenwhitehouse.archives.gov "13991" "testing plan"', 'site.bidenwhitehouse.archives.gov "Office of Science and Technology Policy" "13991"', '"13991" "M-21-15"', '"13991" "M-21-25"', 'site.transportation.gov "13991" "2023"'], result='Initial/followup guidance and post-PHE department plan located. Final CDC plan submission, OSTP assessment and all consultation/report records unresolved.'),
    dict(id='health-search-travel-plans', subject='EO13998', queries=['site.state.gov "13998" "Certificates"', 'site.dhs.gov "13998" "plan"', 'site.state.gov "13998" "Canada"', '"13998" quarantine plan President', '"13998" "sea" "plan"'], result='Mandates and actual agency implementation located; exact domestic recommendations, quarantine/land/sea plans, diplomatic records and ICVP assessment not located.'),
    dict(id='health-search-travel-ending', subject='EO13998', queries=['site.federalregister.gov "Emergency Order No. 32" "rescission"', 'site.railroads.dot.gov "Emergency Order" "32" "April 18, 2022"', 'Health Freedom Defense Fund President June22 2023', 'site.cdc.gov archived orders contact information November21 2025'], result='District opinion, appellate mootness opinion, FTA enforcement response, TSA expiry and CDC later history found; appellate mandate date and full residual-rule rescission remain unverified.')]

def formal_event(n):
    actor=14029 if n==13964 else 14122
    return dict(actor=f'EO:{actor}', source_id=f'ACT:EO:{n}>EO:{actor}',
                effective_date='2021-05-14' if n==13964 else '2024-04-12',
                time=None, timezone=None, date_basis='signed date; present-tense revocation, no postponed effective clause',
                mechanism='express whole-order revocation',
                pin='EO14029 section1, PDF1 /86FR27025' if n==13964 else 'EO14122 section2, PDF1 /89FR27355')

def setrow(row, reason, refs=(), unknown=False, kind='continuing', performance=None):
    row['reason']=reason
    row['checked_through']=CUTOFF
    row['proposal_kind']=kind
    row['source_pins']=[row['clause_id'], *refs]
    row['formal_endpoint']=copy.deepcopy(CURRENT_FORMAL)
    row['state_at_cutoff_explanation']='No prospective duty remains under this revoked EO. Earlier first ending of a one-time obligation is unresolved.' if unknown else 'Prospective force of this continuing provision ended at formal revocation; historical acts and independent law are distinct.'
    row['performance']=performance or dict(state='no specific performance conclusion asserted')
    if unknown:
        row.update(state=None,end_id=None,effective_date=None,effective_date_confirmed=False)
        row['first_end_resolution']='unresolved; do not replace an unknown performance/exhaustion date with the later formal endpoint'
    else:
        row.update(state='terminated',end_id=CURRENT_FORMAL['source_id'],effective_date=CURRENT_FORMAL['effective_date'],effective_date_confirmed=True)
        row['first_end_resolution']='supported for continuing legal force; not a claim that the first implementing act occurred on the revocation date'

proposals={}
for n in (13910,13964,13991,13998):
    pending=BASE/f'coordinator-v2/EO_{n}/LIFECYCLE_PENDING.json'
    sheet=json.loads(pending.read_text())
    d=json.loads((BASE/f'overlay/v1/EO_{n}/DOSSIER.json').read_text())
    CURRENT_FORMAL=formal_event(n)
    sheet.update(agent='codex-continuation-health',approved=False,legal_cutoff=CUTOFF,
                 proposal_version='continuation-health-v1',generated_at=NOW,
                 status='producer proposal only; no adoption, review, readiness or exhaustion claim',
                 original_confirmed=True,original_pages_confirmed=True,inventory_confirmed=True)
    sheet['frozen_input']=dict(pending_sheet=str(pending.relative_to(HERE.parents[4])),
                              pending_sha256=hashlib.sha256(pending.read_bytes()).hexdigest(),
                              dossier_fingerprint=d['fingerprint'],
                              dispatch_receipt='b02/packet-v1/dispatch-continuation-health-v1.json')
    sheet['research_rationale']='Full original and held actor page-image reading, affirmative implementing instruments, primary-source ending investigation and scope-specific counterevidence. Continuous EO duties are distinguished from potentially completed one-time acts. Native decision fields are populated where supported; added formal_endpoint/performance/source_pins fields prevent a later revocation from masquerading as an unknown first performance ending. All remains unapproved.'
    sheet['search_ids']=[x['id'] for x in SEARCHES if x['subject']==f'EO{n}']
    sheet['source_notes']=['Supplemental HEALTH:Sxx references resolve in ../SOURCE_FINDINGS.json. New material must receive native retention/evidence import before approval.',
                            'Exact PDF page numbers in source index are one-based; printed page labels are separately stated.',
                            'EO14148 was read completely: it does not list EO14122 or these target orders. Revocation of EO14029 alone supplies no express restoration of EO13964.']
    sheet['whole_order_formal_endpoint']=CURRENT_FORMAL
    sheet['current_state_under_this_eo']='revoked; earliest lifecycle/performance differs by clause'
    sheet['working_text']['confirmations']=[dict(instrument_id=f'EO:{n}', sha256=d['clauses'][0]['source']['sha256'],
        text_sha256=d['clauses'][0]['source']['text_sha256'],text_path=d['clauses'][0]['source']['text_path'],grade='held_original_pdf_and_complete_text',
        complete_text_confirmed=True,identity_confirmed=True,pages_confirmed=True)]
    for actor in (14029 if n==13964 else 14122,14148):
        held_actor=next(x for x in held if x['instrument_id']==f'EO:{actor}')
        sheet['working_text']['confirmations'].append(dict(instrument_id=f'EO:{actor}',sha256=held_actor['sha256'],
            grade='held_original_pdf_and_complete_text',complete_text_confirmed=True,identity_confirmed=True,pages_confirmed=True,
            page_images=held_actor['rendered_contact_sheet']))
    for row in sheet['clauses']:
        sec=row['scope_id'].split('#')[1]
        original_clause=next(c for c in d['clauses'] if c['scope_id']==row['scope_id'])
        row['original_operative_text']=original_clause['text']
        row['original_pdf_page']=original_clause['pdf_page']
        row['original_sha256']=original_clause['source']['sha256']
        setrow(row,'This contextual, definitional or implementation-limiting provision governs the order while operative; it supplies no independent one-time deliverable or residual new duty after express whole-order revocation.',kind='context_or_scope')
        if n==13910:
            if sec=='sec1':setrow(row,'Anti-hoarding policy and explanatory delegation frame have no emergency-declaration sunset. Expiring particular HHS lists is not withdrawal of the President\'s continuing delegated authority. EO14122 section2 is the supported express ending of this EO policy.', ['HEALTH:S01','HEALTH:S02'])
            elif sec in ('sec2','sec2-a','sec2-i','sec2-i-ii'):
                setrow(row,'Continuing delegation of DPA section102/subchapterIII power (or its parent heading), not a one-time direction exhausted by the March2020 designation. Actual HHS exercises demonstrate activation. November2021 list expiry affects designated materials, not authority to designate again. No source located extinguishes this delegation earlier than EO14122 section2.', ['HEALTH:S01','HEALTH:S02','HEALTH:S18','HEALTH:S19','HEALTH:S20'],performance=dict(state='activated',first_known_instrument='2020-03-25 designation',not_first_end=True))
            elif sec=='sec2-b':setrow(row,'FEMA consultation is a continuing condition each time delegated authority is exercised. HHS notices establish exercises but do not prove every consultation. Particular notices ending does not discharge future conditional consultation; express revocation ends the EO condition prospectively.', ['HEALTH:S01','HEALTH:S02'],performance=dict(state='individual consultations not verified'))
            elif sec=='sec2-c':setrow(row,'As-necessary rule adoption/revision is an open continuing instruction, not a fixed deliverable. The initial HHS notice expressly disclaims being a DPA regulation. No separate final regulation or rescission was identified; that neither proves inaction nor converts the notice into a rule. EO14122 removes the future EO instruction.', ['HEALTH:S01','HEALTH:S02'],performance=dict(state='designation activity verified; separate rules unresolved'))
            elif sec=='sec3':setrow(row,'Periodic reconsideration and prompt withdrawal when no longer necessary are recurring duties. July2021 review removed most categories and extended four, affirmative performance rather than mere lapse of time. Expiration on November15 affects that designation; does not exhaust review of future designations under an otherwise continuing delegation.', ['HEALTH:S02','HEALTH:S19','HEALTH:S20'],performance=dict(state='actual review/removal shown',date='2021-07-01',continuing=True))
        elif n==13964:
            if sec=='sec1':setrow(row,'American-aid branding policy continued until EO14029 section1 expressly revoked the order. Independent FAA/USAID branding requirements are not this presidential policy and do not automatically expire with it.', ['HEALTH:S09','HEALTH:S12'])
            elif sec=='sec2':setrow(row,'Section2(a), embedded in this inventory row, requires initiation of notice-and-comment rulemaking within120 days and implementation after finalization. No primary initiation/finalization instrument located. First performance or exhaustion remains unresolved; April9 deadline alone proves neither. Outer formal endpoint is May14.', ['HEALTH:S09','HEALTH:S12'],unknown=True,kind='one_time_and_contingent_followup',performance=dict(state='unresolved',deadline='2021-04-09',needed='State/USAID notice of proposed marking regulations, final rule and implementation records'))
            elif sec=='sec2-b':setrow(row,'Parent framework for regulation-related single-logo rules has no independent one-time performance; particular logo-selection performance is separately unresolved in sec2-i. Framework\'s future legal force ends May14 revocation.', ['HEALTH:S09','HEALTH:S12'],kind='context_or_scope')
            elif sec=='sec2-i':setrow(row,'One-time presidential single-logo selection was due January9,2021. No actual selection instrument located. Existing USAID identity and the January13 statute do not establish that selection. A missed or passed deadline is not legal exhaustion, nor proof selection never happened.', ['HEALTH:S09','HEALTH:S12'],unknown=True,kind='one_time',performance=dict(state='unresolved',deadline='2021-01-09',needed='Presidential selection decision identifying the single logo'))
            elif sec=='sec2-i-ii':setrow(row,'Display requirement is continuing for covered future aid materials, subject to explicit exclusions for administrative/nonproject items and completed overseas products. No source establishes all categories were exempted or that the EO rule was wholly exhausted before revocation. Existing USAID markings are independent-rule performance, not proof of EO single-logo selection.', ['HEALTH:S09','HEALTH:S12'],performance=dict(state='EO-specific implementation unresolved'))
            elif sec in ('sec2-c','sec2-d'):setrow(row,'The120-day instruction includes an ongoing identification/agency-logo restriction for future covered assistance, plus amendments/rescissions of inconsistent guidance. Continuous marking component ends at express revocation May14. Specific agency guidance performance remains unresolved; do not equate April9 with completion.', ['HEALTH:S09','HEALTH:S12'],performance=dict(state='one-time guidance component unresolved',deadline='2021-04-09',continuing_marking_component='revoked 2021-05-14'))
            elif sec=='sec2-e':setrow(row,'Conditional written waiver authority and delegation-level limits operate whenever the single logo is required; they are not exhausted by a single waiver or by lack of a located waiver. Future EO waiver framework ends with May14 revocation. No particular written waiver or redelegation was located.', ['HEALTH:S09','HEALTH:S12'],performance=dict(state='individual written waivers/delegations unresolved'))
            elif sec=='sec3':setrow(row,'Initial report within180days plus annual reports thereafter is a recurring obligation. Whole recurring duty ends by revocation May14, before the June8 initial deadline. Whether an early initial report was submitted remains unknown; the OIG statutory audit to Congress is a different report. No never-activated or deadline-as-ending inference.', ['HEALTH:S09','HEALTH:S12'],performance=dict(state='actual early initial report unresolved',first_deadline='2021-06-08',recurrence='annually thereafter',formal_revocation_before_first_deadline=True))
        elif n==13991:
            if sec=='sec1':setrow(row,'Science-based federal workplace safety policy is broader than vaccination. EO14099 removes14042/14043 vaccine-based duties only; DOT explicitly retained13991 after the PHE ended. EO14122 is the express whole-order endpoint.', ['HEALTH:S03','HEALTH:S13','HEALTH:S16','HEALTH:S17'])
            elif sec=='sec2':setrow(row,'Section2(a) requires agency action to require compliance with evolving CDC guidelines, not a single fixed mask rule. Initial guidance and completed plans show implementation, while DOT continued revised measures afterMay2023. No whole duty ending follows from a guideline change, vaccine injunction or PHE end; EO14122 ends the future EO instruction.', ['HEALTH:S03','HEALTH:S04','HEALTH:S13','HEALTH:S17'],performance=dict(state='actual implementation corroborated',interval=['2021-01-24','2021-06-10'],later='DOT plan August24,2023'))
            elif sec=='sec2-b':
                setrow(row,'OMB/Task Force M-21-15 affirmatively supplies agency model safety principles onJanuary24,2021 and identifies OPM/GSA-cochaired Task Force. M-21-25 corroborates that initial guidance and later implementation. This proves actual issuance byJanuary24, not absence of an earlier sufficient issuance or every named official\'s separate performance. Earliest full completion is therefore retained as a factual interval/question, not an exact first-ending date; ongoing Task Force guidance is distinct.', ['HEALTH:S03','HEALTH:S04'],unknown=True,kind='one_time_initial_issuance',performance=dict(state='actual guidance issued; earliest full completion not fixed',document_date='2021-01-24',performance_window=['2021-01-20','2021-01-24'],named_officials='OMB/OPM/GSA coordination evidenced through TaskForce; no separate universal performance assumption'))
            elif sec=='sec2-c':setrow(row,'Prompt consultations cover multiple officials, employee/unions, contractors and other parties as appropriate. Guidance existence does not establish all needed consultations or their dates. No underlying consultation record located; unknown first completion retained, with outer express revocation separately recorded.', ['HEALTH:S03','HEALTH:S04'],unknown=True,kind='prompt_consultations',performance=dict(state='specific consultations unresolved'))
            elif sec=='sec2-d':setrow(row,'Agency exception authority and written alternative-safeguard conditions are ongoing and conditional. Model guidance does not prove every exception determination. EO13991 basis ends by express revocation; independently authorized safeguards and historical exceptions require separate analysis.', ['HEALTH:S03','HEALTH:S13'],performance=dict(state='guidance known; individual written exceptions unresolved'))
            elif sec=='sec2-e':setrow(row,'Review of authorities and seeking to provide masks are resource- and law-limited. Initial review completion is unresolved, while future mask provision is a continuing conditional task; no fixed emergency sunset or earlier full discharge is shown. Outer EO instruction ends April12,2024.', ['HEALTH:S03','HEALTH:S13'],performance=dict(state='initial review unresolved; ongoing provision conditional'))
            elif sec=='sec2-f':setrow(row,'Coordination and regular agency progress updates recur; an initial submission cannot exhaust the entire clause. Agency plans and later updates corroborate implementation without establishing each report. Coordinator position and EO13991 both terminate under EO14122; transferred duties in surviving orders do not silently restore this revoked EO.', ['HEALTH:S03','HEALTH:S04','HEALTH:ACTOR:14122'],performance=dict(state='implementation corroborated; exact recurring reports unresolved'))
            elif sec=='sec3':setrow(row,'HHS engagement with state/local/tribal/territorial officials is an as-appropriate continuing instruction to encourage nonfederal masking and safeguards. No source located makes completion of a particular campaign an end of future engagement. Prospective EO obligation ends at express revocation.', ['HEALTH:S03','HEALTH:S17'],performance=dict(state='particular external engagement records unresolved'))
            elif sec=='sec3-b':setrow(row,'Prompt identification and communication of incentive/support options is a distinct one-time deliverable. Federal workplace guidance does not demonstrate communication of the required nonfederal masking options. Actual options record/transmittal not located; first exhaustion remains unknown, despite later formal revocation.', ['HEALTH:S03'],unknown=True,kind='one_time_options',performance=dict(state='unresolved'))
            elif sec.startswith('sec4'):
                if sec=='sec4-f':setrow(row,'Prompt reports by every31USC901(b)agency are a specific performance question. M-21-15 directed submissions byJanuary29 and M-21-25 confirms plans completed/implemented byJune10. Neither identifies every section4(f) report/date. Strong performance interval evidence retained without fabricating exact universal first completion.', ['HEALTH:S03','HEALTH:S04'],unknown=True,kind='one_time_reports',performance=dict(state='substantial corroboration; exact all-agency completion unresolved',interval=['2021-01-24','2021-06-10']))
                elif sec=='sec4-a':setrow(row,'Task Force was self-executingly established January20,2021; M-21-15 confirms actual operation byJanuary24. Institutional authorization is continuing rather than a separate report deliverable. Guidance continued under13991 after vaccine changes; revocation ends this EO-created institutional authorization April12,2024.', ['HEALTH:S03','HEALTH:S04','HEALTH:S13','HEALTH:S16','HEALTH:S17'],performance=dict(state='self-executing establishment and actual operation',established='2021-01-20',operation_confirmed_by='2021-01-24'))
                elif sec in ('sec4-e','sec4-i-dup2','sec4-i-ii-dup2','sec4-i-iii-dup2','sec4-i-iv-dup2','sec4-v-dup2','sec4-v-vi-dup2','sec4-v-vii-dup2','sec4-v-viii-dup2','sec4-v-ix-dup2','sec4-x','sec4-x-xi','sec4-x-xii'):
                    setrow(row,'This subject belongs to the Task Force\'s expressly ongoing guidance mission. Initial model principles, subsequent guidance and revised agency plans establish activity, not exhaustion of the subject or a requirement to preserve an obsolete precaution. Vaccine-only revocation and PHE ending do not extinguish the broader mission; EO14122 does.', ['HEALTH:S03','HEALTH:S04','HEALTH:S13','HEALTH:S16','HEALTH:S17'],performance=dict(state='actual guidance activity established; full topic-by-topic record not reconstructed'))
                else:setrow(row,'Task Force membership, designee/subgroup, administration or parent provision remains incident to its continuing EO13991 mission. Actual initial guidance confirms activation; no distinct one-time submission is imposed here. EO14122 removes this institutional basis. Other saved agency powers are separate.', ['HEALTH:S03','HEALTH:S04','HEALTH:S16'])
            elif sec=='sec5':setrow(row,'Develop-and-submit federal testing plan is a distinct one-time duty with specified contents. M-21-15 says CDC is developing/submitting it, not that final delivery has occurred. Later testing protocols cannot alone establish this required plan submission. Exact final plan/transmittal not located; first exhaustion unknown.', ['HEALTH:S03','HEALTH:S04','HEALTH:S13'],unknown=True,kind='one_time_plan',performance=dict(state='development acknowledged byJanuary24; final submission unresolved',needed='CDC plan and submission to COVID19ResponseCoordinator'))
            elif sec=='sec6':setrow(row,'OSTP assessment of availability of research grants, with named interagency consultations, is a specific assessment rather than all subsequent mask research. No assessment/transmittal or consultation record located. Existence of federal COVID research grants does not prove this assessment; first performance/exhaustion unresolved.', ['HEALTH:S03'],unknown=True,kind='one_time_assessment',performance=dict(state='unresolved',needed='OSTP/NSTC assessment and consultation records'))
            elif sec=='sec7-b':setrow(row,'Consultation with legislative/judicial branch officials plus requested technical assistance is continuing/conditional in part. No located specific consultation record proves universal performance, but one consultation could not exhaust future requested assistance. Prospective EO direction ends at express revocation.', ['HEALTH:S03'],performance=dict(state='specific consultation/assistance records unresolved'))
        elif n==13998:
            if sec=='sec1':setrow(row,'Broad travel safety policy is not textually conditioned on the section319PHE remaining declared. Actual CDC/TSA/FRA actions have their own authorities and terms. Specific mask/testing measures ending does not repeal this broader policy; EO14122 does.', ['HEALTH:S05','HEALTH:S07','HEALTH:S10','HEALTH:S23','HEALTH:S24','HEALTH:S25'])
            elif sec=='sec2-a' or sec in ('sec2-i','sec2-i-ii','sec2-i-iii','sec2-i-iv','sec2-v','sec2-v-vi'):
                setrow(row,'Immediate agency action to impose CDC-consistent masks was actually implemented through January29CDC order, January31TSA directives and February24/March1FRA action, across the listed modes. This supports performance, but exact first full discharge of the multiagency action obligation is not fixed by one instrument. April18,2022district vacatur restrains CDC order, May11,2023ends that order by terms, neither equals this clause\'s universal first performance ending. Outer EOrevocation remainsApril12,2024.', ['HEALTH:S05','HEALTH:S10','HEALTH:S11','HEALTH:S15','HEALTH:S21','HEALTH:S23','HEALTH:S24'],unknown=True,kind='immediate_multiagency_implementation',performance=dict(state='affirmative regulatory implementation',known_instrument_interval=['2021-01-27','2021-03-01'],exact_first_full_performance='unresolved'))
            elif sec=='sec2-b':setrow(row,'As-appropriate interested-party consultation accompanies implementation. Actual CDC/TSA/FRA activity does not establish all required consultations or their first completion. Conditional consultation remains for further lawful implementation until formal revocation; specific consultation chronology unresolved.', ['HEALTH:S05','HEALTH:S23','HEALTH:S24'],performance=dict(state='interagency consultation in FRA text established; all interested-party records unresolved'))
            elif sec=='sec2-c':setrow(row,'Continuing exception authority requires safeguards and written documentation. CDC and TSA instruments contain exceptions, affirmative activity, but do not establish all agency determinations/safeguards. Removal of CDC mandate does not by itself repeal this conditional EO authority before whole revocation.', ['HEALTH:S05','HEALTH:S23'],performance=dict(state='categorical exceptions in implementing instruments established; individual determinations unresolved'))
            elif sec=='sec2-d':setrow(row,'Nonpreemption of more protective public-health measures is a continuing limitation on agency implementation. CDC/TSA/FRA texts affirm it. It is not a one-time report and cannot be treated as exhausted by issuance of one order; prospective EO limit ends with express revocation, without wiping out independently applicable local law.', ['HEALTH:S05','HEALTH:S23','HEALTH:S24'],performance=dict(state='nonpreemption reflected in implementing instruments'))
            elif sec in ('sec2-e','sec2-c-dup2'):
                setrow(row,'Single section2(e) coordination/progress provision, split by frozen parser: sec2-c-dup2 begins the continuation referring back to subsection(c), not a second exceptions subsection. First update dueJanuary28,2021and regular updates thereafter. Recurring duty is not exhausted by initial update; no complete report archive located. EOrevocation ends future coordination, while EO14122 section3 endsCoordinatorposition.', ['HEALTH:ACTOR:14122','HEALTH:S05','HEALTH:S23'],performance=dict(state='actual implementation established; report deliveries unresolved',first_deadline='2021-01-28',recurrence='regularly thereafter'))
                row['inventory_interpretation']='Read EO:13998#sec2-e and #sec2-c-dup2 together as one section2(e); preserve frozen IDs pending native correction.'
            elif sec=='sec3-a':setrow(row,'Domestic additional-measures recommendations toCoordinator are a specific prompt deliverable, distinct from mask mandates and from mere DOT implementation-report discovery. Exact recommendations/transmittal not located. First completion/exhaustion unresolved; formal revocation is recorded separately.', ['HEALTH:S14','HEALTH:S24'],unknown=True,kind='one_time_recommendations',performance=dict(state='unresolved',needed='DOT/DHS recommendations transmitted toCoordinator'))
            elif sec=='sec3-b':setrow(row,'Interested-party engagement implementing additional domestic-measures recommendations is conditional. No universal consultation record located; actual mask-rule consultations are not automatically this separate process. Future EO engagement direction ends with formal revocation.', ['HEALTH:S14'],performance=dict(state='specific domestic additional-measures engagement unresolved'))
            elif sec=='sec4':setrow(row,'Prompt identification and communication of options to support nonfederal transit masking/distancing is a distinct deliverable. General FTA bulletins and federal mask mandates do not establish the required options communication byCoordinator. No exact options record located; first exhaustion unknown.', ['HEALTH:S11','HEALTH:S14'],unknown=True,kind='one_time_options',performance=dict(state='unresolved'))
            elif sec in ('sec5-a','sec5-i','sec5-i-ii'):
                setrow(row,'International-travel policy is feasible negative testing and other CDCguideline compliance, including recommended quarantine. January25CDC order implemented testing, rescissionJune12,2022ended that condition; independent vaccination and contact-information measures followed separate paths. Neither ending repeals the broader feasible policy as a whole, which loses EOforceApril12,2024.', ['HEALTH:S06','HEALTH:S07','HEALTH:S08','HEALTH:S25'],performance=dict(state='actual testing implementation; separate residual instruments identified'))
            elif sec=='sec5-i-dup2':setrow(row,'Four-factor review of January12CDC air-testing order within14days, with further appropriate regulatory action. January25superseding order demonstrates real regulatory performance, but does not explicitly establish all four considerations or required coordination/assessment completion. February4deadline supplies no performance inference. Exact first completion unknown.', ['HEALTH:S06','HEALTH:S07'],unknown=True,kind='one_time_assessment_and_regulation',performance=dict(state='regulatory revision January25confirmed; full assessment unresolved',deadline='2021-02-04'))
            elif sec=='sec5-i-ii-dup2':setrow(row,'Quarantine/self-isolation implementation plan must reachPresident throughCoordinator and identify tools/mechanisms. CDC recommendations or later air-testing/vaccination orders are not the plan transmittal. No actual plan/submission located; first performance/exhaustion unresolved.', ['HEALTH:S06','HEALTH:S08'],unknown=True,kind='one_time_plan',performance=dict(state='unresolved'))
            elif sec=='sec5-i-iii':setrow(row,'State must seek foreign/international stakeholder consultation to establish safe-travel guidelines addressing seven specified subjects. Later international rules show activity but do not demonstrate every required consultation or completed guidelines. Continuing consultation instruction ends prospectively at express revocation.', ['HEALTH:S06','HEALTH:S08','HEALTH:S25'],performance=dict(state='specific diplomatic/international consultation records unresolved'))
            elif sec=='sec5-c':setrow(row,'Immediate Canada/Mexico diplomatic outreach plus multiagency land-port plan toPresident within14days are distinct tasks. Later border restrictions or vaccination rules alone do not prove the outreach/plan. Exact diplomatic and plan records not located; February4deadline is not an ending. First full completion remains unresolved.', ['HEALTH:S08','HEALTH:S25'],unknown=True,kind='diplomatic_outreach_and_one_time_plan',performance=dict(state='unresolved',deadline='2021-02-04'))
            elif sec=='sec5-d':setrow(row,'CoastGuard/DHS sea-port health plan toPresident within14days requires HHS/CDCconsultation and operational considerations. Neither conveyance maskorder nor cruise measures alone establish this plan. Exact plan/transmittal not located; first completion unknown.', ['HEALTH:S05','HEALTH:S08'],unknown=True,kind='one_time_plan',performance=dict(state='unresolved',deadline='2021-02-04'))
            elif sec=='sec5-e':setrow(row,'Three-agency assessment of linking COVIDvaccination toICVP and producing electronicICVPs is distinct from ordinary proof-of-vaccination requirements or digital credential programs. No actual feasibility assessment located. First performance/exhaustion unknown; Proclamation10575 is not the assessment or an EO13998 revocation.', ['HEALTH:S08','HEALTH:S25'],unknown=True,kind='one_time_assessment',performance=dict(state='unresolved'))
            elif sec=='sec5-f':setrow(row,'National-security/domestic-policy consultation, coordination and agency progress updates within7days and regularly thereafter are recurring. No complete report/transmittal archive located. Initial deadlineJanuary28does not end the obligation; EO14122 ends future EOcoordination while separately terminatingCoordinatorpositions.', ['HEALTH:ACTOR:14122','HEALTH:S06','HEALTH:S08'],performance=dict(state='regulatory activity established; exact recurring updates unresolved',first_deadline='2021-01-28',recurrence='regularly thereafter'))
    if n==13991:
        topic_pins={
            'sec4-i-dup2':('testing protocols','M-21-15 PDF5-7; final section5 plan still not established'),
            'sec4-i-ii-dup2':('case investigation/contact tracing','M-21-15 PDF5-6'),
            'sec4-i-iii-dup2':('distancing/occupancy','M-21-15 PDF7-8; M-21-25 PDF3,5'),
            'sec4-i-iv-dup2':('equipment/PPE','M-21-15 PDF5; DOT2023 PDF6-7'),
            'sec4-v-dup2':('air filtration','M-21-15 PDF8; DOT2023 PDF12 /printed11'),
            'sec4-v-vi-dup2':('cleaning/disinfection','M-21-15 PDF7; M-21-25 PDF19'),
            'sec4-v-vii-dup2':('commuting/telework','M-21-15 PDF4; M-21-25 PDF6-10'),
            'sec4-v-viii-dup2':('technology to support telework','M-21-25 PDF2,6,11,13,19-20; exact compliance by all agencies not asserted'),
            'sec4-v-ix-dup2':('vaccination prioritization/distribution/administration','M-21-25 PDF1-3,5 discusses vaccination; EO14043 adds separate mandate. A complete prioritization/distribution guidance record not established'),
            'sec4-x':('external coordination','M-21-15 PDF5-6 local health coordination; M-21-25 PDF7-8,10,18 labor engagement. Complete all-stakeholder guidance record not established'),
            'sec4-x-xi':('management infrastructure','M-21-15 PDF3-4 coordination team; M-21-25 PDF2; DOT2023 PDF4-5'),
            'sec4-x-xii':('exemptions','M-21-15 PDF5,7 exceptions; DOT2023 PDF6-7')}
        for row in sheet['clauses']:
            sec=row['scope_id'].split('#')[1]
            if sec in topic_pins:
                topic,pins=topic_pins[sec]
                row['performance']=dict(state='affirmative topic-related guidance; no exhaustion of expressly ongoing mission',topic=topic,page_pins=pins)
    sheet['savings']=dict(state='independent_law_and_historical_effects_distinguished',source_id=f'CLAUSES:EO:{n}#'+('sec8-i' if n==13991 else 'sec6-i' if n==13998 else 'sec4-i'),
        reason='General savings clauses preserve agency statutory powers and OMB functions; appropriations/applicable-law and no-private-right limits do not create a new prospective duty after revocation. Revocation alone does not automatically rescind every independently grounded rule or historical act. See residual analysis and source findings.')
    sheet['unresolved_material_gaps']={
        13910:['Whether any valid intermediate designation fills January20-31,2021; reconcile exact publication/correction dates and any later extension afterNovember15,2021.', 'Separate implementing regulations and actual FEMA-consultation records; no automatic PHE/national-emergency sunset inference.', 'Native retention/evidence import of new HHS notices before approval.'],
        13964:['Presidential single-logo selection record, State/USAID notice-and-comment initiation/finalization, agency guidance amendments and written waivers.', 'Actual early EOsection3 report toPresident, if any; statutory OIG audit is a distinct document.', 'Later treatment of specific branding regulations, including changes after2025, requires instrument-specific review; do not infer restored EO13964 from EO14029revocation.'],
        13991:['CDC final federal testing plan and submission; OSTP/NSTC research-grant assessment and consultations.', 'All section4(f) agency report deliveries, prompt consultations and external options communications; substantial plan evidence does not fix every first date.', 'M-21-15 establishes actual guidance issuance byJanuary24; verify earliest sufficient guidance and named officials\' exact performance before fixing section2(b) first ending. Native import of all supplemental sources remains required.'],
        13998:['Exact domestic recommendations and nonfederal-support options; quarantine, land-port and sea-port plan transmittals; ICVP feasibility assessment; diplomatic consultations and recurring report deliveries.', 'Appellate mandate issuance date; separately dated FRA rescission/cessation and complete TSA directive chain rather than transplanting CDCvacatur to every instrument.', 'Read queued DOT24monthreport; resolve FRA February24issuance/March1DATES conflict; retain original residual contact-information rescission before exact ending approval.']
    }[n]
    proposals[n]=sheet
    dump(HERE/f'EO_{n}/LIFECYCLE_PROPOSAL.json',sheet)

findings=dict(schema='eo-health-continuation-source-findings/v1',producer='codex-continuation-health',approved=False,
              generated_at=NOW,legal_cutoff=CUTOFF,scope=['EO:13910','EO:13964','EO:13991','EO:13998'],
              packet_sha256='4e4b8c8952d2f3664279d4d201e4ef9e0b79b3fd3aeb876310b53ef75446d637',
              dispatch_receipt='b02/packet-v1/dispatch-continuation-health-v1.json',
              instruction_basis=['AGENTS.md / HANDOFF and README and KEAN owner notes', 'jobs/claim-kit/AGENT_PROTOCOL.md',
                                 'Owner evidence-not-convenience and report-deadline rulings'],
              sources=sources,held_original_and_actor_pins=held,searches=SEARCHES,
              rejected_inferences=[
                  'EO14148 revokes EO14122: false; complete original list does not name14122.',
                  'Revoking14029/14003 automatically restores every previously revoked target: no express restoration shown.',
                  'A deadline or absence of a located public report proves completion, nonperformance or automatic legal termination.',
                  'EndingPHE ends every COVIDEO; ending one designation or mask/test rule ends the parent delegation or all EO duties.',
                  'EO14099 revokes13991; its text revokes14042/14043, not13991.',
                  'District mask-vacatur decree terminatesEO13998 or remains binding appellate merits precedent after mootness vacatur.'],
              inventory_issue=dict(instrument_id='EO:13998',scopes=['EO:13998#sec2-e','EO:13998#sec2-c-dup2'],
                                   finding='Frozen second scope is a page-break continuation of section2(e), not new subsection(c). IDs preserved; interpret together.',
                                   source_pin='original PDF1-2 /86FR7205-7206'),
              runtime=dict(producer_model='inherited Codex model; exact runtime model identifier not exposed',
                           started_at='2026-11-05 (before compacted research checkpoint; exact start not recoverable)',
                           checkpoint_at=NOW,cash_usd=None,tokens=None,
                           cost_note='Actual billing/token telemetry unavailable; no inferred spend.'),
              outcome=dict(proposals=4,clauses=sum(len(x['clauses']) for x in proposals.values()),
                           native_nonnull_states=sum(c['state'] is not None for p in proposals.values() for c in p['clauses']),
                           unknown_first_end_rows=sum(c['state'] is None for p in proposals.values() for c in p['clauses']),
                           status='Substantive producer proposals; no canonical adoption or review; raw source imports still required.'))
findings['source_maps_read']=[dict(path=str(p.relative_to(repo)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(HERE.parent.glob('SOURCE_MAP_*.json'))]
findings['review_gates']=dict(producer_approved=False,source_acceptance=False,status_adoption=False,readiness=False,exhaustion=False)
dump(HERE/'SOURCE_FINDINGS.json',findings)
for n,sheet in proposals.items():
    lines=[f'# EO{n} lifecycle case journal', '',
           'Producer proposal only. Approved: **false**. Legal cutoff: **2026-10-14**.', '',
           f"Formal whole-order endpoint: **{sheet['whole_order_formal_endpoint']['effective_date']}**, {sheet['whole_order_formal_endpoint']['actor']}. This does not replace unknown earlier first performance endings.", '',
           'Complete frozen inventory is retained. Source IDs resolve in `../SOURCE_FINDINGS.json`; native actor/CLAUSES IDs refer to the frozen dossier. No canonical scientific state has been changed.', '']
    for row in sheet['clauses']:
        lines += [f"## {row['scope_id']}", '',
                  f"Original PDF page {row['original_pdf_page']}: "+re.sub(r'\s+',' ',row['original_operative_text']), '',
                  f"Native proposal state: `{row['state']}`; first-end field: `{row['effective_date']}`; mechanism/type: {row.get('mechanism',row['proposal_kind'])}.", '',
                  row['reason'],'', 'Performance: '+json.dumps(row['performance'],ensure_ascii=False)+'.','',
                  'Pins: '+', '.join(row['source_pins'])+'.','']
    lines += ['## Residuals and open records','',sheet['savings']['reason'],'']
    lines += ['- '+gap for gap in sheet['unresolved_material_gaps']]
    (HERE/f'EO_{n}/CASE_JOURNAL.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(findings['outcome'],indent=2))
