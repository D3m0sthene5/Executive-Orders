"""Mechanical check of original_text / replace_original worker RESULT.jsonl files (coordinator tool; no legal judgment).
usage: python3 -I check_text_results.py RESULT.jsonl ..."""
import hashlib, json, sys
sys.path.insert(0, '/home/claude/executive-orders/jobs/_lib')
import eo_identity as I
F = I.load_fragments('/home/claude/executive-orders')
for p in sys.argv[1:]:
    for l in open(p):
        if not l.strip(): continue
        r = json.loads(l); c = r.get('confirmation'); msg = []
        if c:
            fr = [f for f in F.get(r['instrument_id'], []) if all(f.get(k) == c.get(k) for k in ('instrument_id','grade','sha256','text_sha256'))
                  and f.get('text_path','').lstrip('./') == c.get('text_path','').lstrip('./')]
            msg.append('pin_ok' if fr else 'PIN_MISMATCH')
            if fr and f"{fr[0].get('text_path')}" != c.get('text_path'): msg.append('text_path_spelling:'+fr[0].get('text_path'))
            try:
                h = hashlib.sha256(open('/home/claude/executive-orders/'+c['text_path'].lstrip('./'),'rb').read()).hexdigest()
                msg.append('sha_ok' if h == c.get('text_sha256') else 'SHA_MISMATCH')
            except Exception as e: msg.append('FILE_ERR')
            msg.append('checks=%s/%s/%s req_pages=%s confirmed=%s method=%s' % (c.get('identity_confirmed'), c.get('complete_text_confirmed'), c.get('pages_confirmed'), c.get('requires_page_check'), c.get('confirmed'), c.get('method')))
        print(r['instrument_id'], r['step'], r['outcome'][:110], '|', ' '.join(msg))
