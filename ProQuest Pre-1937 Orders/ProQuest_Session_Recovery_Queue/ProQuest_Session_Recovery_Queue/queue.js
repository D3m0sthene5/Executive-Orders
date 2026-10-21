
'use strict';
const ROWS=JSON.parse(document.getElementById('inventory').textContent);
const KEY='proquest-resumable-queue-v2',VALID=new Set(['pending','requesting','saved','needs-review','unavailable','no-link']);
const $=id=>document.getElementById(id);let folder=null,running=false,busy=false,popup=null,lastRequest=0,pendingId=null;
let state={version:2,records:{}};
try{const s=JSON.parse(localStorage.getItem(KEY));if(s?.version===2&&s.records)state=s;}catch{}
for(const r of ROWS){const v=state.records[r.id];if(!v||!VALID.has(v.status))state.records[r.id]={status:r.pdf?'pending':'no-link'};else if(v.status==='requesting'){v.status='needs-review';v.message='Previous session ended during this request. Recheck the folder before retrying.';}}
const record=r=>state.records[r.id];
let recoveryUntil=0,recoveryRetry=false,consecutiveFailures=0;
async function extensionMessage(message){const tab=await chrome.tabs.getCurrent();const reply=await chrome.runtime.sendMessage({...message,queueTabId:tab.id});if(reply?.error)throw Error(reply.error);return reply;}
chrome.runtime.onMessage.addListener(message=>{if(message.type!=='recovery-status'||message.rowId!==pendingId||!running)return;
 say(message.message);
 if(message.phase==='recovering')recoveryUntil=Date.now()+600000;
 if(message.phase==='retry-ready')recoveryRetry=true;
 if(message.phase==='order-error'){state.records[pendingId]={...state.records[pendingId],status:'needs-review',message:message.message};persist();}
 if(message.phase==='paused'){state.records[pendingId]={...state.records[pendingId],status:'needs-review',message:message.message};persist();stop(message.message);}
});

function persist(){try{localStorage.setItem(KEY,JSON.stringify(state));}catch{stop('Progress could not be saved in this browser. Export a checkpoint before continuing.');throw Error('Checkpoint storage unavailable');}}
function say(s){$('status').textContent=s;}
function stop(message){extensionMessage({type:'deactivate'}).catch(()=>{});running=false;$('pause').disabled=true;$('problem').disabled=true;$('start').disabled=!folder||busy;if(message)say(message);}
function render(){
 const saved=ROWS.filter(r=>record(r).status==='saved').length, attention=ROWS.filter(r=>['needs-review','unavailable','no-link'].includes(record(r).status)).length;
 $('counts').textContent=`${saved.toLocaleString()} PDFs saved · ${ROWS.filter(r=>record(r).status==='pending').length.toLocaleString()} pending · ${attention} need attention`;
 $('progress').value=saved;const q=$('query').value.trim().toUpperCase(),filter=$('filter').value;
 const view=ROWS.filter(r=>(!q||r.n.toUpperCase().startsWith(q))&&(filter==='all'||(filter==='review'?['needs-review','unavailable','no-link'].includes(record(r).status):record(r).status===filter)));
 $('rows').replaceChildren();for(const r of view){const tr=document.createElement('tr'),rec=record(r);tr.className=rec.status==='saved'?'saved':rec.status==='pending'?'':'error';
  for(const value of ['EO '+r.n,r.y??'Unknown',rec.status==='saved'?`PDF saved: ${rec.file}`:rec.status+(rec.message?' — '+rec.message:'')]){const td=document.createElement('td');td.textContent=value;tr.append(td);}
  const td=document.createElement('td');const assoc=document.createElement('button');assoc.textContent='Associate saved PDF';assoc.disabled=busy||running;assoc.onclick=()=>associate(r);td.append(assoc);
  const mark=document.createElement('button');mark.textContent=rec.status==='unavailable'?'Return to pending':'Mark unavailable';mark.disabled=busy||running||!r.pdf;mark.onclick=()=>{state.records[r.id]={status:rec.status==='unavailable'?'pending':'unavailable'};persist();render();};td.append(mark);
  if(rec.status==='needs-review'){const retry=document.createElement('button');retry.textContent='Retry on next start';retry.disabled=running||busy;retry.onclick=()=>{state.records[r.id]={status:'pending'};persist();render();};td.append(retry);}
  if(r.rec){const a=document.createElement('a');a.textContent='Record';a.href=r.rec;a.target='_blank';a.rel='noopener';td.append(a);}
  tr.append(td);$('rows').append(tr);
 }
}
function matchName(r,name){if(!r.y)return false;return new RegExp('^PT1-'+r.y+'-EO-'+r.n+'(?: \\(\\d+\\))?\\.pdf$','i').test(name);}
async function inspect(file){
 if(file.size<32)throw Error('File is too small to be a complete PDF');
 const head=await file.slice(0,1024).text(),tail=await file.slice(Math.max(0,file.size-4096)).text();
 if(!head.startsWith('%PDF-')||!tail.includes('%%EOF'))throw Error('PDF header or end marker missing; file may be an error page or incomplete');
 const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await file.arrayBuffer()))).map(x=>x.toString(16).padStart(2,'0')).join('');
 return {file:file.name,size:file.size,modified:file.lastModified,sha256:hash,checkedAt:new Date().toISOString(),check:'PDF header and EOF markers; document identity unreviewed'};
}
async function directoryFiles(){const entries=[];for await(const [name,h] of folder.entries())if(h.kind==='file')entries.push([name,h]);return entries;}
async function findSaved(r,entries){
 const old=record(r);const candidates=entries.filter(([name])=>matchName(r,name)||name===old.file);let lastError=null;
 for(const [name,h] of candidates){try{const meta=await inspect(await h.getFile());if(!matchName(r,name)&&old.sha256&&meta.sha256!==old.sha256)continue;const duplicate=ROWS.find(other=>other.id!==r.id&&record(other).status==='saved'&&record(other).sha256===meta.sha256);if(duplicate&&!old.association){lastError=Error('This PDF has the same contents as saved EO '+duplicate.n+'. Inspect it before associating it with another order.');continue;}return meta;}catch(e){lastError=e;}}
 return {error:lastError?.message};
}
async function reconcile(){
 const entries=await directoryFiles();let checked=0;
 for(const r of ROWS){const meta=await findSaved(r,entries),old=record(r);if(meta.sha256){state.records[r.id]={...old,...meta,status:'saved'};checked++;}else if(old.status==='saved'){state.records[r.id]={...old,status:'needs-review',message:meta.error||'Previously saved PDF was not found in this folder. It will not be downloaded again unless you explicitly request a retry.'};}else if(meta.error){state.records[r.id]={...old,status:'needs-review',message:meta.error};}}
 persist();render();return checked;
}
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function processQueue(){
 busy=true;$('start').disabled=true;$('folder').disabled=true;$('scan').disabled=true;$('import').disabled=true;$('pause').disabled=false;render();
 try{
  say('Checking existing files before resuming…');await reconcile();
  while(running){
   const r=ROWS.find(r=>r.pdf&&record(r).status==='pending');if(!r){stop('No linked pending orders remain. Review the orders needing attention.');break;}
   const seconds=Math.max(12,Number($('interval').value)||12);while(running&&Date.now()-lastRequest<seconds*1000){say('Waiting before the next request…');await wait(500);}if(!running)break;
   
   state.records[r.id]={status:'requesting',requestedAt:new Date().toISOString()};pendingId=r.id;$('problem').disabled=false;persist();render();say('Requesting EO '+r.n+'; waiting for its saved PDF. Recognized session errors will trigger recovery automatically.');
   lastRequest=Date.now();recoveryUntil=0;recoveryRetry=false;await extensionMessage({type:'request-pdf',rowId:r.id,pdf:r.pdf});
   let deadline=Date.now()+120000,saved=false;
   while(running&&record(r).status==='requesting'&&Date.now()<Math.max(deadline,recoveryUntil)){await wait(1500);if(!running)break;const meta=await findSaved(r,await directoryFiles());if(meta.sha256){state.records[r.id]={...record(r),...meta,status:'saved'};persist();render();saved=true;pendingId=null;$('problem').disabled=true;break;}if(meta.error){state.records[r.id]={...record(r),status:'needs-review',message:meta.error};persist();stop('EO '+r.n+': saved file needs inspection. Do not press Back in the ProQuest tab.');break;}if(recoveryRetry){
     while(running&&Date.now()-lastRequest<12000)await wait(500);if(!running)break;
     recoveryRetry=false;recoveryUntil=0;lastRequest=Date.now();await extensionMessage({type:'retry-recovered',rowId:r.id});deadline=Date.now()+120000;
     say('Session recovery completed. Retrying EO '+r.n+' once; waiting for its PDF…');
    }}
   if(!saved&&record(r).status==='requesting'){state.records[r.id]={...record(r),status:'needs-review',message:running?'No matching completed PDF appeared within two minutes.':'Paused during this request; recheck folder before retrying.'};persist();if(running)stop('Paused at EO '+r.n+'. Do not press Back. Inspect the download tab for login, an error, or an unexpected filename.');}
   pendingId=null;
   consecutiveFailures=saved?0:consecutiveFailures+1;
   if(consecutiveFailures>=3)stop('Three consecutive orders failed. Queue paused to avoid repeatedly requesting broken links or an expired session.');
  }
 }catch(e){if(pendingId&&record(ROWS.find(r=>r.id===pendingId)).status==='requesting'){state.records[pendingId].status='needs-review';state.records[pendingId].message='Interrupted: '+e.message;try{persist();}catch{}}stop('Paused: '+e.message);}
 finally{await extensionMessage({type:'deactivate'}).catch(()=>{});running=false;busy=false;pendingId=null;$('start').disabled=!folder;$('pause').disabled=true;$('problem').disabled=true;$('folder').disabled=false;$('scan').disabled=!folder;$('import').disabled=false;render();}
}
async function associate(r){
 try{if(!window.showOpenFilePicker)throw Error('Use current desktop Chrome for file selection.');const [h]=await showOpenFilePicker({multiple:false,types:[{description:'PDF',accept:{'application/pdf':['.pdf']}}]});const f=await h.getFile(),meta=await inspect(f);
  if(!folder)throw Error('Choose the download folder first.');const same=await folder.getFileHandle(f.name);if(!(await same.isSameEntry(h)))throw Error('Select a file inside your chosen download folder.');
  if(!confirm(`Associate ${f.name} with EO ${r.n}? Inspect the PDF to confirm it is the correct order.`))return;
  state.records[r.id]={...meta,status:'saved',association:'user-confirmed filename association'};persist();render();
 }catch(e){if(e.name!=='AbortError')say(e.message);}
}
$('folder').onclick=async()=>{try{if(!window.showDirectoryPicker)throw Error('Folder access is unavailable. Download this HTML and open it directly in current desktop Chrome.');folder=await showDirectoryPicker({mode:'read',id:'proquest-orders',startIn:'downloads'});$('foldername').textContent=folder.name;$('start').disabled=true;$('scan').disabled=true;say('Checking PDFs already in this folder…');busy=true;render();const n=await reconcile();say(`Folder ready. Found ${n} saved PDFs. Press Start / resume to begin requests.`);}catch(e){if(e.name!=='AbortError')say(e.message);}finally{busy=false;$('start').disabled=!folder;$('scan').disabled=!folder;render();}};
$('scan').onclick=async()=>{busy=true;$('start').disabled=true;$('scan').disabled=true;render();try{const n=await reconcile();say('Folder checked: '+n+' PDFs found.');}catch(e){say('Folder check failed: '+e.message);}finally{busy=false;$('start').disabled=!folder;$('scan').disabled=!folder;render();}};
$('start').onclick=()=>{
 if(!folder||busy)return;
 
 if(!navigator.locks){say('This browser cannot prevent concurrent queue runs. Open the file in current desktop Chrome.');return;}
 running=true;busy=true;$('start').disabled=true;
 navigator.locks.request('proquest-pdf-queue',{ifAvailable:true},async lock=>{if(!lock){running=false;busy=false;$('start').disabled=false;say('Another queue is active. Pause it before starting this one.');return;}await processQueue();}).catch(e=>{running=false;busy=false;$('start').disabled=!folder;say(e.message);});
};
$('pause').onclick=()=>stop('Pausing. An already requested download may still finish; recheck the folder before resuming.');
$('problem').onclick=()=>{if(pendingId){state.records[pendingId]={...state.records[pendingId],status:'needs-review',message:'ProQuest error reported. No automatic retry. Inspect the record or resolve the login issue before explicitly retrying.'};persist();}stop('Paused after a ProQuest error. Do not press Back. The affected order is flagged for attention; Start / resume continues with other pending orders.');render();};
function exportState(){const blob=new Blob([JSON.stringify({...state,exportedAt:new Date().toISOString()},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='proquest-queue-checkpoint.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);}
$('export').onclick=exportState;$('import').onclick=()=>$('importfile').click();
$('importfile').onchange=async e=>{try{const f=e.target.files[0];if(!f)return;const s=JSON.parse(await f.text());if(s.version!==2||!s.records||typeof s.records!=='object')throw Error('Unsupported checkpoint');let n=0;for(const r of ROWS){const v=s.records[r.id];if(v&&VALID.has(v.status)){const clean={};for(const k of ['status','file','size','modified','sha256','checkedAt','check','association','requestedAt','message'])if(['string','number'].includes(typeof v[k]))clean[k]=v[k];if(clean.status==='requesting')clean.status='needs-review';state.records[r.id]=clean;n++;}}persist();if(folder)await reconcile();render();say(`Imported ${n} records. Saved files are rechecked before any requests.`);}catch(err){say('Import failed: '+err.message);}finally{e.target.value='';}};
$('query').oninput=render;$('filter').onchange=render;
window.addEventListener('pagehide',()=>{extensionMessage({type:'deactivate'}).catch(()=>{});});
window.addEventListener('beforeunload',e=>{if(running||busy){e.preventDefault();e.returnValue='';}});
persist();render();
