"""Small realistic claims for Tiro's plant tests: held text files with PDF page marks, base64url evidence ids, one
YES claim (continuation notices, an amendment, a clause revoked by another order) and one NO claim (every clause
superseded by another order). Test support only."""
import base64
import hashlib
import json
from pathlib import Path

ORIG = ("=== PDF page 1 of 2 ===\nSection 1. The Secretary shall block the property of the persons listed.\n"
        "Sec. 2. Executive Order 11111 is hereby amended by adding a new section.\n"
        "=== PDF page 2 of 2 ===\nSec. 3. This order is effective immediately.\n")
REVOKER = "=== PDF page 1 of 1 ===\nSection 1. Section 2 of Executive Order 12345 is hereby revoked.\n"
AMENDER = "=== PDF page 1 of 1 ===\nSection 1. Section 1 of Executive Order 12345 is amended to read as follows.\n"
NOTICE = "Continuation of the National Emergency declared in Executive Order 12345, notice of {y}.\n"
SUPERSEDER = "=== PDF page 1 of 1 ===\nSec. 4. Executive Order 12346 is superseded.\n"
OLD = ("=== PDF page 1 of 1 ===\nSection 1. The Board shall meet monthly.\nSec. 2. The Board shall report annually.\n")


def _b64(s):
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')


def _sha(t):
    return hashlib.sha256(t.encode()).hexdigest()


class Texts:
    def __init__(self, repo):
        self.repo = Path(repo)
        self.files = {}

    def add(self, name, text):
        p = self.repo / 'held' / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
        self.files[name] = text

    def src(self, name, needle, evidence, page, signing=None, url=None):
        text = self.files[name]
        a = text.index(needle)
        return {'char_end': a + len(needle), 'char_start': a, 'evidence_id': _b64(evidence),
                'evidence_id_encoding': 'base64url-utf8', 'page_or_item': page, 'quote': needle,
                'sha256': _sha(text), 'signing_date': signing, 'text_path': f'held/{name}', 'text_sha256': _sha(text),
                'url': url or f'https://www.govinfo.gov/{name}.pdf'}


def build(repo):
    """(yes_claim, no_claim) with their held texts written under repo/held/."""
    t = Texts(repo)
    t.add('EO_12345.txt', ORIG)
    t.add('EO_22222.txt', REVOKER)
    t.add('EO_33333.txt', AMENDER)
    for y in (2002, 2003, 2004):
        t.add(f'fr-{y}.txt', NOTICE.format(y=y))
    t.add('EO_12346.txt', OLD)
    t.add('EO_22223.txt', SUPERSEDER)
    sig = '2001-02-03'
    rep = t.src('EO_12345.txt', 'Section 1. The Secretary', 'ORIGINAL:EO:12345', '66 FR 1, PDF pages 1-2', sig)
    s1 = t.src('EO_12345.txt', 'Section 1. The Secretary shall block the property of the persons listed.',
               'CLAUSES:EO:12345#sec1', '66 FR 1, PDF page 1', sig)
    s2 = t.src('EO_12345.txt', 'Sec. 2. Executive Order 11111 is hereby amended by adding a new section.',
               'CLAUSES:EO:12345#sec2', '66 FR 1, PDF page 1', sig)
    s3 = t.src('EO_12345.txt', 'Sec. 3. This order is effective immediately.', 'CLAUSES:EO:12345#sec3',
               '66 FR 2, PDF page 2', sig)
    rev = t.src('EO_22222.txt', 'Section 1. Section 2 of Executive Order 12345 is hereby revoked.',
                'ACT:EO:12345>EO:22222', '68 FR 9, PDF page 1')
    amd = t.src('EO_33333.txt', 'Section 1. Section 1 of Executive Order 12345 is amended to read as follows.',
                'ACT:EO:12345>EO:33333', '70 FR 5, PDF page 1')

    def notice(y, d):
        return {'actor': f'FRDOC:{y}-0001', 'effective_date': d, 'mechanism': 'continuation_of_national_emergency_notice',
                'source': t.src(f'fr-{y}.txt', NOTICE.format(y=y).strip(), f'ACTOR_TEXT:FRDOC:{y}-0001',
                                f'{y - 1935} FR 100; FR Doc. {y}-0001')}
    search = [{'checked_on': '2026-11-11', 'query_or_scope': 'every citation of this order by number',
               'repository': 'U.S. Code and eCFR'}]
    yes = {
        'schema': 'eo-lifecycle-claim/v1', 'instrument_id': 'EO:12345', 'whole_order_status': 'yes',
        'claim_kit': {'agent': 'tw', 'dossier_sha256': 'd' * 64, 'producer_approved': True},
        'original_representation': rep,
        'operative_clauses': [
            {'scope_id': 'EO:12345#sec1', 'state_at_cutoff': 'operative', 'original_operative_text': s1['quote'],
             'original_source': s1,
             'current_predicate': {'checked_through': '2026-10-14', 'legal_basis': 'Section 1 continues under the '
                                   'national emergency, continued each year by notice.', 'source': s1},
             'judgment_reason': 'Section 1 blocks property. Executive Order 33333 amended it on May 5, 2005.',
             'later_events': [notice(2002, '2002-01-10'), notice(2003, '2003-01-09'), notice(2004, '2004-01-08'),
                              {'actor': 'EO:33333', 'effective_date': '2005-05-05', 'mechanism': 'amendment',
                               'source': amd}]},
            {'scope_id': 'EO:12345#sec2', 'state_at_cutoff': 'terminated', 'original_operative_text': s2['quote'],
             'original_source': s2,
             'first_end': {'actor': 'EO:22222', 'date': '2003-03-03', 'mechanism': 'express_revocation', 'source': rev},
             'judgment_reason': 'Section 2 was revoked by Executive Order 22222 on March 3, 2003.', 'later_events': []},
            {'scope_id': 'EO:12345#sec3', 'state_at_cutoff': 'operative', 'original_operative_text': s3['quote'],
             'original_source': s3,
             'current_predicate': {'checked_through': '2026-10-14', 'legal_basis': 'The effective-date clause has no '
                                   'end of its own.', 'source': s3},
             'judgment_reason': 'Section 3 sets the effective date.', 'later_events': []}],
        'whole_order_end': None,
        'savings_residuals': {'state': 'none_after_bounded_search', 'reason': 'No savings clause.', 'source': rep},
        'later_source_search': search, 'unresolved_material_gaps': [],
        'research_rationale': ('The order remains in force. The emergency it acts under was continued by three '
                               'continuation notices recorded as later events on section 1, Executive Order 33333 '
                               'amended section 1, and Executive Order 22222 revoked section 2.')}
    osig = '1990-01-01'
    orep = t.src('EO_12346.txt', 'Section 1. The Board', 'ORIGINAL:EO:12346', '55 FR 1, PDF page 1', osig)
    o1 = t.src('EO_12346.txt', 'Section 1. The Board shall meet monthly.', 'CLAUSES:EO:12346#sec1', '55 FR 1, PDF page 1', osig)
    o2 = t.src('EO_12346.txt', 'Sec. 2. The Board shall report annually.', 'CLAUSES:EO:12346#sec2', '55 FR 1, PDF page 1', osig)
    sup = t.src('EO_22223.txt', 'Sec. 4. Executive Order 12346 is superseded.', 'ACT:EO:12346>EO:22223', '60 FR 7, PDF page 1')
    end = {'actor': 'EO:22223', 'date': '1995-05-05', 'mechanism': 'express_supersession', 'source': sup}
    no = {
        'schema': 'eo-lifecycle-claim/v1', 'instrument_id': 'EO:12346', 'whole_order_status': 'no',
        'claim_kit': {'agent': 'tw', 'dossier_sha256': 'e' * 64, 'producer_approved': True},
        'original_representation': orep,
        'operative_clauses': [
            {'scope_id': f'EO:12346#sec{i}', 'state_at_cutoff': 'terminated', 'original_operative_text': o['quote'],
             'original_source': o, 'first_end': json.loads(json.dumps(end)),
             'judgment_reason': f'Section {i} ended when Executive Order 22223 superseded the order on May 5, 1995.',
             'later_events': []} for i, o in ((1, o1), (2, o2))],
        'whole_order_end': json.loads(json.dumps(end)),
        'savings_residuals': {'state': 'none_after_bounded_search', 'reason': 'No savings clause.', 'source': orep},
        'later_source_search': search, 'unresolved_material_gaps': [],
        'research_rationale': 'Executive Order 22223 superseded the whole order on May 5, 1995; no clause survived.'}
    return yes, no
