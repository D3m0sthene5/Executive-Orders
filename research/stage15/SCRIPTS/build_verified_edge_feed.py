"""Export only chronologically sensible, nonquarantined candidate edges.
Requires Stage14 graph and Stage15 sidecar; candidate legal edges still need review.
"""
import csv,json,sqlite3,sys,os
from pathlib import Path
G=Path(os.environ.get('EO_STAGE14_GRAPH','/mnt/data/eo_stage15_workspace/EO_STAGE14_LEVERAGE_ENGINE_2026-10-16/DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite'))
ROOT=Path(os.environ.get('EO_STAGE15_OUTPUT_DIR','/mnt/data/EO_STAGE15_METHOD_FOUNDATION_2026-10-16'))
S=ROOT/'AUDIT/EO_STAGE15_SCHEMA_AND_RISK_SIDECAR.sqlite'
OUT=ROOT/'AUDIT'
source=sqlite3.connect(G);side=sqlite3.connect(S)
blocked={r[0] for r in side.execute('select edge_id from directed_event_guard where stage15_suppress=1')}
rs=source.execute('select edge_id,actor,predecessor,relation,source_url,asof,statement from relationships').fetchall()
kept=[r for r in rs if r[0] not in blocked]
with (OUT/'STAGE15_CHRONOLOGY_GATED_CANDIDATE_RELATIONS.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['edge_id','actor','candidate_predecessor','relation','source_url','source_asof_not_event_date','statement_excerpt','legal_proof_state']);
 for r in kept:w.writerow([*r[:6],r[6][:320] if r[6] else '', 'CANDIDATE_NOT_ADJUDICATED'])
metrics={'upstream_candidate_edges':len(rs),'quarantined_after_stage15':len(blocked),'candidate_edges_passing_stage15_gate':len(kept),'stage15_newly_quarantined_edges':len(blocked)-sum(source.execute('select quarantined from relationships where edge_id=?',(i,)).fetchone()[0] for i in blocked),'no_status_proposals':True}
(OUT/'STAGE15_SAFE_EDGE_FEED_METRICS.json').write_text(json.dumps(metrics,indent=2)+'\n');print(metrics)
