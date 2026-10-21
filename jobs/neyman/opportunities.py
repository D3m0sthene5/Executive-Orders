"""Sanitized counts for Junto, never workload estimates masquerading as savings."""
from collections import Counter
from survey import write


def aggregate(manifest,rows,uncertainty,out):
    result={'schema':'neyman.aggregate/1','manifest_sha256':manifest['manifest_sha256'],
            'frame_population':len(rows),'attempts':uncertainty['attempts'],
            'outcomes':uncertainty['outcomes'],'blocker_counts':dict(Counter(b.split(':')[0] for r in rows for b in r['blockers'])),
            'shared_events':uncertainty['shared_events_counted_once'],
            'active_phase_coverage':uncertainty['active_phase_coverage'],
            'api_token_valuation_usd':None,'actual_cash_expenditure_usd':None}
    write(out,result);return result
