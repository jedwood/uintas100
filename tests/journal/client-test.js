async page => {
  // Journal client data layer (index.html), end to end against a fresh
  // edits-server harness on :8899 and the fixture server on :8898 — both
  // started by tests/journal/run.sh. Device A = this page; device B = a
  // fresh context (separate storage).
  const BASE = 'http://127.0.0.1:8899';
  const FIXTURES = 'http://127.0.0.1:8898';
  const results = [];
  const ok = (name, cond, info) => results.push(`${cond ? 'PASS' : 'FAIL'}  ${name}${info !== undefined && !cond ? '  — ' + JSON.stringify(info) : ''}`);
  const expected = await (await page.request.get(FIXTURES + '/expected.json')).json();

  // Never let a test reach the LIVE edits server.
  const guard = async ctx => ctx.route(/olaf\.local|ts\.net/, r => r.abort());

  // First visit: the service worker installs, claims the page and the app
  // reloads itself on controllerchange — let that settle before testing.
  const boot = async (p) => {
    await p.goto(BASE + '/');
    await p.evaluate(b => localStorage.setItem('uintas-sync-url', b), BASE);
    for (let i = 0; i < 40; i++) {
      try { if (await p.evaluate(() => !!navigator.serviceWorker.controller)) break; } catch (e) { /* mid-reload */ }
      await p.waitForTimeout(500);
    }
    await p.waitForTimeout(1000);
    await p.reload();
    await p.waitForFunction(() => document.body.classList.contains('loaded') && !!navigator.serviceWorker.controller, null, { timeout: 30000 });
  };
  try {
  const ctxA = page.context();
  await guard(ctxA);
  await boot(page);

  // ---- A: offline — queue docs and add photos --------------------------
  // WebKit's emulated offline also blocks File/Blob reads (they go through
  // its network process), so there photos are added online and only the
  // docs are queued offline. Chromium does the whole step offline.
  const isWebKit = page.context().browser().browserType().name() === 'webkit';
  if (!isWebKit) await ctxA.setOffline(true);
  // Reload with no sync server: truly offline in Chromium; in WebKit (which
  // can't do offline navigations in Playwright) online with /api/* blocked.
  const reloadDisconnected = async () => {
    if (isWebKit) { await ctxA.setOffline(false); await ctxA.route(/:8899\/api\//, r => r.abort()); }
    await page.reload();
    await page.waitForFunction(() => document.body.classList.contains('loaded'), null, { timeout: 30000 });
    if (isWebKit) { await ctxA.unroute(/:8899\/api\//); await ctxA.setOffline(true); }
  };
  await page.evaluate(() => {
    const inp = document.createElement('input');
    inp.type = 'file'; inp.multiple = true; inp.id = 'test-files'; inp.accept = 'image/*';
    document.body.appendChild(inp);
  });
  // Bytes, not paths: WebKit can't re-read path-based test files (sandbox).
  const fx = async (name, mimeType) => ({ name, mimeType, buffer: await (await page.request.get(FIXTURES + '/' + name)).body() });
  await page.locator('#test-files').setInputFiles([await fx('gps_be.jpg', 'image/jpeg'), await fx('gps_le.jpg', 'image/jpeg'),
                                                   await fx('screenshot.png', 'image/png'), await fx('not-an-image.heic', 'image/heic')]);
  const added = await page.evaluate(async () => {
    const out = [];
    for (const f of document.getElementById('test-files').files) {
      try { out.push({ name: f.name, ...(await addPhotoFile(f)) }); }
      catch (e) { out.push({ name: f.name, error: e.message }); }
    }
    return out;
  });
  const [be, le, png, heic] = added;
  if (added.some(a => a.error && !/heic/i.test(a.name))) results.push('DEBUG  ' + JSON.stringify(added.map(a => a.error || 'ok')));
  ok('gps_be: sidecar lat/lng/alt/make/model/taken/gps_time match ImageIO-verified values',
     be.sidecar && ['lat', 'lng', 'alt', 'make', 'model', 'taken', 'gps_time'].every(k => be.sidecar[k] === expected['gps_be.jpg'][k]), be.sidecar);
  ok('gps_le (little-endian TIFF): sidecar matches', le.sidecar && ['lat', 'lng', 'alt', 'make', 'model', 'taken', 'gps_time'].every(k => le.sidecar[k] === expected['gps_le.jpg'][k]), le.sidecar);
  ok('gps_be: taken from DateTimeOriginal', be.taken === '2024-10-13T09:41:07', be.taken);
  ok('gps_be: nearest suggested lake is BR-28 (≈150 m)', be.nearLakes.length && be.nearLakes[0].letter_number === 'BR-28' && be.nearLakes[0].km < 0.3, be.nearLakes);
  ok('gps_le: G-15 suggested', le.nearLakes.some(x => x.letter_number === 'G-15'), le.nearLakes);
  ok('4000×3000 → full 2048×1536', be.w === 2048 && be.h === 1536, [be.w, be.h]);
  ok('PNG screenshot: no sidecar, no taken, no suggestions', png.sidecar === null && png.taken === null && png.nearLakes.length === 0 && png.w === 800, png);
  ok('undecodable HEIC → friendly error', heic.error && /HEIC/.test(heic.error), heic);
  ok('ids match the server pattern', [be, le, png].every(x => /^p-[a-z0-9]+-[a-z0-9]{4}$/.test(x.id)));
  const thumbDims = await page.evaluate(async id => {
    const b = await getImage(id + ':t');
    const bmp = await createImageBitmap(b);
    return [bmp.width, bmp.height, b.type];
  }, be.id);
  ok('thumb ≤ 480 px JPEG', thumbDims[0] === 480 && thumbDims[1] === 360 && thumbDims[2] === 'image/jpeg', thumbDims);

  if (isWebKit) await ctxA.setOffline(true);
  const ids = await page.evaluate(({ be, le, png }) => {
    const trip = queueJournal('trip', { id: newJournalId('trip'), title: 'Toomset + Amethyst w/ Ryan', planned: false,
      date: '2024-10-12', end_date: '2024-10-14', when: null, body: 'Test trip', lakes: ['BR-25', 'BR-28'],
      links: [{ url: 'https://example.com/trail', title: 'Trail' }] });
    const plan = queueJournal('trip', { id: newJournalId('trip'), title: 'Someday', planned: true, when: 'summer 2027', lakes: ['G-15'] });
    queueJournal('photo', { id: be.id, trip: trip.id, lakes: [be.nearLakes[0].letter_number], caption: 'Amethyst', taken: be.taken, w: be.w, h: be.h });
    queueJournal('photo', { id: le.id, trip: null, lakes: ['G-15'], caption: '', taken: le.taken, w: le.w, h: le.h });
    queueJournal('photo', { id: png.id, trip: trip.id, lakes: [], caption: 'map screenshot', taken: null, w: png.w, h: png.h });
    const link = queueJournal('link', { id: newJournalId('link'), lake: 'BR-29', url: 'https://example.com/b', title: 'B', note: '' });
    const bad = queueJournal('link', { id: newJournalId('link'), lake: 'BR-29', url: 'ftp://nope', title: '', note: '' });
    return { trip: trip.id, plan: plan.id, link: link.id, bad: bad.id };
  }, { be, le, png });
  await page.evaluate(() => refreshPendingUploads());
  const offlineState = await page.evaluate((tripId) => ({
    pending: pendingCount(), pj: pendingJournal().length, up: pendingUploads,
    chip: document.getElementById('sync-chip').textContent,
    byLake: (tripsByLake.get('BR-28') || []).map(t => t.title),
    photosBR28: (photosByLake.get('BR-28') || []).length,
    photosTrip: (photosByTrip.get(tripId) || []).length,
    stored: Object.keys(JSON.parse(localStorage.getItem('uintas-local-journal'))).length
  }), ids.trip);
  ok('offline: 7 docs + 3 uploads pending, chip says 10 changes', offlineState.pj === 7 && offlineState.up === 3 && offlineState.pending === 10 && /10 changes pending/.test(offlineState.chip), offlineState);
  ok('offline: indices — trip on BR-28, photo tagged BR-28, 2 photos on the trip', offlineState.byLake[0] === 'Toomset + Amethyst w/ Ryan' && offlineState.photosBR28 === 1 && offlineState.photosTrip === 2, offlineState);
  ok('offline: pending docs persisted to localStorage', offlineState.stored === 7, offlineState);

  // Offline reload keeps the queue (app shell from the SW).
  await reloadDisconnected();
  ok('offline reload: queue + indices survive', await page.evaluate(() => pendingJournal().length === 7 && (tripsByLake.get('BR-25') || []).length === 1));

  // ---- A: back online → sync ------------------------------------------
  await ctxA.setOffline(false);
  await page.evaluate(() => syncNow());
  const afterSync = await page.evaluate(() => ({
    pending: pendingCount(), pj: pendingJournal().length, up: pendingUploads, rejected: rejectedJournal().map(e => e.error),
    status: (refreshSyncModalStatus(), document.getElementById('sync-status-line').textContent),
  }));
  ok('sync: nothing pending afterwards (uploads + docs)', afterSync.pending === 0 && afterSync.up === 0, afterSync);
  ok('sync: bad-url link rejected, kept, not retried, shown in panel', afterSync.rejected.length === 1 && /http/.test(afterSync.rejected[0]) && /1 change rejected/.test(afterSync.status), afterSync);
  const srv = await (await page.request.get(BASE + '/api/user-data')).json();
  ok('server journal: 2 trips, 3 photos, 1 link', srv.journal.trips.length === 2 && srv.journal.photos.length === 3 && srv.journal.links.length === 1, srv.journal);
  ok('server media_meta: sidecars for the 2 GPS photos only, matching values',
     Object.keys(srv.media_meta).length === 2 && srv.media_meta[be.id].lat === expected['gps_be.jpg'].lat && srv.media_meta[le.id].model === 'Pixel 8' && !srv.media_meta[png.id], srv.media_meta);
  // Re-encoding must leave no location/camera/time in the image files.
  // (Safari's encoder writes a tiny EXIF of its own — ColorSpace + pixel
  // dimensions — so "no Exif bytes at all" is not the right test.)
  for (const [id, suf] of [[be.id, '.jpg'], [be.id, '_t.jpg'], [le.id, '.jpg'], [png.id, '.jpg']]) {
    const r = await page.request.get(`${BASE}/api/media/${id}${suf}`);
    const buf = await r.body();
    const leaks = ['iPhone', 'Apple', 'Pixel', 'Google', '2024:10:13', '2020:08:0'].filter(t => buf.indexOf(t) !== -1);
    const parsed = await page.evaluate(arr => parseExif(new Uint8Array(arr).buffer), [...buf]);
    ok(`server ${id}${suf}: JPEG with no GPS / camera / timestamp`, r.status() === 200 && buf[0] === 0xff && buf[1] === 0xd8 &&
       !leaks.length && parsed.lat === undefined && !parsed.make && !parsed.taken, { status: r.status(), leaks, parsed });
  }

  // ---- B: a second device sees everything via /api/user-data -----------
  const ctxB = await page.context().browser().newContext();
  await guard(ctxB);
  const pageB = await ctxB.newPage();
  await boot(pageB);
  await pageB.evaluate(() => syncNow());
  await pageB.waitForFunction(n => journalList('photo').length === n, 3, { timeout: 10000 });
  const bState = await pageB.evaluate(({ be, le }) => ({
    trips: journalList('trip').map(t => t.title).sort(),
    br28: (photosByLake.get('BR-28') || []).map(p => p.caption),
    link: (linksByLake.get('BR-29') || []).map(l => l.url),
    loc: mediaMeta[be.id] && mediaMeta[be.id].lat,
    localPending: Object.keys(localJournal).length,
  }), { be, le });
  ok('B: sees both trips, the BR-28 photo, the BR-29 link, the private location', bState.trips.join('|') === 'Someday|Toomset + Amethyst w/ Ryan' && bState.br28[0] === 'Amethyst' && bState.link[0] === 'https://example.com/b' && bState.loc === expected['gps_be.jpg'].lat && bState.localPending === 0, bState);
  // background thumbnail prefetch lands in B's media store
  await pageB.waitForFunction(async n => (await mediaKeys('blobs')).filter(k => k.endsWith(':t')).length === n, 3, { timeout: 15000, polling: 500 });
  ok('B: background prefetch stored all 3 thumbnails', true);
  const hyd = await pageB.evaluate(async id => {
    const wrap = document.createElement('div');
    wrap.innerHTML = `<img data-pid="${id}" data-size="f" width="100"><img data-pid="p-nothere-zzzz" data-size="t" width="100">`;
    document.body.appendChild(wrap);
    hydrateMedia(wrap);
    await new Promise(r => setTimeout(r, 1500));
    const [a, b] = wrap.querySelectorAll('img');
    return { a: a.dataset.mediaState, aSrc: a.src.slice(0, 5), aW: a.naturalWidth, b: b.dataset.mediaState, bAlt: b.alt };
  }, be.id);
  ok('B: hydrateMedia fetches a full image from the Mini → blob: URL', hyd.a === 'ok' && hyd.aSrc === 'blob:' && hyd.aW === 2048, hyd);
  ok('B: unknown photo → offline placeholder', hyd.b === 'offline' && /offline/.test(hyd.bAlt), hyd);
  ok('B: full image now cached in IDB', await pageB.evaluate(async id => !!(await mediaGet('blobs', id + ':f')), be.id));

  // B edits the trip title (newer)
  await pageB.evaluate(id => { const t = getJournalDoc('trip', id); queueJournal('trip', { ...t, title: 'Renamed on B' }); return syncNow(); }, ids.trip);

  // ---- A: a stale local edit is superseded; a delete propagates ---------
  const sup = await page.evaluate(async id => {
    const t = getJournalDoc('trip', id);
    localJournal['trip:' + id] = { kind: 'trip', doc: { ...t, title: 'STALE from A', updated: '2020-01-01T00:00:00.000Z' }, synced: false };
    saveLocalJournal();
    await syncNow();
    return { title: getJournalDoc('trip', id).title, local: !!localJournal['trip:' + id] };
  }, ids.trip);
  ok('A: stale edit superseded → server copy (B\'s rename) wins, local dropped', sup.title === 'Renamed on B' && !sup.local, sup);

  await page.evaluate(async id => { deleteJournal('photo', id); await syncNow(); }, png.id);
  const delA1 = await page.evaluate(async id => ({ doc: getJournalDoc('photo', id), blob: !!(await mediaGet('blobs', id + ':f')) }), png.id);
  ok('A: deleted photo gone from indices', delA1.doc === null, delA1);
  const gone = await page.request.get(`${BASE}/api/media/${png.id}.jpg`);
  ok('server removed the deleted photo\'s files', gone.status() === 404, gone.status());
  await page.evaluate(() => syncNow());   // tombstone synced on the previous pass → blobs purged now
  const delA2 = await page.evaluate(async id => ({ f: !!(await mediaGet('blobs', id + ':f')), t: !!(await mediaGet('blobs', id + ':t')), m: !!(await mediaGet('meta', id)) }), png.id);
  ok('A: deleted photo\'s blobs + meta purged after the tombstone synced', !delA2.f && !delA2.t && !delA2.m, delA2);
  await pageB.evaluate(() => syncNow());
  const delB = await pageB.evaluate(id => ({ doc: getJournalDoc('photo', id), trip: (photosByTrip.get([...journalDocs.values()].find(d => d.title === 'Renamed on B').id) || []).length }), png.id);
  ok('B: delete propagated (photo gone, trip now has 1 photo)', delB.doc === null && delB.trip === 1, delB);

  // ---- A: offline reload still shows B's latest via the server snapshot --
  await ctxA.setOffline(true);
  await reloadDisconnected();
  ok('A offline reload: server snapshot keeps B\'s rename visible', await page.evaluate(id => getJournalDoc('trip', id).title === 'Renamed on B', ids.trip));
  const offImg = await page.evaluate(async id => {
    photoUrlCache.clear();
    const img = document.createElement('img'); img.dataset.pid = id; img.dataset.size = 't'; document.body.appendChild(img);
    hydrateMedia(document.body); await new Promise(r => setTimeout(r, 800));
    return img.dataset.mediaState;
  }, le.id);
  ok('A offline: own photo still renders from IDB', offImg === 'ok', offImg);
  await ctxA.setOffline(false);
  await ctxB.close();
  } catch (e) { results.push('ERROR  ' + (e.stack || e)); }
  return results.join('\n');
}
