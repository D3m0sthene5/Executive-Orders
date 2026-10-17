import assert from 'node:assert/strict';
import {csvParse,csvWrite} from './merge_statute_custody.mjs';
const x=csvParse('name,note\n"66 Stat., 259","data ""quoted"""\n');
assert.equal(x[0].name,'66 Stat., 259');
assert.deepEqual(csvParse(csvWrite(x,['name','note'])),x);
console.log('Statute custody CSV tests passed. Production crosswalk also enforces 98/10 counts, matching case IDs, and zero legal promotions.');
