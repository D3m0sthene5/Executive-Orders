import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import lambertini
from progress import claim_stages


class ProgressTests(unittest.TestCase):
    def test_hash_pinned_stages_do_not_credit_stale_or_replaced_claims(self):
        selected={'EO:1':'new','EO:2':'prior','EO:3':'ok','EO:4':'ready'}
        effective={'EO:1':'new','EO:2':'different_owner','EO:3':'ok','EO:4':'ready'}
        checks={iid:[{'claim_sha256':sha,'all_checks_passed':True,'gate_passed':True}]
                for iid,sha in [('EO:1','old'),('EO:2','prior'),('EO:3','ok'),('EO:4','ready')]}
        tracker={iid:{'ready_for_human_review':'yes' if iid!='EO:3' else 'no','blockers':'OPEN_SOURCE_AUDIT'} for iid in selected}
        result=claim_stages(selected,effective,checks,tracker)
        self.assertEqual((result['canonical_claims_in_campaign'],result['currently_effective_claims'],
            result['local_checker_passes'],result['integrated_ready_orders']),(4,3,2,1))

    def test_continuation_stops_before_selecting_more_work(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); evidence=root/'review.json'; evidence.write_text('{}')
            contract={'schema':'llull.gate-contract/v1','gate_id':'probe',
                      'planted_defects':{'required':3,'minimum_caught':2},'minimums':{'upheld':5}}
            observation={'schema':'llull.gate-observation/v1','gate_id':'probe',
                'planted_defects':{'present':1,'reviewed':1,'caught':1},'metrics':{'upheld':6},
                'evidence':[{'path':'review.json','sha256':hashlib.sha256(evidence.read_bytes()).hexdigest()}]}
            c=root/'contract.json';o=root/'observation.json'
            c.write_text(json.dumps(contract));o.write_text(json.dumps(observation))
            args=['--repo',td,'continue','--pool','LAMBS','--seed','bounded','--n','1',
                  '--out',str(root/'stop'),'--gate-contract',str(c),'--gate-observation',str(o)]
            with patch.object(lambertini,'cmd_probe') as probe:
                self.assertEqual(lambertini.main(args),5);probe.assert_not_called()
                receipt=json.loads((root/'stop/CONTINUATION_GATE.json').read_text())
                self.assertEqual(receipt['status'],'untested')
            observation['planted_defects']={'present':3,'reviewed':3,'caught':2}
            o.write_text(json.dumps(observation));args[args.index(str(root/'stop'))]=str(root/'pass')
            with patch.object(lambertini,'cmd_probe') as probe:
                self.assertEqual(lambertini.main(args),0);probe.assert_called_once()


if __name__=='__main__':unittest.main()
