import plants
import tiro_common as C
from conftest import claim


def test_shift_date_and_leap_day():
    assert plants.shift_date('1950-06-30') == '1947-06-30'
    assert plants.shift_date('1960-02-29') == '1957-02-28'
    assert plants.shift_date('1950-06-30T00:00') == '1947-06-30T00:00'
    assert plants.shift_date('unknown') == 'unknown'
    assert plants.shift_date(None) is None


def test_control_count_matches_old_rounding():
    assert [plants.control_count(n) for n in (0, 1, 15, 22, 23, 30, 37, 38)] == [0, 1, 1, 1, 2, 2, 2, 3]


def test_end_mode_plants_only_end_dates_and_keys_hash_both_versions():
    claims = [claim('EO:1'), claim('EO:2', end='1960-02-29'), claim('EO:3', end=None)]
    made = plants.make_controls(claims, 'b01')
    assert made['mode'] == 'end' and len(made['controls']) == 1
    k = made['controls'][0]
    assert k['instrument_id'] in ('EO:1', 'EO:2') and k['kind'] == 'date_shift' and k['type'] == 'date_shift_end'
    planted = next(r for r in made['review_rows'] if r['instrument_id'] == k['instrument_id'])
    genuine = made['genuine'][0]
    assert C.canon(planted) == k['planted'] and C.canon(genuine) == k['genuine']
    assert planted['identity'] == genuine['identity']
    assert planted['whole_order_end']['date'] != genuine['whole_order_end']['date']
    assert [r['instrument_id'] for r in made['review_rows']] == ['EO:1', 'EO:2', 'EO:3']
    # Seeded by batch name: the same draw every time.
    assert plants.make_controls(claims, 'b01')['controls'] == made['controls']


def test_event_and_signing_modes():
    ev = [claim('EO:5', end=None, events=[{'effective_date': '1970-01-01'}])]
    made = plants.make_controls(ev, 'x')
    assert made['mode'] == 'event'
    assert made['review_rows'][0]['operative_clauses'][0]['later_events'][0]['effective_date'] == '1967-01-01'
    made = plants.make_controls([claim('EO:6', end=None)], 'x')
    assert made['mode'] == 'signing' and made['review_rows'][0]['identity']['signing_date'] == '1937-01-15'


def test_names_defect_uses_the_kind_words_and_old_keys_default_to_date_shift():
    old_key = {'instrument_id': 'EO:1', 'defect': 'x'}  # written before kinds existed
    assert plants.names_defect({'verdict': 'rejected', 'defects': ['first_end wrong year']}, old_key)
    assert not plants.names_defect({'verdict': 'rejected', 'defects': ['quote mismatch']}, old_key)
    assert not plants.names_defect({'verdict': 'upheld', 'defects': ['date']}, old_key)
    assert not plants.names_defect(None, old_key)
