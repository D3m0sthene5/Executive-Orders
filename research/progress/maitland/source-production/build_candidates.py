"""Reproduce bounded, unreviewed transition proposals from frozen held text.

Run from the repository root. No canonical claim, source, status or review writes.
SOURCES.json is an explicit freeze: any changed source requires a new version.
"""
from pathlib import Path
import hashlib
import json
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def main():
    start = time.monotonic()
    source_doc = json.loads((OUT/'SOURCES.json').read_text())
    sources = {s['instrument_id']: s for s in source_doc['sources']}
    texts = {}
    for iid, s in sources.items():
        raw = (ROOT/s['text_path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != s['text_sha256']:
            raise ValueError('changed frozen source: '+iid)
        texts[iid] = raw.decode('utf-8')

    def excerpt(n, begin, end=None, *, after=0):
        iid = f'EO:{n}'; text = texts[iid]
        a = text.index(begin, after)
        b = text.index(end, a+len(begin)) if end else a+len(begin)
        return {'text_path': sources[iid]['text_path'], 'text_sha256': sources[iid]['text_sha256'],
                'char_start': a, 'char_end': b, 'quote': text[a:b]}

    signing = {13933:'2020-06-26',13934:'2020-07-03',13978:'2021-01-18',
               14029:'2021-05-14',14189:'2025-01-29',10915:'1961-01-24',
               10973:'1961-11-03',11252:'1965-10-20',11963:'1977-01-19',12220:'1980-06-27'}
    provisions, transitions = [], []

    def provision(pid, host, label, src, span, *, questions=()):
        record = {'provision_id':pid,'instrument_id':f'EO:{host}','scope':label,
                  'norm_text':span['quote'],'valid_start':signing[src],
                  'known_sunset_end_exclusive':None,'source_id':f'SRC:EO:{src}','source':span,
                  'date_basis':'Signing-date textual chronology only; commencement is not independently established.',
                  'remaining_gap':'Selected provision witness, not complete order or cutoff-wide legal history.',
                  'unresolved_questions':list(questions)}
        provisions.append(record)
        return record

    def transition(tid, pid, actor, kind, span, *, effective=None, sequence=1, questions=(), **extra):
        record = {'transition_id':tid,'affected_provision_id':pid,'actor_id':f'EO:{actor}',
                  'event_date':signing[actor],'signing_date':signing[actor],
                  'publication_date':sources[f'EO:{actor}']['publication_date'],
                  'kind':kind,'source_id':f'SRC:EO:{actor}','source':span,
                  'date_basis':('Express operative-date text in acting instrument; event/signing/publication dates remain separate.'
                                if effective else 'Signing-date textual chronology; no separate commencement clause located. Publication date retained as an alternative research datum, not a chosen legal endpoint.'),
                  'effective_date':effective,'sequence':sequence,'unresolved_questions':list(questions),**extra}
        transitions.append(record)
        return record

    revoke14029 = excerpt(14029,'Section 1. Revocation of Presidential Actions.','Sec. 2. Implementation.')
    reinstate_garden = excerpt(14189,'Sec. 3. National Garden of American Heroes.','(b) The Assistant to the President')
    reinstate_monuments = excerpt(14189,'Sec. 4. Protecting America’s Monuments from Vandalism.','Recent examples of conduct')

    p33a = provision('P:13933:sec3a',13933,'Section 3(a): Attorney General enforcement priority',13933,
                    excerpt(13933,'Sec. 3. Enforcing Laws Prohibiting','(b) The Attorney General shall'))
    p33s = provision('P:13933:sec5',13933,'Section 5: conditional personnel assistance',13933,
                    excerpt(13933,'Sec. 5. Providing Assistance','Sec. 6. General Provisions.'),
                    questions=('The six-month termination is subject to presidential extension; no extension census was performed.',
                               'The calendar six-month candidate is 2020-12-26. No actual expiry or renewed six-month period is inferred.',
                               'What operative force, if any, does this time-limited section have after reinstatement of the pre-revocation form?'))
    for p in (p33a,p33s):
        pid=p['provision_id']
        transition('T:14029:010-revoke-'+pid,pid,14029,'revoke',revoke14029)
        transition('T:14189:040-reinstate-'+pid,pid,14189,'reinstate',reinstate_monuments,
                   restore_version_id=pid+'::v0',sequence=40,
                   questions=('Restoration of the earlier text is explicit; any independent expiry/completion and surviving consequences require separate examination.',))

    p34c = provision('P:13934:sec3c-chapeau',13934,'Section 3(c) chapeau',13934,
                    excerpt(13934,'(c) In addition to the requirements','(i) The National Garden should'))
    old = p34c['norm_text'][p34c['norm_text'].index('In addition'):p34c['norm_text'].index('National Garden')].rstrip()
    # The amended quotation and the target use different print line wraps. The
    # exact target span is retained; a reviewer must examine the directive too.
    amend_c = transition('T:13978:030-amend-13934-chapeau',p34c['provision_id'],13978,'amend',
                         excerpt(13978,'Sec. 3. Honoring Additional American Heroes.','(b) Section 3(c)(i)'),
                         from_version_id=p34c['provision_id']+'::v0',old_rule=old,new_rule='The',
                         expected_new_text=p34c['norm_text'].replace(old,'The',1),sequence=30)
    transition('T:14029:010-revoke-13934-chapeau',p34c['provision_id'],14029,'revoke',revoke14029)
    transition('T:14189:030-reinstate-13934-chapeau',p34c['provision_id'],14189,'reinstate',reinstate_garden,
               restore_version_id=amend_c['transition_id'],sequence=30,
               questions=('This small scope retains the January 2021 amendment in the pre-revocation version. Other amendments to EO13934 are outside this selected-scope bundle.',))

    p34ii = provision('P:13934:sec3cii-access',13934,'Section 3(c)(ii): public access timing',13934,
                     excerpt(13934,'(ii) The National Garden should be opened','(iii) Statues should depict'))
    transition('T:14029:010-revoke-13934-access',p34ii['provision_id'],14029,'revoke',revoke14029)
    reinst_ii = transition('T:14189:030-reinstate-13934-access',p34ii['provision_id'],14189,'reinstate',reinstate_garden,
                          restore_version_id=p34ii['provision_id']+'::v0',sequence=30)
    old_ii = p34ii['norm_text'][p34ii['norm_text'].index('prior to'):p34ii['norm_text'].index('2026.')+4]
    transition('T:14189:032-amend-13934-access',p34ii['provision_id'],14189,'amend',
               excerpt(14189,'(c) Section 3(c)(ii)','Sec. 4. Protecting'),sequence=32,
               from_version_id=p34ii['provision_id']+'::v0',old_rule=old_ii,new_rule='as expeditiously as possible',
               expected_new_text=p34ii['norm_text'].replace(old_ii,'as expeditiously as possible',1),
               questions=('Within EO14189 the reinstatement in section3(a) precedes this section3(c) amendment; these are distinct operations.',))

    p78 = provision('P:13978:sec6-report',13978,'Section 6: annual public progress report',13978,
                    excerpt(13978,'Sec. 6. Public Report.','Sec. 7. General Provisions.'),
                    questions=('Actual establishment/completion of the National Garden and all listed statues was not examined; do not infer the contingent reporting endpoint.',))
    transition('T:14029:010-revoke-13978-report',p78['provision_id'],14029,'revoke',revoke14029)
    transition('T:14189:031-reinstate-13978-report',p78['provision_id'],14189,'reinstate',reinstate_garden,
               restore_version_id=p78['provision_id']+'::v0',sequence=31)

    # The amendatory act and its embedded norm have distinct identities. This
    # selected norm lives in EO10900, despite being printed in EO10915.
    pfood = provision('P:10900:food-for-peace-coordination',10900,'Section 6 inserted by EO10915; later section 5',10915,
                      excerpt(10915,'“ Se c. 6. Director of the Food-for-Peace','Sec. 2. Executive Order'),
                      questions=('The source is OCR with neighboring documents. Norm identity and parent location require independent review.',))
    transfer = excerpt(11252,'S ection  1. A ll functions','Sec . 2.')
    transfer_date = excerpt(11252,'S ec . 4. This order shall take effect on November 1,1965.')
    tr=transition('T:11252:010-transfer-food-for-peace',pfood['provision_id'],11252,'transfer',transfer,
                  effective='1965-11-01',transfer_to='Secretary of State',
                  questions=('The transfer modifies functions by reference; it prints no replacement of the embedded norm. Do not manufacture replacement statutory wording.',))
    tr['effective_date_source']=transfer_date
    transition('T:11963:020-renumber-food-for-peace',pfood['provision_id'],11963,'renumber',
               excerpt(11963,'Se c. 2. Executive Order No. 10900','T he  W hite'),
               new_label='Section 5 of EO10900 (formerly section 6)',
               questions=('Section5 revoked by this act was the pre-existing different section. The Food-for-Peace norm is old section6, redesignated section5, not the section being revoked.',))
    transition('T:12220:1501-revoke-food-for-peace',pfood['provision_id'],12220,'revoke',
               excerpt(12220,'1-501. Executive Order N o. 10900','1-502.'),
               questions=('This is the explicit parent revocation, not by itself proof of the first cessation of every dependent function or of surviving consequences.',))

    p111 = provision('P:10893:sec111-food-for-peace',10893,'Part I section111 inserted by EO10915',10915,
                     excerpt(10915,'Sec. 111. Director of the Food-for-','J o h n F . K e n n e d y'),
                     questions=('The inserted norm is distinct from the executed command to insert it. No broad first-end or savings closure is inferred.',))
    supersede = excerpt(10973,'Sec. 605. Superseded orders.','Sec. 606. Saving provisions.')
    effective = excerpt(10973,'Sec. 607. Effective date.','John  F. K ennedy')
    tr=transition('T:10973:0605-supersede-food-for-peace-sec111',p111['provision_id'],10973,'supersede',supersede,
                  effective='1961-09-30',questions=('The parent exception is Part II and specified funding use; this norm is inserted in Part I. Exact scope and saved actions require independent review.',
                                                  'Retroactive effective date precedes signing by more than a month. A retrospective valid-time answer differs from what was knowable on that earlier day.'))
    tr['effective_date_source']=effective
    tr['savings_source']=excerpt(10973,'Sec. 606. Saving provisions.','Sec. 607. Effective date.')

    bundle={'schema':'eo-provision-history/v1','producer':'OpenAI-maitland-source-producer',
            'research_only':True,'base_commit':source_doc['base_commit'],
            'provisions':provisions,'transitions':transitions,
            'review_file':None,
            'coverage_notice':'Seven selected norms across two connected examples; not whole-order reconstruction, exhaustive transition discovery, current legal advice, or human certification. All records are unreviewed producer proposals.',
            'legal_cutoff':'2026-10-14'}
    (OUT/'CANDIDATES.json').write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n')
    # Every source reference must survive exact file/hash/span rechecking.
    checked=0
    def walk(v):
        nonlocal checked
        if isinstance(v,dict):
            if all(k in v for k in ('text_path','text_sha256','char_start','char_end','quote')):
                body=(ROOT/v['text_path']).read_bytes()
                assert hashlib.sha256(body).hexdigest()==v['text_sha256']
                text=body.decode('utf-8');assert text[v['char_start']:v['char_end']]==v['quote']
                checked+=1
            for child in v.values():walk(child)
        elif isinstance(v,list):
            for child in v:walk(child)
    walk(bundle)
    for p in provisions:assert p['norm_text'] in p['source']['quote']
    for t in transitions:
        if t['kind']=='amend':
            p=next(p for p in provisions if p['provision_id']==t['affected_provision_id'])
            assert p['norm_text'].count(t['old_rule'])==1
            assert p['norm_text'].replace(t['old_rule'],t['new_rule'],1)==t['expected_new_text']
    result={'provisions':len(provisions),'transitions':len(transitions),'frozen_source_files':len(sources),
            'exact_source_refs_checked':checked,'builder_wall_seconds':round(time.monotonic()-start,6),
            'model_tokens':None,'cash_usd':None,'research_labor_seconds':None,
            'scientific_approval':False,'independent_review_performed':False}
    (OUT/'BUILD_RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
