'use strict';
// Inspect only visible navigation controls; never inspect or fill credential values.
const normalize=t=>String(t||'').replace(/\s+/g,' ').trim().toLowerCase();
const patterns={
 'new-session':/^begin a new session$/,
 'institution':/^(?:(?:log|sign) in (?:through|via) )?(?:your (?:library or )?institution|institution)$/,
 'nyu':/^(?:nyu librar(?:y|ies)|new york university(?: librar(?:y|ies))?)$/
};
function visible(el){return !!(el.getClientRects().length&&!el.disabled&&getComputedStyle(el).visibility!=='hidden'&&getComputedStyle(el).display!=='none');}
function candidates(kind){return [...document.querySelectorAll('a,button,input[type="button"],input[type="submit"],[role="button"]')].filter(el=>visible(el)&&patterns[kind].test(normalize(el.innerText||el.value||el.getAttribute('aria-label'))));}
function observation(){
 const text=normalize(document.body?.innerText);
 if(/too many requests|rate limit|unusual activity|access temporarily blocked|verify (?:that )?you are human|captcha/.test(text))return {kind:'blocked'};
 if([...document.querySelectorAll('input[type="password"]')].some(visible))return {kind:'login'};
 for(const kind of ['new-session','nyu']){const n=candidates(kind).length;if(n>1)return {kind:'ambiguous'};if(n===1)return {kind};}
 if(/we seem to have encountered a problem|your session (?:has|may have) ended/.test(text))return {kind:'error'};
 if(location.hostname==='congressional.proquest.com'&&(/legislative\s*(?:&|and)\s*executive publications|search by number/.test(text)||(/advanced search/.test(text)&&!!document.querySelector('input[type="search"],input[name*="query" i],input[name*="search" i]'))))return {kind:'ready'};
 const institutions=candidates('institution');if(institutions.length>1)return {kind:'ambiguous'};if(institutions.length===1)return {kind:'institution'};
 return {kind:'unknown'};
}
let scanning=false;
async function scan(){if(scanning||document.visibilityState==='prerender')return;scanning=true;
 try{const o=observation(),answer=await chrome.runtime.sendMessage({type:'observe',...o});if(answer?.click&&patterns[answer.click]){const els=candidates(answer.click);if(els.length===1){if(els[0].tagName==='A')els[0].target='_self';els[0].click();}}}catch{}finally{scanning=false;}
}
setInterval(scan,1500);scan();
