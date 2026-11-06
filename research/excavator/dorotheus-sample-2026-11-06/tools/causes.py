"""Group DISPOSITION blockers into causes by fixed keyword rules (coordinator clerical classification; first
matching rule wins; the exact blocker text stays in DISPOSITION.csv). usage: python3 -I causes.py -> CAUSES.json"""
import csv, collections, json, re
from pathlib import Path
W = Path('/home/user/Executive-Orders/research/excavator/dorotheus-sample-2026-11-06')
RULES = [
    ('existing claim of another owner', r'existing incomplete claim of another owner'),
    ('review control missed (batch not filed)', r'control .*missed|missed by arms'),
    ('checker index lacks the order signing date', r'no_signing_date_known'),
    ('source held only as a custody record, or not held (mostly dispatch blocks)', r'mandatory source not held|custody_record_only|dispatch-blocked|not_held|original_or_inventory_absent'),
    ('no acceptable original held (status overlay needs one; transcription or replica only)', r'acceptable.as.original|acceptable original|official original|replica|transcription only|wikisource|proquest replica|page check'),
    ('later instrument held only as mirror or unregistered', r'mirror|registered|not registered|official fr text|official federal register text|federal register pdf|held bytes'),
    ('emergency continuation notices not held', r'continuation notice|national emergenc|nea '),
    ('performance / occurrence not shown (one-time command, waiver, report, completion)', r'perform|appointment|transfer|report|completion|was made|occurr|liquidat|conversion|discharge'),
    ('ending statute or ending instrument text not held', r'statute|act of|public law|pub\. l|stat\.|joint resolution|s\.j\. res|public land order|plo|revocation|revok|terminat|repeal|ending|ended|end of'),
    ('current-law source not held (CFR / U.S. Code / CURRENT record)', r'current|cfr|u\.s\.c|usc|in force|still'),
    ('text or inventory defect (OCR, wrong text, inventory)', r'ocr|garbled|inventory|wrong|text'),
]
def cause(t):
    t = (t or '').lower()
    for name, rx in RULES:
        if re.search(rx, t): return name
    return 'other'
R = [r for r in csv.DictReader(open(W / 'DISPOSITION.csv')) if r['outcome'] in ('blocked', 'nonresponse_dispatch', 'nonresponse_producer', 'rejected_review')]
out = collections.defaultdict(lambda: collections.defaultdict(list))
for r in R: out[r['wave']][cause(r['blocker'])].append(r['id'])
res = {w: {c: {'n': len(v), 'ids': v} for c, v in sorted(d.items(), key=lambda x: -len(x[1]))} for w, d in out.items()}
(W / 'CAUSES.json').write_text(json.dumps(res, indent=1) + '\n')
for w, d in res.items():
    for c, v in d.items(): print(w, v['n'], c, ' '.join(v['ids'][:12]))
