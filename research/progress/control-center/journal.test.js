'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const J = require('./journal.js');

const committed = fs.readFileSync(path.join(__dirname, '../journal/JOURNAL.json'), 'utf8');
const bundled = fs.readFileSync(path.join(__dirname, 'journal.json'), 'utf8');

test('committed journal is valid, dated in order and starts on the first project day', () => {
  const j = J.parse(committed);
  assert.equal(j.days[0].date, '2026-10-17');
  assert.equal(j.headline.certified_whole_lifecycles, 0);  // never inflated
  for (const d of j.days) assert.ok(d.story.length > 40, d.date);
});

test('the bundled copy served by the site equals the committed journal', () => {
  assert.deepStrictEqual(JSON.parse(bundled), JSON.parse(committed));
});

test('rejects a wrong schema, an empty story and dates out of order', () => {
  const j = JSON.parse(committed);
  assert.throws(() => J.validate(Object.assign({}, j, {schema: 'x'})));
  assert.throws(() => J.validate(Object.assign({}, j, {days: [{date: '2026-10-17', story: ' '}]})));
  assert.throws(() => J.validate(Object.assign({}, j, {days: [j.days[1], j.days[0]]})));
  assert.throws(() => J.validate(Object.assign({}, j, {days: [Object.assign({}, j.days[0], {ready: '130'})]})));
});

test('load keeps the last good journal and says so when main cannot be read', async () => {
  const good = await J.load(null, 'a'.repeat(40), async () => committed);
  assert.ok(good.journal && good.source.startsWith('main aaaaaaa'));
  const kept = await J.load(good, 'b'.repeat(40), async () => { throw Error('offline'); });
  assert.strictEqual(kept.journal, good.journal);
  assert.match(kept.note, /unavailable/);
  const bad = await J.load(good, 'c'.repeat(40), async () => '{"schema":"other"}');
  assert.strictEqual(bad.journal, good.journal);
});

test('render escapes text and shows every day, newest first, plus the rocket link', () => {
  const j = JSON.parse(committed);
  j.days[j.days.length - 1].story = 'Injected <script>alert(1)</script> text that is long enough to pass.';
  const html = J.render({journal: J.validate(j), source: 'test'});
  assert.ok(!html.includes('<script>'));
  assert.ok(html.includes('&lt;script&gt;'));
  assert.equal((html.match(/class="jr-day"/g) || []).length, j.days.length);
  assert.ok(html.indexOf('day-2026-11-09') < html.indexOf('day-2026-10-17'));
  assert.ok(html.includes('href="#mission"'));
});

test('the DKLA deploy copies match the control-center sources', () => {
  const dkla = path.join(__dirname, '../journal/dkla/eo/dashboard');
  for (const f of ['journal.js', 'journal.css', 'journal.json'])
    assert.equal(fs.readFileSync(path.join(dkla, f), 'utf8'), fs.readFileSync(path.join(__dirname, f), 'utf8'), f);
  assert.ok(fs.readFileSync(path.join(dkla, 'index.html'), 'utf8').includes('/eo/dashboard/journal.js'));
  assert.ok(fs.readFileSync(path.join(dkla, 'app.js'), 'utf8').includes("read('/eo/dashboard/journal.json','text')"));
});
