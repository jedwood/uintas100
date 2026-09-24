#!/usr/bin/env python3
"""Build USGS-topo contact sheets for eyeballing whether a lake is really remote.

Renders 4 lakes per page: USGS Topo, the OSM route network drawn over the top
(red = foot trail, orange = track/service, yellow = road), 1 km / 2 km rings,
neighbouring lakes labelled. Screenshot them with playwright-cli against a
local static server. Usage:

    python3 scripts/fetch_osm_routes.py
    python3 scripts/lake_trail_distance.py
    echo '{"sheet1": ["RC-36","U-100","U-91","U-79"]}' > /tmp/spec.json
    python3 scripts/build_topo_sheets.py /tmp/spec.json
    cd data/cache/sheets && python3 -m http.server 8811

Written for docs/less-visited-lakes.md (2026-09-23)."""
import json, math, os, shutil, sqlite3, sys

import os
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "data", "cache")
os.makedirs(CACHE, exist_ok=True)

HERE = CACHE
OUT = f"{CACHE}/sheets"; os.makedirs(OUT, exist_ok=True)
DB = os.path.join(REPO, "uinta_lakes.db")

rows = {r["letter_number"]: r for r in json.load(open(f"{CACHE}/lake_trail_distance.json"))}
osm  = json.load(open(f"{CACHE}/osm_routes.json"))
conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row

TRAIL = {"path","footway","bridleway"}
ROUGH = {"track","service"}

def ways_near(lat, lng, pad=0.035):
    out = []
    for e in osm["elements"]:
        g = e.get("geometry")
        if not g: continue
        if not any(abs(p["lat"]-lat) < pad and abs(p["lon"]-lng) < pad for p in g[::3]):
            continue
        hw = e["tags"].get("highway")
        kind = "trail" if hw in TRAIL else ("rough" if hw in ROUGH else "drive")
        out.append({"k": kind, "n": e["tags"].get("name") or "",
                    "c": [[round(p["lat"],5), round(p["lon"],5)] for p in g]})
    return out

def all_lakes_near(lat, lng, pad=0.035):
    return [dict(r) for r in conn.execute(
        "SELECT letter_number,name,lat,lng,no_fish FROM lakes WHERE lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?",
        (lat-pad, lat+pad, lng-pad, lng+pad))]

def panel_data(desig, zoom):
    L = conn.execute("""SELECT letter_number,name,drainage,lat,lng,elevation_ft,size_acres,max_depth_ft,
                        fish_species,fishing_pressure,status,no_fish FROM lakes WHERE letter_number=?""",
                     (desig,)).fetchone()
    r = rows[desig]
    return {"L": dict(L), "zoom": zoom,
            "d_any": r["d_any_m"], "d_drive": r["d_drive_m"], "d_trail": r["d_trail_m"],
            "near": r["near_any"],
            "ways": ways_near(L["lat"], L["lng"]),
            "lakes": all_lakes_near(L["lat"], L["lng"])}

TEMPLATE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="leaflet.css"><script src="leaflet.js"></script>
<style>
 body{margin:0;background:#111;color:#eee;font:12px/1.35 -apple-system,Helvetica,Arial}
 .grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;padding:10px}
 .cell{background:#1c1c1c;border:1px solid #333;border-radius:6px;overflow:hidden}
 .map{height:430px}
 .cap{padding:6px 8px}
 .cap b{font-size:14px;color:#fff}
 .cap .m{color:#9ad;font-weight:600}
 .cap .s{color:#aaa}
 .lg{position:fixed;right:8px;bottom:8px;background:#000c;padding:6px 9px;border-radius:5px;z-index:9999}
 .lg i{display:inline-block;width:18px;height:3px;vertical-align:middle;margin-right:5px}
</style></head><body>
<div class="grid" id="g"></div>
<div class="lg"><span><i style="background:#ff2d2d"></i>path/foot</span> &nbsp;
 <span><i style="background:#ff9500"></i>track/service</span> &nbsp;
 <span><i style="background:#ffe600"></i>road</span> &nbsp;
 <span style="color:#0ff">◎ candidate</span> &nbsp;<span style="color:#fff">· other lake</span> &nbsp;
 <span style="color:#0f8">dashed = 1 km / 2 km from candidate</span></div>
<script>
const DATA = %(data)s;
const COL = {trail:'#ff2d2d', rough:'#ff9500', drive:'#ffe600'};
const g = document.getElementById('g');
DATA.forEach((d,i)=>{
  const L = d.L;
  const cell = document.createElement('div'); cell.className='cell';
  cell.innerHTML = `<div class="map" id="m${i}"></div><div class="cap">
    <b>${L.letter_number}${L.name?' '+L.name:' (unnamed)'}</b> <span class="s">— ${L.drainage||''}</span><br>
    <span class="s">${L.elevation_ft?L.elevation_ft.toLocaleString()+' ft':'elev ?'} ·
    ${L.size_acres?L.size_acres+' ac':'? ac'} · ${L.max_depth_ft?L.max_depth_ft+' ft deep':'depth ?'} ·
    ${L.fish_species||'species ?'} · pressure ${L.fishing_pressure||'?'}${L.status?' · JED '+L.status:''}</span><br>
    <span class="m">${(d.d_any/1000).toFixed(2)} km to nearest mapped route</span>
    <span class="s">(${d.near?d.near[0]+': '+d.near[1]:'?'}) · ${(d.d_drive/1000).toFixed(1)} km to a drivable road</span>
  </div>`;
  g.appendChild(cell);
  const map = L2map(`m${i}`, d);
});
function L2map(id, d){
  const m = L.map(id, {zoomControl:false, attributionControl:false,
                       center:[d.L.lat,d.L.lng], zoom:d.zoom});
  L.tileLayer('https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
              {maxZoom:16}).addTo(m);
  d.ways.forEach(w=>L.polyline(w.c,{color:COL[w.k],weight:w.k=='trail'?2.5:2,opacity:.95}).addTo(m));
  d.lakes.forEach(k=>{
    if(k.letter_number===d.L.letter_number) return;
    L.circleMarker([k.lat,k.lng],{radius:3,color:'#fff',weight:1,fillOpacity:.5}).addTo(m)
     .bindTooltip(k.letter_number,{permanent:true,direction:'right',className:'lbl'});
  });
  [1000,2000].forEach(r=>L.circle([d.L.lat,d.L.lng],{radius:r,color:'#0f8',weight:1,
      dashArray:'5,6',fill:false,opacity:.8}).addTo(m));
  L.circleMarker([d.L.lat,d.L.lng],{radius:8,color:'#0ff',weight:3,fill:false}).addTo(m);
  return m;
}
</script>
<style>.lbl{background:#000a;border:0;color:#fff;font-size:10px;padding:0 2px;box-shadow:none}
.lbl:before{display:none}</style>
</body></html>"""

def build(name, desigs, zoom=14):
    data = [panel_data(d, zoom) for d in desigs]
    html = TEMPLATE % {"data": json.dumps(data)}
    p = f"{OUT}/{name}.html"; open(p, "w").write(html)
    return p

if __name__ == "__main__":
    # the sheets reference Leaflet relatively, so vendor it alongside them
    for asset in ("leaflet.css", "leaflet.js"):
        shutil.copy(os.path.join(REPO, "vendor", "leaflet", asset), os.path.join(OUT, asset))
    spec = json.load(open(sys.argv[1]))
    for name, desigs in spec.items():
        print(build(name, desigs, zoom=14))
