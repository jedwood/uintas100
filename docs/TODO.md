# TODO

- **Drive time from home to each Falcon trailhead.** Add a per-trailhead
  drive time (and miles) from Jed's house to the 22 `guide_trailheads`, so the
  hike index can answer "hikes under N hours of driving". Needs trailhead
  coordinates first (none are stored yet — the book gives only prose directions;
  candidates: GNIS `data/gnis/DomesticNames_UT.txt` trailhead/campground
  entries, OSM, or hand-placing them in the Locator), then one routing call per
  trailhead (Apple/Google Maps, OSRM, etc.), stored as new columns on
  `guide_trailheads` and surfaced in `data/hike_index.{json,md}` by
  `scripts/build_hike_index.py`. Several trailheads are behind rough 4WD roads,
  so a router's time will undershoot — keep the book's `4wd` access tag beside it.
