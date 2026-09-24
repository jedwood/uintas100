# Uinta lakes that are less likely to be visited

Compiled 2026-09-23. Companion to `4x4-access-lakes.md` — and in several places its
mirror image: a lake that scores well here usually scores badly there.

## How this was built

Three passes, deliberately independent, then reconciled by hand.

**Pass 1 — semantic read of every description.** Seven agents, one per drainage
group, read the *full text* of every fishable lake in the range: DWR pamphlet
write-ups (current **and** superseded edition), Cordell Andersen's book notes,
junesucker.com pages, the Falcon guide's hike rows, the DWR 2025 survey tables,
and Jed's own notes and trip reports. **579 fishable lakes** (`no_fish = 0`),
~730 KB of source text, all of it read — not keyword-matched. They were told to
judge meaning, not vocabulary: "there is no trail and both routes are cross
country," "for anglers who like solitude and ruggedness," "the trail soon
disappears and you just have to bushwhack," "this lake is seldom visited."
Every claim below is a verbatim quote with its source and edition year.

**Pass 2 — geometry, for the lakes no one wrote up.** The OSM trail and road
network for the whole range (9,791 ways: foot trails, pack trails, jeep tracks,
service roads, highways) was pulled from Overpass, densified to 100 m spacing
and indexed, then every one of the 738 lakes with trusted coordinates was
measured against it. Two numbers per lake:

- **off-route** — straight-line distance to the *nearest mapped route of any
  kind*. This is the off-trail proxy.
- **to road** — straight-line distance to the nearest drivable road. This is the
  how-deep-in proxy.

**Pass 3 — actually looking.** Candidates were rendered onto USGS topo contact
sheets (this session's throwaway tool: Leaflet + USGS Topo, the OSM route network
drawn over the top in red/orange/yellow, 1 km and 2 km rings around the
candidate, neighbouring lakes labelled) and read by eye — cirque or meadow, tight
contours or open bench, genuinely isolated or merely unlabelled. **40 lakes were
inspected this way**, including all 15 fishable lakes that have no description at
all. This pass changed the answer for nine of them.

## Read the caveats before you trust a number

- **OSM trail coverage in the Uintas is uneven, in both directions.** Some real
  USFS trails are unmapped, so a lake can look more isolated than it is (W-64
  Elkhorn reads 3.0 mi from a "trail" but 96 yards from a jeep track). And some
  mapped `path` ways are cross-country routes, not trails — RC-11 Sea Lion
  measures 0.08 mi off-route even though DWR calls it "one of the most
  inaccessible waters of the Rock Creek drainage." **Neither number is evidence
  on its own.** They are used here only to corroborate or challenge the text.
- **Most DWR write-ups date from 1981–1999.** Trails named in them have grown
  over, and pressure ratings have drifted. Where the 2025 editions exist (Bear
  River, Blacks Fork, Whiterocks) they are quoted in preference.
- **Straight-line, not trail miles.** "1.5 mi off-route" across a talus headwall
  is a different day than 1.5 mi across a meadow. The topo panels were how that
  got judged.
- **Fishless and "probably no fish" lakes were excluded** (`no_fish` 1 and 2 —
  167 lakes). A few entries below are flagged because the *pamphlet* wrongly
  says fishless while DWR quietly keeps stocking them; that gap is the point.
- **Rotenone warning.** Andersen records a DWR proposal to treat the Fall Creek,
  Ottoson, Oweep and Garfield drainages between 2022 and 2034, and the Carter
  Creek project already ran in Aug 2021. **Confirmed since:** the West Fork Smiths
  Fork treatment of Aug 30 – Sep 1, 2021 took in two lettered lakes, **G-64** and
  **G-113** — see `lake_treatments` and the PWA's rotenone modal. That touches **X-87, X-88, X-89, X-90,
  X-94's neighbourhood, X-100, X-113, X-121, LF-21, LF-22, LF-30, GR-22, GR-23,
  GR-24** below. Several score well *because* they were just restocked. Confirm
  status with DWR before a long trip.

Jed status: 🎣 = CAUGHT, 👥 = OTHERS, ⭐ = starred, blank = not yet.

---

## Tier A — the shortlist

Text, geometry and topo all agree, and there is a real fishery at the end of it.
Ordered roughly by how confident I am.

| Lake | Size / depth / elev | Off-route | To road | Fish | The case |
|---|---|---|---|---|---|
| **WR-34 Katy** (Whiterocks) | 9.0 ac / **45 ft** / 11,200 | 1.07 mi | 4.3 mi | Cutts, stocked →2024 | DWR (2025): *"This cold, remote lake is stocked with cutthroat trout. Fishing pressure is very light. Katy Lake is a good lake to visit and be by yourself."* CMA independently: *"rarely visited."* Topo: a closed high basin NW of Point Lake, tight contours on every side, no route within a mile. **45 ft at 11,200 ft means it overwinters.** The single best text+map+fish agreement in the range. |
| **U-93** (Uinta River) | 11.1 ac / 8 ft / 11,402 | 1.05 mi | **10.4 mi** | Cutts →2023 | The **only lake in the whole database rated "Very low"** pressure. DWR (1997): *"This is one of the most remote lakes in the Uinta River drainage."* Falcon #58 rates Painter Basin usage Light and difficulty *"High—cross-country travel"* on a 32.5-mile round trip. Against it: 8 ft deep, and Falcon says the cutts *"either bite or they don't, and if they do, they are small."* Go for the place. |
| **U-88** (Uinta River) | 14.0 ac / 18 ft / 11,030 | 1.37 mi | **10.7 mi** | wild Brookies, never stocked | Falcon #58: *"Angling pressure is almost nil, and eager brook trout should be fighting one another to get to your lure first."* DWR: *"a natural population of nice brook trout."* Largest lake in Painter Basin, wild fish so no stocking dependence. Best fish-per-solitude ratio found. |
| **U-98 Penny Nickell** (Uinta River) | 11.5 ac / **43 ft** / 10,710 | **2.03 mi** | 5.8 mi | Cutts →2025 | **3rd-most off-route fishable lake in the range**, and the deepest of the three. DWR (1997): *"There is no trail to the lake and its best to use a U.S.G.S. map for directions."* CMA: *"fishing pressure very light."* 43 ft plus a steady stocking cadence is the holdover-fish profile — of everything beyond 2 miles off-route, this is the one most likely to hold big fish. |
| **RC-8 Thompson** (Rock Creek) | 21.2 ac / 26 ft / 10,690 | 0.75 mi | 7.0 mi | Brookies →**2026** | DWR (1997): *"Thompson is a remote lake of typical glacial origin located in a rocky cirque… Access by horse is impossible across the extensive boulder fields between Cyclone Pass and the lake. Fishing pressure is very light."* CMA: *"One mile of boulder hopping to remote Thompson Lake."* Best size+depth of the truly remote Rock Creek group, and freshly stocked. |
| **BR-46 Lorena** (Bear River) | 12.8 ac / 20 ft / 10,580 | 1.21 mi | 2.8 mi | Brookies →2025 | DWR's own 2025 words: *"This remote lake provides a good opportunity for anglers seeking solitude in the Bear River basin,"* with *"1.5 miles up the steep and rocky ridge… should not be attempted on horseback."* CMA: *"Solitude is the name of the game."* Only 3.5 trail miles total — the best solitude-per-mile on the list. |
| **X-94 Crater** (Lake Fork) | 28.0 ac / **147 ft** / 11,268 | 1.59 mi | **10.0 mi** | Splake →2026, Tigers | **The deepest lake in the High Uintas**, at 11,268 ft, 17 miles from Moon Lake, and still rated Low pressure. Splake stocked four times through 2026. The one caveat the Lake Fork agent raised is fair — Andersen writes it up glowingly twice, so "light" may not hold — but 147 ft of water with splake in it is unique in this range. |
| **WR-73 Tamara** (Whiterocks) | 7.1 ac / 18 ft / 10,960 | 1.72 mi | 4.4 mi | Cutts →2023 | DWR (2025): *"Total distance from the West Fork Trailhead is 4.2 miles, all of it is cross-country."* — the most explicit off-trail sentence found anywhere. Sits at the very head of the Rasmussen basin, which DWR says has **no maintained trails at all**. |
| **Y-16 Doll** (Yellowstone) | **42.5 ac / 47 ft** / 11,352 | 1.04 mi | 8.5 mi | wild Brookies, abundant | DWR (1996): *"Access is 3/4 mile west-northwest of Five Point Reservoir up a trailless ridge for a total distance of 13 miles."* Both DWR and CMA say light pressure and an abundant self-sustaining brookie population. **The best size-to-solitude ratio in the range** — a 42-acre, 47-foot lake behind a trailless ridge. Fish are pan-sized: numbers, not trophies. |
| **G-5 Cliff** (Henrys Fork) | 33.1 ac / **69 ft** / 11,443 | 0.97 mi | 9.2 mi | Cutts →2025, Tigers | DWR (1986): *"This remote alpine lake receives relatively light angler use… These fish are unusually wary and may be difficult to catch."* CMA adds *"the possibility of large fish."* A mile of open tundra above the Basin Trail. The exception to being skeptical of Henrys Fork — the crowd is on the Kings Peak line, not here. |
| **WR-55 Walk Up** (Whiterocks) | 18.4 ac / **60 ft** / 11,114 | 1.53 mi | 2.2 mi | Brookies →2022 | Falcon #64 rates usage **Very light** — the lowest rating on any hike in the drainage — and says: *"its inaccessibility keeps it a quiet place."* DWR: *"a deep bowl with surrounding cliffs towering a thousand feet above the surface."* junesucker: *"Do not attempt if you're not in great hiking shape."* Protected by the climb, not the mileage — only 2.2 mi from a road. |
| **RC-42 Cabin** (Rock Creek) | 4.3 ac / 16 ft / 10,450 | 1.31 mi | 3.3 mi | Cutts →2022 + wild Brookies | Three sources agree. DWR: *"Angling pressure is quite light due to the inaccessibility of the lake."* Falcon #40: *"Cabin Lake gets very little usage. This isolated lake sits all by its lonesome in its own little basin… Tall tales of this lake speak of big, healthy brook trout."* A 1-mile boulder-field add-on to a long trip. |
| **X-87 Ottoson Upper** (Lake Fork) | 12.4 ac / 30 ft / 11,099 | 1.35 mi | **10.5 mi** | Cutts →2022 | DWR (1996): *"the last 2 miles are trailless over open tundra,"* 15 miles from Moon Lake. Falcon #45 rates the basin **Light**. Best-shaped water in Ottoson Basin. ⚠️ Inside the proposed rotenone area — check status. |
| **U-15 Roberts** (Uinta River) | 23.3 ac / **38 ft** / 11,550 | 1.21 mi | 9.3 mi | Cutts →2023 + wild Brookies | DWR: *"Follow a faint trail 1.5 miles west of Mt. Emmons Lake through a wet meadow, and zigzag a steep ravine… No camping or horse feed is available in this windswept tundra area."* CMA confirms the faint trail and the ravine. Deepest high-cirque water in the Atwood group. DWR warns success is *"quite variable."* |
| **GR-144 Coffin** (Beaver Creek) | 25.8 ac / 28 ft / 10,853 | 0.96 mi | 6.0 mi | Cutts →2024, Tigers | DWR (1986): *"There is no trail to the lake and the terrain is rough… Angling pressure is light."* 25 acres and 28 ft in a talus-walled cirque, and the crowd stops at Beaver Lake three-quarters of a mile short. Pairs with GR-145 and GR-177 — see basins below. |
| **X-15 Doc's** (Rock Creek) | 14.5 ac / **45 ft** / 9,882 | 0.84 mi | 1.9 mi | Brookies →2025 | DWR (1997): *"This isolated lake is in heavy timber high on a rocky bench… There are no trails to the lake, and the lake can be difficult to find. Access is via three miles of hard climbing."* Deepest trailless lake in the drainage and the lowest here at 9,882 ft, so it opens early. Caveat: only 1.9 mi from a road — the protection is the timber and the climb. |

---

## The five trailless basins

The strongest finding isn't a lake, it's a **basin**. Five places have multiple
fish-bearing lakes with no mapped route touching any of them. Each is one trip.

### 1. Upper Crow Canyon (Dry Gulch) — seven lakes, zero trails
The clearest case in the range. The topo shows the entire DG chain with **not one
mapped route in the basin**. DWR on DG-14: *"There is no trail to the lake."* All
stocked through **2025**.

| Lake | Size / depth | Off-route | Fish | DWR pressure |
|---|---|---|---|---|
| **DG-9** | 10 ac / **27 ft** | 1.45 mi | Cutts →2025 | Low |
| **DG-10** | 10 ac / 12 ft | 1.25 mi | Cutts →2025 | *"Angling pressure is very light"* |
| **DG-14** | 2 ac / 10 ft | 1.78 mi | Cutts →2025 | *"very light"* |
| **DG-15 / DG-16 / DG-17** | 3 ac each / 8–12 ft | 1.20–1.30 mi | Cutts →2025 | *"very light"* ×3 |
| **DG-27 Hidden** | 10 ac / **39 ft** | 1.05 mi | Brookies →**2026** | *"Hidden is isolated lake in the head of Heller basin"* |

Route: Timothy Creek Road to Jackson Park, down the rim to DG-6, follow the DG-6
inlet 1/2 mi and up the rock escarpment to **DG-9** (the deep one), then the DG-9
inlet a further mile to **DG-10**. DG-14/15/16/17 sit at the head. DG-27 Hidden is
a separate leg off Heller Reservoir on *"a poorly marked trail."*

### 2. Upper Rasmussen (Whiterocks) — DWR: "no maintained trails in this basin"
**WR-73 Tamara** (Tier A), **WR-77 Becky** (6.2 ac / 24 ft, 1.89 mi off, Brookies
→2024 — DWR: *"There is no trail and both routes are cross country through downed
timber and rocky terrain… receives very little fishing pressure"*), **WR-74 Ann**
(3.4 ac / 14 ft, Cutts →2025, *"very light"*), **WR-75 Nellie**, **WR-76 Eric**
(wild brookies *and* cutts, no stocking needed), **WR-33 Cirque** (Grayling
→**2026**, at the toe of a rock glacier). Six to seven lakes, one basin, and DWR
states outright there are no maintained trails in it. 3.5–4.4 mi from a road, so
it's a short approach to a genuinely trailless place.

### 3. Painter Lakes Basin (Uinta River) — the deepest-in cluster
**U-93** and **U-88** (Tier A), plus **U-89** (11.5 ac / 15 ft, Brookies →2022),
**U-85 Craig** (the gateway lake — has the basin's only campsites, so parties stop
there), **U-91** (no write-up anywhere, Cutts stocked 6× through 2024), and
**U-76 / U-75 / U-74 Beard** up by Trail Rider Pass. Everything here is **9.5–10.7
miles from a drivable road** — the deepest-in group in this report. Falcon #58:
32.5 miles round trip, usage Light, difficulty *"High—cross-country travel."*
Entry is a river ford and a 900-ft climb on a vague trail.

CMA on **U-75**: *"I had caught there a very large brook trout, and figured any
survivors would really be big."*

### 4. Beaver Lake cirques (Beaver Creek) — three off-trail lakes above one camp
**GR-144 Coffin** (Tier A) → **GR-145** 1/8 mi further *"up the talus ridge"*
(5.6 ac, Grayling ×6) → **GR-177** (18.3 ac, reached by *"an obscure sheep trail…
very difficult to locate and follow"*). Basecamp at Beaver Lake, which is busy;
everything above it is not.

### 5. Weyman Lakes Basin (Sheep/Carter) — past where the horses stop
DWR repeatedly marks the line: *"Horses should be ridden only as far as Anson
Lakes."* Beyond it: **GR-13** (*"up rock slides and across rough boulder fields…
Fishing pressure is very light"*), **GR-15 Sesame** (*"some of the roughest
boulder fields in the Uintas. Use caution when traversing the rocks. Even 5 ton
boulders can sometimes shift when stepped on"* — and **new grayling in 2026**),
**GR-12 Clear** (10 ac / 25 ft, Tigers), **GR-7 Hidden** (8.5 ac / 26 ft).

---

## Tier B — strong picks, one caveat each

| Lake | Size / depth / elev | Off-route | To road | Fish | Case, and the caveat |
|---|---|---|---|---|---|
| **BR-43** (Bear R.) ⭐ | 1.7 ac / 10 ft / 11,120 | 1.01 mi | 3.4 mi | Tigers →**2026** | DWR (2025): *"BR-43 is isolated in a glacial cirque just north of Lamotte Peak, the rugged country making it difficult to reach."* The **previous edition said "This lake does not sustain fish life"** — the best anti-advertising there is. Caveat: 1.7 acres. |
| **BR-44** (Bear R.) | 3.5 ac / 15 ft / 10,900 | 1.38 mi | 3.1 mi | Tigers →2024 | *"BR-44 lies in an isolated basin and access is difficult"* — 5.25 trail miles then 1.75 mi west up a steep drainage. Do it with BR-43 in one trip. |
| **RC-11 Sea Lion** (Rock Ck) | 7.9 ac / 11 ft / 10,385 | *0.08 mi* | 5.8 mi | Cutts →2025 | DWR: *"one of the most inaccessible waters of the Rock Creek drainage… impossible by horse."* 12.7 mi in. **The off-route number is wrong** — OSM has a `path` that is really the boulder-field route. Trust the text. Caveat: 11 ft, winterkill risk. |
| **RC-38 Horseshoe** (Rock Ck) | 2.9 ac / 20 ft / 10,118 | 0.76 mi | 4.5 mi | Brookies →**2026** | DWR: *"Difficult to find without a topographic map… This lake is seldom visited."* Caveat: 2.9 acres, no campsites — a quick tick. |
| **RC-45 Audrey** (Rock Ck) ⭐ | 13.2 ac / 25 ft / 10,021 | 1.50 mi | 1.7 mi | Brookies →2022, aerial only | DWR: *"a remote, seldom visited pond located in a cirque… Access to the lake is difficult by foot and likely impossible on horseback."* Caveat: the approach starts on the Miners Gulch jeep trail — overlaps the 4x4 report. |
| **U-73 Milk** (Uinta R.) | 13.1 ac / **35 ft** / 11,236 | 0.67 mi | 8.1 mi | wild Brookies + Cutts | DWR: *"The last mile is extremely rocky and trailless… Fishing pressure is very light."* Falcon: *"If you feel alone and remote at Milk Lake, it's because, well, you are."* Caveat: no stocking record, both species asterisked. |
| **U-5 Oke Doke** (Uinta R.) | 12.9 ac / **38 ft** / 11,320 | 1.15 mi | 8.7 mi | Cutts →2023 | DWR: *"Oke Doke is ideal for a small group of one to three backpackers who want to get off the beaten trail."* No inlet or outlet, so it holds fish. Caveat: hangs off the Chain Lakes trail, which Falcon rates **Heavy**. |
| **U-59 Divide** (Uinta R.) | 18.9 ac / **39 ft** / 11,217 | 0.13 mi | 7.2 mi | Cutts →2025 (9,498 fish) | DWR: *"Angling pressure is considered light and limited to day use"* — nobody camps there. CMA: *"the reputation of being very good fishing for larger than normal fish."* Caveat: it's **on** the trail, 2 mi from Heavy-use Fox Lake. |
| **U-82 Gilbert** (Uinta R.) | 14.6 ac / 20 ft / 11,459 | 1.77 mi | 6.9 mi | Cutts →2023 | **20.5 trail miles** from U-Bar Ranch — the longest walk-in of any light-pressure lake here — and no Falcon hike routes anyone to it. Caveat: DWR says the trail is good, so the barrier is pure distance; late-summer sheep grazing. |
| **X-14 Farney** (Rock Ck / Marsell) | 12.6 ac / 14 ft / 10,320 | *0.10 mi* | 4.1 mi | **Grayling →2026, 17,981 fish** | Best short-effort pick found. DWR: *"1/2 mile west through downed timber with no trail."* Neighbouring Fish Hatchery Lake (pressure Heavy) absorbs everyone. The heaviest grayling commitment in the dataset. Caveat: occasional winterkill. |
| **G-73 Bobs** (Blacks Fork) | 6.1 ac / **30 ft** / 11,150 | *0.06 mi* | 3.4 mi | Cutts →2025, Tigers | DWR (2025): the Middle Fork Trail *"is blazed but receives limited use and can be indistinct and extremely difficult to locate in areas. The trail disappears in large headwater meadows."* CMA agrees. **The off-route number is meaningless here** — OSM maps a trail that barely exists. |
| **G-74** (Blacks Fork) | 2.9 ac / 3 ft / 10,934 | — | — | Brookies →2024 | Same vanished Middle Fork trail, and it *has* campsites, spring water and horse feed — the natural basecamp for a Bobs trip. DWR: *"G-74 experiences very light angler use."* Caveat: 3 ft deep. |
| **G-105 Wagonwheel** (Blacks Fork) | 2.2 ac / 3 ft / 10,820 | 0.69 mi | 6.3 mi | **native, never stocked** | DWR biologist Matt McKell, quoted by CMA: *"Lake G-105 is very remote… it has a population of genetically pure Colorado River Cutthroat Trout. The lake has never been stocked and the population is entirely natural and native."* Caveat: 2.2 acres, 3 ft. Go for what the fish *are*. |
| **G-67** (Blacks Fork) | 7.1 ac / 25 ft / 11,158 | 1.22 mi | 5.6 mi | Brookies →**2026** | 9.5 trail miles into a rugged above-timberline cirque on a drainage Falcon rates **Light**; the 2025 pamphlet records no campsites and no horse feed. |
| **GR-152** (Beaver Ck) | 4.8 ac / 13 ft / 11,295 | 0.90 mi | 5.4 mi | Brookies →**2026** | DWR (1986): *"GR-152 is stocked with brook trout and is seldom visited by anglers."* 10 miles in, two successive off-trail ridge climbs, under Gilbert Peak. Caveat: not ice-free until mid-July. |
| **GR-130 Snow** (Burnt Fork) | 9.4 ac / **35 ft** / 10,550 | 0.98 mi | 5.4 mi | Cutts →**2026** | DWR: *"surrounded on three sides by talus slides and ledges… Horse access is impossible. No campsites are available."* Physically hostile to horses and to camping, which filters both. Caveat: inside the Island Lake orbit. |
| **GR-25 Judy** (Sheep/Carter) | 4.7 ac / 24 ft / 10,830 | 0.64 mi | 1.6 mi | Tigers →2023 | DWR: *"This seldom visited, picturesque pond sits on a high bench… A hard scramble up 400 vertical feet."* CMA: *"rarely visited."* Best fishery-per-effort found — 1.8 mi total. Caveat: 1.6 mi from a road; busy Tamarack directly below. |
| **X-60 / X-57** (Yellowstone) | 8.0 ac / **30 ft**; 8.8 ac / **30 ft** | 0.40 / 0.72 mi | 4.6 mi | Cutts →2025 / Brookies →2022 | Both *"up a trailless slope"* above Swasey Hole, which DWR calls popular with heavy pressure. Two 30-ft lakes for a third of a mile and a mile of climbing. The classic everyone-stops-at-the-big-one setup. |
| **X-78** (Lake Fork) | **17.0 ac** / 18 ft / 10,636 | 0.76 mi | 6.5 mi | Cutts →2025, **10,183 fish** | *"1 mile through trailless timber."* The heaviest stocking of any trailless lake in the dataset, which makes DWR's cautious *"a few cutthroat trout may be present"* badly out of date. Caveat: Clements is moderate-to-heavy, so the first 11 mi are busy. |
| **W-28 Jerry** (Weber) | 3.2 ac / 16 ft / 10,220 | 0.78 mi | 3.5 mi | Brookies →**2026** | DWR (1999): *"This remote natural lake… There are no clearly defined trails… Angling pressure is light and campsites are not established."* OSM itself tags the nearest route *"Middle Fork Weber River Trail (overgrown)."* Stocked 12× — the most frequent cadence here. Caveat: occasional winterkill. |
| **W-58 Jean** (Weber) | 3.0 ac / 25 ft / 10,100 | 1.13 mi | 3.6 mi | Grayling →2024, Goldens* | Both approaches are bad on purpose: *"an obscure trail over the steep pass into Hell's Kitchen,"* or a trail that *"is not maintained and is difficult to follow. Topographic maps are useful to locate the lake."* One of a handful of Uinta waters ever planted with goldens (2014–15; almost certainly gone). Caveat: 1999 route notes over an unmaintained trail are 27 years stale. |
| **DF-4** (Ashley Ck) | 10.0 ac / 23 ft / 10,830 | 1.23 mi | 4.2 mi | Cutts →2025 | DWR (1981), almost a sales pitch: *"This lake is for anglers who like solitude and ruggedness."* Follow Reynolds Creek to its spring source *"then head due west over boulder terrain."* Caveat: starts at jeep-reachable Blanchett Park. |
| **GR-28 Upper Potter** (Sheep/Carter) | **21.3 ac / 75 ft** / 10,130 | 0.21 mi | 4.1 mi | wild Brookies + Cutts →**2026** | *Added after the data fix — the DB had it as a 4-acre, 28-ft, High-pressure pond.* DWR (1996): *"a faint trail cuts off to the south… A topo map is a good thing to carry… Campsites are not available in the immediate vicinity due to the rough terrain. There is no horse feed or spring water… Upper Potter is not stocked; however, the lake contains a self-sustaining population of brook trout. Fishing pressure is light."* **75 ft is the deepest wild-brookie water in the drainage**, 6.5 mi from Browne Lake, and DWR has since added cutthroat (5×, 7,707 fish, through 2026). Caveat: the faint spur is mapped in OSM, so the 0.21 mi figure understates it. |
| **GR-62 Bert** (Ashley Ck) | 3.7 ac / 11 ft / 10,220 | **1.69 mi** | 3.8 mi | Grayling →**2026** + Brookies | DWR: *"Horse access is impossible over the rocky, timbered terrain… This attractive lake seldom receives anglers or campers."* CMA: *"rarely receives visitors."* Three off-trail legs deep, two species, currently stocked. |
| **X-81 Hook** (Lake Fork) | **21.0 ac** / 19 ft / 10,722 | 1.17 mi | 7.1 mi | Brookies →**2026** | 18 miles in, then *"1 mile south of Picture Lake over rugged terrain"*; CMA calls the last mile *"somewhat difficult bushwhacking."* Has camping and spring water, so you can base there. The quiet alternative to Picture, which is the named Falcon destination. |
| **U-27 Samuals** (Uinta R.) | 4.8 ac / 7 ft / 10,995 | 0.79 mi | 7.9 mi | wild Brookies, abundant | DWR recommends it outright: *"Try this commonly 'passed up' lake and avoid the people usually present at the Kidney and Fox lakes."* Caveat: 7 ft, horse-friendly — overlooked rather than hard. |
| **U-39** (Uinta R.) | 5.3 ac / 9 ft / 11,160 | 0.43 mi | 7.8 mi | **Grayling →2026** | DWR (1997) tells every reader: *"This lake is no longer managed to provide any recreational fishing."* DWR has since stocked grayling **seven times, 3,862 fish, through 2026**. Anyone working from the book walks past. That gap is the entire case. |
| **GR-148 Dine** (Beaver Ck) | 5.1 ac / 15 ft / 10,460 | 0.37 mi | 4.3 mi | **Grayling →2026** | DWR: *"Dine is subject to light fishing pressure and is a good choice for anglers seeking solitude."* Brand-new grayling in a lake nobody walks to. Caveat: *"known to winterkill on occasion,"* and closer to the North Slope Highline than the text implies. |
| **A-15 Hidden** (Provo) | 8.2 ac / 25 ft / 9,760 | 0.50 mi | 2.8 mi | Brookies →**2026** | The one Provo lake worth listing: *"Hidden is situated in a small, remote basin and is difficult to locate. A topographic map may be helpful."* The last 2¼ mi are on a segment DWR calls indistinct. Caveat: pressure Moderate — hard to find hasn't meant unvisited. |
| **P-62 Shingle Creek Lower** (Provo) | 4.0 ac / 14 ft / 9,620 | 0.67 mi | 1.5 mi | wild Brookies | Three sources agree there's no trail and a 300-ft wall. Dan Potts, in Jed's notes: *"this lake cannot handle a lot of fishing pressure. A good lake for those who are more adventuresome."* Caveat: the only stocking on record is 121 tigers in 2014 — it's a wild-brookie gamble. |

---

## Batch 2 — the lakes with no description at all

Jed's second ask. Fifteen fishable lakes in the database have **no DWR write-up,
no Andersen entry and no junesucker page** — RC-36 is the archetype. Each was put
on the topo with the trail network overlaid. The map settled nine of them.

| Lake | Off-route | To road | Fish | Verdict |
|---|---|---|---|---|
| **U-100** (Uinta R.) | **2.25 mi** | 4.3 mi | Grayling →**2026** | ✅ **Best of the batch.** 2nd-most off-route fishable lake in the range. A hanging bench below U-99 Wall, steep glacial step, no route within two miles. Grayling stocked six times through 2026 — the fish are current. |
| **RC-36** (Rock Ck) | 1.05 mi | 6.1 mi | Brookies ×5 →2022 | ✅ **Jed's instinct was right.** A shelf under Brown Duck Mountain east of the Tworoose Pass Trail, tight contours, 6 mi from a road, near X-81 Hook and Horseshoe. DWR quietly stocked it five times over twenty years and no published source has ever described it. |
| **U-91** (Uinta R.) | 1.66 mi | **10.5 mi** | Cutts ×6 →2024 | ✅ **Strong.** Inside the trailless Painter Lakes basin with U-88/U-89/U-93. Stocked more consistently than any other undescribed lake. See basin 3. |
| **U-79** (Uinta R.) | 1.43 mi | 6.9 mi | Brookies ×5 →2022 | ✅ **Good.** A trailless bench in Gilbert Creek Basin / North Fork Gilbert Creek, inside the High Uintas Wilderness, 1.4 mi off the Highline. |
| **U-22** (Uinta R.) | 0.38 mi | **10.1 mi** | Brookies ×6 →2024 | ✅ **Good, for depth-in.** A high pocket near Trail Rider Pass and Lake George Beard, above the Chain Lakes–Atwood Trail. Close to a trail but **10 miles from any road** — the distance is the filter. |
| **Y-32** (Yellowstone) | 0.77 mi | 7.6 mi | Grayling →**2026** | ⚠️ **Worth a look.** Trailless, 7.6 mi from a road, fresh grayling. But it sits 1.1 mi from Five Point Reservoir, which DWR calls heavily camped. (One agent said "1/2 mile" — measured, it's 1.78 km / 1.1 mi.) |
| **X-50** (Swift Ck) | 0.20 mi | 6.7 mi | Grayling →**2026** | ⚠️ **Marginal.** 6.7 mi from a road with current grayling, but it sits right by the Jackson Park Trail in the Farmers Lake / White Miller pocket. |
| **GR-129** (Burnt Fork) | 0.54 mi | 5.3 mi | Brookies* | ❌ **Drop.** One plant ever — 493 brookies in 2012. Species is already marked historical. Probably no fishery. |
| **P-16 Charity** (Provo) | 0.55 mi | 1.1 mi | Brookies ×7 →2026 | ❌ **Obscure, not remote.** Jed's own note: *"It's in the stocking reports, but is mentioned nowhere else online that I could find!"* — true, and it took a DWR biologist to place it. But the topo puts it squarely in the Notch Mountain / Wall Lake / Clegg corridor, ringed by trails, **1.1 mi from a drivable road.** The isolation is informational only. |
| **D-45** (Duchesne) | 0.58 mi | **1.1 mi** | Tigers* | ❌ **Wrong report.** Murdock Basin — the topo shows it surrounded by ATV track. Belongs to `4x4-access-lakes.md`. |
| **P-11** (Provo) | 0.13 mi | 2.5 mi | Brookies ×8 →2026 | ❌ **On the trail.** Sits on the North Fork Provo River trail between Duck/Pot/Weir and A-17/A-20. Busiest trail network in the range. |
| **G-113** (Smiths Fork) | 0.14 mi | 3.5 mi | **CRCT →2023** | ♻️ **Reclassified — the single plant was the point.** The original verdict here ("one plant of 276 fish", dismissed) was wrong, and the stocking record was the tell we misread. G-113 was **rotenone-treated Aug 30 – Sep 1, 2021** as part of DWR's West Fork Smiths Fork Colorado River cutthroat restoration, then restocked 2023-09-19 with ~270 CRCT fingerling from the North Slope brood at Mammoth Creek Hatchery — our 276-fish row *is* that event. UDWR, *Cutthroat Trout Report, Northern Region, 2023*, p. 52: *"a small headwater lake, G-113, which was also part of the rotenone treatment."* Still not remote (0.14 mi off-route, 3.5 mi from a road), so it stays out of the solitude tiers — but it is now a pure-strain CRCT water in a drainage that has none other, which is a different reason to go. See `lake_treatments`. |
| **GR-119** (Sheep/Carter) | 0.48 mi | 0.5 mi | Grayling ×4 →2019 | ❌ **Half a mile from the Spirit Lake Road.** A meadow pond. Nothing since 2019. |
| **BR-50** (Bear R.) | 0.30 mi | 0.4 mi | Brookies ×13 →2026 | ❌ **Roadside — but useful.** 0.4 mi from a drivable road on the Whiskey Creek corridor (Falcon usage Heavy). Its only description turns out to live on junesucker's *BR-1 Bourbon* page: *"There is no trail to BR-50 and you will likely need a GPS to find it… Marshes and downed trees make this lake difficult to fish."* A GPS detour, not a destination. |
| **GR-3 Spirit Lake** (Sheep/Carter) | 0.12 mi | 0.1 mi | Cutts, Tigers | ❌ **It's a drive-to resort lake** with a lodge. Blank notes are a data gap, not remoteness. |

**Net:** five real finds (U-100, RC-36, U-91, U-79, U-22), two maybes, seven out, and **one reclassified** (G-113 — not remote, but a 2021 rotenone restoration water).
Note that **four of the five winners are in the Uinta River drainage** — it has by
far the most undescribed-but-stocked water in the range.

---

## Traps — reads remote, isn't

Worth knowing so you don't burn a weekend on them.

| Lake | Why it reads remote | Why it isn't |
|---|---|---|
| **A-11 Azure** (Provo) | DWR: *"Access is limited to backpackers due to the presence of large rockslides. Recreational use is very light."* junesucker: *"Do not attempt this hike if you're not in great shape."* | **0.8 mi from a drivable road**, in the middle of the Spring Canyon jeep-road network. The boulder field is real; the remoteness isn't. Grayling →2026 make it a fine *short* trip. |
| **GR-57 Fish** (Ashley Ck) | 1.6 mi off-route, 17.5 ac / 40 ft | DWR pressure **High**: *"Litter and mosquitoes are a nuisance."* A dotted Macks Park route runs right to it. |
| ~~**GR-28 Upper Potter**~~ | *Not a trap after all* — the DB's `High` pressure and 4.3 ac / 28 ft were a **transcription error**, now corrected to 21.3 ac / 75 ft / Low (see Data issues). | **Promote it.** DWR (1996): a faint spur off the Lamb Lakes trail, *"A topo map is a good thing to carry if you are not familiar with the country,"* no campsites, no horse feed, and *"a self-sustaining population of brook trout"* in **75 feet** of water 6.5 mi from Browne Lake. On the corrected numbers this belongs in Tier B — it is the deepest wild-brookie lake in the Sheep/Carter drainage and nobody was looking at it. |
| **W-64 Elkhorn** (Weber) | The single largest gap to a mapped *foot trail* in the range (3.0 mi) | 96 yards from a jeep track. First 4.5 mi of the approach is road. |
| **WR-48 Watkins** (Whiterocks) | DWR: *"Very few fishermen."* 36 ft deep, no trail | **100 yards from the Cliff Lake 4WD road terminus.** Already in the 4x4 report. |
| **W-37 Bench** (Weber) | Every published source says it has no fish — *"no longer managed for fishing"* | On the Notch Mountain Loop, 2.5 mi from Bald Mountain TH, corridor usage **Heavy**. But DWR planted **339 grayling in 2026**, reversing the reputation. Low visitation here is purely reputational — worth a look in 2027–28 to see if they held. |

---

## Data issues this turned up

Seven were flagged. On checking each against the committed source files, **four
were real errors and are now fixed** by `scripts/fix_data_issues_2026_09_23.py`
(idempotent; re-running reports no changes). Three turned out not to be errors —
recorded here so nobody "fixes" them later on the same bad reasoning.

### Fixed

1. **GR-28 Upper Potter — three wrong fields.** The DB held `size_acres 4.3 /
   max_depth_ft 28 / fishing_pressure High`. Both independent sources agree on
   **21.3 acres / 75 ft / Low**: `data/norrick_lakes.txt:353`
   (*"Potter, Upper, GR-28  21.3  75  Brook trout (naturally reproducing)  Low"*)
   and the lake's own 1996 `dwr_notes` (*"Upper Potter Lake is 21.3 acres,
   10,130 feet in elevation with a maximum depth of 75 feet… Fishing pressure is
   light."*). The stored values matched **neither** source — a transcription
   error, not a disagreement. This one mattered: it was hiding a 21-acre,
   75-foot, light-pressure lake behind a 4-acre pond rated High.
2. **WR-40 Wooley — `fishing_pressure` Moderate → Low.** Every other physical
   field on this record is lifted verbatim from the 2025 pamphlet (*"sits at
   10,680 feet… 20.5 surface acres with a maximum depth of 42 feet"* — note
   Norrick says 18 acres, so the record had already moved to the 2025 edition).
   Only the pressure field was left at Norrick's older "Moderate" while the same
   2025 sentence says *"fishing pressure is light."* Internally inconsistent
   about its own source edition.
3. **X-77 → X-49: a misattributed Andersen paragraph.** CMA p.326 prints
   *"TWIN (X-77): Access is 3/4 mile northwest of White Miller… 10,816 ft.
   elevation, 14 acres, 15' deep… Cutthroat trout."* Those numbers are an exact
   match for **X-49 Twin** (Swift Creek: 14.0 ac / 15 ft / 10,816 ft, Cutthroats),
   and both White Miller (X-54) and Farmers (X-23) are Swift Creek lakes. Lake
   Fork's X-77 Twin is a different lake (12.9 ac / 15 ft / 10,594 ft, Grayling)
   that was showing a stranger's stats in the PWA modal; X-49 had no CMA note at
   all. Paragraph moved, with an editor's note recording the book's misprint.
4. **G-73 → U-73: the same error again.** CMA p.292 prints *"MILK (G-73): …At
   11,236 ft. elevation, 13.1 acres, 35' deep… Abundant Cutthroat trout, rarely
   fished."* Exact match for **U-73 Milk** (Uinta River: 13.1 ac / 35 ft /
   11,236 ft) — a G/U designation typo. The surrounding U-80/U-81/U-83 sentences
   in the same block are Uinta lakes too, so the whole p.292 block moved to
   U-73, which had no CMA note.

### Checked and deliberately left alone

5. **X-121 Continent `fishing_pressure = Moderate` — not an error.**
   `data/norrick_lakes.txt:277` says Moderate; the 1997 pamphlet says *"Fishing
   pressure is light."* The physical fields (27.4 ac / 23 ft) match **both**, so
   the record is faithfully Norrick-sourced and this is two contemporaneous
   independent sources disagreeing — unlike WR-40, there is no newer edition to
   break the tie. Overwriting one with the other would manufacture confidence
   that doesn't exist. Treat Continent's pressure as genuinely uncertain.
6. **The undescribed lakes' missing fields — not fixable.** All fifteen batch-2
   lakes lack elevation, acreage and depth. There is no source: none of them
   appears in `norrick_lakes.txt` or in `dwr_lake_summary`. Left NULL rather
   than invented. If you ever get numbers for U-100, U-91, U-79, U-22 and
   RC-36 — the five that are actively stocked — they're worth entering.
7. **Name collisions — not an error, but worth knowing.** **U-99 "Wall L"**
   (Uinta River, grayling, no write-up) is a completely different lake from
   **A-29 Wall** (Provo, 80 ac, 97 ft, pressure High). Likewise **GR-7 Hidden**
   (Weyman Basin) vs **GR-112 Hidden** (Spirit Lake) vs **DG-27 Hidden** vs
   **A-15 Hidden** — four lakes, one name; DWR flags the first pair itself.
   These are what the sources genuinely call them.

Two things noticed but left for you to judge, since both are pipeline questions
rather than bad rows:

- **GR-28's `fish_species` reads `Brookies*, Cutthroats`.** The asterisk marks
  brookies as historical, but DWR describes a *self-sustaining* brook trout
  population, so the flag looks wrong. It is derived by `species_utils.py` from
  stocking records, which is exactly the case a naturally-reproducing population
  defeats — a pipeline question, not a one-row fix.
- **Andersen paragraph bleed is normal, not a bug.** 92 of the 440 records with
  `cma_notes` carry sentences about neighbouring lakes, because the book's prose
  runs lakes together. Only the two genuinely *misattributed* paragraphs above
  were touched; the ordinary bleed was left intact.

---

## Appendix A — the 60 most off-route fishable lakes

Straight-line distance to the nearest mapped route of any kind (OSM), then to the
nearest drivable road. Read with the caveats at the top — this is corroboration,
not evidence.

| # | Lake | Drainage | Off-route | To road | Elev | Acres | Depth | DWR pressure | Species | Last stocked |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **U-99** Wall L | Uinta River | 2.53 mi | 4.3 mi | — | — | — | — | Grayling | 2020 |
| 2 | **U-100** *(unnamed)* | Uinta River | 2.25 mi | 4.3 mi | — | — | — | — | Grayling | 2026 |
| 3 | **U-98** Penny Nickell | Uinta River | 2.03 mi | 5.8 mi | 10,710 | 11.5 | 43 | Low | Cutthroats | 2025 |
| 4 | **BR-45** Baker | Bear River | 2.00 mi | 2.4 mi | 10,420 | 3.4 | 8 | Moderate | Tigers | 2026 |
| 5 | **WR-77** Becky | White Rocks | 1.89 mi | 3.5 mi | 10,960 | 6.2 | 24 | Low | Brookies, Cutthroats | 2024 |
| 6 | **DG-14** *(unnamed)* | Dry Gulch | 1.78 mi | 5.0 mi | 11,000 | 2 | 10 | Low | Cutthroats | 2025 |
| 7 | **U-82** Gilbert | Uinta River | 1.77 mi | 6.9 mi | 11,459 | 14.6 | 20 | Low | Brookies*, Cutthroats | 2023 |
| 8 | **WR-73** Tamara | White Rocks | 1.72 mi | 4.4 mi | 10,960 | 7.1 | 18 | Low | Brookies*, Cutthroats | 2023 |
| 9 | **GR-62** Bert | Ashley Creek | 1.69 mi | 3.8 mi | 10,220 | 3.7 | 11 | Low | Brookies, Grayling | 2026 |
| 10 | **WR-14** Upper Rock | White Rocks | 1.67 mi | 1.7 mi | 10,562 | 33.4 | 28 | Low | Cutthroats | 2025 |
| 11 | **U-91** *(unnamed)* | Uinta River | 1.66 mi | 10.5 mi | — | — | — | — | Cutthroats | 2024 |
| 12 | **GR-57** Fish | Ashley Creek | 1.61 mi | 4.3 mi | 10,745 | 17.5 | 40 | High | Cutthroats* | never |
| 13 | **WR-75** Nellie | White Rocks | 1.59 mi | 4.0 mi | 10,691 | 2.7 | 8 | Low | Brookies*, Cutthroats | 2023 |
| 14 | **X-94** Crater | Lake Fork | 1.59 mi | 10.0 mi | 11,268 | 28 | 147 | Low | Brookies*, Splake, Tigers | 2026 |
| 15 | **WR-55** Walk Up | White Rocks | 1.53 mi | 2.2 mi | 11,114 | 18.4 | 60 | Low | Brookies | 2022 |
| 16 | **GR-177** *(unnamed)* | Beaver Creek | 1.52 mi | 6.2 mi | 10,860 | 18.3 | 11 | — | Cutthroats* | never |
| 17 | **WR-74** Ann | White Rocks | 1.51 mi | 4.1 mi | 11,000 | 3.4 | 14 | Low | Cutthroats | 2025 |
| 18 | **U-45** *(unnamed)* | Uinta River | 1.51 mi | 7.0 mi | 11,425 | 5 | 5 | Low | Cutthroats | 2023 |
| 19 | **U-89** *(unnamed)* | Uinta River | 1.51 mi | 10.8 mi | 11,037 | 11.5 | 15 | Low | Brookies | 2022 |
| 20 | **RC-45** Audrey | Rock Creek | 1.50 mi | 1.7 mi | 10,021 | 13.2 | 25 | Low | Brookies | 2022 |
| 21 | **U-85** Craig | Uinta River | 1.49 mi | 10.2 mi | 10,848 | 9.3 | 14 | Low | Brookies*, Cutthroats | 2018 |
| 22 | **U-94** Albert | Uinta River | 1.49 mi | 6.1 mi | 10,826 | 7 | 8 | Low | Cutthroats* | never |
| 23 | **DG-9** *(unnamed)* | Dry Gulch | 1.45 mi | 4.3 mi | 10,750 | 10 | 27 | Low | Cutthroats | 2025 |
| 24 | **U-79** *(unnamed)* | Uinta River | 1.43 mi | 6.9 mi | — | — | — | — | Brookies, Cutthroats* | 2022 |
| 25 | **WR-76** Eric | White Rocks | 1.41 mi | 3.5 mi | 10,610 | 4.2 | 7 | Unknown | Brookies*, Cutthroats* | never |
| 26 | **GR-145** *(unnamed)* | Beaver Creek | 1.40 mi | 6.4 mi | 11,020 | 5.6 | 11 | Low | Cutthroats*, Grayling | 2020 |
| 27 | **WR-40** Wooley | White Rocks | 1.39 mi | 3.3 mi | 10,680 | 20.5 | 42 | Low | Brookies, Tigers | 2022 |
| 28 | **BR-44** *(unnamed)* | Bear River | 1.38 mi | 3.1 mi | 10,900 | 3.5 | 15 | Low | Tigers | 2024 |
| 29 | **U-88** *(unnamed)* | Uinta River | 1.37 mi | 10.7 mi | 11,030 | 14 | 18 | Low | Brookies* | never |
| 30 | **X-87** Ottoson Upper | Lake Fork | 1.35 mi | 10.5 mi | 11,099 | 12.4 | 30 | Low | Cutthroats | 2022 |
| 31 | **RC-42** Cabin | Rock Creek | 1.31 mi | 3.3 mi | 10,450 | 4.3 | 16 | Low | Brookies*, Cutthroats | 2022 |
| 32 | **DG-17** *(unnamed)* | Dry Gulch | 1.30 mi | 4.5 mi | 10,950 | 3 | 12 | Low | Cutthroats | 2025 |
| 33 | **DG-6** *(unnamed)* | Dry Gulch | 1.28 mi | 4.1 mi | 10,550 | 3 | 5 | Low | Cutthroats | 2025 |
| 34 | **G-68** *(unnamed)* | Blacks Fork | 1.28 mi | 5.9 mi | 11,421 | 4.2 | 6 | — | Brookies | 2026 |
| 35 | **DG-10** *(unnamed)* | Dry Gulch | 1.25 mi | 4.7 mi | 10,750 | 10 | 12 | Low | Cutthroats | 2025 |
| 36 | **DG-15** *(unnamed)* | Dry Gulch | 1.24 mi | 4.5 mi | 10,950 | 3 | 9 | Low | Cutthroats | 2025 |
| 37 | **DF-4** *(unnamed)* | Ashley Creek | 1.23 mi | 4.2 mi | 10,830 | 10 | 23 | Low | Cutthroats | 2025 |
| 38 | **DF-14** West Kibah | Ashley Creek | 1.23 mi | 2.6 mi | 10,580 | 7.8 | 15 | Moderate | Brookies | 2025 |
| 39 | **G-67** *(unnamed)* | Blacks Fork | 1.22 mi | 5.6 mi | 11,158 | 7.1 | 25 | Low | Brookies | 2026 |
| 40 | **U-15** Roberts | Uinta River | 1.21 mi | 9.3 mi | 11,550 | 23.3 | 38 | Low | Brookies*, Cutthroats | 2023 |
| 41 | **X-77** Twin | Lake Fork | 1.21 mi | 6.2 mi | 10,594 | 12.9 | 15 | Low | Brookies*, Grayling | 2024 |
| 42 | **BR-46** Lorena | Bear River | 1.21 mi | 2.8 mi | 10,580 | 12.8 | 20 | Low | Brookies | 2025 |
| 43 | **BR-55** *(unnamed)* | Bear River | 1.20 mi | 1.6 mi | 10,860 | 1.5 | 12 | — | Brookies | 2025 |
| 44 | **DG-16** *(unnamed)* | Dry Gulch | 1.20 mi | 4.5 mi | 10,950 | 3 | 8 | Low | Cutthroats | 2025 |
| 45 | **LF-43** *(unnamed)* | Lake Fork | 1.19 mi | 10.7 mi | 10,820 | 1.4 | 4 | Low | Brookies | 2024 |
| 46 | **X-81** Hook | Lake Fork | 1.17 mi | 7.1 mi | 10,722 | 21 | 19 | Low | Brookies, Rainbows* | 2026 |
| 47 | **WR-16** Middle Rock | White Rocks | 1.17 mi | 1.2 mi | 10,600 | 7.1 | 10 | Low | Brookies*, Cutthroats | 2025 |
| 48 | **U-5** Oke Doke | Uinta River | 1.15 mi | 8.7 mi | 11,320 | 12.9 | 38 | Low | Cutthroats | 2023 |
| 49 | **X-88** Ottoson Lower | Lake Fork | 1.14 mi | 10.6 mi | 11,075 | 9.1 | 8 | Low | Cutthroats* | never |
| 50 | **W-58** Jean | Weber River | 1.13 mi | 3.6 mi | 10,100 | 3 | 25 | Low | Cutthroats*, Goldens*, Grayling | 2024 |
| 51 | **Y-22** Kings | Yellowstone | 1.13 mi | 10.5 mi | 11,416 | 10 | — | Low | Cutthroats | 2023 |
| 52 | **W-59** *(unnamed)* | Weber River | 1.12 mi | 3.0 mi | 10,140 | 4 | 10 | Moderate | Brookies, Grayling | 2026 |
| 53 | **LF-44** East Slide | Lake Fork | 1.11 mi | 6.8 mi | — | 5 | — | Low | Brookies | 2022 |
| 54 | **GR-59** Shaw | Ashley Creek | 1.11 mi | 4.3 mi | 10,700 | 2.8 | 5 | Low | Cutthroats* | never |
| 55 | **LF-25** Toquer | Lake Fork | 1.10 mi | 2.3 mi | 10,470 | 11.1 | 32 | Low | Brookies*, Cutthroats | 2024 |
| 56 | **W-29** Anchor | Weber River | 1.09 mi | 3.9 mi | 10,380 | 13 | 50 | Moderate | Brookies* | never |
| 57 | **DG-3** Crow | Dry Gulch | 1.09 mi | 3.8 mi | 10,350 | 18 | 26 | Moderate | Cutthroats | 2023 |
| 58 | **WR-33** Cirque L | White Rocks | 1.07 mi | 2.4 mi | 10,652 | 5.7 | 10 | — | Grayling | 2026 |
| 59 | **WR-34** *(unnamed)* | White Rocks | 1.07 mi | 4.3 mi | 11,200 | 9 | 45 | Low | Cutthroats | 2024 |
| 60 | **U-93** *(unnamed)* | Uinta River | 1.05 mi | 10.4 mi | 11,402 | 11.1 | 8 | Very low | Cutthroats | 2023 |
---

## Appendix B — every lake flagged by the semantic pass, by drainage

All ~200 lakes that scored ≥ 3 in pass 1, so nothing is lost. Score 5 = explicit
multi-source off-trail + low pressure + real fishery; 4 = clear single-source
evidence; 3 = suggestive. Tier A/B picks above are marked **bold**.

**Whiterocks** (49 read, 17 flagged) — **WR-34 Katy** 5 · **WR-73 Tamara** 5 ·
**WR-77 Becky** 5 · **WR-55 Walk Up** 5 · WR-40 Wooley 5 · WR-14 Upper Rock 4 ·
WR-33 Cirque 4 · WR-45 Pearl 4 · WR-74 Ann 4 · WR-8 Taylor 3 · WR-6 Point 3 ·
WR-75 Nellie 3 · WR-76 Eric 3 · WR-66 Reader 3 · WR-67 Horseshoe 3 ·
WR-48 Watkins 3 (4x4 overlap) · WR-37 3

**Rock Creek** (60 read, 19 flagged) — **RC-42 Cabin** 5 · **RC-11 Sea Lion** 5 ·
**RC-8 Thompson** 5 · **RC-38 Horseshoe** 5 · **X-15 Doc's** 5 · **RC-45 Audrey** 5 ·
X-131 Uintah 4 · X-125 Reconnaissance 4 · X-96 Rock 1 4 · X-121 Continent 4 ·
Z-23 Margo 4 · X-124 Boot 4 · RC-20 Survey 3 · Z-44 Allen 3 (wild grayling) ·
X-129 Margie 3 · X-100 Young 3 ⚠️rotenone · X-97 Rock 2 3 · X-43 Diamond 3 ·
**RC-36** 3 (see batch 2)

**Provo / Dry Gulch** (72 read, 18 flagged) — A-11 Azure 5 (see traps) ·
**DG-10** 5 · **DG-9** 5 · **DG-14** 4 · **DG-27 Hidden** 4 · DG-17 4 ·
U-96 Bollie 4 · A-10 Rock 4 · **A-15 Hidden** 4 · **P-62 Shingle Ck Lower** 4 ·
DG-15 3 · DG-16 3 · DG-26 Lower Lily Pad 3 · A-17 Beaver 3 · A-38 Ramona 3 ·
A-20 Brook 3 · P-11 3 (see batch 2) · P-16 Charity 3 (see batch 2)

**Bear River / Weber** (78 read, 27 flagged) — **BR-46 Lorena** 5 ·
BR-31 Seidner 5 · **BR-43** 5 · **BR-44** 5 · BR-20 Kermsuh 5 · BR-55 5 ·
**W-28 Jerry** 5 · **W-58 Jean** 5 · BR-3 Whiskey Island 4 (state-record grayling
1990) · BR-12 Scow 4 · BR-19 Meadow 4 · BR-25 Toomset 4 🎣 · BR-26 Salamander 4 ·
BR-48 Priord 4 · BR-50 4 (see batch 2) · W-34 Adax 4 · W-59 4 (first grayling
2026) · BR-29 Hell Hole 3 🎣 · BR-45 Baker 3 · BR-47 Norice 3 · W-16 3 (DWR
prints no access route at all) · W-31 Neil 3 · W-37 Bench 3 (see traps) ·
W-51 Carol 3 · W-52 3 · W-62 3 🎣 · W-64 Elkhorn 3 (see traps)

**Lake Fork / Sheep-Carter / Ashley** (98 read, 40 flagged) — **DF-4** 5 ·
**GR-62 Bert** 5 · LF-44 East Slide 5 🎣 *(the calibration point — DWR: "the most
inaccessible lake in the Lake Fork Drainage… a true wilderness lake"; Jed fished
it Aug 2026)* · **X-81 Hook** 5 · GR-13 5 · GR-15 Sesame 5 · **GR-25 Judy** 5 ·
GR-36 Wilde 4 · GR-5 Summit 4 · GR-115 Gail 4 · GR-12 Clear 4 · GR-7 Hidden 4 ·
GR-23 Mutton 4 · GR-24 Ram 4 · LF-22 Porcupine 4 ⚠️ · LF-30 Oweep 4 ⚠️ ·
LF-34 Gates 4 · **X-87 Ottoson Upper** 4 ⚠️ · X-89 4 ⚠️ · X-84 4 · X-85 4 ·
X-77 Twin 4 · **X-78** 4 · GR-39 Marsh 3 · GR-101 Mystery 3 · GR-104 Stove 3 ·
GR-112 Hidden 3 · GR-116 Columbine 3 · GR-119 3 (see batch 2) · GR-17 Candy 3 ·
GR-19 Lamb 3 · GR-22 Bummer 3 · **GR-28 Upper Potter** 3→promoted after the data fix · X-86 3 ·
X-88 Ottoson Lower 3 ⚠️ · X-79 Stewart 3 · X-63 Aspen 3 · X-32 Big Dog 3 ·
**X-94 Crater** 3 · X-82 Picture 3 · LF-16 3 · LF-36 Linda 3

**Smiths Fork / Blacks Fork / Burnt Fork / Yellowstone / Henrys Fork / Beaver
Creek** (113 read, 40 flagged) — **GR-144 Coffin** 5 · GR-145 5 ·
**GR-148 Dine** 5 · **GR-152** 5 · **G-73 Bobs** 5 · **G-105 Wagonwheel** 5 ·
G-63 Bald 5 · **X-57** 5 · **Y-16 Doll** 5 · **G-5 Cliff** 4 · G-11 Castle 4 ·
**G-67** 4 · G-69 4 · G-71 4 · **G-74** 4 · G-76 Ejod 4 · G-80 4 · G-81 4 ·
GR-128 Crystal 4 · **GR-130 Snow** 4 · GR-154 4 · G-56 4 · X-104 Little Superior
4 · X-105 4 · **X-60** 4 · Y-2 4 · Y-4 4 · Y-22 Kings 4 · Y-37 4 · GR-160 3 ·
GR-177 3 · G-65 3 · G-68 3 · G-64 3 · G-52 3 · G-50 3 · GR-134 Lower Bennion 3 ·
Y-25 Milk 3 · Y-36 3 · Y-5 3 · G-16 Upper Red Castle 3 👥

**Duchesne / Uinta River / Swift Creek** (109 read, 39 flagged) — U-94 Albert 5
*(DWR: "receives very little fishing pressure and is a must for the rugged
outdoorsman")* · **U-98 Penny Nickell** 5 · **U-93** 5 · **U-88** 5 · U-76 5 ·
U-75 5 · **U-73 Milk** 5 · **U-15 Roberts** 5 · **U-5 Oke Doke** 5 · X-51 5 ·
**X-14 Farney** 5 · U-99 Wall 4 · **U-91** 4 · U-85 Craig 4 · **U-82 Gilbert** 4 ·
U-74 Beard 4 · **U-59 Divide** 4 · **U-39** 4 · U-34 Davis South 4 ·
**U-27 Samuals** 4 · U-21 George Beard 4 · **U-100** 3 · **U-79** 3 · U-37 3 ·
U-23 Lily 3 · **U-22** 3 · U-17 Carrot 3 · U-13 Mt. Emmons 3 · Z-18 Gem 3 ·
X-50 3 · X-49 Twin 3 · X-26 3 · X-21 Carrol East 3 · X-12 Sonny 3 🎣

⚠️ = inside an area Andersen lists in DWR's proposed 2022–2034 rotenone /
native-cutthroat restoration program.

---

## Method notes (for re-running this)

Scratch tooling for this pass lived outside the repo (session scratchpad) and is
not committed. To rebuild:

1. Overpass query for `highway ~ path|footway|bridleway|track|service|
   unclassified|residential|tertiary|secondary|primary|motorway` over
   `40.50,-111.35,41.05,-109.70`, `out geom` — 9,791 ways, ~16 MB. Mirror
   `overpass.private.coffee` answered when `overpass-api.de` was busy.
2. Densify every way to 100 m spacing, bucket into a 500 m grid, expanding-ring
   nearest-neighbour per lake. Pure Python, ~1.2 s for 738 lakes (no numpy in
   `venv`).
3. Contact sheets: Leaflet + `USGSTopo/MapServer/tile/{z}/{y}/{x}` at z14, OSM
   ways drawn as coloured polylines, 1 km/2 km rings, neighbour labels; screenshot
   with `playwright-cli` against a local static server. Four lakes per sheet was
   the readable density.
4. Per-drainage source dumps (FACTS + stocking + DWR 2025 summary + Falcon rows +
   full DWR/CMA/junesucker/Jed text) fed one agent each, ~150 KB per agent.
