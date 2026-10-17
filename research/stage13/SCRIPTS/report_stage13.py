"""Derive report metrics and self-contained offline HTML from corrected Stage13 audit layer."""
import json,csv,sys,pathlib,collections,hashlib,base64,html
root=pathlib.Path(sys.argv[1]);rows=[json.loads(x) for x in (root/'CENSUS/STAGE13_DATE_REFERENCE_OVERLAY_15010.jsonl').open()]
unique=[r for r in rows if r.get('included_unique_document_proxy')];assert len(rows)==15010 and len(unique)==14972
bins=[('1789–1861',1789,1861),('1862–1906',1862,1906),('1907–1936',1907,1936),('1937–1989',1937,1989),('1990–2026',1990,2026)]
def era(r):
 d=r['signing_date_audit_projection'] or r['nara_1989_bibliographic_reference_date'];y=int(d[:4]) if d else 0
 for name,l,h in bins:
  if l<=y<=h:return name
 return 'Undated'
ct=collections.defaultdict(collections.Counter)
for r in unique:ct[era(r)][r['substantive_effect_original']]+=1
rt=[]
for name,*_ in bins:
 c=ct[name];k=c['yes']+c['no']+c['indeterminate'];d=c['yes']+c['no'];rt.append(dict(era=name,included=k,yes=c['yes'],no=c['no'],unknown=c['indeterminate'],determined=d,pct=round(d*100/k,2) if k else None))
c=ct['Undated'];rt.append(dict(era='Undated',included=sum(c.values()),yes=c['yes'],no=c['no'],unknown=c['indeterminate'],determined=c['yes']+c['no'],pct=round((c['yes']+c['no'])*100/sum(c.values()),2)))
assert sum(r['included'] for r in rt)==14972 and sum(r['determined'] for r in rt)==2515
(root/'REPORTS/STATUS_BY_ERA_AFTER_DATE_REFS.csv').parent.mkdir(parents=True,exist_ok=True)
with (root/'REPORTS/STATUS_BY_ERA_AFTER_DATE_REFS.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rt[0]));w.writeheader();w.writerows(rt)
flags=json.loads((root/'AUDIT/ORIGINAL_1943_FLAG_ERROR_VERIFIED.json').read_text());dates=json.loads((root/'CENSUS/DATE_REFERENCE_OVERLAY_METRICS.json').read_text());source_sha=hashlib.sha256((root/'AUDIT/INDEPENDENT_BLIND_FIRST_EIGHT.jsonl').read_bytes()).hexdigest()
blind=list(csv.DictReader((root/'AUDIT/POSTBLIND_COMPARISON_FIRST_EIGHT.csv').open()))
metrics={'release':'stage13','historical_cutoff':'2026-10-14','ledger_preserved_rows':15010,'included_document_proxies':14972,'determinate_substantive':2515,'coverage_fraction':2515/14972,'status_rollup':dict(collections.Counter(r['substantive_effect_original'] for r in unique)),'nara_recovered_editorial_date_labels':18,'still_undated_after_overlay':100,'pre1862_source_dated_proxy_records':3,'no_original_signed_authentication_claim_for_18_dates':True,'lord_date_column_markers_unvalidated':sum(1 for _ in (root/'CENSUS/LORD_GEOMETRY_DATE_LEADS.jsonl').open()),'cohort_provenance_directly_verified':True,'cohort_false_positive_flags':7,'blind_precomparison_count':len(blind),'blind_precomparison_agree_determinate':sum(i['comparison']=='AGREE' for i in blind),'blind_precomparison_hold':sum(i['comparison']=='BLIND_INDETERMINATE' for i in blind),'blind_precomparison_sha256':source_sha,'postkey_EO13286_yes_evidence_stored':True,'first_cessation_national_distribution_known':False,'accepted_legal_yes_no_revised':False,'era_data':rt}
(root/'REPORTS/STAGE13_METRICS.json').write_text(json.dumps(metrics,indent=2)+'\n')
rowmd='\n'.join(f"| {r['era']} | {r['included']:,} | {r['determined']:,} | {str(r['pct'])+'%' if r['pct'] is not None else 'N/A'} |" for r in rt)
readme=f'''# STAGE 13 — Foundational research verification and historical coverage repair

**Cutoff remains:** October 14, 2026. **Mode:** source-grounded, non-destructive corrections, with explicit legal confidence. **Source releases:** Stage 11 frozen ledger SHA256 `c0308e008cd719cd153ca667271c93267d5d855bf3eb26d48076e41938fc7729`; Stage 12 ZIP bundled unaltered in `SOURCES/`.

## Results, and what they mean

Current **working deduplicated bibliography = 14,972 identities**. Substantive Stage11 determinate results = **193 YES, 2,322 NO, 12,457 UNKNOWN**, or **2,515/14,972 = {100*2515/14972:.4f}% classification coverage**. NONE of these legal status assignments was newly promoted or altered. The true 1789–2026 all-history count remains unknown, so the 16.8% is neither a historical census completion fraction nor a survival rate.

**Three genuinely completed foundation checks:**

1. Located original **1,943**-record cohort CSV in persistent Library; compared real unique `canonical_id`s against **1,950** true Stage11 legacy flags; directly verified exactly **seven false-positive cohort flags**, zero missing originals. This previously inherited finding now has original source CSV, source hashes and deterministic `SCRIPTS/verify_original_cohort.py` proof.
2. Recovered **18 exact NARA dated *source-row labels*** for previously undated, already-counted unnumbered identities from the frozen Stage 10 importer. Three labels date to before 1862 (1849, 1852, 1856). Working identity proxies with no usable date decreased **118 → 100**; no legal status nor census membership changed. Keep original signed-date fields NULL until authenticated. Bibliographic month/day/year and actual document signing dates are not automatically equivalent. EO9761 expressly identifies and supersedes an order of President James K. Polk dated Feb. 9, 1849. The Feb. 26, 1852 date may refer to multiple distinct presidential acts; original-document crosswalk required.
3. Conducted and froze **eight** first-pass source-first legal reviews before checking Stage11 outcome key (SHA256 `{source_sha}`). **Seven** independently supported the substantive Stage11 status; **one** (EO13286) was held. Subsequent and **explicitly post-key** independent source research identifies EO13286 §22, amending EO12978, and current 31 CFR §536.312 plus Sept. 30, 2026 official Federal Register authority referencing EO13286. EO13286 YES is supported. This is an eight-case diagnostic, not an estimated overall error rate. Most ancillary-effect questions still need deeper proof.

**Causation and attribution findings:** EO6877's original February 1, 1935 expiry was extended on that date by EO6955-A until 30 days after submission of the Board's report; first cessation remains unknown. EO12220 in June 1980 explicitly describes EO10746 and other revokee EOs as previously superseded at least *in part*: express final revocation is not their first-proven cause. EO14371's two-day 2025 closure is independently checked against original text as a spent substantive dated task, with ancillary-pay rights separately unclosed. EO8507 supersedes the August 8, 1914 public-water-reserve withdrawal only as to lands covered by the new withdrawal; the two same-date NARA rows may be duplicate representations and must not be automatically coded wholesale NO.

**Lord source work:** A better geometric extraction of the provided 1943 *Unnumbered Series* identifies **1,023 potential date-column month tokens**, of which 927 include a plausible day. Its OCR year heuristics proved unreliable; **all extracted years are intentionally NULL** and hints are stored separately as unverified. The leads are **NOT 1,023 executive orders** and none has been admitted. Need manual/document-level inspection and independent original sourcing before expanding the denominator.

## Status by period (source reference dates add a provisional historical layer)

| Period | Working entries | Determinate | Classification coverage |
|---|---:|---:|---:|
{rowmd}

Where the date comes only from the old NARA table, it is a **source reference date**, not authenticated signing date. The pre-1862 row is particularly nonrepresentative. The 2020s include only 2020–October 14 2026.

## Recommended immediate execution gates

- Finish the **60-case independently blind** review from Stage12. The eight completed were a small diagnostic subset; do not compute a national legal error rate from them. Add a source-document/signature check to each validation.
- Independently authenticate a stratified subset of Lord's >1,500 unnumbered catalog entries; extract more document-based identifiers, especially 1789–1862 and 1862–1936, and handle second-hand references separately.
- Resolve possible same-date duplicates of Aug. 8, 1914, and distinct same-date Fillmore orders Feb. 26, 1852. Authenticate EO3016C/K/N signatures and differentiate delegated statutory action from direct presidential instrument.
- Build first-cause **operative episode** timelines, starting with EO6877 and other bounded-ended/revoked orders, and preserve evidence for original automatic expiry vs later-amended condition vs statutory/judicial action.
- Select and publish the primary **legal-effect attribution estimand** only after adversarial TC07/TC09 sensitivity and specialist review; do not rewrite codebook 2.0.0 or alter existing accepted status prematurely.

## How to verify

Use `SCRIPTS/verify_original_cohort.py` with the included `SOURCES/EO_Original_1943_Status_Queue_2026-10-14.csv` and original Stage11 ledger (inside bundled Stage12 frozen release). Use `SCRIPTS/build_source_date_overlay.py` with the included frozen Stage12 normalized JSONL and the previously saved Stage10 disposition-import zip in Library. For the Lord PDF, run `SCRIPTS/geometry_lord_candidates.py` with the PDF in Library, verifying its SHA256 `0553dd2318903af8fd4cdbb56140cd035f3bac52ec5420148307206940ab69e1`. `SCRIPTS/verify_stage13.py` checks structure, source links, sample and no legal decision mutations. No claim is made that all 60 legal reviews or all 30 identity certifications were completed.

**External sources and adverse cases:** `LEGAL/PROVISION_LEVEL_FALSIFICATION_FINDINGS.md`, `CENSUS/IDENTITY_COLLISION_RISK_REGISTER.csv`, `LEGAL/CAUSE_TIMELINE_INDEPENDENT_EVIDENCE.csv`, and `LEGAL/TC07_TC09_ALTERNATIVE_OUTCOME_PANEL.csv`.
'''
(root/'README_FIRST.md').write_text(readme)
# Embed images in self-contained dashboard.
headers='<tr><th>Period</th><th>Included identities</th><th>Substantive decided</th><th>Decided %</th></tr>'
tbody=''.join(f"<tr><td>{html.escape(x['era'])}</td><td>{x['included']:,}</td><td>{x['determined']:,}</td><td>{x['pct'] if x['pct'] is not None else 'N/A'}%</td></tr>" for x in rt)
images=[]
for filename in ['HISTORICAL_ISSUANCE_STATUS_STAGE13.png','DECENNIAL_CLASSIFICATION_COVERAGE_STAGE13.png']:
 b=(root/'VISUALS'/filename).read_bytes();images.append(f'<img alt="{filename}" src="data:image/png;base64,{base64.b64encode(b).decode()}" style="width:100%;height:auto;max-width:1120px">')
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Executive Order Research Stage 13</title><style>body{{background:#f9fafb;color:#17212f;font:16px/1.55 system-ui,-apple-system,sans-serif;max-width:1170px;margin:32px auto;padding:0 20px}}h1{{font-size:29px}}h2{{margin-top:38px;font-size:21px}}.muted{{color:#59697e}}.statgrid{{display:flex;gap:14px;flex-wrap:wrap}}.stat{{flex:1;min-width:175px;background:white;border:1px solid #ddd;border-radius:12px;padding:18px}}.stat strong{{display:block;font-size:28px}}.progress{{height:18px;background:#d5dfe6;border-radius:9px;overflow:hidden}}.progress>div{{height:100%;width:16.798%;background:#386e99}}table{{width:100%;border-collapse:collapse}}td,th{{text-align:right;padding:8px;border-bottom:1px solid #ddd}}td:first-child,th:first-child{{text-align:left}}img{{display:block;margin:17px auto}}.caution{{border-left:4px solid #aa863e;padding-left:15px}}</style></head><body><h1>The Afterlife of Executive Orders · Stage 13</h1><p class="muted">Independent foundational validation, release dated October 16, 2026 · legal cutoff October 14, 2026</p><div class="statgrid"><div class="stat">Candidate included identities<strong>14,972</strong><small>One deduplicated document proxy</small></div><div class="stat">Determinate substantive statuses<strong>2,515</strong><small>193 YES · 2,322 NO</small></div><div class="stat">Unresolved legal statuses<strong>12,457</strong><small>83.2% of working bibliography</small></div><div class="stat">New archival date references<strong>18</strong><small>Three dated before 1862</small></div></div><h2>Substantive classification coverage</h2><div class="progress"><div></div></div><p><strong>16.798%</strong> of the currently identified document-proxy bibliography; this is NOT a surviving-order fraction, a complete historical census, or a measured first-cessation rate.</p><h2>Issuance distribution</h2>{images[0]}<h2>Research completion by decade</h2>{images[1]}<h2>By period</h2><table><thead>{headers}</thead><tbody>{tbody}</tbody></table><h2>What this stage independently accomplished</h2><p>Verified original 1,943-case provenance set against 1,950 Stage11 flags and confirmed seven inherited false flags. Added 18 already-present NARA date-only reference labels to a non-destructive provenance layer. Independently checked eight legal statuses source-first, with one held before comparing the key and subsequently resolved from EO13286 §22 plus contemporary CFR/Federal Register evidence. Identified EO6877's 1935 deadline-extension and two highly ambiguous same-date historical order clusters.</p><p class="caution"><strong>Still unproved:</strong> all-history EO census; actual historical missing fraction; attribution consistency of TC07/TC09 across all categories; nationwide model-classification error rate; first-cessation causal distribution. No existing adjudicated legal-status rows were modified.</p></body></html>'''
(root/'VISUALS/EO_STAGE13_RESEARCH_DASHBOARD.html').write_text(page)
print('metrics and dashboard generated',len(unique))
