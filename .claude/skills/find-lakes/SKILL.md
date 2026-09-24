---
name: find-lakes
description: Find Uinta lakes matching criteria — species, stocking timing, drainage, size/depth/elevation, fishing pressure, distance to trail or road, hike length, Jed's caught/untried status. Use for any "find me lakes that…", "where should I fish…", "which lakes have…", "what's stocked with…", "shortest hike to…" question, or anything that needs the lake database queried rather than the app code changed.
---

# Finding lakes

Answer with `scripts/lakes.py`. It flattens six tables plus the hike index,
the curated collections and the OSM trail-distance cache into one row per
lake, so a question is one `SELECT` — not a join you have to rediscover.

```bash
python3 scripts/lakes.py "SELECT designation, name, drainage, elevation_ft, last_stocked
                          FROM lake_search WHERE ... ORDER BY ... LIMIT 20"
python3 scripts/lakes.py --columns        # full column list, both tables
python3 scripts/lakes.py -f json "..."    # also: -f csv, -f md
```

It is read-only and rebuilds its cache automatically when the DB or any
source changes (~1 s). Never write to `uinta_lakes.db` — the Mini is the
single writer.

Two tables, plus the canonical DB attached as `raw.*` for anything the flat
table doesn't carry (`raw.stocking_records`, `raw.guide_hikes`, `raw.lakes`
for the long prose columns, …):

| table | grain | use it for |
|---|---|---|
| `lake_search` | one row per lake (746) | almost everything |
| `lake_species` | one row per (lake, species) | "grayling stocked since 2023", per-species timing |

## Value vocabulary — match these exactly

**`drainage`** (18, all end in " Drainage" except one): Ashley Creek, Bear
River, Beaver Creek, Blacks Fork, Burnt Fork, Dry Gulch, Duchesne River,
Henrys Fork, Lake Fork, Provo River, Rock Creek, Sheep/Carter Creek
*Drainages*, Smiths Fork, Swift Creek, Uinta River, Weber River, White Rocks,
Yellowstone. Filter with `drainage LIKE 'Rock Creek%'` and you can't get the
suffix wrong.

**`species`** (normalized — see `scripts/species_utils.py`): Brookies,
Rainbows, Tigers, Cutthroats, Grayling, Goldens, Splake, Tiger muskie.
Jed's shorthand maps onto these: brookies/brook trout → `Brookies`, cutts →
`Cutthroats`, tiger trout → `Tigers`, arctic grayling → `Grayling`.

**`fishing_pressure`**: Low (255), Moderate (195), High (103), plus a
handful of Very low / Moderate high / Unknown / n/a, and 188 NULL. Treat
NULL as unknown, not as low.

**`status`** — Jed's own record: `CAUGHT` (41), `NONE` (10, fished and
skunked), `OTHERS` (3, others caught fish), NULL (692, never logged).
"Untried" / "haven't been" = `status IS NULL`.

## Gotchas that will bite

- **An asterisk in `species` means historical.** `"Brookies, Cutthroats*"`
  = brookies are current, cutthroats were stocked once and aren't now. Use
  `species_current` for "what's in there today" and `species_historical` for
  "used to have". Never pattern-match the raw `species` column for a
  current-fish question.
- **`no_fish = 1` (121 lakes)** are DWR's "does not sustain fish life"
  landmarks. Add `AND fishable` to any fishing query unless Jed asks about
  them.
- **Not every lake is stocked.** 471 of 746 have stocking records; the rest
  are winterkill ponds, wild-reproduction waters, or fishless. A few sustain
  fish with no stocking record at all (A-51 grayling, WR-3 and WR-77 cutts,
  JW-1, JW-2 — `WILD_SPECIES` in `species_utils.py`), so
  `ever_stocked = 0` does not mean fishless.
- **`stock_interval_yr` is a crude mean** (span ÷ gaps). A-11 shows 5.0 from
  2006, 2008, 2020, 2021, 2026 — meaningless. For cadence questions read
  `stocked_years` (the actual list) or `dwr_stocking_cycle` (DWR's own
  published cycle, 2025 pamphlet drainages only: "1"/"2"/"3" = years, "NR" =
  natural reproduction, no stocking).
- **The letter prefix is a survey block, not a drainage code.** `X-` lakes
  live in five different drainages. Always filter on `drainage`, never on
  the designation prefix.
- **Trail distances are OSM straight-line metres, not hiking miles.**
  `trail_mi` is how far the lake sits off the nearest mapped path;
  `route_mi` counts any route including 4x4 track; `road_mi`-ish columns are
  `road_m` (drivable) and `rough_road_m` (track/service). OSM coverage in
  the Uintas is uneven **in both directions** — real trails unmapped, and
  cross-country routes tagged as paths. Good for ranking "off the beaten
  path"; say so rather than quoting it as a hiking distance. For a real
  hiking number use `min_hike_mi` (Falcon guide, round trip) or
  `dwr_trail_miles` (DWR's own one-way trail miles, 77 lakes).
- **Only 284 lakes appear in the Falcon guide**, so `min_hike_mi IS NULL`
  means "the book doesn't cover it", not "no trail".
- 738 of 746 lakes have coordinates; the 8 without are all fishless.

## Recipes

```sql
-- current species, recently stocked, untried, close to a trail
SELECT designation, name, drainage, elevation_ft, size_acres, max_depth_ft,
       last_stocked, trail_mi, fishing_pressure
FROM lake_search
WHERE species_current LIKE '%Grayling%' AND years_since_stocked <= 3
  AND trail_mi <= 2 AND status IS NULL AND fishable
ORDER BY trail_mi;

-- due for a stocking: on a published cycle, gap >= the cycle
-- (returns nothing as of 2026-09 — DWR is on schedule everywhere. Empty
--  is a real answer here, not a broken query.)
SELECT designation, name, drainage, dwr_stocking_cycle, last_stocked_year, stocked_years
FROM lake_search
WHERE dwr_stocking_cycle GLOB '[0-9]*'
  AND years_since_stocked >= CAST(dwr_stocking_cycle AS INT);

-- per-species timing
SELECT designation, name, drainage, stock_last_year, stocked_years, stock_total_fish
FROM lake_species WHERE species = 'Tigers' AND stock_last_year >= 2024;

-- shortest hike to water Jed hasn't caught
SELECT designation, name, min_hike_mi, min_hike_hours, min_hike_difficulty,
       hike_numbers, trailheads, species_current
FROM lake_search
WHERE status IS NULL AND fishable AND min_hike_mi <= 8
ORDER BY min_hike_mi;

-- big-fish evidence from the 2025 DWR gillnet tables
SELECT designation, name, drainage, gillnet_species, gillnet_mean_length_in,
       gillnet_max_length_in, gillnet_max_weight_lb
FROM lake_search WHERE gillnet_max_length_in IS NOT NULL
ORDER BY gillnet_max_length_in DESC;

-- lakes DWR has chemically reclaimed (rotenone), and what went back in
SELECT designation, name, drainage, treatment_year, treatment_project,
       treatment_restored, species_current, last_stocked
FROM lake_search WHERE treated = 1 ORDER BY treatment_year DESC;

-- solitude: deep, low pressure, well off any mapped route
SELECT designation, name, drainage, max_depth_ft, size_acres, route_mi,
       fishing_pressure, collection_labels
FROM lake_search
WHERE fishable AND max_depth_ft >= 20 AND route_mi >= 1
  AND (fishing_pressure IN ('Low','Very low') OR fishing_pressure IS NULL)
ORDER BY route_mi DESC;

-- one of Jed's curated sets (see data/collections.json for keys)
SELECT designation, name, drainage, collection_notes
FROM lake_search WHERE collections LIKE '%basin-painter%';

-- a whole basin / trailhead day
SELECT designation, name, elevation_ft, species_current, last_stocked_year, status
FROM lake_search WHERE trailheads LIKE '%Crystal Lake%' ORDER BY min_hike_mi;
```

## Answering well

- Lead with the shortlist, not the SQL. A table of 5–15 lakes beats 60 rows.
- Always carry **designation + name** (many lakes have no name; the
  designation is the key), plus whatever criteria Jed asked about.
- Include `app_url` (`…/uintas100/#A-11`) when he might want to open one on
  his phone — it deep-links straight to that lake's modal in the PWA.
- Say which filters you applied, and flag it when a criterion couldn't be
  filtered cleanly (e.g. only 77 lakes have `dwr_trail_miles`).
- Prose lives in the DB when a shortlist needs colour:
  `raw.lakes.dwr_notes` (DWR pamphlet write-up), `junesucker_notes`,
  `cma_notes` (Andersen book), `jed_notes` / `trip_reports` (Jed's own), and
  `raw.guide_hikes.narrative` (Falcon guide). Pull them for the final few
  candidates, not for the whole result set.
- `data/hike_index.md` is the human-readable hike table if the question is
  really about hikes rather than lakes; `docs/less-visited-lakes.md` and
  `docs/4x4-access-lakes.md` are the worked arguments behind the collections.
- If Jed likes a set enough to keep it, it can become a Collection in
  `data/collections.json` → shows up as a filter chip in the PWA
  (`docs/runbooks/publishing.md`).
