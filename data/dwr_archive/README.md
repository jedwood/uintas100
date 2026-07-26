# Utah DWR statewide stocking archive (snapshot)

A complete local copy of Utah DWR's online fish-stocking report, **all counties,
all years**, so no future project has to re-scrape it.

| File | What it is |
|---|---|
| `utah_stocking_all_counties.csv.gz` | 59,357 parsed records, 2002–2026 |
| `raw_html.tar.gz` | the 25 unparsed year pages the CSV was built from |

Snapshot taken **2026-07-25**.

## Source

```
https://dwrapps.utah.gov/fishstocking/FishAjax?y=<YEAR>&sort=watername&sortorder=ASC&sortspecific=<VALUE>&whichSpecific=<FACET>
```

Three facets are known to work:

| Facet | Example | Use |
|---|---|---|
| `whichSpecific=label` | `sortspecific=ALL` | **everything for a year** — how this snapshot was built |
| `whichSpecific=county` | `sortspecific=Summit` | one county-year |
| `whichSpecific=species` | `sortspecific=GOLDEN%20TROUT` | one species-year |

Each response is an HTML fragment of `<tr class="table1">` rows with six cells:
`watername | county | species | quantity | length | stockdate (MM/DD/YYYY)`.

## CSV columns

`water_name, county, species, quantity, length, stock_date, source_year`

Values are verbatim DWR strings — ALL-CAPS species codes, unnormalized water
names. Normalize at read time; don't edit this file.

## Known quirks

- **2002 is the practical floor.** Years before that return an empty table.
- **A handful of rows fall outside 2002–2026** and look like `stockdate` year
  typos: 1984 (5 rows, Summit), 1995 and 1998 (Doudy Pond, Box Elder), 2001
  (Big Sandwash Res), plus future-dated 2027 (2 rows) and 2035 (2 rows,
  Jordanelle). A sweep that hard-codes 2002–present will miss them.
- **Exact-duplicate rows exist** — byte-identical water/species/quantity/length/
  date. e.g. `WEBER R` 1984 appears 3×, `JORDANELLE RES` 2035 twice, and 171 such
  rows sit in Wayne/Garfield alone. Decide deliberately whether to collapse them.
- **`ALL TROUT`** (37 rows) is a generic aggregate, not a species.
- **`CUTBOW CTBL*RTWV`** (12 rows) contains an asterisk that breaks naive parsing.
- **Water names carry regional suffix codes** that disambiguate same-named
  waters — `BLIND L NBS` and `BLIND L TLM` are two different Blind Lakes 30 miles
  apart. Never match on the bare name. See `boulders/scripts/water_utils.py` for
  the decoded Wayne/Garfield codes.
- **Whitespace is unreliable** — `ROW L  8 GT` and `U- 19` contain stray internal
  spaces. Collapse runs of whitespace before matching.

## Validation

Built by an unfiltered statewide sweep, then cross-checked against an
independent per-county scrape of Wayne and Garfield: both produced exactly
**4,222** rows for those counties with zero county-year discrepancies, differing
only in whether stray internal double-spaces were collapsed.

## Consumers

- `boulders/` — Boulder Mountain database (Wayne + Garfield)
- the Uintas pipeline still fetches live per-county; this snapshot is a
  historical backstop and a source for one-off analysis.
