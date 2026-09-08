# DWR 2025 pamphlet survey tables → database (plan, executed 2026-09-08)

The 2025 revised DWR pamphlets carry tabular data the app never had:

| Pamphlet | Table | What it holds |
|---|---|---|
| Whiterocks | "Brook / Cutthroat / Grayling trout gillnetting samples" (Tables 1–3) | per lake × species: stocking cycle, other species present, number of fish gillnetted (1960s–present), mean/max length (in), mean/max weight (lb); footnotes |
| Bear River, Blacks Fork | lake summary tables (pp. 20–23 / 15–17) | per lake: sub-drainage, access route, trail distance (mi), elevation, size, depth, campsites Y/N, spring water Y/N, horse feed Y/N/limited, fish species, stocking cycle; or "Unable to support a fishery" / "Private property" |

Whiterocks has no summary table; Bear River and Blacks Fork have no gillnet table.

## Steps
1. **Extract** with `pdftotext -layout` (row-per-line; the plain `-text.txt`
   dumps already in `data/dwr_new_pamphlets/` are one cell per line and unusable
   for tables). Rows are located by their numeric tail; multi-line cells
   (lake name + designation, wrapped access text) are re-joined by column
   position relative to the page's table header. Designations resolve to
   `lakes.id`; the few name-only rows ("Cleveland", "Deadfall", "Fish") resolve
   by unique name within the pamphlet's drainage, otherwise `lake_id` stays NULL
   and the printed name is kept.
2. **Store** in two new tables (schema in `create_database()`, seeds, rebuild,
   verify all extended):
   - `dwr_gillnet_samples` (lake_id, printed_name, species, stocking_cycle,
     other_species, n_sampled, mean_length_in, max_length_in, mean_weight_lb,
     max_weight_lb, note, source_edition)
   - `dwr_lake_summary` (lake_id, printed_name, sub_drainage, access,
     trail_miles, elevation_ft, size_acres, depth_ft, campsites, spring_water,
     horse_feed, fish_species, stocking_cycle, note, source_edition)
   Stocking-cycle codes are stored as printed (`1`…`5` = every N years, `2/3`,
   `NR` natural reproduction, `MIG` migrates in from the stream, `3a`/`1b`
   footnoted).
3. **Export** both nested per lake in `lakes_data.json` (`dwr_summary`,
   `dwr_gillnet`).
4. **Show** in the lake modal as a "DWR survey (2025 pamphlet)" block above the
   DWR notes: stocking cycle + amenities + trail distance, and a small
   gillnet table per species.
5. Re-runnable: `python3 scripts/import_dwr_survey_tables.py [--dry-run]`
   replaces all rows for `source_edition` 2025 each run; add a new pamphlet's
   PDF to `PAMPHLETS` when DWR reissues another drainage.

## Not done (ideas)
- Fold `stocking_cycle` / gillnet mean length into `data/hike_index.json` for
  "hikes with big-fish lakes" queries.
- The color coding in the PDF (green >12", gold 10–11", blue <10") is derivable
  from mean length; not stored.
