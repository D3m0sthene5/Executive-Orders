'use strict';
// Only the tab opened by this extension's queue may perform recovery actions.
let chain=Promise.resolve();
const load=async()=>(await chrome.storage.session.get('active')).active;
const save=active=>chrome.storage.session.set({active});
const tell=async(s,message,phase)=>{try{await chrome.runtime.sendMessage({type:'recovery-status',rowId:s.rowId,message,phase});}catch{}};
async function pause(s,message){s.enabled=false;s.phase='paused';await save(s);await tell(s,message,'paused');}
async function leaveForReview(s,message){s.enabled=false;s.phase='order-error';await save(s);await tell(s,message,'order-error');}
function trustedUI(sender){return sender.url===chrome.runtime.getURL('queue.html');}
async function uiOwner(m,sender){if(!trustedUI(sender))return null;const id=sender.tab?.id??m.queueTabId;if(!Number.isInteger(id))return null;try{await chrome.tabs.get(id);return id;}catch{return null;}}
function validPDF(url){try{const u=new URL(url);return u.origin==='https://congressional.proquest.com'&&u.pathname.includes('/congressional/result/pqpresultpage.gispdfhitspanel.pdflink/');}catch{return false;}}
async function handle(m,sender){
 if(m.type==='request-pdf'){
  const owner=await uiOwner(m,sender);if(owner===null||!validPDF(m.pdf)||!/^EO:[A-Za-z0-9-]+$/.test(m.rowId))return {error:'Invalid queue request'};
  const old=await load();
  if(old?.enabled&&old.ownerTab!==owner)return {error:'Another queue tab is active. Pause it before starting this queue.'};
  const s={enabled:true,ownerTab:owner,tabId:old?.tabId,rowId:m.rowId,pdf:m.pdf,phase:'download',recoveryUsed:false,clicks:{}};
  if(s.tabId){try{await chrome.tabs.get(s.tabId);}catch{s.tabId=null;}}
  if(!s.tabId){const tab=await chrome.tabs.create({url:'about:blank',active:false});s.tabId=tab.id;}
  // Persist ownership before navigation, so the new document can safely identify itself.
  await save(s);await chrome.tabs.update(s.tabId,{url:s.pdf});return {ok:true};
 }
 if(m.type==='deactivate'){
  const s=await load(),owner=await uiOwner(m,sender);if(owner!==null&&s&&s.ownerTab===owner){s.enabled=false;await save(s);}return {ok:true};
 }
 if(m.type==='retry-recovered'){
  const s=await load(),owner=await uiOwner(m,sender);if(owner===null||!s?.enabled||s.ownerTab!==owner||s.rowId!==m.rowId||s.phase!=='retry-ready')return {error:'No recovered request is ready'};
  s.phase='retrying';await save(s);await chrome.tabs.update(s.tabId,{url:s.pdf});return {ok:true};
 }
 if(m.type!=='observe')return {};
 const s=await load();if(!s?.enabled||sender.tab?.id!==s.tabId)return {};
 let host;try{host=new URL(sender.url).hostname;}catch{return {};}
 if(!(host==='proquest.com'||host.endsWith('.proquest.com')))return {};
 if(m.kind==='blocked'){await pause(s,'ProQuest asks you to wait or shows an access challenge. Queue paused.');return {};}
 if(m.kind==='login'){await pause(s,'Complete the ProQuest/NYU sign-in yourself, then explicitly retry this order.');return {};}
 if(m.kind==='ambiguous'){await pause(s,'More than one institution control matched. Choose NYU manually, then retry this order.');return {};}
 if(m.kind==='new-session'){
  if(s.recoveryUsed&&s.phase!=='recovering'){await leaveForReview(s,'This order still errors after one session recovery. Leaving it for review and continuing with pending orders.');return {};}
  if(s.clicks['new-session'])return {};
  s.recoveryUsed=true;s.phase='recovering';s.started=Date.now();s.clicks['new-session']=true;await save(s);await tell(s,'Starting a new ProQuest session…','recovering');return {click:'new-session'};
 }
 if(s.phase!=='recovering'){
  if(m.kind==='error'){await leaveForReview(s,'ProQuest returned an error without a recognized session button. Leaving this order for review.');}
  return {};
 }
 if(Date.now()-s.started>600000){await pause(s,'Session recovery timed out. Inspect the ProQuest tab.');return {};}
 if(m.kind==='institution'||m.kind==='nyu'){
  if(s.clicks[m.kind])return {};
  s.clicks[m.kind]=true;await save(s);await tell(s,m.kind==='institution'?'Choosing institutional access…':'Choosing NYU Library…','recovering');return {click:m.kind};
 }
 if(m.kind==='ready'){
  s.phase='retry-ready';await save(s);await tell(s,'ProQuest returned to its search page. Retrying the interrupted order once…','retry-ready');return {};
 }
 return {};
}
chrome.runtime.onMessage.addListener((m,sender,reply)=>{
 if(m.type==='recovery-status')return false;
 chain=chain.catch(()=>{}).then(()=>handle(m,sender));chain.then(reply,e=>reply({error:e.message}));return true;
});
chrome.action.onClicked.addListener(async()=>{await chrome.tabs.create({url:chrome.runtime.getURL('queue.html')});});
chrome.tabs.onRemoved.addListener(tabId=>{chain=chain.catch(()=>{}).then(async()=>{const s=await load();if(s&&(tabId===s.ownerTab||tabId===s.tabId)){s.enabled=false;await save(s);await tell(s,'The queue or its download tab closed. Start / resume to continue.','paused');}});});
chrome.tabs.onUpdated.addListener((tabId,change)=>{
 if(!change.url)return;
 chain=chain.catch(()=>{}).then(async()=>{const s=await load();if(!s?.enabled||s.tabId!==tabId||s.phase!=='recovering')return;let u;try{u=new URL(change.url);}catch{return;}
  if(u.hostname==='nyu.edu'||u.hostname.endsWith('.nyu.edu'))await tell(s,'Waiting for NYU to return to ProQuest. Complete sign-in in the download tab if prompted; no credentials are entered by the helper.','recovering');
  else if(!u.hostname.endsWith('.proquest.com')&&u.hostname!=='proquest.com')await pause(s,'Session recovery left ProQuest. Complete the institution step manually, then retry this order.');
 });
});
