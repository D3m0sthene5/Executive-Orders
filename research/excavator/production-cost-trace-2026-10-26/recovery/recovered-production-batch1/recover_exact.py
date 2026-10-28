"""Reconstruct producer proposal objects solely from retained tool-call history.
No retrieval/research. Only label exact recovery after matching historical hashes.
Run from the restored eo-audit repository root. Outputs go to this recovery folder.
"""
from pathlib import Path
import json, hashlib, copy, sys
OUT=Path(__file__).resolve().parent
BASE=Path('research/excavator/production-cost-trace-2026-10-26')
PACKET=BASE/'packet-b1-v1/PACKET.json'
EXPECTED_COMBINED='f58d14ab50626c4ea7015cea0f2c61d6ab4549e28a5b40ab1f43fc6a3f19038a'

def ref(path,raw,url,item,a=0,b=None,local=None):
    t=Path(path).read_text(); b=len(t) if b is None else b
    r=dict(url=url,sha256=raw,page_or_item=item,text_path=str(path),text_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),char_start=a,char_end=b,quote=t[a:b])
    if local:r['local_path']=str(local)
    return r

def canonical(j):return json.dumps(j,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def csha(j):return hashlib.sha256(canonical(j).encode()).hexdigest()

def build():
    packet=json.load(open(PACKET))
    # Original source records are reconstructed from ASSIGNMENT.json and the exact
    # original partial-v1 construction call, not newly graded.
    originals={
      'EO:8179':dict(text_path='jobs/fr-originals/data/full_run/texts/EO_8179.txt',raw='d052a33fdd9c8ff05659a6b87bd79b9e8d63a78985d542bbad8d327d5083a503',url='https://www.govinfo.gov/content/pkg/FR-1939-06-23/pdf/FR-1939-06-23.pdf',page='4 FR 2468, PDF pages 2-2'),
      'EO:8300':dict(text_path='jobs/fr-originals/data/full_run/texts/EO_8300.txt',raw='c0b002da446936c9bd01f992d127bc38ebb8498f5a2e2dd87ae4b515b2887a4c',url='https://www.govinfo.gov/content/pkg/FR-1939-12-14/pdf/FR-1939-12-14.pdf',page='4 FR 4847, PDF pages 1-1')}
    actor=Path('jobs/fr-originals/data/full_run/texts/EO_9830.txt');a=actor.read_text();raw='e99c5924861f876d90b2a5b5fc9e3c67da5076cafac0633e85906eaa2b92e519';url='https://www.govinfo.gov/content/pkg/FR-1947-02-25/pdf/FR-1947-02-25.pdf';local=BASE/'acquisition/pdf'/f'{raw}.pdf'
    end=ref(actor,raw,url,'12 FR1269, PDFpage11, PartIIIrevocation opening and list through complete EO8300row',90277,a.index('No. 8423',90277),local)
    eff=ref(actor,raw,url,'12 FR1259, PDFpage1, order opening effectiveMay1 1947',2164,2220,local)
    sup=BASE/'acquisition-b1-supplement';trans=BASE/'acquisition-b1-transitional'
    results=json.load(open(sup/'RESULTS.json'))
    def page_ref(result,n,item):
        z=next(x for x in result['pages'] if x['pdf_page']==n)
        return ref(sup/z['text'],result['sha256'],result['url'],item,local=sup/result['retained_pdf'])
    war=page_ref(results[1],1,'7 FR8007, PDFpage1, CivilServiceCommission Part18amendments signedSep28 1942/filedOct9; complete§18.11scope including postalexception')
    r8707=ref('jobs/fr-originals/data/full_run/texts/EO_8707.txt',results[3]['sha256'],results[3]['url'],'6 FR1399, PDFpage1, complete EO8707 amending RuleIX§2 andX§6(a); officialpageinspected',local=sup/results[3]['retained_pdf'])
    s8707=Path(r8707['text_path']).read_text();x=s8707.index('EXECUTIVE ORDER');y=s8707.index('EXECUTIVE ORDER',x+1);r8707=ref(r8707['text_path'],r8707['sha256'],r8707['url'],r8707['page_or_item'],x,y,r8707['local_path'])
    r8423=ref('jobs/fr-originals/data/full_run/texts/EO_8423.txt',results[2]['sha256'],results[2]['url'],'5 FR2099, PDFpage1, completeEO8423 RuleVII§2(b) amendment; officialpageinspected',local=sup/results[2]['retained_pdf'])
    s8423=Path(r8423['text_path']).read_text();x=s8423.index('EXECUTIVE ORDER');y=s8423.index('EXECUTIVE ORDER',x+1);r8423=ref(r8423['text_path'],r8423['sha256'],r8423['url'],r8423['page_or_item'],x,y,r8423['local_path'])
    tr=json.load(open(trans/'RESULTS.json'))[0]
    def trref(n,item):
        z=next(x for x in tr['pages'] if x['pdf_page']==n)
        return ref(trans/z['text'],tr['sha256'],tr['url'],item,local=trans/tr['retained_pdf'])
    intro=trref(4,'11 FR1424, PDFpage4, Part27intro/effective formulation and supersession of Part18')
    selection=trref(7,'11 FR1427, PDFpage7, Part27§27.7(c) merit/fitness selection from highest3 with objections/veteran preference')
    reinstate=trref(9,'11 FR1429, PDFpage9, Part27§§27.9reinstatement and27.10transfer')
    promotion=trref(10,'11 FR1430, PDFpage10, Part27§27.11promotion including probation and Commissionapproval')
    benefits=trref(11,'11 FR1431, PDFpage11, Part27§27.16(g) status/tenure and samebenefits under RuleIX; officialpageinspected')
    r9691=ref('jobs/fr-originals/data/full_run/texts/EO_9691.txt','66eea8c88ed91c1f37339b7146ce206d51700776d7f96b2e3997f003698936bc','https://www.govinfo.gov/content/pkg/FR-1946-02-06/pdf/FR-1946-02-06.pdf','11 FR1383, PDFpage3, EO9691§9 revocation and acquiredreemploymentrights saving')
    s9691=Path(r9691['text_path']).read_text();x=s9691.index('9. Executive Orders');y=s9691.index('H arry',x);r9691=ref(r9691['text_path'],r9691['sha256'],r9691['url'],r9691['page_or_item'],x,y)
    def dec(z):
        if isinstance(z,list):return[dec(v)for v in z]
        if isinstance(z,dict):
            if '@eo:ref'in z:return dec(packet['shared_objects'][z['@eo:ref']])
            if '@eo:source'in z:return dec(packet['sources'][z['@eo:source']])
            return{k:dec(v)for k,v in z.items()}
        return z
    claims={}
    for iid,inv in [('EO:8179',[('rule-IX-2',4520,5339),('rule-X-6a',5340,5487),('rule-XI-1ab',5488,5897)]),('EO:8300',[('rule-VII-2b',699,1580)])]:
        z=originals[iid];t=Path(z['text_path']).read_text();item=z['page']+'; complete target page inspected; text span through target closing record only'
        if iid=='EO:8179':
            start=t.index('EXECUTIVE ORDER\nAmending');stop=t.index('Rules, Regulations, Orders',start)
        else:
            start=t.index('EXECUTIVE ORDER');stop=t.index('EXECUTIVE ORDER',start+1)
        orig=ref(z['text_path'],z['raw'],z['url'],item,start,stop,BASE/'acquisition/pdf'/f"{z['raw']}.pdf")
        orig={k:orig[k]for k in ['url','sha256','page_or_item','local_path','text_path','text_sha256','char_start','char_end','quote']}
        cl=[]
        for s,x,y in inv:
            src=ref(z['text_path'],z['raw'],z['url'],z['page']+'; complete numbered amendment scope inspected',x,y,BASE/'acquisition/pdf'/f"{z['raw']}.pdf")
            src={k:src[k]for k in ['url','sha256','page_or_item','local_path','text_path','text_sha256','char_start','char_end','quote']}
            cl.append({'scope_id':iid+'#'+s,'original_operative_text':t[x:y],'original_source':src,'state_at_cutoff':'terminated','first_end':None,'current_predicate':None,'later_events':[],'reason':''})
        j={'schema':'eo-lifecycle-claim/v1','instrument_id':iid,'whole_order_status':'no','original_representation':orig,'operative_clauses':cl,'whole_order_end':None,'savings_residuals':None,'later_source_search':[],'unresolved_material_gaps':[],'research_rationale':''}
        j['earlier_candidate_ends']=[]
        for c in j['operative_clauses']:
            c['first_end']={'date':'1947-05-01','actor':'EO:9830','mechanism':'express named whole revocation under owner2026-10-21unnamed-instruments convention','source':end,'effective_date_source':eff}
            c['later_events']=[]
            c['reason']='Continuous incorporated host amendment under TC09 and Oct21strike-and-insert ruling; namedwhole revocation effectiveMay1 1947 is endpoint under Oct21unnamed-instruments ruling. Earlier unnamed scope changes disclosed separately rather than silently treated as named first ends.'
            if 'rule-IX' in c['scope_id'] or 'rule-X-6' in c['scope_id']:
                mechanism='amendment continuing host norm; addedRuleIX§2(c)' if 'rule-IX'in c['scope_id'] else 'amendment continuing host norm; RuleX§6(a)substantively rewritten'
                c['later_events'].append({'effective_date':'1941-03-10','actor':'EO:8707','mechanism':mechanism,'source':r8707,'before_text':c['original_operative_text'],'after_text':r8707['quote'],'reason':'No delayed effectiveterm; signedMarch10 1941. Before/after text explicitly retained; rewriting is not cessation under ownerOct21rule.'})
            if iid=='EO:8300':
                c['later_events'].append({'effective_date':'1940-05-28','actor':'EO:8423','mechanism':'amendment continuing host sentence, substantively broadening objectionexception to preparedness/nationaldefense agencies','source':r8423,'before_text':c['original_operative_text'],'after_text':r8423['quote'],'reason':'No delayedterm; signedMay28 1940. Whole-sentencerewrite disclosed as substantivechange for humanreviewer; endpoint not set to1940underOct21ruling.'})
            if 'rule-XI'not in c['scope_id']:
                j['earlier_candidate_ends'].append({'scope_id':c['scope_id'],'candidate':'WarServiceRegulations§18.11 supersession of hostRulesVII,IX,X for coveredpositions, with postalfieldexception','source':war,'date_qualification':'Primary amendment signedSep28 1942/filedOct9/publishedOct10. InitialPart18effectiveMarch16 1942 is described retrospectively in1946Part27; exact initial application/agencydates not asserted here.','disposition':'Disclosed earlier candidate for humanreview under ownerunnamed-instruments ruling; does not name target EO and is not substituted as targetendpoint.'})
            target=selection if iid=='EO:8300' else promotion if 'rule-XI'in c['scope_id'] else reinstate
            j['earlier_candidate_ends'].append({'scope_id':c['scope_id'],'candidate':'1946Part27temporaryrecasting of host subject; supersedesPart18 underEO9691','source':target,'effective_context_source':intro,'date_qualification':'Intro says30daysfromEO9691Feb4 plus optionalagencyearlyoperation; ordinary arithmeticMar6, whereas EO9830§3.2callsMarch7 1946theTemporaryRegulations effectivedate. This candidate-date ambiguity preserved, not converted to exactfirstcessation.','disposition':'Unnamedhostrulechange disclosed for humanreview underOct21ruling; no contrary namedtargetend located. Part18§18.11 doesnot listRuleXI, so that earlier1942scope is not asserted for originalitem3.'})
        j['whole_order_end']={'date':'1947-05-01','actor':'EO:9830','mechanism':'express named whole revocation under owner2026-10-21unnamed-instruments convention','source':end,'effective_date_source':eff}
        j['savings_residuals']={'state':'transferred_or_accrued','reason':'EO9830 contains no saving of target authority; PartIIreplaces completeCivilServiceRules and PartIII expresslyrevokes target. Prior completedappointments/promotions and acquiredstatus may remain historical/savedacts independently under successor authority, rather than currenttargetnorms. EO9691§9saves acquiredreemploymentrights generally; Part27§27.16(g) retains tenure and awards samebenefits asRuleIX, making it a material earlierincorporation/savings candidate disclosed here. Part27is expressly transitional untilCivilServiceRulesrevision; EO9830substitutes newRules/prescribes newCommissionstandards and revokes target without a target saving. No currentapplication of oldtargetterms identified through boundedcheck. This doesnot assert extinction of everyindividuals accruedrights or certify any suchindividualhistory.','source':end,'sources':[copy.deepcopy(r9691),benefits,intro]}
        d=dec(packet['dossiers'][iid]);j['later_source_search']=[x['entry'] for x in d['machine_searches']]
        j['later_source_search'] += [{'repository':'Held FederalRegister original-text corpus, jobs/fr-originals/data/full_run/texts','query_or_scope':'Earlier8179<n<9830:1481heldtextfiles number+RuleIX/X/XI/VII, probation, absoluteappointment and confidentialpositionterms; actualmatches/contextreview in EARLIER_RULE_SCAN.json. LaternumericEOtexts>8179 scanned for named8179/8300, yielding only9830targetrows; record LATER_NAMING_SCAN.json. Coveragefinite/neighborOCR; independently evaluateunnamedhostchanges and savings as disclosed.','checked_on':'2026-10-27'},{'repository':'Official OFR1939dispositiontable and primary-domainwebsearch archives.gov/govinfo.gov/loc.gov','query_or_scope':'Search targetEO numbers withamendment/revocation, revival/reinstatement and WarServiceRulespostal/supersession terms. OFRlists9830revocation; primaryregulations inspected separately. No relevantrevival identified; noisy numericfalsepositives excluded. Not an exhaustive universalnegative or originalauthentication.','checked_on':'2026-10-27'}]
        claims[iid]=j
    return claims,packet

RATIONALE='''The complete official original was compared with its target page: EO 8179 has three numbered amendments, including all nested conditions; EO 8300 has one amendment of the first sentence of Rule VII section 2(b). The originals contain no sunset, completed assignment, or independent command outside those host-rule amendments. Probation and objection conditions govern recurring application rather than ending the entire order. EO 8707 and EO 8423 are later amendments, with before-and-after text retained. The earlier ACT commentary that EO 8707 ended EO 8179 item 2 is reconsidered under the owner's October 21 strike-and-insert ruling, which continues the amended clause.

The full text and operative pages of EO 9830 were examined. Its opening May 1, 1947 effective date governs Parts I, II and III. Part II replaces the Civil Service Rules, and Part III expressly names both target orders and their original dates without a savings qualification. Every original footprint therefore ends on May 1, 1947 under the owner's October 21 unnamed-instruments convention. This is the convention's named endpoint, not a claim that no substantive application changed earlier. The earlier War Service Regulations and 1946 temporary regulations are pinned and expressly disclosed as candidate earlier changes. The 1942 list does not include Rule XI. The 1946 effective-date qualification is preserved rather than converted to an unsupported exact date.

EO 9691 and temporary regulation 27.16(g) protect acquired rights, tenure and benefits. These are separately analyzed as saved acts and successor authority, not silently erased or treated as current authority under the revoked target orders. No independent target command or present application of the old target terms was identified in the bounded later-source, host-rule, savings and revival checks. The U.S. Code machine search reaches October 9 only; it is not the sole bridge to the October 14, 2026 cutoff. This is a producer proposal under the existing codebook and owner rulings, subject to independent whole-case review and human review of the disclosed earlier candidates.'''

def finalize_v3(claims,packet):
    for iid,j in claims.items():
        j['research_rationale']=RATIONALE
        for c in j['operative_clauses']:
            c['first_end']['mechanism']='Express named revocation under the owner\'s October 21, 2026 unnamed-instruments convention'
            c['reason']='The original creates continuing host-rule norms. Later amendments continue those clauses under the strike-and-insert ruling. EO 9830 names and revokes the target, effective May 1, 1947. Earlier unnamed host-rule changes and the saved-benefits issue are expressly disclosed for human review; they are not silently equated with this named endpoint.'
            for e in c['later_events']:
                if iid=='EO:8300':e['reason']='Signed May 28, 1940, with no delayed effective term. The entire sentence was rewritten and its substantive exception broadened; the before-and-after text is recorded for the human reviewer. The amendment continues the clause under the owner ruling.'
                else:e['reason']='Signed March 10, 1941, with no delayed effective term. The added Rule IX subdivision and revised Rule X exception are recorded with before-and-after text. The revised clause continues under the owner ruling.'
        for candidate in j['earlier_candidate_ends']:
            candidate['disposition']='Disclosed earlier candidate for human review under research/readiness/owner_rulings/2026-10-21-unnamed-instruments.md. The instrument changes host-rule subjects but does not name the target EO; its date is not substituted for the named endpoint.'
            if 'WarService'in candidate['candidate']:
                candidate['candidate']='War Service Regulations section 18.11 supersedes host Rules VII, IX and X for covered positions, subject to the postal field-service exception.'
                candidate['date_qualification']='This primary amendment is signed September 28, 1942, filed October 9 and published October 10. The 1946 temporary regulations retrospectively identify March 16, 1942 as Part 18\'s effective date. Exact initial scope and agency application dates are not asserted here.'
            else:
                candidate['candidate']='The 1946 temporary regulations recast the corresponding host-rule subject and supersede Part 18 under EO 9691.'
                candidate['date_qualification']='The introduction provides thirty days from the February 4 order, with optional earlier agency operation. Ordinary addition gives March 6; EO 9830 section 3.2 identifies March 7, 1946 as the temporary regulations\' effective date. This earlier-candidate date issue is preserved. The 1942 section 18.11 list omits Rule XI; no 1942 supersession of EO 8179 item 3 is asserted from that list.'
        j['whole_order_end']['mechanism']=j['operative_clauses'][0]['first_end']['mechanism']
        residual=j['savings_residuals'];residual['reason']='EO 9830 contains no savings clause for either target and replaces the Civil Service Rules while expressly revoking the targets. Completed appointments and promotions and acquired status may remain saved acts under successor authority; this does not by itself continue the revoked source. EO 9691 section 9 protects acquired reemployment rights generally. Temporary regulation 27.16(g) retains status and tenure and awards the same benefits as reinstatement under Rule IX, so it is a material incorporation/savings candidate. Those regulations are expressly transitional until revision of the Civil Service Rules. EO 9830 replaces the Rules, prescribes successor Commission standards and revokes the targets without preserving their terms. The bounded check identified no current application of an old target term. No finding is made that every individual\'s accrued rights ceased; such saved acts are excluded from continuing source authority under TC08.'
        for r in residual['sources']:
            if r['sha256']=='66eea8c88ed91c1f37339b7146ce206d51700776d7f96b2e3997f003698936bc':r['local_path']='research/excavator/production-cost-trace-2026-10-26/acquisition-b1-9691/pdf/'+r['sha256']+'.pdf'
        j['producer_qualifications']={'endpoint_convention':'Owner October 21 unnamed-instruments ruling; not an estimate of the first historical loss of every application.','earlier_candidates_disclosed':True,'original_inventory_confirmed':True,'original_pages_confirmed':True,'source_grade_changed':False,'human_review':False,'packet_fingerprint':packet['fingerprint'],'notes':'Original item 1 of EO 8179 retains the exact OCR footnote within the held span; it is page furniture, not an added operative command.'}
    return claims

def correct_v4(j):
    j=copy.deepcopy(j);a=BASE/'acquisition-b1-8514';tpath=Path('jobs/fr-originals/data/full_run/texts/EO_8514.txt');t=tpath.read_text();start=t.index('EXECUTIVE ORDER');stop=t.index('EXECUTIVE ORDER',start+1);raw='d18dc8f5621fe056733f17fe0b17e7a1513aac9ba46988826a046b51a06289ae';local=a/'pdf'/f'{raw}.pdf'
    r={'url':'https://www.govinfo.gov/content/pkg/FR-1940-08-16/pdf/FR-1940-08-16.pdf','sha256':raw,'page_or_item':'5 FR 2857, PDF page 1, complete EO8514; signed August13, filed August14, published August16,1940; official target page inspected','local_path':str(local),'text_path':str(tpath),'text_sha256':hashlib.sha256(tpath.read_bytes()).hexdigest(),'char_start':start,'char_end':stop,'quote':t[start:stop]}
    old=next(x for x in j['savings_residuals']['sources']if x['sha256'].startswith('66eea8'))
    c=next(x for x in j['operative_clauses']if x['scope_id']=='EO:8179#rule-X-6a')
    c['later_events'].insert(0,{'effective_date':'1940-08-13','actor':'EO:8514','mechanism':'Commission permission to transfer probationers to appropriate positions directly concerned with national defense; a distinct exception to the absolute-appointment transfer norm','source':r,'reason':'The complete order has no delayed effective term, so August13 signing is used for this authorization. It contains no six-month minimum. It predates EO8707 and is not subsumed by that later exception for persons completing six months in a longer probation. It does not name EO8179 or end its entire host-rule footprint.','before_text':c['original_operative_text'],'after_text':r['quote']})
    c['later_events'].append({'effective_date':'1946-02-04','actor':'EO:9691','mechanism':'Express revocation of the distinct EO8514 authorization; general acquired-reemployment-rights saving retained','source':copy.deepcopy(old),'reason':'Section9 expressly names and revokes EO8514, signedFebruary4 with no delayed term for this revocation. Its following sentence protects acquired reemployment rights under any law, order, regulation or administrative procedure. This ends the8514exception authority; it does not revoke EO8179 or establish that every transfer right disappeared, nor does it by itself restore all applications displaced by other wartime regulations.'})
    c['reason']+=' EO8514 is separately recorded from August13,1940 to its express revocation by EO9691 on February4,1946. Its national-defense scope lacks the six-month minimum of EO8707 and cannot be omitted merely because a later host-rule amendment is disclosed.'
    j['earlier_candidate_ends'].insert(0,{'scope_id':c['scope_id'],'candidate':'EO8514 authorizes the Commission to permit probationary transfers to positions directly concerned with national defense, qualifying the absolute-appointment rule before EO8707.','source':r,'date_qualification':'Signed August13,1940, with no delayed operative term; filed August14 and published August16. These publication/custody dates are distinct from the authorization date.','disposition':'Disclosed earlier partial scope exception under the October21 unnamed-instruments ruling. EO8514 does not name EO8179 and is not substituted for the target\'s May1,1947 named endpoint. It is independently material because it has no six-month minimum. EO9691 section9 expressly revokes it on February4,1946 and saves acquired reemployment rights generally.','follow_through_source':copy.deepcopy(old)})
    j['research_rationale']+='\n\nCorrection after independent review: EO8514 is a distinct earlier exception affecting item2. It permits Commission-approved probationary transfers into positions directly concerned with national defense without a six-month minimum. EO8707 does not subsume it. The authorization begins on August13,1940 under its immediate operative wording and is expressly revoked by EO9691 section9 on February4,1946. The acquired-reemployment-rights saving is retained without assuming all rights were extinguished or all other wartime limitations were removed. This member-specific exception and its end are pinned in the actual item2 later events and earlier-candidate disclosure; the May1,1947 named target endpoint remains unchanged under the owner convention.'
    j['savings_residuals']['reason']+=' The separately preserved EO8514 national-defense transfer exception was expressly revoked by EO9691 section9. The general acquired-rights saving follows that revocation; no inference is made that it saved EO8514 or EO8179 as continuing source authority.'
    j['producer_qualifications']['correction_v4']='EO8514 omission identified by independent reviewT9; original inventory, endpoint and all EO8300v3object fields unchanged.'
    return j

if __name__=='__main__':
    try:
        claims,packet=build();claims=finalize_v3(claims,packet)
        j=correct_v4(claims['EO:8179']);other=claims['EO:8300']
        objects={'EO_8179.CLAIM.v4.json':j,'EO_8300.CLAIM.v3.json':other}
        for name,obj in objects.items():(OUT/name).write_text(json.dumps(obj,indent=2))
        combined=''.join(json.dumps(z,sort_keys=True)+'\n'for z in [j,other]);(OUT/'CLAIMS.v4.reconstructed.jsonl').write_text(combined)
        actual=hashlib.sha256(combined.encode()).hexdigest()
        report={'status':'exact_historical_bytes_recovered'if actual==EXPECTED_COMBINED else 'reconstructed_new_bytes_not_historical_approval','expected_combined_sha256':EXPECTED_COMBINED,'actual_combined_sha256':actual,'combined_exact':actual==EXPECTED_COMBINED,'orders':{name:{'artifact_sha256':hashlib.sha256((OUT/name).read_bytes()).hexdigest(),'claim_sha256':csha(obj)}for name,obj in objects.items()},'independent_review':'No review bytes reconstructed; root owns restoration and exact-version approval verification.','research_repeated':False}
        (OUT/'RECOVERY_RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    except Exception as e:
        (OUT/'RECOVERY_BLOCKED.json').write_text(json.dumps({'error':str(e),'type':type(e).__name__,'exact_bytes_recovered':False},indent=2));raise
