# Deploy: Notes→DB LaunchAgent (Mac Mini only)

The Mini is the sole DB writer. This LaunchAgent runs `scripts/notes_sync_agent.py`
every 6h: Apple Notes → DB, then commit + push if the DB changed. (No DB→Notes —
that direction has a note-wipe bug and stays manual.)

This machine's home is on an external `/Volumes` disk, which makes LaunchAgents
non-standard. The rules below are load-bearing.

## Install / update

The live plist must **physically** live on the internal disk (launchd won't load
a plist from the `noowners` `/Volumes` home). The repo keeps the source of truth
in `deploy/`; copy it to the internal LaunchAgents dir and (re)load:

```bash
cp deploy/com.limechile.uintas-notes-sync.plist \
   /Users/jed/Library/LaunchAgents/com.limechile.uintas-notes-sync.plist
launchctl bootstrap gui/$(id -u) /Users/jed/Library/LaunchAgents/com.limechile.uintas-notes-sync.plist
# To reload after editing the plist:
#   launchctl bootout  gui/$(id -u)/com.limechile.uintas-notes-sync
#   launchctl bootstrap gui/$(id -u) /Users/jed/Library/LaunchAgents/com.limechile.uintas-notes-sync.plist
```

`launchctl bootstrap` printing `5: Input/output error` just means "already
loaded" — verify real state instead:

```bash
launchctl print gui/$(id -u)/com.limechile.uintas-notes-sync
launchctl kickstart -k gui/$(id -u)/com.limechile.uintas-notes-sync   # run it now
tail -f /Users/jed/Library/Logs/uintas-notes-sync.log
```

## Required: grant Full Disk Access (one-time, GUI)

launchd execs the venv python **directly** so that python is the TCC responsible
process for the in-process `NoteStore.sqlite` read. Until it has FDA the log shows
`PERMISSION ERROR: Cannot read NoteStore.sqlite` and the sync no-ops.

System Settings → Privacy & Security → **Full Disk Access** → **+**. The venv
path (`venv/bin/python3`) is a symlink and shows GREYED OUT in the picker — add
the resolved real binary instead: in the picker press **Cmd+Shift+G** and paste
the output of

```bash
readlink -f /Volumes/OLAF-EXT/jedwoodx/repos/uintas/venv/bin/python3
# e.g. /opt/homebrew/Cellar/python@3.13/3.13.7/Frameworks/Python.framework/Versions/3.13/bin/python3.13
```

That real binary is what the kernel actually execs for the LaunchAgent, so the
grant covers it. Re-add the grant after a Homebrew python upgrade (the Cellar
path moves) or a venv rebuild. Verify with:

```bash
launchctl kickstart -k gui/$(id -u)/com.limechile.uintas-notes-sync
tail -20 /Users/jed/Library/Logs/uintas-notes-sync.log   # no PERMISSION ERROR
```
Removing the `*update` tag also needs Automation→Notes, but that's best-effort;
the DB still updates without it.

## Reboot survival

Login-time auto-load is broken here (home is on `/Volumes`). The system agent
`/Library/LaunchAgents/com.limechile.agent-bootstrapper.plist` runs
`/Users/jed/dotfiles/bin/bootstrap-jedos-agents.sh`, which waits for the external
volume to mount and then `launchctl bootstrap`s every `com.*.plist` in
`/Users/jed/Library/LaunchAgents` — including this one. So as long as the live
plist is in that dir, it comes back after a reboot. Nothing else to do.
