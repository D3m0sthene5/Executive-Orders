"""Render honest, separate census/status/causal/validity/capability progress."""
from pathlib import Path
import sqlite3,json,csv,html,datetime,collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
C=sqlite3.connect(ROOT/'DATA/AFTERLIFE_STAGE16_CANONICAL.sqlite')
metrics=json.loads((ROOT/'REPORTS/VERIFIED_BUILD_METRICS.json').read_text())['metrics']
labels=[]; categories=[]
for y in range(1780,2030,10):
 rows=C.execute('SELECT original_legacy_status,count(*) FROM instruments WHERE include_proxy=1 AND CAST(substr(issuance_date,1,4) AS INT) BETWEEN ? AND ? GROUP BY original_legacy_status',(y,y+9)).fetchall()
 a=dict(rows)
 labels.append(y);categories.append([a.get('yes',0),a.get('no',0),a.get('indeterminate',0)])
x=np.array(labels);vals=np.array(categories)
fig,ax=plt.subplots(figsize=(15,5.2))
width=8.0
ax.bar(x,vals[:,2],width=width,label='Substantive UNKNOWN')
ax.bar(x,vals[:,1],bottom=vals[:,2],width=width,label='Provisional substantive NO')
ax.bar(x,vals[:,0],bottom=vals[:,2]+vals[:,1],width=width,label='Provisional substantive YES')
ax.set_xlabel('Executive-order issuance decade (source-date projection)')
ax.set_ylabel('Number of working documentary proxies')
ax.set_xlim(1782,2030)
ax.set_xticks(np.arange(1790,2030,20))
ax.grid(axis='y',alpha=.18)
ax.legend(loc='upper left')
fig.suptitle('Executive-order working bibliography, 1789–October 2026',fontsize=14)
ax.set_title('Historical census incomplete; bars show only identified, dated proxies. 100 undated records excluded.',fontsize=10)
fig.tight_layout()
png=ROOT/'VISUALS/ISSUANCE_DECADE_DISTRIBUTION_STAGE16.png';fig.savefig(png,dpi=150);plt.close(fig)

def progress(label,main,description,proportion=None,accent='#426d91'):
 bar='' if proportion is None else f'<div class="track"><span style="width:{max(0,min(proportion,1))*100:.3f}%;background:{accent}"></span></div>'
 return f'<section class="metric"><div class="label">{label}</div><div class="number">{main}</div>{bar}<div class="description">{description}</div></section>'
sub=metrics['stage11_determinate']/metrics['working_unique_proxies']
metrics_ui=''.join([
 progress('Historical census','Incomplete','14,972 documentary proxies; original signed-document count and the all-history issued denominator remain unknown. 1,023 raw Lord date leads are not orders.'),
 progress('Present legal status',f'{sub*100:.2f}%','2,515 inherited, model-reviewed YES/NO decisions among working proxies. This does not establish legal accuracy or survival rate.',sub),
 progress('First-cessation history','Unestablished','21 newly reconstructed provision episodes, 8 exact scoped expiration events; no newly certified whole-order first-cessation dates.'),
 progress('Independent scientific validity','0 / 120','Independent probability-sample reviews completed: 0 of 120. One new whole-order normative NO is a first-pass conclusion; four others remain held or indeterminate. None has independent legal certification.',0),
 progress('Research infrastructure','7,084','Usable research candidate edges after source reconstruction and conflict quarantine; 438 source-anchored historical event records. No metadata-only status promotions.')])
eras=list(csv.DictReader(open(ROOT/'REPORTS/PROGRESS_BY_ERA.csv')))
tr=''.join(f'<tr><td>{r["period"]}</td><td>{int(r["total"]):,}</td><td>{int(r["yes"]):,}</td><td>{int(r["no"]):,}</td><td>{int(r["unknown"]):,}</td><td>{((int(r["yes"])+int(r["no"]))/int(r["total"])*100):.1f}%</td></tr>' for r in eras)
import base64
inline='data:image/png;base64,'+base64.b64encode(png.read_bytes()).decode()
content=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Afterlife of Executive Orders | Stage16</title><style>
:root{{--fg:#20272f;--bg:#f5f7fa;--muted:#5c6670;--line:#dfe6ee;--paper:#fff}}*{{box-sizing:border-box}}body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--fg);margin:0}}main{{max-width:1100px;margin:auto;padding:38px 24px 80px}}h1{{font-size:32px;letter-spacing:-.9px;margin:12px 0 9px}}h2{{font-size:21px;margin-top:36px}}p{{color:var(--muted);line-height:1.55}}.meta{{font-size:13px;text-transform:uppercase;letter-spacing:1.2px;color:#5c778c}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:12px;margin:27px 0}}.metric{{padding:18px;border:1px solid var(--line);border-radius:12px;background:var(--paper)}}.label{{color:var(--muted);font-size:13px;min-height:36px}}.number{{font-weight:700;font-size:28px;letter-spacing:-.7px}}.description{{font-size:12px;color:var(--muted);line-height:1.5;margin-top:12px}}.track{{height:8px;border-radius:5px;background:#e8edf1;margin-top:10px;overflow:hidden}}.track span{{display:block;height:100%;border-radius:5px}}.panel{{background:var(--paper);padding:18px;border:1px solid var(--line);border-radius:13px}}.panel img{{width:100%;height:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{padding:11px 9px;border-bottom:1px solid var(--line);text-align:right}}td:first-child,th:first-child{{text-align:left}}.note{{border-left:3px solid #9b7444;padding:12px 16px;background:#fff;line-height:1.5}}footer{{color:var(--muted);font-size:12px;padding-top:25px}}@media(max-width:680px){{table{{font-size:10px}}td,th{{padding:8px 4px}}main{{padding:24px 12px}}}}
</style></head><body><main><div class="meta">Scientific reconstruction · Stage 16 · cutoff October 14, 2026</div><h1>The Afterlife of Executive Orders</h1><p>A five-dimensional research status, with no claimed national census completion or invented survival estimate. The legacy v2.0.0 classifications are preserved separately from new source-reviewed v3.0.0 decisions.</p><div class="metrics">{metrics_ui}</div><h2>Historical issuance and research status</h2><div class="panel"><img alt="Decade by decade histogram of currently identified executive order working documentary proxies with YES NO UNKNOWN legal status" src="{inline}"><p>Only existing bibliographic proxies with usable issuance dates are shown. The unnumbered historical population is seriously undercovered. Editorial date matches remain unverified documentary identity evidence.</p></div><h2>Coverage by era</h2><div class="panel"><table><thead><tr><th>Issuance era</th><th>Working proxies</th><th>YES</th><th>NO</th><th>UNKNOWN</th><th>Legacy research coverage</th></tr></thead><tbody>{tr}</tbody></table></div><h2>Evidence movement during Stage 16</h2><p>11,164 government source observations unified; 513 previously omitted NARA successor-reference candidates discovered; one fails chronology and two more conflict with a controlling-source schedule, leaving 510 usable recovered leads. Among 7,084 surviving candidate links, all remain unverified for whole-order scope until adjudication. There are 386 primary-schedule EO 12553 formal revocation targets and 45 EO 3461 numbered targets with incumbent-savings qualifications.</p><div class="note"><b>Scientific limit:</b> The 120-case probability sample has no independent completed outcomes. The statistical estimator explicitly refuses national survival and competing-risk estimates. The present coverage bar is a research workflow metric, not the national survival proportion.</div><footer>Generated reproducibly from AFTERLIFE_STAGE16_CANONICAL.sqlite. Upstream archives unchanged. All source-based legal conclusions require further independent review before article certification.</footer></main></body></html>'''
(ROOT/'VISUALS/RESEARCH_DASHBOARD_STAGE16.html').write_text(content)
print('saved',png, 'dashboard',len(content))
