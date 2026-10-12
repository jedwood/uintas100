async page => {
  // Trip modal (Phase 4): new trip from a lake, editor (dates, lakes + GPS
  // suggestions, body, links, photos + tags), trip view, lake ↔ trip hops
  // and ←, deep link, planned trip + "Mark as done", edit (remove a photo),
  // Cancel discards new photos, delete trip keeping its photos. iPhone-sized
  // viewport, fresh harness on :8899 + fixtures on :8898 (tests/journal/run.sh).
  // /api/link-title is mocked in the page's fetch, as in ui-test.js.
  const BASE = 'http://127.0.0.1:8899';
  const FIXTURES = 'http://127.0.0.1:8898';
  const results = [];
  const ok = (name, cond, info) => results.push(`${cond ? 'PASS' : 'FAIL'}  ${name}${info !== undefined && !cond ? '  — ' + JSON.stringify(info) : ''}`);
  const ctx = page.context();
  await ctx.route(/olaf\.local|ts\.net/, r => r.abort());
  const mockTitles = () => page.evaluate(() => {
    if (window.titleLookups) return;
    const realFetch = window.fetch;
    window.titleLookups = [];
    window.fetch = (url, opts) => {
      if (String(url).includes('/api/link-title?')) {
        window.titleLookups.push(String(url));
        return new Promise(res => setTimeout(() => res(new Response(JSON.stringify({ title: 'Mocked page title' }),
                                                                    { headers: { 'Content-Type': 'application/json' } })), 300));
      }
      return realFetch(url, opts);
    };
  });
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
  const visible = sel => page.locator(sel).isVisible();
  const fx = async (name, mimeType) => ({ name, mimeType, buffer: await (await page.request.get(FIXTURES + '/' + name)).body() });
  const state = () => page.evaluate(() => ({
    lake: !document.getElementById('lake-detail-modal').classList.contains('hidden'),
    trip: !document.getElementById('trip-modal').classList.contains('hidden'),
    editing: document.getElementById('trip-modal').classList.contains('editing'),
    lakeTitle: document.getElementById('modal-title').textContent.trim(),
    tripTitle: document.getElementById('trip-title').textContent.trim(),
    hash: location.hash, cross: crossStack.map(e => e.type + ':' + e.id) }));
  const chips = sel => page.evaluate(s => [...document.querySelectorAll(s)].map(c => c.textContent.replace(/\s+/g, ' ').trim()), sel);
  try {
  await page.setViewportSize({ width: 390, height: 844 });
  await boot(page);
  await mockTitles();

  // ---- helpers -----------------------------------------------------------
  const al = await page.evaluate(() => autolinkHtml('See https://example.org/a/b. And (https://x.org/p) <b> & https://w.org/q_(1)'));
  ok('autolinkHtml: links URLs, keeps trailing punctuation as text, escapes the rest',
     al === 'See <a href="https://example.org/a/b" target="_blank" rel="noopener">example.org/a/b</a>. And (<a href="https://x.org/p" target="_blank" rel="noopener">x.org/p</a>) &lt;b&gt; &amp; <a href="https://w.org/q_(1)" target="_blank" rel="noopener">w.org/q_(1)</a>', al);

  // ---- ＋ Trip from a lake → editor ------------------------------------
  await page.evaluate(() => showLakeDetail('BR-25'));
  await page.click('#jr-cards [data-jr="add-trip"]');
  let st = await state();
  ok('＋ Trip: lake modal hidden, trip modal in editor mode, "New trip", hash #trip-t-…, lake on crossStack',
     !st.lake && st.trip && st.editing && st.tripTitle === 'New trip' && /^#trip-t-/.test(st.hash) && st.cross.join() === 'lake:BR-25', st);
  ok('editor: title focused, Taken selected, BR-25 prefilled',
     await page.evaluate(() => document.activeElement.id === 'te-title') &&
     (await page.textContent('.te-seg button.on')).includes('Taken') &&
     (await page.evaluate(() => tripEdit.lakes.join())) === 'BR-25' && (await chips('#te-lakes .jr-chip.on')).length === 1, await chips('#te-lakes .jr-chip'));
  ok('editor: Save/Cancel in the header; ← and × hidden', await visible('#trip-save') && await visible('#trip-cancel') && !(await visible('#trip-back')) && !(await visible('#trip-close')));

  // Validation: empty title
  await page.click('#trip-save');
  ok('Save without a title → inline error, still editing', await visible('#te-error') && (await state()).editing);
  await page.fill('#te-title', 'Toomset + Amethyst w/ Ryan');
  await page.fill('#te-date', '2024-10-14');
  await page.fill('#te-end', '2024-10-12');
  await page.click('#trip-save');
  ok('end date before start → error', /before the start/.test(await page.textContent('#te-error')) && (await state()).editing);
  await page.fill('#te-date', '2024-10-12');
  await page.fill('#te-end', '2024-10-14');

  // Photo with GPS near BR-28 → BR-28 suggested for the trip (and the photo)
  await page.locator('#te-photo-input').setInputFiles([await fx('gps_be.jpg', 'image/jpeg'), await fx('screenshot.png', 'image/png')]);
  await page.waitForFunction(() => document.querySelectorAll('#te-photos .te-photo img[data-media-state="ok"]').length === 2, null, { timeout: 15000 });
  const sugg = await chips('#te-lakes .jr-chip.suggest');
  ok('photo GPS → "＋ … BR-28 · 166 m" suggestion in the trip\'s lakes', sugg.length === 1 && /BR-28 · 166 m/.test(sugg[0]), sugg);
  await page.click('#te-lakes .jr-chip.suggest[data-ln="BR-28"]');
  ok('tap suggestion → BR-28 added', (await chips('#te-lakes .jr-chip.on')).length === 2 && !(await chips('#te-lakes .jr-chip.suggest')).length);
  const tagRows = await page.evaluate(() => [...document.querySelectorAll('#te-photos .te-tags')].map(r => [...r.querySelectorAll('[data-te="tag"]')].map(c => c.dataset.ln + (c.classList.contains('on') ? '+' : '-'))));
  ok('each photo offers the trip\'s lakes as off toggles', tagRows.length === 2 && tagRows.every(r => r.join() === 'BR-25-,BR-28-'), tagRows);
  const gpsPid = await page.evaluate(() => tripEdit.photos.find(p => mediaMeta[p.id]).id);
  await page.click(`#te-photos .te-tags[data-pid="${gpsPid}"] [data-ln="BR-28"]`);
  await page.fill(`[data-te-caption="${gpsPid}"]`, 'Amethyst from the inlet');
  // other lake… search on the same photo
  await page.click(`#te-photos [data-te="tag-other"][data-pid="${gpsPid}"]`);
  await page.fill(`[data-te-tag-search="${gpsPid}"]`, 'g-15');
  await page.click(`.te-tag-search[data-pid="${gpsPid}"] .te-matches button`);
  const gpsTags = await page.evaluate(id => tripEdit.photos.find(p => p.id === id).lakes, gpsPid);
  ok('photo tags: BR-28 toggled on + G-15 via "other lake…"; caption kept', gpsTags.join() === 'BR-28,G-15' &&
     (await page.inputValue(`[data-te-caption="${gpsPid}"]`)) === 'Amethyst from the inlet', gpsTags);

  // Lake search adds a lake to the trip
  await page.fill('#te-lake-search', 'br-29');
  await page.waitForSelector('#te-lake-matches button');
  await page.press('#te-lake-search', 'Enter');
  ok('lake search + Enter adds BR-29', (await page.evaluate(() => tripEdit.lakes)).join() === 'BR-25,BR-28,BR-29');
  await page.click('#te-lakes [data-te="lake-remove"][data-ln="BR-29"]');

  // Body + links
  await page.fill('#te-body', 'Hiked in from Christmas Meadows.\nMap: https://example.org/map.');
  await page.fill('#te-link-url', 'example.org/trip-beta');
  await page.waitForFunction(() => document.getElementById('te-link-title').value === 'Mocked page title', null, { timeout: 5000 });
  await page.click('[data-te="add-link"]');
  await page.fill('#te-link-url', 'https://example.org/second');   // left in the box: Save adds it
  await page.fill('#te-link-title', 'Second link');

  await page.click('#trip-save');
  st = await state();
  const tripId = await page.evaluate(() => currentTrip);
  const view = await page.evaluate(() => ({
    when: document.querySelector('.tv-when').textContent.trim(),
    lakes: [...document.querySelectorAll('#trip-content [data-tv="lake"]')].map(c => c.dataset.ln),
    bodyLink: (document.querySelector('.tv-body a') || {}).href, body: document.querySelector('.tv-body').textContent,
    thumbs: document.querySelectorAll('.tv-grid .tv-thumb').length,
    links: [...document.querySelectorAll('#tv-links .jr-link-title')].map(x => x.textContent.trim()),
    btns: [...document.querySelectorAll('#trip-content .jr-btn')].map(b => b.textContent.trim()) }));
  ok('Save → trip view: title, 🥾 Oct 12–14, 2024, lake chips', !st.editing && st.tripTitle === 'Toomset + Amethyst w/ Ryan' && view.when === '🥾 Oct 12–14, 2024' && view.lakes.join() === 'BR-25,BR-28', { st, view });
  ok('trip view: body with its URL autolinked (trailing "." stays text), 2 photos, 2 links, Edit only (not planned)',
     view.bodyLink === 'https://example.org/map' && /Christmas Meadows\.\nMap: example\.org\/map\.$/.test(view.body) && view.thumbs === 2 &&
     view.links.join('|') === 'Mocked page title|Second link' && view.btns.join() === 'Edit', view);
  const docs = await page.evaluate(id => ({ trip: getJournalDoc('trip', id), photos: (photosByTrip.get(id) || []).map(p => ({ trip: p.trip, lakes: p.lakes, caption: p.caption })) }), tripId);
  ok('trip doc: dates, lakes, body, links (normalized URL)', docs.trip.date === '2024-10-12' && docs.trip.end_date === '2024-10-14' && !docs.trip.planned &&
     docs.trip.links.map(l => l.url).join() === 'https://example.org/trip-beta,https://example.org/second' && docs.trip.body.startsWith('Hiked in'), docs.trip);
  ok('photo docs: both point at the trip; tags/caption as edited', docs.photos.length === 2 && docs.photos.every(p => p.trip === tripId) &&
     docs.photos.some(p => p.lakes.join() === 'BR-28,G-15' && p.caption === 'Amethyst from the inlet') && docs.photos.some(p => !p.lakes.length), docs.photos);

  // ---- navigation --------------------------------------------------------
  await page.click('#trip-content [data-tv="lake"][data-ln="BR-28"]');
  st = await state();
  ok('lake chip → BR-28 lake modal (trip hidden, trip on crossStack)', st.lake && !st.trip && /BR-28/.test(st.lakeTitle) && st.cross.join() === `lake:BR-25,trip:${tripId}` && st.hash === '#BR-28', st);
  const br28 = await page.evaluate(() => ({ rows: [...document.querySelectorAll('#jr-trips-card .jr-row')].length, thumbs: document.querySelectorAll('#jr-trips-card .jr-thumb').length }));
  ok('BR-28 shows the trip row and the one photo tagged BR-28', br28.rows === 1 && br28.thumbs === 1, br28);
  await page.click('#modal-back');
  st = await state();
  ok('← from BR-28 → back to the trip', st.trip && !st.lake && st.tripTitle === 'Toomset + Amethyst w/ Ryan' && st.hash === `#trip-${tripId}`, st);
  await page.click('#trip-back');
  st = await state();
  const br25rows = await chips('#jr-trips-card .jr-row');
  ok('← from the trip → BR-25 again, its card now lists the trip', st.lake && !st.trip && /BR-25/.test(st.lakeTitle) && !st.cross.length && br25rows.length === 1 && /Oct 12–14, 2024 · Toomset/.test(br25rows[0]), { st, br25rows });
  await page.click('#jr-trips-card [data-jr="trip"]');
  ok('trip row in the lake card → trip view', (await state()).trip);

  // Lightbox over the trip: "From trip" stays; lake chip hops to the lake
  await page.click('.tv-grid .tv-thumb >> nth=0');
  await page.waitForFunction(() => lightbox.open && document.getElementById('lb-img').dataset.level, null, { timeout: 10000 });
  ok('photo → lightbox over the trip\'s photos (1 / 2)', (await page.textContent('#lb-count')) === '1 / 2');
  await page.click('#lb-info [data-lb="trip"]');
  st = await state();
  ok('"From trip" on the open trip just closes the lightbox', !(await page.evaluate(() => lightbox.open)) && st.trip, st);
  await page.locator(`.tv-grid img[data-pid="${gpsPid}"]`).click();
  await page.click('#lb-info [data-lb="lake"][data-ln="G-15"]');
  st = await state();
  ok('lightbox lake chip over a trip → G-15, ← returns to the trip', st.lake && /G-15/.test(st.lakeTitle) && !st.trip, st);
  await page.click('#modal-back');
  ok('…back on the trip', (await state()).trip);

  // Escape closes the whole stack; browser back too
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
  st = await state();
  ok('Escape on the trip view closes everything', !st.trip && !st.lake && !st.hash, st);

  // ---- deep link ---------------------------------------------------------
  await page.evaluate(() => syncNow());
  await page.evaluate(id => history.replaceState(null, '', '/#trip-' + id), tripId);
  await page.reload();
  await page.waitForFunction(() => document.body.classList.contains('loaded'), null, { timeout: 30000 });
  await page.waitForTimeout(500);
  await mockTitles();
  st = await state();
  ok('deep link #trip-<id> opens the trip after a reload', st.trip && st.tripTitle === 'Toomset + Amethyst w/ Ryan', st);
  await page.goBack();
  await page.waitForTimeout(300);
  st = await state();
  ok('browser back closes it', !st.trip && !st.lake, st);

  // ---- planned trip + Mark as done --------------------------------------
  await page.evaluate(() => showLakeDetail('BR-28'));
  await page.click('#jr-trips-card [data-jr="add-plan"]');
  ok('＋ Plan → editor titled "Plan a trip", Planned selected, "when" field', (await state()).tripTitle === 'Plan a trip' &&
     (await page.textContent('.te-seg button.on')).includes('Planned') && await visible('#te-when') && !(await page.$('#te-date')));
  await page.fill('#te-title', 'Back for the big ones');
  await page.fill('#te-when', 'summer 2027');
  await page.click('#trip-save');
  const planId = await page.evaluate(() => currentTrip);
  const pv = await page.evaluate(() => ({ when: document.querySelector('.tv-when').textContent.trim(),
    btns: [...document.querySelectorAll('#trip-content .jr-btn')].map(b => b.textContent.trim()) }));
  ok('planned trip view: 🧭 Planned · summer 2027, Edit + ✓ Mark as done', pv.when === '🧭 Planned · summer 2027' && pv.btns.join('|') === 'Edit|✓ Mark as done', pv);
  await page.click('[data-tv="mark-done"]');
  ok('Mark as done: date form, prefilled with today', await visible('#tv-done') && /^\d{4}-\d\d-\d\d$/.test(await page.inputValue('#tv-done-date')));
  await page.fill('#tv-done-date', '2027-07-20');
  await page.fill('#tv-done-end', '2027-07-19');
  await page.click('[data-tv="done-save"]');
  ok('…end before start → error', await visible('#tv-done-error'));
  await page.fill('#tv-done-end', '2027-07-22');
  await page.click('[data-tv="done-save"]');
  const done = await page.evaluate(id => ({ doc: getJournalDoc('trip', id), when: document.querySelector('.tv-when').textContent.trim() }), planId);
  ok('…saved: planned=false, dates set, "when" cleared, view shows 🥾 Jul 20–22, 2027', !done.doc.planned && done.doc.date === '2027-07-20' &&
     done.doc.end_date === '2027-07-22' && done.doc.when === null && done.when === '🥾 Jul 20–22, 2027', done);
  await page.click('#trip-back');
  const br28rows = await chips('#jr-trips-card .jr-row');
  ok('← back to BR-28: both trips, newest first', br28rows.length === 2 && /Jul 20–22, 2027/.test(br28rows[0]) && /Oct 12–14, 2024/.test(br28rows[1]), br28rows);

  // ---- edit: remove a photo (undo, then again), Cancel discards new ones ---
  await page.click('#jr-trips-card [data-jr="trip"] >> nth=1');
  await page.click('[data-tv="edit"]');
  ok('Edit → editor titled "Edit trip" with the saved values', (await state()).tripTitle === 'Edit trip' &&
     (await page.inputValue('#te-title')) === 'Toomset + Amethyst w/ Ryan' && (await page.inputValue('#te-end')) === '2024-10-14' &&
     (await page.$$('#te-links .te-link-row')).length === 2 && (await page.$$('#te-photos .te-photo')).length === 2);
  const shotPid = await page.evaluate(() => tripEdit.photos.find(p => !mediaMeta[p.id]).id);
  await page.click(`[data-te="photo-remove"][data-pid="${shotPid}"]`);
  ok('remove saved photo → "will be deleted" row with Undo', /will be deleted/.test(await page.textContent(`.te-photo.removed[data-pid="${shotPid}"]`)));
  await page.click(`[data-te="photo-undo"][data-pid="${shotPid}"]`);
  ok('Undo brings it back', !(await page.$('.te-photo.removed')));
  await page.click(`[data-te="photo-remove"][data-pid="${shotPid}"]`);
  await page.click('#te-links [data-te="link-remove"][data-i="1"]');
  await page.fill('#te-links [data-te-link-title="0"]', 'Trip beta');
  await page.click('#trip-save');
  const edited = await page.evaluate(id => ({ links: getJournalDoc('trip', id).links, photos: (photosByTrip.get(id) || []).map(p => p.id) }), tripId);
  ok('Save: removed photo tombstoned, link removed, link title edited', edited.photos.join() === gpsPid &&
     edited.links.length === 1 && edited.links[0].title === 'Trip beta' && (await page.evaluate(id => !getJournalDoc('photo', id), shotPid)), edited);

  // Cancel on an edit with a freshly added photo: its blobs go
  await page.click('[data-tv="edit"]');
  await page.locator('#te-photo-input').setInputFiles([await fx('gps_le.jpg', 'image/jpeg')]);
  await page.waitForFunction(() => tripEdit && tripEdit.photos.some(p => p.isNew), null, { timeout: 15000 });
  const newPid = await page.evaluate(() => tripEdit.photos.find(p => p.isNew).id);
  await page.fill('#te-title', 'changed but cancelled');
  await page.click('#trip-cancel');
  await page.waitForTimeout(300);
  const cancelled = await page.evaluate(async ([tid, pid]) => ({
    title: getJournalDoc('trip', tid).title, viewTitle: document.getElementById('trip-title').textContent,
    blob: await getImage(pid + ':f').catch(() => 'err'), doc: getJournalDoc('photo', pid) }), [tripId, newPid]);
  ok('Cancel: nothing saved, back to the view, new photo\'s blobs discarded', cancelled.title === 'Toomset + Amethyst w/ Ryan' &&
     cancelled.viewTitle === cancelled.title && !cancelled.blob && !cancelled.doc, cancelled);

  // Cancel on a NEW trip returns to where it was opened from
  await page.click('#trip-back');
  await page.click('#jr-trips-card [data-jr="add-trip"]');
  await page.click('#trip-cancel');
  st = await state();
  ok('Cancel on a new trip → back to the lake, no doc', st.lake && !st.trip && /BR-28/.test(st.lakeTitle) &&
     (await page.evaluate(() => journalList('trip').length)) === 2, st);

  // ---- delete trip, keep its photos ------------------------------------
  await page.click('#jr-trips-card [data-jr="trip"] >> nth=1');
  await page.click('[data-tv="edit"]');
  await page.click('[data-te="delete"]');
  ok('Delete on a trip with photos asks: delete photos too, or keep them', await visible('[data-te="delete-all"]') && await visible('[data-te="delete-keep"]'));
  await page.click('[data-te="delete-keep"]');
  st = await state();
  const after = await page.evaluate(([tid, pid]) => ({ trip: getJournalDoc('trip', tid), photo: getJournalDoc('photo', pid),
    rows: document.querySelectorAll('#jr-trips-card .jr-row').length, thumbs: document.querySelectorAll('#jr-trips-card .jr-thumb').length }), [tripId, gpsPid]);
  ok('keep photos: trip tombstoned, photo unattached but still on BR-28; back on the lake', st.lake && !st.trip && !after.trip &&
     after.photo && after.photo.trip === null && after.photo.lakes.join() === 'BR-28,G-15' && after.rows === 1 && after.thumbs === 1, { st, after });

  // ---- everything reaches the server -----------------------------------
  await page.evaluate(() => syncNow());
  const srv = await (await page.request.get(BASE + '/api/user-data')).json();
  const live = k => srv.journal[k].filter(d => !d.deleted);
  ok('server: 1 live trip (marked done), tombstoned trip, 1 live unattached photo, pending 0',
     live('trips').length === 1 && live('trips')[0].id === planId && !live('trips')[0].planned &&
     srv.journal.trips.some(t => t.id === tripId && t.deleted) && live('photos').length === 1 && live('photos')[0].trip === null &&
     (await page.evaluate(() => pendingCount())) === 0, srv.journal);

  // ---- month-only dates (old reports: "2024 Oct", day unknown) ----------
  const labels = await page.evaluate(() => [['2024-10', null], ['2024-07', '2024-08'], ['2024-12', '2025-01'], ['2024-10', '2024-10']]
    .map(([date, end_date]) => tripDateLabel({ planned: false, date, end_date })));
  ok('tripDateLabel month-only: "Oct 2024" · "Jul–Aug 2024" · "Dec 2024 – Jan 2025" · same month = single',
     labels.join(' | ') === 'Oct 2024 | Jul–Aug 2024 | Dec 2024 – Jan 2025 | Oct 2024', labels);
  await page.evaluate(() => { hideModals(); openTripEditor(null, { lakes: ['A-18'] }); });
  await page.fill('#te-title', 'Month-only trip');
  await page.fill('#te-date', '2024-10-05');
  await page.check('#te-month-only');
  ok('Month only → inputs become YYYY-MM, day dropped', (await page.getAttribute('#te-date', 'type')) === 'month' &&
     (await page.inputValue('#te-date')) === '2024-10' && (await page.textContent('label[for="te-date"]')).trim() === 'Month');
  // Chromium's month picker can't hold a bad value; the text fallback
  // (desktop Safari/Firefox) can, so put one straight into the draft.
  await page.evaluate(() => { tripEdit.end_date = '2024-13'; });
  await page.click('#trip-save');
  ok('bad month → error, still editing', (await state()).editing && /YYYY-MM/.test(await page.textContent('#trip-content')));
  await page.fill('#te-end', '2024-11');
  await page.click('#trip-save');
  const mo = await page.evaluate(() => { const t = journalList('trip').find(x => x.title === 'Month-only trip'); return t && { id: t.id, date: t.date, end: t.end_date, when: document.querySelector('.tv-when').textContent.trim() }; });
  ok('saved as 2024-10 … 2024-11, view shows 🥾 Oct–Nov 2024', mo && mo.date === '2024-10' && mo.end === '2024-11' && mo.when === '🥾 Oct–Nov 2024', mo);
  await page.click('[data-tv="edit"]');
  ok('Edit reopens month-only (box checked, 2024-10)', await page.isChecked('#te-month-only') && (await page.inputValue('#te-date')) === '2024-10');
  await page.uncheck('#te-month-only');
  ok('uncheck → exact-day inputs prefilled with the 1st', (await page.getAttribute('#te-date', 'type')) === 'date' &&
     (await page.inputValue('#te-date')) === '2024-10-01' && (await page.inputValue('#te-end')) === '2024-11-01');
  await page.click('#trip-cancel');
  await page.evaluate(() => syncNow());
  const srvMo = (await (await page.request.get(BASE + '/api/user-data')).json()).journal.trips.find(t => t.id === mo.id);
  ok('server stored the month-only dates', srvMo && srvMo.date === '2024-10' && srvMo.end_date === '2024-11' &&
     (await page.evaluate(() => pendingCount())) === 0, srvMo);
  } catch (e) { results.push('ERROR  ' + (e.stack || e)); }
  return results.join('\n');
}
