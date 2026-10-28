"""Enter revised producer judgments in ordinary native CSV; no claim construction."""
import pathlib,csv,json,shutil
P=pathlib.Path(__file__).resolve().parent;B=P.parents[1];R=B.parent;old=R/'packet-b2-final-v8/producers/batch2'
def j(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
with (B/'decisions.csv').open() as f:rd=csv.DictReader(f);fields=rd.fieldnames;fresh=list(rd)
with (old/'decisions.v1.csv').open() as f:prior={r['instrument_id']:r for r in csv.DictReader(f)}
shutil.copyfile(B/'decisions.csv',P/'decisions.blank.csv');shutil.copyfile(B/'clauses.csv',P/'clauses.blank.csv')
correction=('Correction after independent source examination: the prior proposal omitted the April 1946 version of temporary reinstatement regulation §27.9. The February published §27.9(a)(1) used completed probation or absolute appointment. The April2 Commission instrument, filed April12 and published April16 at11FR4143/4145, expressly effective March7,1946, adds an exception for(a)(6). That exception permits reinstatement after separation during probation only in the same agency, type of position, grade and locality, within one year except for preference eligibles, to complete probation. It has no six-month service minimum. Separately, revised(d) permits conversion of war-service indefinite appointments after separation of30days or more from probational, probational-indefinite or permanent appointments, with six months total satisfactory service, at agency discretion without Commission prior approval, subject to report and post-audit. These provisions must not be merged. They differ from8707 broad any-part-of-service reinstatement after six satisfactory months in a long-probation position. The amendment is retroactive to March7; no finding is made that the initial February completed-probation condition remained unqualified throughout March–July. July§27.9(b)(3) modifies the intervening April certificate version. The explicit date establishes revised§27.9 timing, not every other Part27 section effective date. April does not name8707, so the owner convention retains May1,1947 as its named endpoint. Successor rules granting completion of probation do not by themselves preserve or revive8707authority. ')
newtext=('The initial February-published Part27§27.9(a)(1) used completed probation/absolute appointment; the April amendment expressly effective March7,1946 adds(a)(6) probation-separated reinstatement within same agency/type/grade/locality, one year with preference waiver, to complete probation, without a six-month minimum, plus the separate(d) six-month-total-service war-service conversion route. These versions and the later July certificate amendment must be distinguished; no blanket completed-probation requirement for the whole1946interval is asserted. §27.10')
needle='Part27§27.9requires completedprobation/absoluteappointment for ordinaryreinstatement, materially differs from8707six-monthlong-probationpermission;§27.10'
for r in fresh:
 saved=prior[r['instrument_id']];fingerprint=r['dossier_sha256'];r.update(saved);r['dossier_sha256']=fingerprint;r['approved']='true';r['outcome']='submit'
 r['research_rationale']+=' Fresh packet v9 explicitly reaffirms the same original inventory, original/page confirmations, selected sources, dates and member judgments against their unchanged held bytes; old producer approval is not inherited as an independent review. '
 if r['instrument_id']=='EO:8705':
  r['research_rationale']+=' The newly held April§27.9 source concerns reinstatement; it changes no8705politics, retention or withholding-salary footprint or prior savings/current-application judgment. '
 else:
  assert r['research_rationale'].count(needle)==1;r['research_rationale']=r['research_rationale'].replace(needle,newtext)+correction
  r['earlier_end_check']=r['earlier_end_check'].replace('1946Part27FebandJulyversionswithdatequalification','Februarypublished/AprilretroactiveMarch7/July1946Part27versionswithspecificdatequalification')
  r['savings_reason']+=' The April§27.9(a)(6) exception and(d) conversion route create successor regulatory permissions and may yield acquired appointments/status; neither names8707 or preserves its prospective terms. Preserve those rights/status and the existing§27.16(g) savings analysis, without treating analogous completion-of-probation words as a revival. '
  r['savings_check']=r['savings_reason']
  notes=json.loads(r['source_notes'])
  for n in notes:
   if n['id']=='SUPPLEMENT:prior-held-5':
    n['reason']='Initial February-published§27.9(a)(1)completed-probation/absolute-appointment text must be read with April retroactive March7(a)(6)exception and(d)conversion route, then July certificate amendment; no unchanged February regime asserted. Initial§27.10transfer version is separately qualified by later host changes.'
    n['date_qualification']='April expressly establishes revised§27.9 effectiveMarch7,1946; the general initial Part27intro date qualification remains for other provisions.'
   if n['id']=='SUPPLEMENT:part27-july1946':
    n['reason']+=' Its§27.9(b)(3) adds a certificate rule to the intervening April§27.9(b)version, not an untouched February version.'
  notes.extend([{'id':'SUPPLEMENT:april1946-reinstatement-page1','reason':'CSC§27.9(a)(1)retains completed-probation/absolute-appointment general condition but expressly adds except-as-provided-in(a)(6). This is the Commission regulation adjacent to EO9712, not an EO9712acting provision. Complete continuation onpage3 is also selected. Before/after initialFebruary and Aprilamended versions are retained.','date_qualification':'ExpressMarch7,1946 effective date inpage3continuation; Commission signedApril2/filedApril12/publishedApril16. No universal Part27date inferred.'},{'id':'SUPPLEMENT:april1946-reinstatement-page3','reason':correction,'date_qualification':'ExpressretroactiveMarch7,1946 for amended§27.9. One-year/preference limit in(a)(6) and six-month-total-service condition in(d) are eligibility limits, not8707end dates.'}])
  r['source_notes']=j(notes)
with (B/'decisions.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(fresh)
with (old/'clauses.v1.csv').open() as f:rd=csv.DictReader(f);cf=rd.fieldnames;clauses=list(rd)
for c in clauses:
 if c['scope_id']=='EO:8707#rule-IX-section-2c':
  c['later_events']=j([{'id':'SUPPLEMENT:april1946-reinstatement-page3','effective_date':'1946-03-07','effective_date_confirmed':True,'mechanism':'amendment_of_unnamed_temporary_reinstatement_regulation_27.9;_not_revocation_of_EO8707'}])
  c['reason']+=' April amended§27.9expressly effectiveMarch7 adds the distinct same-agency/type/grade/locality probationary reinstatement exception with one-year/preference qualification and completion of probation; separately(d)war-service conversion uses six months total service. February-before/April-after/July-follow-on text is pinned and explained; does not alter the named May1,1947target endpoint. '
with (B/'clauses.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=cf);w.writeheader();w.writerows(clauses)
for n in ['decisions','clauses']:shutil.copyfile(B/(n+'.csv'),P/(n+'.corrected-v1.csv'))
(P/'CORRECTION_RATIONALE.v1.txt').write_text(correction+'\n')
print('Corrected/reaffirmed',len(fresh),'members',len(clauses),'clauses')
