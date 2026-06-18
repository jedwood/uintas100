"""Shared helpers for the coordinate seeding + Lake Locator tools."""

import re
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "uinta_lakes.db"

# Generous bounding box around the Uinta Mountains (S, W, N, E)
UINTA_BBOX = (40.40, -111.30, 41.05, -109.40)

COORD_COLUMNS = {
    "lat": "REAL",
    "lng": "REAL",
    "coord_source": "TEXT",   # e.g. 'osm-designation', 'osm-name', 'manual'
    "coord_status": "TEXT",   # 'seed_unverified' | 'confirmed' | 'manual' | 'cant_find'
}


def ensure_coord_columns(conn: sqlite3.Connection) -> None:
    """Idempotently add the coordinate columns to the lakes table."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(lakes)")}
    for name, decl in COORD_COLUMNS.items():
        if name not in existing:
            # Coordinate edits shouldn't trip the notes-sync trigger, but the
            # column add itself is harmless; ALTER can't be parameterized.
            conn.execute(f"ALTER TABLE lakes ADD COLUMN {name} {decl}")
    conn.commit()


def normalize_designation(value: str) -> str:
    """'BR - 33' / 'br-33' / 'BR33' -> 'BR33' for robust matching."""
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def normalize_name(value: str) -> str:
    """'Butterfly Lake' / 'butterfly  lk.' -> 'butterfly' for matching."""
    if not value:
        return ""
    name = value.lower()
    name = re.sub(r"\b(lake|lk|reservoir|res|pond)\b", " ", name)
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


# A db designation looks like a designation when it matches LETTERS-DIGITS,
# e.g. BR-25, X-64, GR-19, X-22b. Used to tell named lakes from bare designations.
DESIGNATION_RE = re.compile(r"^[A-Za-z]{1,3}-?\d+[a-z]?$")


def looks_like_designation(letter_number: str) -> bool:
    return bool(DESIGNATION_RE.match((letter_number or "").strip()))
