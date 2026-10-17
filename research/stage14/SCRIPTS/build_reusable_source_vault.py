#!/usr/bin/env python3
"""Index/cache previously acquired original-text representations from Stage 11 agent ZIPs.

Content addresses text representations; preserves every source member path, cached
retrieval metadata, original URL, hash attestations, duplicate content, and
provenance. No attempt to treat a filename/HTML result as an authenticated EO.
Usage: python build_reusable_source_vault.py FULL_STAGE11_SOURCE_ZIP STAGE14_DB OUTDIR
"""
from io import BytesIO
from zipfile import ZipFile
import collections,csv,hashlib,json,pathlib,re,sqlite3,sys,html
from html.parser import HTMLParser

class Scrub(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.skip=0;self.parts=[]
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','noscript'):self.skip+=1
  if tag in ('p','br','h1','h2','h3','li','div'):self.parts.append('\n')
 def handle_endtag(self,tag):
  if tag in ('script','style','noscript') and self.skip:self.skip-=1
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
def shrink(b,ext):
 t=b.decode('utf8',errors='replace')
 if ext in ('.html','.htm'):
  z=Scrub();z.feed(t);t=' '.join(z.parts)
 return re.sub(r'\s+',' ',t).strip()
def sha(b):return hashlib.sha256(b).hexdigest()
def clip(s,n):return str(s or '')[:n]

base=pathlib.Path(sys.argv[3]);base.mkdir(parents=True,exist_ok=True)
db=sqlite3.connect(sys.argv[2]);db.execute('''CREATE TABLE IF NOT EXISTS cache_blobs(sha256 TEXT PRIMARY KEY, size INT,extracted_text TEXT,content_kind TEXT, flags TEXT)''')
db.execute('''CREATE TABLE IF NOT EXISTS cache_representations(repr_id INTEGER PRIMARY KEY,sha256 TEXT,archive_member TEXT,inner_archive TEXT,source_url TEXT,original_host_sha256 TEXT,declared_extracted_sha256 TEXT,checksum_verdict TEXT,subject_id_hint TEXT,source_grade TEXT, content_kind TEXT)''')
db.execute('''CREATE INDEX IF NOT EXISTS idx_cache_ref_subject ON cache_representations(subject_id_hint)''')
db.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS cache_fts USING fts5(sha256 UNINDEXED,text,tokenize='unicode61')''')
root=ZipFile(sys.argv[1]); toscan=[('OPUS',ZipFile(BytesIO(root.read('INPUTS/OPUS_STAGE9_STATUS_DELTA.zip')))),('ASTRA',ZipFile(BytesIO(root.read('INPUTS/ASTRA_STAGE10_EVIDENCE_FIRST_DELTA.zip'))))]
N=0; mismatch=[];cache_rows=[];copied=[];counts=collections.Counter();hash_members=collections.defaultdict(list);subject_sources=collections.defaultdict(list)
for tag,z in toscan:
 names=set(z.namelist())
 for member in z.infolist():
  n=member.filename; ext=pathlib.Path(n).suffix.lower()
  # Generated source-representation caches only; agent decisions/scripts are not archival originals.
  if ext not in ('.txt','.html','.htm','.xml') or '/cache/' not in n:continue
  if member.file_size==0 or member.file_size>1600000:continue
  b=z.read(n);digest=sha(b)
  # Adjacent captured metadata provide source URL and original-host vs extracted bytes checks.
  metaname=n.rsplit('.',1)[0]+'.meta.json'
  meta={}
  if metaname in names:
   try:meta=json.loads(z.read(metaname))
   except Exception:pass
  expected=meta.get('text_file_sha256')
  validity='MATCHES_DECLARED_TEXT_SHA256' if expected and expected==digest else 'CONFLICTING_DECLARED_TEXT_SHA256' if expected else 'NO_DECLARED_TEXT_SHA256'
  if validity=='CONFLICTING_DECLARED_TEXT_SHA256':mismatch.append({'path':n,'expected':expected,'actual':digest})
  text=shrink(b,ext)
  low=text.lower();noise=any(v in low[:1500] for v in ('request access','verify you are human','enable javascript and cookies','captcha','access denied'))
  if '/app_search/' in n or re.search(r'/(search|query|frsrch|frapi|frlist)[^/]*\.',n.lower()):grade='SEARCH_RESULT_OR_API_RESPONSE_NOT_COMPLETE_ORIGINAL'
  elif re.search(r'(?:app_eo|rv_app_eo|gihtml_eo|nara_original_eo|eo_\d+)',pathlib.PurePosixPath(n).name,re.I):grade='POSSIBLE_ORDER_TEXT_CACHED_UNAUTHENTICATED'
  elif 'govinfo' in str(meta.get('url','')).lower() and len(text)>400:grade='POSSIBLE_GOVINFO_PUBLICATION_TEXT_UNAUTHENTICATED'
  else:grade='OTHER_CACHED_EVIDENCE_UNAUTHENTICATED'
  if noise:grade='BLOCKED_OR_SEARCH_PAGE_DO_NOT_USE_AS_ORIGINAL'
  if len(text)<120 and grade=='POSSIBLE_ORDER_TEXT_CACHED_UNAUTHENTICATED':grade='SHORT_OR_EMPTY_EO_CACHE_UNUSABLE_AS_WHOLE_TEXT'
  match=re.search(r'(?:^|[_-])(?:rv_)?(?:app_|gihtml_|ofr_)?eo[_-]?(\d{1,5}(?:[-_]?[a-z])?)(?:[^0-9A-Za-z]|\.)',pathlib.PurePosixPath(n).name,re.I)
  subject=None
  if match:
   tok=match.group(1)
   mm=re.fullmatch(r'(\d{1,5})[-_]?([a-z])',tok,re.I)
   subject='EO:'+((mm.group(1)+mm.group(2).upper()) if mm else tok)
  raw_json={'tag':tag,'path':n,'sha256':digest,'size':len(b),'url':meta.get('url'),'original_sha256':meta.get('sha256'),'source_grade':grade,'check':validity,'subject_id_hint':subject}
  hash_members[digest].append(n)
  if subject:subject_sources[subject].append(raw_json)
  counts[grade]+=1;counts['all_representations']+=1
  if digest not in copied:
   pass
  # Store canonical blob only once, keep all references for de-dup and provenance.
  if not db.execute('SELECT 1 FROM cache_blobs WHERE sha256=?',(digest,)).fetchone():
   flags='BLOCKED_PAGE' if noise else ''
   # Full searchable text stored, preserving distinct source location and hash separate.
   db.execute('INSERT INTO cache_blobs VALUES(?,?,?,?,?)',(digest,len(b),clip(text,350000),ext,flags))
   db.execute('INSERT INTO cache_fts(sha256,text) VALUES(?,?)',(digest,clip(text,350000)))
   copied.append(digest)
  db.execute('''INSERT INTO cache_representations(sha256,archive_member,inner_archive,source_url,original_host_sha256,declared_extracted_sha256,checksum_verdict,subject_id_hint,source_grade,content_kind) VALUES(?,?,?,?,?,?,?,?,?,?)''',(
   digest,n,tag,meta.get('url'),meta.get('sha256'),expected,validity,subject,grade,ext))
  N+=1
 db.commit()
# de-duplicate by digest and prioritize reliable source representations.
byid=[]
for k,rows in subject_sources.items():
 uniq={x['sha256'] for x in rows};likely={x['sha256'] for x in rows if x['source_grade']=='POSSIBLE_ORDER_TEXT_CACHED_UNAUTHENTICATED'}
 byid.append({'instrument_id_hint':k,'representations':len(rows),'unique_sha256':len(uniq),'possible_single_eo_text_blobs':len(likely),'representations_with_matched_extracted_sha256':sum(x['check']=='MATCHES_DECLARED_TEXT_SHA256' for x in rows),'cached_urls':' | '.join(sorted(set(str(x['url']) for x in rows if x['url']))[:6])})
byid.sort(key=lambda x:(-x['possible_single_eo_text_blobs'],-x['representations'],x['instrument_id_hint']))
with open(base/'INDEXED_CACHED_EO_SOURCE_HINTS.csv','w',newline='',encoding='utf8') as f:
 w=csv.DictWriter(f,fieldnames=list(byid[0]));w.writeheader();w.writerows(byid)
with open(base/'CACHED_SOURCE_CHECKSUM_MISMATCHES.jsonl','w',encoding='utf8') as f:
 for r in mismatch:f.write(json.dumps(r)+'\n')
repeated=sorted(((k,len(v)) for k,v in hash_members.items() if len(v)>1),key=lambda x:-x[1]);dups=[]
for k,num in repeated[:70]:dups.append({'sha256':k,'references':num,'sample_paths':hash_members[k][:8]})
(base/'REPEATED_CACHED_BYTES.json').write_text(json.dumps(dups,indent=2)+'\n')
metric={'total_cached_representations_indexed':N,'unique_cached_content_blobs':len(hash_members),'duplicate_references_removed_at_blob_layer':N-len(hash_members),'sha_matches_extracted_file':db.execute("SELECT COUNT(*) FROM cache_representations WHERE checksum_verdict='MATCHES_DECLARED_TEXT_SHA256'").fetchone()[0], 'sha_mismatches_extracted_file':len(mismatch),'subject_ids_in_cache_filename':len(subject_sources),'subject_ids_with_likely_eo_text_cache':sum(x['possible_single_eo_text_blobs']>0 for x in byid),'by_evidence_role':dict(counts),'note':'SHA match corroborates cached text integrity only. Filename-to-ID is a hint, not authenticated original document. Search result pages may be duplicated, blocked, or unrelated; never use as whole original.'}
(base/'SOURCE_VAULT_METRICS.json').write_text(json.dumps(metric,indent=2)+'\n');db.commit();db.close();print(json.dumps(metric,indent=2))
