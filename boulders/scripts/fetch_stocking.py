#!/usr/bin/env python3
"""
Fetch the Utah DWR fish-stocking archive for the Boulder Mountain counties.

Boulder Mountain straddles Wayne and Garfield counties, so both are pulled in
full. The DWR archive begins in 2002 -- earlier years return an empty table --
and runs to the current year.

Pages are cached under data/raw_stocking/ so the parse/classify step can be
re-run offline and so a re-fetch only touches the years that can still change.

    python3 scripts/fetch_stocking.py              # refresh current + prior year
    python3 scripts/fetch_stocking.py --all        # re-fetch every year 2002..now
    python3 scripts/fetch_stocking.py --year 2019
"""

import argparse
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / 'data' / 'raw_stocking'

COUNTIES = ['Wayne', 'Garfield']
FIRST_YEAR = 2002          # DWR archive floor, verified by probing 1990..2004
URL = ('https://dwrapps.utah.gov/fishstocking/FishAjax'
       '?y={year}&sort=watername&sortorder=ASC&sortspecific={county}&whichSpecific=county')


def fetch(county, year, timeout=60):
    req = urllib.request.Request(URL.format(year=year, county=county),
                                 headers={'User-Agent': 'boulders-db/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', errors='replace')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true',
                    help=f'refetch every year from {FIRST_YEAR}')
    ap.add_argument('--year', type=int, help='refetch a single year')
    args = ap.parse_args()

    now = datetime.now().year
    if args.year:
        years = [args.year]
    elif args.all:
        years = list(range(FIRST_YEAR, now + 1))
    else:
        # Late-season stocking is often published after the year rolls over.
        years = [now, now - 1]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ok = failed = 0
    for year in years:
        for county in COUNTIES:
            dest = CACHE_DIR / f'{county}_{year}.html'
            try:
                html = fetch(county, year)
            except (urllib.error.URLError, OSError) as e:
                print(f'  ERROR {county} {year}: {e}', file=sys.stderr)
                failed += 1
                continue
            dest.write_text(html, encoding='utf-8')
            rows = html.count('<tr class="table1">')
            print(f'  {county} {year}: {rows} rows')
            ok += 1
            time.sleep(0.3)   # be polite to a small state server

    print(f'\nFetched {ok} pages ({failed} failed) into {CACHE_DIR}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
