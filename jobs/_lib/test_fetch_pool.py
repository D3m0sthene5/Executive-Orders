import io,json,tempfile,threading,time,unittest
from pathlib import Path
from fetch_pool import FetchPool,FetchError,sha,prune
class PoolTests(unittest.TestCase):
    def test_cache_hash_and_offline(self):
        calls=[]
        def net(u,h,t):calls.append(u);return 200,{},io.BytesIO(b'User-agent: *\nAllow: /' if u.endswith('robots.txt') else b'body')
        with tempfile.TemporaryDirectory() as d:
            p=FetchPool(d,transport=net,min_interval=0);self.assertEqual(p.fetch('https://test/a')['sha256'],sha(b'body'))
            self.assertEqual(p.fetch('https://test/a')['body'],b'body');self.assertEqual(len(calls),2)
            q=FetchPool(d,offline=True);self.assertEqual(q.fetch('https://test/a')['body'],b'body')
            with self.assertRaises(FetchError):q.fetch('https://test/missing')
    def test_robots_blocks_and_failure_closed(self):
        for status,raw in [(200,b'User-agent: *\nDisallow: /private'),(503,b'')]:
            with tempfile.TemporaryDirectory() as d:
                p=FetchPool(d,transport=lambda *a:(status,{},io.BytesIO(raw)),min_interval=0)
                with self.assertRaises(FetchError):p.fetch('https://test/private')
    def test_host_limit_and_order(self):
        lock=threading.Lock();active=peak=0
        def net(u,h,t):
            nonlocal active,peak
            if u.endswith('robots.txt'):return 404,{},io.BytesIO(b'')
            with lock:active+=1;peak=max(peak,active)
            time.sleep(.01)
            with lock:active-=1
            return 200,{},io.BytesIO(u.encode())
        with tempfile.TemporaryDirectory() as d:
            p=FetchPool(d,workers=20,per_host=99,transport=net,min_interval=0)
            urls=['https://test/'+str(i) for i in range(20)]
            self.assertEqual([r['url'] for r in p.map(p.fetch,urls)],urls);self.assertLessEqual(peak,6);self.assertGreater(peak,1)
    def test_duplicate_requests_coalesced(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def net(u,h,t):calls.append(u);return 404 if u.endswith('robots.txt') else 200,{},io.BytesIO(b'x')
            p=FetchPool(d,transport=net,min_interval=0);p.map(p.fetch,['https://test/a']*8);self.assertEqual(calls.count('https://test/a'),1)
    def test_validated_resume(self):
        with tempfile.TemporaryDirectory() as d:
            seen=[]
            def net(u,h,t):
                if u.endswith('robots.txt'):return 404,{},io.BytesIO(b'')
                seen.append(h);return 206,{'content-range':'bytes 3-5/6','etag':'v1','content-length':'3'},io.BytesIO(b'def')
            p=FetchPool(d,transport=net,min_interval=0);_,_,part,resume=p._paths('https://test/a');part.parent.mkdir();part.write_bytes(b'abc');resume.write_text('{"etag":"v1"}')
            self.assertEqual(p.fetch('https://test/a')['body'],b'abcdef');self.assertEqual(seen[0]['Range'],'bytes=3-')
    def test_invalid_resume_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            p=FetchPool(d,transport=lambda u,h,t:(404 if u.endswith('robots.txt') else 206,{'content-range':'bytes 0-2/3'},io.BytesIO(b'abc')),min_interval=0)
            with self.assertRaises(FetchError):p.fetch('https://test/a')
    def test_source_ladder_adapter_preserves_document_validation(self):
        import importlib.util
        path=Path(__file__).resolve().parents[1]/'source-ladder/fetch_ladder.py'
        spec=importlib.util.spec_from_file_location('pool_test_ladder',path)
        import sys
        m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as d:
            def net(u,h,t):return (404,{},io.BytesIO(b'')) if u.endswith('robots.txt') else (200,{'content-type':'application/pdf'},io.BytesIO(b'%PDF-1.4\n'+b'x'*1500+b'\n%%EOF'))
            pool=FetchPool(Path(d)/'pool',transport=net,min_interval=0)
            fetcher=m.Fetcher(Path(d)/'ladder',transport=pool.request,sleep=lambda _:None)
            self.assertTrue(fetcher.fetch('https://test/a.pdf',expect='pdf')['accepted'])
    def test_rejected_html_stays_rejected(self):
        import importlib.util,sys
        path=Path(__file__).resolve().parents[1]/'source-ladder/fetch_ladder.py'
        spec=importlib.util.spec_from_file_location('pool_bad_ladder',path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as d:
            pool=FetchPool(Path(d)/'pool',transport=lambda u,h,t:(404 if u.endswith('robots.txt') else 200,{'content-type':'text/html'},io.BytesIO(b'<html>captcha</html>')),min_interval=0)
            fetcher=m.Fetcher(Path(d)/'ladder',transport=pool.request,sleep=lambda _:None)
            self.assertFalse(fetcher.fetch('https://test/a.pdf',expect='pdf')['accepted'])
    def test_pool_enforces_cache_cap(self):
        with tempfile.TemporaryDirectory() as d:
            def net(u,h,t):return (404,{},io.BytesIO(b'')) if u.endswith('robots.txt') else (200,{},io.BytesIO(b'x'*1000))
            p=FetchPool(d,transport=net,min_interval=0,max_cache_bytes=500)
            self.assertEqual(p.fetch('https://test/a')['body'],b'x'*1000)
            self.assertLessEqual(sum(x.stat().st_size for x in Path(d).rglob('*') if x.is_file()),500)
    def test_url_policy_and_cap(self):
        with tempfile.TemporaryDirectory() as d:
            p=FetchPool(d,offline=True)
            for url in ['http://test/a','https://user:pass@test/a','file:///a']:
                with self.assertRaises(FetchError):p.fetch(url)
            (Path(d)/'big').write_bytes(b'x'*100);self.assertEqual(prune(d,20)['bytes_retained'],0)
if __name__=='__main__':unittest.main()
