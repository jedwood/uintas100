"""Single-writer guard for the database.

In this project exactly one machine (the Mac Mini) is allowed to WRITE the
database — stocking fetch, Notes->DB, DB->Notes, and the commit+push. Every
other clone is a read-only mirror that only `git pull`s and runs the app.

To enforce that independently of any GUI toggle or scheduler, a mirror carries a
gitignored marker file `.db-readonly` in the repo root. The writing scripts call
exit_if_readonly() up front and bail out cleanly when the marker is present, so
even if a scheduler fires the job it does nothing.

    Make a machine a read-only mirror:   touch .db-readonly
    Let a machine write again (the Mini): rm .db-readonly   (it should not exist there)
"""
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKER = os.path.join(REPO_ROOT, ".db-readonly")


def is_readonly_mirror():
    """True if this clone is marked read-only (must not write the DB)."""
    return os.path.exists(MARKER)


def exit_if_readonly(job="this job"):
    """Exit 0 immediately if this machine is a read-only mirror."""
    if is_readonly_mirror():
        print(f"[writer-guard] .db-readonly present — read-only mirror; skipping {job}.")
        sys.exit(0)


def pull_and_exit_if_readonly(job="this job"):
    """On a read-only mirror, refresh the clone (`git pull --ff-only`) and exit 0.

    A mirror's version of "fetch the latest data" is pulling what the Mini
    pushed. Used by the stocking-fetch path so a scheduler firing the job on a
    mirror (e.g. the Tauri app on the MacBook) keeps that clone — and the web
    app it serves — up to date instead of silently no-oping.
    """
    if not is_readonly_mirror():
        return
    print(f"[writer-guard] .db-readonly present — read-only mirror; pulling instead of {job}.")
    result = subprocess.run(
        ["git", "pull", "--ff-only"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    sys.stdout.write(result.stdout + result.stderr)
    if result.returncode != 0:
        print("[writer-guard] WARNING: git pull failed; mirror may be stale.")
    sys.exit(0)
