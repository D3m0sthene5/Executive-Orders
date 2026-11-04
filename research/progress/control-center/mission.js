/* Capcom's frozen model and Apollo presentation, fed by a hash-bound generation. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.EOMission = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const PATHS = Object.freeze({mission:'jobs/daily-digest/output/MISSION.json', refresh:'jobs/daily-digest/output/MISSION_REFRESH.json', tracker:'jobs/readiness-tracker/output/READINESS_BY_ORDER.csv', tracker_status:'jobs/readiness-tracker/output/STATUS.json', tracker_summary:'jobs/readiness-tracker/output/SUMMARY.json', checker_status:'jobs/claim-checker/output/STATUS.json', universe:'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv', weights:'research/progress/remaining-work/MISSION_WEIGHTS.csv', human_review:'research/stage19/output/PROGRESS.json'});
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number = value => Number.isFinite(value) ? value.toLocaleString('en-US') : 'Unknown';
  const percent = value => Number.isFinite(value) ? (100 * value).toFixed(2) + '%' : 'Unknown';
  const date = value => Number.isFinite(Date.parse(value)) ? new Date(value).toLocaleString('en-US', {timeZone:'UTC',year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',timeZoneName:'short'}) : 'Date unknown';
  const clock = hours => {const minutes = Math.round(hours * 60); return 'T+' + Math.floor(minutes / 60) + 'h ' + String(minutes % 60).padStart(2,'0') + 'm';};
  const integer = value => Number.isInteger(value) && value >= 0;
  const sha = value => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
  const gitSha = value => typeof value === 'string' && /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/.test(value);
  const initial = () => ({data:null,ref:null,state:'unavailable',message:'Mission generation has not been loaded.',checked_utc:null,accepted_utc:null,human:null});
  async function hash(text) {return Array.from(new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))), b => b.toString(16).padStart(2,'0')).join('');}
  function validateRow(row, model) {
    return row && Number.isFinite(row.progress) && row.progress >= 0 && row.progress <= 1 && Number.isFinite(row.met_hours) && row.met_hours >= 0 && Math.abs(row.met_hours - row.progress * model.first_step_hours) < .003 && integer(row.orders_in_census) && row.orders_goal === row.orders_in_census + model.census_gap && integer(row.ready_for_human_review) && row.ready_for_human_review <= row.orders_in_census && integer(row.provisional_statuses) && row.provisional_statuses <= row.orders_in_census && typeof row.phase === 'string' && Number.isFinite(Date.parse(row.committed_at || row.date));
  }
  function validate(payload, context) {
    const fail = message => ({ok:false,message});
    if (!payload || payload.schema !== 'eo-mission/v1') return fail('Mission publication is missing or has an unsupported schema.');
    const model = payload.model, latest = payload.latest;
    if (!model || model.version !== 'capcom-frozen-weights-v1' || model.denominator_version !== 'current-census-plus-frozen-gap-v1' || model.history_compatible !== true || model.census_gap !== 1314 || !Number.isFinite(model.first_step_hours) || Math.abs(model.first_step_hours - (109 + 24/60 + 15/3600)) > 1e-8 || !sha(model.weights_sha256)) return fail('Mission model or historical comparison needs review.');
    if (payload.freshness?.state !== 'generation_reported' || payload.freshness?.claim_receipts !== 'claim_versions_match') return fail('Mission publication is awaiting a matching tracker generation.');
    if (!Number.isFinite(Date.parse(payload.generated_utc)) || !/^[0-9a-f]{40}$/.test(payload.repository_input_commit || '')) return fail('Mission generation receipt is incomplete.');
    if (!context.status || context.status.job !== 'readiness-tracker' || context.status.result !== 'succeeded') return fail('The published tracker generation has not succeeded.');
    const generation = payload.tracker_generation;
    if (!generation || ['job','result','commit_run','finished_utc','run_url'].some(key => generation[key] !== context.status[key])) return fail('Newer tracker detected; mission publication is pending.');
    if(!context.checker || context.checker.job!=='claim-checker' || context.checker.result!=='succeeded' || context.checker.exit_code!==0) return fail('The current checker generation has not succeeded; mission publication is pending.');
    if(!payload.checker_generation || ['job','result','exit_code','commit_run','finished_utc','run_url'].some(key=>payload.checker_generation[key]!==context.checker[key])) return fail('Newer checker detected; mission publication is pending.');
    for (const key of ['tracker','tracker_status','tracker_summary','checker_status','universe','weights','human_review']) {
      const source = payload.sources?.[key];
      if (!source || source.path !== PATHS[key] || !sha(source.sha256) || source.sha256 !== context.hashes[key]) return fail('Source mismatch (' + key.replaceAll('_',' ') + '); mission publication is pending.');
    }
    if (model.weights_sha256 !== payload.sources.weights.sha256) return fail('Frozen mission weights do not match the source receipt.');
    if (!validateRow(latest,model) || latest.orders_goal !== model.orders_goal || latest.orders_in_census !== context.summary?.orders_total || latest.ready_for_human_review !== context.summary?.ready_for_human_review || latest.provisional_statuses !== context.summary?.orders_with_provisional_status) return fail('Mission totals do not match the tracker generation.');
    if (!Array.isArray(payload.history) || !payload.history.length || payload.history.some((row,i) => !validateRow(row,model) || i > 0 && row.date < payload.history[i-1].date) || ['date','committed_at','progress','ready_for_human_review','met_hours','orders_in_census','orders_goal','provisional_statuses','phase'].some(key=>payload.history.at(-1)[key]!==latest[key])) return fail('Mission history is incomplete or incompatible with its latest checkpoint.');
    if (!Array.isArray(payload.milestones) || !payload.milestones.length || !payload.milestones.some(m => m.key === 'first_step' && Math.abs(m.hours-model.first_step_hours)<1e-8) || payload.milestones.some(m => !Number.isFinite(m.hours) || m.hours < 0 || m.hours > model.first_step_hours)) return fail('Apollo milestone clock is incomplete.');
    return {ok:true};
  }
  function reject(previous, message, checked = new Date().toISOString()) {return {...(previous || initial()),state:'pending',message,checked_utc:checked};}
  async function readinessTree(ref, readTree) {
    if(!gitSha(ref) || typeof readTree!=='function') throw Error('Readiness tree API unavailable');
    const child=(tree,path)=>{
      if(!tree || tree.truncated!==false || !Array.isArray(tree.tree)) throw Error('Incomplete scoped tree');
      const entries=tree.tree.filter(entry=>entry.path===path);
      if(entries.length!==1 || entries[0].type!=='tree' || entries[0].mode!=='040000' || !gitSha(entries[0].sha)) throw Error('Missing scoped tree');
      return entries[0].sha;
    };
    const research=child(await readTree(ref),'research');
    const tree=await readTree(research);
    if(tree?.sha!==research) throw Error('Scoped tree identity mismatch');
    return child(tree,'readiness');
  }
  async function load(previous, ref, readText, readTree) {
    const checked = new Date().toISOString();
    let receipt;
    try {
      receipt=JSON.parse(await readText(PATHS.refresh));
      if(receipt.schema!=='eo-mission-refresh/v1' || !['ready','pending'].includes(receipt.state) || !Number.isFinite(Date.parse(receipt.attempted_utc))) return reject(previous,'Mission publication receipt is incomplete.',checked);
      if(receipt.state==='pending' && previous?.data) return {...reject(previous,receipt.reason || 'New research inputs are awaiting a matching mission publication.',checked),attempted_utc:receipt.attempted_utc};
      const entries = await Promise.all(Object.entries(PATHS).filter(([key])=>key!=='refresh').map(async ([key,path]) => [key,await readText(path)]));
      const texts = Object.fromEntries(entries), payload = JSON.parse(texts.mission);
      const hashes = Object.fromEntries(await Promise.all(Object.keys(texts).filter(key => key !== 'mission').map(async key => [key,await hash(texts[key])])));
      const human = JSON.parse(texts.human_review), context = {hashes,status:JSON.parse(texts.tracker_status),checker:JSON.parse(texts.checker_status),summary:JSON.parse(texts.tracker_summary)};
      const result = validate(payload,context);
      if (!result.ok) return reject(previous,result.message,checked);
      if(!receipt.tracker_generation || ['job','result','commit_run','finished_utc','run_url'].some(key=>receipt.tracker_generation[key]!==context.status[key])) return reject(previous,'Mission publication receipt does not match the tracker generation.',checked);
      const certified = human.independently_reviewed_whole_lifecycle_complete;
      const reported = payload.human_review?.published_whole_lifecycle_certifications;
      if ((integer(certified) ? certified : null) !== reported) return reject(previous,'Human-review source changed; mission publication is pending.',checked);
      const accepted={data:payload,ref,state:'current',message:'Mission and tracker sources match at the checked main revision.',checked_utc:checked,accepted_utc:checked,attempted_utc:receipt.attempted_utc,human:integer(certified)?certified:null};
      if(receipt.state==='pending') return reject(accepted,receipt.reason || 'New research inputs are awaiting a matching mission publication.',checked);
      const retained=previous?.data?previous:accepted, witness=payload.readiness_inputs;
      if(witness?.path!=='research/readiness' || !gitSha(witness.git_tree) || receipt.readiness_inputs?.path!==witness.path || receipt.readiness_inputs?.git_tree!==witness.git_tree) return reject(retained,'Readiness input witness is missing or inconsistent; mission publication is pending.',checked);
      let currentTree;
      try {currentTree=await readinessTree(ref,readTree);} catch {return reject(retained,'Current readiness inputs could not be verified; mission freshness is unknown.',checked);}
      if(currentTree!==witness.git_tree) return reject(retained,'Research inputs changed after this mission generation; a checker/tracker refresh is pending.',checked);
      return accepted;
    } catch (error) {
      return reject(previous,receipt?.state==='pending' ? (receipt.reason || 'New research inputs are awaiting a matching mission publication.') : 'Mission refresh unavailable; waiting for a complete matching publication.',checked);
    }
  }
  // The original Apollo Earth-to-Moon path and ship, using sampled arc length
  // so the visual distance follows the same fraction as the mission clock.
  function flight(payload) {
    const latest = payload.latest, end = payload.model.first_step_hours;
    const p0={x:105,y:248}, p1={x:240,y:18}, p2={x:590,y:16}, p3={x:730,y:108};
    const curve = t => ({x:(1-t)**3*p0.x+3*(1-t)**2*t*p1.x+3*(1-t)*t*t*p2.x+t**3*p3.x,y:(1-t)**3*p0.y+3*(1-t)**2*t*p1.y+3*(1-t)*t*t*p2.y+t**3*p3.y});
    const samples=[{...p0,length:0}];
    for(let i=1;i<=300;i++){const p=curve(i/300),last=samples.at(-1);samples.push({...p,length:last.length+Math.hypot(p.x-last.x,p.y-last.y)});}
    const total=samples.at(-1).length;
    const at=f=>{const target=Math.max(0,Math.min(1,f))*total;const i=Math.max(1,samples.findIndex(p=>p.length>=target));const a=samples[i-1],b=samples[i],r=(target-a.length)/(b.length-a.length);return {x:a.x+(b.x-a.x)*r,y:a.y+(b.y-a.y)*r,angle:Math.atan2(b.y-a.y,b.x-a.x)*180/Math.PI};};
    const current=at(latest.met_hours/end),path='M105 248 C240 18 590 16 730 108';
    const names={launch:'Launch',tli:'Leave Earth orbit',loi:'Lunar orbit',landing:'Landing',first_step:'First step'};
    const points=payload.milestones.map(m=>{const p=at(m.hours/end),label=names[m.key]||m.label||m.event||m.key;return '<g class="mission-milestone '+(latest.met_hours>=m.hours?'passed':'')+'"><title>'+escape(label+' · '+clock(m.hours))+'</title><circle cx="'+p.x+'" cy="'+p.y+'" r="4"/><text x="'+(m.key==='landing'?p.x-15:p.x)+'" y="'+(m.key==='landing'?p.y+34:p.y-22)+'" text-anchor="'+(m.key==='landing'?'end':'middle')+'">'+escape(label)+'</text></g>';}).join('');
    const crumbs=payload.history.slice(0,-1).map(row=>{const p=at(row.met_hours/end);return '<circle class="mission-crumb" cx="'+p.x+'" cy="'+p.y+'" r="3"><title>'+escape(row.date+' · '+clock(row.met_hours)+' · '+percent(row.progress))+'</title></circle>';}).join('');
    return '<svg class="mission-flight" viewBox="0 0 820 330" role="img" aria-label="'+escape('Apollo mission: '+latest.phase+', '+clock(latest.met_hours)+', '+percent(latest.progress)+' effort-weighted progress. First step represents every modeled order ready for human review.')+'"><circle class="mission-earth" cx="69" cy="281" r="46"/><path class="mission-land" d="M32 258q18-19 32-10l-6 18 17 13-11 15-23-5z M85 289l19 3-16 22-12-10z"/><circle class="mission-moon" cx="759" cy="99" r="24"/><circle class="mission-crater" cx="750" cy="92" r="5"/><circle class="mission-crater" cx="766" cy="107" r="4"/><path class="mission-trail" d="'+path+'"/><path class="mission-traveled" d="'+path+'" pathLength="1" stroke-dasharray="'+latest.progress+' 1"/>'+points+crumbs+'<g transform="translate('+current.x+','+current.y+') rotate('+current.angle+')"><path class="mission-flame" d="M-13-4Q-30 0-13 4Z"/><path class="mission-fin" d="M-11-5L-17-11-6-5ZM-11 5L-17 11-6 5Z"/><path class="mission-ship" d="M-13-5.5H6Q15-5.5 20 0Q15 5.5 6 5.5H-13Z"/><circle class="mission-window" cx="4" r="2.6"/></g><text class="mission-here" x="'+current.x+'" y="'+(current.y+34)+'" text-anchor="middle">'+escape(clock(latest.met_hours)+' · '+percent(latest.progress))+'</text></svg>';
  }
  function render(state, sourceLink) {
    state=state||initial();
    const pending=state.state!=='current', payload=state.data;
    const link=(path,label,ref=state.ref)=>sourceLink?sourceLink(path,label,ref):escape(label);
    let html='<div class="pagetop"><span class="eyebrow">Capcom / Apollo 11</span><h1 class="pagetitle">Mission</h1><p>The original Earth-to-Moon view, refreshed from the published research generation. The first step represents every modeled order ready for human review.</p></div><div class="section-head"><span class="sectionhead">Flight status</span><button class="inlinebtn" id="refresh">Refresh from GitHub</button></div><div class="mission-notice '+(pending?'pending':'')+'" role="status"><strong>'+(pending?'Pending mission publication':'Matching published generation')+'</strong><p>'+escape(state.message)+'</p><small>Last check: '+escape(date(state.checked_utc))+(payload?' · Displayed tracker: '+escape(date(payload.tracker_generation.finished_utc)):'')+'</small></div>';
    if(!payload)return html+'<section class="panel mission-empty"><h2>Awaiting a verified flight</h2><p>No matching mission generation is available yet. The existing production views continue to show their loaded tracker generation.</p><p>'+link(PATHS.mission,'Mission publication','main')+' · '+link(PATHS.tracker_status,'Tracker receipt','main')+'</p></section>';
    const latest=payload.latest,model=payload.model;
    html+='<section class="mission-hero '+(pending?'mission-retained':'')+'"><div class="mission-heading"><div class="eyebrow">'+(pending?'Last verified flight / retained':'Published flight')+'</div><h2>'+escape(latest.phase)+'</h2><p>'+escape(clock(latest.met_hours))+' of '+escape(clock(model.first_step_hours))+' to the first step</p></div>'+flight(payload)+'<p class="mission-caption">'+(pending?'Retained checkpoint: ':'Tracker checkpoint: ')+escape(date(payload.tracker_generation.finished_utc))+'. Flight distance is a model of completed steps; the clock does not advance with elapsed wall time.</p></section>';
    html+='<div class="metrics mission-metrics">'+[['Effort-weighted progress',percent(latest.progress),'Frozen minutes per readiness step'],['Ready for human review',number(latest.ready_for_human_review),'Of '+number(latest.orders_in_census)+' admitted identities'],['Modeled order goal',number(latest.orders_goal),number(latest.orders_in_census)+' census + '+number(model.census_gap)+' frozen gap'],['Human-certified',number(state.human),'Published Stage 19 register · separate from the flight']].map(([label,value,note])=>'<div class="stat"><span class="statlabel">'+escape(label)+'</span><strong>'+escape(value)+'</strong><small>'+escape(note)+'</small></div>').join('')+'</div>';
    html+='<div class="lower"><section class="panel"><div class="kicker">Recorded checkpoints</div><h2>Flight log</h2><p class="small">Daily retained checkpoints plus the latest reported generation, under the same frozen model. Corrections can move progress backward.</p><div class="tablebox"><table><thead><tr><th>Checkpoint (UTC)</th><th>Phase</th><th>Clock</th><th>Work</th><th>Ready</th></tr></thead><tbody>'+[...payload.history].reverse().map(row=>'<tr><td>'+escape(row.date)+'</td><td>'+escape(row.phase)+'</td><td class="mono">'+escape(clock(row.met_hours))+'</td><td>'+percent(row.progress)+'</td><td>'+number(row.ready_for_human_review)+'</td></tr>').join('')+'</tbody></table></div></section><section class="panel mission-source"><div class="kicker">Meaning & provenance</div><h2>Read the instruments</h2><p>The weighted share counts completed readiness steps against completed and open steps, including the frozen census gap. It is a planning model, not a completion-date forecast.</p><p>Ready dossiers and independently human-certified whole histories remain separate. A missing published certification count is shown as Unknown.</p><dl><dt>Mission published</dt><dd>'+escape(date(payload.generated_utc))+'</dd><dt>Repository revision checked</dt><dd class="mono">'+escape(state.ref)+'</dd><dt>Tracker run input</dt><dd class="mono">'+escape(payload.tracker_generation.commit_run)+'</dd><dt>Readiness input tree</dt><dd class="mono">'+escape(payload.readiness_inputs?.git_tree || 'Unknown')+'</dd><dt>Model</dt><dd>'+escape(model.version)+'<br>'+escape(model.denominator_version)+'</dd></dl><p>'+link(PATHS.mission,'Mission data')+' · '+link(PATHS.tracker_status,'Tracker receipt')+' · '+link(PATHS.tracker,'Per-order readiness')+' · '+link(PATHS.weights,'Frozen weights')+' · '+link(PATHS.human_review,'Human-review register')+'</p><details class="detail"><summary>Generation sources & limits</summary><ul>'+Object.values(payload.sources).map(source=>'<li>'+link(source.path,source.path)+'<br><span class="mono">SHA-256 '+escape(source.sha256)+'</span></li>').join('')+'</ul>'+(payload.limits||[]).map(limit=>'<p>'+escape(limit)+'</p>').join('')+'</details></section></div>';
    return html;
  }
  return Object.freeze({PATHS,initial,hash,validate,reject,readinessTree,load,render,clock,flight});
});
