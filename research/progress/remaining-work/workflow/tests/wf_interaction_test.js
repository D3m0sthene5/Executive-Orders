const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const OUT = process.argv[2];
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const results = [];
  const check = (name, ok, info = '') => results.push(`${ok ? 'PASS' : 'FAIL'} ${name}${info ? ' :: ' + info : ''}`);
  for (const w of [1280, 820, 390]) {
    const page = await browser.newPage({ viewport: { width: w, height: 900 }, deviceScaleFactor: 2 });
    const errs = [];
    page.on('pageerror', (e) => errs.push(e.message));
    page.on('console', (m) => m.type() === 'error' && !m.text().includes('404') && errs.push(m.text()));
    await page.goto('http://localhost:8765/index.html#workflow');
    await page.waitForFunction(() => window.__drawn, null, { timeout: 20000 });
    await page.waitForTimeout(400);
    const n = await page.locator('#wf-map .wf-node').count();
    check(`${w}: nodes rendered`, n === 79, `${n}`);
    check(`${w}: stage columns`, (await page.locator('#wf-map .wf-stage').count()) === 8);
    check(`${w}: flow arrows drawn`, (await page.locator('#wf-map svg.wf-overlay path.flow').count()) === 7);
    await page.screenshot({ path: `${OUT}/wf-${w}.png`, fullPage: true });
    // hover
    const lewis = page.locator('#wf-map .wf-node[data-id="lewis-originals"]');
    await lewis.hover(); await page.waitForTimeout(250);
    const hv = page.locator('#wf-hover');
    check(`${w}: hover card shows`, await hv.isVisible());
    check(`${w}: hover has Wikipedia link`, (await hv.locator('a[href*="wikipedia.org/wiki/Meriwether_Lewis"]').count()) === 1);
    if (w === 1280) await page.screenshot({ path: `${OUT}/wf-hover.png`, clip: await (async () => { const b = await page.locator('#wf-wrap').boundingBox(); return { x: b.x, y: b.y, width: b.width, height: Math.min(b.height, 900) }; })() });
    // click pins detail
    await lewis.click(); await page.waitForTimeout(250);
    const det = page.locator('#wf-detail');
    check(`${w}: click pins detail`, await det.isVisible());
    check(`${w}: detail aria-pressed`, (await lewis.getAttribute('aria-pressed')) === 'true');
    const txt = await det.innerText();
    check(`${w}: detail has catalog stats`, txt.toLowerCase().includes('catalog stats'));
    check(`${w}: detail source links pinned`, (await det.locator('a[href*="/blob/88cef0253ed735b2a6e612770f25f9148641ce93/"]').count()) > 0);
    if (w === 1280) await det.screenshot({ path: `${OUT}/wf-detail.png` });
    await page.keyboard.press('Escape'); await page.waitForTimeout(150);
    check(`${w}: Escape closes detail`, !(await det.isVisible()));
    // keyboard: focus a node and press Enter
    await page.locator('#wf-map .wf-node[data-id="norton"]').focus(); await page.keyboard.press('Enter'); await page.waitForTimeout(200);
    const nt = await det.innerText();
    check(`${w}: Enter pins (NORTON)`, nt.includes('Margaret Cross Norton'));
    check(`${w}: NORTON provenance date shown`, nt.includes('2026-10-20'));
    await page.keyboard.press('Escape');
    // search
    await page.fill('#wf-search', 'cruden'); await page.waitForTimeout(150);
    const cnt = await page.locator('#wf-count').innerText();
    const shown = await page.locator('#wf-map .wf-node:not(.dim)').count();
    check(`${w}: search narrows`, shown >= 1 && shown < 79, `${cnt}`);
    await page.fill('#wf-search', '');
    await page.click('.wf-filter button[data-wf="historical"]'); await page.waitForTimeout(150);
    const hist = await page.locator('#wf-map .wf-node:not(.dim)').count();
    check(`${w}: historical filter`, hist === 17, `${hist}`);
    await page.click('.wf-filter button[data-wf="proposed"]'); await page.waitForTimeout(100);
    check(`${w}: proposed filter`, (await page.locator('#wf-map .wf-node:not(.dim)').count()) === 1);
    await page.click('.wf-filter button[data-wf="all"]');
    // no horizontal page scroll
    const sw = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    check(`${w}: no horizontal scroll`, sw <= 1, `${sw}px`);
    // other tabs still draw
    for (const t of ['steps', 'effort', 'toolmap', 'apollo']) {
      await page.click(`#tab-${t}`); await page.waitForTimeout(300);
      check(`${w}: tab ${t} visible`, await page.locator(`#${t}`).isVisible());
    }
    check(`${w}: Mission still draws rocket`, (await page.locator('#flight svg').count()) === 1);
    check(`${w}: no page errors`, errs.length === 0, errs.slice(0, 3).join(' | '));
    await page.close();
  }
  // dark
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2 });
  await page.goto('http://localhost:8765/index-dark.html#workflow');
  await page.waitForFunction(() => window.__drawn, null, { timeout: 20000 });
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${OUT}/wf-dark.png`, fullPage: false });
  console.log(results.join('\n'));
  await browser.close();
})();
