"""Clause-specific research obligations and resumable source-blocked work.

Preparation only: these records never establish legal endings or replace the
claim gate. A relevant evidence/route change reopens a blocked investigation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def clause_features(text):
    patterns = {
        'deadline': r'\b(?:within\s+(?:\d+|thirty|sixty|ninety)|(?:not|no)\s+later\s+than|on\s+or\s+before)\b',
        'performance_command': r'\b(?:shall|must|direct(?:ed)?\s+to)\b.{0,250}\b(?:submit|deliver|issue|review|prepare|complete|provide\s+(?:a|the)\s+report|report\s+to)\b',
        'actual_performance_lead': r'\b(?:submitted|delivered|completed|transmitted|issued)\b',
        'recurring_duty': r'\b(?:annually|annual\s+reports?|periodically|each\s+(?:year|month|quarter)|from\s+time\s+to\s+time|on\s+a\s+continuing\s+basis)\b',
        'fixed_sunset': r'\b(?:terminate|expire|cease|sunset)(?:s|d)?\b.{0,150}\b(?:on|after|at|\d{4})\b',
        'contingent_end': r'\b(?:until|upon\s+(?:completion|submission|delivery|approval)|unless)\b',
        'extension': r'\b(?:extend(?:ed|s)?|further\s+exempt|continue(?:d|s)?\s+in\s+effect)\b',
        'renewal': r'\b(?:renew(?:ed|s|al)?|reestablish(?:ed|es)?)\b',
        'savings_or_residual': r'\b(?:shall\s+not\s+affect|shall\s+remain\s+in\s+(?:force|effect)|rights\s+accrued|pending\s+(?:proceedings|actions)|until\s+(?:modified|revoked|superseded))\b',
    }
    return [kind for kind, pattern in patterns.items() if re.search(pattern, text, re.I | re.S)]


def obligations(instrument_id, clauses, terms, acts):
    ending = [a for a in acts if a.get('verb') in
              {'revoke', 'supersede', 'terminate', 'abolish', 'rescind', 'nullify'}]
    out = []
    for clause in clauses:
        scope = clause.get('scope_id')
        own = [t for t in terms if t.get('scope_id') == scope]
        features = sorted(set(clause_features(clause.get('text', ''))) | {t['kind'] for t in own})
        questions = ['Determine the first cessation or current predicate for this scope; check independent commands and surviving effects.']
        if ending:
            questions.append('Investigate cessation before the later revocation/ending instrument; locating that instrument does not establish the first end.')
        if set(features) & {'deadline', 'report_deadline', 'performance_command', 'actual_performance_lead'}:
            questions.append('Distinguish the due date, demonstrated performance, and continuing duties. Establish occurrence from evidence and explain its effect on this clause.')
        if set(features) & {'fixed_sunset', 'fixed_term', 'sunset_date', 'contingent_end', 'until_event', 'extension', 'renewal'}:
            questions.append('Confirm the relevant event or operative sunset, scope, extensions and renewals; a detected date remains a candidate.')
        if 'recurring_duty' in features:
            questions.append('A completed installment does not establish cessation of the recurring duty; examine remaining installments and later law.')
        out.append({'schema':'eo-lifecycle-obligation/v1', 'instrument_id':instrument_id,
            'scope_id':scope, 'clause_sha256':hashlib.sha256(clause.get('text', '').encode()).hexdigest(),
            'wording_features':features, 'own_term_evidence_ids':[t.get('id') for t in own],
            'later_actor_evidence_ids':[a.get('id') for a in ending],
            'state':'requires_clause_specific_research', 'questions':questions,
            'established_ending':None, 'human_certified':False})
    return out


def material_source_results(value):
    """Retry timing alone is not new evidence; hashes, status and failures are."""
    transient = {'retrieved_utc','attempted_utc','fetched_utc','retrieved_at','accessed_on','time_utc',
                 'elapsed_seconds','duration_seconds','wall_seconds','retry_count','carried_forward'}
    if isinstance(value, dict):
        return {k:material_source_results(v) for k,v in value.items() if k not in transient}
    if isinstance(value, list):return [material_source_results(v) for v in value]
    return value


def work_fingerprint(dossier, requests, route_fingerprint, source_results=None, prior_research=None):
    if not isinstance(route_fingerprint, str) or not re.fullmatch(r'[0-9a-f]{64}', route_fingerprint):
        raise ValueError('route_fingerprint must be a SHA-256 of relevant route code/configuration')
    # Never trust a stale embedded fingerprint to hide changed evidence.
    return digest({'dossier_content':{k:v for k,v in dossier.items() if k!='fingerprint'},
                   'source_requests':requests, 'route_fingerprint':route_fingerprint,
                   'source_results':material_source_results(source_results or []),
                   'prior_research':prior_research})


def blocked_checkpoint(dossier, requests, route_fingerprint, reason, result_paths, source_results=None, prior_research=None):
    if not reason or not requests or not result_paths:
        raise ValueError('blocked attempt needs a reason, unresolved requests and preserved result paths')
    return {'schema':'eo-source-blocked-work/v1', 'instrument_id':dossier['instrument_id'],
        'state':'source_blocked', 'reason':reason, 'source_requests':requests,
        'result_paths':result_paths, 'route_fingerprint':route_fingerprint,
        'source_results':material_source_results(source_results or []),
        'input_fingerprint':work_fingerprint(dossier, requests, route_fingerprint, source_results, prior_research)}


def resume_decision(checkpoint, dossier, requests, route_fingerprint, source_results=None, prior_research=None):
    if checkpoint.get('schema') != 'eo-source-blocked-work/v1' or checkpoint.get('state') != 'source_blocked':
        raise ValueError('only a recorded source-blocked attempt can be deferred')
    if checkpoint.get('instrument_id') != dossier.get('instrument_id'):
        raise ValueError('checkpoint belongs to another order')
    current = work_fingerprint(dossier, requests, route_fingerprint, source_results, prior_research)
    changed = current != checkpoint.get('input_fingerprint')
    return {'instrument_id':dossier['instrument_id'],
        'action':'reopen' if changed else 'defer_unchanged_source_block',
        'reason':'Relevant evidence/request/route/prior research changed.' if changed else 'No relevant input changed; retain the unsuccessful attempt and wait for evidence.',
        'previous_input_fingerprint':checkpoint.get('input_fingerprint'), 'input_fingerprint':current,
        'result_paths':checkpoint.get('result_paths', []), 'legal_conclusion':None}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['checkpoint', 'resume'])
    p.add_argument('--dossier', type=Path, required=True)
    p.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument('--requests', type=Path, required=True, help='JSON array of validated unresolved requests')
    p.add_argument('--source-results', type=Path, help='JSON array of relevant source receipts, including new acquisitions before corpus rebuild')
    p.add_argument('--routes-sha256', required=True)
    p.add_argument('--checkpoint', type=Path)
    p.add_argument('--reason')
    p.add_argument('--result', action='append', default=[])
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(argv)
    dossier = json.loads(a.dossier.read_text())
    requests = json.loads(a.requests.read_text())
    source_results = json.loads(a.source_results.read_text()) if a.source_results else []
    if not isinstance(requests, list): p.error('--requests must contain a JSON array')
    if not isinstance(source_results, list): p.error('--source-results must contain a JSON array')
    from prior_research import collect
    prior = collect(a.repo, {dossier['instrument_id']: dossier}, exclude=[a.out, a.checkpoint])
    if a.command == 'checkpoint':
        result = blocked_checkpoint(dossier, requests, a.routes_sha256, a.reason, a.result, source_results, prior)
    else:
        if not a.checkpoint: p.error('resume requires --checkpoint')
        result = resume_decision(json.loads(a.checkpoint.read_text()), dossier, requests, a.routes_sha256, source_results, prior)
    result['prior_research'] = prior
    if a.out.exists(): p.error('use a new result path; previous attempts are retained')
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__': raise SystemExit(main())
