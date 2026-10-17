import unittest
from ofr_batch_forge import build

def data():
    conversion=[]
    for n in range(3359):
        conversion.append({
         'instrument_id':'EO:'+str(n+20000),
         'provisional_status':'no' if n%2 else 'yes',
         'decision_origin':'opus_checkpoint2' if n<844 else 'legacy',
         'conversion_lane':'trace_end_or_footprint',
         'research_triage_not_confidence':'10',
         'opus_narrative_materialized':'yes' if n<844 else 'no',
         'opus_footprint_claim':'true' if n<844 else 'not_in_notes',
         'date_mentions_unclassified':'1950-01-01' if n<844 else '',
         'possible_mechanism_keywords':'statutory' if n<844 else '',
         'source_entry_locally_preserved':'1' if n<14 else '0',
         'structured_history_rows':'0',
         'whole_lifecycle_completed':'no',
        })
    sources=[]
    statutes=[]
    cursor=0
    for f in range(98):
        # Ten shared statute families spanning 42 case links; 88 other
        # shared-authority families spanning the remaining 310 links.
        family='STAT::'+str(f) if f<10 else 'EO::'+str(20000+f)
        count=5 if f<2 else 4 if f<10 else 4 if f<56 else 3
        for j in range(count):
            id_='EO:'+str(20000+cursor)
            cursor+=1
            sources.append({'authority':family,'cited_in':id_,'certified':'no'})
            if f<10:
                acquired=len(statutes)<18
                statutes.append({'source_key':family,'instrument_id':id_,
                    'citation':family,'acquired_pdf_bytes':'yes' if acquired else 'no',
                    'stored_local_pdf_candidate_path':'research/example.pdf' if acquired else '',
                    'sha256_acquired_candidate_pdf':'a'*64 if acquired else '',
                    'human_certified':'no'})
    assert len(sources)==352 and len(statutes)==42
    causal=[{'instrument_id':'EO:'+str(20000+n),
             'possible_event_date_mentions_NOT_FINDINGS':'1'} for n in range(844)]
    return conversion,sources,statutes,causal

class MassBatchTest(unittest.TestCase):
    def test_no_auto_certification_and_total_assignments(self):
        c,s,t,n=data()
        m=build(c,s,t,n,{'fixture':'x'})
        self.assertEqual(m['metrics']['case_level_batch_assignments'],3359)
        self.assertEqual(m['metrics']['candidate_case_source_edges'],352)
        self.assertEqual(m['metrics']['human_certified_dossiers'],0)
        self.assertLessEqual(m['metrics']['actual_largest_batch'],20)
        self.assertEqual(len(set(x['instrument_id'] for x in m['assignments'])),3359)
        self.assertEqual(sum(x['case_count'] for x in m['batches']),3359)
    def test_frozen_identity_gate(self):
        c,s,t,n=data()
        c[1]['instrument_id']=c[0]['instrument_id']
        with self.assertRaises(ValueError):
            build(c,s,t,n,{})
    def test_no_preapproved_links(self):
        c,s,t,n=data()
        s[0]['certified']='yes'
        with self.assertRaises(ValueError):
            build(c,s,t,n,{})


    def test_original_source_candidates_are_linked_without_certification(self):
        c,s,t,n=data()
        urls=[]
        custody=[]
        for i,case in enumerate(c):
            ident=case['instrument_id']
            url=('https://www.govinfo.gov/content/pkg/FR-1949/pdf/'+
                 ident.replace(':','-')+'.pdf') if i<386 else ''
            urls.append({
                'instrument_id':ident,
                'provisional_status_UNVERIFIED':case['provisional_status'],
                'selected_literal_URL':url,
                'PDF_candidate':url,
                'selected_format':'pdf_url' if url else '',
                'document_identity_authenticated':'no',
                'operative_clause_legal_effect_verified':'no',
                'independent_human_review':'no'})
            if i<386:
                state=('PDF_BYTES_CAPTURED_NOT_AUTHENTICATED'
                       if i==0 else 'not_attempted')
                custody.append({
                    'instrument_id':ident, 'official_PDF_candidate_URL':url,
                    'custody_state':state,
                    'source_repository_path':(
                        'research/stage21/original_sources/EO_'+ident[3:]+'.pdf'
                        if i==0 else ''),
                    'sha256_source_bytes_if_present':'a'*64 if i==0 else '',
                    'original_EO_identity_and_pages_human_verified':'no',
                    'operative_clause_scope_verified':'no',
                    'causal_effects_verified':'no',
                    'independent_human_certified':'no'})
        m=build(c,s,t,n,{'fixture':'x'},urls,custody)
        self.assertEqual(m['metrics']['provisional_cases_with_PDF_source_candidate'],386)
        self.assertEqual(m['metrics']['original_candidate_PDFs_locally_captured'],1)
        self.assertEqual(m['metrics']['human_certified_dossiers'],0)
        match=next(row for batch in m['batches'] for row in batch['cases']
                   if row['instrument_id']==c[0]['instrument_id'])
        self.assertEqual(match['original_legal_text_and_page_authenticated'],False)
        self.assertTrue(match['captured_original_PDF_candidate_repository_path'])
        custody[0]['independent_human_certified']='yes'
        with self.assertRaises(ValueError):
            build(c,s,t,n,{},urls,custody)

if __name__ == '__main__':
    unittest.main()
