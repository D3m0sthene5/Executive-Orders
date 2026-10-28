"""Read-only verification of the published boundary audit and exact sources."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent
ROOT=R.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
    assert ROOT.name != 'research'
    reg=json.loads((R/'SOURCE_REGISTRATION.json').read_text());cat=ROOT/'jobs/astra-source-retention/output/SOURCES.jsonl'
    raw=cat.read_bytes();prefix=raw[:reg['prior_catalogue_bytes']]
    assert hashlib.sha256(prefix).hexdigest()==reg['prior_catalogue_sha256']
    rows=[json.loads(x) for x in raw[reg['prior_catalogue_bytes']:].splitlines()]
    assert len(rows)==16
    for d in rows:
        assert not d.get('instrument_ids')
        assert sha(cat.parent/d['cache_path'])==d['sha256']
        assert (cat.parent/d['text_path']).is_file()
    for d in json.loads((R/'PROTECTED_INPUTS.json').read_text()):
        path=ROOT/d['path']
        actual=path.read_bytes() if path.is_file() else subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:'+d['path']])
        assert hashlib.sha256(actual).hexdigest()==d['sha256']
    cards=json.loads((R/'inventory-trial/BLIND_CARDS.json').read_text())
    review=json.loads((R/'inventory-trial/BLIND_REVIEW.json').read_text())
    assert sha(R/'inventory-trial/BLIND_CARDS.json')==review['blind_packet_sha256']
    verdicts={x['card_id']:x for x in review['cards']}
    for c in cards:
        v=verdicts[c['card_id']];assert canon(c)==v['canonical_card_sha256']
        assert v['verdict'].startswith('upheld')
        text=(ROOT/c['text_path']).read_bytes().decode()
        assert sha(ROOT/c['text_path'])==c['text_sha256']
        prev=-1
        for q in c['clauses']:
            assert prev<=q['char_start']<q['char_end']<=len(text)
            assert text[q['char_start']:q['char_end']]==q['quote']
            prev=q['char_end']
    replay=json.loads((R/'REPLAY.json').read_text())
    for p,digest in replay['code_sha256'].items():assert sha(ROOT/p)==digest
    assert replay['counts']=={'orders':894,'changed':598,'unchanged':296,'patched_outside_bound':0}
    recheck=json.loads((R/'review/FINAL_RECHECK.json').read_text())
    print(json.dumps({'source_versions':len(rows),'reviewed_inventory_cards':len(cards),
                      'screened_trailing_number_texts':894,'changed_inventories':598,
                      'existing_catalogue_prefix_preserved':True,'canonical_status_changes':0,
                      'whole_histories_completed':0,'large_campaign_saving_established':False}))
if __name__=='__main__':main()
