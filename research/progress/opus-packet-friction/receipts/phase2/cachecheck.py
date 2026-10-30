"""Stale-index check for jobs/claim-kit/fragment_cache.py on the real corpus.

Run: python3 -I cachecheck.py   (writes CACHE_CHECK.json next to this script)

Every perturbation of the isolated tree is made by renaming the original out of the way into
w-cache/backup (so the original inode/bytes/mtime are never written to) and, where needed, writing a NEW file;
revert is the rename back. Everything touched is verified afterwards by sha256, inode, size, mtime_ns, and a
whole-tree stat manifest taken before and after.
"""
import sys
sys.dont_write_bytecode = True
import glob
import hashlib
import json
import os
import re
import shutil
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = Path('/tmp/claude-0/-home-user-Executive-Orders/43dc4dbb-34dc-5dd9-8960-2e617340c49a/scratchpad/opus/replay/cachecheck')
CACHE = HERE / 'cache'
BACKUP = HERE / 'backup'
OUT = HERE / 'CACHE_CHECK.json'
shutil.rmtree(CACHE, ignore_errors=True)
shutil.rmtree(BACKUP, ignore_errors=True)
BACKUP.mkdir(parents=True)
os.environ['CLAIM_KIT_CACHE_DIR'] = str(CACHE)
os.environ.pop('CLAIM_KIT_INDEX_CACHE', None)
sys.path.insert(0, str(TREE / 'jobs' / 'claim-kit'))
import working_text as W          # noqa: E402
import fragment_cache as F        # noqa: E402

T = TREE
T0 = time.time()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for c in iter(lambda: fh.read(1 << 22), b''):
            h.update(c)
    return h.hexdigest()


def manifest():
    files, dirs = {}, set()
    for root, ds, fs in os.walk(TREE):
        for d in ds:
            dirs.add(os.path.relpath(os.path.join(root, d), TREE))
        for f in fs:
            p = os.path.join(root, f)
            st = os.lstat(p)
            files[os.path.relpath(p, TREE)] = (st.st_ino, st.st_size, st.st_mtime_ns, st.st_nlink, st.st_mode)
    return files, dirs


# ---------------------------------------------------------------- perturbation transaction journal
class Tx:
    def __init__(self):
        self.entries = []   # every touched path, ever
        self.n = 0

    def _rec(self, path, kind):
        path = Path(path)
        e = {'path': str(path.relative_to(TREE)), 'kind': kind, 'active': True, 'created_dirs': []}
        if path.exists():
            st = path.stat()
            e.update(orig_sha256=sha256_file(path), orig_ino=st.st_ino, orig_size=st.st_size,
                     orig_mtime_ns=st.st_mtime_ns, orig_atime_ns=st.st_atime_ns, orig_mode=st.st_mode & 0o7777)
        else:
            e['orig_absent'] = True
        self.entries.append(e)
        return e

    def _stash(self, path, e):
        self.n += 1
        bak = BACKUP / f'{self.n}.orig'
        os.rename(path, bak)
        e['backup'] = str(bak)

    def delete(self, path):
        e = self._rec(path, 'delete')
        self._stash(path, e)
        return e

    def edit(self, path, newraw, keep_times=False):
        e = self._rec(path, 'edit')
        self._stash(path, e)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'wb') as fh:
            fh.write(newraw)
        os.chmod(path, e['orig_mode'])
        if keep_times:
            os.utime(path, ns=(e['orig_atime_ns'], e['orig_mtime_ns']))
        return e

    def create(self, path, raw):
        path = Path(path)
        e = self._rec(path, 'create')
        assert e.get('orig_absent'), f'{path} exists'
        missing = []
        d = path.parent
        while not d.exists():
            missing.append(d)
            d = d.parent
        for d in reversed(missing):
            d.mkdir()
            e['created_dirs'].append(str(d))
        path.write_bytes(raw)
        return e

    def revert(self, e):
        if not e['active']:
            return
        p = TREE / e['path']
        if e['kind'] in ('delete', 'edit'):
            if p.exists():
                p.unlink()
            os.rename(e['backup'], p)
        else:
            if p.exists():
                p.unlink()
            for d in reversed(e['created_dirs']):
                try:
                    os.rmdir(d)
                except OSError:
                    pass
        e['active'] = False

    def revert_all(self):
        for e in reversed(self.entries):
            self.revert(e)

    def verify(self):
        res = []
        for e in self.entries:
            p = TREE / e['path']
            if e.get('orig_absent'):
                ok = not p.exists() and not any(os.path.exists(d) for d in e['created_dirs'])
                res.append({'path': e['path'], 'kind': e['kind'], 'expected': 'absent', 'ok': ok})
            else:
                st = p.stat()
                ok = (sha256_file(p) == e['orig_sha256'] and st.st_ino == e['orig_ino'] and st.st_size == e['orig_size']
                      and st.st_mtime_ns == e['orig_mtime_ns'] and (st.st_mode & 0o7777) == e['orig_mode'])
                res.append({'path': e['path'], 'kind': e['kind'], 'sha256': e['orig_sha256'], 'ok': ok,
                            'same_inode_size_mtime_mode': True if ok else False})
        return res


tx = Tx()


# ---------------------------------------------------------------- equality
def eq(a, b):
    """Strict: type, repo, dict equality AND key order AND JSON-serialised equality (inner key order too)."""
    if type(a) is not type(b) or a.repo != b.repo:
        return False
    for n in ('by_sha', 'official', 'official_by_sha'):
        x, y = getattr(a, n), getattr(b, n)
        if x != y or list(x) != list(y):
            return False
        if json.dumps(x, ensure_ascii=True) != json.dumps(y, ensure_ascii=True):
            return False
    return True


def shape(i):
    return [len(i.by_sha), sum(map(len, i.by_sha.values())), len(i.official), len(i.official_by_sha),
            sum(map(len, i.official_by_sha.values()))]


# ---------------------------------------------------------------- claims
CLAIMS = sorted(glob.glob(str(TREE / 'research/readiness/claims/*.jsonl')))
SHA_LOC = {}   # source sha -> [(file basename, line no)]
for f in CLAIMS:
    with open(f, encoding='utf-8') as fh:
        for n, line in enumerate(fh):
            try:
                c = json.loads(line)
            except ValueError:
                continue
            if not isinstance(c, dict):
                continue
            for _, ref in W.references(c):
                s = W.source_sha(ref)
                if s:
                    SHA_LOC.setdefault(s, set()).add((os.path.basename(f), n))
_claim_cache = {}


def load_claim(loc):
    if loc not in _claim_cache:
        with open(TREE / 'research/readiness/claims' / loc[0], encoding='utf-8') as fh:
            for n, line in enumerate(fh):
                if n == loc[1]:
                    _claim_cache[loc] = json.loads(line)
                    break
    return _claim_cache[loc]


def claims_for(shas, limit=2):
    locs = sorted({l for s in shas for l in SHA_LOC.get(s, ())})
    return locs[:limit]


# ---------------------------------------------------------------- fresh baseline & fixed claims
log = []


def say(*a):
    msg = ' '.join(str(x) for x in a)
    log.append(f'[{time.time() - T0:7.1f}s] {msg}')
    print(log[-1], file=sys.stderr, flush=True)


report = {'tree': str(TREE), 'cache_dir': str(CACHE), 'python': sys.version.split()[0], 'started': time.strftime('%F %T')}
man_before = manifest()
report['manifest_before'] = {'files': len(man_before[0]), 'dirs': len(man_before[1])}

t = time.time()
fresh0 = W.Index(TREE)
t_fresh0 = time.time() - t
say('fresh baseline', round(t_fresh0, 2), shape(fresh0))

by_decl = {}
for d, m in (('by', fresh0.by_sha), ('off', fresh0.official_by_sha)):
    for s, recs in m.items():
        for r in recs:
            by_decl.setdefault((d, r['declaration_path']), set()).add(s)
fixed = []
for key in (('by', 'jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl'),
            ('by', 'jobs/app-transcriptions/output/FRAGMENTS.jsonl'),
            ('by', 'jobs/hathi-gpo-orders/output/FRAGMENTS.jsonl'),
            ('off', 'jobs/ofr-compilations/output/FRAGMENTS.jsonl'),
            ('off', 'jobs/fr-originals/output/FRAGMENTS.jsonl')):
    for loc in claims_for(by_decl[key], limit=50):
        if loc not in fixed:
            fixed.append(loc)
            break
assert len(fixed) == 5, fixed
report['fixed_claims'] = [list(l) for l in fixed]

# baseline policies (fresh) for every claim we might use, to show perturbations have teeth
BASE_POL = {}


def pol_fresh(loc, idx):
    errs, dep = W.policy(load_claim(loc), TREE, idx)
    return [errs, dep]


def base_policy(loc):
    if loc not in BASE_POL:
        BASE_POL[loc] = pol_fresh(loc, fresh0)
    return BASE_POL[loc]


for l in fixed:
    base_policy(l)
report['fixed_claims_baseline'] = {f'{l[0]}:{l[1]}': {'errors': len(BASE_POL[l][0]), 'dependent': len(BASE_POL[l][1])}
                                   for l in fixed}


# ---------------------------------------------------------------- compare
def drop_cache_for(key):
    for p in CACHE.glob(f'*{key}*.json'):
        p.unlink()


def compare(label, claim_locs, baseline=fresh0):
    rec = {'label': label}
    t = time.time(); fresh = W.Index(TREE); rec['seconds_fresh'] = round(time.time() - t, 3)
    rec['shape'] = shape(fresh)
    rec['perturbation_effective'] = not eq(fresh, baseline)
    # (a) fragment_cache.build, natural cache state
    t = time.time(); b, status, key, _w = F.build(TREE); rec['seconds_build'] = round(time.time() - t, 3)
    rec['status'] = status
    rec['equal_build'] = eq(fresh, b)
    # (b) shared() in the long-lived process; first force the shared() miss path by dropping this key's disk entry
    # (otherwise build() above would have pre-populated the disk cache for it)
    had_inprocess = len(F._SHARED)
    drop_cache_for(key)
    t = time.time(); s = F.shared(TREE); rec['seconds_shared_first'] = round(time.time() - t, 3)
    rec['shared_status_first'] = F.last_status
    rec['equal_shared'] = eq(fresh, s)
    t = time.time(); s2 = F.shared(TREE); rec['seconds_shared_reuse'] = round(time.time() - t, 3)
    rec['shared_status_second'] = F.last_status
    rec['equal_shared_reuse'] = eq(fresh, s2)
    rec['shared_reuse_same_object'] = s2 is s
    rec['inprocess_entries_before'] = had_inprocess
    # second build after shared stored the entry -> must be a hit and still equal
    t = time.time(); b2, status2, _, _ = F.build(TREE); rec['seconds_build_hit'] = round(time.time() - t, 3)
    rec['status_after_shared'] = status2
    rec['equal_build_hit'] = eq(fresh, b2)
    # policy
    pe, changed, per = True, 0, []
    for loc in claim_locs:
        claim = load_claim(loc)
        pf = pol_fresh(loc, fresh)
        with F.policy_index(TREE):
            pc = W.policy(claim, TREE)
        same = [pf[0], pf[1]] == [pc[0], pc[1]]
        pe = pe and same
        ch = pf != base_policy(loc)
        changed += ch
        per.append({'claim': f'{loc[0]}:{loc[1]}', 'equal': same, 'errors': len(pf[0]), 'dependent': len(pf[1]),
                    'differs_from_unperturbed': ch})
    rec['policy_equal'] = pe
    rec['policy_claims'] = per
    rec['policy_results_changed_vs_unperturbed'] = changed
    assert W.policy.__name__ == 'policy' and not hasattr(W.policy, '__wrapped__')
    say(label, rec['status'], 'build', rec['equal_build'], 'shared', rec['equal_shared'], rec['equal_shared_reuse'],
        'policy', pe, 'effective', rec['perturbation_effective'])
    return rec


# ---------------------------------------------------------------- step 0
step0 = {}
step0['seconds_fresh'] = round(t_fresh0, 3)
t = time.time(); c1, s1, k1, _ = F.build(TREE); step0['seconds_build_1'] = round(time.time() - t, 3)
t = time.time(); c2, s2, k2, _ = F.build(TREE); step0['seconds_build_2'] = round(time.time() - t, 3)
step0.update(status_1=s1, status_2=s2, equal_1=eq(fresh0, c1), equal_2=eq(fresh0, c2), key=k1,
             order_equal=all(list(getattr(fresh0, n)) == list(getattr(c2, n)) for n in ('by_sha', 'official', 'official_by_sha')),
             tuple_equal=(fresh0.by_sha, fresh0.official, fresh0.official_by_sha) == (c2.by_sha, c2.official, c2.official_by_sha))
t = time.time(); sh = F.shared(TREE); step0['seconds_shared_first'] = round(time.time() - t, 3)
step0['shared_status_first'] = F.last_status
t = time.time(); sh2 = F.shared(TREE); step0['seconds_shared_reuse'] = round(time.time() - t, 3)
step0['shared_status_second'] = F.last_status
step0['equal_shared'] = eq(fresh0, sh) and eq(fresh0, sh2)
cache_files = sorted(p.name for p in CACHE.glob('*.json'))
step0['cache_files'] = cache_files
step0['cache_bytes'] = sum(p.stat().st_size for p in CACHE.glob('*.json'))
t = time.time()
with F.policy_index(TREE):
    for l in fixed[:1]:
        W.policy(load_claim(l), TREE)
step0['seconds_policy_index_one_claim_warm'] = round(time.time() - t, 3)
report['step0'] = step0
say('step0', step0)

results = []


def run(name, setup, claim_shas_fn, teardown=None, extra=None):
    """setup() applies the perturbation and returns journal entries; compare; revert; compare."""
    entry = {'perturbation': name}
    try:
        info = setup()
        entry['detail'] = info['detail']
        shas = info.get('shas', ())
        locs = list(fixed) + [l for l in claims_for(shas) if l not in fixed]
        entry['claims_used'] = [f'{l[0]}:{l[1]}' for l in locs]
        entry['applied'] = compare(name + ':applied', locs)
        for e in info['entries']:
            tx.revert(e)
        entry['reverted'] = compare(name + ':reverted', locs)
        entry['reverted_equals_original'] = eq(fresh0, W.Index(TREE))
    except Exception:
        entry['error'] = traceback.format_exc()
        say('ERROR in', name, entry['error'])
        tx.revert_all()
    results.append(entry)
    return entry


def find_line(raw, needle_bytes, pred):
    pos = 0
    while True:
        i = raw.find(needle_bytes, pos)
        if i < 0:
            return None
        s = raw.rfind(b'\n', 0, i) + 1
        e = raw.find(b'\n', i)
        e = len(raw) if e < 0 else e
        try:
            row = json.loads(raw[s:e])
        except ValueError:
            row = None
        if row is not None and pred(row):
            return s, e, row
        pos = e + 1


def mutate_row(rel, rec, field):
    """Same-length edit of data[field] of the row that produced fresh-index record rec. Returns (path, newraw)."""
    path = TREE / rel
    raw = path.read_bytes()
    want = rec[field]
    hit = find_line(raw, rec['sha256'].encode(), lambda r: r.get('kind') == 'original_representation'
                    and r.get('instrument_id') == rec['instrument_id'] and isinstance(r.get('data'), dict)
                    and r['data'].get('sha256') == rec['sha256'] and r['data'].get(field) == want
                    and r['data'].get('text_sha256') == rec['text_sha256'])
    assert hit, 'row not found'
    s, e, row = hit
    line = raw[s:e]
    m = None
    for mm in re.finditer(rb'"%s"\s*:\s*"([^"]*)"' % field.encode(), line):
        if mm.group(1).decode() == want:
            m = mm
            break
    assert m, 'value not found in line'
    a, b = m.span(1)
    old = line[a:b]
    last = old[-1:]
    new_last = b'0' if last != b'0' else b'1'
    if field == 'grade':
        new_last = b'x' if last != b'x' else b'y'
    newline = line[:b - 1] + new_last + line[b:]
    assert len(newline) == len(line)
    new_row = json.loads(newline)
    diffs = [k for k in row['data'] if row['data'][k] != new_row['data'].get(k)]
    assert diffs == [field] and {k: v for k, v in row.items() if k != 'data'} == {k: v for k, v in new_row.items() if k != 'data'}, diffs
    newraw = raw[:s] + newline + raw[e:]
    assert len(newraw) == len(raw)
    return path, newraw, {'file': rel, 'instrument_id': rec['instrument_id'], 'field': field,
                          'old': old.decode(), 'new': (old[:-1] + new_last).decode(), 'byte_offset': s + a}


def referenced_recs(index_map, decl, need_text_sha=True):
    out = []
    for s, recs in index_map.items():
        if s in SHA_LOC:
            for r in recs:
                if r['declaration_path'] == decl and (not need_text_sha or (isinstance(r.get('text_sha256'), str) and len(r['text_sha256']) == 64)):
                    out.append(r)
    return out


# ---------------------------------------------------------------- P1 addition
P1_FILE = TREE / 'jobs/zz-cachecheck/output/FRAGMENTS.jsonl'


def real_row_for(rec):
    raw = (TREE / rec['declaration_path']).read_bytes()
    hit = find_line(raw, rec['sha256'].encode(), lambda r: r.get('kind') == 'original_representation'
                    and r.get('instrument_id') == rec['instrument_id'] and isinstance(r.get('data'), dict)
                    and r['data'].get('sha256') == rec['sha256'])
    assert hit
    return hit[2]


def setup_p1():
    rec = referenced_recs(fresh0.by_sha, 'jobs/hathi-gpo-orders/output/FRAGMENTS.jsonl', False)[0]
    row = real_row_for(rec)
    row = json.loads(json.dumps(row))
    row['instrument_id'] = 'ZZ-CACHECHECK-1'
    row['data']['text_path'] = rec['text_path']        # repo-relative form, resolves for the new provider dir
    e = tx.create(P1_FILE, (json.dumps(row) + '\n').encode())
    return {'entries': [e], 'shas': [rec['sha256']],
            'detail': {'new_file': str(P1_FILE.relative_to(TREE)), 'copied_from': rec['declaration_path'],
                       'orig_instrument_id': rec['instrument_id'], 'new_instrument_id': 'ZZ-CACHECHECK-1', 'sha256': rec['sha256']}}


run('P1_add_provider_file', setup_p1, None)


# ---------------------------------------------------------------- P2 deletion (few rows) and P2b (claim-referenced)
def delete_provider(rel):
    def setup():
        rows = sum(1 for m in (fresh0.by_sha, fresh0.official_by_sha) for v in m.values() for r in v if r['declaration_path'] == rel)
        shas = {s for m in (fresh0.by_sha, fresh0.official_by_sha) for s, v in m.items() for r in v if r['declaration_path'] == rel}
        e = tx.delete(TREE / rel)
        return {'entries': [e], 'shas': sorted(shas), 'detail': {'deleted': rel, 'index_rows_contributed': rows,
                                                                  'size': e['orig_size']}}
    return setup


run('P2_delete_provider_numbered-early-orders', delete_provider('jobs/numbered-early-orders/output/FRAGMENTS.jsonl'), None)
run('P2b_delete_provider_hathi-gpo-orders', delete_provider('jobs/hathi-gpo-orders/output/FRAGMENTS.jsonl'), None)


# ---------------------------------------------------------------- P3 same-size edit + mtime restored
def edit_setup(decl, field, keep_times):
    def setup():
        rec = referenced_recs(fresh0.by_sha, decl)[0]
        path, newraw, det = mutate_row(decl, rec, field)
        orig = path.stat()
        e = tx.edit(path, newraw, keep_times=keep_times)
        new = path.stat()
        det.update(size=new.st_size, size_unchanged=new.st_size == orig.st_size, mtime_ns_restored=new.st_mtime_ns == orig.st_mtime_ns,
                   new_inode=new.st_ino != orig.st_ino, sha256_changed=sha256_file(path) != e['orig_sha256'])
        assert det['size_unchanged'] and det['mtime_ns_restored']
        return {'entries': [e], 'shas': [rec['sha256']], 'detail': det}
    return setup


run('P3_same_size_edit_text_sha256_mtime_restored', edit_setup('jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl', 'text_sha256', True), None)


# ---------------------------------------------------------------- P4 delete text file of an official row
def setup_p4():
    rec = referenced_recs(fresh0.official_by_sha, 'jobs/ofr-compilations/output/FRAGMENTS.jsonl', False)[0]
    e = tx.delete(TREE / rec['text_path'])
    return {'entries': [e], 'shas': [rec['sha256']],
            'detail': {'deleted_text_file': rec['text_path'], 'row_instrument_id': rec['instrument_id'],
                       'declared_in': rec['declaration_path'], 'size': e['orig_size'],
                       'provider_inventory_unchanged': True}}


run('P4_delete_text_file_of_official_row', setup_p4, None)

# ---------------------------------------------------------------- P5 create a text file for a row whose text file is absent
missing_real = 0
for p in F.provider_paths(TREE):
    for r in F._parse_file(p)[1]:
        try:
            a = W._child(TREE, r[5], p.parent)
            if not a.is_file():
                a = W._child(TREE, r[5])
        except (ValueError, TypeError):
            continue
        if not a.is_file():
            missing_real += 1
report['P5_real_rows_with_missing_text_file'] = missing_real

P5_DIR = 'jobs/zz-cachecheck/output'
P5_A = TREE / P5_DIR / 'zz_missing_provider_relative.txt'
P5_B = TREE / 'zz_missing_repo_relative.txt'
entry5 = {'perturbation': 'P5_create_text_file_for_row_with_missing_text',
          'note': f'Real rows whose text file is absent: {missing_real} (every parsed provider row resolves to an existing file). '
                  'A synthetic official-eligible provider (jobs/zz-cachecheck, acceptable_as_original=true, needs_page_check=false) '
                  'references one provider-relative and one repo-relative absent text path; the text files are then created/removed.'}
try:
    rows = []
    for name, tp in (('ZZ-CACHECHECK-P5A', 'zz_missing_provider_relative.txt'), ('ZZ-CACHECHECK-P5B', 'zz_missing_repo_relative.txt')):
        rows.append(json.dumps({'kind': 'original_representation', 'instrument_id': name, 'produced_by': 'zz-cachecheck',
                                'data': {'sha256': hashlib.sha256(name.encode()).hexdigest(), 'grade': 'official_original',
                                         'acceptable_as_original': True, 'needs_page_check': False,
                                         'text_path': tp, 'text_sha256': hashlib.sha256(b'x').hexdigest(), 'complete_text': True,
                                         'url': 'https://example.invalid/' + name}}))
    ep = tx.create(P1_FILE, ('\n'.join(rows) + '\n').encode())
    base5 = W.Index(TREE)       # provider present, text files absent
    entry5['setup_equal_to_original'] = eq(base5, fresh0)       # expected True: absent text files add nothing
    locs = list(fixed)
    entry5['claims_used'] = [f'{l[0]}:{l[1]}' for l in locs]
    entry5['provider_added_text_absent'] = compare('P5_0_provider_added_text_absent', locs, baseline=fresh0)
    ea = tx.create(P5_A, b'provider-relative working text\n')
    entry5['created_provider_relative'] = compare('P5_1_create_provider_relative_text', locs, baseline=base5)
    eb = tx.create(P5_B, b'repo-relative text\n')
    entry5['created_both'] = compare('P5_2_create_repo_relative_text_too', locs, baseline=base5)
    tx.revert(ea)
    entry5['removed_provider_relative'] = compare('P5_3_remove_provider_relative_text', locs, baseline=base5)
    tx.revert(eb)
    entry5['removed_both'] = compare('P5_4_remove_repo_relative_text', locs, baseline=base5)
    tx.revert(ep)
    entry5['reverted'] = compare('P5_5_provider_removed', locs)
except Exception:
    entry5['error'] = traceback.format_exc()
    say('ERROR in P5', entry5['error'])
    tx.revert_all()
results.append(entry5)

# ---------------------------------------------------------------- P6 same-size edit on a >10 MB file
big = [(p, p.stat().st_size) for p in F.provider_paths(TREE) if p.stat().st_size > 10 * 1024 * 1024]
report['files_over_10MB'] = [[p.relative_to(TREE).as_posix(), s] for p, s in big]
run('P6_same_size_edit_grade_on_gt10MB_file_mtime_restored',
    edit_setup('jobs/app-transcriptions/output/FRAGMENTS.jsonl', 'grade', True), None)

# ---------------------------------------------------------------- finish
tx.revert_all()
report['perturbations'] = results
report['restoration'] = tx.verify()
man_after = manifest()
report['manifest_identical_after'] = man_before == man_after
if man_before != man_after:
    report['manifest_diff'] = {
        'files_changed': sorted(k for k in set(man_before[0]) | set(man_after[0]) if man_before[0].get(k) != man_after[0].get(k))[:50],
        'dirs_changed': sorted(man_before[1] ^ man_after[1])[:50]}
report['all_restored'] = all(r['ok'] for r in report['restoration'])
report['finished'] = time.strftime('%F %T')
report['elapsed_seconds'] = round(time.time() - T0, 1)

# rollup
bad = []
for r in results:
    for k, v in r.items():
        if isinstance(v, dict) and 'equal_build' in v:
            for fld in ('equal_build', 'equal_shared', 'equal_shared_reuse', 'equal_build_hit', 'policy_equal'):
                if v[fld] is not True:
                    bad.append((r['perturbation'], k, fld))
    if 'error' in r:
        bad.append((r['perturbation'], 'error'))
report['inequalities'] = bad
report['log'] = log
OUT.write_text(json.dumps(report, indent=1))
say('DONE; inequalities:', bad, 'restored:', report['all_restored'], 'manifest identical:', report['manifest_identical_after'])
