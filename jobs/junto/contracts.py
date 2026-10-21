"""Minimal optional prospective saver contract; no test execution or scoring."""
import re


def validate_contract(candidate):
    c=candidate.get('test_contract')
    if c is None:return
    if not isinstance(c,dict) or c.get('schema')!='junto.test-contract/1':raise ValueError('invalid test contract schema')
    for key in ('unit_of_work','baseline','quality_requirement','stopping_rule','result_location'):
        if not isinstance(c.get(key),str) or not c[key].strip():raise ValueError('test contract missing '+key)
    if not re.fullmatch(r'[a-z][a-z0-9_]*',candidate.get('saver_key','')):raise ValueError('invalid stable saver key')
    if candidate.get('origin') not in ('owner-seeded','neyman-observed'):raise ValueError('test contract missing origin')
    path=c['result_location']
    if path.startswith('/') or '..' in path.split('/') or not path.startswith(('research/','jobs/')):
        raise ValueError('test result must be repository relative')
