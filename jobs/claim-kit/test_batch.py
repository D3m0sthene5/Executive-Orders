"""Real assembler integration, lossless sharing and blocked-member retention."""
import csv
import json
from pathlib import Path
import unittest
import test_build as T
write_json=T.write_json
import batch


class BatchTests(T.BuildIntegrationTests):
    # Inherit the actual integration corpus, not its tests a second time.
    def packet(self,ids=('EO:1','EO:2')):
        self.run_build();dest=self.repo/'research/experiment/packet'
        batch.prepare(self.repo,self.out,dest,list(ids),'producer')
        return dest

    def fill(self,folder,iid='EO:1'):
        s=self.decision(iid);order=batch.rows(folder/'decisions.csv');clauses=batch.rows(folder/'clauses.csv')
        r=next(r for r in order if r['instrument_id']==iid)
        r.update(outcome='submit',approved='true',original_confirmed='true',inventory_confirmed='true',
            original_pages_confirmed='false',research_rationale=s['research_rationale'],
            savings_state=s['savings']['state'],savings_source_id=s['savings']['source_id'],savings_reason=s['savings']['reason'],
            search_ids=json.dumps(s['search_ids']),conflict_resolutions='{}',unresolved_material_gaps='[]')
        for k in ('earlier_end_check','scope_check','independent_command_check','savings_check'):r[k]='Explicit synthetic corpus review confirms this target-specific check.'
        for c in clauses:
            if c['instrument_id']==iid:
                decision=next(d for d in s['clauses'] if d['scope_id']==c['scope_id'])
                for k,v in decision.items():c[k]=json.dumps(v) if isinstance(v,(bool,list,dict)) else ('' if v is None else v)
        batch.csv_write(folder/'decisions.csv',batch.ROW_FIELDS,order)
        batch.csv_write(folder/'clauses.csv',batch.CLAUSE_FIELDS,clauses)

    def test_valla_context_attaches_without_approval_and_refuses_stale_claim(self):
        import shutil
        source=Path(__file__).resolve().parents[1]/'valla'
        target=self.repo/'jobs/valla';target.mkdir(parents=True)
        for name in ('valla.py','premises.json'):shutil.copyfile(source/name,target/name)
        self.run_build();folder=self.repo/'research/valla-test/packet'
        result=batch.prepare(self.repo,self.out,folder,['EO:1'],'producer')
        packet,ds=batch.load_packet(folder,self.repo)
        self.assertEqual(packet['valla_context']['automatic_approvals'],0)
        self.assertTrue(packet['valla_context']['whole_case_review_required'])
        self.assertIn('Valla review leads',(folder/'READ.md').read_text())
        # A new active version changes context, not the frozen packet or any approval.
        p=self.repo/'research/readiness/claims/new.jsonl';p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps({'schema':'eo-lifecycle-claim/v1','instrument_id':'EO:1',
            'research_rationale':'Every clause remains part of the order until revoked.'})+'\n')
        with self.assertRaisesRegex(ValueError,'changed Valla review context'):
            batch.load_packet(folder,self.repo)

    def test_lossless_roundtrip_shares_sources_and_full_text(self):
        p=self.packet();packet,dossiers=batch.load_packet(p,self.repo)
        self.assertEqual(dossiers,{iid:self.dossier(iid) for iid in ('EO:1','EO:2')})
        self.assertTrue(packet['text_blocks']);self.assertTrue(packet['shared_objects'])
        text=(p/'READ.md').read_text('utf-8')
        self.assertIn('Missing/overflow',text);self.assertIn('earlier ending',text)
        self.assertTrue(all(d['fingerprint'] in text for d in dossiers.values()))

    def test_explicit_rows_use_real_assembler_and_keep_blocked_case(self):
        p=self.packet();self.fill(p)
        result=batch.apply(self.repo,p,p/'applied')
        self.assertEqual(result['counts'],{'assembled_proposal':1,'unresolved':1})
        self.assertEqual(result['extraction_calls'],0);self.assertEqual(result['claims_published'],0)
        checked=batch.check(self.repo,p,p/'applied',actual=False)
        self.assertEqual(checked['strict_claim_pass'],1)
        self.assertEqual(checked['packet_members'],2)
        self.assertFalse((self.repo/'research/readiness/claims').exists())

    def test_changed_source_or_packet_rejected(self):
        p=self.packet();packet,_=batch.load_packet(p,self.repo)
        rel=next(iter(packet['held_text_file_pins']));(self.repo/rel).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'changed held source'):batch.apply(self.repo,p,p/'applied')

    def test_missing_member_cannot_disappear(self):
        p=self.packet();r=batch.rows(p/'decisions.csv')[:1];batch.csv_write(p/'decisions.csv',batch.ROW_FIELDS,r)
        with self.assertRaisesRegex(ValueError,'every packet member'):batch.apply(self.repo,p,p/'applied')

    def test_nonredundant_legal_fields_are_retained_in_readable_view(self):
        p=self.packet();packet,ds=batch.load_packet(p,self.repo)
        e=next(iter(ds['EO:1']['evidence'].values()))
        e['provision_text']='Unique retained exception outside the ordinary text alias.'
        e['alternative_provisions']=[{'id':'unique-alternative','text':'A unique unresolved saving provision.'}]
        text=batch.render(packet,ds)
        self.assertIn(e['provision_text'],text)
        self.assertIn(e['alternative_provisions'][0]['text'],text)

    def test_bounded_navigation_preserves_exact_source_text(self):
        p=self.packet();packet,ds=batch.load_packet(p,self.repo)
        tid=next(iter(packet['text_blocks']))
        self.assertIn(tid,batch.view(self.repo,p))
        self.assertTrue(batch.view(self.repo,p,source=tid).endswith(packet['text_blocks'][tid]['text']))
        self.assertIn(ds['EO:1']['fingerprint'],batch.view(self.repo,p,order='EO:1'))
        with self.assertRaisesRegex(ValueError,'outside packet'):batch.view(self.repo,p,order='EO:999')

    def test_missing_target_specific_review_is_actionable_failure(self):
        p=self.packet();self.fill(p)
        r=batch.rows(p/'decisions.csv');r[0]['earlier_end_check']='';batch.csv_write(p/'decisions.csv',batch.ROW_FIELDS,r)
        result=batch.apply(self.repo,p,p/'applied')
        self.assertEqual(result['counts']['rejected'],1)
        self.assertEqual(batch.check(self.repo,p,p/'applied',actual=False)['actionable_failures'][0]['instrument_id'],'EO:1')

    def test_existing_owner_and_other_reservations_are_preserved(self):
        self.run_build();lock=self.repo/'research/readiness/CLAIM_KIT_LOCK.json'
        write_json(lock,{'orders':{'EO:1':{'agent':'another'}}})
        before=lock.read_bytes()
        with self.assertRaisesRegex(ValueError,'reservation belongs'):batch.prepare(self.repo,self.out,self.repo/'research/x',['EO:1'],'producer')
        self.assertEqual(lock.read_bytes(),before)

    def test_own_term_bucket_is_not_shared_legal_family(self):
        self.run_build();d=self.dossier('EO:1');d['actor_provisions']=[]
        self.assertEqual(batch.family_groups({'EO:1':d}),[])

    def test_actual_shared_provision_groups_but_exception_changes_do_not(self):
        self.run_build();ds={i:self.dossier(i) for i in ('EO:1','EO:2')}
        # Put both targets under one *identical* operative paragraph.
        for iid,d in ds.items():
            d['actor_provisions']=['shared'];d['evidence']['shared']={'actor_id':'EO:5','text':'Orders 1 and 2 are revoked, except accrued rights.',
                'scope':'whole','source':{'sha256':'a'*64,'text_sha256':'b'*64}}
        self.assertEqual(batch.family_groups(ds)[0]['orders'],2)
        ds['EO:2']['evidence']['shared']['text']+=' Subject to a separate condition.'
        self.assertTrue(all(g['orders']==1 for g in batch.family_groups(ds)))

    def test_inventory_correction_rows_are_reconstructed_by_existing_assembler(self):
        p=self.packet(('EO:1',));self.fill(p)
        d=self.dossier('EO:1');original=d['evidence'][d['original_source_id']]
        # Preserve the operative body exactly while explicitly correcting its scope.
        c=batch.rows(p/'clauses.csv')[0];source=d['clauses'][0]
        c.update(scope_id='EO:1#reviewed',inventory_source_id=d['original_source_id'],
            inventory_char_start=str(source['char_start']),inventory_char_end=str(source['char_end']),
            inventory_reason='Synthetic original span independently selected to correct the extracted inventory.')
        batch.csv_write(p/'clauses.csv',batch.CLAUSE_FIELDS,[c])
        result=batch.apply(self.repo,p,p/'applied');self.assertEqual(result['counts'],{'assembled_proposal':1})
        claim=json.loads((p/'applied/CLAIMS.proposed.jsonl').read_text('utf-8'))
        self.assertEqual(claim['operative_clauses'][0]['scope_id'],'EO:1#reviewed')
        self.assertEqual(batch.check(self.repo,p,p/'applied',actual=False)['strict_claim_pass'],1)


    def test_every_direct_policy_dependency_change_requires_new_packet(self):
        from unittest import mock
        p = self.packet(('EO:1',))
        pins = batch.policy_code_pins()
        self.assertEqual(set(pins), set(batch.POLICY_CODE_FILES))
        for rel in batch.POLICY_CODE_FILES:
            with self.subTest(dependency=rel):
                changed = dict(pins); changed[rel] = '0'*64
                with mock.patch.object(batch, 'policy_code_pins', return_value=changed):
                    with self.assertRaisesRegex(ValueError, 'direct policy code changed'):
                        batch.apply(self.repo, p, p/'applied')
        # A properly hashed historical packet without the pins is still stale.
        packet = json.loads((p/'PACKET.json').read_text())
        packet.pop('policy_code_sha256'); packet.pop('fingerprint')
        packet['fingerprint'] = batch.digest(batch.canon(packet).encode())
        (p/'PACKET.json').write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, 'direct policy code changed or missing'):
            batch.apply(self.repo, p, p/'applied')

    def test_batch_codec_pin_is_enforced_even_for_rehashed_packet(self):
        p = self.packet(('EO:1',))
        original = json.loads((p/'PACKET.json').read_text())
        for stale in ('0'*64, None):
            with self.subTest(pin=stale):
                packet = dict(original)
                packet.pop('fingerprint')
                if stale is None:
                    packet.pop('codec_code_sha256')
                else:
                    packet['codec_code_sha256'] = stale
                packet['fingerprint'] = batch.digest(batch.canon(packet).encode())
                (p/'PACKET.json').write_text(json.dumps(packet))
                with self.assertRaisesRegex(ValueError, 'batch codec changed or missing'):
                    batch.apply(self.repo, p, p/'applied')


# Only the nine batch-specific tests above run in this subclass.
for _name in tuple(vars(T.BuildIntegrationTests)):
    if _name.startswith('test_'):setattr(BatchTests,_name,None)

if __name__=='__main__':unittest.main()
