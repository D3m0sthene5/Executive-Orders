"""Additive producer proposal; never modifies earlier versions or native registries."""
import copy
import datetime
import hashlib
import json
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[5]
# Resolve from the git repository rather than the caller's cwd.
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').exists())
BASE = Path(__file__).resolve().parent
OUT = BASE / 'final-dtv-v3'
assert not OUT.exists(), 'Version is immutable once created'
OUT.mkdir()
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return str(p.relative_to(ROOT))
def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

sources = []
quotes = []
def add_source(identifier, raw, url, text=None, pages=None):
    raw = ROOT / raw
    if text is None:
        doc = fitz.open(raw)
        text = OUT / 'texts' / (identifier.replace(':', '_') + '.txt')
        text.parent.mkdir(exist_ok=True)
        text.write_text(''.join(f'=== PDF page {n} ===\n' + doc[n-1].get_text() + '\n' for n in pages))
    else:
        text = ROOT / text
    item = {'id': identifier, 'url': url, 'raw_path': rel(raw), 'raw_sha256': sha(raw),
            'text_path': rel(text), 'text_sha256': sha(text), 'pdf_pages': pages,
            'custody_verified': True, 'native_registration': False,
            'source_acceptance': 'Proposed source only; ordinary source-role/factual acceptance remains separate.'}
    sources.append(item)
    return item
def quote(identifier, source, start, end):
    text = (ROOT / source['text_path']).read_text()
    a = text.index(start)
    b = text.index(end, a) + len(end)
    q = {'id': identifier, 'source_id': source['id'], 'char_start': a, 'char_end': b,
         'text': text[a:b], 'text_sha256': source['text_sha256']}
    quotes.append(q)
    return q

parent = add_source('PRIMARY:EO13038', 'research/stage21/original_sources/EO_13038.pdf',
 'https://www.govinfo.gov/content/pkg/FR-1997-03-13/pdf/97-6571.pdf',
 rel(BASE/'source-check-v3/EO_13038.complete.txt'), [1,2])
quote('Q:PARENT-ESTABLISHMENT', parent, 'Section 1. Establishment.', 'Sec. 2. Functions.')
quote('Q:PARENT-VP-FUNCTION', parent, 'Sec. 2. Functions.', 'broadcasters should assume.')
quote('Q:PARENT-DELEGATION-AND-SUNSET', parent, '(e) The Assistant Secretary', 'unless extended by the President.')
quote('Q:PARENT-EXPENSES-SUPPORT', parent, '(c) Members of the Committee', 'performance of the Committee’s functions.')

for n in (13081,13102):
    proposal = json.loads((BASE/f'v2/EO_{n}/LIFECYCLE_PROPOSAL.json').read_text())
    x = proposal['inventory_source']
    raw = f'research/stage21/original_sources/EO_{n}.pdf'
    if not (ROOT/raw).exists():
        candidates = list(ROOT.glob(f'**/{x["sha256"]}.pdf'))
        assert candidates
        raw = rel(candidates[0])
    s = add_source(f'PRIMARY:EO{n}', raw, x['url'], x['text_path'], [1])
    assert s['raw_sha256'] == x['sha256']
    quote(f'Q:EO{n}-OPERATIVE', s, 'By the authority vested', 'in lieu thereof.')

report_raw = 'research/excavator/machiavelli-modern-undecided-20261105/acquisition/report-native-v1/pdf/d903d0bfec8d86307910d3b228f76bf876d86a62963ef9ab15180527e6700015.pdf'
report = add_source('PRIMARY:DTV-REPORT', report_raw,
 'https://www.ntia.gov/files/ntia/publications/piacreport-orig.pdf', pages=[4,153,160,161,162])
quote('Q:VP-SUBMISSION', report, 'December 18, 1998', 'Co-Chair\nCo-Chair')
quote('Q:REPORT-HISTORY', report, 'Initially, the President gave', 'Advisory Committee met\non eight occasions:')
quote('Q:CHARTER-ESTABLISHMENT', report, 'ESTABLISHMENT\nThe Secretary', 'Digital Television Broadcasters\n(\x93Committee).')
quote('Q:CHARTER-OLD-DEADLINE', report, '2. The Committee will draw', 'October 1, 1998.1')
quote('Q:CHARTER-DELEGATION-DURATION-SIGNER', report, '10. Notwithstanding any other', 'Assistant Secretary of Administration')
quote('Q:CHARTER-NOTES', report, 'Notes\n1\nParagraph', 'Oct. 31, 1998.')

acq = ROOT / 'research/excavator/machiavelli-modern-undecided-20261105/continuation-20261105/acquisition-v4/documents/SOURCES.jsonl'
html = [json.loads(line) for line in acq.read_text().splitlines()]
for x in html:
    identifier = 'PRIMARY:CFR1998' if 'CFR-1998' in x['url'] else 'PRIMARY:FACA2015-COMPILATION'
    s = add_source(identifier, x['raw_path'], x['url'], x['text_path'])
    assert s['raw_sha256'] == x['sha256'] and s['text_sha256'] == x['text_sha256']
    if identifier == 'PRIMARY:CFR1998':
        for section, end in [('1013','Sec. 101-6.1014 [Reserved]'),
                             ('1027','Sec. 101-6.1028 [Reserved]'),
                             ('1029','Sec. 101-6.1030 [Reserved]'),
                             ('1031','Sec. 101-6.1032 [Reserved]')]:
            quote('Q:CFR-'+section, s, 'Sec. 101-6.'+section+' ', end)
    else:
        quote('Q:FACA9', s, '§9. Establishment and purpose', '§10. Advisory committee procedures;')
        quote('Q:FACA14', s, '§14. Termination of advisory committees;', '(Pub. L. 92–463, §14, Oct. 6, 1972, 86 Stat. 776.)')

statute_raw = 'research/excavator/machiavelli-modern-undecided-20261105/continuation-20261105/acquisition-v4/pdf-run-1/pdf/d46eb8e8384da8352c9619cf2c5df1c534e0b20dd36b68317c76bf5b612718d8.pdf'
statute = add_source('PRIMARY:FACA1972', statute_raw,
 'https://www.govinfo.gov/content/pkg/STATUTE-86/pdf/STATUTE-86-Pg770.pdf', pages=[5,7])
quote('Q:FACA1972-CHARTER', statute, '(c) No advisory committee shall meet', 'furnished to the Library of \nCongress.')
quote('Q:FACA1972-SUNSET', statute, 'SEC. 14.', 'otherwise terminate.')

reason = ('Actual December 18, 1998 signed submission to the Vice President satisfies EO13038 §2 and §4; '
          '30 calendar days later is January 17, 1999. This conclusion uses submission, not receipt, publication, '
          'or the December31 deadline. Best legal reading: EO13038 itself establishes the committee and its '
          '§4 sunset; later EO13102 extends the report schedule while preserving §4. The charter retains the '
          'superseded October1/October31 schedule and does not revoke or abolish presidential establishment '
          'authority. 1998 CFR .1031(a) requires conformity to later presidential authority; .1027 describes '
          'earlier termination by revoking or abolishing establishment authority. Section3(e) delegates FACA '
          'functions, not a demonstrated power or action to contradict the specific presidential sunset. '
          'The competing delegated-earlier-termination interpretation is explicitly retained for independent '
          'review. No extension or separate earlier revocation was located in the bounded sources examined; '
          'this negative finding is not proof that none existed. September30 1999 is later formal revocation.')
residual = ('The sole amendment has no independent continuing command after the parent committee sunset. '
            'EO13038 §3(c)-(d) travel/expense and support consequences, completed legal acts and independent '
            'records obligations can persist; no particular unpaid claim is proved. The report and Benton '
            'institutional memory do not continue the committee or this amendment. No predecessor revival.')
counter = [
 'The charter literally says the Committee shall terminate October31 1998 unless earlier terminated or renewed by proper authority by appropriate action; it is legally significant counterevidence, not ignored paperwork.',
 'FACA §9(c)(I) requires a charter to state a sub-two-year termination date. EO13038 §3(e) delegates presidential FACA functions except reporting to Congress; the strongest contrary theory treats the signed duration clause as a competent earlier termination under that delegation.',
 'The charter also purports to establish the Committee pursuant to EO13038 and says its FACA delegation operates notwithstanding any other Executive Order. Those charter recitals do not themselves enlarge the authority conferred by the President.',
 'EO13102 expressly amends the reporting deadline only, not §4 or the charter duration. Its prospective reporting command and preserved §4 strongly favor continuation, but it is not an explicit charter renewal or an explicit override of October31.',
 'Commerce signature is Raymond G. Kammer Jr., Acting CFO and Assistant Secretary of Administration; the source does not prove whether he was the §3(e) Assistant Secretary’s designee. The preferred conclusion does not depend on assuming lack of designation.',
 'The statutory-committee survival provision in CFR .1029(a)(1) cannot simply be applied to this President-established committee. CFR .1029(b) requires presidential action and a new charter for renewal; a true prior legal sunset would make renewal legally important.',
 'Report history gives actual work through December; that supports post-October activity but does not by itself establish legal authority or prove an extension. Later EO13138 confirms termination and completed work by September30 1999 without identifying the earliest ending.',
 'Charter note5 prints June17 1997 for the October31 extension while note1 gives June17 1998 for the paired October1 deadline; this discrepancy is preserved, not silently corrected.',
]
gaps = [
 'Independent examination must test the disclosed legal interpretation against the delegated-earlier-termination countertheory; producer conclusion is unapproved.',
 'Raw/text custody is verified, but ordinary source-role/factual supplement acceptance, fresh native preparation, distinct status review/adoption and exact lifecycle review remain required.',
 'No separate later charter or termination notice was located in this bounded assignment. Its absence is not itself a legal prerequisite or a reason to require renewal if the presidential establishment never terminated; a contrary duly authorized action would require revising the conclusion.',
]
for n in (13081,13102):
    old = BASE/f'v2/EO_{n}'
    p = json.loads((old/'LIFECYCLE_PROPOSAL.json').read_text())
    p.update(version='final-dtv-v3', producer_approved=False,
      disposition='complete_unapproved_legal_application_proposal_with_charter_countertheory_retained',
      first_end={'date':'1999-01-17','actor':'EO13038 §4 applied to actual December18 submission to the Vice President',
                 'mechanism':'parent_submission_relative_sunset',
                 'precision_note':'Calendar date only; no submission time or receipt date proved. Legal interpretation, not an observed closure date.'},
      whole_order_end='1999-01-17', counterevidence=counter, remaining_scientific_gaps=gaps,
      residuals={'state':'transferred_or_accrued','assessment':residual},
      legal_rationale=reason,
      exact_source_manifest='EVIDENCE_SUPPLEMENT_PROPOSED.json',
      prior_version={'path':rel(old/'LIFECYCLE_PROPOSAL.json'),'sha256':sha(old/'LIFECYCLE_PROPOSAL.json')},
      frozen_prior_research_preserved=True)
    p.pop('conditional_candidate', None)
    p['supported_events'] += [{'date':'1999-01-17','event':'Proposed legal sunset under preserved presidential §4; competing charter reading disclosed.'}]
    p['source_acceptance_gaps'] = gaps[1:2]
    p['formal_revocation']['scope'] = 'EO13138 §3(b) revokes EO13038 as amended, expressly including EO13081 and EO13102; §9 effective September30 1999.'
    p['html_source_refs'] = [x for x in p['html_source_refs'] if x['id']=='WEB:PIAC-SITE']
    write(OUT/f'EO_{n}/LIFECYCLE_PROPOSAL.json',p)
    d = json.loads((old/'LIFECYCLE_DECISION.proposed.json').read_text())
    d['approved'] = False
    d['research_rationale'] = reason
    d['unresolved_material_gaps'] = gaps
    d['savings'] = {'state':'transferred_or_accrued','source_id':'PROPOSED-SUPPLEMENT:EO13038-SEC3CD','reason':residual}
    c = d['clauses'][0]
    c.update(state='terminated',effective_date='1999-01-17',effective_date_confirmed=True,
      end_id='PROPOSED-SUPPLEMENT:EO13038-SEC4-PLUS-VP-SUBMISSION',reason=reason,
      mechanism='parent_submission_relative_sunset',
      later_events=[{'id':f'ACT:EO:{n}>EO:13138','effective_date':'1999-09-30',
                     'effective_date_confirmed':True,'mechanism':'formal_parent_revocation_after_sunset'}])
    d['source_notes'] += [{'id':'PROPOSED-SUPPLEMENT:EO13038-SEC4-PLUS-VP-SUBMISSION',
      'reason':'Composite proposed rule-and-fact basis only; no registered native evidence ID yet. See exact source manifest and DTV_LEGAL_ADDENDUM.md. Not applyable before ordinary admission and fresh preparation.',
      'date_qualification':'Actual submission to Vice President December18; January17 by30-calendar-day rule; no receipt or intraday time established.'}]
    write(OUT/f'EO_{n}/LIFECYCLE_DECISION.proposed.json',d)

write(OUT/'EVIDENCE_SUPPLEMENT_PROPOSED.json', {'schema':'source-bound-proposed-supplement/v1',
 'created_at_utc':NOW,'approved':False,'sources':sources,'quotes':quotes,
 'scope':'EO13081 and EO13102 legal application only. No canonical source/status/claim registry changes.',
 'temporal_limits':'1998 annual CFR is contemporaneous. FACA1972 is as enacted; later 2015 compilation source notes disclose 1977 Administrator substitution in §9 and original-only §14. No later rule applied retroactively.'})
write(OUT/'SOURCE_FINDINGS.json', {'created_at_utc':NOW,'instrument_ids':['EO:13081','EO:13102'],
 'producer_approved':False,'conclusion':'January17 1999 proposed first and whole operative end under parent rule; not approval.',
 'trigger_fact':'Signed report submits to the Vice President December18 1998; receipt is neither proved nor required.',
 'interpretation':reason,'counterevidence':counter,'remaining_gaps':gaps,
 'coverage':'Five original assigned cases remain inventoried in v2. This bounded revision affects only the two DTV amendments; three other v2 cases are unchanged. No new broad searches or downloads.',
 'source_manifest':'EVIDENCE_SUPPLEMENT_PROPOSED.json'})
write(OUT/'TELEMETRY.json', {'created_at_utc':NOW,'model':'OpenAI Codex GPT-6 (inherited model; variant not instrumented)',
 'incremental_tokens':None,'incremental_cash':None,'start_utc':None,
 'start_qualification':'Final bounded follow-up start not instrumented; no cost or duration estimate invented.',
 'work':'Retained primary-source reading, legal interpretation, additive unapproved proposals, exact hash/offset validation.'})
print(OUT)
