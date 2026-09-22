async page => {
  const BASE = 'http://127.0.0.1:8813';
  const results = [];
  const ok = async (name, cond, info) => { const l = `${cond ? 'PASS' : 'FAIL'}  ${name}${info !== undefined ? '  — ' + JSON.stringify(info) : ''}`; results.push(l); return page.request.get(`${BASE}/__ctl?log=` + encodeURIComponent(l)); };
  const ctl = async (q) => {
    // Control calls go through a separate context so an "offline" page can't block them.
    const r = await page.request.get(`${BASE}/__ctl?${q}`);
    return r.json();
  };
  const sleep = ms => page.waitForTimeout(ms);

  // Helpers evaluated in the page
  const cacheNames = () => page.evaluate(async () => (await caches.keys()).filter(n => n.startsWith('uintas-v')).sort());
  const dataKeysIn = (name) => page.evaluate(async (name) => {
    const c = await caches.open(name);
    return (await c.keys()).map(r => r.url).filter(u => u.includes('lakes_data.json'));
  }, name);
  const lakeCount = () => page.evaluate(() => (typeof lakes !== 'undefined' && lakes.length) || 0);
  const readyLine = async () => {
    await page.evaluate(() => runOfflineCheck({ show: true }));
    await page.waitForFunction(() => !/Checking|Repairing/.test(document.getElementById('offline-ready-line').textContent), null, { timeout: 15000 });
    return page.evaluate(() => document.getElementById('offline-ready-line').textContent);
  };
  const swLog = () => page.evaluate(async () => {
    const c = await caches.open('uintas-push-state');
    const r = await c.match('/__push__/swlog');
    return r ? (await r.json()).map(e => e.e + (e.d && e.d.error ? ' ' + e.d.error : '')) : [];
  });
  const waitLoaded = () => page.waitForFunction(() => document.body.classList.contains('loaded'), null, { timeout: 30000 });
  const waitControlled = () => page.waitForFunction(() => !!navigator.serviceWorker.controller, null, { timeout: 30000 });
  const waitActivated = () => page.waitForFunction(async () => {
    const reg = await navigator.serviceWorker.getRegistration();
    return !!(reg && reg.active && !reg.installing && !reg.waiting);
  }, null, { timeout: 30000 });

  // ---- 0. Clean slate ---------------------------------------------------
  await ctl('version=A&fail=&portal=0&offline=0');
  await page.goto(BASE + '/');
  await page.evaluate(async () => {
    const regs = await navigator.serviceWorker.getRegistrations();
    await Promise.all(regs.map(r => r.unregister()));
    await Promise.all((await caches.keys()).map(k => caches.delete(k)));
    await new Promise(res => { const r = indexedDB.deleteDatabase('uintas-data'); r.onsuccess = r.onerror = r.onblocked = res; });
    localStorage.clear();
  });

  // ---- A. First load online: precache completes, app works --------------
  await page.goto(BASE + '/');
  await waitLoaded();
  await waitControlled();
  await waitActivated();
  await sleep(1500);
  let names = await cacheNames();
  ok('A1 first load: one versioned cache uintas-vA', names.length === 1 && names[0] === 'uintas-vA', names);
  const nA = await lakeCount();
  ok('A2 lakes loaded online', nA > 500, nA);
  let line = await readyLine();
  ok('A3 Offline panel says Ready', /^✓ Ready for offline/.test(line), line);
  await sleep(2500);  // let saveDataCopy fire
  const idb = await page.evaluate(() => readDataCopy().then(c => !!(c && c.text)));
  ok('A4 IndexedDB backup copy written', idb);

  // ---- B. Refresh polls don't accumulate copies -------------------------
  await page.evaluate(async () => { for (let i = 0; i < 4; i++) { await refreshData(); await new Promise(r => setTimeout(r, 200)); } });
  await sleep(1500);
  const keys = await dataKeysIn('uintas-vA');
  ok('B1 exactly one lakes_data.json entry after 4 cache-busted polls', keys.length === 1, keys.map(k => k.replace(BASE, '')));

  // ---- C. Genuine offline reload works (connection dropped) -------------
  await ctl('offline=1');
  await page.reload();
  await waitLoaded();
  const nC = await lakeCount();
  ok('C1 offline reload: lakes loaded from cache', nC === nA, nC);
  const srcC = await page.evaluate(() => dataSource);
  ok('C2 data came via the worker', srcC === 'worker', srcC);
  await ctl('offline=0');

  // ---- D. THE TRAILHEAD SCENARIO: new version, precache fails -----------
  // A new worker script arrives (cache name B) but lakes_data.json can't be
  // fetched. The install must FAIL and leave A in charge.
  await page.reload();
  await waitLoaded();
  await ctl('version=B&fail=lakes_data.json');
  await page.evaluate(async () => { const reg = await navigator.serviceWorker.getRegistration(); await reg.update(); });
  await sleep(4000);
  names = await cacheNames();
  const ctrl = await page.evaluate(async () => {
    const reg = await navigator.serviceWorker.getRegistration();
    return { installing: !!reg.installing, waiting: !!reg.waiting, controller: navigator.serviceWorker.controller && navigator.serviceWorker.controller.scriptURL };
  });
  const logD = await swLog();
  ok('D1 failed precache did NOT create cache B, A intact', names.length === 1 && names[0] === 'uintas-vA', names);
  ok('D2 no worker installing/waiting after the failure', !ctrl.installing && !ctrl.waiting, ctrl);
  ok('D3 worker log records install:failed', logD.some(e => e.startsWith('install:failed')), logD.slice(-3));
  // Now go offline (as at the trailhead) and relaunch.
  await ctl('offline=1');
  await page.reload();
  await waitLoaded();
  const nD = await lakeCount();
  ok('D4 offline after the botched update: app still opens with all lakes', nD === nA, nD);
  await ctl('offline=0&fail=');

  // ---- E. The update completes once the connection is good --------------
  await page.reload();
  await waitLoaded();
  await page.evaluate(() => { window.confirm = () => true; });   // auto-accept "New version available?"
  await page.evaluate(async () => { const reg = await navigator.serviceWorker.getRegistration(); await reg.update(); });
  await sleep(1000);
  await page.waitForFunction(async () => (await caches.keys()).includes('uintas-vB'), null, { timeout: 30000 });
  await sleep(4000);   // reload-on-controllerchange + activate cleanup
  await waitLoaded();
  names = await cacheNames();
  ok('E1 good connection: version B installed, A cleaned up', names.length === 1 && names[0] === 'uintas-vB', names);
  line = await readyLine();
  ok('E2 Offline panel Ready on version B', /^✓ Ready for offline/.test(line), line);

  // ---- F. Captive portal must not poison the data cache -----------------
  await ctl('portal=1');
  await page.evaluate(() => refreshData());
  await sleep(2000);
  await ctl('portal=0');
  const stillJson = await page.evaluate(async () => {
    const r = await caches.match('lakes_data.json', { ignoreSearch: true });
    const t = await r.text();
    try { JSON.parse(t); return true; } catch (e) { return false; }
  });
  ok('F1 captive-portal HTML did not replace the cached JSON', stillJson);

  // ---- G. Exactly Jed's symptom: shell cached, data entry gone ----------
  await page.evaluate(async () => {
    for (const n of await caches.keys()) {
      const c = await caches.open(n);
      for (const req of await c.keys()) if (req.url.includes('lakes_data.json')) await c.delete(req);
    }
  });
  await ctl('offline=1');
  await page.reload();
  await waitLoaded();
  const nG = await lakeCount();
  const srcG = await page.evaluate(() => dataSource);
  ok('G1 data entry lost + offline: app opens from the IndexedDB backup', nG === nA && srcG === 'idb', { lakes: nG, source: srcG });
  await sleep(9000);   // startup self-check (8s) — offline, so it must warn
  const chip = await page.evaluate(() => ({ cls: document.getElementById('offline-chip').className, txt: document.getElementById('offline-chip').textContent }));
  ok('G2 header warns that the offline copy is incomplete', !/hidden/.test(chip.cls) && /incomplete/.test(chip.txt), chip.txt);
  line = await readyLine();
  ok('G3 Offline panel says Not ready, names the missing file', /Not ready.*lakes_data\.json/.test(line), line);
  // Back online → Repair fixes it.
  await ctl('offline=0');
  await page.evaluate(() => runOfflineCheck({ show: true, repair: true }));
  await page.waitForFunction(() => /^✓ Ready/.test(document.getElementById('offline-ready-line').textContent), null, { timeout: 30000 });
  line = await page.evaluate(() => document.getElementById('offline-ready-line').textContent);
  const chip2 = await page.evaluate(() => document.getElementById('offline-chip').className);
  ok('G4 Repair restores Ready and clears the warning', /^✓ Ready/.test(line) && /hidden/.test(chip2), line);

  // ---- H. Everything gone except the shell, no backup: honest message ---
  await page.evaluate(async () => {
    for (const n of await caches.keys()) {
      const c = await caches.open(n);
      for (const req of await c.keys()) if (req.url.includes('lakes_data.json')) await c.delete(req);
    }
    await new Promise(res => { const r = indexedDB.deleteDatabase('uintas-data'); r.onsuccess = r.onerror = r.onblocked = res; });
  });
  await ctl('offline=1');
  await page.reload();
  await page.waitForFunction(() => document.querySelector('#load-retry-btn'), null, { timeout: 30000 });
  const msg = await page.evaluate(() => document.querySelector('.not-loaded').innerText);
  ok('H1 with no copy anywhere the message is honest and offers retry', /no offline copy of it was found/.test(msg) && /Try again/.test(msg), msg.split('\n')[0]);
  await ctl('offline=0');
  await page.click('#load-retry-btn');
  await waitLoaded();
  ok('H2 Try again recovers once online', (await lakeCount()) === nA);

  return results.join('\n');
}
