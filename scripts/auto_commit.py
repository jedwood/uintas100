#!/usr/bin/env python3
"""
Commit + push for the UNATTENDED writers (the edits server, the stocking cron)
without sweeping up whatever a human or Claude is editing in the same working
tree at that moment.

The problem this solves (recurring through Sept 2026): both automations run in
the one working tree the Mini's dev sessions also use. A plain `git add X; git
commit` commits the WHOLE index — so any file a dev had `git add`ed but not yet
committed went out under "App edits: …" — and the pre-commit hook used to
`git add service-worker.js` after bumping the cache version, which staged every
in-progress edit to that file too. Half-finished service-worker rewrites were
pushed to github.io several times this way.

How it works: the commit is built in a PRIVATE index that starts as exactly
HEAD, gets only the paths the caller owns added from the working tree, and is
then committed. The pre-commit hook inherits GIT_INDEX_FILE, so what it stages
(the cache-version bump, regenerated seeds + lakes_data.json) lands in the
same private index. Afterwards the real index is re-pointed at the new HEAD for
just the paths the commit touched, so `git status` is clean for those and
untouched for everything else. Nothing a dev has staged or edited elsewhere is
ever included — automation can only ever publish HEAD + its own files.

    from auto_commit import commit_own_files
    commit_own_files(["uinta_lakes.db", "data/app_edits_log.jsonl"],
                     "App edits: status/notes updates from the PWA")

Returns the new commit hash, or None when there was nothing to commit.
"""
import os
import subprocess
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _git(args, env=None, check=True):
    return subprocess.run(["git", *args], cwd=REPO_ROOT, env=env,
                          capture_output=True, text=True, check=check)


def commit_own_files(paths, message, push=True, log=print):
    """Commit HEAD + the working-tree contents of `paths` (only), then push.

    `paths` may include untracked files (e.g. the first app_edits_log.jsonl)
    and directories. Raises subprocess.CalledProcessError on a git failure
    other than push (a failed push is reported via `log` and the commit stays
    local, exactly like before).
    """
    fd, index_path = tempfile.mkstemp(prefix="uintas-auto-index-")
    os.close(fd)
    os.unlink(index_path)            # git creates it; an empty file confuses read-tree
    env = dict(os.environ, GIT_INDEX_FILE=index_path, UINTAS_AUTO_COMMIT="1")
    try:
        _git(["read-tree", "HEAD"], env=env)
        _git(["add", "--", *paths], env=env)
        if _git(["diff", "--cached", "--quiet"], env=env, check=False).returncode == 0:
            return None                          # nothing changed in the owned paths
        _git(["commit", "-m", message], env=env)   # hook runs against the private index
        sha = _git(["rev-parse", "HEAD"]).stdout.strip()
        # Sync the REAL index to the new HEAD for the paths this commit touched
        # (and only those). Without this the real index would still hold the
        # old blobs and a later plain `git commit` would silently revert them.
        touched = _git(["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"]).stdout.split("\n")
        touched = [p for p in touched if p]
        if touched:
            _git(["reset", "-q", "--", *touched])
        log(f"[auto-commit] {sha[:7]} {message} ({len(touched)} files)")
    finally:
        try:
            os.unlink(index_path)
        except FileNotFoundError:
            pass
    if push:
        p = _git(["push"], check=False)
        if p.returncode != 0:
            log("[auto-commit] WARNING: git push failed (committed locally): " + (p.stderr or "").strip())
    return sha


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        sys.exit("usage: auto_commit.py 'message' path [path ...]")
    print(commit_own_files(sys.argv[2:], sys.argv[1]) or "nothing to commit")
