async page => {
  // Journal list (Phase 5): home entry points + counts, the list modal's
  // three tabs (order, cards, photo grouping), ＋ Add photos → lightbox
  // editor, lake / trip / lightbox opened above the list and closing back to
  // it, browser back, drainage scoping (results row + chip), deep link, and
  // the Sync panel's photo status + "save all full-size". iPhone-sized
  // viewport, fresh harness on :8899 + fixtures on :8898 (tests/journal/run.sh).
  const BASE = 'http://127.0.0.1:8899';
  const FIXTURES = 'http://127.0.0.1:8898';
  const results = [];
  const ok = (name, cond, info) => results.push(`${cond ? 'PASS' : 'FAIL'}  ${name}${info !== undefined && !cond ? '  — ' + JSON.stringify(info) : ''}`);
  const ctx = page.context();
  await ctx.route(/olaf\.local|ts\.net/, r => r.abort());
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
  const fx = async (name, mimeType) => ({ name, mimeType, buffer: await (await page.request.get(FIXTURES + '/' + name)).body() });
  const state = () => page.evaluate(() => ({
    journal: isOpen('journal-modal'), lake: isOpen('lake-detail-modal'), trip: isOpen('trip-modal'), lb: lightbox.open,
    tab: journalView.tab, scope: journalView.drainage, hash: location.hash, hist: history.state && history.state.modal }));
  const texts = sel => page.evaluate(s => [...document.querySelectorAll(s)].map(c => c.textContent.replace(/\s+/g, ' ').trim()), sel);
  const homeCounts = () => page.evaluate(() => Object.fromEntries([...document.querySelectorAll('#home-journal [data-n]')].map(e => [e.dataset.n, e.textContent])));
  try {
  page.setDefaultTimeout(15000);   // a stuck step fails instead of hanging the suite
  await page.setViewportSize({ width: 390, height: 844 });
  await boot(page);

  ok('home: three journal buttons, no counts while empty',
     (await texts('#home-journal button')).join('|') === 'Photos|Trip reports|Future trips'.split('|').map((t, i) => ['📷 ', '🥾 ', '🧭 '][i] + t).join('|') &&
     Object.values(await homeCounts()).every(n => n === ''), await texts('#home-journal button'));

  // ---- seed trips (docs only) -------------------------------------------
  const ids = await page.evaluate(() => {
    const mk = (doc) => queueJournal('trip', { id: newJournalId('trip'), links: [], body: '', when: null, date: null, end_date: null, ...doc }).id;
    const t1 = mk({ title: 'Toomset + Amethyst w/ Ryan', planned: false, date: '2024-10-12', end_date: '2024-10-14', lakes: ['BR-25', 'BR-28'],
                    body: 'Hiked in from Christmas Meadows. Wind all afternoon, fish rising at dusk.' });
    const t2 = mk({ title: 'Norway Flats day', planned: false, date: '2026-09-20', lakes: ['A-14'] });
    const t3 = mk({ title: 'Highline loop', planned: true, when: 'summer 2027', lakes: ['G-15'] });
    const t4 = mk({ title: 'Provo plan', planned: true, lakes: ['P-60'] });
    return { t1, t2, t3, t4 };
  });
  await page.waitForTimeout(50);   // touch the second plan later, so "most recently updated" is unambiguous
  await page.evaluate(id => queueJournal('trip', { ...getJournalDoc('trip', id), when: 'fall 2027' }), ids.t4);

  // ---- Photos tab: ＋ Add photos → lightbox editor -----------------------
  await page.click('#home-journal [data-journal-tab="photos"]');
  let st = await state();
  ok('📷 Photos → journal modal on the Photos tab, #journal-photos, own history entry', st.journal && st.tab === 'photos' && st.hash === '#journal-photos' && st.hist === 'journal', st);
  ok('empty Photos tab says so', /No photos yet/.test(await page.textContent('#journal-body')));
  await page.locator('#journal-photo-input').setInputFiles([await fx('gps_be.jpg', 'image/jpeg'), await fx('screenshot.png', 'image/png')]);
  await page.waitForFunction(() => lightbox.open && lightbox.editing, null, { timeout: 20000 });
  const lbChips = await texts('#lb-info .jr-chip.suggest');
  ok('after adding: lightbox opens on the first new photo in edit mode, GPS suggests BR-28',
     (await page.textContent('#lb-count')) === '1 / 2' && lbChips.some(c => /BR-28 · 166 m/.test(c)), lbChips);
  ok('status line under the tabs', /Added 2 photos — tag the lakes in each/.test(await page.textContent('#journal-status')));
  await page.click('#lb-info [data-lb="tag"][data-ln="BR-28"]');
  await page.click('#lb-info [data-lb="save"]');
  const pids = await page.evaluate(() => {
    const all = journalList('photo');
    return { gps: all.find(p => p.taken).id, shot: all.find(p => !p.taken).id };
  });
  ok('tag saved on the GPS photo', (await page.evaluate(id => getJournalDoc('photo', id).lakes.join(), pids.gps)) === 'BR-28');
  await page.click('#lb-close');
  // The screenshot goes on trip 1 (untagged → scoped by the trip's lakes);
  // a doc-only photo (no image anywhere) on trip 2.
  pids.ghost = await page.evaluate(({ ids, pids }) => {
    queueJournal('photo', { ...getJournalDoc('photo', pids.shot), trip: ids.t1 });
    return queueJournal('photo', { id: newJournalId('photo'), trip: ids.t2, lakes: ['A-14'], caption: 'ghost', taken: '2026-09-20T10:00:00', w: 10, h: 10 }).id;
  }, { ids, pids });

  const groups = await page.evaluate(() => [...document.querySelectorAll('#journal-body .jl-group')].map(g => ({
    head: g.querySelector('.jl-group-h').textContent.replace(/\s+/g, ' ').trim(),
    ids: [...g.querySelectorAll('[data-jl="photo"]')].map(b => b.dataset.id) })));
  ok('Photos grouped newest first: trip 2 (Sep 2026) → trip 1 (Oct 12–14, 2024) → October 2024 (trip-less)',
     groups.length === 3 && /^Norway Flats day Sep 20, 2026 · 1 photo$/.test(groups[0].head) && groups[0].ids.join() === pids.ghost &&
     /^Toomset \+ Amethyst w\/ Ryan Oct 12–14, 2024 · 1 photo$/.test(groups[1].head) && groups[1].ids.join() === pids.shot &&
     /^October 2024 ?1 photo$/.test(groups[2].head) && groups[2].ids.join() === pids.gps, groups);
  ok('tab counts: Trips 2 · Planned 2 · Photos 3', (await texts('.jl-tabs .jl-n')).join() === '2,2,3', await texts('.jl-tabs .jl-n'));
  ok('home counts follow', JSON.stringify(await homeCounts()) === JSON.stringify({ photos: '3', trips: '2', planned: '2' }), await homeCounts());

  // Lightbox over the visible set, lake chip → lake above the list, × → list
  await page.click(`#journal-body [data-jl="photo"][data-id="${pids.gps}"]`);
  ok('photo → lightbox over all 3 in display order (3 / 3)', (await page.textContent('#lb-count')) === '3 / 3');
  await page.click('#lb-info [data-lb="lake"][data-ln="BR-28"]');
  st = await state();
  ok('lightbox lake chip → BR-28 above the list (list still open, #BR-28)', st.lake && st.journal && !st.lb && st.hash === '#BR-28', st);
  await page.click('#close-modal');
  await page.waitForTimeout(300);
  st = await state();
  ok('× on the lake → back on the list, #journal-photos, history entry again', !st.lake && st.journal && st.hash === '#journal-photos' && st.hist === 'journal', st);

  // ---- Trips tab ---------------------------------------------------------
  await page.click('.jl-tabs [data-jl-tab="trips"]');
  const cards = await page.evaluate(() => [...document.querySelectorAll('#journal-body .jl-card')].map(c => ({
    id: c.dataset.id, title: c.querySelector('.jl-title').textContent, sub: c.querySelector('.jr-sub').textContent,
    lakes: (c.querySelector('.jl-lakes') || {}).textContent || '', snippet: (c.querySelector('.jl-snippet') || {}).textContent || '',
    img: !!c.querySelector('img[data-pid]') })));
  ok('Trips tab: newest first, date · photo count, lake names, snippet, first-photo thumb',
     (await state()).hash === '#journal-trips' && cards.length === 2 && cards[0].id === ids.t2 && cards[1].id === ids.t1 &&
     cards[1].sub === 'Oct 12–14, 2024 · 1 photo' && /BR-25.*BR-28/.test(cards[1].lakes) && /^Hiked in from Christmas Meadows/.test(cards[1].snippet) && cards[1].img, cards);
  await page.click(`#journal-body .jl-card[data-id="${ids.t1}"]`);
  st = await state();
  ok('card → trip view above the list', st.trip && st.journal && st.hash === `#trip-${ids.t1}`, st);
  await page.click('#trip-content [data-tv="lake"][data-ln="BR-25"]');
  await page.click('#modal-back');
  st = await state();
  ok('trip → lake → ← → the trip again', st.trip && !st.lake && st.journal, st);
  await page.click('#trip-back');
  await page.waitForTimeout(300);
  st = await state();
  ok('← on the trip (nothing left to pop) → back on the list', !st.trip && st.journal && st.hash === '#journal-trips' && st.hist === 'journal', st);

  // Browser back from a trip lands on the list too
  await page.click(`#journal-body .jl-card[data-id="${ids.t2}"]`);
  await page.goBack();
  await page.waitForTimeout(300);
  st = await state();
  ok('browser back from a trip → the list', !st.trip && st.journal && st.hash === '#journal-trips', st);

  // ---- Planned tab -------------------------------------------------------
  await page.click('.jl-tabs [data-jl-tab="planned"]');
  const planned = await page.evaluate(() => [...document.querySelectorAll('#journal-body .jl-card')].map(c => c.dataset.id));
  ok('Planned tab: most recently updated first', planned.join() === [ids.t4, ids.t3].join(), planned);
  await page.click('#journal-body [data-jl="add-plan"]');
  ok('＋ Plan a trip → planned editor above the list', (await page.textContent('#trip-title')) === 'Plan a trip' && (await state()).journal);
  await page.click('#trip-cancel');
  await page.waitForTimeout(300);
  st = await state();
  ok('Cancel → back on the list, no new doc', !st.trip && st.journal && (await page.evaluate(() => journalList('trip').length)) === 4, st);

  // Back from the list closes it
  await page.goBack();
  await page.waitForTimeout(300);
  st = await state();
  ok('browser back on the list closes it', !st.journal && !st.hash, st);

  // ---- drainage scoping --------------------------------------------------
  await page.evaluate(() => showDrainageLakes('Bear River Drainage'));
  ok('Bear River view: "🥾 1 trip · 📷 2 photos" row (screenshot counts via its trip)',
     (await texts('#results-journal button')).join('|') === '🥾 1 trip|📷 2 photos', await texts('#results-journal button'));
  await page.click('#results-journal [data-journal-tab="photos"]');
  st = await state();
  ok('row → list scoped to Bear River, Photos tab, scope chip', st.journal && st.scope === 'Bear River Drainage' && st.tab === 'photos' &&
     /Bear River ✕/.test(await page.textContent('#journal-body [data-jl="unscope"]')) &&
     (await page.evaluate(() => document.querySelectorAll('#journal-body [data-jl="photo"]').length)) === 2 &&
     (await texts('.jl-tabs .jl-n')).join() === '1,,2', { st, n: await texts('.jl-tabs .jl-n') });
  await page.click('#journal-body [data-jl="unscope"]');
  ok('✕ on the chip → every drainage again', (await state()).scope === null && (await page.evaluate(() => document.querySelectorAll('#journal-body [data-jl="photo"]').length)) === 3);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
  ok('Escape closes the list', !(await state()).journal);

  await page.evaluate(() => showDrainageMap('Provo River Drainage'));
  // Let the smooth scroll settle.
  for (let last = -1, i = 0; i < 30; i++) {
    await page.waitForTimeout(200);
    const y = await page.evaluate(() => scrollY);
    if (y === last) break;
    last = y;
  }
  const provo = await page.evaluate(() => {
    const top = Math.round(document.getElementById('results-journal').getBoundingClientRect().top);
    return { row: [...document.querySelectorAll('#results-journal button')].map(b => b.textContent), top,
             atBottom: scrollY >= document.documentElement.scrollHeight - innerHeight - 1 };
  });
  ok('Provo map jump: "🥾 1 trip · 🧭 1 planned · 📷 1 photo" row, scrolled to the top of the screen (or as far as the page goes)',
     provo.row.join('|') === '🥾 1 trip|🧭 1 planned|📷 1 photo' && provo.top >= -2 && (provo.top < 40 || (provo.atBottom && provo.top < 200)), provo);
  await page.evaluate(() => showDrainageLakes('Ashley Creek Drainage'));
  ok('a drainage with nothing: row hidden', await page.evaluate(() => document.getElementById('results-journal').classList.contains('hidden')));
  await page.evaluate(() => showAllOnMap());
  ok('not a drainage view: row hidden', await page.evaluate(() => document.getElementById('results-journal').classList.contains('hidden')));

  // ---- Sync panel: photos ------------------------------------------------
  await page.evaluate(() => syncNow());
  await page.evaluate(() => refreshPendingUploads());
  ok('everything synced (pending 0)', (await page.evaluate(() => pendingCount())) === 0, await page.evaluate(() => pendingCount()));
  // Drop the GPS photo's full image from this device so "save all" has to fetch it back.
  await page.evaluate(id => mediaTx('blobs', 'readwrite', s => s.delete(id + ':f')), pids.gps);
  // Playwright's headless WebKit wedges the whole page on
  // pushManager.getSubscription() (real Safari doesn't); the panel's
  // notification line isn't under test here.
  await page.evaluate(() => { window.refreshNotifStatus = async () => {}; });
  await page.click('#sync-settings-link');
  await page.waitForFunction(() => /full-size/.test(document.getElementById('photos-status-line').textContent), null, { timeout: 5000 });
  ok('Sync panel: "3 photos · 1 full-size on this device"', (await page.textContent('#photos-status-line')) === '3 photos · 1 full-size on this device',
     await page.textContent('#photos-status-line'));
  ok('button offers the 2 missing', (await page.textContent('#photos-save-all-btn')) === 'Save all full-size photos offline (2)');
  await page.click('#photos-save-all-btn');
  await page.waitForFunction(() => /^Saved/.test(document.getElementById('photos-save-progress').textContent), null, { timeout: 15000 });
  ok('save all: fetched the GPS photo back, the image-less one reported', /^Saved 1 of 2; 1 couldn’t be downloaded/.test(await page.textContent('#photos-save-progress')),
     await page.textContent('#photos-save-progress'));
  await page.waitForFunction(() => /2 full-size/.test(document.getElementById('photos-status-line').textContent), null, { timeout: 5000 });
  ok('status line after: 2 full-size; full image back in IndexedDB',
     (await page.textContent('#photos-status-line')) === '3 photos · 2 full-size on this device' &&
     !!(await page.evaluate(id => getImage(id + ':f').then(b => !!b), pids.gps)));
  await page.click('#close-sync-modal');

  // ---- deep link ---------------------------------------------------------
  await page.evaluate(() => history.replaceState(null, '', '/#journal-planned'));
  await page.reload();
  await page.waitForFunction(() => document.body.classList.contains('loaded'), null, { timeout: 30000 });
  await page.waitForTimeout(500);
  st = await state();
  ok('deep link #journal-planned opens the list on Planned after a reload', st.journal && st.tab === 'planned' &&
     (await page.evaluate(() => document.querySelectorAll('#journal-body .jl-card').length)) === 2, st);
  } catch (e) { results.push('ERROR  ' + (e.stack || e)); }
  return results.join('\n');
}
