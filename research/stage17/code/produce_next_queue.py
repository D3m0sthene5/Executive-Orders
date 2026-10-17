#!/usr/bin/env python3
import pathlib,sqlite3,json,csv,collections
root=pathlib.Path(__file__).resolve().parent.parent;c=sqlite3.connect(root/'data'/'AFTERLIFE_STAGE17_CANONICAL.sqlite');c.row_factory=sqlite3.Row
rows=[]
# Original-forward work: all 155 temporary orders that Opus treated as NO; recover originals, scope each sunset and any extensions.
for x in c.execute("SELECT o.instrument_id, o.source_text_obtained, o.source_grade, o.review_directory_declared, i.issuance_date FROM opus_checkpoint2_import o JOIN instruments i ON o.instrument_id=i.id WHERE origin_lane='C_NARA_TEMPORARY' ORDER BY i.issuance_date"):
 r=dict(x);rows.append(dict(priority='P1',strategy='ORIGINAL_FORWARD',id=r['instrument_id'],family='OPUS_TEMPORARY_155',known='legacy NO only; historical first cause UNKNOWN',required='Reinspect original EO; extract all scope-specific sunsets, amendments, later extensions and savings; validate earliest actual ending',source_state='OPUS_COMPANION_ORIGINALS_NOT_ATTACHED',confidence='UNVERIFIED_CAUSAL_HISTORY'))
# Backward source cases, NOT automatically legal endings.
for source in ['EO:12553','EO:3461']:
 items=c.execute('SELECT affected_instrument,effective_date,scope FROM legal_event WHERE actor_instrument=?',(source,)).fetchall()
 for r in items:
  rows.append(dict(priority='P2',strategy='SUCCESSOR_BACKWARD',id=r['affected_instrument'],family=source,known='formal predecessor link only, no first cessation implication',required='Read full predecessor; check whether its provisions still operated immediately before successor; account for savings and partial clause scope',source_state='ARCHIVAL_RETRIEVAL_NEEDED',confidence='FORMAL_EVENT_NOT_CAUSAL_PROOF'))
# Material newly catalogued early years.
for r in c.execute('SELECT * FROM stage17_catalogue_candidate ORDER BY date_guess,catalogue_key'):
 rows.append(dict(priority='P1',strategy='ALL_HISTORY_CENSUS',id=r['catalogue_key'],family='LORD_1789_1790',known=r['date_guess']+' archival printed entry',required='Get cited Sparks/Richardson/Annals original; authenticate presidential capacity, distinct physical document, and order versus letter; resolve two 1790 same-date references',source_state='LORD_PRINTED_SCAN_CACHED_ORIGINAL_SIGNED_NOT_ACQUIRED',confidence='BIBLIOGRAPHIC_ONLY'))
for r in c.execute('SELECT marker_id,pdf_page,year_heuristic,month,day FROM lord_date_markers ORDER BY pdf_page,marker_id'):
 rows.append(dict(priority='P3',strategy='ALL_HISTORY_CENSUS',id=r['marker_id'],family='LORD_DATE_MARKERS_1023',known=f'printed scan page {r["pdf_page"]}, year OCR {r["year_heuristic"]}',required='Visual page inspect; locate date-text source reference, signer, exact document; crosswalk aliases and remove duplicates before admission',source_state='INDEX_OCR_POSSIBLY_CORRUPTED',confidence='OCR_LEAD_ONLY'))
# Distinct missing source and high-relevance blockers.
for id,req in [
 ('OPUS_STAGE11_CHECKPOINT2_EVIDENCE_ORIGINALS.zip','Obtain Opus evidence-original companion with original images and SHA manifest; unlock independent reinspection of 540 provisional status records'),
 ('EO:4872','Retrieve signed original land withdrawal and complete subsequent property-disposition chain'),
 ('EO:UN:executive-orders-01:row:3','Obtain original signed 1856 historical unnumbered document, distinguish archival source row from presidential instrument'),
 ('EO:9616','Recover full appointment/beneficiary/survivor-right savings text; substantive NO vs any-effect UNKNOWN'),
 ('EO:12446','Retrieve surviving host provision and entire successor-amendment chain for bounded YES'),
 ('EO:13286','Verify host-amendment attribution versus regulation independence; preserve existing v3 hold')]:
  rows.append(dict(priority='P1',strategy='TARGETED_SOURCE_ACQUISITION',id=id,family='CRITICAL_SOURCE_GAP',known='Previously reported limitation',required=req,source_state='MISSING_ORIGINALS_OR_UNRESOLVED_HOST',confidence='NOT_CERTIFIED'))
path=root/'reports'/'NEXT_LEVERAGE_QUEUE_STAGE17.csv';keys=list(rows[0]);withopen=path.open('w',newline='');w=csv.DictWriter(withopen,fieldnames=keys);w.writeheader();w.writerows(rows);withopen.close()
counts=collections.Counter((x['strategy'],x['family']) for x in rows)
(root/'reports'/'NEXT_QUEUE_SUMMARY.json').write_text(json.dumps({'total_action_rows_not_disjoint_research_population':len(rows),'queue_groups':[{'strategy':a,'family':b,'rows':n} for (a,b),n in counts.items()]},indent=2)+'\n')
print('queue size',len(rows),'classes',counts)
