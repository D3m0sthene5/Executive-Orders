#!/usr/bin/env python3
"""Compare baseline and instrumented FetchPool with a bounded loopback server."""
import http.client, importlib.util, json, subprocess, sys, tempfile, threading, time, types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import urllib.parse

ROOT=Path(__file__).resolve().parents[4]
LIB=ROOT/'jobs'/'_lib'/'fetch_pool.py'
BASE='f9c6d806ad059dcad7875ab3708715f20ea386df'
def load_base():
    source=subprocess.check_output(['git','show',f'{BASE}:jobs/_lib/fetch_pool.py'],cwd=ROOT,text=True)
    module=types.ModuleType('fetch_pool_base');module.__file__=str(LIB)
    exec(compile(source,str(LIB),'exec'),module.__dict__)
    return module
def load_current():
    spec=importlib.util.spec_from_file_location('fetch_pool_current',LIB)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

PAYLOADS={'/a':b'A'*4096,'/b':b'B'*8192}
server_log={'requests':0,'body_bytes':0}
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        server_log['requests']+=1
        if self.path=='/robots.txt':self.send_response(404);self.end_headers();return
        body=PAYLOADS.get(self.path,b'');server_log['body_bytes']+=len(body)
        self.send_response(200);self.send_header('Content-Length',str(len(body)))
        self.send_header('Last-Modified','Wed, 01 Jan 2020 00:00:00 GMT');self.end_headers();self.wfile.write(body)
    def log_message(self,*args):pass
httpd=ThreadingHTTPServer(('127.0.0.1',0),Handler)
thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start();port=httpd.server_address[1]
body_reads={'count':0,'bytes':0};original_read_bytes=Path.read_bytes
def count_body_reads(path):
    data=original_read_bytes(path)
    if path.suffix=='.body':body_reads['count']+=1;body_reads['bytes']+=len(data)
    return data
Path.read_bytes=count_body_reads

def transport_for(fp):
    def local_transport(url,headers,timeout):
        c=http.client.HTTPConnection('127.0.0.1',port,timeout=timeout)
        c.request('GET',urllib.parse.urlsplit(url).path,headers=headers);r=c.getresponse()
        status=r.status;hs={k.lower():v for k,v in r.getheaders()};body=r.read();c.close()
        return status,hs,fp.io.BytesIO(body)
    return local_transport

def probe(fp,label,cache):
    reads_before=dict(body_reads);server_before=dict(server_log);urls=[f'https://127.0.0.1:{port}{p}' for p in ('/a','/b')]
    pool=fp.FetchPool(cache,transport=transport_for(fp),min_interval=0)
    t0=time.perf_counter();results=[]
    for _ in range(2):
        for url in urls:results.append(pool.fetch(url))
    elapsed=time.perf_counter()-t0
    return {'label':label,'outputs':len(results),'unique_body_hashes':len({x['sha256'] for x in results}),
            'elapsed_seconds':round(elapsed,6),'network_requests':server_log['requests']-server_before['requests'],
            'network_body_bytes':server_log['body_bytes']-server_before['body_bytes'],
            'persistent_body_reads_for_validation':{'count':body_reads['count']-reads_before['count'],
                                                     'bytes':body_reads['bytes']-reads_before['bytes']},
            'pool_counters':pool.cache_stats() if hasattr(pool,'cache_stats') else None}

try:
    base=load_base();current=load_current()
    with tempfile.TemporaryDirectory() as td:
        a=probe(base,'baseline source at '+BASE,Path(td)/'base')
        b=probe(current,'working tree instrumentation',Path(td)/'current')
        body_meta=[]
        for url in (f'https://127.0.0.1:{port}/a',f'https://127.0.0.1:{port}/b'):
            meta,body,_,_=current.FetchPool(Path(td)/'current')._paths(url)
            m=json.loads(meta.read_text());raw=original_read_bytes(body)
            body_meta.append({'exact_url':m['url']==url,'sha256':current.sha(raw),'bytes':len(raw),
                              'last_modified':m['headers'].get('last-modified')})
        print(json.dumps({'benchmark':'two local deterministic bodies; 2 cold misses + 2 repeated reads',
                          'network':'loopback only through injected HTTP transport; no public requests',
                          'baseline':a,'instrumented':b,'custody_check':body_meta,
                          'conclusion':'No optimization or production saving measured; counters expose persistent verification work.'},
                         sort_keys=True,indent=2))
finally:
    httpd.shutdown();httpd.server_close();thread.join(timeout=2);Path.read_bytes=original_read_bytes
