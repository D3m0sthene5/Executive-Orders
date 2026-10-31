"""Independent bounded probes; stdout JSON only, no canonical writes."""
from pathlib import Path
import sys, json, hashlib, tempfile, copy, re, time
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'jobs/claim-kit'))
import evidence_preflight as p


def run(text, clauses=None, iid='EO:2', transform=None):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp); (root/'source.txt').write_text(text)
        source={'text_path':'source.txt','text_sha256':hashlib.sha256(text.encode()).hexdigest(),'sha256':'a'*64}
        item={'source':source,'text':text,'char_start':0,'char_end':len(text)}
        d={'instrument_id':iid,'original_source_id':'ORIGINAL:'+iid,'evidence':{'ORIGINAL:'+iid:item},'actor_provisions':[],
           'clauses': copy.deepcopy(clauses) if clauses is not None else [copy.deepcopy(item)]}
        if transform: transform(d, source)
        before=copy.deepcopy(d); out=p.inspect(d,root)
        assert d == before, 'mutated dossier'
        for task in out['tasks']:
            for gap in task.get('uncovered_regions',[]):
                a,b=gap['char_start'],gap['char_end']; assert text[a:b] == gap['text'] and 0 <= a < b <= len(text)
        return out


def case(name, text, clauses=None, iid='EO:2', transform=None):
    out=run(text, clauses, iid, transform)
    return {'name':name,'kinds':[t['kind'] for t in out['tasks']], 'tasks':out['tasks']}


def main():
    cases=[]
    base='Executive Order 2\nSection 1. The Board is hereby established.\n\nThe Secretary shall publish annual reports.\nTHE WHITE HOUSE\n'
    a,b=base.index('Section 1.'),base.index('The Secretary')
    ranges=[{'char_start':a,'char_end':b}]
    cases.append(case('omitted_unnumbered',base,ranges))
    cases.append(case('complete_disjoint',base,[{'char_start':a,'char_end':b},{'char_start':b,'char_end':base.index('THE WHITE HOUSE')}]))
    cases.append(case('overlapping_complete',base,[{'char_start':a,'char_end':b+12},{'char_start':b,'char_end':base.index('THE WHITE HOUSE')}]))
    for bad in [None,{},'bad',True,-3,3.5]:
        cases.append(case('malformed_start_'+repr(bad),base,[{'char_start':bad,'char_end':len(base)}]))
    for key,value in [('text_path','other.txt'),('text_sha256','b'*64),('sha256','b'*64)]:
        def alter(d,s,key=key,value=value):
            d['clauses']=[{'char_start':a,'char_end':len(base),'text':base[a:],'source':dict(s,**{key:value})}]
        cases.append(case('conflicting_'+key,base,transform=alter))
    cases.append(case('wrong_quote',base,[{'char_start':a,'char_end':len(base),'text':'not the quote'}]))
    for ref in ['Executive Order 3 is hereby amended.', 'Executive Order No. 3 of January 1, 2000.',
                'Executive Order 3 Is Hereby Amended.', 'Executive Order No. 3 of January 1, 2000']:
        cases.append(case('reference_'+ref,'Executive Order 2\n'+ref+'\nThe Secretary shall publish annual reports.\nTHE WHITE HOUSE\n', []))
    cases.append(case('multi_order_target_middle','Executive Order 1\nThe Secretary shall create a first board.\nTHE WHITE HOUSE\n'+base+'Executive Order 3\nThe Secretary shall create a third board.\nTHE WHITE HOUSE\n',[]))
    cases.append(case('duplicate_target_heading','Executive Order 2\nThe Secretary shall create a first board.\nTHE WHITE HOUSE\n'+base,[]))
    cases.append(case('two_bare_headings','EXECUTIVE ORDER\nThe Secretary shall create a first board.\nTHE WHITE HOUSE\nEXECUTIVE ORDER\nThe Secretary shall create a second board.\nTHE WHITE HOUSE\n',[]))
    cases.append(case('bare_target_numbered_neighbor','EXECUTIVE ORDER\nThe Secretary shall create a first board.\nTHE WHITE HOUSE\nExecutive Order 3\nThe Secretary shall create a second board.\nTHE WHITE HOUSE\n',[]))
    for lead in ['WHEREAS the law provides that the Secretary shall submit a report;',
                 'By the authority vested in me, it is hereby ordered as follows:',
                 'By the authority vested in me, the Secretary shall submit a report.',
                 'I hereby find that public work is complete.',
                 '"The Secretary shall submit an annual report."',
                 '\'The Secretary shall submit an annual report.\'',
                 'The Secretary is hereby directed to submit an annual report.',
                 'The Secretary must submit an annual report.',
                 'The Secretary will submit an annual report.']:
        cases.append(case('lead_'+lead,'Executive Order 2\n'+lead+'\nTHE WHITE HOUSE\n',[]))
    quoted='Executive Order 2\nSection 1. The Secretary shall use this form:\n"The Secretary shall publish a report.\nThe Board shall issue a certificate."\nTHE WHITE HOUSE\n'
    cases.append(case('quoted_continuation',quoted,[{'char_start':quoted.index('Section 1.'),'char_end':quoted.index('"')}]))
    amendment='Executive Order 2\nSection 1. Executive Order 1 is amended by inserting:\n"The Secretary shall publish a report."\nTHE WHITE HOUSE\n'
    cases.append(case('omitted_amendment_quoted_payload',amendment,[{'char_start':amendment.index('Section 1.'),'char_end':amendment.index('"')}]))
    for lead in ['T his order sh all become effective upon the report.', 'It is unlawful to transfer the parcel.', 'No person shall transfer the parcel.', 'THIS ORDER SHALL BECOME EFFECTIVE IMMEDIATELY.']:
        cases.append(case('ocr_or_prohibition_'+lead, 'Executive Order 2\n'+lead+'\nTHE WHITE HOUSE\n', []))
    separated='Executive Order 2\nSection 1. Executive Order 1 is amended as follows:\n\n\"The Secretary shall publish a report.\"\nTHE WHITE HOUSE\n'
    cases.append(case('separate_paragraph_quoted_amendment', separated,[{'char_start':separated.index('Section 1.'),'char_end':separated.index(chr(34))}]))
    cases.append(case('post_signature_annex',base+'SCHEDULE\nThe Secretary shall preserve the forms.\n[F. R. Doc. test]\n',ranges+[{'char_start':b,'char_end':base.index('THE WHITE HOUSE')}]))
    for c in cases:
        c['gap_texts']=[g['text'] for t in c['tasks'] for g in t.get('uncovered_regions',[])]
    return {'cases':cases, 'count':len(cases),'no_mutation':True,'exact_spans':True}
if __name__=='__main__': print(json.dumps(main(),indent=2))
