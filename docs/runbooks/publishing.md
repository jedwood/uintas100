# Runbook: publishing changes

Seeds, the pre-commit hook, the PWA cache bump, and how to work in this
tree while the automation commits. Split out of CLAUDE.md 2026-09-24;
the text below is unchanged.

### Database Management
```bash
# Initial setup (run once)
python3 scripts/setup_database.py

# Update with latest stocking data
python3 scripts/fetch_latest_stocking.py
python3 scripts/update_stocking.py

# Regenerate the frontend data file after any database change
# (the pre-commit hook also runs this automatically when uinta_lakes.db is committed)
python3 scripts/export_web_data.py

# Generate human-readable dumps
python3 -c "from scripts.database_utils import *; import sqlite3; conn = sqlite3.connect('uinta_lakes.db'); dump_lake_data(conn); dump_stocking_data(conn); dump_combined_data(conn)"
```

### Database Reproducibility (seeds → rebuild → verify)
`uinta_lakes.db` is canonical, but it is also fully reconstructable from committed,
git-diffable CSV **seeds** in `data/seeds/` (one per table). This is the recovery
path — and the regression guard that the DB never silently drifts.

```bash
# Enable the version-controlled git hooks ONCE per clone (this is the only manual
# step — afterward seeds stay in sync automatically):
git config core.hooksPath .githooks

# Rebuild a content-equivalent DB from the seeds, fully offline (writes a temp file)
python3 scripts/rebuild_database.py                      # or --output PATH

# Prove the seeds round-trip to the canonical DB (exit 0 = equivalent, 1 = drift)
python3 scripts/verify_rebuild.py

# Manual re-export (rarely needed — only if committing the DB with hooks disabled)
python3 scripts/export_seeds.py
```

**Seeds regenerate automatically** — you do not need to remember `export_seeds.py`:
- The `.githooks/pre-commit` hook regenerates + stages `data/seeds/` whenever
  `uinta_lakes.db` is staged (covers every manual commit and the cron auto-update,
  since both go through `git commit`). Enable it once with the `core.hooksPath`
  command above; it also bumps the PWA cache version.
- `fetch_latest_stocking.py` (the unattended cron path) also re-exports seeds in
  its commit step, so it can't push a DB with stale seeds even on a machine where
  the hook isn't enabled.

Why seeds and not a replay of `utah_dwr_stocking_data.csv`: a clean matcher replay
does **not** reproduce the curated DB. `find_matching_lake` strips `RESERVOIR`, so
it mis-credits lowland reservoirs onto same-named Uinta lakes (e.g. "Echo Reservoir"
→ Z-16 Echo, which the curated DB excludes), and it can't recreate the ~55
manually-added lakes or the drainage/photo rows (their original sources aren't
committed). The seeds capture the curated truth exactly; `verify_rebuild.py`
confirms an exact, zero-diff round-trip on every table. SQL `NULL` is stored in the
seeds as the sentinel `\N` (empty string stays empty) so the `NULL`-vs-`''`
distinction (e.g. `basin`) round-trips. Schema lives in one place —
`create_database()` builds the full canonical schema (all columns + triggers +
coordinate columns); `setup_database.py`/`update_stocking.py` no longer patch it
ad hoc. Full recovery write-up: `docs/db-recovery-plan.md`.

### PWA Cache Management
```bash
# PWA cache version is automatically updated by the .githooks/pre-commit hook
# (enable once per clone: git config core.hooksPath .githooks)
# No manual intervention needed - just commit and the hook handles it
git commit -m "your changes"  # Bumps cache version + re-exports data/seeds when the DB changed
```
**Every** commit bumps the version — including the 08:00 stocking auto-update
and every edits-server "App edits" commit — so a phone that checks in finds a
"new version" most days. The bump only touches the `const CACHE_NAME = …` line.

### Working in this tree while the automation commits (enforced, 2026-09-22)
The edits server and the stocking cron commit + push **in this same working
tree, at any moment**. Until 2026-09-22 they swept up in-progress work on
nearly every dev session: a plain `git commit` took everything staged, and the
hook's `git add service-worker.js` staged every half-finished edit to the
worker (six "App edits" commits on 2026-09-21 shipped a mid-rewrite worker).
Now enforced by code:
- `scripts/auto_commit.py: commit_own_files(paths, msg)` — both automations
  commit through a **private index** (`GIT_INDEX_FILE` = HEAD + only their own
  paths; the hook inherits it and adds the bump + regenerated seeds/JSON), then
  re-point the real index at the new HEAD for just the touched paths. Anything
  a dev has staged or edited elsewhere is untouched. Use it for any new
  unattended committer; never `git add -A` / `git commit -a` from automation.
- The hook stages the bump by rewriting the **index copy** of
  `service-worker.js` (`git show :service-worker.js` → sed →
  `update-index --cacheinfo`) — never the working-tree file's other changes.
  It still bumps the working-tree line so a clean tree stays clean, which is
  why the Edit tool sometimes reports the file "changed on disk" mid-session.
- `tests/auto_commit_isolation.sh` proves it in a throwaway clone (13 checks).
Not covered, by design: the DB is committed as-is whenever the automation
fires (run migrations as single scripts), and the hook runs the working-tree
exporters (finish + commit an exporter change in one go).
So: leave in-progress work uncommitted as long as you like; only what you
`git add` yourself ships. When you DO want to publish, commit normally.

### Curated lake collections (`data/collections.json`) — the "Collections" filter
The reports in `docs/` (`less-visited-lakes.md`, `4x4-access-lakes.md`) are also
selectable *in the app*: a **Collections** multi-select in the filter panel, first
control, grouped by report. Picking one shows that set in the list/map like any
other filter, and it **composes** with drainage/species/depth/etc. rather than
replacing them.

- **Source of truth is `data/collections.json`, hand-curated.** It is NOT parsed
  from the markdown: those reports also list ruled-out lakes, traps and
  heavy-pressure waters in prose and tables, and a parser would sweep them in.
  The reports are the argument; this file is the pick list.
- **Kept OUTSIDE `uinta_lakes.db` on purpose** (same reasoning as
  `data/app_edits_log.jsonl`) so the seeds / `rebuild_database` / `verify_rebuild`
  machinery is untouched. `export_web_data.py` reads it and nests it into
  `lakes_data.json` as `collections`.
- **Validation is hard and happens at export time**, i.e. in the pre-commit hook:
  an unknown designation or a duplicate key/lake raises and *fails the commit*,
  rather than silently shipping a filter chip that matches nothing.
- Each lake may carry a `note` — the curated one-liner for why it is in that set.
  It shows on the result card when exactly one collection is selected (two sets
  would make a single note ambiguous), and in the lake modal's "Collections"
  section, which links back to the whole set.

Adding a set: append an object with a unique `key`, a short `label` (it becomes a
filter chip — keep it under ~28 chars), a `group`, and the `lakes`. Then
`python3 scripts/export_web_data.py`.

### Frontend Asset Regeneration
- `lakes_data.json` - regenerate with `python3 scripts/export_web_data.py` after db changes (pre-commit hook does this automatically when the db is committed)
- `cma_book.html` - full text of Cordell Andersen's book, one `<section id="cma-pNNN">` per printed page; regenerate with `python3 scripts/export_cma_book.py` (Mini-only — needs the gitignored PDF). The lake modal's "(p. NNN)" citation links and trailhead "book p. N" links fetch this file and jump to the cited page in an in-modal viewer (back arrow returns to the lake). It is deliberately NOT in the service-worker precache list (a missing file must not break install); `initApp` warm-fetches it so the SW caches it lazily for offline use.
- `tailwind.css` - regenerate only if new Tailwind classes are added to index.html: `npx tailwindcss@3.4.17 -o tailwind.css --content "./index.html" --minify`

### Development Server
Since this is a static web app, serve locally with:
```bash
python3 -m http.server 8804   # NOT 8000 — the Qwen3 embeddings LaunchAgent owns :8000 on the Mini
# or
npx serve .
```

