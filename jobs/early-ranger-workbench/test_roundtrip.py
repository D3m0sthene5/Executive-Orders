"""Bounded engineering regressions; synthetic bytes do not certify source content."""
import contextlib
import base64
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

wb = module('r3_test_workbench', HERE / 'job.py')
rt = wb.rt
census = module('r3_test_census', HERE.parent / 'census-candidates/job.py')

NODE_RUN = r"""
const fs=require('fs'),vm=require('vm');
const crypto=require('crypto').webcrypto;
global.crypto=crypto;
(async()=>{
 const input=JSON.parse(fs.readFileSync(0,'utf8'));
 if(input.action==='validate'){
  const rt=require(input.module);
  const records=await rt.validate(input.document,input.cases);
  process.stdout.write(JSON.stringify(records));return;
 }
 const html=input.html;
 const payload=html.match(/<script id="payload" type="application\/json">([\s\S]*?)<\/script>/)[1];
 const script=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
 const elements={},alerts=[],blobs=[];
 const unescape=s=>s.replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'");
 function element(id){return elements[id]??=(
 {value:'',textContent:id==='payload'?payload:'',files:[],addEventListener(){},replaceChildren(){},append(){},click(){},
 set innerHTML(value){this.html=value;
  for(const m of value.matchAll(/<textarea id="([^"]+)">([\s\S]*?)<\/textarea>/g))element(m[1]).value=unescape(m[2]);
  for(const m of value.matchAll(/<select id="([^"]+)">([\s\S]*?)<\/select>/g)){
   const opts=[...m[2].matchAll(/<option([^>]*)>([^<]*)<\/option>/g)];element(m[1]).value=(opts.find(o=>o[1].includes('selected'))||opts[0]||['','',''])[2];
  }
 },get innerHTML(){return this.html;}});}
 const sandbox={crypto,TextEncoder,Blob,console,setTimeout:()=>0,alert:x=>alerts.push(x),URL:{createObjectURL:b=>{blobs.push(b);return 'blob:synthetic'},revokeObjectURL(){}},document:{getElementById:element,createElement:()=>element('created')}};
 vm.createContext(sandbox);vm.runInContext(script,sandbox);
 for(let tries=0;tries<1000&&!element('detail').innerHTML&&!element('detail').textContent;tries++)await new Promise(resolve=>setTimeout(resolve,1));
 if(!element('detail').innerHTML)throw Error('Workbench initialization failed: '+element('detail').textContent);
 if(input.raw!==undefined){element('import').files=[{text:async()=>input.raw}];await element('import').onchange();}
 element('export-all').onclick();
 const exported=JSON.parse(await blobs.at(-1).text());
 process.stdout.write(JSON.stringify({exported,alerts,detail:element('detail').innerHTML}));
})().catch(e=>{console.error(e.stack);process.exit(1)});
"""

class RoundtripTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.id = 'mjm017456'
        self.url = 'https://www.loc.gov/item/' + self.id + '/'
        self.meta = {'catalog_item_id': self.id, 'url': self.url,
                     'official_item_title': 'Fixture — retained directive', 'item_date': '1814-08-13',
                     'status': 'official_item_JSON_retrieved'}
        self.text_path = 'jobs/early-ranger-transcriptions/output/derived_text/' + self.id + '.txt'
        self.xml_path = 'jobs/early-ranger-transcriptions/output/source.xml'
        self.page_path = 'jobs/early-ranger-full-pages/output/' + self.id + '/page_01.jpg'
        self.write(self.text_path, 'Fixture operative text <unaltered>.')
        self.write(self.xml_path, '<xml>Fixture operative text.</xml>')
        self.write(self.page_path, b'fixture page bytes; not a real manuscript')
        self.texts = [{'catalog_item_id': self.id, 'item_url': self.url,
                       'transcript_path': 'derived_text/' + self.id + '.txt',
                       'xml_path': 'source.xml', 'sha256': self.sha(self.xml_path)}]
        self.pages = {self.id: [{'catalog_item': self.id, 'item_url': self.url,
                         'source_state': 'original_page_JPEG_bytes_acquired',
                         'stored_path': self.id + '/page_01.jpg',
                         'page_in_LOC_resource_sequence': '1',
                         'source_URL': 'https://example.invalid/retained.jpg',
                         'sha256': self.sha(self.page_path)}]}
        self.candidates = {self.url: {'candidate_id': 'fixture', 'item_url': self.url}}
        self.case = self.make_case()
        self.notes = {'reviewer': 'Independent fixture AI',
                      'operative_clause_inventory': 'RETAIN THIS EXACT HISTORICAL NOTE',
                      'proposal': {'disposition': 'recommend_inclusion', 'reason': 'Synthetic source review',
                                   'attribution': 'AI_research'},
                      'census_membership': 'ADMITTED', 'legal_inclusion': 'INCLUDE',
                      'human_certified': True}
        self.doc = rt.export_worksheet([self.case], {self.id: self.notes})

    def write(self, path, content):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content if isinstance(content, bytes) else content.encode())

    def sha(self, path):
        return hashlib.sha256((self.root / path).read_bytes()).hexdigest()

    def make_case(self):
        return wb.make_case(self.meta, self.texts, self.pages, self.candidates, self.root)

    def checked(self, doc=None, case=None):
        return rt.validate_worksheet(doc or self.doc, [case or self.make_case()])[0]

    def assert_status(self, expected, doc=None, case=None):
        result = self.checked(doc, case)
        self.assertEqual(result['validation'], expected)
        self.assertTrue(result['research_only'])
        if expected != 'unchanged_source':
            self.assertIsNone(rt.validated_proposal(result))
        return result

    def node(self, **values):
        if not shutil.which('node'):
            self.skipTest('Node unavailable: cross-language/browser-script checks not run')
        p = subprocess.run(['node', '-e', NODE_RUN], input=json.dumps(values), text=True,
                           encoding='utf-8', capture_output=True, timeout=20, check=True)
        return json.loads(p.stdout)

    def browser(self, doc=None, case=None, raw=None, embedded=False):
        document = self.doc if doc is None else doc
        html = wb.make_html([case or self.make_case()], {}, [document] if embedded else [])
        args = {'action': 'html', 'html': html}
        if not embedded:
            args['raw'] = raw if raw is not None else json.dumps(document)
        return self.node(**args)

    def test_current_notes_and_exact_binding_roundtrip(self):
        result = self.assert_status('unchanged_source')
        self.assertEqual(result['notes'], self.notes)
        self.assertEqual(rt.validated_proposal(result), self.notes['proposal'])
        self.assertEqual(self.doc['per_case'][self.id]['source_binding'], self.case['source_binding'])

    def test_export_copies_inputs(self):
        saved = copy.deepcopy(self.doc)
        self.notes['proposal']['reason'] = 'changed later'
        self.case['source_binding']['fingerprint'] = 'changed later'
        self.assertEqual(self.doc, saved)

    def test_changed_transcript_bytes(self):
        self.write(self.text_path, 'Altered operative text')
        self.assert_status('changed_source')

    def test_generated_html_displays_exact_bound_page_bytes(self):
        case = self.make_case()
        result = self.browser(case=case)
        images = re.findall(r'<img[^>]* src="([^"]*)"', result['detail'])
        self.assertTrue(images)
        for uri in images:
            self.assertTrue(uri.startswith('data:image/jpeg;base64,'))
            self.assertEqual(hashlib.sha256(base64.b64decode(uri.split(',', 1)[1])).hexdigest(),
                             self.sha(self.page_path))
        self.assertNotIn('/main/', case['master_JPEG_pages_stored'][0]['github_original_page'])
        self.assertNotIn('display_data_uri', json.dumps(case['source_binding']))

    def test_preview_rejects_page_changed_after_binding(self):
        captured = self.sha(self.page_path)
        self.write(self.page_path, b'page changed during build')
        with self.assertRaisesRegex(ValueError, 'Source changed'):
            wb.preview(self.root, self.page_path, captured)

    def test_retained_facsimile_display_and_grade_bind_exact_bytes(self):
        self.census_fixture()
        path = 'retained/page.png'
        self.write(path, b'synthetic png bytes')
        custody = [{'catalog_item_id': self.id, 'item_url': self.url,
                    'facsimile_files': [{'state': 'downloaded_exact_source_bytes',
                       'stored_relpath': 'page.png', 'sha256': self.sha(path),
                       'source_url': 'https://example.invalid/derivative.png',
                       'representation_grade': 'IIIF_derivative_unreviewed'}]}]
        self.write('retained/CUSTODY.json', json.dumps(custody))
        case = wb.build_cases(self.root, facsimile_custodies=['retained/CUSTODY.json'])[0]
        image = case['retained_facsimiles'][0]
        self.assertEqual(hashlib.sha256(base64.b64decode(image['display_data_uri'].split(',', 1)[1])).hexdigest(), self.sha(path))
        self.assertEqual(image['representation_grade'], 'IIIF_derivative_unreviewed')
        self.assertNotIn('display_data_uri', json.dumps(case['source_binding']))
        d = rt.export_worksheet([case], {self.id: self.notes})
        self.write(path, b'changed png bytes')
        custody[0]['facsimile_files'][0]['sha256'] = self.sha(path)
        self.write('retained/CUSTODY.json', json.dumps(custody))
        changed = wb.build_cases(self.root, facsimile_custodies=['retained/CUSTODY.json'])[0]
        self.assert_status('changed_source', d, changed)

    def test_retained_workbench_identity_and_missing_snapshot(self):
        retained = copy.deepcopy(self.case)
        retained['id'] = 'other'
        with self.assertRaises(ValueError):
            wb.make_case(self.meta, self.texts, self.pages, {}, self.root,
                         retained, 'missing.html')
        retained['id'] = self.id
        case = wb.make_case(self.meta, self.texts, self.pages, {}, self.root,
                            retained, 'missing.html')
        d = rt.export_worksheet([case], {self.id: self.notes})
        self.assert_status('missing_source', d, case)

    def test_transcript_changed_after_hash_cannot_display_under_old_binding(self):
        artifact = wb.rt.artifact
        def race(root, path, role, *args, **kwargs):
            source = artifact(root, path, role, *args, **kwargs)
            if role == 'transcript':
                self.write(self.text_path, 'transcript changed during build')
            return source
        with mock.patch.object(wb.rt, 'artifact', race):
            try:
                case = self.make_case()
            except ValueError:
                return
        source = next(s for s in case['source_binding']['sources'] if s['role'] == 'transcript')
        self.assertEqual(hashlib.sha256(case['transcription'].encode()).hexdigest(), source['sha256'])

    def test_changed_page_bytes_without_changed_declaration(self):
        self.write(self.page_path, b'changed page')
        self.assert_status('conflicting_representation')

    def test_changed_page_bytes_and_declaration(self):
        self.write(self.page_path, b'changed page')
        self.pages[self.id][0]['sha256'] = self.sha(self.page_path)
        self.assert_status('changed_source')

    def test_changed_xml_bytes_and_declaration(self):
        self.write(self.xml_path, '<xml>changed</xml>')
        self.texts[0]['sha256'] = self.sha(self.xml_path)
        self.assert_status('changed_source')

    def test_changed_metadata(self):
        self.meta['official_item_title'] = 'Corrected catalog identity'
        self.assert_status('changed_source')

    def test_changed_prior_candidate_record_is_stale(self):
        self.candidates[self.url]['candidate_id'] = 'corrected-prior-identity'
        self.assert_status('changed_source')

    def test_changed_transcription_inventory_provenance_is_stale(self):
        self.texts[0]['provenance_note'] = 'new extraction context'
        self.assert_status('changed_source')

    def test_changed_page_inventory_provenance_is_stale(self):
        self.pages[self.id][0]['provenance_note'] = 'new acquisition context'
        self.assert_status('changed_source')

    def test_each_missing_bound_source(self):
        for path in (self.text_path, self.xml_path, self.page_path):
            with self.subTest(path=path):
                p = self.root / path
                content = p.read_bytes()
                p.unlink()
                self.assert_status('missing_source')
                p.write_bytes(content)

    def test_wrong_entry_and_binding_candidate_ids(self):
        for target in ('entry', 'binding'):
            with self.subTest(target=target):
                d = copy.deepcopy(self.doc)
                e = d['per_case'][self.id]
                (e if target == 'entry' else e['source_binding'])['candidate_id'] = 'LOC:other'
                self.assert_status('conflicting_representation', d)

    def test_unknown_current_item_is_not_relabelled(self):
        d = copy.deepcopy(self.doc)
        d['per_case']['unknown'] = d['per_case'].pop(self.id)
        self.assert_status('conflicting_representation', d)

    def test_tampered_binding_fingerprint(self):
        d = copy.deepcopy(self.doc)
        d['per_case'][self.id]['source_binding']['candidate_version'] = 'altered'
        self.assert_status('conflicting_representation', d)

    def test_absent_binding_is_unverified(self):
        d = copy.deepcopy(self.doc)
        del d['per_case'][self.id]['source_binding']
        self.assert_status('unknown_version', d)

    def test_duplicate_transcript_records_rejected(self):
        self.texts.append(copy.deepcopy(self.texts[0]))
        with self.assertRaises(ValueError):
            self.make_case()

    def test_mismatched_source_identity_rejected(self):
        for target in (self.texts[0], self.pages[self.id][0]):
            previous = target['item_url']
            target['item_url'] = 'https://www.loc.gov/item/other/'
            with self.assertRaises(ValueError):
                self.make_case()
            target['item_url'] = previous

    def test_duplicate_current_case_ids_rejected(self):
        with self.assertRaises(ValueError):
            rt.validate_worksheet(self.doc, [self.case, self.case])
        with self.assertRaises(ValueError):
            rt.export_worksheet([self.case, self.case], {})

    def test_conflicting_page_representations(self):
        duplicate = copy.deepcopy(self.pages[self.id][0])
        duplicate['source_URL'] = 'https://example.invalid/other-representation.jpg'
        self.pages[self.id].append(duplicate)
        self.assert_status('conflicting_representation')

    def test_legacy_notes_recovered_without_proposal(self):
        d = {'schema': 'eo-early-source-worksheet/v1', 'review_state': rt.STATE,
             'per_case': {self.id: self.notes}}
        result = self.assert_status('legacy_unverified', d)
        self.assertEqual(result['notes'], self.notes)

    def test_duplicate_json_keys_rejected_by_python(self):
        path = self.root / 'duplicate.json'
        path.write_text('{"schema":"one","schema":"two"}')
        with self.assertRaises(ValueError):
            rt.read_worksheet(path)

    def test_source_path_escape_rejected(self):
        with self.assertRaises(ValueError):
            rt.artifact(self.root, '../outside.txt', 'transcript')

    def test_javascript_python_status_parity(self):
        scenarios = [(self.doc, self.case)]
        self.write(self.text_path, 'changed transcript')
        scenarios.append((self.doc, self.make_case()))
        (self.root / self.page_path).unlink()
        scenarios.append((self.doc, self.make_case()))
        legacy = {'schema': 'eo-early-source-worksheet/v1', 'review_state': rt.STATE,
                  'per_case': {self.id: self.notes}}
        scenarios.append((legacy, self.case))
        unknown = copy.deepcopy(self.doc)
        del unknown['per_case'][self.id]['source_binding']
        scenarios.append((unknown, self.case))
        conflict = copy.deepcopy(self.doc)
        conflict['per_case'][self.id]['candidate_id'] = 'LOC:another'
        scenarios.append((conflict, self.case))
        for document, case in scenarios:
            with self.subTest(expected=rt.validate_worksheet(document, [case])[0]['validation']):
                js = self.node(action='validate', module=str(HERE / 'roundtrip.js'),
                               document=document, cases=[case])
                self.assertEqual(js, rt.validate_worksheet(document, [case]))

    def test_generated_html_current_note_import_export(self):
        for embedded in (False, True):
            with self.subTest(embedded=embedded):
                exported = self.browser(embedded=embedded)['exported']
                self.assertEqual(exported['per_case'][self.id]['notes']['operative_clause_inventory'],
                                 self.notes['operative_clause_inventory'])
                self.assertEqual(self.checked(exported)['validation'], 'unchanged_source')

    def test_generated_html_stale_notes_never_rebound(self):
        self.write(self.text_path, 'changed current transcript')
        for embedded in (False, True):
            with self.subTest(embedded=embedded):
                exported = self.browser(embedded=embedded)['exported']
                self.assertTrue(exported['unverified_notes'])
                current = exported['per_case'].get(self.id, {}).get('notes', {})
                self.assertNotEqual(current.get('operative_clause_inventory'), self.notes['operative_clause_inventory'])
                records = rt.validate_worksheet(exported, [self.make_case()])
                proposals = [rt.validated_proposal(r) for r in records]
                self.assertFalse(any(p and p['disposition'] == 'recommend_inclusion' for p in proposals))
                self.assertIn(self.notes['operative_clause_inventory'], json.dumps(exported['unverified_notes']))

    def test_generated_html_legacy_notes_survive_two_roundtrips_unverified(self):
        d = {'schema': 'eo-early-source-worksheet/v1', 'review_state': rt.STATE,
             'per_case': {self.id: self.notes}}
        for _ in range(2):
            d = self.browser(doc=d)['exported']
            self.assertIn(self.notes['operative_clause_inventory'], json.dumps(d['unverified_notes']))
            self.assertNotEqual(d['per_case'].get(self.id, {}).get('notes', {}).get('operative_clause_inventory'),
                                self.notes['operative_clause_inventory'])
            self.assertFalse(any(rt.validated_proposal(r) for r in rt.validate_worksheet(d, [self.case])))

    def test_generated_html_duplicate_json_entries_rejected(self):
        entry = json.dumps(self.doc['per_case'][self.id])
        raw = '{"schema":' + json.dumps(rt.SCHEMA) + ',"review_state":' + json.dumps(rt.STATE)
        raw += ',"per_case":{' + json.dumps(self.id) + ':' + entry + ',' + json.dumps(self.id) + ':' + entry + '}}'
        result = self.browser(raw=raw)
        self.assertTrue(any(x.startswith('Import rejected:') for x in result['alerts']), result['alerts'])

    def test_generated_html_escaped_duplicate_keys_rejected(self):
        raw = json.dumps(self.doc)
        raw = raw.replace('"reviewer":', '"reviewer":"earlier", "\\u0072eviewer":', 1)
        result = self.browser(raw=raw)
        self.assertTrue(any(x.startswith('Import rejected:') for x in result['alerts']), result['alerts'])

    def test_historical_record_cannot_self_declare_current(self):
        d = copy.deepcopy(self.doc)
        d['per_case'] = {}
        d['unverified_notes'] = [{'item_id': self.id, 'validation': 'unchanged_source',
                                  'entry': copy.deepcopy(self.doc['per_case'][self.id]),
                                  'notes': self.notes, 'research_only': False}]
        for _ in range(2):
            d = self.browser(doc=d)['exported']
            self.assertIn(self.notes['operative_clause_inventory'], json.dumps(d['unverified_notes']))
            self.assertFalse(any(rt.validated_proposal(r) for r in rt.validate_worksheet(d, [self.case])))

    def test_source_change_then_restore_does_not_upgrade_quarantined_notes(self):
        original = (self.root / self.text_path).read_bytes()
        self.write(self.text_path, 'temporarily altered transcript')
        d = self.browser()['exported']
        self.write(self.text_path, original)
        d = self.browser(doc=d)['exported']
        self.assertIn(self.notes['operative_clause_inventory'], json.dumps(d['unverified_notes']))
        self.assertFalse(any(rt.validated_proposal(r) for r in rt.validate_worksheet(d, [self.make_case()])))

    def test_script_delimiters_in_source_and_notes_roundtrip(self):
        content = '</script><script>throw Error("must not execute")</script> & café'
        self.write(self.text_path, content)
        case = self.make_case()
        self.notes['operative_clause_inventory'] = content
        d = rt.export_worksheet([case], {self.id: self.notes})
        result = self.browser(doc=d, case=case, embedded=True)
        self.assertEqual(result['exported']['per_case'][self.id]['notes']['operative_clause_inventory'], content)

    def test_legacy_record_shaped_like_v2_stays_unverified(self):
        d = copy.deepcopy(self.doc)
        d['schema'] = 'eo-early-source-worksheet/v1'
        self.assert_status('legacy_unverified', d)
        d = self.browser(doc=d)['exported']
        self.assertFalse(any(rt.validated_proposal(r) for r in rt.validate_worksheet(d, [self.case])))

    def test_proposals_require_attribution_reviewer_reason_and_disposition(self):
        for field, value in [('reviewer', ''), ('attribution', 'human'), ('reason', ''),
                             ('disposition', 'admitted')]:
            with self.subTest(field=field):
                record = self.checked()
                target = record['notes'] if field == 'reviewer' else record['notes']['proposal']
                target[field] = value
                self.assertIsNone(rt.validated_proposal(record))

    def census_fixture(self):
        for path in census.INPUTS.values():
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        self.write(census.INPUTS['curated'], json.dumps(list(self.candidates.values())))
        self.write(census.INPUTS['item_metadata'], json.dumps(self.meta) + '\n')
        self.write(census.INPUTS['transcriptions'], json.dumps(self.texts[0]) + '\n')
        row = self.pages[self.id][0]
        self.write(census.INPUTS['page_images'], ','.join(row) + '\n' + ','.join(row.values()) + '\n')
        self.write(census.INPUTS['lord'], 'candidate_id\nLORD:fixture\n')
        self.write(census.INPUTS['early_sources'], 'candidate_id,primary_source_url,date\n')
        self.write(census.INPUTS['census'], 'id\nEO:fixture\n')

    def test_census_import_proposals_never_admit_or_certify(self):
        self.census_fixture()
        for stale in (False, True):
            with self.subTest(stale=stale):
                if stale:
                    self.write(self.text_path, 'changed transcript for census')
                self.write('worksheet.json', json.dumps(self.doc))
                output = self.root / ('out-stale' if stale else 'out-current')
                with contextlib.redirect_stdout(io.StringIO()):
                    census.build(self.root, output, research_worksheets=[self.root / 'worksheet.json'])
                item = json.loads((output / 'ITEM_CANDIDATES.jsonl').read_text())
                summary = json.loads((output / 'SUMMARY.json').read_text())
                self.assertEqual(item['census_membership'], 'NOT_ADMITTED')
                self.assertEqual(item['legal_inclusion'], 'HOLD')
                self.assertIs(item['human_certified'], False)
                self.assertEqual(summary['newly_admitted_EOs'], 0)
                self.assertEqual(summary['independent_human_certifications'], 0)
                self.assertEqual(len(item.get('research_proposals', [])), 0 if stale else 1)
                for proposal in item.get('research_proposals', []):
                    self.assertIs(proposal['scientific_approval'], False)
                self.assertEqual(item['research_notes'][0]['validation'], 'changed_source' if stale else 'unchanged_source')

if __name__ == '__main__':
    unittest.main()
