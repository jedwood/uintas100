# Runbook: single-writer model, edits server, push notifications

How writes reach the database and how devices find out. Split out of
CLAUDE.md 2026-09-24; the text below is unchanged.

### Single-writer model (the Mac Mini writes; everything else is a client)
Exactly ONE machine — the Mac Mini — writes `uinta_lakes.db` and pushes. Every
other device is a **client of the published app**: since 2026-09-08 the MacBook
runs no clone and no Tauri shell at all — Jed uses a Dock-installed PWA (Safari
web app of the github.io page), exactly like the iPhone. A device "sees" a
change when the PWA picks up the new service-worker cache version after a push.
Any other clone that does exist (a dev checkout, say) is a **read-only mirror**:
it only `git pull`s and runs the app, and must never run a sync/fetch or commit
the DB. This removes the two-machine write-conflict class (e.g. the binary-DB
autostash conflicts).

- **Enforcement:** a gitignored `.db-readonly` marker in the repo root makes a
  clone a mirror. `fetch_latest_stocking.py`, `update_stocking.py`,
  `sync_notes_to_db.sh`, and `sync_notes_and_push.sh` call
  `writer_guard.exit_if_readonly()` (or the bash equivalent) and exit early when
  the marker exists — so even if a scheduler fires the job, it does nothing.
  Exception: on a mirror, `fetch_latest_stocking.py` runs `git pull --ff-only`
  instead (`writer_guard.pull_and_exit_if_readonly()`), so a scheduler that
  fires the stocking job on a mirror doubles as that clone's auto-refresh. (This
  was how the MacBook's Tauri app stayed fresh before it was retired; nothing
  uses it routinely now.)
  - Mirror (any non-Mini clone): `touch .db-readonly`
  - Writer (Mini): the marker must NOT exist (`ls .db-readonly` → absent)
- The Mini is the only machine that should run the schedulers/cron for fetch and
  Notes sync. You edit Apple Notes on any device; iCloud syncs them to the Mini,
  which is the only place Notes↔DB is translated.
- Notes sync runs on the Mini as the `com.limechile.uintas-notes-sync` LaunchAgent
  (every 6h; `scripts/notes_sync_agent.py` → Notes→DB, then DB→Notes for lakes
  flagged by stocking updates, then commit+push). Because
  the home is on an external `/Volumes` disk, its deployment is non-standard
  (internal-disk plist, FDA on the venv python, reboot revival via the
  agent-bootstrapper). Full runbook: `deploy/README.md`.

### App edits (status / Jed's Notes / trip reports) — the PWA write path
Since 2026-08-10 the user-owned lake fields (`status`, `jed_notes`,
`trip_reports`) are edited **in the PWA itself** ("My Record" section of the
lake modal), not in Apple Notes. This keeps the single-writer model intact
while allowing edits to *originate* on any device:

- **Client side (`index.html`)**: saves land in `localStorage` instantly
  (fully offline — designed for multi-day trips), overlay the loaded data, and
  are flushed to the edits server whenever it's reachable. A header chip shows
  the pending count; the "Sync" link (next to "About") opens a panel with a
  manual sync button and a server-URL override. Server auto-resolution tries
  the page's own host on :8802, then `http://olaf.local:8802` (LAN), then
  `https://olaf.tail89dcea.ts.net:8443` (Tailscale). The Tailscale HTTPS proxy
  (`tailscale serve --bg --https=8443 http://127.0.0.1:8802` on the Mini; config
  persists across reboots but NOT across a tailnet re-login — port **8443**, not
  443, because the jedOS dashboard owns the :443 root on the same hostname) exists because the iPhone's PWA is installed from the **https**
  github.io page, and a secure page cannot fetch `http://` LAN URLs (Safari
  silently blocks mixed content) — so the iPhone syncs only via the Tailscale
  URL, and only while its Tailscale VPN is on (from anywhere, not just home).
- **Server side (`scripts/edits_server.py`)**: runs ONLY on the Mini (writer
  guard) as the `com.limechile.uintas-edits-server` LaunchAgent, port 8802.
  Applies edits last-write-wins per (lake, field) using the committed audit log
  `data/app_edits_log.jsonl` (kept OUTSIDE the DB on purpose, so the
  seeds/rebuild/verify machinery is untouched), then commits + pushes in the
  background — the pre-commit hook regenerates seeds + `lakes_data.json`, the
  github.io deploy publishes them, and every PWA picks them up on its next
  service-worker update. A device that was offline for a
  week gets "superseded" (not applied) for any edit older than what another
  device already wrote to the same field.
- **Test harness**: `python3 scripts/edits_server.py --db /tmp/x.db --log
  /tmp/x.jsonl --no-git --port 8899` — also serves the repo statically, so one
  process backs a full browser test.

```bash
curl http://olaf.local:8802/api/ping        # is the writer up?
tail -f /Users/jed/Library/Logs/uintas-edits-server.log
```

### Push notifications + home-screen badge (iOS 16.4+ Web Push, added 2026-08-15)
Replaces the old external Telegram "new stockings" ping with native PWA push
notifications and an app-icon badge. iOS 16.4+ supports Web Push **and** the
Badging API for a PWA **installed to the Home Screen** — using standard VAPID,
so **no Apple Developer account / APNs certs** are needed (Apple runs the relay).

- **Keys/secrets (Mini-only, gitignored `data/push/`):** one VAPID keypair.
  The private key + the per-device `subscriptions.json` are secrets and MUST NOT
  be committed (the repo is public). The **public** key is embedded in
  `index.html` (`VAPID_PUBLIC_KEY`). Regenerate only via
  `python3 scripts/push_utils.py generate-keys` — it reprints the public key to
  paste into `index.html`; a new key invalidates every existing subscription.
- **`scripts/push_utils.py`** — shared module: key handling, subscription store,
  and `broadcast(title, body, report, badge)` which sends to every device and
  **auto-prunes** any subscription the push service 404/410s. Never raises (a
  push failure can't break the stocking run). Honors `UINTAS_PUSH_DIR` for tests.
- **Server (reuses the edits server on :8802, Mini-only):** `edits_server.py`
  adds `GET /api/push/public-key`, `POST /api/push/subscribe`,
  `POST /api/push/unsubscribe`, `POST /api/push/test`. The iPhone reaches these
  over the **same** Tailscale HTTPS proxy the edits sync uses (a secure github.io
  page can't fetch http:// LAN URLs), so enabling/testing needs Tailscale on.
- **Client (`index.html` "Notifications" block in the Sync panel):** an
  **Enable notifications** button (iOS requires a user gesture) requests
  permission → `pushManager.subscribe()` → POSTs the subscription. A **Send
  test** button hits `/api/push/test`. The app clears the badge when it's opened.
- **Service worker (`service-worker.js`):** `push` shows the notification, bumps
  a **cumulative** badge (`setAppBadge`), and stashes the full report in a
  version-independent cache (`uintas-push-state`, spared by the activate cleanup);
  `notificationclick` opens the app to the **full stocking report** built from the
  payload (race-free — no dependency on the github.io redeploy);
  `pushsubscriptionchange` re-subscribes on its own.
- **Trigger (`fetch_latest_stocking.py`):** after committing, if there are new
  **lettered-lake** stockings (fringe creeks/ponds aren't in the PWA, so they're
  not pushed) it calls `push_utils.broadcast(...)` with a summary + the full list.

```bash
python3 scripts/push_utils.py list             # which devices are subscribed
python3 scripts/push_utils.py test "message"   # send a real test push to all devices
# After changing edits_server.py, restart so endpoints reload:
launchctl kickstart -k gui/$(id -u)/com.limechile.uintas-edits-server
```

