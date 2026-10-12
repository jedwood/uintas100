#!/usr/bin/env python3
"""Photo fixtures for tests/journal: JPEGs with a hand-built EXIF APP1 (Make,
Model, DateTimeOriginal, GPS) in big- and little-endian TIFF order, a PNG
"screenshot" and a fake HEIC, all derived from one plain JPEG (macOS `sips`).
Writes expected.json with the values a correct parser must recover — those
values are independently confirmed by ImageIO (imageio_meta.swift).

    python3 tests/journal/make_fixtures.py <source.jpg> <out_dir>
"""
import json, os, struct, subprocess, sys

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

def strip_app1(jpeg):
    assert jpeg[:2] == b"\xff\xd8"
    out, i = bytearray(b"\xff\xd8"), 2
    while True:
        assert jpeg[i] == 0xFF
        marker = jpeg[i + 1]
        if marker == 0xDA:
            out += jpeg[i:]
            return bytes(out)
        ln = struct.unpack(">H", jpeg[i + 2:i + 4])[0]
        if marker != 0xE1:
            out += jpeg[i:i + 2 + ln]
        i += 2 + ln

def build_tiff(le, make, model, dto, lat, lng, alt, gps_date, gps_time):
    E = "<" if le else ">"
    # entries: (tag, type, count, payload bytes)
    def ascii(s): b = s.encode() + b"\0"; return (2, len(b), b)
    def rat(vals): return (5, len(vals), b"".join(struct.pack(E + "II", n, d) for n, d in vals))
    def long_(v): return (4, 1, struct.pack(E + "I", v))
    def byte(v): return (1, 1, bytes([v]))
    def dms(x):
        x = abs(x); d = int(x); m = int((x - d) * 60); s = (x - d - m / 60) * 3600
        return [(d, 1), (m, 1), (int(round(s * 10000)), 10000)]

    def ifd_bytes(entries, base):
        # entries sorted by tag; returns bytes with out-of-line data after
        entries = sorted(entries.items())
        n = len(entries)
        data_off = base + 2 + n * 12 + 4
        head, data = bytearray(struct.pack(E + "H", n)), bytearray()
        for tag, (typ, count, payload) in entries:
            if len(payload) <= 4:
                head += struct.pack(E + "HHI", tag, typ, count) + payload.ljust(4, b"\0")
            else:
                head += struct.pack(E + "HHII", tag, typ, count, data_off + len(data))
                data += payload + (b"\0" if len(payload) % 2 else b"")
        head += struct.pack(E + "I", 0)
        return bytes(head + data)

    gps = {1: ascii("N" if lat >= 0 else "S"), 2: rat(dms(lat)),
           3: ascii("E" if lng >= 0 else "W"), 4: rat(dms(lng)),
           5: byte(0), 6: rat([(int(alt * 10), 10)]),
           7: rat([(gps_time[0], 1), (gps_time[1], 1), (gps_time[2], 1)]),
           0x1D: ascii(gps_date)}
    exif = {0x9003: ascii(dto)}
    # layout: header(8) | IFD0 | ExifIFD | GPS IFD — compute offsets iteratively
    ifd0_entries = {0x010F: ascii(make), 0x0110: ascii(model), 0x8769: long_(0), 0x8825: long_(0)}
    ifd0 = ifd_bytes(ifd0_entries, 8)
    exif_off = 8 + len(ifd0)
    exif_b = ifd_bytes(exif, exif_off)
    gps_off = exif_off + len(exif_b)
    ifd0_entries[0x8769] = long_(exif_off)
    ifd0_entries[0x8825] = long_(gps_off)
    ifd0 = ifd_bytes(ifd0_entries, 8)
    assert 8 + len(ifd0) == exif_off
    gps_b = ifd_bytes(gps, gps_off)
    header = (b"II" if le else b"MM") + struct.pack(E + "HI", 42, 8)
    return header + ifd0 + exif_b + gps_b

def with_exif(jpeg, tiff):
    body = b"Exif\0\0" + tiff
    app1 = b"\xff\xe1" + struct.pack(">H", len(body) + 2) + body
    return jpeg[:2] + app1 + jpeg[2:]

big = os.path.join(OUT, "_big.jpg")
subprocess.run(["sips", "-z", "3000", "4000", SRC, "--out", big], check=True, capture_output=True)
plain = strip_app1(open(big, "rb").read())
open(os.path.join(OUT, "plain.jpg"), "wb").write(plain)

expected = {}
# near BR-28 (40.7515583, -110.7585861): ~150 m north-east
cases = {
    "gps_be.jpg": dict(le=False, make="Apple", model="iPhone 15 Pro", dto="2024:10:13 09:41:07",
                       lat=40.7528, lng=-110.7575, alt=3215.4, gps_date="2024:10:13", gps_time=(15, 41, 7)),
    "gps_le.jpg": dict(le=True, make="Google", model="Pixel 8", dto="2020:08:02 18:05:00",
                       lat=40.7905, lng=-110.4760, alt=3290.0, gps_date="2020:08:03", gps_time=(0, 5, 0)),
}
for name, c in cases.items():
    open(os.path.join(OUT, name), "wb").write(with_exif(plain, build_tiff(**c)))
    expected[name] = {"lat": c["lat"], "lng": c["lng"], "alt": c["alt"], "make": c["make"],
                      "model": c["model"],
                      "taken": c["dto"][:10].replace(":", "-") + "T" + c["dto"][11:],
                      "gps_time": c["gps_date"].replace(":", "-") + "T%02d:%02d:%02dZ" % c["gps_time"]}
subprocess.run(["sips", "-s", "format", "png", "-z", "600", "800", SRC, "--out",
                os.path.join(OUT, "screenshot.png")], check=True, capture_output=True)
open(os.path.join(OUT, "not-an-image.heic"), "wb").write(b"\0\0\0\x18ftypheic" + os.urandom(200))
os.remove(big)
json.dump(expected, open(os.path.join(OUT, "expected.json"), "w"), indent=1)
