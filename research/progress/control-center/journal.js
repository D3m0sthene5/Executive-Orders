/* Froissart: the project journal, one narrative entry per project day.
   Reads research/progress/journal/JOURNAL.json from the checked main commit (falls back to the bundled copy). */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.EOJournal = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const PATH = 'research/progress/journal/JOURNAL.json';
  const SCHEMA = 'eo-project-journal/v1';
  const esc = v => String(v ?? '').replace(/[&<>"']/g, k => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[k]));
  const num = v => Number.isFinite(v) ? v.toLocaleString('en-US') : '';
  const DATE = /^\d{4}-\d{2}-\d{2}$/;

  function validate(j) {
    if (!j || j.schema !== SCHEMA || !Array.isArray(j.days) || !j.days.length) throw Error('journal schema');
    let prev = '';
    for (const d of j.days) {
      if (!d || !DATE.test(d.date) || typeof d.story !== 'string' || !d.story.trim()) throw Error('journal entry');
      if (d.date <= prev) throw Error('journal dates out of order');
      if (d.ready !== undefined && !Number.isInteger(d.ready)) throw Error('journal ready count');
      prev = d.date;
    }
    return j;
  }

  function parse(text) { return validate(JSON.parse(text)); }

  /* state: {journal, source, note}. readText(path) reads the file at the checked commit. */
  async function load(state, sha, readText) {
    try {
      const j = parse(await readText(PATH));
      return {journal: j, source: 'main ' + String(sha || '').slice(0, 7), note: ''};
    } catch (err) {
      return Object.assign({}, state || {}, {note: 'Journal refresh unavailable; showing ' + ((state && state.source) || 'the saved copy') + '.'});
    }
  }

  function dayLabel(iso) {
    const [y, m, d] = iso.split('-').map(Number);
    return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString('en-US', {timeZone: 'UTC', weekday: 'short', month: 'long', day: 'numeric'});
  }

  function spark(days) {
    const pts = days.filter(d => Number.isInteger(d.ready));
    if (pts.length < 2) return '';
    const max = Math.max(...pts.map(d => d.ready)) || 1, w = 320, h = 60;
    const t0 = Date.parse(pts[0].date), t1 = Date.parse(pts[pts.length - 1].date) || t0 + 1;
    const xy = pts.map(d => [((Date.parse(d.date) - t0) / (t1 - t0 || 1)) * w, h - (d.ready / max) * (h - 6) - 3]);
    const path = xy.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
    return '<svg class="jr-spark" viewBox="-4 0 ' + (w + 8) + ' ' + h + '" role="img" aria-label="Orders ready for human review, by day">' +
      '<path d="' + path + '"/>' + xy.map((p, i) => '<circle cx="' + p[0].toFixed(1) + '" cy="' + p[1].toFixed(1) + '" r="2.5"><title>' +
      esc(pts[i].date + ': ' + num(pts[i].ready) + ' ready') + '</title></circle>').join('') + '</svg>';
  }

  function caption(days) {
    const pts = days.filter(d => Number.isInteger(d.ready));
    if (pts.length < 2) return '';
    const peak = pts.reduce((a, d) => d.ready > a.ready ? d : a, pts[0]), last = pts[pts.length - 1];
    const short = iso => dayLabel(iso).replace(/^\w+, /, '');
    return '<p class="jr-cap">Orders ready for human review on each day with a published count: ' + esc(num(pts[0].ready)) + ' on ' + esc(short(pts[0].date)) +
      ', peak ' + esc(num(peak.ready)) + ' on ' + esc(short(peak.date)) + ', ' + esc(num(last.ready)) + ' on ' + esc(short(last.date)) + '.</p>';
  }

  function render(state) {
    const j = state && state.journal;
    if (!j) return '<section class="journal"><h1>Project journal</h1><p>' + esc((state && state.note) || 'Loading the journal…') + '</p></section>';
    const h = j.headline || {}, l = j.last_48_hours;
    const days = j.days.slice().reverse();
    const stat = (v, t) => '<div class="jr-stat"><b>' + esc(num(v)) + '</b><span>' + esc(t) + '</span></div>';
    return '<section class="journal">' +
      '<div class="eyebrow">' + esc(j.title || 'Project journal') + ' · ' + esc(j.days.length) + ' days · updated ' + esc(j.updated || '') + '</div>' +
      '<h1>What the project has done, day by day</h1>' +
      (state.note ? '<p class="jr-note">' + esc(state.note) + '</p>' : '') +
      '<div class="jr-stats">' + stat(h.ready_for_human_review, 'ready for human review') + stat(h.orders_with_provisional_status, 'orders with a provisional status') +
      stat(h.orders_in_census, 'orders in the census') + stat(h.certified_whole_lifecycles, 'certified by a person (so far)') + '</div>' +
      spark(j.days) + caption(j.days) +
      '<div class="jr-meaning">' + (j.meaning || []).map(p => '<p>' + esc(p) + '</p>').join('') + '</div>' +
      (l ? '<section class="jr-recent"><h2>The last 48 hours</h2><p class="jr-delta">Ready ' + esc(num(l.ready_start)) + ' → ' + esc(num(l.ready_end)) +
        '</p><ul>' + (l.summary || []).map(p => '<li>' + esc(p) + '</li>').join('') + '</ul></section>' : '') +
      '<h2>Every day</h2><ol class="jr-days">' + days.map(d =>
        '<li class="jr-day" id="day-' + esc(d.date) + '"><div class="jr-date">' + esc(dayLabel(d.date)) +
        (Number.isInteger(d.ready) ? '<span class="jr-ready">' + esc(num(d.ready)) + ' ready</span>' : '') + '</div>' +
        '<h3>' + esc(d.title || '') + '</h3><p>' + esc(d.story) + '</p>' +
        (Array.isArray(d.milestones) && d.milestones.length ? '<ul class="jr-ms">' + d.milestones.map(m => '<li>' + esc(m) + '</li>').join('') + '</ul>' : '') +
        '</li>').join('') + '</ol>' +
      '<p class="jr-how">' + esc(j.how_written || '') + ' Source: <a href="https://github.com/D3m0sthene5/Executive-Orders/blob/main/' + PATH +
      '" target="_blank" rel="noopener">' + PATH + '</a> (' + esc(state.source || 'saved copy') + '). The rocket view is still at <a href="#mission">#mission</a>.</p>' +
      '</section>';
  }

  return {PATH, SCHEMA, validate, parse, load, render};
});
