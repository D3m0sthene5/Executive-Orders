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
    for f in range(98):
        for j in range(2 if f<40 else 3):
            if len(sources)>=352:break
            idx=(f*5+j)%3359
            sources.append({'authority':'EO::'+str(f+20000),
                 'cited_in':'EO:'+str(idx+20000),'certified':'no'})
    # Fill remaining without creating new families or duplicate pairs.
    x=0
    seen={(s['authority'],s['cited_in']) for s in sources}
    while len(sources)<352:
        fam=x%98;case=(x*13+37)%3359;x+=1
        pair=('EO::'+str(fam+20000),'EO:'+str(case+20000))
        if pair in seen:continue
        seen.add(pair);sources.append({'authority':pair[0],
                'cited_in':pair[1],'certified':'no'})
    statutes=[]
    for j in range(42):
        s=sources[j]
        # Must point at existing case authority pairs. For fixture, treat
        # first five families as statute families.
        authority='STAT::'+str(j//10)
        # Change source cases in fixture to statute names before compiling.
        sources[j]['authority']=authority
        statutes.append({'source_key':authority,'instrument_id':s['cited_in'],
           'citation':authority,'acquired_pdf_bytes':'yes' if j<18 else 'no',
           'stored_local_pdf_candidate_path':'research/example.pdf' if j<18 else '',
           'sha256_acquired_candidate_pdf':'a'*64 if j<18 else '',
           'human_certified':'no'})
    # Deterministically remove any identical (authority,case) pairs; keep 352
    # edges by using distinct cases within each group. Fix initial source map.
    pairs=set()
    for j,s in enumerate(sources):
        pair=(s['authority'],s['cited_in'])
        if pair in pairs:
            s['cited_in']='EO:'+str(30000+j)
        pairs.add((s['authority'],s['cited_in']))
        if j<42:statutes[j]['instrument_id']=s['cited_in']
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

if __name__ == '__main__':
    unittest.main()
