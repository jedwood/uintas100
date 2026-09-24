# Runbook: retired subsystems

Kept for reference. None of these run on a schedule any more — do not
restart one without reading why it was retired. Split out of CLAUDE.md
2026-09-24; the text below is unchanged.

### Apple Notes Sync (RETIRED as a write path, 2026-08-10; LaunchAgent undeployed 2026-08-12)
The Notes round trip is retired: `notes_sync_agent.py` exits immediately unless
run with `UINTAS_NOTES_SYNC=force`. Reason: the user fields are now edited in
the app (above), and a Notes→DB run would overwrite them with stale note
content (most notes still carry pre-migration placeholders — see the
2026-08-10 data-loss investigation). The `com.limechile.uintas-notes-sync`
LaunchAgent is no longer loaded or scheduled at all (`launchctl bootout`-ed,
plist removed from `/Users/jed/Library/LaunchAgents/` — source of truth stays
in `deploy/`, see `deploy/README.md`); leaving it loaded as a no-op used to
also trip a stale-log watchdog in `fetch_latest_stocking.py` on every stocking
run, which has since been removed. The JXA scripts below remain for manual /
archival use only.
```bash
# Sync changes from Apple Notes to database
osascript scripts/sync_notes_to_db_jxa.js

# Sync flagged database changes to Apple Notes
osascript scripts/sync_db_to_notes_jxa.js

# Shell wrapper for notes sync (Notes -> DB only; self-guards on mirrors)
./scripts/sync_notes_to_db.sh

# Mini-only: Notes -> DB AND commit+push the result (durably persists note edits)
./scripts/sync_notes_and_push.sh
```
**DB→Notes (`sync_db_to_notes_jxa.js`) is now wipe-safe.** Apple Notes has no
surgical edit (writing a note replaces its whole body), so for an EXISTING note
the script reads the live note and **preserves everything above the ═══ delimiter
verbatim** (your Status / Jed's Notes / Trip Reports), rebuilding the body as
preserved-above + fresh delimiter + DB-regenerated auto-data; only the `<h1>`
title emoji is refreshed. It does NOT source your editable content from the DB, so
it can't clobber un-captured edits regardless of the `*update`-tag/ordering.
Safety nets: it **backs up** each old note body to `logs/notes_backups/` before
overwriting, **skips** (won't touch) any note lacking a ═══ delimiter or that looks
conflict-merged (2+ delimiters / doubled title), and **waits 30s after launching
Notes** for iCloud to pull before reading (`UINTAS_SYNC_SETTLE=<secs>` to tune, `0`
to skip) — rewriting from a stale replica makes iCloud concatenate both versions
into one note (the 2026-07-01 incident). Never set `note.name` after setting
`body` (the first body line already becomes the name; setting both doubles the
title text).
Preview without writing: `UINTAS_DRYRUN=1 osascript scripts/sync_db_to_notes_jxa.js`.
`notes_sync_agent.py` still implements the full **round trip** (Notes→DB, then
DB→Notes for any lakes flagged `notes_needs_update`, then commit+push) but only
runs it when manually invoked with `UINTAS_NOTES_SYNC=force` — there is no
longer a LaunchAgent firing it automatically. `sync_notes_and_push.sh` (the
manual wrapper) remains Notes→DB only. Known hiccup: if a lake note is OPEN on
another device while DB→Notes rewrites it, that device may iCloud-conflict-merge
and show a duplicated section — fix is simply deleting the duplicated lower
section(s) by hand on that device.

### Tauri control-panel app (`tauri-app/`) — retired on the MacBook 2026-09-08
The MacBook no longer runs this; Jed dropped the Tauri shell there, separated
pull from build, and uses a Dock-installed PWA instead (see Single-writer model).
The source stays in the repo for reference or for the Mini. What it was: a
desktop wrapper (`/Applications/Uintas.app`) that ran the schedulers, served
the web app on :8804 (moved off :8000 2026-08-12 — the shared Qwen3 embeddings
LaunchAgent claims :8000), and exposed a gear-icon control panel. Build + install:
```bash
cd tauri-app && cargo tauri build --bundles app
rm -rf /Applications/Uintas.app && cp -R src-tauri/target/release/bundle/macos/Uintas.app /Applications/
```
- **Schedule lives in a store, not in the repo.** Live intervals are in
  `~/Library/Application Support/com.jedwood.uintas/schedule.json`; the values in
  `scheduler.rs` are only defaults for a machine with no store yet. Don't read the
  source and conclude what a given machine is doing — read that file (or the panel).
- **On a mirror, the "Stocking Updates" interval IS the mirror-refresh cadence.**
  `writer_guard.pull_and_exit_if_readonly()` turns that job into a
  `git pull --ff-only`, so the interval sets how far behind the clone can drift.
  (The MacBook ran it hourly until it dropped the app.) End-to-end freshness is
  still capped by how often the *Mini* actually fetches from DWR — a mirror
  can't be fresher than what was pushed.
- The frontend is embedded at compile time by `tauri::generate_context!()`.
  `build.rs` emits `rerun-if-changed` for `frontend/` to force a recompile on
  frontend-only edits — `tauri_build::build()` does NOT do this itself, and without
  it cargo skips the rebuild and silently ships a stale UI.
- Editing an interval by hand in `schedule.json` requires quitting the app first;
  a running app holds the config in memory and overwrites the file on its next save.

### Apple Notes Structure
**Organization**: Notes are organized in the "Uintas 💯" folder with subfolders for each drainage. Lake notes are stored within their respective drainage subfolders.

```
Lake Name (A-42) 🎣        ← Status emoji in title
Status: CAUGHT             ← Sync field
Jed's Notes                ← User content
Trip Reports               ← User content
═══════════════════════   ← Delimiter
Auto-generated lake data   ← System content
```

