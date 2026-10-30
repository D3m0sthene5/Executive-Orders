"""Build exact-span receipt from the reviewed, Git-verified connector input cache.

This script does not retrieve sources or perform legal review. If _inputs.json is
absent, it reads the same pinned files from the checkout and verifies their blobs.
"""
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
INPUTS = {
    'owner_amendment': ('research/readiness/owner_rulings/2026-10-21-strike-and-insert.md', '7a9e6b7ab7ccb62633e1664b802caccc7480e5f3'),
    'owner_report': ('research/readiness/owner_rulings/2026-10-21-report-deadline.md', '1a7372b4ab618dab5e6fa240c32d79a765f94298'),
    'owner_until': ('research/readiness/owner_rulings/2026-10-21-until-and-further-exempt.md', 'c1230a11030f529fbaa8c3722db94599433d0b4f'),
    'owner_transcription': ('research/readiness/owner_rulings/2026-10-21-transcription-as-text.md', '6f28ba7fd3bc81af9fd82064c2367db014771d43'),
    'owner_unnamed': ('research/readiness/owner_rulings/2026-10-21-unnamed-instruments.md', 'f898bb475c84b2f13e563040653b2cf988c462a9'),
    'memo': ('research/excavator/claude-nira-sweep-2026-10-29/SHARED_ANALYSIS.md', '983883fb9b4cf26cc579a76b9f1083e50368dfe6'),
    'propositions': ('research/excavator/claude-nira-sweep-2026-10-29/review-shared/PROPOSITIONS_v2_SOL.md', '7e0dfc1780c31ae08cf8ea9eeef71c3e42b09178'),
    'owner': ('research/readiness/owner_rulings/2026-10-28-evidence-not-convenience.md', 'dc23159ce2cc6843fd0527429427b79e7253e3d3'),
    'resolution': ('jobs/astra-source-retention/output/pages/98e35c567ea86208eadc55548eb7a5ea5f1edd92d8116c9e4c4847da1bab0305/d19d25fe35e98a1ade9b1fd03ed8751743502c5d1005a61ca97974657cf08386/selected-pages.txt', 'da46e27f4cd40c9bf8607200d7e512147a6a9309'),
    'nira': ('jobs/astra-source-retention/output/pages/c9fcb1910615c2d9b677700a8fa96edc8da2cfdca204ed04f51e5f8dde99ebe7/6fca72c4672ad8ad9a53ad398017a587b67e2950dd8f5bec674c7a0f3c25b446/selected-pages.txt', '91270c35d5abc30e49c02ce438e5fcf8a653b308'),
    'schechter': ('jobs/astra-source-retention/output/pages/881859243da21bea9a6026dd5895230e0d8c3c4416afdbe41e50ad21eee10015/ad2b3136c546eeb5f588d031acb575049be56b5341b922af2fe2e152787e4fa2/selected-pages.txt', '1768095ee3157e72809acb0828e41d9384aebf93'),
    'eo7075': ('jobs/app-executive-orders/output/texts/executive-order-7075-reorganizing-the-nra.txt', '6873f0572cb18836389bfeada72b3c8a282747db'),
    'eo7252': ('jobs/app-executive-orders/output/texts/executive-order-7252-terminating-the-national-recovery-administration-and-transferring.txt', '2d6c5b9086841b74d0675c813dc30005ed6edde0'),
}
cache = json.loads((HERE / '_inputs.json').read_text()) if (HERE / '_inputs.json').exists() else None
texts, sources, spans = {}, [], []
for key, (path, blob) in INPUTS.items():
    if cache and path in cache:
        row = cache[path]
        raw = row['content'].encode('utf-8')
        # Connector's full content is checked against its actual blob, never an
        # inferred text hash or a hash inferred from a PDF filename.
        blob = row['sha']
    else:
        raw = (ROOT / path).read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    assert actual == blob, (key, actual, blob)
    texts[key] = raw.decode('utf-8')
    sources.append(dict(id=key, path=path, sha256=hashlib.sha256(raw).hexdigest(), git_blob_sha1=actual,
                        bytes=len(raw), chars=len(texts[key]), git_blob_verified=True,
                        role='review_target' if key in ('memo','propositions') else 'owner_instruction' if key.startswith('owner') else 'held_evidence'))

def span(key, ident, start, end, label, include_end=False):
    t = texts[key]
    a = t.index(start)
    b = t.index(end, a) + (len(end) if include_end else 0)
    assert b > a
    q = t[a:b]
    spans.append(dict(id=ident, source_id=key, label=label, char_start=a, char_end=b,
                      offset_convention='zero_based_unicode_half_open', quote=q,
                      quote_sha256=hashlib.sha256(q.encode()).hexdigest()))

span('resolution','R1','[CHAPTER 246.] JOINT RESOLUTION','Approved, June 14, 1935.','49 Stat. 375, chapter 246, sections 1-2 and proviso',True)
span('nira','N2C','(c) This title shall cease','CODES OF FAIR COMPETITION','48 Stat. 196, section 2(c)')
span('nira','N3ABCD','Sec . 3. (a)','(e) On his own motion','48 Stat. 196, sections 3(a)-(d)')
span('nira','N3F4A','(f) When a code of fair competition','(b) Whenever the President','48 Stat. 197, sections 3(f), 4(a)')
span('nira','N5','Sec . 5. While this title','Nothing in this Act','48 Stat. 198, section 5')
span('nira','N7BC','(b) The President shall, so far as practicable','(d) As used in this title','48 Stat. 199, section 7(b)-(c)')
span('nira','N10','Sec . 10. (a)','TITLE II—PUBLIC WORKS AND CONSTRUCTION','48 Stat. 200, section 10(a)-(b)')
span('schechter','S_DATE','No. 854. Argued','1. Extraordinary','295 U.S. 495, case heading')
span('schechter','S_DELEGATION','To summarize and conclude upon this point:','Third. The question','295 U.S. 541-542, section 3 delegation holding')
span('schechter','S_JUDGMENT','On both the grounds we have discussed','Mr . Justi ce Cardozo','295 U.S. 551, actual disposition')
for key in ('owner_amendment','owner_report','owner_until','owner_transcription','owner_unnamed','eo7075','eo7252'):
    q=texts[key]
    spans.append(dict(id=key.upper(),source_id=key,label='Whole owner ruling' if key.startswith('owner') else 'Whole held APP transcription; not original authentication',char_start=0,char_end=len(q),offset_convention='zero_based_unicode_half_open',quote=q,quote_sha256=hashlib.sha256(q.encode()).hexdigest()))
for m in re.finditer(r'^P(\d+)\. [\s\S]*?(?=\nP\d+\.|\n## Held sources|\Z)',texts['propositions'],re.M):
    q=m.group()
    spans.append(dict(id='PROP_P'+m[1],source_id='propositions',label='Exact reviewed proposition P'+m[1],char_start=m.start(),char_end=m.end(),offset_convention='zero_based_unicode_half_open',quote=q,quote_sha256=hashlib.sha256(q.encode()).hexdigest()))

evidence=dict(schema='independent-shared-source-review-evidence/v1',input_commit='f9c6d806ad059dcad7875ab3708715f20ea386df',
              sources=sources,spans=spans,pdf_pages_inspected=True,pdf_hashes_newly_verified=True,
              source_acquisition='Existing GitHub connector, exact pinned repository files; no external source acquisition')
pdf_checks=[]
for digest, pages, printed in [
    ('98e35c567ea86208eadc55548eb7a5ea5f1edd92d8116c9e4c4847da1bab0305',[1],['49 Stat. 375']),
    ('c9fcb1910615c2d9b677700a8fa96edc8da2cfdca204ed04f51e5f8dde99ebe7',[2,3,4,5,6],['48 Stat. 196-200']),
    ('881859243da21bea9a6026dd5895230e0d8c3c4416afdbe41e50ad21eee10015',[1,47,48,57],['295 U.S. 495','295 U.S. 541-542','295 U.S. 551'])]:
    path='jobs/astra-source-retention/output/pdf/'+digest+'.pdf'
    raw=(ROOT/path).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==digest
    pdf_checks.append(dict(path=path,sha256=digest,bytes=len(raw),pages_visually_examined=pages,printed_pages=printed,
                           method='Reviewer inspected rendered primary page PNGs at 115dpi; source bytes independently rehashed'))
evidence['primary_pdf_checks']=pdf_checks
(HERE/'EVIDENCE.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n')

verdicts=[]
def verdict(p,v,reason,ev,correction=None,contradiction=None):
    x=dict(proposition=p,verdict=v,reason=reason,evidence_ids=ev,proposition_span_id='PROP_'+p)
    if correction: x['corrected_wording']=correction
    if contradiction:
        assert len(contradiction.split())<25
        x['contradicting_passage_under_25_words']=contradiction
    verdicts.append(x)
verdict('P1','upheld','The chapter, approval date and substituted sunset are explicit in the held statute.',['R1','N2C'])
verdict('P2','upheld','The statute says hereby repealed and provides no delayed effective date.',['R1'])
verdict('P3','upheld_with_correction','The FTC and criminal provisions have commerce limitations; section 3 is not a complete inventory of all consequences.',['N3ABCD','N3F4A','N5','N7BC','N10'],
        'NIRA section 3(b) makes an approved code the standard of fair competition and treats violations in transactions in or affecting interstate or foreign commerce as unfair methods under the FTC Act; section 3(c) provides equity enforcement; section 3(f) makes violations in such transactions misdemeanors. Section 3(d) permits a prescribed code with the same effect as one approved under 3(a). These are the principal compulsory code effects, not an exhaustive inventory of Title I consequences.')
verdict('P4','upheld_with_correction','The repeal removes the common prospective statutory basis, but neither continued operation until repeal nor every residual consequence is proved.',['R1','N3ABCD','N3F4A','S_DELEGATION'],
        'S.J. Res. 113 section 2, by functional description, removes the Title I statutory basis for prospective approval, prescription and enforcement of section 3 codes from June 14, 1935. For a command genuinely dependent solely on that basis, it supplies a statutory repeal backstop no later than that date. It does not establish the first ending of every related EO, negate earlier constitutional invalidity or exhaustion, or decide independent commands and accrued consequences.')
verdict('P5','upheld','The date, broad delegation conclusion and actual Live Poultry disposition are express.',['S_DATE','S_DELEGATION','S_JUDGMENT'])
verdict('P7','rejected','Non-vacatur of other orders is not evidence of continuing operative legal force. The broad delegation rationale reaches their asserted common authority; the sources do not establish administrative cancellation as the only earlier ending or establish a universal first end.',['S_DELEGATION','S_JUDGMENT','R1'],contradiction='is an unconstitutional delegation of legislative power.')
verdict('P8','upheld_with_correction','Preserve section 5 conditions and the proviso\'s actual conjunction; earlier-action immunity and retroactive effect are not resolved by this record.',['N5','R1'],
        'As enacted, section 5 exempts qualifying codes, agreements or licenses approved, prescribed or issued and in effect under Title I, and compliant action taken during the specified period, from the federal antitrust laws, with the stated sixty-day tail and license qualification. The resolution restricts the exemption to agreements and action thereunder described in numbered clauses (1) and (2), joined in the statute by and. It does not convert codes into agreements. The temporal effect on pre-repeal code actions is unresolved here. A surviving defense for prior action would not itself establish continued prospective compulsory code operation.')
verdict('P9','upheld','The described administrative acts are in the held transcriptions; EO7252 dates EO7075 and sets its own January 1, 1936 effectiveness. This judgment is limited to the section 3 code-approval scope and does not confirm EO7075\'s abridged text as a complete inventory.',['EO7075','EO7252','R1'])
verdict('P10','upheld_with_correction','The statute establishes a scheduled sunset, retains earlier termination language, and does not defer the separate repeal.',['R1','N2C','N3F4A'],
        'S.J. Res. 113 substituted April 1, 1936 as Title I\'s scheduled sunset while leaving section 2(c)\'s earlier-emergency-termination alternative. It did not postpone the June 14 repeal of code-making and enforcement provisions. The scheduled sunset is a later statutory event for a genuinely section 3-dependent command; actual persistence and first ending of remaining authorities such as section 4(a) require their own evidence.')
verdict('P11','upheld_with_correction','No actual denial order is among these shared sources. A self-executing disposition can be completed, but signature alone cannot prove all performance/effective conditions.',['N3ABCD','N10','R1'],
        'Where the complete operative text itself finally and unconditionally denies an exemption or dismisses a complaint, without a later act or unmet effective condition, the decisional command can be exhausted when that disposition takes effect. Establish that event from the actual instrument. Identify any stay, exception, direction or retained authority separately. Continuing code obligations derive from their own legal basis; the resolution is a later repeal event, subject to earlier invalidity and endings, not proof of the denial\'s performance.')
verdict('P12','rejected','The proviso limits antitrust immunity for agreements/action; no source supplies universal conversion or continued code operation through April 1. EO7075 voluntary cooperation is a new administrative purpose, not the claimed conversion.',['R1','N3F4A','EO7075'],contradiction='shall extend only to agreements and action thereunder')

now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
baseline=datetime.fromisoformat('2026-10-30T00:09:21+00:00')
review=dict(schema='independent-shared-source-review/v1',reviewer='Codex / OpenAI GPT family',
            model_variant='not exposed in this reviewer context',producer_family='Anthropic / Claude',
            review_kind='independent_cross_family_source_review',human_review=False,certified_count=0,
            input_commit=evidence['input_commit'],propositions_sha256=next(x['sha256'] for x in sources if x['id']=='propositions'),shared_analysis_sha256=next(x['sha256'] for x in sources if x['id']=='memo'),
            verdicts=verdicts,missing_numbered_propositions=['P6'],
            overall_A=dict(verdict='first_end_not_established',statutory_repeal_date='1935-06-14',judicial_invalidity_holding_date='1935-05-27',
                           conclusion='Record both the broad section 3 delegation holding and the June 14 statutory repeal. The latter is a prospective statutory backstop, not proof of an arbitrary member\'s first end. Do not automatically substitute May 27 or issuance as every member\'s first-ending date either.',individual_dossier_clearance=False),
            overall_B=['section 4(a) agreements','section 4(b) licensing','section 7(b) labor agreements','section 7(c) limited codes','section 3(e) import restrictions','sections 8(b) and Agricultural Adjustment Act authority','section 9 petroleum authority','Title II public works','sections 2/6/10 organizational or administrative authority','independent labor-board authority','adjudicated Live Poultry provisions','post-repeal orders','mixed orders and independent conditions, stays, reports, committees, appointments, delegations','earlier own-terms or actor endings','accrued liabilities, adjudications and antitrust defenses'],
            unresolved=['Constitutional invalidity, factual prior operation and formal repeal must be reconciled before asserting first operative end.','General saving statute and relevant temporal doctrines are not held among these inputs.','Pre-repeal action immunity under section 5 and the 1935 proviso remains unresolved.','Complete clause-specific inventories, earlier actors and actual performance are individual requirements.','Apply owner strike/insert continuity with before/after later_event, report-deadline prohibition, inclusive until-date disclosure, provisional-transcription note, and unnamed-instrument candidate disclosure; do not infer owner adoption of a universal first end.'],
            blinding=dict(existing_verdict_files_read=False,control_keys_read=False,seed_receipts_read=False,control_adjudications_read=False,summary_exposure='Mandatory KEAN/newest handoff and reviewed memo disclose prior review-success and planted-proposition metadata; not used as evidence.'),
            custody_limits=dict(pdf_pages_inspected=True,pdf_bytes_newly_verified=True,eo7075_abridged=True,text_git_blobs_verified=True),
            timing=dict(start_utc=None,start_unavailable_reason='No start clock was recorded before the initial instructions/source reads.',observed_timer_start_utc='2026-10-30T00:09:21Z',end_utc=now,observed_elapsed_seconds_lower_bound=(datetime.now(timezone.utc)-baseline).total_seconds(),includes_source_read_review_and_receipt_work=True,exclusive_active_time_available=False,tokens=None,cash=None),
            canonical_changes=False)
(HERE/'REVIEW.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(dict(sources=len(sources),spans=len(spans),verdicts=len(verdicts),end_utc=now)))
