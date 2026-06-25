# DB Recovery Plan — rebuild `uinta_lakes.db` from scratch

**Status:** ✅ DONE (2026-06-24). Implemented via committed CSV **seeds** + a
self-verifying rebuild, not the originally-hypothesized CSV-replay (see
"Outcome" below for why the replay approach was abandoned).
**Goal:** a single documented, idempotent, offline sequence that reconstructs a database **content-equivalent** to the committed `uinta_lakes.db`, with a self-verifying harness — so the committed DB stops being an unreproducible black box.

The committed DB remains the source of truth. This plan does **not** change it; it makes it *rebuildable*. Good baseline md5 of the live DB: `2469f083eb098f3ace8d40bb63b52221`.

---

## Outcome (what shipped)

A clean replay of `utah_dwr_stocking_data.csv` through the matcher was proven
**unable** to reproduce the curated DB, so the design pivoted to seeds:

- **Echo Reservoir finding.** `find_matching_lake` strips a trailing `RESERVOIR`,
  so "ECHO RES" (Echo Reservoir, a lowland reservoir) name-matches the tiny Uinta
  **Z-16 "Echo"** lake. The canonical DB has 2 records for Z-16 (the explicit
  "ECHO L Z-16" rows); a replay credits it ~59 (adding Rainbows/Walleye that don't
  belong). Same class of lowland-water mis-filing the matcher overhaul fought.
  A faithful, offline, zero-residual rebuild therefore cannot come from the raw CSV.
- **Lost sources.** 55 live lakes aren't in `lake_data.csv` (manual / lost-importer
  additions; 29 carry curated coordinates), and `drainages` (19) + `photos` (34)
  have no committed source files. None are reconstructable algorithmically.

**What shipped instead** — the DB is now reconstructable from committed, diffable text:

- `scripts/export_seeds.py` → `data/seeds/*.csv` (one per table; FKs as natural
  keys; SQL `NULL` written as `\N` so `NULL`-vs-`''` round-trips, e.g. `basin`).
- `scripts/rebuild_database.py` → loads seeds into a fresh canonical schema, fully
  offline. Defaults to a temp file; refuses to overwrite the real DB without `--force`.
- `scripts/verify_rebuild.py` → rebuilds to temp and content-diffs every table
  vs the canonical DB on natural keys (ignoring surrogate `id` + `last_modified`).
  **Verified PASS: 0 diff across all 7 tables (721 / 7074 / 19 / 34 / 14 / 161 / 0).**
- `create_database()` now builds the **full** canonical schema (24 lakes cols in
  live order + all triggers incl. `flag_lake_for_notes_update` + coordinate cols);
  `setup_database.py` no longer patches schema ad hoc. PRAGMA parity verified.
- Dumps assert their required columns (`assert_lake_columns`) so future drift fails
  loudly instead of mid-query.

**Ongoing workflow:** after any DB change run `export_seeds.py` and commit the seeds
with the DB; run `verify_rebuild.py` to catch drift. The matcher still owns the
*ongoing* update path (`fetch_latest_stocking.py` / `update_stocking.py`) — seeds
own *reconstruction*.

The task notes below are the original plan, kept for context.

---

## Why we need this (verified findings, 2026-06-24)

A clean `setup_database.py` + `update_stocking.py` run into an isolated temp copy produced:

| Table | Clean rebuild | Live DB |
|---|---|---|
| lakes | 668 | 721 |
| stocking_records | 7122 | 7074 |
| other_waters | 14 | **14 ✓** |
| other_stocking_records | 161 | **161 ✓** |

So fringe routing is now faithful (the `update_stocking.py` alignment this session), but the broader rebuild is **not** faithful:

### Gap A — schema drift
`create_database()` (in `database_utils.py`) + setup's `last_modified` ALTERs build a 16-column `lakes` table. The live table has 24. The **8 missing columns**:

- `lat`, `lng`, `coord_source`, `coord_status` — added only by `coord_utils.ensure_coord_columns()`, which `setup_database.py` never calls.
- `elevation_ft`, `dwr_notes`, `trip_reports`, `notes_needs_update` — added by **no script anywhere**; they were applied ad hoc to the live DB and are simply assumed to exist by readers/writers.

Symptom: `dump_combined_data()` throws `no such column: l.elevation_ft` at the end of a fresh build (data already committed; the crash is in the dump step).

### Gap B — data completeness
- **Lakes (668 → 721):** the extra ~53 lakes in the live DB come from historical importers not in the setup flow — `import_uintah_daggett_historical.py`, `import_historical_stocking.py`, `fetch_historical_stocking.py` (Uintah/Daggett 2002–present, etc.).
- **Stocking (7122 vs 7074):** the clean replay over the *current* CSV yields **more** lake-credited records than the live DB. Direction is opposite to lakes, so this is not just "missing imports" — it needs reconciliation (see T3). Likely causes: live DB had records removed/re-filed by the matcher overhaul + `migrate_fringe_waters.py` that still sit in the CSV, or dedup differs between the replay and the accumulated history.

### Gap C — drift sources
DB has been edited from two machines (Macbook + Mac Mini) and accreted across many one-off scripts. Canonical = the committed DB.

---

## Tasks

### T1 — Canonicalize the schema
Make `create_database()` build the **full** `lakes` (24 cols) and `stocking_records` schema in one place:
- Add explicit idempotent `ALTER TABLE ... ADD COLUMN` (try/except `OperationalError`) for `elevation_ft`, `dwr_notes`, `trip_reports`, `notes_needs_update`.
- Have `create_database()` call `coord_utils.ensure_coord_columns(conn)` so `lat/lng/coord_source/coord_status` always exist.
- Confirm `last_modified` columns + triggers live in `create_database()` (currently partly in `setup_database.main()`), so any entry point gets them.
- **Acceptance:** `PRAGMA table_info(lakes)` on a fresh build == live DB column set + types (match column order too if cheap).

### T2 — Define one canonical, offline build order
Single runbook / driver script. Proposed order:
1. `setup_database.py` — schema + lake list + Norrick physical data + drainages.
2. Historical importers (decide order; make them idempotent and **offline**).
3. `update_stocking.py` — replay `data/utah_dwr_stocking_data.csv` (now fringe-aware).
4. `export_web_data.py` — regenerate `lakes_data.json`.

Key decision: the historical importers currently hit the DWR site over the network. **Prefer offline** — make `data/utah_dwr_stocking_data.csv` the single committed source for *all* stocking (historical + recent), so a rebuild needs no network. Verify the CSV already spans 2002–present for all 5 counties; if not, snapshot the historical data into a committed CSV once.

### T3 — Reconcile every row-level delta to zero-unexplained
Row-level diff clean-rebuild vs live:
- lakes keyed by `letter_number`; stocking keyed by (`lake letter_number`, species, quantity, `stock_date`, `source_year`).
- Classify each diff: (a) legit live-only data not in any source CSV → fold into a committed seed/CSV; (b) rebuild-only artifacts → fix matcher/dedup; (c) already-resolved ghost/cleanup.
- **Acceptance:** rebuild differs from live only by explainable, documented rows (ideally zero).

### T4 — Make dumps robust
`dump_combined_data()` / friends should not crash on a valid schema. After T1 they won't reference a missing column, but add a guard or schema assert so future drift fails loudly, not cryptically.

### T5 — One-command rebuild + self-verify (regression guard)
A `make rebuild-verify` (or `scripts/verify_rebuild.py`) that:
- builds into a **temp path** (reuse this session's isolation pattern — see below),
- content-diffs against the committed DB ignoring surrogate ids,
- prints a reconciliation report and **exits non-zero on any unexplained diff**.
This is what keeps the DB reproducible going forward.

### T6 — Docs
Update CLAUDE.md "Database Management" with the canonical rebuild sequence and the reproducibility guarantee, and link this plan.

---

## Reusable verification harness (prototyped this session)

Isolation pattern so `create_database()` never touches the real DB:
- Copy `scripts/` into a temp dir (so `__file__`-relative `create_database()` writes to `<temp>/uinta_lakes.db`).
- Symlink `data/`; create an empty `scripts/drainages/` (makes drainage load a no-op); create a real `logs/` dir.
- Run `setup_database.py` then `update_stocking.py` with cwd = `<temp>/scripts`.
- Diff tables on **natural keys**, not surrogate ids (ids differ between builds).

DB backups from this session: `<scratchpad>/db-backups/` (worktree / head / origin / autostash variants).

---

## Safety rules
- **Never** run `setup_database.py` (or any `create_database()` entry point) against the real DB path.
- Back up the committed `uinta_lakes.db` before any destructive run.
- Treat the committed DB as canonical; the rebuild must conform to it, not vice-versa, until T3 proves equivalence.
