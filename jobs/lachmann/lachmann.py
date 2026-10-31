"""Lachmann: machine collation of held working texts against the order register.

Karl Lachmann established texts by collating independent witnesses. This module does the
same for each order whose only held text is a compiled transcription or a ProQuest replica
scan: it picks one held representation, applies conservative deterministic tests (right
order, complete text, pages checked) and records a machine confirmation pinned to the exact
fragment. A confirmation is a working-text confirmation under the owner's rulings; it never
authenticates an original (acceptable_as_original is always false).

Offline, standard library only. See README.md.
"""
import csv
import hashlib
import json
import random
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # importing claim-kit must not write into its folder
sys.path.insert(0, str(HERE.parent / 'claim-kit'))
import working_text as W  # noqa: E402  (read-only import; never edited here)

SCHEMA = 'eo-lachmann-confirmation/v1'
RULING = 'research/readiness/owner_rulings/2026-10-31-jacquard-and-working-texts.md'
SCOPE_BLOCKERS = ('ONLY_COMPILED_TRANSCRIPTION_FOUND', 'ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK')
OUT_OF_SCOPE_BLOCKER = 'ORIGINAL_FOUND_NEEDS_PAGE_CHECK'

TRACKER_CSV = 'jobs/readiness-tracker/output/READINESS_BY_ORDER.csv'
REGISTER_CSV = 'jobs/domesday-register/output/REGISTER.csv'
PINAKES_ORDERS = 'jobs/pinakes-proquest-ingest/output/ORDERS.csv'
PINAKES_INVENTORY = 'jobs/pinakes-proquest-ingest/output/INVENTORY.csv'
APP_DOCUMENTS = ('jobs/app-executive-orders/output/DOCUMENTS.jsonl',
                 'jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl')

# Best representation first; ties are broken by the longest text.
GRADE_ORDER = ('government_printed_copy', 'machine_read_government_printed_copy',
               'government_printed_reproduction', 'archival_replica_scan_pending_codebook',
               'compiled_transcription', 'mirror_transcription', 'compiled_transcription_lead')
GRADE_RANK = {g: n for n, g in enumerate(GRADE_ORDER)}

SIM_JACCARD = 0.80
SIM_RATIO = (0.85, 1.15)
TITLE_OVERLAP = 0.6
START_WINDOW = 400
END_WINDOW = 500
PAGE_ONE_WINDOW = 1500
MIN_CUE_FRACTION = 0.3  # a closing cue must sit past this fraction of the text, so an opening dateline never counts
SNIPPET = 80

# ---------------------------------------------------------------------------
# Text preparation

_MARKER = re.compile(r'^-{3,}[ \t]*EXACT[^\n]*?-{3,}[ \t]*$', re.M)
_WIKI_ID_LINE = re.compile(r'^\d{3,}[A-Za-z].*$', re.M)
_WIKI_END = re.compile(r'^(?:See [Rr]elated|Amends|Amended by|Revoked by|Revokes|Superseded by|Supersedes|Related)\s*:?\s*$'
                       r'|^This work is in the public domain', re.M)


def body_of(text):
    """The order text without the producer's own wrapper (comment header, page chrome).

    The wrappers name the instrument (for example "# order: EO:1136"), so they cannot count as evidence.
    """
    m = _MARKER.search(text)
    if m:
        return text[m.end():].strip('\n')
    if 'From Wikisource' in text[:800] and 'Retrieved from "' in text:
        m = _WIKI_ID_LINE.search(text)
        if m:
            rest = text[m.end():]
            end = _WIKI_END.search(rest)
            return (rest[:end.start()] if end else rest).strip()
    lines = text.split('\n')
    i = 0
    while i < len(lines) and (lines[i].startswith('#') or not lines[i].strip()):
        i += 1
    return '\n'.join(lines[i:]).strip('\n') if i and lines[0].startswith('#') else text


_STOP = frozenset('''a about above after again against all also am an and any are as at be because been before being below
between both but by can could did do does doing down during each executive few for from further had has have having he her here
hers him his how i if in into is it its itself just me more most my no nor not now of off on once only or other our out over own
same she should so some such than that the their them then there these they this those through to too under until up upon very
was we were what when where which while who whom why will with would you your order orders relating regarding concerning
amending amendment amended establishing providing president united states'''.split())
_WORD = re.compile(r'[a-z0-9]+')


def norm_words(text):
    """Lowercase words with punctuation stripped (whitespace collapses by construction)."""
    return _WORD.findall(text.lower())


def trigrams(words):
    if len(words) < 3:
        return {tuple(words)} if words else set()
    return {tuple(words[i:i + 3]) for i in range(len(words) - 2)}


def similarity(text_a, text_b):
    """Word 3-gram Jaccard and normalized-length ratio (shorter over longer is not used: a over b)."""
    wa, wb = norm_words(text_a), norm_words(text_b)
    ga, gb = trigrams(wa), trigrams(wb)
    union = ga | gb
    jaccard = len(ga & gb) / len(union) if union else 0.0
    la, lb = len(' '.join(wa)), len(' '.join(wb))
    ratio = la / lb if lb else 0.0
    agree = jaccard >= SIM_JACCARD and SIM_RATIO[0] <= ratio <= SIM_RATIO[1]
    return {'jaccard': round(jaccard, 4), 'length_ratio': round(ratio, 4), 'agrees': agree}


def title_words(title):
    t = re.sub(r'^\s*(?:executive\s+order|order)\s*(?:no\.?)?\s*[0-9A-Za-z-]*\s*[—–\-:]*\s*', '', title or '', flags=re.I)
    return {w for w in _WORD.findall(t.lower()) if len(w) > 2 and w not in _STOP}


def title_overlap(title, text):
    words = title_words(title)
    if not words:
        return None
    have = set(norm_words(text))
    return round(len(words & have) / len(words), 4)


# ---------------------------------------------------------------------------
# Order numbers

_LOOK = str.maketrans({'O': '0', 'o': '0', 'I': '1', 'l': '1', '|': '1', 'i': '1', 'S': '5', 's': '5', 'B': '8', 'Z': '2'})
_TOK = r'[0-9OoIl|SsBZ]{1,6}'
_NUMBER = re.compile(
    r'(?<![A-Za-z0-9])(?:Executive\s+Order(?:\s+(?:No\.?|Number))?|Exec\.\s*Order(?:\s+No\.?)?|E\.\s?O\.(?:\s*No\.?)?'
    r'|Order\s+(?:No\.?|Number)|No\.|Number)\s*[:#]?\s*(?P<tok>' + _TOK + r')'
    r'(?:\s?-?\s?(?P<suf>(?-i:[A-Z]))(?![A-Za-z]))?(?![0-9A-Za-z])', re.I)


def _token_value(tok):
    """Unify OCR digit look-alikes inside a number token; None when it is not mostly digits."""
    digits = sum(c.isdigit() for c in tok)
    if digits == 0 or digits < (len(tok) + 1) // 2:
        return None
    return tok.translate(_LOOK)


def suffix_letter(suffix):
    s = (suffix or '').strip().lstrip('-')
    return s.upper() if s.isalpha() else ''


def number_matches(text, number, suffix=''):
    """(matched string, offset) for every place the text names this executive-order number.

    A letter suffix in the register (6945-A) must be present in the text; an order without one
    does not match a suffixed number of the same digits. Numeric suffixes such as -1 are register
    disambiguators that no printed order carries, so only the digits are required.
    """
    want = str(number).lstrip('0') or '0'
    letter = suffix_letter(suffix)
    found = []
    for m in _NUMBER.finditer(text):
        val = _token_value(m.group('tok'))
        if val is None or (val.lstrip('0') or '0') != want:
            continue
        got = (m.group('suf') or '').upper()
        if got != letter:
            continue
        found.append((re.sub(r'\s+', ' ', m.group(0)).strip()[:SNIPPET], m.start()))
    return found


# ---------------------------------------------------------------------------
# Dates

_MONTHS = ('january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october',
           'november', 'december')
_MON = r'(?P<mon>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
_D = r'(?P<d>[0-9OoIl]{1,2})(?:st|nd|rd|th)?'
_Y = r'(?P<y>[12OoIl][0-9OoIl]{3})'
_DATE_FORMS = (
    re.compile(r'(?<![A-Za-z])' + _MON + r'\.?\s*' + _D + r'\s*,?\s*' + _Y + r'(?![0-9])', re.I),
    re.compile(r'(?<![0-9A-Za-z])' + _D + r'(?:\s+day)?(?:\s+of)?\s+' + _MON + r'\.?\s*,?\s*' + _Y + r'(?![0-9])', re.I),
)
_ISO = re.compile(r'(?<![0-9])(?P<y>[12]\d{3})-(?P<mo>\d{2})-(?P<d>\d{2})(?![0-9])')
_SLASH = re.compile(r'(?<![0-9])(?P<mo>\d{1,2})/(?P<d>\d{1,2})/(?P<y>[12]\d{3})(?![0-9])')


def _num(tok):
    s = tok.translate(_LOOK)
    return int(s) if s.isdigit() else None


def _month(name):
    n = name.lower()
    for i, full in enumerate(_MONTHS, 1):
        if full.startswith(n[:3]) and (full.startswith(n) or n == 'sept'):
            return i
    return None


def parse_register_date(value):
    """('full', (y, m, d)) | ('partial', None) | ('missing', None)."""
    v = (value or '').strip()
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', v)
    if m:
        return 'full', tuple(int(x) for x in m.groups())
    return ('partial', None) if v else ('missing', None)


def date_matches(text, ymd):
    """(matched string, offset) for each occurrence of this full date in a common written form."""
    y, mo, d = ymd
    found = []
    for rx in _DATE_FORMS:
        for m in rx.finditer(text):
            if _month(m.group('mon')) == mo and _num(m.group('d')) == d and _num(m.group('y')) == y:
                found.append((re.sub(r'\s+', ' ', m.group(0)).strip()[:SNIPPET], m.start()))
    for m in _ISO.finditer(text):
        if (int(m.group('y')), int(m.group('mo')), int(m.group('d'))) == (y, mo, d):
            found.append((m.group(0), m.start()))
    for m in _SLASH.finditer(text):
        if (int(m.group('y')), int(m.group('mo')), int(m.group('d'))) == (y, mo, d):
            found.append((m.group(0), m.start()))
    return sorted(found, key=lambda x: x[1])


_ANY_DATE = re.compile(_MON + r'\.?\s*[0-9OoIl]{1,2}(?:st|nd|rd|th)?\s*,?\s*[12OoIl][0-9OoIl]{3}', re.I)

# ---------------------------------------------------------------------------
# Start and end of an order

_PRESIDENTS = (
    ('abraham', 'lincoln'), ('andrew', 'johnson'), ('ulysses', 'grant'), ('rutherford', 'hayes'), ('james', 'garfield'),
    ('chester', 'arthur'), ('grover', 'cleveland'), ('benjamin', 'harrison'), ('william', 'mckinley'),
    ('theodore', 'roosevelt'), ('william', 'taft'), ('woodrow', 'wilson'), ('warren', 'harding'),
    ('calvin', 'coolidge'), ('herbert', 'hoover'), ('franklin', 'roosevelt'), ('harry', 'truman'),
    ('dwight', 'eisenhower'), ('john', 'kennedy'), ('lyndon', 'johnson'), ('richard', 'nixon'), ('gerald', 'ford'),
    ('jimmy', 'carter'), ('ronald', 'reagan'), ('george', 'bush'), ('william', 'clinton'), ('bill', 'clinton'),
    ('barack', 'obama'), ('donald', 'trump'), ('joseph', 'biden'), ('andrew', 'jackson'), ('martin', 'buren'),
    ('john', 'tyler'), ('james', 'polk'), ('zachary', 'taylor'), ('millard', 'fillmore'), ('franklin', 'pierce'),
    ('james', 'buchanan'), ('james', 'monroe'), ('james', 'madison'), ('thomas', 'jefferson'), ('john', 'adams'),
    ('george', 'washington'))
_SURNAMES = {s for _, s in _PRESIDENTS}


def is_signature(line):
    """A short line that is a president's name: surname plus a first name or an initial."""
    if len(line) > 60:
        return False
    words = re.sub(r'[^A-Za-z. ]', ' ', line).lower().replace('.', ' ').split()
    if not words or len(words) > 7:
        return False
    for first, sur in _PRESIDENTS:
        if sur in words and (first in words or any(len(w) == 1 for w in words)):
            return True
    return False


def _date_line(line):
    return len(line) <= 70 and bool(_ANY_DATE.search(line) or _ISO.search(line))


def closing_cues(text):
    """Every closing cue as (offset, kind, line): president's name, THE WHITE HOUSE, or a short dated line."""
    cues, pos = [], 0
    for raw in text.split('\n'):
        line = raw.strip()
        if line:
            low = line.lower()
            if re.match(r'^\W*the\s+white\s+house\b', low):
                cues.append((pos, 'white_house', line))
            elif is_signature(line):
                cues.append((pos, 'signature', line))
            elif _date_line(line):
                cues.append((pos, 'dated_line', line))
        pos += len(raw) + 1
    return cues


_HEADING = re.compile(
    r'^\W{0,3}(?:executive\s+order|exec\.?\s+order|order)\s*(?:no\.?|number)?\s*(?P<tok>' + _TOK + r')'
    r'(?:\s?-?\s?(?P<suf>(?-i:[A-Z]))(?![A-Za-z]))?(?![0-9A-Za-z])', re.I)
# A bare "No. 1234" counts as a heading only when it is the whole line, as in the bracketed [No. 1234] tag.
_BARE_HEADING = re.compile(r'^\W{0,3}no\.\s*(?P<tok>' + _TOK + r')(?:\s?-?\s?(?P<suf>(?-i:[A-Z]))(?![A-Za-z]))?\s*[\]\)}]?\W{0,3}$', re.I)


def other_headings(text, number, suffix=''):
    """Offsets of lines that head an order with a different number (or a different letter suffix)."""
    want = str(number).lstrip('0') or '0'
    letter = suffix_letter(suffix)
    out, pos = [], 0
    for raw in text.split('\n'):
        line = raw.strip()
        if line and len(line) <= 160:
            m = _HEADING.match(line) or _BARE_HEADING.match(line)
            if m:
                val = _token_value(m.group('tok'))
                if val is not None:
                    val = val.lstrip('0') or '0'
                    # One extra trailing digit is OCR reading the closing bracket of the order's own [No. n] tag.
                    same = val == want or (len(val) == len(want) + 1 and val.startswith(want))
                    if not same or (m.group('suf') or '').upper() != letter:
                        out.append((pos, line[:SNIPPET]))
        pos += len(raw) + 1
    return out


_OPENING = re.compile(r'executive\s+(?:order|mansion|chamber)|by\s+virtue\s+of|it\s+is\s+hereby\s+ordered|whereas|'
                      r'the\s+white\s+house|by\s+the\s+president|^\W*order\b|department\s+of|regulations?|rules?\b|'
                      r'amendment|hereby', re.I | re.M)


def start_test(text, order):
    """(passes, evidence). The text must open with this order, not a fragment of it or of another."""
    head = text[:START_WINDOW]
    ev = {}
    if order['number']:
        nm = number_matches(head, order['number'], order['suffix'])
        if nm:
            ev.update(start_kind='number_heading', start_snippet=head[max(0, nm[0][1] - 10):nm[0][1] + 70].strip().replace('\n', ' ')[:SNIPPET])
            return True, ev
        if order['ymd'] and date_matches(head, order['ymd']):
            ev.update(start_kind='dateline', start_snippet=head[:SNIPPET].replace('\n', ' '))
            return True, ev
        ov = title_overlap(order['title'], head)
        if ov is not None and ov >= TITLE_OVERLAP:
            ev.update(start_kind='title_words', start_snippet=head[:SNIPPET].replace('\n', ' '))
            return True, ev
        ev['start_snippet'] = head[:SNIPPET].replace('\n', ' ')
        return False, ev
    if _OPENING.search(head) or (order['ymd'] and date_matches(head, order['ymd'])):
        ev.update(start_kind='recognizable_opening', start_snippet=head[:SNIPPET].replace('\n', ' '))
        return True, ev
    ev['start_snippet'] = head[:SNIPPET].replace('\n', ' ')
    return False, ev


def end_test(text, order):
    """(passes, reason, evidence): closing cue in the last 500 characters and no other order after it."""
    stripped = text.rstrip()
    n = len(stripped)
    tail_start = max(0, n - END_WINDOW)
    floor = MIN_CUE_FRACTION * n
    cues = closing_cues(stripped)
    ev = {'end_snippet': stripped[-SNIPPET:].replace('\n', ' ')}
    tail = [c for c in cues if c[0] >= tail_start and c[0] >= floor]
    if not tail:
        return False, 'no_closing_cue', ev
    cue = tail[0]
    ev.update(end_cue_kind=cue[1], end_cue_snippet=cue[2][:SNIPPET])
    anchors = [cue[0]] + [c[0] for c in cues if c[1] in ('signature', 'white_house')]
    after = min(anchors)
    runs = [h for h in other_headings(stripped, order['number'], order['suffix']) if h[0] > after]
    if runs:
        ev['next_heading_snippet'] = runs[0][1]
        return False, 'runs_into_other_order', ev
    return True, None, ev


# ---------------------------------------------------------------------------
# Data loading

def read_csv(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return list(csv.DictReader(fh))


def load_scope(repo):
    """Tracker rows with the original-text step open for a compiled-transcription or replica-only blocker."""
    rows = read_csv(Path(repo) / TRACKER_CSV)
    scope = OrderedDict()
    for r in rows:
        blockers = [b for b in (r.get('blockers') or '').split('|') if b]
        if r.get('step_original_text') != 'open' or OUT_OF_SCOPE_BLOCKER in blockers:
            continue
        mine = [b for b in blockers if b in SCOPE_BLOCKERS]
        if mine:
            scope[r['instrument_id']] = mine
    return OrderedDict(sorted(scope.items()))


def load_register(repo):
    reg = {}
    for r in read_csv(Path(repo) / REGISTER_CSV):
        number = (r.get('number') or '').strip()
        kind, ymd = parse_register_date(r.get('date'))
        reg[r['instrument_id']] = {'instrument_id': r['instrument_id'], 'number': number, 'suffix': (r.get('suffix') or '').strip(),
                                   'date': (r.get('date') or '').strip(), 'date_kind': kind, 'ymd': ymd,
                                   'title': (r.get('title') or '').strip()}
    return reg


class Pinakes:
    def __init__(self, repo):
        self.orders, self.inventory = {}, defaultdict(list)
        p = Path(repo) / PINAKES_ORDERS
        if p.is_file():
            for r in read_csv(p):
                self.orders[r['instrument_id']] = r
        p = Path(repo) / PINAKES_INVENTORY
        if p.is_file():
            for r in read_csv(p):
                self.inventory[r['instrument_id']].append(r)


def load_app_documents(repo):
    by_sha = defaultdict(list)
    for rel in APP_DOCUMENTS:
        p = Path(repo) / rel
        if not p.is_file():
            continue
        with p.open(encoding='utf-8') as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict) and isinstance(row.get('sha256'), str):
                    by_sha[row['sha256']].append(row)
    return by_sha


def load_producers(repo, records):
    """(instrument_id, sha256, text_sha256) -> produced_by, from the declaration rows themselves."""
    wanted = {r['declaration_path'] for r in records}
    out = {}
    for rel in sorted(wanted):
        with (Path(repo) / rel).open(encoding='utf-8') as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(row, dict) or row.get('kind') != 'original_representation':
                    continue
                d = row.get('data') if isinstance(row.get('data'), dict) else {}
                out[(row.get('instrument_id'), d.get('sha256'), d.get('text_sha256'))] = row.get('produced_by') or rel.split('/')[1]
    return out


def collect_witnesses(repo, index, ids, producers, skipped):
    """Held witnesses per order. A witness whose bytes do not hash to its declared text_sha256 is skipped and counted."""
    by_order = defaultdict(list)
    want = set(ids)
    for recs in index.by_sha.values():
        for rec in recs:
            if rec['instrument_id'] in want:
                by_order[rec['instrument_id']].append(rec)
    held = {}
    for iid in sorted(by_order):
        seen, ws = set(), []
        for rec in sorted(by_order[iid], key=lambda r: (r['grade'] or '', r['sha256'], r['text_path'], r['declaration_path'])):
            ident = (rec['grade'], rec['sha256'], rec['text_sha256'], rec['text_path'])
            if ident in seen:
                continue
            seen.add(ident)
            if rec['grade'] not in W.GRADES:
                skipped.append({'instrument_id': iid, 'text_path': rec['text_path'], 'grade': rec['grade'], 'why': 'grade_not_in_working_text_policy'})
                continue
            path = Path(repo) / rec['text_path']
            try:
                raw = path.read_bytes()
            except OSError:
                skipped.append({'instrument_id': iid, 'text_path': rec['text_path'], 'grade': rec['grade'], 'why': 'text_file_missing'})
                continue
            if not isinstance(rec.get('text_sha256'), str) or hashlib.sha256(raw).hexdigest() != rec['text_sha256']:
                skipped.append({'instrument_id': iid, 'text_path': rec['text_path'], 'grade': rec['grade'], 'why': 'text_hash_mismatch'})
                continue
            try:
                text = raw.decode('utf-8')
            except UnicodeError:
                skipped.append({'instrument_id': iid, 'text_path': rec['text_path'], 'grade': rec['grade'], 'why': 'text_not_utf8'})
                continue
            ws.append(make_witness(rec, text, producers.get((iid, rec['sha256'], rec['text_sha256']))
                                   or rec['declaration_path'].split('/')[1]))
        held[iid] = ws
    return held


def make_witness(rec, text, producer):
    return {'rec': rec, 'producer': producer, 'grade': rec['grade'], 'sha256': rec['sha256'], 'text_sha256': rec['text_sha256'],
            'text_path': rec['text_path'], 'text': text, 'body': body_of(text)}


def pick_chosen(witnesses):
    return sorted(witnesses, key=lambda w: (GRADE_RANK.get(w['grade'], 99), -len(w['body']), w['producer'], w['sha256'], w['text_path']))[0]


def independent(a, b):
    return (a['sha256'] != b['sha256'] and a['producer'] != b['producer'] and a['text_sha256'] != b['text_sha256'])


# ---------------------------------------------------------------------------
# The three tests

def identity_test(order, chosen, others):
    """(confirmed, route, reasons, evidence). others are (witness, similarity) for independent witnesses."""
    ev, reasons = {}, []
    numbered = bool(order['number'])
    agreeing = [(w, s) for w, s in others if s['agrees']]
    date_hit = None
    if order['date_kind'] == 'full':
        hits = date_matches(chosen['body'], order['ymd'])
        date_hit = hits[0][0] if hits else None
    if numbered:
        nm = number_matches(chosen['body'], order['number'], order['suffix'])
        ev['matched_number'] = nm[0][0] if nm else None
        ev['matched_date'] = date_hit
        if nm and date_hit:
            return True, 'a_number_and_date', [], ev
        if not nm:
            reasons.append('identity:number_not_in_text')
        if order['date_kind'] != 'full':
            reasons.append('identity:register_date_incomplete' if order['date_kind'] == 'partial' else 'identity:register_date_missing')
        elif not date_hit:
            reasons.append('identity:date_not_in_text')
        for w, s in agreeing:
            wn = number_matches(w['body'], order['number'], order['suffix'])
            wd = date_matches(w['body'], order['ymd']) if order['date_kind'] == 'full' else []
            if wn and wd:
                ev.update(route_witness={'producer': w['producer'], 'grade': w['grade'], 'sha256': w['sha256']},
                          matched_number=wn[0][0], matched_date=wd[0][0])
                return True, 'c_agreeing_witness_with_number_and_date', [], ev
        if others and not agreeing:
            reasons.append('identity:no_independent_witness_agrees')
        elif not others:
            reasons.append('identity:no_second_witness')
        elif agreeing:
            reasons.append('identity:agreeing_witness_lacks_number_and_date')
        return False, None, reasons, ev
    overlap = title_overlap(order['title'], chosen['body'])
    ev.update(matched_number=None, matched_date=date_hit, title_overlap=overlap)
    if not date_hit:
        reasons.append('identity:register_date_incomplete' if order['date_kind'] == 'partial' else
                       'identity:register_date_missing' if order['date_kind'] == 'missing' else 'identity:date_not_in_text')
    if overlap is None or overlap < TITLE_OVERLAP:
        reasons.append('identity:title_overlap_below_0.6')
    if not agreeing:
        reasons.append('identity:no_independent_witness_agrees' if others else 'identity:no_second_witness')
    if not reasons:
        w, s = agreeing[0]
        ev['route_witness'] = {'producer': w['producer'], 'grade': w['grade'], 'sha256': w['sha256']}
        return True, 'b_unnumbered_date_title_and_agreeing_witness', [], ev
    return False, None, reasons, ev


_NUMBERED_ITEM = re.compile(r'^\s*(\d{1,2})\.\s+\S', re.M)
_SECTION = re.compile(r'^\s*(?:sec(?:tion)?\.?|§)\s*(\d{1,2})\b', re.M | re.I)


def numbering_gaps(text):
    """Forward jumps in a numbered sequence (1, 2, 7) show text lost inside the order, e.g. OCR that dropped
    courses of a metes-and-bounds description (EO 5528 in the 2026-10-31 audit). Restarts are allowed."""
    gaps = []
    for pattern, family in ((_NUMBERED_ITEM, 'item'), (_SECTION, 'section')):
        nums = [int(m.group(1)) for m in pattern.finditer(text)]
        if 1 not in nums:
            continue
        prev = None
        for n in nums:
            if prev is not None and n > prev + 1 and n - prev <= 12:
                gaps.append(f'{family}:{prev}->{n}')
            if prev is None or n > prev or n == 1:
                prev = n
    return gaps


def dangling_before_signature(text):
    """The last non-empty line before the first signature line ends mid-list (comma, semicolon, hyphen, or a
    connective), so operative text was lost before the signature (EO 5252 in the 2026-10-31 audit)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if is_signature(line):
            prev = next((l.strip() for l in reversed(lines[:i]) if l.strip()), '')
            return bool(prev) and bool(re.search(r'([,;\-]|\b(and|or|of|the|to|in))\s*$', prev, re.I))
    return False


def complete_test(order, chosen, others):
    """(confirmed, route, reasons, evidence). The chosen text must also be free of numbering gaps and must not
    break off just before the signature."""
    ok, route, reasons, ev = _complete_test(order, chosen, others)
    if dangling_before_signature(chosen['body']):
        ev['dangling_before_signature'] = True
        if ok:
            return False, None, ['complete:dangling_before_signature'], ev
        reasons = reasons + ['complete:dangling_before_signature']
    gaps = numbering_gaps(chosen['body'])
    if gaps:
        ev['numbering_gaps'] = gaps[:5]
        if ok:
            return False, None, ['complete:numbering_gap'], ev
        reasons = reasons + ['complete:numbering_gap']
    return ok, route, reasons, ev


def _complete_test(order, chosen, others):
    """(confirmed, route, reasons, evidence)."""
    ok_s, ev_s = start_test(chosen['body'], order)
    ok_e, why_e, ev_e = end_test(chosen['body'], order)
    ev = dict(ev_s, **ev_e)
    if ok_s and ok_e:
        return True, 'own_start_and_end', [], ev
    for w, s in others:
        if not s['agrees']:
            continue
        ws, _ = start_test(w['body'], order)
        we, _, wev = end_test(w['body'], order)
        if ws and we:
            ev['route_witness'] = {'producer': w['producer'], 'grade': w['grade'], 'sha256': w['sha256']}
            return True, 'agreeing_witness_has_start_and_end', [], ev
    reasons = []
    if not ok_s:
        reasons.append('complete:start_not_found')
    if not ok_e:
        reasons.append('complete:' + why_e)
    return False, None, reasons, ev


def pages_test(order, chosen, pinakes, app_docs, repo):
    """(confirmed, reasons, evidence) for a chosen text whose fragment requires a page check."""
    ev, reasons = {}, []
    producer = chosen['producer']
    if chosen['grade'] == 'archival_replica_scan_pending_codebook' and producer == 'pinakes-proquest-ingest':
        iid = order['instrument_id']
        row = pinakes.orders.get(iid)
        inv = [r for r in pinakes.inventory.get(iid, [])
               if r.get('sha256') == chosen['sha256'] and not r.get('duplicate_of') and not r.get('pdf_error')]
        if not row or row.get('sha256') != chosen['sha256'] or not inv:
            return False, ['pages:not_the_per_order_pinakes_file'], ev
        try:
            pages = int(row.get('pages') or inv[0].get('pages') or 0)
        except ValueError:
            pages = 0
        ev.update(pdf_file=row.get('file'), pages=pages or None, text_source=row.get('text_source'),
                  page_text_available=False)
        if pages <= 0:
            reasons.append('pages:page_count_unknown')
        if not chosen['body'].strip():
            reasons.append('pages:extracted_text_empty')
        if row.get('text_usable') != 'yes':
            reasons.append('pages:text_flagged_low_quality_or_handwritten')
        first = chosen['body'][:PAGE_ONE_WINDOW]
        if order['number']:
            hit = number_matches(first, order['number'], order['suffix'])
            ev['first_page_match'] = hit[0][0] if hit else None
            if not hit:
                reasons.append('pages:number_not_in_first_page_text')
        else:
            hit = date_matches(first, order['ymd']) if order['ymd'] else []
            ev['first_page_match'] = hit[0][0] if hit else None
            if not hit:
                reasons.append('pages:date_not_in_first_page_text')
        return not reasons, reasons, ev
    if producer == 'app-executive-orders':
        rows = [r for r in app_docs.get(chosen['sha256'], []) if r.get('instrument_id') == order['instrument_id']]
        if not rows:
            return False, ['pages:app_page_record_missing'], ev
        row = sorted(rows, key=lambda r: r.get('text_sha256') != chosen['text_sha256'])[0]
        title = row.get('heading') or row.get('listing_title') or ''
        ev.update(app_heading=title[:SNIPPET], app_date=row.get('date'))
        if row.get('text_sha256') != chosen['text_sha256']:
            reasons.append('pages:app_record_text_hash_differs')
        if order['number'] and not number_matches(title, order['number'], order['suffix']):
            reasons.append('pages:app_heading_number_mismatch')
        if order['date_kind'] != 'full' or row.get('date') != order['date']:
            reasons.append('pages:app_date_mismatch')
        ov = title_overlap(title, chosen['body'])
        ev['app_subject_overlap'] = ov
        if ov is None or ov < TITLE_OVERLAP:
            reasons.append('pages:app_subject_not_in_text')
        return not reasons, reasons, ev
    return False, ['pages:no_page_record_rule_for_' + producer], ev


# ---------------------------------------------------------------------------
# Assessment of one order

def assess(order, blockers, witnesses, pinakes, app_docs, repo, index, skipped_here=()):
    iid = order['instrument_id']
    rec_out = OrderedDict([('schema', SCHEMA), ('instrument_id', iid)])
    if not witnesses:
        rec_out.update(grade=None, sha256=None, text_sha256=None, text_path=None, acceptable_as_original=False,
                       requires_page_check=False, identity_confirmed=False, complete_text_confirmed=False,
                       pages_confirmed=None, confirmed=False, method='machine', witnesses=[],
                       evidence={'skipped_witnesses': list(skipped_here)}, reasons=['no_valid_witness'],
                       ruling=RULING, standing_note=W.NOTE)
        return rec_out, None
    chosen = pick_chosen(witnesses)
    others = []
    for w in sorted(witnesses, key=lambda w: (GRADE_RANK.get(w['grade'], 99), w['producer'], w['sha256'])):
        if w is not chosen and independent(chosen, w):
            others.append((w, similarity(chosen['body'], w['body'])))
    requires = any(r['requires_page_check'] for r in index.match(W.confirmation(chosen['rec']))) or chosen['rec']['requires_page_check']
    id_ok, id_route, id_reasons, id_ev = identity_test(order, chosen, others)
    co_ok, co_route, co_reasons, co_ev = complete_test(order, chosen, others)
    if requires:
        pg_ok, pg_reasons, pg_ev = pages_test(order, chosen, pinakes, app_docs, repo)
    else:
        pg_ok, pg_reasons, pg_ev = None, [], {}
    confirmed = bool(id_ok and co_ok and (pg_ok is None or pg_ok))
    ev = OrderedDict()
    ev['identity_route'] = id_route
    ev['complete_route'] = co_route
    ev['matched_number'] = id_ev.pop('matched_number', None)
    ev['matched_date'] = id_ev.pop('matched_date', None)
    ev['register_number'] = (order['number'] + order['suffix']) or None
    ev['register_date'] = order['date'] or None
    ev['similarity'] = [{'producer': w['producer'], 'grade': w['grade'], 'sha256': w['sha256'], 'jaccard': s['jaccard'],
                         'length_ratio': s['length_ratio'], 'agrees': s['agrees']} for w, s in others]
    ev['first_cue_snippet'] = (co_ev.get('start_snippet') or '')[:SNIPPET]
    ev['last_cue_snippet'] = (co_ev.get('end_cue_snippet') or co_ev.get('end_snippet') or '')[:SNIPPET]
    ev['identity_detail'] = id_ev
    ev['complete_detail'] = {k: v for k, v in co_ev.items() if k not in ('start_snippet', 'end_snippet', 'end_cue_snippet')}
    ev['pages_detail'] = pg_ev
    ev['skipped_witnesses'] = list(skipped_here)
    ev['text_chars'] = len(chosen['body'])
    rec = W.confirmation(chosen['rec'])
    rec_out.update(rec)
    rec_out.update(acceptable_as_original=False, requires_page_check=bool(requires), identity_confirmed=id_ok,
                   complete_text_confirmed=co_ok, pages_confirmed=pg_ok, confirmed=confirmed, method='machine',
                   witnesses=[{'producer': w['producer'], 'grade': w['grade'], 'sha256': w['sha256'], 'text_path': w['text_path']}
                              for w in sorted(witnesses, key=lambda w: (GRADE_RANK.get(w['grade'], 99), w['producer'], w['sha256']))],
                   evidence=ev, reasons=[] if confirmed else id_reasons + co_reasons + pg_reasons,
                   ruling=RULING, standing_note=W.NOTE)
    return rec_out, chosen


# ---------------------------------------------------------------------------
# Whole run

def run(repo, out):
    repo, out = Path(repo), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    scope = load_scope(repo)
    register = load_register(repo)
    pinakes = Pinakes(repo)
    app_docs = load_app_documents(repo)
    index = W.Index(repo)
    recs = [r for v in index.by_sha.values() for r in v if r['instrument_id'] in scope]
    producers = load_producers(repo, recs)
    skipped = []
    held = collect_witnesses(repo, index, scope, producers, skipped)
    skipped_by_order = defaultdict(list)
    for s in skipped:
        skipped_by_order[s['instrument_id']].append({k: s[k] for k in ('text_path', 'grade', 'why')})
    results, missing_register = [], []
    for iid, blockers in scope.items():
        order = register.get(iid)
        if order is None:
            missing_register.append(iid)
            continue
        rec, chosen = assess(order, blockers, held.get(iid, []), pinakes, app_docs, repo, index, skipped_by_order.get(iid, []))
        results.append((rec, blockers, order, chosen))
    with (out / 'CONFIRMATIONS.jsonl').open('w', encoding='utf-8', newline='\n') as fh:
        for rec, *_ in results:
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
    with (out / 'RESIDUAL.csv').open('w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, lineterminator='\n')
        w.writerow(['instrument_id', 'blocker', 'chosen_grade', 'chosen_producer', 'text_path', 'register_number', 'register_date',
                    'identity_confirmed', 'complete_text_confirmed', 'pages_confirmed', 'reasons', 'title'])
        for rec, blockers, order, chosen in results:
            if not rec['confirmed']:
                w.writerow([rec['instrument_id'], '+'.join(blockers), rec['grade'] or '', chosen['producer'] if chosen else '',
                            rec['text_path'] or '', order['number'] + order['suffix'], order['date'], rec['identity_confirmed'],
                            rec['complete_text_confirmed'], '' if rec['pages_confirmed'] is None else rec['pages_confirmed'],
                            '|'.join(rec['reasons']), order['title'][:120]])
    summary = summarize(results, skipped, missing_register, scope)
    (out / 'SUMMARY.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return summary


def summarize(results, skipped, missing_register, scope):
    confirmed = [r for r in results if r[0]['confirmed']]
    by_blocker, conf_blocker, by_grade, conf_grade = Counter(), Counter(), Counter(), Counter()
    reasons, routes_i, routes_c = Counter(), Counter(), Counter()
    for rec, blockers, order, chosen in results:
        by_blocker.update(blockers)
        by_blocker['+'.join(blockers)] += 1 if len(blockers) > 1 else 0
        by_grade[rec['grade']] += 1
        if rec['confirmed']:
            conf_blocker.update(blockers)
            conf_grade[rec['grade']] += 1
            routes_i[rec['evidence']['identity_route']] += 1
            routes_c[rec['evidence']['complete_route']] += 1
        else:
            reasons.update(rec['reasons'])
    by_blocker = Counter({k: v for k, v in by_blocker.items() if v})
    return {
        'schema': 'eo-lachmann-summary/v1',
        'in_scope': len(scope),
        'assessed': len(results),
        'missing_from_register': sorted(missing_register),
        'confirmed': len(confirmed),
        'not_confirmed': len(results) - len(confirmed),
        'by_blocker': dict(sorted(by_blocker.items())),
        'confirmed_by_blocker': dict(sorted(conf_blocker.items())),
        'by_chosen_grade': dict(sorted((k or 'none', v) for k, v in by_grade.items())),
        'confirmed_by_grade': dict(sorted(conf_grade.items())),
        'identity_confirmed': sum(1 for r in results if r[0]['identity_confirmed']),
        'complete_text_confirmed': sum(1 for r in results if r[0]['complete_text_confirmed']),
        'pages_confirmed_true': sum(1 for r in results if r[0]['pages_confirmed'] is True),
        'pages_confirmed_false': sum(1 for r in results if r[0]['pages_confirmed'] is False),
        'pages_not_required': sum(1 for r in results if r[0]['pages_confirmed'] is None),
        'identity_routes': dict(sorted(routes_i.items())),
        'complete_routes': dict(sorted(routes_c.items())),
        'failure_reasons': dict(sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0]))),
        'witnesses_skipped_hash_mismatch': sum(1 for s in skipped if s['why'] == 'text_hash_mismatch'),
        'witnesses_skipped_other': dict(sorted(Counter(s['why'] for s in skipped if s['why'] != 'text_hash_mismatch').items())),
        'standing_note': W.NOTE,
        'ruling': RULING,
    }


# ---------------------------------------------------------------------------
# Blinded audit sample

LEAK_WORDS = ('audit key', 'swap', 'truncat', 'planted', 'control')


def read_confirmations(path):
    out = []
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def _clean(text):
    low = text.lower()
    return not any(w in low for w in LEAK_WORDS)


def audit_sample(n=59, seed='lachmann-2026-10-31', confirmations=None, packets=None, key_path=None, repo=None):
    """Draw n confirmed orders plus planted defects; write blinded packets and a separate key.

    Genuine items and the sources of planted defects are drawn only from confirmed orders whose
    text and title hold none of the reviewer-visible words in LEAK_WORDS, so that no packet can hint at its
    purpose. Planted defects: half carry one order's header over another confirmed order's text,
    half carry a confirmed text cut to its first 60 percent.
    """
    repo = Path(repo or HERE.parents[1])
    confirmations = Path(confirmations or HERE / 'output' / 'CONFIRMATIONS.jsonl')
    if packets is None or key_path is None:
        raise ValueError('packets directory and key path are required')
    packets, key_path = Path(packets).resolve(), Path(key_path).resolve()
    if key_path == packets or packets in key_path.parents:
        raise ValueError('the key file must live outside the packet directory')
    register = load_register(repo)
    pinakes = Pinakes(repo)
    pool = []
    for rec in read_confirmations(confirmations):
        if not rec.get('confirmed') or rec['instrument_id'] not in register:
            continue
        raw = (repo / rec['text_path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != rec['text_sha256']:
            continue
        body = body_of(raw.decode('utf-8'))
        if _clean(body) and _clean(register[rec['instrument_id']]['title']) and len(body.split()) >= 20:
            pool.append((rec['instrument_id'], rec, body))
    pool.sort(key=lambda x: x[0])
    rng = random.Random(seed)
    n_def = max(4, round(0.08 * n))
    n_swap = n_def // 2
    n_trunc = n_def - n_swap
    need = n + n_def + n_swap  # genuine, defective headers, and swap-source texts
    if len(pool) < need:
        raise ValueError(f'only {len(pool)} eligible confirmed orders; {need} needed')
    order = list(range(len(pool)))
    rng.shuffle(order)
    sample = [pool[i] for i in order[:n]]
    rest = [pool[i] for i in order[n:]]
    swaps_head = rest[:n_swap]
    truncs = rest[n_swap:n_swap + n_trunc]
    donor_pool = rest[n_swap + n_trunc:]
    items = []

    def page_count(iid):
        row = pinakes.orders.get(iid)
        try:
            return int(row['pages']) if row and row.get('pages') else None
        except ValueError:
            return None

    def packet_for(iid, rec, text):
        o = register[iid]
        has_pdf = rec['grade'] == 'archival_replica_scan_pending_codebook'
        return {'claimed_number': o['number'] + o['suffix'] if o['number'] else None, 'claimed_date': o['date'] or None,
                'claimed_title': o['title'] or None, 'page_count': page_count(iid) if has_pdf else None, 'text': text}

    for iid, rec, body in sample:
        items.append(({'kind': 'genuine', 'instrument_id': iid}, packet_for(iid, rec, body)))
    used_donors = set()
    for iid, rec, body in swaps_head:
        year = register[iid]['date'][:4]
        cands = [d for d in donor_pool if d[0] not in used_donors and d[0] != iid and register[d[0]]['date'][:4] == year]
        cands = cands or [d for d in donor_pool if d[0] not in used_donors and d[0] != iid]
        donor = cands[rng.randrange(len(cands))]
        used_donors.add(donor[0])
        items.append(({'kind': 'defect_header_with_other_text', 'instrument_id': iid, 'text_from_instrument': donor[0]},
                      packet_for(iid, rec, donor[2])))
    for iid, rec, body in truncs:
        cut = int(len(body) * 0.6)
        sp = body.rfind(' ', max(0, cut - 40), cut + 1)
        cut = sp if sp > 0 else cut
        items.append(({'kind': 'defect_text_cut_short', 'instrument_id': iid, 'kept_chars': cut, 'full_chars': len(body)},
                      packet_for(iid, rec, body[:cut].rstrip())))
    rng.shuffle(items)
    packets.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = OrderedDict()
    for k, (meta, packet) in enumerate(items, 1):
        item_id = 'P' + hashlib.sha256(f'{seed}|{k}|{meta["instrument_id"]}'.encode()).hexdigest()[:10]
        meta['sequence'] = k
        key[item_id] = meta
        doc = OrderedDict([('item_id', item_id)] + list(packet.items()))
        (packets / f'{item_id}.json').write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    key_path.write_text(json.dumps({'seed': seed, 'n_genuine': n, 'n_defects': n_def, 'items': key}, indent=2, ensure_ascii=False) + '\n',
                        encoding='utf-8')
    return {'items': len(items), 'genuine': n, 'defects': n_def, 'swap': n_swap, 'cut_short': n_trunc, 'eligible_pool': len(pool)}


def check_packets(packets, key_path):
    """Leak check: the words a reviewer must never see, and any source instrument id, outside the order text itself."""
    problems = []
    key = json.loads(Path(key_path).read_text(encoding='utf-8'))['items']
    sources = {v['text_from_instrument'] for v in key.values() if 'text_from_instrument' in v}
    for p in sorted(Path(packets).glob('*.json')):
        raw = p.read_text(encoding='utf-8')
        doc = json.loads(raw)
        wrapper = json.dumps({k: v for k, v in doc.items() if k != 'text'}).lower() + ' ' + p.name.lower()
        for w in LEAK_WORDS:
            if w in wrapper or w in raw.lower():
                problems.append((p.name, w))
        for s in sources:
            if s.lower() in raw.lower():
                problems.append((p.name, s))
    return problems


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run', help='collate every in-scope order and write CONFIRMATIONS.jsonl, RESIDUAL.csv, SUMMARY.json')
    r.add_argument('--repo', default=str(HERE.parents[1]))
    r.add_argument('--out', default=str(HERE / 'output'))
    a = sub.add_parser('audit-sample', help='write blinded audit packets and a separate key file')
    a.add_argument('--repo', default=str(HERE.parents[1]))
    a.add_argument('--confirmations', default=str(HERE / 'output' / 'CONFIRMATIONS.jsonl'))
    a.add_argument('--packets', required=True, help='directory for the blinded packets')
    a.add_argument('--key', required=True, help='path of the key file; keep it away from the reviewer')
    a.add_argument('--n', type=int, default=59)
    a.add_argument('--seed', default='lachmann-2026-10-31')
    args = ap.parse_args(argv)
    if args.cmd == 'run':
        print(json.dumps(run(args.repo, args.out), indent=2, sort_keys=True))
    else:
        res = audit_sample(args.n, args.seed, args.confirmations, args.packets, args.key, args.repo)
        print(json.dumps(res, indent=2))
        bad = check_packets(args.packets, args.key)
        print('leak check:', 'clean' if not bad else bad)
        if bad:
            sys.exit(1)


if __name__ == '__main__':
    main()
