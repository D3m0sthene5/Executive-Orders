"""Design-weighted analyses permitted only after complete blind source review.

This module intentionally refuses national survival/causal estimates from status-selected
cases, partial reviewed samples, unknown operative states, and missing denominators.
"""
import sqlite3,sys
from pathlib import Path
class ScientificInferenceUnavailable(Exception):pass

def probability_sample_estimate(db, outcome='normative_survives'):
    c=sqlite3.connect(str(db))
    rows=c.execute('SELECT id,design_weight,review_state,independent_verdict FROM probability_sample').fetchall()
    n=len(rows)
    if n!=120:raise ScientificInferenceUnavailable('Sampling frame is incomplete or unrecognized; refused')
    incomplete=[r for r in rows if r[2]!='REVIEWED' or r[3] not in ('yes','no')]
    if incomplete:raise ScientificInferenceUnavailable(f'REFUSED: {len(incomplete)} of {n} probability-sampled cases have no independently adjudicated binary legal effect outcome; no national estimate')
    total=sum(r[1] for r in rows)
    estimate=sum(r[1] for r in rows if r[3]=='yes')/total
    # Exact design uncertainty requires probability design info including covariance for stratified sampling;
    # do not report misleading binomial standard error here.
    return {'estimate':estimate,'weighted_frame_size':total,'n':n,'design_uncertainty_status':'needs per-stratum finite-population variance calculation'}

def competing_risk_survival(db):
    raise ScientificInferenceUnavailable('REFUSED: No probability sample has sufficiently dated, independently reviewed operative episodes and first causes; no survival/competing-risk curve')

if __name__=='__main__':
    try:print(probability_sample_estimate(sys.argv[1]))
    except ScientificInferenceUnavailable as e:print(str(e))
