# The Boulders

A stocking database for **Boulder Mountain**, Utah — the eastern half of the
Aquarius Plateau, straddling Wayne and Garfield counties. Same idea as the
Uintas project one directory up, but data-only for now: no front end.

```bash
python3 scripts/query.py summary
python3 scripts/query.py species --has Grayling --only
python3 scripts/query.py water blind
```

## What's in it

**130 waters, 4,222 stocking records, 2002–2026** — the full depth of the DWR
online archive, which returns an empty table for any year before 2002.

| Scope | Waters | Events |
|---|---:|---:|
| Boulder Mountain proper (`--scope boulders`, the default) | 84 | 2,088 |
| \+ Griffin Top and the Escalante Mountains (`--scope aquarius`) | 98 | 2,412 |
| Everything DWR stocks in Wayne + Garfield (`--scope all`) | 130 | 3,932 |

That last scope includes the Panguitch/Bryce/Escalante-town lowlands, which
share the two counties but sit up to 69 miles from Boulder Top. They are kept in
the database — dropping them would hide DWR's own county framing — but they are
excluded from every default query.

## Two counties, not one

Boulder Mountain spans **Wayne** (north and east slopes, Boulder Top) and
**Garfield** (south and west slopes, North Creek Lakes). There is no single
county that contains it, and neither county contains only it.

## The unit-code discovery

DWR appends an undocumented geographic management-unit code to most water names
in these two counties. This matters enormously: `BLIND L NBS` and `BLIND L TLM`
are two different Blind Lakes 30 miles apart, and a name-only matcher merges
them. Likewise `ROUND L NBS`/`ROUND L TLM`, `GREEN L NBS`/`GREEN L EBS`,
`BLUE L NCL`/`BLUE L GT`, `GRASS L TLM`/`GRASS L SB`.

The codes were reverse-engineered from the data and confirmed against outside
sources:

| Code | Meaning | On Boulder? |
|---|---|---|
| `BT` / `BTN` / `BTS` | Boulder Top, and its north / south halves | yes |
| `NBS` / `NB` | North Boulder Slope / North Boulder | yes |
| `EBS` / `EB` | East Boulder Slope / East Boulder | yes |
| `SB` | South Boulder | yes |
| `NCL` | North Creek Lakes | yes — "extreme southwest extension" |
| `GT` | Griffin Top | Aquarius, not Boulder proper |
| `EMW` | Escalante Mountains, west | Aquarius, not Boulder proper |
| `TLM` | Thousand Lake Mountain | no — a separate mountain to the north |

Confirmations: junesucker.com files `GREEN L NBS` under
`/green-lake-north-boulder-slope/`; Visit Utah writes "Blue Lake (Griffin Top)",
matching `BLUE L GT`; Dixie NF describes Barker Reservoir as "within the North
Creek Lakes drainage … an extreme southwest extension of Boulder Mountain". The
unit clusters also separate cleanly by GNIS coordinates. Codes are stored
verbatim in `waters.unit_code`, so a wrong gloss costs nothing.

Waters with **no** code are classified by hand in
[`data/water_classification.csv`](data/water_classification.csv), one row per
water with an `area`, a `confidence`, and a written `basis`. The main source
there is a Boulder Mountain Blue Ribbon fishery guide that groups waters by the
same slope scheme DWR uses.

## No golden trout — anywhere on Boulder Mountain

The obvious first question, "which lakes hold goldens and only goldens", has no
answer here. A sweep of the **entire** DWR archive (all counties, all years)
finds just **9 golden trout records across 6 waters**, all 2012–2015, and every
one is in the Uintas:

Atwood (U-16), Echo (Z-16), Jean (W-58), U-19, Mt. Emmons (U-13), Marsh (GR-39).

Zero in Wayne or Garfield. Boulder Mountain has too much native Colorado River
cutthroat range to justify an exotic. The equivalent Boulders questions are
grayling-only (Circle Lake, Clark Lake) or brookie-only (12 waters).

## Data problems found and handled

- **171 sets of byte-identical rows** (290 extra rows) — same water, species,
  quantity, length and date. Preserved, not silently collapsed:
  `dup_index`/`dup_total` mark each set, and every default query filters to
  `dup_index = 1`.
- **`GUNLOCK TOWN POND` is filed under Wayne county** but Gunlock is in
  Washington county, ~250 miles away. Flagged via `waters.county_suspect`.
- **`BULBERRY` vs `BULLBERRY`** — DWR spells the same lake group both ways in
  one report. Normalized to the GNIS spelling.
- **Stray double spaces** — `CLEAR L  NBS`, `ROW L  8 GT` — collapsed, or they
  fork one water into two.
- **`ALL TROUT`** at Posey Lake in 2006 is not a species. Kept (the fish were
  really stocked) but `species_known = 0` so it never appears in a species list.
- **6 records with quantity 0.** Flagged `zero-quantity`.
- **GNIS calls Posey Lake "Posy Lake"** — one `e`. Aliased.
- **Non-game transplants** (one sucker plant, one dace plant) are excluded from
  `species_list`, so a management move can't break an "only holds X" query.
- **Name collisions are resolved by unit centroid.** A GNIS candidate is
  rejected if it lies more than 15 miles from its unit's centre — which is what
  stops `HEART L … NBS` from being placed on the Heart Lake at 38.50 N, and
  `DONKEY L NBS` from landing on the Garfield "Donkey Lake" 30 miles south.
  8 candidates were rejected this way; 86 of 130 waters are placed.

Six low-volume waters could not be placed in any area and are marked
`Unclassified` rather than guessed: May Day Pond, Deer Creek (Mitchell), Spring
Lake, Three Mile Creek (+ its north fork), and Gates Lake — whose DWR county
may itself be wrong, since the only GNIS Gates Lake is in Sevier county.

## Layout

```
boulders/
  boulders.db                     rebuilt from scratch by build_database.py
  data/
    water_classification.csv      curated areas for uncoded waters (git-diffable)
    dwr_stocking_data.csv         full-fidelity export of every loaded row
    raw_stocking/                 cached DWR pages (gitignored)
  scripts/
    fetch_stocking.py             DWR -> data/raw_stocking/
    build_database.py             cache -> boulders.db  (+ QA report)
    query.py                      the CLI
    water_utils.py                name parsing, unit codes, classification
    species_utils.py              species normalization
    db_utils.py                   schema
```

GNIS coordinates come from `../data/gnis/DomesticNames_UT.txt`, shared with the
Uintas project rather than duplicated. A statewide DWR snapshot lives in
`../data/dwr_archive/` so no future project needs to re-scrape.

## Refresh

```bash
python3 scripts/fetch_stocking.py     # current + prior year
python3 scripts/build_database.py     # rebuild, prints a QA report
```

`build_database.py` drops and recreates the database every run, so the cached
pages plus `water_classification.csv` are the only inputs that matter.

## Query cookbook

```bash
# one species and nothing else, lakes only
python3 scripts/query.py species --has Grayling --only --type lake,reservoir,pond

# waters holding every species in a list
python3 scripts/query.py species --has Brookies,Tigers,Grayling --all-of

# still being stocked recently, biggest first
python3 scripts/query.py list --since 2020 --sort fish

# widen past Boulder proper
python3 scripts/query.py species --has Grayling --scope aquarius

# anything else
python3 scripts/query.py sql "SELECT name, species_list FROM waters
                              WHERE boulder_mountain=1 AND lat IS NULL"
```

The `water_species` view (one row per water per species) is the convenient
starting point for ad-hoc SQL.
