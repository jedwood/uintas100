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
