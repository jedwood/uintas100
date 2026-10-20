# Runbook: retired subsystems

Kept for reference. None of these run on a schedule any more — do not
restart one without reading why it was retired. Split out of CLAUDE.md
2026-09-24; the text below is unchanged except where dated later.

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

### Tauri desktop app (`tauri-app/`) — REMOVED 2026-10-20
A desktop wrapper (`/Applications/Uintas.app`) that served the web app on
:8804 in an iframe, ran an in-app stocking scheduler, and exposed a gear-icon
control panel (intervals, run-now, logs). It came from a stretch of wanting
everything self-contained in one app; the PWA plus the jedOS scheduler made it
redundant. The MacBook dropped it 2026-09-08; on the Mini it was still
launched but its scheduler was disabled, so it did nothing. On 2026-10-20 the
source was deleted from the repo, the app bundle and its
`~/Library/Application Support/com.jedwood.uintas/` store were removed, and
the PWA's iframe `REFRESH_DATA` listener was dropped. The stocking fetch is
scheduled by jedOS; see "What runs unattended on the Mini" in
`edits-push.md`. The source is in git history before that date if it's ever
needed.

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

