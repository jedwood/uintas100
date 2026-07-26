#!/usr/bin/env python3
"""
Ask questions of the Boulder Mountain database.

    # the headline shape: waters holding ONE species and nothing else
    query.py species --has Grayling --only
    query.py species --has Splake

    # waters stocked with every species in a list (and possibly others)
    query.py species --has Brookies,Tigers --all-of

    # everything about one water
    query.py water blind

    # inventories
    query.py list --type lake --sort events
    query.py species-list
    query.py summary

    # escape hatch
    query.py sql "SELECT name, species_list FROM waters WHERE lat IS NULL"

Scope defaults to Boulder Mountain proper. Widen with --scope aquarius (adds
Griffin Top and the Escalante Mountains) or --scope all (every water DWR stocks
in Wayne and Garfield counties, including the Panguitch/Bryce lowlands).
"""

import argparse
import sqlite3
import sys
import textwrap

from db_utils import DB_PATH, connect

SCOPES = {
    'boulders': 'w.boulder_mountain = 1',
    'aquarius': 'w.aquarius_plateau = 1',
    'all':      '1=1',
}


def scope_clause(args):
    where = [SCOPES[args.scope]]
    params = []
    if args.type:
        where.append('w.water_type IN (%s)' % ','.join('?' * len(args.type.split(','))))
        params += [t.strip() for t in args.type.split(',')]
    if args.since:
        where.append('w.last_year >= ?')
        params.append(args.since)
    return ' AND '.join(where), params


def fmt_table(rows, headers):
    if not rows:
        return '  (no matches)'
    cols = [list(map(lambda r: '' if r[i] is None else str(r[i]), rows))
            for i in range(len(headers))]
    widths = [max(len(headers[i]), max((len(v) for v in cols[i]), default=0))
              for i in range(len(headers))]
    out = ['  ' + '  '.join(h.ljust(widths[i]) for i, h in enumerate(headers)),
           '  ' + '  '.join('-' * widths[i] for i in range(len(headers)))]
    for r in rows:
        out.append('  ' + '  '.join(
            ('' if r[i] is None else str(r[i])).ljust(widths[i])
            for i in range(len(headers))))
    return '\n'.join(out)


# ---------------------------------------------------------------------------

def cmd_species(conn, args):
    wanted = [s.strip() for s in args.has.split(',') if s.strip()]
    if not wanted:
        sys.exit('--has requires at least one species')

    known = {r[0] for r in conn.execute(
        'SELECT DISTINCT species FROM stocking_records WHERE species_known = 1')}
    for s in wanted:
        if s not in known:
            close = sorted(k for k in known if k.lower().startswith(s.lower()[:3]))
            hint = f'  Did you mean: {", ".join(close)}' if close else ''
            print(f'WARNING: {s!r} has never been stocked anywhere in this '
                  f'database.{hint}', file=sys.stderr)

    where, params = scope_clause(args)

    if args.only:
        # Waters whose entire game-species history is a subset of `wanted`.
        # Non-game species (sucker, dace) are excluded from species_list at
        # build time, so a management transplant does not disqualify a water.
        placeholders = ','.join('?' * len(wanted))
        sql = f"""
            SELECT w.name, w.unit_name, w.water_type, w.species_list,
                   w.first_year, w.last_year, w.stocking_events, w.total_stocked
            FROM waters w
            WHERE {where}
              AND w.species_list IS NOT NULL
              AND NOT EXISTS (
                    SELECT 1 FROM stocking_records s
                    WHERE s.water_id = w.id AND s.species_known = 1
                      AND s.species NOT IN ({placeholders})
                      AND s.species NOT IN ('Sucker','Dace'))
              AND EXISTS (
                    SELECT 1 FROM stocking_records s
                    WHERE s.water_id = w.id AND s.species IN ({placeholders}))
            ORDER BY w.total_stocked DESC
        """
        rows = conn.execute(sql, params + wanted + wanted).fetchall()
        title = f'Waters stocked with {" / ".join(wanted)} AND NOTHING ELSE'
    elif args.all_of:
        sql = f"""
            SELECT w.name, w.unit_name, w.water_type, w.species_list,
                   w.first_year, w.last_year, w.stocking_events, w.total_stocked
            FROM waters w
            WHERE {where}
              AND (SELECT COUNT(DISTINCT s.species) FROM stocking_records s
                   WHERE s.water_id = w.id AND s.species IN ({','.join('?' * len(wanted))})) = ?
            ORDER BY w.total_stocked DESC
        """
        rows = conn.execute(sql, params + wanted + [len(wanted)]).fetchall()
        title = f'Waters stocked with ALL of {" + ".join(wanted)}'
    else:
        sql = f"""
            SELECT w.name, w.unit_name, w.water_type, w.species_list,
                   MIN(s.source_year), MAX(s.source_year),
                   COUNT(*), SUM(s.quantity)
            FROM waters w JOIN stocking_records s ON s.water_id = w.id
            WHERE {where} AND s.dup_index = 1
              AND s.species IN ({','.join('?' * len(wanted))})
            GROUP BY w.id ORDER BY SUM(s.quantity) DESC
        """
        rows = conn.execute(sql, params + wanted).fetchall()
        title = f'Waters stocked with any of {" / ".join(wanted)}'

    print(f'\n{title}   [scope: {args.scope}]\n')
    print(fmt_table([tuple(r) for r in rows],
                    ['Water', 'Unit', 'Type', 'All species ever stocked',
                     'First', 'Last', 'Events', 'Fish']))
    print(f'\n  {len(rows)} water(s)\n')


def cmd_water(conn, args):
    like = f'%{args.name}%'
    waters = conn.execute("""
        SELECT * FROM waters
        WHERE name LIKE ? OR dwr_name LIKE ? OR gnis_name LIKE ?
        ORDER BY boulder_mountain DESC, name""", (like, like, like)).fetchall()
    if not waters:
        sys.exit(f'No water matching {args.name!r}')
    for w in waters:
        print(f'\n=== {w["name"]} ===')
        loc = f'{w["lat"]:.4f}, {w["lng"]:.4f}' if w['lat'] else 'unknown'
        print(f'  DWR name       {w["dwr_name"]}')
        if w['gnis_name']:
            print(f'  GNIS name      {w["gnis_name"]}')
        print(f'  Area           {w["area"] or "?"}'
              f'{"  (" + w["unit_name"] + ")" if w["unit_name"] else ""}')
        print(f'  Type / county  {w["water_type"]} / {w["county"]}'
              f'{"  [county suspect]" if w["county_suspect"] else ""}')
        print(f'  Coordinates    {loc}')
        print(f'  Basis          {w["classification_basis"]} '
              f'(confidence: {w["classification_confidence"]})')
        if w['notes']:
            print('\n'.join(textwrap.wrap(f'  Note           {w["notes"]}',
                                          96, subsequent_indent=' ' * 17)))
        print(f'  Species        {w["species_list"] or "(none)"}')
        print(f'  Stocked        {w["first_year"]}-{w["last_year"]}, '
              f'{w["stocking_events"]} events, {w["total_stocked"]:,} fish\n')
        rows = conn.execute("""
            SELECT species, COUNT(*), SUM(quantity), MIN(source_year), MAX(source_year),
                   ROUND(AVG(length_in),2)
            FROM stocking_records WHERE water_id = ? AND dup_index = 1
            GROUP BY species ORDER BY SUM(quantity) DESC""", (w['id'],)).fetchall()
        print(fmt_table([tuple(r) for r in rows],
                        ['Species', 'Events', 'Fish', 'First', 'Last', 'Avg in']))
        print()


def cmd_list(conn, args):
    where, params = scope_clause(args)
    order = {'events': 'w.stocking_events DESC', 'fish': 'w.total_stocked DESC',
             'name': 'w.name', 'area': 'w.area, w.name'}[args.sort]
    rows = conn.execute(f"""
        SELECT w.name, w.area, w.unit_name, w.water_type, w.species_list,
               w.first_year, w.last_year, w.stocking_events, w.total_stocked
        FROM waters w WHERE {where} ORDER BY {order}""", params).fetchall()
    print(f'\nWaters   [scope: {args.scope}'
          f'{", type " + args.type if args.type else ""}]\n')
    print(fmt_table([tuple(r) for r in rows],
                    ['Water', 'Area', 'Unit', 'Type', 'Species',
                     'First', 'Last', 'Events', 'Fish']))
    print(f'\n  {len(rows)} water(s)\n')


def cmd_species_list(conn, args):
    where, params = scope_clause(args)
    rows = conn.execute(f"""
        SELECT s.species, COUNT(DISTINCT w.id), COUNT(*), SUM(s.quantity),
               MIN(s.source_year), MAX(s.source_year)
        FROM waters w JOIN stocking_records s ON s.water_id = w.id
        WHERE {where} AND s.dup_index = 1 AND s.species_known = 1
        GROUP BY s.species ORDER BY COUNT(DISTINCT w.id) DESC""", params).fetchall()
    print(f'\nSpecies stocked   [scope: {args.scope}]\n')
    print(fmt_table([tuple(r) for r in rows],
                    ['Species', 'Waters', 'Events', 'Fish', 'First', 'Last']))
    print()


def cmd_summary(conn, args):
    print('\n=== Boulder Mountain stocking database ===\n')
    for label, sql in [
        ('Waters by area', """
            SELECT COALESCE(area,'(none)'), COUNT(*), SUM(stocking_events),
                   SUM(total_stocked)
            FROM waters GROUP BY area ORDER BY 3 DESC"""),
    ]:
        print(f'{label}:')
        print(fmt_table([tuple(r) for r in conn.execute(sql)],
                        ['Area', 'Waters', 'Events', 'Fish']))
        print()
    print('Boulder Mountain units:')
    print(fmt_table([tuple(r) for r in conn.execute("""
        SELECT unit_name, COUNT(*), SUM(stocking_events), SUM(total_stocked)
        FROM waters WHERE boulder_mountain = 1 AND unit_name IS NOT NULL
        GROUP BY unit_name ORDER BY 2 DESC""")],
        ['Unit', 'Waters', 'Events', 'Fish']))
    r = conn.execute("""SELECT COUNT(*), MIN(source_year), MAX(source_year)
                        FROM stocking_records""").fetchone()
    print(f'\n{r[0]:,} stocking rows, {r[1]}-{r[2]}')
    q = conn.execute("""SELECT COUNT(*) FROM stocking_records WHERE dup_index > 1""").fetchone()[0]
    print(f'{q} of them are exact republished duplicates (dup_index > 1)')
    n = conn.execute('SELECT COUNT(*) FROM waters WHERE lat IS NULL').fetchone()[0]
    print(f'{n} waters still have no coordinates\n')


def cmd_sql(conn, args):
    try:
        rows = conn.execute(args.statement).fetchall()
    except sqlite3.Error as e:
        sys.exit(f'SQL error: {e}')
    if not rows:
        print('  (no rows)')
        return
    print()
    print(fmt_table([tuple(r) for r in rows], list(rows[0].keys())))
    print(f'\n  {len(rows)} row(s)\n')


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--scope', choices=SCOPES, default='boulders')
    ap.add_argument('--type', help='water_type filter, e.g. lake or lake,reservoir')
    ap.add_argument('--since', type=int, help='only waters stocked in/after this year')

    # The same scope flags are accepted after the subcommand, which is where
    # they read most naturally ("species --has X --only --type lake").
    # SUPPRESS keeps an omitted flag here from clobbering one given up front.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--scope', choices=SCOPES, default=argparse.SUPPRESS)
    common.add_argument('--type', default=argparse.SUPPRESS)
    common.add_argument('--since', type=int, default=argparse.SUPPRESS)

    sub = ap.add_subparsers(dest='cmd', required=True, parser_class=(
        lambda **kw: argparse.ArgumentParser(parents=[common], **kw)))

    p = sub.add_parser('species', help='find waters by species')
    p.add_argument('--has', required=True, help='comma-separated species')
    g = p.add_mutually_exclusive_group()
    g.add_argument('--only', action='store_true',
                   help='waters holding these species and no others')
    g.add_argument('--all-of', action='store_true',
                   help='waters holding every listed species')
    p.set_defaults(fn=cmd_species)

    p = sub.add_parser('water', help='detail for one water')
    p.add_argument('name')
    p.set_defaults(fn=cmd_water)

    p = sub.add_parser('list', help='list waters')
    p.add_argument('--sort', choices=['events', 'fish', 'name', 'area'], default='name')
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser('species-list', help='all species with counts')
    p.set_defaults(fn=cmd_species_list)

    p = sub.add_parser('summary', help='database overview')
    p.set_defaults(fn=cmd_summary)

    p = sub.add_parser('sql', help='run arbitrary read-only SQL')
    p.add_argument('statement')
    p.set_defaults(fn=cmd_sql)

    args = ap.parse_args()
    if not DB_PATH.exists():
        sys.exit(f'{DB_PATH} not found -- run scripts/build_database.py first.')
    conn = connect(read_only=True)
    args.fn(conn, args)


if __name__ == '__main__':
    main()
