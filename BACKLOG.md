# Backlog

Running list of ideas and follow-ups that aren't urgent enough to do now.

## Content / data

- ~~**Revamp the June Sucker notes.**~~ Done 2026-08-10: `scripts/scrape_junesucker.py`
  re-scrapes all 40 matched lakes section-aware, dropping the DWR-pamphlet and
  "Nearby Areas to Fish" sections that duplicated `dwr_notes`. Remaining judgement
  call: whether the surviving prose (directions / hike / fish species / history)
  should be trimmed further, and whether the modal should de-emphasize the section.

- **Find P-11's location.** Provo River drainage; currently `coord_status = cant_find`
  with no name. It has recent DWR stocking records, so it's a real, stocked water —
  call the DWR to pin down where it is, then place it in the Lake Locator.
  (One other Provo lake is also `cant_find`.)

## Maps

- True offline tiles (PMTiles/OPFS or the Tauri native build) so the satellite/topo
  imagery — not just pins + drainage photos — is available with no signal.
