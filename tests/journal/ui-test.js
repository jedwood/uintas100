async page => {
  // Lake-modal journal UI (Phase 3): Junesucker source link, My Record's
  // "Older notes", Trips & photos card, ＋ Photo, photo lightbox, Links card.
  // iPhone-sized viewport, fresh harness on :8899 + fixtures on :8898
  // (started by tests/journal/run.sh). /api/link-title is mocked in the
  // page's fetch — the real endpoint needs the internet, and WebKit's
  // Playwright can't route requests from a service-worker-controlled page.
  const BASE = 'http://127.0.0.1:8899';
  const FIXTURES = 'http://127.0.0.1:8898';
  const results = [];
  const ok = (name, cond, info) => results.push(`${cond ? 'PASS' : 'FAIL'}  ${name}${info !== undefined && !cond ? '  — ' + JSON.stringify(info) : ''}`);
  const expected = await (await page.request.get(FIXTURES + '/expected.json')).json();
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
  const visible = sel => page.locator(sel).isVisible();
  const fx = async (name, mimeType) => ({ name, mimeType, buffer: await (await page.request.get(FIXTURES + '/' + name)).body() });
  try {
  await page.setViewportSize({ width: 390, height: 844 });
  await boot(page);
  await page.evaluate(() => {
    const realFetch = window.fetch;
    window.titleLookups = [];
    window.fetch = (url, opts) => {
      if (String(url).includes('/api/link-title?')) {
        window.titleLookups.push(String(url));
        // A real lookup takes a moment; the untitled-then-filled check relies on it.
        return new Promise(res => setTimeout(() => res(new Response(JSON.stringify({ title: 'Mocked page title' }),
                                                                    { headers: { 'Content-Type': 'application/json' } })), 700));
      }
      return realFetch(url, opts);
    };
  });

  // ---- date labels -------------------------------------------------------
  const labels = await page.evaluate(() => [
    tripDateLabel({ date: '2024-10-12', end_date: '2024-10-14' }),
    tripDateLabel({ date: '2024-09-30', end_date: '2024-10-02' }),
    tripDateLabel({ date: '2024-12-30', end_date: '2025-01-02' }),
    tripDateLabel({ date: '2024-10-12', end_date: null }),
    tripDateLabel({ planned: true, when: 'summer 2027' }),
    tripDateLabel({ planned: true, when: null }),
    photoTakenLabel('2024-10-13T09:41:07'), photoTakenLabel('2024-10-13T21:05'), photoTakenLabel('2024-10-13'),
    normalizeUrl('example.org/x'), normalizeUrl('ftp://x.org'), normalizeUrl('not a url'), prettyUrl('https://www.example.org/a/b/')]);
  ok('date / url helpers', JSON.stringify(labels) === JSON.stringify([
    'Oct 12–14, 2024', 'Sep 30 – Oct 2, 2024', 'Dec 30, 2024 – Jan 2, 2025', 'Oct 12, 2024',
    'Planned · summer 2027', 'Planned', 'Oct 13, 2024 · 9:41 AM', 'Oct 13, 2024 · 9:05 PM', 'Oct 13, 2024',
    'https://example.org/x', null, null, 'example.org/a/b']), labels);

  // ---- Junesucker source link + empty-lake pills -----------------------
  await page.evaluate(() => showLakeDetail('A-1'));
  const js = await page.evaluate(() => {
    const a = document.getElementById('js-source-link');
    const preview = document.querySelector('#js-notes');
    return { href: a && a.href, target: a && a.target, want: lakes.find(l => l.letter_number === 'A-1').junesucker_url,
             before: !!(a && preview && (a.compareDocumentPosition(preview) & Node.DOCUMENT_POSITION_FOLLOWING)),
             n: lakes.filter(l => l.junesucker_url).length };
  });
  ok('Junesucker card: "View original" link to the source page, above the notes', js.href === js.want && js.target === '_blank' && js.before && /junesucker\.com\/lakes\//.test(js.href), js);
  ok('40 lakes carry junesucker_url', js.n === 40, js.n);
  const empty = await page.evaluate(() => ({
    pills: [...document.querySelectorAll('#jr-cards .jr-pill')].map(b => b.textContent.trim()),
    cards: !!document.getElementById('jr-trips-card') || !!document.getElementById('jr-links-card') }));
  ok('unvisited lake: only the 4 action pills, no cards', empty.pills.join('|') === '＋ Photo|＋ Trip|＋ Plan|＋ Link' && !empty.cards, empty);

  // ---- My Record: Trip Reports textarea gone; old text read-only -------
  await page.evaluate(() => showLakeDetail('BR-25'));
  const rec = await page.evaluate(() => ({
    textarea: !!document.getElementById('edit-trip-reports'),
    older: [...document.querySelectorAll('#record-compact .text-sm.font-medium')].some(d => /^Older notes/.test(d.textContent.trim())),
    oldLabel: /Trip Reports/.test(document.getElementById('record-compact').textContent.replace('old Trip Reports', '')) }));
  ok('My Record: no Trip Reports editor; old text shown read-only as "Older notes"', !rec.textarea && rec.older && !rec.oldLabel, rec);

  // ---- Trips & photos card ---------------------------------------------
  const tripId = await page.evaluate(() => {
    const t = queueJournal('trip', { id: newJournalId('trip'), title: 'Toomset + Amethyst w/ Ryan', planned: false,
      date: '2024-10-12', end_date: '2024-10-14', when: null, body: '', lakes: ['BR-25', 'BR-28'], links: [] });
    queueJournal('trip', { id: newJournalId('trip'), title: 'Back for the big ones', planned: true, when: 'summer 2027', lakes: ['BR-28'] });
    return t.id;
  });
  const br25 = await page.evaluate(() => [...document.querySelectorAll('#jr-trips-card .jr-row')].map(r => r.textContent.replace(/\s+/g, ' ').trim()));
  ok('journalchange re-renders the open lake in place (BR-25 trip row appears)', br25.length === 1 && /Oct 12–14, 2024 · Toomset \+ Amethyst w\/ Ryan/.test(br25[0]) && /2 lakes/.test(br25[0]), br25);
  await page.evaluate(() => showLakeDetail('BR-28'));
  const br28 = await page.evaluate(() => ({
    rows: [...document.querySelectorAll('#jr-trips-card .jr-row')].map(r => r.textContent.replace(/\s+/g, ' ').trim()),
    pills: [...document.querySelectorAll('#jr-trips-card .jr-pill')].map(b => b.textContent.trim()),
    strip: !!document.querySelector('#jr-trips-card .jr-strip') }));
  ok('BR-28: taken trip first (🥾), then planned (🧭 Planned · summer 2027)', br28.rows.length === 2 && /^🥾/.test(br28.rows[0]) && /^🧭 Planned · summer 2027 · Back for the big ones/.test(br28.rows[1]), br28.rows);
  ok('card carries the pills (incl. ＋ Link while no links); no strip without photos', br28.pills.length === 4 && !br28.strip, br28);

  // ＋ Photo: two images (GPS JPEG + PNG screenshot) and an undecodable HEIC
  await page.locator('#jr-photo-input').setInputFiles([await fx('gps_be.jpg', 'image/jpeg'), await fx('screenshot.png', 'image/png')]);
  await page.waitForFunction(() => document.querySelectorAll('#jr-trips-card .jr-thumb img[data-media-state="ok"]').length === 2, null, { timeout: 15000 });
  const added = await page.evaluate(() => ({
    docs: (photosByLake.get('BR-28') || []).map(p => ({ trip: p.trip, lakes: p.lakes, taken: p.taken })),
    status: document.getElementById('jr-status').textContent }));
  ok('＋ Photo: 2 photo docs, tagged BR-28, no trip; thumbnails render', added.docs.length === 2 && added.docs.every(d => d.trip === null && d.lakes.join() === 'BR-28') && added.docs[0].taken === '2024-10-13T09:41:07' && /Added 2 photos/.test(added.status), added);
  await page.locator('#jr-photo-input').setInputFiles([await fx('not-an-image.heic', 'image/heic')]);
  await page.waitForFunction(() => /HEIC/.test(document.getElementById('jr-status').textContent), null, { timeout: 10000 });
  ok('＋ Photo: HEIC → friendly inline error', (await page.evaluate(() => (photosByLake.get('BR-28') || []).length)) === 2);

  // ---- Lightbox ----------------------------------------------------------
  await page.locator('#jr-trips-card .jr-thumb').first().click();
  await page.waitForFunction(() => document.getElementById('lb-img').dataset.level === 'f', null, { timeout: 10000 });
  const lb1 = await page.evaluate(() => {
    const img = document.getElementById('lb-img');
    const r = img.getBoundingClientRect();
    return { open: !document.getElementById('photo-lightbox').classList.contains('hidden'), count: document.getElementById('lb-count').textContent,
             src: img.src.slice(0, 5), w: img.naturalWidth, fits: r.width <= innerWidth && r.height > 100,
             maps: (document.getElementById('lb-maps') || {}).href || null,
             meta: document.querySelector('#lb-info .lb-meta').textContent.replace(/\s+/g, ' ').trim(),
             chips: [...document.querySelectorAll('#lb-info [data-lb="lake"]')].map(c => c.textContent.trim()) };
  });
  ok('lightbox: opens on the tapped photo, 1 / 2, full image swapped in, fits the screen', lb1.open && lb1.count === '1 / 2' && lb1.src === 'blob:' && lb1.w === 2048 && lb1.fits, lb1);
  ok('lightbox: taken date + 📍 Open in Maps at the sidecar location', /Oct 13, 2024 · 9:41 AM/.test(lb1.meta) && lb1.maps && lb1.maps.includes(`ll=${expected['gps_be.jpg'].lat},${expected['gps_be.jpg'].lng}`), lb1);
  ok('lightbox: lake chip for BR-28', lb1.chips.length === 1 && /BR-28/.test(lb1.chips[0]), lb1.chips);
  await page.click('#lb-next');
  const lb2 = await page.evaluate(() => ({ count: document.getElementById('lb-count').textContent, maps: !!document.getElementById('lb-maps'),
                                           next: document.getElementById('lb-next').disabled, prev: document.getElementById('lb-prev').disabled }));
  ok('lightbox: › steps to 2 / 2 (screenshot: no location link; › disabled at the end)', lb2.count === '2 / 2' && !lb2.maps && lb2.next && !lb2.prev, lb2);
  await page.keyboard.press('ArrowLeft');
  ok('lightbox: ← arrow key steps back', (await page.textContent('#lb-count')) === '1 / 2');

  // Edit: caption + a suggested nearby lake + a searched lake
  await page.click('#lb-info [data-lb="edit"]');
  const sugg0 = await page.evaluate(() => [...document.querySelectorAll('#lb-info .jr-chip.suggest')].map(c => c.dataset.ln));
  ok('edit: no suggestions while the only lake within 1.2 km (BR-28) is already tagged', sugg0.length === 0, sugg0);
  await page.fill('#lb-caption-input', 'Amethyst inlet');
  await page.click('#lb-info [data-lb="untag"][data-ln="BR-28"]');
  const sugg = await page.evaluate(() => [...document.querySelectorAll('#lb-info .jr-chip.suggest')].map(c => c.textContent.trim()));
  ok('edit: untagged BR-28 comes back as a GPS suggestion with its distance', sugg.length === 1 && /BR-28 · 166 m/.test(sugg[0]), sugg);
  await page.click('#lb-info .jr-chip.suggest[data-ln="BR-28"]');
  await page.fill('#lb-lake-search', 'g-15');
  await page.waitForSelector('#lb-lake-matches button');
  const firstMatch = await page.getAttribute('#lb-lake-matches button', 'data-ln');
  ok('edit: lake search ranks the exact designation first', firstMatch === 'G-15', firstMatch);
  await page.click('#lb-lake-matches button');
  ok('edit: caption survives re-rendering the tag chips', (await page.inputValue('#lb-caption-input')) === 'Amethyst inlet');
  await page.click('#lb-info [data-lb="save"]');
  const saved = await page.evaluate(() => {
    const p = photosByLake.get('BR-28')[0];
    return { caption: p.caption, lakes: p.lakes, shown: document.querySelector('#lb-info .lb-caption').textContent,
             chips: [...document.querySelectorAll('#lb-info [data-lb="lake"]')].map(c => c.dataset.ln) };
  });
  ok('edit: Save queues caption + tags; info view shows them', saved.caption === 'Amethyst inlet' && saved.lakes.join() === 'BR-28,G-15' && saved.shown === 'Amethyst inlet' && saved.chips.join() === saved.lakes.join(), saved);

  // Lake chip → that lake; ← walks back
  await page.click('#lb-info [data-lb="lake"][data-ln="G-15"]');
  const g15 = await page.evaluate(() => ({ lb: lightbox.open, title: document.getElementById('modal-title').textContent,
    thumbs: document.querySelectorAll('#jr-trips-card .jr-thumb').length }));
  ok('lake chip → lightbox closes, modal shows G-15 with the photo in its strip', !g15.lb && /G-15/.test(g15.title) && g15.thumbs === 1, g15);
  await page.click('#modal-back');
  ok('← returns to BR-28', /BR-28/.test(await page.textContent('#modal-title')));

  // Escape / backdrop close only the lightbox
  await page.locator('#jr-trips-card .jr-thumb').first().click();
  await page.keyboard.press('Escape');
  ok('Escape closes the lightbox, keeps the lake modal', !(await page.evaluate(() => lightbox.open)) && await visible('#lake-detail-modal'));
  await page.locator('#jr-trips-card .jr-thumb').first().click();
  await page.locator('#lb-stage').click({ position: { x: 5, y: 5 } });
  ok('tap outside the image closes the lightbox', !(await page.evaluate(() => lightbox.open)) && await visible('#lake-detail-modal'));

  // Delete (two taps) the screenshot
  await page.locator('#jr-trips-card .jr-thumb').nth(1).click();
  await page.click('#lb-info [data-lb="delete"]');
  const armed = await page.evaluate(() => ({ still: (photosByLake.get('BR-28') || []).length, text: document.querySelector('#lb-info [data-lb="delete"]').textContent }));
  ok('delete: first tap only arms', armed.still === 2 && /Tap again/.test(armed.text), armed);
  await page.click('#lb-info [data-lb="delete"]');
  const del = await page.evaluate(() => ({ n: (photosByLake.get('BR-28') || []).length, lb: lightbox.open, count: document.getElementById('lb-count').textContent,
                                           thumbs: document.querySelectorAll('#jr-trips-card .jr-thumb').length }));
  ok('delete: second tap tombstones it; lightbox stays on the remaining photo; strip updates', del.n === 1 && del.lb && del.count === '' && del.thumbs === 1, del);
  await page.click('#lb-close');

  // ---- Links -----------------------------------------------------------
  await page.click('#jr-trips-card [data-jr="add-link"]');
  ok('＋ Link opens the form with the URL field focused', await page.evaluate(() => document.activeElement && document.activeElement.id === 'lf-url'));
  await page.fill('#lf-url', 'not a url');
  await page.click('#lf-save');
  ok('bad URL → inline error, nothing saved', await visible('#lf-error') && (await page.evaluate(() => (linksByLake.get('BR-28') || []).length)) === 0);
  await page.fill('#lf-url', 'example.org/trail-guide');
  await page.waitForFunction(() => document.getElementById('lf-title').value === 'Mocked page title', null, { timeout: 5000 });
  const lookups = await page.evaluate(() => window.titleLookups);
  ok('title prefilled from the Mini\'s /api/link-title (normalized URL sent)', lookups.length === 1 && lookups[0] === 'http://127.0.0.1:8899/api/link-title?url=https%3A%2F%2Fexample.org%2Ftrail-guide', lookups);
  // A background journalchange must not wipe the open form
  await page.evaluate(() => queueJournal('trip', { ...journalList('trip').find(t => t.planned), title: 'Back for the big ones!' }));
  ok('open form survives a re-render', (await page.inputValue('#lf-url')) === 'example.org/trail-guide');
  await page.fill('#lf-note', 'Good beta on the\nupper basin');
  await page.click('#lf-save');
  const link1 = await page.evaluate(() => {
    const row = document.querySelector('#jr-links-card .jr-link');
    return { form: document.getElementById('jr-link-form').hidden, href: row && row.querySelector('a').href, target: row && row.querySelector('a').target,
             title: row && row.querySelector('.jr-link-title').textContent, host: row && (row.querySelector('.jr-host') || {}).textContent,
             note: row && row.querySelector('.jr-note').textContent,
             pills: [...document.querySelectorAll('#jr-trips-card .jr-pill')].map(b => b.textContent.trim()) };
  });
  ok('saved link row: title, host chip, note, opens https URL in a new tab', link1.form && link1.href === 'https://example.org/trail-guide' && link1.target === '_blank' && link1.title === 'Mocked page title' && link1.host === 'example.org' && link1.note === 'Good beta on the\nupper basin', link1);
  ok('＋ Link pill moves into the Links card once there are links', !link1.pills.includes('＋ Link') && await visible('#jr-links-card [data-jr="add-link"]'), link1.pills);
  await page.click('#jr-links-card [data-jr="edit-link"]');
  ok('edit form prefilled', (await page.inputValue('#lf-title')) === 'Mocked page title' && (await page.inputValue('#lf-url')) === 'https://example.org/trail-guide');
  await page.fill('#lf-title', '');
  await page.click('#lf-save');
  ok('untitled link shows host + path', (await page.textContent('#jr-links-card .jr-link-title')).trim() === 'example.org/trail-guide' && !(await page.$('#jr-links-card .jr-host')));
  await page.waitForFunction(() => (linksByLake.get('BR-28') || [])[0]?.title === 'Mocked page title', null, { timeout: 5000 });
  ok('…and the title is filled in afterwards in the background', true);
  await page.click('#jr-links-card [data-jr="edit-link"]');
  await page.click('#lf-delete');
  await page.click('#lf-delete');
  ok('delete link (two taps) → Links card gone', !(await page.$('#jr-links-card')) && (await page.evaluate(() => (linksByLake.get('BR-28') || []).length)) === 0);

  // ---- Everything reaches the server -----------------------------------
  await page.evaluate(() => syncNow());
  const srv = await (await page.request.get(BASE + '/api/user-data')).json();
  const live = k => srv.journal[k].filter(d => !d.deleted);
  ok('server: 2 trips, 1 live photo (+1 tombstone), link tombstoned, sidecar uploaded',
     live('trips').length === 2 && live('photos').length === 1 && srv.journal.photos.length === 2 &&
     srv.journal.links.length === 1 && srv.journal.links[0].deleted && live('photos')[0].caption === 'Amethyst inlet' &&
     Object.keys(srv.media_meta).length === 1 && (await page.evaluate(() => pendingCount())) === 0, srv.journal);
  } catch (e) { results.push('ERROR  ' + (e.stack || e)); }
  return results.join('\n');
}
