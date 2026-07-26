#!/usr/bin/env python3
"""Schema and shared helpers for the Boulder Mountain database.

create_database() builds the full canonical schema in one place, so no other
script patches columns ad hoc (a lesson carried over from the Uintas project).
"""

import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / 'boulders.db'

SCHEMA = """
CREATE TABLE IF NOT EXISTS waters (
    id                INTEGER PRIMARY KEY,
    dwr_name          TEXT    NOT NULL UNIQUE,  -- canonical DWR name, code included
    name              TEXT    NOT NULL,         -- readable display name
    unit_code         TEXT,                     -- NBS, BTS, GT, TLM ... verbatim
    unit_name         TEXT,                     -- 'North Boulder Slope'
    area              TEXT,                     -- 'Boulder Mountain', 'Griffin Top' ...
    boulder_mountain  INTEGER NOT NULL DEFAULT 0,  -- 1 = "the Boulders" proper
    aquarius_plateau  INTEGER NOT NULL DEFAULT 0,  -- 1 = anywhere on the Aquarius
    classification_basis TEXT,                  -- how the area was decided
    classification_confidence TEXT,             -- high | medium | low
    water_type        TEXT,                     -- lake|reservoir|pond|stream|river|other
    county            TEXT,
    county_suspect    INTEGER NOT NULL DEFAULT 0,  -- DWR county looks wrong
    lat               REAL,
    lng               REAL,
    coord_source      TEXT,                     -- 'gnis'
    gnis_name         TEXT,                     -- official name, if it differs
    first_year        INTEGER,
    last_year         INTEGER,
    stocking_events   INTEGER NOT NULL DEFAULT 0,
    total_stocked     INTEGER NOT NULL DEFAULT 0,
    species_list      TEXT,                     -- denormalized, game species only
    notes             TEXT
);

CREATE TABLE IF NOT EXISTS stocking_records (
    id            INTEGER PRIMARY KEY,
    water_id      INTEGER NOT NULL REFERENCES waters(id),
    species       TEXT,                 -- normalized display name
    species_raw   TEXT NOT NULL,        -- exactly as DWR published it
    species_known INTEGER NOT NULL DEFAULT 1,  -- 0 = not a real species (ALL TROUT)
    quantity      INTEGER,
    length_in     REAL,
    stock_date    TEXT,                 -- YYYY-MM-DD
    source_year   INTEGER,
    county        TEXT,
    -- DWR's report contains sets of byte-identical rows (same water, species,
    -- quantity, length and date). They are preserved rather than silently
    -- collapsed: dup_index/dup_total mark each member of such a set, so a
    -- query can count unique events (dup_index = 1) or every published row.
    dup_index     INTEGER NOT NULL DEFAULT 1,
    dup_total     INTEGER NOT NULL DEFAULT 1,
    qa_flag       TEXT                  -- 'zero-quantity', 'unknown-species', ...
);

CREATE INDEX IF NOT EXISTS idx_stocking_water   ON stocking_records(water_id);
CREATE INDEX IF NOT EXISTS idx_stocking_species ON stocking_records(species);
CREATE INDEX IF NOT EXISTS idx_stocking_year    ON stocking_records(source_year);
CREATE INDEX IF NOT EXISTS idx_waters_area      ON waters(area);

-- One row per water per species: the shape most questions actually want.
CREATE VIEW IF NOT EXISTS water_species AS
SELECT w.id              AS water_id,
       w.name            AS water,
       w.area            AS area,
       w.unit_name       AS unit,
       w.water_type      AS water_type,
       w.county          AS county,
       w.boulder_mountain,
       w.aquarius_plateau,
       s.species         AS species,
       COUNT(*)                AS events,
       SUM(s.quantity)         AS total_stocked,
       MIN(s.source_year)      AS first_year,
       MAX(s.source_year)      AS last_year
FROM waters w
JOIN stocking_records s ON s.water_id = w.id
WHERE s.dup_index = 1 AND s.species_known = 1
GROUP BY w.id, s.species;
"""


def create_database(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def connect(path=DB_PATH, read_only=True):
    if read_only:
        conn = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    else:
        conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
