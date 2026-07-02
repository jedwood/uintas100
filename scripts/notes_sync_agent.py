#!/usr/bin/env python3
"""
LaunchAgent entrypoint (Mac Mini, the sole DB writer): sync Apple Notes -> DB,
then commit + push if the DB changed.

WHY THIS IS A PYTHON ENTRYPOINT (not the sync_notes_and_push.sh bash wrapper):
launchd must `exec` the Full-Disk-Access-needing binary DIRECTLY so THIS python
process is the TCC "responsible process" — its FDA grant then covers the
in-process read of ~/Library/Group Containers/.../NoteStore.sqlite. Routing the
FDA tool through a bash/launcher intermediary makes TCC walk up to the parent and
deny. So the plist execs `venv/bin/python3 scripts/notes_sync_agent.py` directly,
and the git commit/push lives here in the same process (git needs no FDA).
See deploy/com.limechile.uintas-notes-sync.plist.

Guards:
  - single-writer: bails on a read-only mirror (.db-readonly present).
  - volume race: if uinta_lakes.db is absent (external volume not mounted), do
    nothing. (At boot the agent-bootstrapper only bootstraps us AFTER the volume
    mounts, but this is a cheap belt-and-suspenders check.)

Round trip: after Notes -> DB captures the user's note edits, this agent ALSO
runs DB -> Notes (sync_db_to_notes_jxa.js) when any lakes are flagged
notes_needs_update (set by stocking updates), so fresh stocking data lands in the
lake notes within one agent cycle. The JXA script is wipe-safe (preserves
everything above the ═══ delimiter from the live note, backs up old bodies,
skips conflict-merged notes, waits for iCloud to settle) — see its header for
the 2026-07-01 incident rules. DB -> Notes is skipped if Notes -> DB failed
(capture first, then write).

The pre-commit hook (core.hooksPath .githooks) regenerates data/seeds/ and
lakes_data.json from the DB on commit, so we never do that here.
"""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from writer_guard import exit_if_readonly  # noqa: E402
import sync_notes_to_db  # noqa: E402


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)


def main():
    # 1. Single-writer guard — a read-only mirror must never write/commit.
    exit_if_readonly("notes sync agent")

    # 2. Volume-mounted sanity check.
    db = os.path.join(REPO, "uinta_lakes.db")
    if not os.path.exists(db):
        print(f"[notes-agent] {db} missing (external volume not mounted?); skipping.")
        return 0

    # 3. Apple Notes -> DB. Reads NoteStore.sqlite IN THIS PROCESS, so this is the
    #    step that needs Full Disk Access on this python binary.
    rc = sync_notes_to_db.sync(dry_run=False)

    # 3b. DB -> Notes round trip: push flagged stocking updates into the lake
    #     notes. Only when Notes -> DB succeeded (capture the user's edits first)
    #     and something is actually flagged. Runs BEFORE the commit so the flag
    #     clears land in the same commit.
    if rc == 0:
        flagged = subprocess.run(
            ["sqlite3", db, "SELECT COUNT(*) FROM lakes WHERE notes_needs_update = TRUE;"],
            capture_output=True, text=True,
        )
        n_flagged = int(flagged.stdout.strip() or 0) if flagged.returncode == 0 else 0
        if n_flagged:
            print(f"[notes-agent] {n_flagged} lakes flagged — running DB -> Notes.")
            r = subprocess.run(
                ["osascript", os.path.join(SCRIPT_DIR, "sync_db_to_notes_jxa.js")],
                cwd=REPO, capture_output=True, text=True, timeout=1800,
            )
            sys.stdout.write(r.stdout + r.stderr)
            if r.returncode != 0:
                print("[notes-agent] WARNING: DB -> Notes failed; flags stay set, will retry next cycle.")
    else:
        print(f"[notes-agent] Notes -> DB failed (rc={rc}); skipping DB -> Notes this cycle.")

    # 4. Persist iff the sync actually changed the DB. (A permission failure
    #    returns non-zero BEFORE any DB write, so `changed` stays False and we
    #    commit nothing. If some notes applied before a later error, those real
    #    edits are still committed rather than left dangling in the working tree.)
    changed = git("diff", "--quiet", "--", "uinta_lakes.db").returncode != 0
    if not changed:
        print(f"[notes-agent] No DB change (sync rc={rc}); nothing to commit.")
        return rc

    print(f"[notes-agent] DB changed (sync rc={rc}) — committing + pushing.")
    git("add", "uinta_lakes.db")  # pre-commit hook adds seeds + lakes_data.json
    c = git("commit", "-m", "Notes sync: apply Apple Notes edits to DB")
    sys.stdout.write(c.stdout + c.stderr)
    p = git("push")
    sys.stdout.write(p.stdout + p.stderr)
    if p.returncode != 0:
        print("[notes-agent] WARNING: git push failed (committed locally).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
