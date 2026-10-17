"""Shared bounded HTTPS byte custody. Stdlib; no model, status or ledger writes.

Transport injection makes all tests and benchmarks network-free. Bodies and
metadata survive runner restarts under JOB_CACHE_DIR. Range resume requires an
ETag and a matching Content-Range; otherwise a clean request replaces the part.
"""
from __future__ import annotations
import concurrent.futures, hashlib, io, json, os, re, threading, time
import urllib.error, urllib.parse, urllib.request, urllib.robotparser
from pathlib import Path

class FetchError(RuntimeError):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**k):return None

def http_transport(url,headers,timeout):
    req=urllib.request.Request(url,headers=headers)
    try:r=urllib.request.build_opener(NoRedirect).open(req,timeout=timeout)
    except urllib.error.HTTPError as e:r=e
    return r.status,{k.lower():v for k,v in r.headers.items()},r

def sha(raw):return hashlib.sha256(raw).hexdigest()
def atomic(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    # Per-URL locks serialize writers, including replace on Windows.
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_bytes(raw);os.replace(temp,path)

class FetchPool:
    def __init__(self,cache,workers=12,per_host=6,transport=None,max_bytes=100_000_000,
                 timeout=35,user_agent='EO-Road-System/1.0',min_interval=0.1,offline=False):
        self.cache=Path(cache);self.cache.mkdir(parents=True,exist_ok=True)
        self.workers=max(1,min(int(workers),32));self.per_host=max(1,min(int(per_host),6))
        self.transport_fn=transport or http_transport;self.max_bytes=max_bytes;self.timeout=timeout
        self.user_agent=user_agent;self.min_interval=min_interval;self.offline=offline
        self.lock=threading.RLock();self.hosts={};self.urls={};self.robots={};self.robots_locks={};self.next_start={}
        self.requests=0;self.bytes_downloaded=0;self.cache_hits=0
    def url_lock(self,url):
        with self.lock:return self.urls.setdefault(url,threading.Lock())
    def _origin(self,url):
        p=urllib.parse.urlsplit(url)
        if p.scheme!='https' or not p.hostname or p.username or p.password:raise FetchError('HTTPS URL without credentials required')
        return p.scheme+'://'+p.netloc,p.hostname
    def _request(self,url,headers,timeout,delay=0):
        origin,host=self._origin(url)
        with self.lock:sem=self.hosts.setdefault(host,threading.BoundedSemaphore(self.per_host))
        with sem:
            with self.lock:
                at=max(time.monotonic(),self.next_start.get(host,0));self.next_start[host]=at+max(self.min_interval,delay)
            if at>time.monotonic():time.sleep(max(0,at-time.monotonic()))
            status,hs,body=self.transport_fn(url,headers,timeout)
            hs={k.lower():v for k,v in hs.items()}
            # Stream under the host semaphore; preserve partial bytes on interrupted downloads.
            try:raw=body.read(500001)
            finally:body.close()
            return status,hs,io.BytesIO(raw),sem
    def allowed(self,url):
        origin,host=self._origin(url)
        with self.lock:lock=self.robots_locks.setdefault(origin,threading.Lock())
        with lock:
            if origin not in self.robots:
                if self.offline:raise FetchError('offline robots unavailable')
                # Unknown/failed robots is retryable, never an exhaustion finding.
                status,hs,body,_=self._request(origin+'/robots.txt',{'User-Agent':self.user_agent},self.timeout)
                try:raw=body.read(500001)
                finally:body.close()
                with self.lock:self.requests+=1
                rp=urllib.robotparser.RobotFileParser()
                if status==200 and len(raw)<=500000:rp.parse(raw.decode('utf-8','replace').splitlines())
                elif status in (404,410):rp.allow_all=True
                elif status in (401,403):rp.disallow_all=True
                else:raise FetchError('robots unavailable: '+str(status))
                self.robots[origin]=rp
            rp=self.robots[origin]
        if not rp.can_fetch(self.user_agent,url):raise FetchError('blocked_by_robots_txt')
        rate=rp.request_rate(self.user_agent)
        return max(float(rp.crawl_delay(self.user_agent) or 0),rate.seconds/rate.requests if rate else 0)
    def _paths(self,url):
        key=sha(url.encode());base=self.cache/key[:2]/key
        return base.with_suffix('.json'),base.with_suffix('.body'),base.with_suffix('.part'),base.with_suffix('.resume')
    def request(self,url,headers=None,timeout=None):
        self._origin(url)
        with self.url_lock(url):
            meta,bodypath,part,resume=self._paths(url)
            if meta.is_file() and bodypath.is_file():
                try:
                    m=json.loads(meta.read_text(encoding='utf-8'));raw=bodypath.read_bytes()
                    if sha(raw)==m['sha256']:
                        with self.lock:self.cache_hits+=1
                        return m['status'],m['headers'],io.BytesIO(raw)
                except (ValueError,KeyError):pass
                meta.unlink(missing_ok=True);bodypath.unlink(missing_ok=True)
            if self.offline:raise FetchError('offline_and_not_cached')
            delay=self.allowed(url) if not urllib.parse.urlsplit(url).path=='/robots.txt' else 0
            hs={'User-Agent':self.user_agent,**(headers or {})};start=0;etag=''
            if part.is_file() and resume.is_file():
                try:etag=json.loads(resume.read_text())['etag'];start=part.stat().st_size
                except (ValueError,KeyError):start=0
                if start and etag:hs.update(Range=f'bytes={start}-',**{'If-Range':etag})
                else:start=0
            # _request protects starts. A second semaphore is held for the response stream.
            host=urllib.parse.urlsplit(url).hostname
            with self.lock:sem=self.hosts.setdefault(host,threading.BoundedSemaphore(self.per_host))
            # Read under one permit, with throttling and transport called directly to avoid nested acquisition.
            with sem:
                with self.lock:
                    at=max(time.monotonic(),self.next_start.get(host,0));self.next_start[host]=at+max(self.min_interval,delay)
                    self.requests+=1
                if at>time.monotonic():time.sleep(max(0,at-time.monotonic()))
                status,rh,response=self.transport_fn(url,hs,timeout or self.timeout);rh={k.lower():v for k,v in rh.items()}
                if status not in (200,206):
                    try:raw=response.read(min(self.max_bytes,500000)+1)
                    finally:response.close()
                    return status,rh,io.BytesIO(raw)
                if status==206:
                    cr=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',rh.get('content-range',''))
                    if not start or not cr or int(cr[1])!=start or (rh.get('etag') and rh['etag']!=etag):
                        response.close();part.unlink(missing_ok=True);resume.unlink(missing_ok=True);raise FetchError('invalid resume range')
                else:start=0
                part.parent.mkdir(parents=True,exist_ok=True)
                if rh.get('etag'):atomic(resume,json.dumps({'etag':rh['etag']}).encode())
                count=start
                try:
                    with part.open('ab' if start else 'wb') as f:
                        while True:
                            block=response.read(65536)
                            if not block:break
                            count+=len(block)
                            if count>self.max_bytes:raise FetchError('download exceeds bound')
                            f.write(block)
                            with self.lock:self.bytes_downloaded+=len(block)
                finally:response.close()
                expected=int(rh.get('content-length','0') or 0)
                if expected and count-start!=expected:raise FetchError('short body; retry can resume')
                if status==206 and count!=int(cr[3]):raise FetchError('incomplete range; retry can resume')
                raw=part.read_bytes()
                os.replace(part,bodypath);resume.unlink(missing_ok=True)
                # A resumed object is a complete 200 response to downstream document validators.
                rh.pop('content-range',None);rh['content-length']=str(len(raw))
                atomic(meta,(json.dumps({'url':url,'status':200,'headers':rh,'bytes':len(raw),'sha256':sha(raw)},sort_keys=True)+'\n').encode())
                return 200,rh,io.BytesIO(raw)
    def fetch(self,url):
        current=url
        for _ in range(7):
            status,headers,body=self.request(current)
            if status in (301,302,303,307,308):
                body.close();current=urllib.parse.urljoin(current,headers.get('location',''));continue
            try:raw=body.read(self.max_bytes+1)
            finally:body.close()
            if status!=200:raise FetchError('HTTP '+str(status))
            if len(raw)>self.max_bytes:raise FetchError('download exceeds bound')
            return {'url':url,'final_url':current,'sha256':sha(raw),'bytes':len(raw),'body':raw}
        raise FetchError('redirect limit')
    def map(self,func,items):
        # executor.map preserves input order; worker completion never changes serialized outputs.
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:return list(ex.map(func,items))
    def prefetch(self,urls):
        def one(url):
            try:
                result=self.fetch(url);return {k:v for k,v in result.items() if k!='body'}
            except Exception as e:return {'url':url,'error':type(e).__name__+': '+str(e)}
        return self.map(one,list(dict.fromkeys(urls)))

def prune(cache,cap_bytes):
    """Evict oldest complete URL groups, then temporary files, to an enforced job cap."""
    cache=Path(cache)
    files=sorted((p for p in cache.rglob('*') if p.is_file()),key=lambda p:(p.stat().st_mtime_ns,p.as_posix()))
    total=sum(p.stat().st_size for p in files);removed=0
    for p in files:
        if total<=cap_bytes:break
        size=p.stat().st_size;p.unlink();total-=size;removed+=size
    return {'bytes_retained':total,'bytes_evicted':removed,'cap_bytes':cap_bytes}
