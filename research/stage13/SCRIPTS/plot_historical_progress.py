"""Produce two clearly separate historical issuance charts from Stage13 date-reference overlay."""
import csv,sys,pathlib,collections,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p,out=sys.argv[1:];out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader(open(p,newline='')))
rows=[r for r in rows if r['decade']!='UNKNOWN_DATE']
xs=[int(r['decade'][:-1]) for r in rows]
orig=[sum(int(r['stage12_signed_date_projection_'+st]) for st in ('yes','no','indeterminate')) for r in rows]
editorial=[sum(int(r['NARA_1989_EDITORIAL_DATE_REFERENCE_ONLY_'+st]) for st in ('yes','no','indeterminate')) for r in rows]
decided=[int(r['determined']) for r in rows]
unknown=[int(r['total'])-int(r['determined']) for r in rows]
assert sum(orig)==14854 and sum(editorial)==18 and sum(decided)==2514 # one determined among 100 still-undated identities
fig,ax=plt.subplots(figsize=(17,6.5))
ax.bar(xs,decided, width=8,label='Substantive status determined (Stage 11)',align='center')
ax.bar(xs,unknown,width=8,bottom=decided,label='Substantive status unknown',align='center')
# Dates are part of the status stack already. A dot shows separate provenance without double-counting orders.
for x,ed,tot in zip(xs,editorial,orig):
 if ed:ax.scatter(x,tot+ed+20,marker='d',s=38,zorder=6,label='NARA editorial dates (already included; no extra orders)' if x==min([xx for xx,e in zip(xs,editorial) if e]) else None)
ax.set_xlim(1782,2037)
ax.set_xticks(list(range(1790,2030,10)));ax.tick_params(axis="x",labelrotation=55)
ax.set_ylabel('Number of currently catalogued order identities (not national universe)')
ax.set_xlabel('Signing decade where available; 18 NARA-source dates are provisional')
ax.set_title('Executive-order status research across issuance decades — Stage 13')
ax.legend(loc='upper left',frameon=False)
ax.text(1800,max(a+b for a,b in zip(decided,unknown))*.73,'1789–1861 largely absent\n3 NARA bibliographic date references;\nnot a complete census',fontsize=10)
ax.grid(axis='y',alpha=.15)
fig.tight_layout();fig.savefig(out/'HISTORICAL_ISSUANCE_STATUS_STAGE13.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(figsize=(17,5.3))
proportions=[100*int(r['determined'])/int(r['total']) if int(r['total']) else 0 for r in rows]
ax.bar(xs,proportions,width=8)
ax.set_xlim(1782,2037);ax.set_ylim(0,100)
ax.set_xticks(list(range(1790,2030,10)));ax.tick_params(axis="x",labelrotation=55)
ax.set_xlabel('Decade of available issue/date reference')
ax.set_ylabel('Fraction substantively YES/NO classified within available bibliography (%)')
ax.set_title('Coverage by decade — classified identity fraction, not survival rate')
ax.grid(axis='y',alpha=.15)
fig.tight_layout();fig.savefig(out/'DECENNIAL_CLASSIFICATION_COVERAGE_STAGE13.png',dpi=150);plt.close(fig)
print('generated',out)
