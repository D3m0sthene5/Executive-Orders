"""Measured latency simulation only: no internet and no projected agent savings."""
import io,json,tempfile,time
from fetch_pool import FetchPool

def benchmark(count=48,latency=.02):
    urls=[f'https://host{i%2}.example/file{i}' for i in range(count)]
    def network(url,headers,timeout):
        if url.endswith('robots.txt'):return 404,{},io.BytesIO(b'')
        time.sleep(latency);return 200,{},io.BytesIO(url.encode())
    with tempfile.TemporaryDirectory() as d:
        serial=FetchPool(d+'/serial',workers=1,transport=network,min_interval=0)
        t=time.perf_counter();serial.map(serial.fetch,urls);before=time.perf_counter()-t
        parallel=FetchPool(d+'/parallel',workers=12,transport=network,min_interval=0)
        t=time.perf_counter();parallel.map(parallel.fetch,urls);after=time.perf_counter()-t
        warm=FetchPool(d+'/parallel',workers=12,offline=True)
        t=time.perf_counter();warm.map(warm.fetch,urls);cached=time.perf_counter()-t
    return {'benchmark':'48 deterministic mocked 20 ms downloads, two hosts; disk and SHA-256 included',
            'network_used':False,'serial_seconds':round(before,4),'parallel_seconds':round(after,4),'warm_cache_seconds':round(cached,4),
            'speedup':round(before/after,2),'wall_seconds_saved':round(before-after,4),
            'production_speedup_measured':False,'host_limit':6}
if __name__=='__main__':print(json.dumps(benchmark(),indent=2))
