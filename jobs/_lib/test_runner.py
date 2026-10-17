import importlib.util,os,tempfile,unittest
from pathlib import Path
class RunnerTests(unittest.TestCase):
    def test_dependency_order_and_selection(self):
        path=Path(__file__).resolve().parents[2]/'.github/scripts/pick_jobs.py'
        spec=importlib.util.spec_from_file_location('road_picker',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as d:
            old=Path.cwd();os.chdir(d)
            try:
                for name,deps in [('family-rules',[]),('claim-drafts',['family-rules']),('case-bundles',['claim-drafts']),('daily-digest',['case-bundles'])]:
                    p=Path('jobs')/name;p.mkdir(parents=True);(p/'job.py').touch();(p/'after.txt').write_text('\n'.join(deps))
                selected=m.with_consumers(['family-rules'])
                self.assertEqual(m.ordered(sorted(selected)),['family-rules','claim-drafts','case-bundles','daily-digest'])
            finally:os.chdir(old)
if __name__=='__main__':unittest.main()
