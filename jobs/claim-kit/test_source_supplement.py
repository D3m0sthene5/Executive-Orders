"""Held-excerpt preparation tested through ordinary CSV application."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import assemble as A
import batch as B
import source_supplement as S
import test_build as F


class SourceSupplementTests(unittest.TestCase):
    def setUp(self):
        self.f = F.BuildIntegrationTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.repo = self.f.repo
        self.f.run_build()
        self.parent = self.repo / 'research/test/parent'
        B.prepare(self.repo, self.f.out, self.parent, ['EO:1'], 'synthetic-producer')
        self.code = self.repo / 'jobs/claim-kit/source_supplement.py'
        self.code.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(S.__file__, self.code)
        self.patcher = patch.object(S, '__file__', str(self.code))
        self.patcher.start(); self.addCleanup(self.patcher.stop)
        _, self.ds = B.load_packet(self.parent, self.repo)
        actor = next(v for v in self.ds['EO:1']['evidence'].values() if v.get('actor_id') == 'EO:5')
        src = copy.deepcopy(actor['source'])
        src = {k:src[k] for k in ['url','sha256','text_path','text_sha256','page_or_item']}
        src['local_path'] = src['text_path']
        self.entry = {'alias':'held-revocation','instrument_ids':['EO:1'], 'actor_id':'EO:5',
                      'reason':'Producer must examine this exact held excerpt.', 'source':src,
                      'char_start':actor['char_start'],'char_end':actor['char_end']}
        self.decl = self.repo / 'research/test/sources.json'
        self.write_decl([self.entry])
        self.dest = self.repo / 'research/test/supplemented'

    def write_decl(self, entries):
        self.decl.write_text(json.dumps({'schema':S.SCHEMA,'sources':entries}))

    def prepare(self):
        return S.prepare(self.repo, self.parent, self.decl, 'synthetic-producer', self.dest)

    def fill(self, mechanism=True):
        sheet = self.f.decision('EO:1')
        rows = B.rows(self.dest/'decisions.csv')
        r = rows[0]
        r.update(outcome='submit',approved='true',original_confirmed='true',inventory_confirmed='true',
                 original_pages_confirmed='false',research_rationale=sheet['research_rationale'],
                 savings_state=sheet['savings']['state'],savings_source_id=sheet['savings']['source_id'],
                 savings_reason=sheet['savings']['reason'],search_ids=json.dumps(sheet['search_ids']),
                 conflict_resolutions='{}',unresolved_material_gaps='[]')
        for k in ['earlier_end_check','scope_check','independent_command_check','savings_check']:
            r[k]='Explicit synthetic member examination of this issue.'
        clauses = B.rows(self.dest/'clauses.csv')
        for c in clauses:
            decision = next(x for x in sheet['clauses'] if x['scope_id']==c['scope_id'])
            c.update({k:json.dumps(v) if isinstance(v,(bool,list,dict)) else (v or '') for k,v in decision.items()})
            c['end_id']='SUPPLEMENT:held-revocation'
            c['mechanism']='revocation' if mechanism else ''
        B.csv_write(self.dest/'decisions.csv', B.ROW_FIELDS, rows)
        B.csv_write(self.dest/'clauses.csv', B.CLAUSE_FIELDS, clauses)

    def test_native_csv_apply_and_strict_gate(self):
        receipt=self.prepare();self.fill()
        result=B.apply(self.repo,self.dest,self.dest/'applied')
        self.assertEqual(result['counts'],{'assembled_proposal':1})
        claim=json.loads((self.dest/'applied/CLAIMS.proposed.jsonl').read_text())
        _,ds=B.load_packet(self.dest,self.repo)
        self.assertEqual(A.check_claim(claim,self.repo,ds['EO:1']),[])
        self.assertEqual(claim['operative_clauses'][0]['first_end']['mechanism'],'revocation')
        self.assertFalse(receipt['producer_approval']);self.assertFalse(receipt['independent_review'])

    def test_absent_mechanism_not_inferred(self):
        self.prepare();self.fill(mechanism=False)
        r=B.apply(self.repo,self.dest,self.dest/'applied')
        self.assertEqual(r['counts'],{'rejected':1})

    def test_source_notes_native_csv_keep_qualified_source_without_event_date(self):
        self.prepare();self.fill()
        rows=B.rows(self.dest/'decisions.csv')
        rows[0]['source_notes']=json.dumps([{'id':'SUPPLEMENT:held-revocation',
            'reason':'Earlier scope candidate requires independent legal examination.',
            'date_qualification':'Publication is established; initial application date is unresolved.'}])
        B.csv_write(self.dest/'decisions.csv',B.ROW_FIELDS,rows)
        result=B.apply(self.repo,self.dest,self.dest/'applied')
        self.assertEqual(result['counts'],{'assembled_proposal':1})
        claim=json.loads((self.dest/'applied/CLAIMS.proposed.jsonl').read_text())
        self.assertEqual(len(claim['source_notes']),1)
        self.assertNotIn('effective_date',claim['source_notes'][0])
        self.assertNotIn('date',claim['source_notes'][0])
        _,ds=B.load_packet(self.dest,self.repo)
        self.assertEqual(A.check_claim(claim,self.repo,ds['EO:1']),[])
        claim['source_notes'][0]['source']['quote']='Invented source text.'
        self.assertTrue(A.check_claim(claim,self.repo,ds['EO:1']))

    def test_source_notes_reject_free_source_missing_id_and_fact_route(self):
        self.prepare();_,ds=B.load_packet(self.dest,self.repo)
        for note in [{'id':'missing','reason':'Specific candidate.','date_qualification':'Not settled.'},
                     {'id':'FACT:unreviewed','reason':'Specific candidate.','date_qualification':'Not settled.'},
                     {'id':'SUPPLEMENT:held-revocation','reason':'Specific candidate.',
                      'date_qualification':'Not settled.','source':{'quote':'Injected'}}]:
            sheet=self.f.decision('EO:1');sheet['dossier_sha256']=ds['EO:1']['fingerprint'];sheet['source_notes']=[note]
            claim,errors=A.assemble(sheet,ds['EO:1'],self.repo)
            self.assertTrue(errors)

    def test_old_csv_without_new_columns_retains_act_fallback(self):
        self.prepare();self.fill()
        rows=B.rows(self.dest/'decisions.csv');clauses=B.rows(self.dest/'clauses.csv')
        for r in rows:r.pop('source_notes')
        end=self.f.decision('EO:1')['clauses'][0]['end_id']
        for c in clauses:c.pop('mechanism');c['end_id']=end
        B.csv_write(self.dest/'decisions.csv',[k for k in B.ROW_FIELDS if k!='source_notes'],rows)
        B.csv_write(self.dest/'clauses.csv',[k for k in B.CLAUSE_FIELDS if k!='mechanism'],clauses)
        result=B.apply(self.repo,self.dest,self.dest/'applied')
        self.assertEqual(result['counts'],{'assembled_proposal':1})

    def test_existing_human_review_requires_note_url_in_checked_sources(self):
        # Synthetic fixture only; this creates no real review or certification.
        self.entry['source']['url']='https://example.gov/qualified-context'
        self.write_decl([self.entry]);self.prepare();self.fill()
        rows=B.rows(self.dest/'decisions.csv')
        rows[0]['source_notes']=json.dumps([{'id':'SUPPLEMENT:held-revocation',
            'reason':'Additional qualified context.','date_qualification':'No exact event date asserted.'}])
        B.csv_write(self.dest/'decisions.csv',B.ROW_FIELDS,rows)
        # Select the original ACT ending, so the note URL is a separate citation.
        clauses=B.rows(self.dest/'clauses.csv')
        for c in clauses:c['end_id']=self.f.decision('EO:1')['clauses'][0]['end_id']
        B.csv_write(self.dest/'clauses.csv',B.CLAUSE_FIELDS,clauses)
        B.apply(self.repo,self.dest,self.dest/'applied')
        claim=json.loads((self.dest/'applied/CLAIMS.proposed.jsonl').read_text())
        urls={claim['original_representation']['url'],claim['whole_order_end']['source']['url'],
              claim['savings_residuals']['source']['url']}
        review={'schema':'eo-lifecycle-review/v1','instrument_id':'EO:1','claim_sha256':A.canonical_sha(claim),
                'reviewer':'synthetic-reviewer','reviewer_role':'independent_human','decision':'uphold',
                'rationale':'Synthetic structural coverage fixture; no actual human reviewed this case.',
                'checked_source_urls':sorted(urls),'reviewed_on':'2026-10-27'}
        gate=A._gate(self.repo)
        self.assertIn('unchecked_cited_source',gate.validate_review(review,claim))
        review['checked_source_urls'].append(self.entry['source']['url'])
        self.assertEqual(gate.validate_review(review,claim),[])

    def test_inherited_fields_unchanged(self):
        self.prepare();_,ds=B.load_packet(self.dest,self.repo)
        actual=copy.deepcopy(ds['EO:1']);actual.pop('source_supplement');actual.pop('fingerprint')
        actual['evidence'].pop('SUPPLEMENT:held-revocation')
        expected=copy.deepcopy(self.ds['EO:1']);expected.pop('fingerprint')
        self.assertEqual(actual,expected)
        e=ds['EO:1']['evidence']['SUPPLEMENT:held-revocation']
        self.assertNotIn('mechanism',e);self.assertNotIn('effective_date',e);self.assertNotIn('grade',e)

    def test_invalid_hashes_spans_and_injected_grade(self):
        variants=[]
        for k in ['sha256','text_sha256']:
            e=copy.deepcopy(self.entry);e['source'][k]='0'*64;variants.append(e)
        for a,b in [(True,3),(-1,3),(0,9999999),(4,4)]:
            e=copy.deepcopy(self.entry);e.update(char_start=a,char_end=b);variants.append(e)
        e=copy.deepcopy(self.entry);e['source']['grade']='official';variants.append(e)
        for e in variants:
            with self.subTest(e=e),self.assertRaises(ValueError):
                S.derive(self.repo,self.ds,{'schema':S.SCHEMA,'sources':[e]}, {})

    def test_foreign_target_alias_and_duplicate_refused(self):
        for change in [{'instrument_ids':['EO:2']},{'alias':'ACT:EO:1>EO:5'}]:
            e={**self.entry,**change}
            with self.assertRaises(ValueError):S.derive(self.repo,self.ds,{'schema':S.SCHEMA,'sources':[e]}, {})
        with self.assertRaises(ValueError):S.derive(self.repo,self.ds,{'schema':S.SCHEMA,'sources':[self.entry,self.entry]}, {})

    def test_symlink_escape_refused(self):
        link=self.repo/'escaped';link.symlink_to(Path(__file__).resolve())
        e=copy.deepcopy(self.entry);e['source']['local_path']='escaped'
        with self.assertRaises(ValueError):S.derive(self.repo,self.ds,{'schema':S.SCHEMA,'sources':[e]}, {})

    def test_each_lineage_pin_enforced_by_native_load(self):
        self.prepare()
        for path in [self.decl,self.code,self.parent/'PACKET.json']:
            old=path.read_bytes();path.write_bytes(old+b' ')
            with self.subTest(path=path),self.assertRaises(ValueError):B.load_packet(self.dest,self.repo)
            path.write_bytes(old)
        self.assertEqual(S.verify(self.repo,self.dest)['orders'],1)

    def test_tampered_inherited_dossier_with_recomputed_fingerprint_refused(self):
        self.prepare();packet,ds=B.load_packet(self.dest,self.repo)
        ds['EO:1']['whole_order_status']='yes';ds['EO:1']['fingerprint']=A.canonical_sha(ds['EO:1'])
        encoded=B.encode(ds,self.repo)
        packet.update(encoded);packet.pop('fingerprint');packet['fingerprint']=B.digest(B.canon(packet).encode())
        B.dump(self.dest/'PACKET.json',packet)
        with self.assertRaisesRegex(ValueError,'changed supplemented dossier'):B.load_packet(self.dest,self.repo)

    def test_changed_raw_source_refused(self):
        self.prepare();path=self.repo/self.entry['source']['local_path'];path.write_bytes(path.read_bytes()+b' changed')
        with self.assertRaises(ValueError):B.load_packet(self.dest,self.repo)

    def test_stripped_lineage_cannot_bypass_native_validation(self):
        self.prepare();packet,ds=B.load_packet(self.dest,self.repo)
        ds['EO:1'].pop('source_supplement')
        ds['EO:1']['fingerprint']=A.canonical_sha(ds['EO:1'])
        packet.update(B.encode(ds,self.repo));packet.pop('fingerprint')
        packet['fingerprint']=B.digest(B.canon(packet).encode())
        B.dump(self.dest/'PACKET.json',packet)
        (self.dest/'SOURCE_SUPPLEMENT.json').unlink()
        with self.assertRaisesRegex(ValueError,'supplement lineage missing'):B.load_packet(self.dest,self.repo)

    def test_undecided_and_chained_parent_refused(self):
        for change in [{'whole_order_status':None},{'source_supplement':{'schema':'old'}}]:
            ds=copy.deepcopy(self.ds);ds['EO:1'].update(change);ds['EO:1']['fingerprint']=A.canonical_sha(ds['EO:1'])
            with self.assertRaises(ValueError):S.derive(self.repo,ds,{'schema':S.SCHEMA,'sources':[self.entry]}, {})


if __name__=='__main__':unittest.main()
