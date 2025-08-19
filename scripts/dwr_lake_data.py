#!/usr/bin/env python3
"""
Manually extracted lake data from DWR PDF: dwr-dry-gulch-and-uinta-trimmed.pdf
This data will be processed by process_dwr_pdf.py
"""

DWR_LAKE_ENTRIES = [
    # Page 1 - DRY GULCH - CROW BASIN
    {
        'designation': 'DG-1',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'DG-3', 
        'name': 'CROW',
        'text': "Crow is an irregular shaped lake located in steep rocky terrain. It is 18 acres, 10,350 feet in elevation, with 26 feet maximum depth. Access is via the Timothy Creek Road to Jackson Park, then down the steep sides of the basin to lakes DG 6, 7 and 8. Follow the outlet stream south 3/4 mile to Crow Lake. Good campsites, spring water and horse feed are available. This lake contains a good population of cutthroat trout. Angling pressure is moderate, and there is excessive litter around the shoreline."
    },
    {
        'designation': 'DG-4',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'DG-5',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'DG-6',
        'name': None,
        'text': "Lakes DG 6, 7 and 8 are shallow, interconnecting lakes located in a grassy meadow. DG-6 is 3 acres, 10,550 feet in elevation, with 5 feet maximum depth. Access is via Jackson Park north 1-1/2 miles, then descend over the canyon rim following an east-northeast direction. Good campsites, spring water and horse feed are available near the lake. Cutthroat trout are stocked and angling pressure is light."
    },
    {
        'designation': 'DG-7',
        'name': None,
        'text': "This is a very shallow lake located between lakes DG-6 and DG-8. It is 6 acres, 10,550 feet in elevation, with 4 feet maximum depth. Good campsites, spring water and horse feed are available. This lake has a small population of cutthroat trout which migrate from DG-6. The lake is too shallow to stock because of winterkill. Fishing pressure is very light."
    },
    {
        'designation': 'DG-8', 
        'name': None,
        'text': "DG-8 sits due east of DG-7 about 70 yards. It is 7 acres, 10,550 feet in elevation, with 8 feet maximum depth. Access by following the main basin stream north 3/4 mile from Crow Lake to DG-6. Campsites, spring water and horse feed are within 1/2-mile of the lake. DG-8 is too shallow to stock, but has a few cutthroat trout that migrate from DG-6. Fishing pressure is very light."
    },
    {
        'designation': 'DG-9',
        'name': None, 
        'text': "This lake has a steep rock escarpment located just below the outlet. It is 10 acres, 10,750 feet in elevation, with 27 feet maximum depth. Access is via Timothy Creek Road to Jackson Park then down into the lakes DG 6, 7 and 8. Follow the DG-6 inlet north 1/2-mile and up the rock escarpment. Campsites and spring water are limited, but good horse feed is available. This lake contains a small population of cutthroat trout. Angling pressure is light."
    },
    {
        'designation': 'DG-10',
        'name': None,
        'text': "This natural lake is bounded by meadows on the north and south with rock ledges on the east and west. It is 10 acres, 10,750 feet in elevation, with 12 feet maximum depth. Access is to follow the DG-9 inlet north 1 mile. There is no spring water and campsites are marginal, but good horse feed is available to the north and south. A small population of healthy cutthroat trout inhabit the lake. Angling pressure is very light."
    },
    {
        'designation': 'DG-14',
        'name': None,
        'text': "DG-14 sits at the northeast head of the canyon 2 miles north of Crow Lake. It is 2 acres, 11,000 feet in elevation, with 10 feet maximum depth. There is no trail to the lake. No campsites or horse feed are available, but cold spring water is plentiful from the talus slope. This lake contains a fair population of cutthroat trout which are maintained through stocking. Angling pressure is very light."
    },
    {
        'designation': 'DG-15',
        'name': None,
        'text': "This lake sits at the base of the northwest rim at the head of Crow Canyon. The lake has a good fairy shrimp population but has extreme water level fluctuations. It is 3 acres, 10,950 feet in elevation, with 9 feet maximum depth. Campsites, spring water and horse feed are not available. It contains a small population of cutthroat trout which is subject to occasional winterkill. Angling pressure is very light."
    },
    {
        'designation': 'DG-16',
        'name': None,
        'text': "This is the second lake northwest against the northwest rim of the canyon located 100 feet south of DG-15. It is 3 acres, 10,950 feet in elevation, with 8 feet maximum depth. No campsites, spring water or horsefeed are available. A small population of cutthroat trout inhabit the lake, and it is subject to winterkill. Angling pressure is very light."
    },
    {
        'designation': 'DG-17',
        'name': None,
        'text': "This is the third lake near the northwest rim at the head of the basin, and is 100 yards east of DG-16. It is 3 acres, 10,950 feet in elevation, with 12 feet maximum depth. No campsites, spring water or horsefeed are available. A large population of cutthroat is found in the lake, and it is partially sustained through natural reproduction. Angling pressure is very light."
    },
    
    # Page 1 - DRY GULCH - HELLER BASIN
    {
        'designation': 'U-96',
        'name': 'BOLLIE', 
        'text': "This natural lake is in the Uinta River drainage and is described in that section of this booklet. It is also listed in this section of the booklet because the Dry Gulch drainage also shows the access better than the Uinta drainage map does."
    },
    {
        'designation': 'DG-29',
        'name': None,
        'text': "DG-29 is a small beaver pond subject to an occasional winterkill. It is 2 acres, 9,500 feet in elevation, with 8 feet maximum depth. Access is via Heller Reservoir 1/4 mile northwest to a long park. Follow the park 1/2-mile then turn east 1/8 mile. Horse feed is excellent, but campsites and spring water are not available to fishery. This pond is presently not managed to provide any fishery. Fishing pressure is very light."
    },
    {
        'designation': 'DG-30',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    
    # Page 2 - HELLER RESERVOIR, DG-28
    {
        'designation': 'DG-28',
        'name': 'HELLER RESERVOIR',
        'text': "Heller Reservoir has a small, dam at the outlet. It is 12 acres, 10,108 feet in elevation, with 37 feet maximum depth. Access is 4 miles north on the Dry Gulch Road. The trail is closed at this point, so follow the jeep trail on foot 2 miles to the reservoir. Spring water and campsites are available, but there is no horse feed. The fishery is composed of a stable population of pan-sized brook trout. Angling pressure is heavy, and winter is a problem around the lake."
    },
    {
        'designation': 'DG-27',
        'name': 'HIDDEN',
        'text': "Hidden is isolated lake in the head of Heller basin. It is 10 acres, 9,520 feet in elevation, with 39 feet maximum depth. Access is 5 miles northeast on a poorly marked trail from Heller Reservoir. Spring water is abundant, but good campsites and horse feed are not available. This lake contains a fair population of healthy brook trout. Fishing pressure is light."
    },
    {
        'designation': 'DG-26',
        'name': 'LOWER LILY PAD',
        'text': "Lower Lily Pad is a productive meadow lake covered with aquatic vegetation. It is 9 acres, 10,275 feet in elevation, with 11 feet maximum depth. Access is via the vague trail to Upper Lily Pad Lake, then, 1/8 mile due east. Campsites are available, horse feed is limited, and there is no spring water. A small population of brook trout are found in this lake. Fishing pressure is light."
    },
    {
        'designation': 'DG-25',
        'name': 'UPPER LILY PAD',
        'text': "Upper Lily Pad is a beautiful meadow lake surrounded by conifers. It is 12 acres, 10,280 feet in elevation, with 37 feet maximum depth. Access is 7.5 miles via the Dry Gulch Road and pack trail over Flat Top Mountain, or 2 miles northwest of Hellers Reservoir, cross-country. Excellent campsites and horse feed are found around the lake, but spring water is limited. This lake contains small populations of healthy brook and cutthroat trout. Angling pressure is heavy, and there is a litter problem."
    },
    
    # Page 2 - UINTA RIVER DRAINAGE
    {
        'designation': 'U-94',
        'name': 'ALBERT',
        'text': "This cirque lake is located in the far southwest corner of an extremely steep and rocky basin. It is 7 acres, 10,826 feet in elevation, with 8 feet maximum depth. Access is to go northwest up a ridge 2 miles from Bollie Lake, then turn north and climb down a steep talus slope into the basin. There are no trails, camping sites or horsefeed around the lake; horses cannot be taken into Albert. Many pan-sized cutthroat inhabit the lake. These fish are sustained by natural reproduction. The lake receives very little fishing pressure and is a must for the rugged outdoorsman."
    },
    {
        'designation': 'U-14',
        'name': 'ALLRED',
        'text': "This natural lake is located 18 miles from the Uinta River trailhead and 225 yards south of the Atwood Lake dam. It is 34 acres, 10,995 feet in elevation, with 30 feet maximum depth. The rocky trail is well marked, but due to the numerous steep switchbacks the distance seems longer than it is. Campsites and horse pasture are both abundant around Allred Lake. Nice-sized brook trout are quite numerous in the lake and are sustained through natural reproduction. Fishing and camping pressure is quite moderate. Allred Lake is a must for those wanting a rugged wilderness experience and fast fly-fishing for plump brookies in the evening."
    },
    {
        'designation': 'U-16',
        'name': 'ATWOOD',
        'text': "Atwood Lake is the largest lake in the Uinta River drainage. It has an earthen dam on the southwest end and water levels fluctuate considerably each year. Atwood is approximately 200 acres, 11,030 feet in elevation, with 40 feet maximum depth. Access is 18 miles from U-Bar Ranch over a well-marked trail. Good campsites and horse feed are available around the lake. Atwood Lake has one of the largest brook trout populations in the Uinta Mountains. A few golden trout are also found in the lake. Camping and angling pressure are moderate."
    },
    
    # Page 3 - Continue UINTA RIVER DRAINAGE
    {
        'designation': 'U-18',
        'name': 'B-29 LAKE',
        'text': "This natural lake sits in a wet meadow in the far southeast corner of Atwood Basin. It is 19 acres, 10,740 feet in elevation, with 7 feet maximum depth. There is no marked trail to B-29, but it can be reached from Carrot Lake by going east 1/4 mile after crossing Carrot Creek on the Atwood Lake trail. Total miles from the U-Bar Ranch trailhead is 17 miles. Camping sites and horse pasture are abundant around the lake; however, the pasture is quite boggy. A large brook trout population inhabits the lake. Camping and fishing pressure is light at B-29. Take plenty of insect repellent during July."
    },
    {
        'designation': 'U-74',
        'name': 'BEARD',
        'text': "The high cirque lake sits way above timberline at the eastern base of South Kings Peak. It is 9 acres, 11,740 feet in elevation, with an estimated 15 feet maximum depth. Access is to follow the well marked Forest Service trail 22 miles through Atwood Basin to Trail Rider Pass. Follow the trail an additional 1/8 mile into Painter Basin, then turn southwest and go 150 yards into a small cirque basin to the lake. Horse access is fairly rugged over the rocky terrain (especially up Trail Rider Pass). There are no horse pastures or camping area in the windswept tundra around the lake. Stocked brook trout grow well in Beard and fishing pressure is quite light."
    },
    {
        'designation': 'U-96',
        'name': 'BOLLIE',
        'text': "This natural lake is surrounded by beautiful meadows and open timber. It is 10 acres, 10,660 feet in elevation, with 15 feet maximum depth. Trail access is via a primitive logging road 3 miles north past Jefferson Park to the canyon rim. Follow the trail west for 2 miles along the rim until you reach the lake near the head of the basin. Excellent campsites and abundant horse feed are available around the lake. This lake contains cutthroat trout. Fishing pressure and camping use are light. (Refer to the Dry Gulch drainage map for a better illustration of the access route.)"
    },
    {
        'designation': 'U-32',
        'name': 'BOWDEN',
        'text': "Bowden is a shallow, natural lake located 1/2 mile southeast of the Kidney Lakes. It is 4.5 acres, 10,693 feet in elevation, with 14 feet maximum depth. Total distance from the U-Bar Ranch is 18.5 miles. The last half mile is trailless. Horse access is good, and numerous campsites and pasture are available around the lake. Bowden Lake contains stocked brook trout. Camping and fishing pressure is rated moderate. Bowden Lake has excellent brook production and may occasionally winterkill, so fishing is generally not fast."
    },
    {
        'designation': 'U-54',
        'name': 'BROOK',
        'text': "This natural lake can be reached by following the trail east 1 mile along the south shore of Fox Lake. It is 10 acres, 10,950 feet in elevation, with 18 feet maximum depth. It can also be reached by following the Highline Trail west through Whiterocks drainage over North Pole Pass (first lake encountered). Some horse feed and campsites are available around the lake. Brook trout are stocked in Brook Lake and fishing pressure is"
    },
    {
        'designation': 'U-17',
        'name': 'CARROT',
        'text': "This beautiful glacial lake sits along the rim of Atwood Basin and is located 1/2 mile southwest of the big meadow where the trail crosses Atwood Creek. It is 31 acres, 10,830 feet in elevation, with 31 feet maximum depth. Total distance from the U-Bar Ranch is 17.5 miles over a good trail. Good pasture and campsites are located on the north side of the lake. Fishing is generally good for stocked brook trout. Fishing pressure is rated light."
    },
    {
        'designation': 'U-3',
        'name': 'CHAIN 1 (LOWER)',
        'text': "Chain 1 is a fluctuating reservoir and is the lowest of the Chain lake series. Full pool is 62 acres, 10,580 feet in elevation, with 38 feet maximum depth. Access is 11.5 miles via a well-marked Forest Service trail from the U-Bar Ranch trailhead. Some camping sites are available around the lake. Limited horse pasture can be found on the east shore, and 1/4 mile south of the dam. Chain 1 contains a large population of pan-sized brook trout produced through natural reproduction. Fishing pressure is heavy during early summer but decreases later in the season as water drawdown occurs."
    },
    {
        'designation': 'U-2',
        'name': 'CHAIN 2 (MIDDLE)',
        'text': "Chain 2 is second lake in the Chain Lake series. It is 14.4 acres, 10,612 feet in elevation, with 13 feet maximum depth. It used as a storage reservoir but the earthen dam has washed out. It sits 1/2 trail mile above Chain 1 and less than 100 yards below the Chain 3 dam. Total distance from U-Bar Ranch is 12 miles along a well-marked trail. Horse pasture is fairly good but limited, and there are a few camping sites. The abundant brook trout population in Chain 2 is self sustaining. Angling and camping pressure is moderate."
    },
    {
        'designation': 'U-1',
        'name': 'CHAIN 3 (UPPER)',
        'text': "This reservoir is the third lake in the Chain Lake series. It is 51 acres at full pool, 10,624 feet in elevation, with 44 feet maximum depth. Total distance is 12.5 miles from the U-Bar Ranch via a well-marked trail. Horse pasture and campsites are limited around the somewhat rocky shoreline. Pan-sized brook trout are very abundant in Chain 3 and are sustained through natural reproduction. Angling and camping pressure are not moderate. Fishing is especially fast on flies and spinners."
    },
    {
        'designation': 'U-4',
        'name': 'CHAIN 4',
        'text': "Chain 4 is a natural lake that sits along the trail on a plateau located above Chain 3 Lake and below Roberts Pass. It is 13.5 acres, 10,870 feet in elevation, with 31 feet maximum depth. Total distance is 13.5 miles from U-Bar Ranch. Horse access is quite good though steep the last 1/2 mile. No horse pasture and very few campsites exist around the lake. This lake is managed with cutthroat trout. Fishing and camp-"
    },
    
    # Page 4 - Continue UINTA RIVER DRAINAGE  
    {
        'designation': 'U-85',
        'name': 'CRAIG',
        'text': "This natural lake is the first large lake (and lower in elevation) encountered in the Painter Lakes Basin. It is 9.3 acres, 10,848 feet in elevation, and about 14 feet maximum depth. Leave U-Bar Ranch and proceed via a well-marked trail 14 miles to North Fork Park (where the North and Center Forks of the Uinta River converge). Head due south for 2 very steep and rough miles up a vague trail (along a small creek) into the Painter Lakes Basin. There are good horse pastures and camping sites around the lake. Craig contains mostly cutthroat trout with an occasional brook trout. Fishing and camping pressure are light."
    },
    {
        'designation': 'U-48',
        'name': 'CRESCENT',
        'text': "This long narrow reservoir fluctuates 4 feet annually. It is 31 acres, 10,830 feet in elevation, with 23 feet maximum depth. Access is very good via two well marked forest service trails: the shortest is about 8 miles over the Fox Quaaint Pass trail via the West Fork Whiterocks River drainage, and the other is about 15.5 miles up the Shale Dugway from the U-Bar Ranch. Camping sites are available around the lake and good horse pasture can be found 1/2 mile north (Fox Lake) or west (large meadow) from Crescent. The Crescent Lake fishery is mainly cutthroat trout along with a few brook trout. Camping and fishing pressure is moderate to heavy, and the area is quite popular with large scout groups during mid summer."
    },
    {
        'designation': 'U-46',
        'name': 'DAVIS, NORTH',
        'text': "This natural lake sits about 250 yards due north of South Davis Lake, or about 1-1/4 miles north of the Kidney lakes. It is 7.3 acres, 11,060 feet in elevation, with 7 feet maximum depth. Good camping sites and abundant horse pasture are found to the south between South Davis and the Kidney lakes. North Davis contains small pan-sized brook trout that are hard to catch. These fish are stocked and can freely move between both Davis lakes. Fishing pressure is light, but camping pressure is moderate in the vicinity."
    },
    {
        'designation': 'U-34',
        'name': 'DAVIS, SOUTH',
        'text': "This shallow lake sits in a large, wet meadow 1 mile north of the Kidney lakes. It is 6.1 acres, 11,020 feet in elevation, with 4 feet maximum depth. Camping sites and horse feed are plentiful south of the lake. Pan-sized brook trout inhabit the lake. Camping pressure is moderate, but angling pressure is light. This lake can be good for fly-fishing."
    },
    {
        'designation': 'U-59',
        'name': 'DIVIDE',
        'text': "This natural lake sits in windswept tundra below the mountain pass separating Uinta River drainage (south slope) from Burnt Fork drainage (north slope). It is 18.9 acres, 11,217 feet in elevation, with an estimated 39 feet maximum depth. Access is 2 miles north from Fox Lake via the trail which goes over the pass to Island Lake. No camping sites or horse feed are available around the lake or the vicinity. Divide Lake has been managed with cutthroat trout. Angling pressure is considered light and fishing is generally excellent."
    },
    {
        'designation': 'U-49',
        'name': 'DOLLAR',
        'text': "This pretty lake is located in a large meadow, and is occasionally called Dime Lake. It is 11.5 acres, 10,704 feet in elevation, with 6 feet maximum depth. Trail access to very good and the lake is located about 1 mile northwest of Fox Lake. Total distance from U-Bar Ranch is 15 miles. Excellent horse feed and camping sites are in the Dollar Lake vicinity. A natural population of pan-sized brook trout inhabits the lake. Camping and fishing pressure are generally rated moderate, though heavy use occasionally occurs from large groups. Brookies spawn easily in the meadow stream below Dollar, and are quite a challenge for the fly fisherman."
    },
    {
        'designation': 'U-47',
        'name': 'FOX',
        'text': "This reservoir lake is popular despite 20-foot fluctuations annually. It is 102 acres at full pool, 10,790 feet in elevation, with 47 feet maximum depth. Trails are well marked, and distance is either 15 miles from the U-Bar Ranch to the south, or 8.5 miles from the West Fork trailhead to the northeast. Horse feed and heavily used camping areas are located in the general area around the lake. Brook and cutthroat trout are well established, however, large groups frequently visit this lake, and the area has been abused."
    },
    {
        'designation': 'U-21',
        'name': 'GEORGE BEARD',
        'text': "This natural lake sits in open, windswept tundra. It is 7.4 acres, 11,420 feet in elevation, with 15 feet maximum depth. Access is 2 miles via a rocky trail from Atwood Lake and is located just below Trail Rider Pass. No camping areas or horse pasture exist around the lake. Brook trout have reproduced naturally at George Beard and can be quite abundant. Fishing pressure is limited to day-users and considered light."
    },
    {
        'designation': 'U-82',
        'name': 'GILBERT',
        'text': "This natural lake sits at the head of Gilbert Creek, a tributary to the Center Fork of the Uinta River. It is 14.6 acres, 11,459 feet in elevation, with 20 feet maximum depth. Good trail access exists heading northwest from North Fork Park for 6.5 miles. Total trail distance from U-Bar Ranch is 20.5 miles. Good camping and horse pasture exists 3 miles southeast of the lake. The lake is currently stocked with brook trout. Fishing pressure is light. Sheep grazing during late summer detracts from the aesthetic beauty of this meadow basin."
    },
    {
        'designation': 'U-25',
        'name': 'KIDNEY, EAST',
        'text': "This natural lake is located about 15 miles from the West Fork Whiterocks River trailhead, or just under 18 miles from U-Bar Ranch; both access trails are well marked. It is 13.7 acres, 10,850 feet in elevation, with 12 feet maximum depth. Horse pasture is abundant north of the lake. Camping areas are abundant, but overused in the area between the Kidney lakes. The lake contains brook trout. Both camping and angling pressure are quite heavy from large recreational groups."
    },
    
    # Page 5 - Continue UINTA RIVER DRAINAGE
    {
        'designation': 'U-26',
        'name': 'KIDNEY, WEST',
        'text': "This natural lake is located 100 yards due west of Kidney, East. It is 20 acres, 10,850 feet in elevation, with 4 feet maximum depth. Trail access is quite good, and distance is 18 miles from the U-Bar Ranch or 15 miles from the West Fork Whiterocks river trailhead. Horse pasture is available north of the lake. Camping sites are found around the lake, but most are overused. The lake contains brook trout. Both camping and angling pressure are quite heavy from large recreational groups."
    },
    {
        'designation': 'U-23',
        'name': 'LILY',
        'text': "This pretty little lake is surrounded by yellow water lilies. It is 5.3 acres, 10,919 feet in elevation, with 15 feet maximum depth. Lily is located about 1/2 mile northeast of the Kidney lakes. There is no trail, but horse access is fairly easy over this somewhat open terrain. Campsites and horse pasture are available west of the lake. Brook trout are stocked into the lake. Angling pressure is generally light considering its close proximity to the Kidney lakes."
    },
    {
        'designation': 'U-8',
        'name': 'LILY PAD',
        'text': "Lily Pad is the first lake encountered on the Chain lakes trail approximately 8 miles from U-Bar Ranch. It is 3.7 acres, 10,818 feet in elevation, with 7 feet maximum depth. It sits in a small stream-fed valley 1/4 mile off the trail, located 1 mile east of Chain 1 and about 1/3 mile north of the Shale Creek trail crossing. (A trail sign marking this lake may or may not be tacked to a pine tree near the trail turnoff.) Horse pasture is limited and a few camping sites are on the south margin. This lake contains abundant populations of brook and rainbow trout sustained through natural reproduction. Fishing pressure is moderate, and Lily Pad is considered a good fly-fishing lake. This lake has been used as a base camp by commercial packers."
    },
    {
        'designation': 'U-73',
        'name': 'MILK',
        'text': "This isolated lake is located in a cirque basin on the talus ridge bordering the north part of Painter Basin. It is 13.1 acres, 11,236 feet in elevation, with 35 feet maximum depth. Milk is about 5 trail miles west of North Fork Park, or 19 trail miles northeast of Trail Rider Pass. The last mile is extremely rocky and trailless, and very difficult for horses. There are no campsites or horse pasture around the lake. Pan-sized brook and cutthroat trout are quite numerous. Fishing pressure is very light."
    },
    {
        'designation': 'U-13',
        'name': 'MT. EMMONS',
        'text': "This pretty lake is located 1/4 mile south of Allred Lake (Atwood Basin) through a timbered terrain. It is 5.2 acres, 10,950 feet in elevation, with 21 feet maximum depth. Total distance is about 18.5 miles from the U-Bar Ranch. Some pasture and limited camping areas are available along the fringes of the wet meadow east of the lake. Brook trout are common in the lake. This lake has had golden trout in the past but it is doubtful if any remain. Angling and camping pressure are light."
    },
    {
        'designation': 'U-5',
        'name': 'OKE DOKE',
        'text': "This pretty cirque lake is located at the eastern base of Mt. Emmons 1 mile due west of Roberts Pass. It has no inlet or outlet stream, and is 12.9 acres, 11,320 feet in elevation, with 38 feet maximum depth. Total distance by trail is 15 miles from U-Bar Ranch. Limited horse feed and marginal camping areas are located south of Roberts Pass. Cutthroat trout are stocked into Oke Doke. Fishing pressure is light. Oke Doke is ideal for a small group of one to three backpackers who want to get off the beaten trail."
    },
    {
        'designation': 'U-98',
        'name': 'PENNY NICKELL',
        'text': "This pretty cirque lake sits next to a steep talus slope 3.5 miles due south of Fox Lake. It is 11.5 acres, 10,710 feet in elevation, with 43 feet maximum depth. There is no trail to the lake and it's best to use a U.S.G.S. map for directions. Various camping areas and horse feed exists in wet meadows between Fox and Penny Nickell lakes. The lake is stocked with cutthroat. Angling and camping pressure are light."
    },
    {
        'designation': 'U-9',
        'name': 'PIPPEN',
        'text': "This meadow lake has a small island near the south shore. It is 3.2 acres, 10,450 feet in elevation, with 3 feet maximum depth. Go west about 1 mile through a large meadow located 1/2 mile southwest of Chain 1. Total distance from U-Bar Ranch is 10 miles. Excellent horse pasture and camping sites exist around the lake and a fair natural population of brook trout inhabit the lake. Angling pressure is moderate, and Pippen is considered a good fly-fishing lake. This lake has been used as a base camp by commercial packers."
    },
    {
        'designation': 'U-33',
        'name': 'RAINBOW',
        'text': "This natural lake is located in a windswept tundra 1-1/4 miles northwest of the Kidney lakes along a well-marked trail. It is 35.1 acres, 11,130 feet in elevation, with 28 feet maximum depth. No campsites or horse pasture exist around this lake but they are available 1 mile to the east. Brook trout spawn naturally in the lake and it may contain a few rainbows and cutthroat trout. Fishing pressure is usually moderate, but heavy pressure occasionally occur from large pack groups staying at the Kidney lakes."
    },
    {
        'designation': 'U-15',
        'name': 'ROBERTS',
        'text': "This deep natural lake is located in a high cirque basin 1 mile southwest of Atwood Lake past the Chain 3 series. It is 23.5 acres, 11,550 feet in elevation, with 38 feet maximum depth. Follow a faint trail 1.5 miles west of Mt. Emmons Lake through a wet meadow, and zigzag a steep ravine to Roberts Lake. No camping or horse feed is available in this windswept tundra area. The lake contains mainly cutthroat trout along with a few brook trout. Angling pressure is light and fishing success is quite variable."
    },
    {
        'designation': 'U-27',
        'name': 'SAMUELS',
        'text': "This nice lake sits 1 mile north of the upper trail between Fox and Kidney lakes at the head of Samuels Creek. It is 4.8 acres, 10,995 feet in elevation, with 7 feet maximum depth. Horse pasture and camping areas are quite abundant around the lake and to the south. The lake contains an abundant population of brook trout. Angling pressure is light. Try this commonly \"passed up\" lake and avoid the people usually present at the Kidney and Fox lakes."
    },
    
    # Page 6 - Continue UINTA RIVER DRAINAGE
    {
        'designation': 'U-19',
        'name': None,
        'text': "This natural lake is located near the head of Atwood Basin in windswept tundra. It is 15 acres, 11,420 feet in elevation, with 8 feet maximum depth. Trail access is 1 mile south of George Beard Lake past U-22 Lake, or 2 miles due west of the Atwood Lake Dam. Horse pasture and camping are available 2 miles east of Atwood and Allred lakes. Horses should not be grazed in this fragile tundra. The lake contains a fine population of brook trout. Fishing pressure is light."
    },
    {
        'designation': 'U-35',
        'name': None,
        'text': "This natural lake is located over 100 yards northeast of Rainbow Lake; in fact, the outlet stream from Rainbow Lake flows into U-35. It is 4.4 acres, 11,110 feet in elevation, with 5 feet maximum depth. No horse pasture or camping areas are around the lake. This small lake holds only a few stocked cutthroat and brook trout. Fishing pressure is moderate from people camped near Kidney lakes."
    },
    {
        'designation': 'U-36',
        'name': None,
        'text': "This lake sits in windswept tundra about 100 yards southeast of U-35 and receives its outlet stream; or is located under 1 mile northwest of the Kidney lakes. It is 6.3 acres, 11,180 feet in elevation, with 12 feet maximum depth. There are no camping sites or pasture. These are available southeast 1-1/4 miles at the Kidney lakes. The lake is stocked with brook trout. Fishing pressure is light."
    },
    {
        'designation': 'U-37',
        'name': None,
        'text': "This windswept tundra lake is located 1/2 mile northeast of Rainbow Lake and 1/2 mile southeast of U-38 in the basin above the Kidney lakes. It is 6.3 acres, 11,180 feet in elevation, with 12 feet maximum depth. There are no camping sites or pasture. These are available southeast 1-1/4 miles at the Kidney lakes. The lake is stocked with brook trout. Fishing pressure is light."
    },
    {
        'designation': 'U-38',
        'name': None,
        'text': "This windswept tundra lake sits 1/2 mile due north of Rainbow Lake past U-39 Lake. It is 15 acres, 11,218 feet in elevation, with 11 feet maximum depth. An intermittent inlet stream comes from U-42 Lake while the outlet stream flows into U-40 Lake. A little horse pasture is available northeast of the lake around U-40, but there are no camping sites. Cutthroat trout inhabit the lake. Fishing pressure varies from light to moderate."
    },
    {
        'designation': 'U-39',
        'name': None,
        'text': "This shallow lake sits in the tundra 1/4 mile due north of Rainbow Lake; in fact, the outlet stream flows into Rainbow Lake. It is 5.3 acres, 11,160 feet in elevation, with 9 feet maximum depth. No horse pasture or camping areas exist around the lake. This lake was experimentally stocked with brook trout but they did not survive. This lake is no longer managed to provide any recreational fishing. Fishing pressure is light."
    },
    {
        'designation': 'U-42',
        'name': None,
        'text': "This natural lake has some water level fluctuation and sits in windswept tundra. It is 7.6 acres, 11,350 feet in elevation, with 7 feet maximum depth. U-42 is located about 1/4 mile northwest of Rainbow Lake and 1/2 mile west of U-38. Camping and horse pasture are not available. The lake was experimentally stocked with cutthroat trout and only has marginal habitat. Fishing pressure is light."
    },
    {
        'designation': 'U-45',
        'name': None,
        'text': "This shallow lake is quite long and narrow, and sits next to the talus slope at the head of the basin 2-1/2 miles northwest of Kidney lakes. It is 5 acres, 11,425 feet in elevation, with 7 feet maximum depth. No horse pasture and campsites are available. The lake contains a natural population of nice brook trout. Angling pressure is light."
    },
    
    # Page 6-7 - End of UINTA RIVER DRAINAGE section, plus final lakes
    {
        'designation': 'U-50',
        'name': None,
        'text': "This pretty lake sits quite shallow for its size. It is 18 acres, 10,832 feet in elevation, with 8 feet maximum depth. It is located 1/4 mile north-west of Dollar Lake and horse access is easy. Camping and horse pasture are available in the vicinity. The lake is stocked with brook trout. Angling pressure is light."
    },
    {
        'designation': 'U-75',
        'name': None,
        'text': "This natural lake sits in open tundra in the extreme western end of Painter Basin. It is 6.9 acres, 11,390 feet in elevation, with 18 feet maximum depth. The lake is located about 1 trail mile northwest of Trail Rider Pass. It contains a fairly abundant population of pan-sized brook trout. No camping areas or horse feed exist around the lake; in fact, the area is usually windy and cold late season and the lake receives few anglers."
    },
    {
        'designation': 'U-76',
        'name': None,
        'text': "This cirque lake is located at the southwest base of Kings Peak in the Upper Painter Basin in cold, windswept tundra. It is 6 acres, 11,475 feet in elevation, with 15 feet maximum depth. Access is about 2 miles northwest of Trail Rider Pass over gentle, timbered terrain. Excellent camping sites and limited horse pasture are around the lake. The lake contains pan-sized brook and cutthroat trout. Angling pressure is very light at this remote lake, and a visit will provide a true wilderness experience."
    },
    {
        'designation': 'U-88',
        'name': None,
        'text': "This pretty, natural lake is the largest in the Painter Lakes Basin. (See access to Craig Lake.) It is 14 acres, 11,030 feet in elevation, with 18 feet maximum depth. U-88 sits 1 mile due west of Craig Lake over gentle, timbered terrain. Excellent camping sites and limited horse pasture are on the south shore. The lake contains a natural population of nice brook trout. Angling pressure is light."
    },
    {
        'designation': 'U-89',
        'name': None,
        'text': "The water level in this pretty lake fluctuates annually. It is 11.5 acres, 11,037 feet in elevation, with 15 feet maximum depth. (See access to Craig Lake.) This lake sits about 1 mile due west of Craig Lake and is 100 yards southwest of U-88. Excellent camping and limited horse pasture are around the lake. It contains a few brook trout. Angling pressure is light."
    },
    {
        'designation': 'U-93',
        'name': None,
        'text': "This natural lake is the highest and most westerly in the Painter Lakes Basin. It is 11 acres, 11,402 feet in elevation, with 8 feet maximum depth. (See access to Craig Lake.) U-93 sits 1.5 miles west of Craig Lake over somewhat steep but rolling terrain. The lake is stocked with cutthroat trout. No horse pasture or camping areas exist around the lake. Angling pressure is very low. This is one of the most remote lakes in the Uinta River drainage."
    },
    {
        'designation': 'U-41',
        'name': 'VERLIE',
        'text': "This natural lake sits due west of the Kidney lakes about 1 mile. It is 10.6 acres, 10,906 feet in elevation, with 12 feet maximum depth. The last several hundred yards are inaccessible to horses. Camping sites are marginal and quite limited. A natural population of brook trout inhabits the lake, along with an occasional cutthroat trout. Angling pressure is rated moderate."
    },
    
    # BEAR RIVER DRAINAGE - dwr-bear-blacks-fork-trimmed.pdf
    {
        'designation': 'BR-42',
        'name': 'ALLSOP',
        'text': "Allsop is a beautiful natural lake situated in a small cirque basin at the head of the Left Hand Fork of the East Fork Drainage. It is 12.3 acres, 10,580 feet in elevation, with 22 feet maximum depth. The lake is in an alpine meadow with open shorelines and timbered slopes to the east and west. Access is 8.5 miles southeast of the East Fork-Bear River Trailhead on the East Fork and Left Hand Fork pack trails. Campsites are available with several excellent sources of spring water. Pasture is present in the lake vicinity and adjacent to the outlet stream for some distance below the lake. Allsop contains a population of cutthroat trout sustained by natural reproduction. Allsop is subject to moderate levels of angling pressure."
    },
    {
        'designation': 'BR-28',
        'name': 'AMETHYST',
        'text': "Amethyst is a striking natural lake situated within the timberline transition zone in a rugged cirque basin at the head of the Ostler Fork Drainage. It is 42.5 acres, 10,750 feet in elevation, with 59 feet maximum depth. The lake is emerald green in appearance due to a glacial turbidity. Access if 6.25 miles southeast of the Christmas Meadows Trailhead on the Stillwater and Amethyst Lake pack trails. The lake is situated at the head of the basin, 1 mile beyond the lower meadows. Campsites adjacent to the lake are poor and horse feed is restricted due to the windswept and rocky nature of the surrounding timberline terrain. Better sites are available in the vicinity of the lower meadows. Amethyst provides some fast fishing for pan-sized brook and cutthroat trout. Angling pressure has established at moderate levels."
    },
    {
        'designation': 'BR-45',
        'name': 'BAKER',
        'text': "This meadow lake is situated at the base of gently sloping timbered terrain in the Boundary Creek Drainage. It is 3.6 acres, 10,420 feet in elevation, with 8 feet maximum depth. The meadow surrounding Baker is large and quite boggy. Access is 4.25 miles southeast of the Bear River Boy Scout Camp on the unmarked Boundary Creek Trail past the old burn to the head of the drainage. The last 0.75 mile of trail immediately below the lake is indistinct and difficult to locate. Good campsites are available with plentiful horse feed. A good spring water source is located 0.25 mile downstream from the lake. Baker contains a population of wary brook trout. Shorelines are open enough to permit fly casting."
    },
    {
        'designation': 'BR-10',
        'name': 'BEAVER',
        'text': "Beaver is a scenic meadow lake located in open terrain characterized by grassy slopes and scattered groves of conifers in the West Fork Drainage. The lake is 13.2 acres, 9,420 feet in elevation, with 32 feet maximum depth. Beaver is easily accessible on the Moffit Pass Road 1.75 miles southwest of the Whitney Reservoir dam. The total distance from U-150 in the Hayden Fork Drainage is about 9 miles. Excellent sites are available for camping activity, but spring water and fuelwood are scarce. Large shallow shelves and dense growths of aquatic vegetation around the lake perimeter make shore fishing very difficult. Anglers are encouraged to bring boats or rubber rafts. Beaver Lake is productive in nature and subject to frequent winterkill. As a result, the Forest Service has installed a water circulator on the surface of this lake in an attempt to improve winter survival. Beaver is currently stocked on an annual basis with catchable-sized rainbow trout and may contain brook and cutthroat trout."
    },
    {
        'designation': 'BR-1',
        'name': 'BOURBON (GOLD HILL)',
        'text': "Bourbon is a small crescent-shaped lake in timbered country at the foot of a steep, jagged peak and associated talus rock. It is 1.9 acres, 9,820 feet in elevation, with 8 feet maximum depth. Campsites are poor in the lake vicinity, but a spring water source is available. Bourbon is located 1 steep mile west of Highway U-150 on the Whiskey Creek Trail which begins across the highway from the Sulpher Campground. Access is also afforded by the Whiskey Creek Road which begins across the highway from and slightly north of the Kletting Peak Information Turnoff. Follow this road north and west for 2.5 miles to the end and then continue northwest on foot for 0.25 mile to the lake. Bourbon, containing a population of brook trout, is a popular fishing spot."
    },
    {
        'designation': 'BR-2',
        'name': None,
        'text': "This productive meadow pond is located some 100 yards downstream from Bourbon Lake in the Hayden Fork of the Bear River Drainage. It is 0.7 acres, 9,780 feet in elevation, with 5 feet maximum depth. Small and quite shallow, BR-2 would not appear to provide suitable fish habitat. However, the lake contains a population of brook trout sustained by natural reproduction and downstream migration from Bourbon Lake. Camping opportunities are available with a limited supply of horse feed. Spring water is available at Bourbon. Fishing pressure is light despite the easy access afforded by the Whiskey Creek timber road."
    },
    {
        'designation': 'BR-4',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-5',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-6',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-16',
        'name': None,
        'text': "BR-16 is a small, narrow pond situated at the foot of a rocky ridge on the stream immediately below Ryder in the Stillwater Fork Drainage. It is 1.0 acre, 10,610 feet in elevation, with 5 feet maximum depth. Suitable camping areas are available in the lake vicinity with horse pasture in large parks to the east. Spring water can be obtained at the nearby Ryder Lake. BR-16 contains a population of brook and cutthroat trout maintained by natural reproduction and recruitment from Ryder. Fishing pressure is regarded as moderate to light."
    },
    {
        'designation': 'BR-17',
        'name': None,
        'text': "BR-17 is a small spring-fed lake located in sparsely timbered terrain in the Middle Basin of the Stillwater Fork Drainage. It is 2.8 acres, 10,630 feet in elevation, with 7 feet maximum depth. BR-17 is situated immediately south of Ryder Lake. Several good potential campsites are available with very little horse feed. Spring water can be obtained from any one of several sources feeding the lake. BR-17 contains a population of pan-sized brook trout sustained by natural reproduction. A major portion of the shoreline at this timberline lake is open enough to permit fly casting. Angling pressure is moderate to light."
    },
    {
        'designation': 'BR-18',
        'name': None,
        'text': "This spring-fed glacial lake is located in timberline terrain 200 yards southeast of Ryder Lake or immediately downstream from BR-17 in the Stillwater Fork Drainage. The lake is 4.8 acres, 10,610 feet in elevation, with 12 feet maximum depth. Good campsites are available with abundant spring water in the lake vicinity. Limited horse feed can be located in the general area. BR-18 contains a good population of brook trout and provides some fair fishing on occasion. Recreational use is generally light."
    },
    {
        'designation': 'BR-21',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-22',
        'name': None,
        'text': "BR-22 is not capable of sustaining a fishery. It is included on the map as a landmark."
    },
    {
        'designation': 'BR-23',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-24',
        'name': None,
        'text': "This small cirque lake abuts a rocky ledge and talus slope in Amethyst Basin. BR-24 is 2.4 acres, 10,460 feet in elevation, with 10 feet maximum depth. The lake is emerald green in color due to a glacial turbidity, and is quite shallow in overall depth. BR-24 is located within sight of the Amethyst Lake Trail 5.25 miles southeast of the Christmas Meadows Trailhead just beyond the lower meadows. Excellent campsites are available in the lake vicinity with ample horse feed in the lower meadows. Spring water is available from several inlet sources. BR-24 provides spotty fishing for cutthroat trout."
    },
    {
        'designation': 'BR-30',
        'name': None,
        'text': "BR-30 is natural meadow lake abutting a talus slope at the head of the Hell Hole Basin. It is 1.2 acres, 10,580 feet in elevation with 6 feet maximum depth. The lake is brown in color with a glacial turbidity of pulverized rock. Access is 0.75 mile southwest of Hell Hole Lake overland through wet meadows and timber following the major drainage system. Potential campsites are available with spring water early in the season. Horse feed is present to the east in a large, wet meadow. Stocking has been discontinued at BR-30 due to winterkill problems."
    },
    {
        'designation': 'BR-33',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-34',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-35',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-41',
        'name': None,
        'text': "BR-41 is an unproductive natural lake situated at the base of a steep talus ridge at the head of the Mill Creek Drainage. The lake is 3.4 acres maximum, 10,412 feet in elevation, with 19 feet maximum depth. Snowslides are common in the lake vicinity as indicated by the presence of stunted conifers and avalanche litter along the southern lake margin. Marginal campsites are present. Better opportunities are available lower in the drainage. Spring water sources are not available in the immediate lake vicinity. BR-41 is located 6 miles south of the Mill Creek Guard Station on the unimproved Mill Creek Road which degrades to a jeep trail for the last several miles. The lake is also accessible from the East Fork of the Bear River Trailhead east on the Bear River-Smiths Fork Trail over the top of Deadman Pass. BR-41 experiences extreme water level fluctuation and does not contain suitable habitat to sustain a fishery. The lake is not presently stocked."
    },
    {
        'designation': 'BR-43',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-44',
        'name': None,
        'text': "BR-44 is a natural glacial lake located in rugged timberline terrain in the Right Hand Fork of the East Fork Drainage. It is 3.6 acres, 10,900 feet in elevation, with 15 feet maximum depth. The lake abuts a steep talus ridge to the west and the remainder of the shoreline is composed of rocky slopes and sparse timber. BR-44 lies in an isolated basin and access is difficult. From the East Fork Trailhead, follow the East Fork Bear River Pack Trail southeast for 5.25 miles to a large trailside spring in the Right Hand Fork. Then proceed directly west for 1.75 miles up the steep hillside following the drainage system to the head of the basin. Potential campsites are available without horse feed or spring water sources. BR-44 is not easily accessible on horseback. This lake has been scheduled for experimental cutthroat trout stocking during 1983."
    },
    {
        'designation': 'BR-49',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-51',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-52',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-53',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-37',
        'name': 'CUTTHROAT',
        'text': "Cutthroat is a natural lake located near timberline in a rugged cirque basin at the head of the Hayden Fork Drainage. It is 3.8 acres, 10,390 feet in elevation, with 16 feet maximum depth. There is no direct trail to Cutthroat Lake. Access is 1 rough mile west of Ruth Lake through thick timber and boulder fields. Horse access is possible but difficult. Campsites in the immediate lake vicinity are limited and poor due to the open and windswept nature of the surrounding terrain, but good sites are available to the east in the vicinity of a wet meadow. Spring water can be obtained at the lake through at least mid-August. Cutthroat contains a wary population of brook trout and a few remaining cutthroat trout. Fisherman use is moderate."
    },
    {
        'designation': 'BR-36',
        'name': 'HAYDEN',
        'text': "Hayden is an irregular natural water located in rocky terrain 0.25 mile due west of Ruth Lake in the Hayden Fork Drainage. There is no direct access trail, but the lake is readily accessible. It is 4.4 acres, 10,420 feet in elevation, with 5 feet maximum depth. The lake abuts a talus slope to the west and scattered conifers encompass the remainder of the shoreline. Campsites are available at Hayden with a good source of spring water. The lake contains a small population of cutthroat trout and sustains moderate levels of angling pressure."
    },
    {
        'designation': 'BR-29',
        'name': 'HELL HOLE',
        'text': "Hell Hole is a shallow lake with partly open shorelines situated centrally in the Hell Hole Basin near the head of the Main Fork Drainage. The lake is 8.5 acres, 10,340 feet in elevation with 9 feet maximum depth. The surrounding terrain is scenic and composed of large, boggy meadows and thick patches of timber. Access is 5 miles southeast of Highway U-150 on the Main Fork Stillwater Trail which begins as an unmarked jeep road across the highway from the Gold Hill turnoff. This trail, not well maintained, is difficult to follow at times. Campsites are excellent at Hell Hole with plenty of horse feed and running water. Several small springs are present as well. Hell Hole contains a good population of pan-sized cutthroat trout often overlooked by anglers. Fishermen are encouraged to bring plenty of mosquito repellent on trips to this basin."
    },
    {
        'designation': 'BR-38',
        'name': 'JEWELL',
        'text': "This natural glacial lake is situated in partially open, timbered country at the foot of a talus rockslide. Jewell is 2.4 acres, 10,300 feet in elevation, with 13 feet maximum depth. The lake is located 0.5 mile northwest of Ruth Lake over rough terrain with no direct access trail. Several camping areas are available in the lake vicinity, and horse feed can be located to the southwest in a large, wet meadow. Spring water is not present. Jewell Lake is stocked with cutthroat trout and sustains moderate levels of fishing pressure. Jewell is a popular water for single day fisherman use."
    },
    {
        'designation': 'BR-20',
        'name': 'KERMSUH',
        'text': "Kermsuh is a long, narrow lake situated in rocky timbered country in the isolated West Basin of the Stillwater Fork Drainage. It is 12.4 acres, 10,300 feet in elevation, with 14 feet maximum depth. Campsites are poor due to the rocky nature of the surrounding terrain, but running water is abundant. Horse feed can be located in a small meadow to the south. Access is 4.5 miles south of Christmas Meadows on the Stillwater Pack Trail to the junction with the Kermsuh Lake Trail and then 2.25 miles southwest up the steep grade into West Basin. The cutthroat trout population is sustained by natural reproduction. This lake provides a good opportunity for users seeking solitude."
    },
    {
        'designation': 'BR-11',
        'name': 'LILY',
        'text': "Lily is an extremely large beaver pond situated in partly open, timbered terrain east of U-150 in the East Fork Drainage. It is 12.6 acres, 8,890 feet in elevation, with 20 feet maximum depth. Access is 1 mile north of the Bear River Ranger Station on U-150 to a well marked turnoff and then some 2 miles southeast on the unimproved Lily Lake-Boundary Creek Road to the lake. Primitive camping areas are available with no source of spring water. A forest fire occurred in the vicinity of Lily Lake during 1980 burning much of the timber to the east of the lake. Lily is stocked on an annual basis with catchable rainbow trout. However, this productive water may stagnate late in the summer and the best fishing usually occurs prior to July 20. Lily sustains moderate levels of fisherman utilization."
    },
    {
        'designation': 'BR-46',
        'name': 'LORENA',
        'text': "Lorena is an irregular water situated in a small glacial cirque at the head of an isolated basin in the East Fork Drainage. The lake is 12.0 acres, 10,580 feet in elevation, with 20 feet maximum depth. Access is 2 miles southeast of the East Fork-Bear River Trailhead on the East Fork Trail to the old tie-hack cabin sites. From this point proceed south for 1.5 miles up the steep and rocky ridge to the head of basin. Access can be difficult and should not be attempted on horseback. Campsites are poor due to the rocky nature of the surrounding terrain. Horse feed is unavailable in the basin. A spring water source can be located about 0.25 mile downstream from the lake. Lorena is stocked with brook trout. This remote lake provides a good opportunity for anglers seeking solitude in the Bear River Basin."
    },
    {
        'designation': 'BR-7',
        'name': 'LYM',
        'text': "Lym is a natural moraine lake located in thick conifers at the base of Table Top Mountain in the Mill Creek Drainage. The lake is 6.4 acres, 10,115 feet in elevation, with 20 feet maximum depth. Lym is long and narrow in outline. Access is 4 miles south of the Mill Creek Guard Station on the unimproved Mill Creek Road and then 2 miles northeast on the rough Lym Lake jeep trail to the lake. Be sure to take the left hand turn at the old tie-hack cabin sites in the large meadow. Numerous campsites are available along the lake perimeter with several sources of spring water. Limited horse feed is present to the north in a small, wet meadow. The population of brook trout present in Lym Lake is maintained by natural reproduction. Remember to carry out all refuse."
    },
    {
        'designation': 'BR-14',
        'name': 'MCPHETERS',
        'text': "This picturesque natural lake is situated near timberline at the head of the Middle Basin of the Stillwater Fork Drainage. McPheters is 28.8 acres, 10,860 feet in elevation, with 45 feet maximum depth. The surrounding terrain is composed of extensive bedrock shelves, windswept alpine meadows, and talus slopes. The lake is irregular in outline with a narrow, shallow arm to the east. Access is 0.5 mile northwest of Ryder Lake to the top of the rocky ridge. The total distance from the Christmas Meadows Trailhead is 9 miles. Campsites and horse feed are not immediately available due to the open nature of the terrain and absence of fuelwood. However, good sites are present nearby. Spring water is plentiful. McPheters Lake is stocked with cutthroat trout."
    },
    {
        'designation': 'BR-19',
        'name': 'MEADOW',
        'text': "Meadow Lake is a shallow natural lake located in rocky, timbered country directly east of and downstream from BR-18 in the Stillwater Fork Drainage. It is 2.9 acres, 10,470 feet in elevation, with 5 feet maximum depth. There are several deep water channels running through the middle of the lake. Good camping opportunities are available with excellent sources of spring water. Horse feed is located to the north. The best route of access is to head 0.25 mile southeast of the Stillwater Pack Trail from the vicinity of the large meadows due east of Ryder. Meadow contains a population of brook trout sustained by natural reproduction. The lake experiences light angling pressure and provides a good opportunity for anglers who wish to get away from the crowds."
    },
    {
        'designation': 'BR-8',
        'name': 'MT. ELIZABETH',
        'text': "Mt. Elizabeth Lake is a productive natural water located at the foot of Elizabeth Mountain in the Mill Creek Drainage. It is 3.1 acres, 9,984 feet in elevation, with 15 feet maximum depth. The surrounding terrain is composed of scattered patches of conifers and open meadows. Campsites are available with early season spring water. Access is 11.25 miles east of of U-150 on the North Slope Road to Elizabeth Pass and then 4.5 miles north and west on the Elizabeth Mountain Road to the point overlooking Elizabeth Lake. Secondary logging routes provide direct vehicular access to the lake for 4-wheel drive vehicles, (see Blacks Fork Drainage map). Elizabeth Lake is stocked with cutthroat trout and received moderate levels of Fishing pressure."
    },
    {
        'designation': 'BR-39',
        'name': 'NAOMI',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-47',
        'name': 'NORICE',
        'text': "This shallow meadow lake is situated near the head of the Right Hand Fork some 8.25 miles southeast of the East Fork Trailhead on the East Fork Bear River Pack Trail. Norice is 4.8 acres, 10,470 feet in elevation, with only 3 feet maximum depth. The pack trail is excellent to the forks but deteriorates beyond this point due to bogs and dead fall timber. Camping areas are available at Norice with ample feed in surrounding meadows, although this area is quite boggy. Spring water is not immediately available. Norice contains a good cutthroat trout population sustained by natural reproduction. This lake provides some good fly fishing on occasion."
    },
    {
        'designation': 'BR-27',
        'name': 'OSTLER',
        'text': "Ostler is an irregularly shaped natural lake located in a small glacial pocket in rocky timberline terrain at the western end of Amethyst Basin. The lake is 14.0 acres, 10.540 feet in elevation, with 14 feet maximum depth. Access is 5.25 miles southeast of the Christmas Meadows Trailhead on the Stillwater and Amethyst Lake pack trails to the lower meadows and then 0.25 mile west up the steep hillside to Ostler. Some campsites with limited horse feed are available at the southwestern end of the lake. However, better sites are available in the vicinity of the lower meadows. Spring water is present at the lake through July. Ostler contains a population of brook and cutthroat trout and is a popular Boy Scout lake."
    },
    {
        'designation': 'BR-48',
        'name': 'PRIORD',
        'text': "Priord is an emerald green lake situated in a rugged cirque basin at the head of the East Fork Drainage. It is 12.0 acres, 10,860 feet in elevation, with 20 feet maximum depth. Access is 9 miles east and south of the East Fork-Bear River Trailhead on the East Fork Trail, 1 short mile beyond Norice Lake. This trail is well-traveled in the lower reaches of the drainage, but becomes difficult to locate in the vicinity of Norice. The aforementioned East Fork Trailhead is located 0.125 mile beyond the turnoff to the Boy Scout Camp on an improved Forst Service road. Campsites are available at Priord with good spring water sources and limited horse feed. The lake is situated in timberline terrain. Fuelwood is scarce. Priord is stocked with cutthroat trout and sustains moderate to light angling pressure."
    },
    {
        'designation': 'BR-40',
        'name': 'RUTH',
        'text': "Ruth is a popular alpine lake located 0.75 mile west of U-150 on the Ruth Lake Trail from a well-marked highway turnoff and parking area. It is 9.7 acres, 10,340 feet in elevation, with 30 feet maximum depth. The surrounding terrain is composed of large areas of bedrock with sparse conifers and small meadows. There are several campsites available to the angler with some spring water. Horse feed is limited. Ruth experiences substantial fishing pressure from primarily day anglers. The lake is frequently stocked with brook trout."
    },
    {
        'designation': 'BR-15',
        'name': 'RYDER',
        'text': "This deep natural lake is situated in open timber with beautiful meadows and steep, rocky ledges. Ryder is 23.7 acres, 10,620 feet in elevation, with 55 feet maximum depth. Inlets cascade off cliffs to the west adding to the aesthetic qualities of this water. Access is 8.25 miles south of the Christmas Meadows Trailhead on the Stillwater Pack Trail. This trail becomes indistinct and difficult to locate in meadow areas immediately east of the lake, but the route is clearly marked with rock cairns. Campsites are present with spring water sources. Horse feed in available in limited supply, but is more abundant to the east adjacent to the access trail. Ryder contains a large population of brook trout and produces some fair fly fishing on occasion."
    },
    {
        'designation': 'BR-26',
        'name': 'SALAMANDER',
        'text': "Salamander is a productive natural lake with boggy banks situated atop a timbered ridge in the Ostler Fork Drainage. It is 4.1 acres, 10,020 feet in elevation, wiih 13 feet maximum depth. Access is 3.25 miles south and east of the Christmas Meadows Trailhead on the Stillwater and Amethyst Lake pack trails to the first meadow in Amethyst Basin. From this point, proceed southwest up the ridge to the Take. Salamander is surrounded by heavy timber and can be difficult to locale. Campsites are poor. Running water and horse feed are not available in the lake vicinity. Salamander is occasionally stocked with brook trout."
    },
    {
        'designation': 'BR-12',
        'name': 'SCOW',
        'text': "Scow is a spring-fed meadow lake located in heavy timber on the ridge between the Stillwater and Boundary Creek Drainages. It is 22.9 acres, 10,100 feet in elevation, with 6 feet maximum depth. Access is 2.5 miles south of the East Fork of the Bear River Boy Scout Camp on the Boundary Creek Trail past the old burn to a small off-stream meadow. From this point, continue south for 0.75 mile through thick timber to the lake. Campsites are present with some horse feed in surrounding wet meadows. Spring water is readily available during the early summer months. Scow is stocked with brook trout, but fishing is unpredictable due to the occasional occurrence of winterkill."
    },
    {
        'designation': 'BR-31',
        'name': 'SEIDNER',
        'text': "Seidner is a small spring-fed lake which abuts a talus slope at the head of an isolated basin in the Stillwater Fork Drainage. It is 3.2 acres, 10,460 feet in elevation, with 8 feet maximum depth. Access is 2.25 miles south of the Christmas Meadows Trailhead on the Stillwater Pack Trail to a minor side drainage, and then some 2 steep miles west following this drainage to the head of the basin. Direct access trails are not available. Access on horseback can be difficult. The lake is immediately west of a large meadow where campsites and horse feed can be found. Spring water is available from any one of several inlet sources. Seidner presently contains a large population of brook trout sustained by natural reproduction."
    },
    {
        'designation': 'BR-32',
        'name': 'TEAL',
        'text': "Teal is a natural moraine lake situated at the base of a talus ridge in the Hayden Fork Drainage. It is 6.9 acres, 10,260 feet in elevation, with 14 feet maximum depth. Access is 1.25 miles northwest of Ruth Lake over rough and rocky terrain. Trails are not present and access on horseback can be difficult. Marginal campsites are available for small groups in the lake vicinity, but spring water and horse feed are not present. Teal is best suited for single day fishing trips. The lake is stocked on a regular basis with cutthroat trout."
    },
    {
        'designation': 'BR-25',
        'name': 'TOOMSET',
        'text': "This natural oval-shaped lake is located in a small glacial basin against sliderock 0.25 mile north of Ostler Lake in Amethyst Basin. Toomset is 2.1 acres, 10,300 feet in elevation, with 11 feet maximum depth. Camping areas are poor in the vicinity of the lake with no available horse feed or spring water. Better sites for camping activity are located in the lower meadows due east of Ostler Lake. Toomset contains a brook trout population maintained by natural reproduction. The lake is often overlooked by anglers. Toomset provides a good opportunity to get away from the crowds in Amethyst Basin."
    },
    {
        'designation': 'BR-3',
        'name': 'WHISKEY ISLAND (GUYS)',
        'text': "Whiskey Island is a natural alpine lake situated in a rugged cirque basin at the fool of a steep talus ridge. It is 5 acres, 10,340 feel in elevation, with 19 feet maximum depth. The lake, characterized by a glacial turbidity, is green in color. Due to the frequent snowslides in the area, Whiskey Island is not usually free of ice and snow until mid-July. Access is 1.25 miles southwest of the Whiskey Creek timber road from a point approximately 1.25 miles northwest of U-150. The terrain is rough and composed of boulder fields and deadfall timber. There is no direct access trail. Whiskey Island is not accessible on horseback. Campsites, horse feed and spring water are not available in the lake vicinity. Whiskey Island is subject to winterkill, but experimental stocking of artic grayling has been scheduled for 1985."
    },
    
    # BLACKS FORK DRAINAGE - dwr-bear-blacks-fork-trimmed.pdf
    {
        'designation': 'G-73',
        'name': 'BOBS',
        'text': "Bobs is a scenic natural lake located in a glacial cirque at the base of Tokewanna Peak in the Middle Fork of the Blacks Fork Drainage. It is 6.6 acres, 11,150 feet in elevation, with 30 feet maximum depth. Access is 10.25 miles southwest of the East Fork Blacks Fork Road on the hit-and-miss Middle Fork Trail which begins as a jeep readjust south of the Blacks Fork bridge. This trail is blazed but receives limited use and can be indistinct and extremely difficult to locate in areas. The trail disappears in large headwater meadows, but Bobs can be located by following the tributary system towards the west. Bobs is situated well above timberline. Campsites are not available. However, an excellent spring water source is present at the lake. Better camping opportunities are situated lower in the basin. Bobs is stocked with cutthroat trout and fishing can be unpredictable."
    },
    
    # DUCHESNE DRAINAGE - dwr-duchesne-trimmed.pdf
    {
        'designation': 'D-25',
        'name': 'BLIZZARD',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'Z-32',
        'name': 'BLUE',
        'text': "Blue is an aesthetic alpine lake situated at the foot of Mt. Agassiz in Naturalist Basin. It is 19 acres, 10,940 feet in elevation, with 36 feet maximum depth. The lake basin is steep and rocky with scattered tundra-type vegetation. Camping areas are unavailable. Campsites are present in the Morat Lakes vicinity. Spring water is available early in the season. Access is 5 miles east of the Highline Trailhead on the Highline and Naturalist Basin Pack trails to the Blue Lake Trail Junction and then 3/4 mile north over steep terrain. Angling pressure is moderate, and fishing is fast for small brook trout."
    },
    {
        'designation': 'Z-20',
        'name': 'BLYTHE',
        'text': "Blythe is a productive meadow lake with floating banks situated at the base of a steep timbered ridge. It is 5 acres, 9,000 feet in elevation, with 14 feet maximum depth. Blythe may be subject to occasional winterkill. Camping areas are available with spring water early in the season. Blythe is located 1/2 mile northeast of the Mirror Lake Trailhead. There is no trail, but the lake can easily be located. Brook trout are stocked regularly."
    },
    {
        'designation': 'Z-6',
        'name': 'BONNIE',
        'text': "This natural meadow lake is located 150 yards south of U-150 near the Scout Lake Turnoff on an established trail. Bonnie is 3.6 acres, 10,100 feet in elevation, with 7 feet maximum depth. A large boggy meadow lies east of the lake. Campsites are established but spring water is unavailable. Access is also available on 1 mile of trail from the Mirror Lake Trailhead. Fishing pressure is heavy due to the accessibility of this water. Bonnie is stocked annually with brook trout. There are also a few wild cutthroat trout."
    },
    {
        'designation': 'D-40',
        'name': 'BROADHEAD',
        'text': "Broadhead Lake is situated on a ledge 3/4 mile south of the Little Deer Creek Damsite. Access to the damsite is provided by the Duchesne Tunnel road. Broadhead Lake is 8.8 acres, 9,960 feet in elevation, with 16 feet maximum depth. Potential campsites are available with spring water throughout the summer season. There are no trails present and horse access is difficult. Old timber sale roads in the vicinity have become overgrown and eroded and are no longer suitable for vehicles. Broadhead is stocked with brook trout."
    },
    {
        'designation': 'Z-2',
        'name': 'BUD',
        'text': "Bud is a stagnant meadow lake situated in thick conifers 75 yards south of U-150 near the Butterfly Lake Campground. It is 3.7 acres, 10,220 feet in elevation with 13 feet maximum depth. Bud is subject to occasional winterkill. Campsites are available but most of the angling pressure is day use. Bud is stocked annually with brook trout. Fishing is only fair for the small brook trout."
    },
    {
        'designation': 'Z-1',
        'name': 'BUTTERFLY',
        'text': "Butterfly is a pretty, natural lake situated in open timber immediately across U-150 from Highline Trailhead at Hayden Pass. It is 4.3 acres, 10,300 feet in elevation, with 13 feet maximum depth. The Forest Service has developed a campground at Butterfly and angler use is very heavy. Butterfly is stocked on a regular basis with rainbow and albino rainbow catchables, and brook trout fingerling."
    },
    {
        'designation': 'Z-42',
        'name': 'CAROLYN',
        'text': "Carolyn is a small natural lake located in timbered country with boggy shorelines. It is 5 acres, 10,430 feet in elevation, with 17 feet maximum depth. Access is 6 miles south and east of the Highline Trailhead on the Highline Pack Trail to about 1/2 mile short of the Olga Lake Trail Junction. At this point proceed south for 200 yards along a trail established by users to the Carolyn Lake vicinity. Horse feed and campsites are available and spring water is present early in the season. Carolyn contains a good population of arctic grayling sustained by natural reproduction. This lake also has a small population of brook and cutthroat trout. Angling pressure is moderate."
    },
    {
        'designation': 'D-14',
        'name': 'CASTLE',
        'text': "Castle is a small natural lake located in timbered country with open shorelines. It is 1 acre, 10,300 feet in elevation, with 12 feet maximum depth. Access is 3/8 mile west of Butterfly Lake along the base of the talus ridge past several small ponds. Trails are not present. Campsites are available with spring water early in the season. Castle contains a small cutthroat trout population. Fishing pressure is moderate."
    },
    {
        'designation': 'D-5',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'D-10',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'D-19',
        'name': None,
        'text': "D-19 is a small meadow lake located immediately south of Bonnie. It is 1.2 acres, 10,000 feet in elevation, with 6 feet maximum depth. Campsites are available adjacent to the lake and horse feed is present in nearby meadows. D-19 contains a large population of brook trout often overlooked by the angler. This lake may also contain a few cutthroat trout. Angling pressure is moderate."
    },
    {
        'designation': 'D-26',
        'name': None,
        'text': "D-26 is surrounded by boggy meadows and thick timber and has an irregular shoreline. It is 3 acres, 10,060 feet in elevation, with 10 feet maximum depth. The lake is located on a steep talus ridge 1/4 mile north of Echo Lake. There are no trails present and access is limited to backpackers. Annual recreational use is moderate. Campsites are available with spring water sources. This lake has been stocked with brook trout but the habitat is marginal."
    },
    {
        'designation': 'D-30',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'D-31',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'D-32',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'D-34',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'Z-16',
        'name': 'ECHO',
        'text': "Echo is a beautiful lake located in thick conifers at the base of a talus slope. This lake is 18 acres, 9,740 feet in elevation, with 44 feet maximum depth. Echo is a popular lake and receives heavy recreational use. Access is 5 1/4 miles east and north on the Murdock Basin Road to the Echo Lake turnoff, and then north for 1/2 mile along a rough road. Numerous campsites with spring water are available at the southeastern end of the lake. Horse feed is limited. Echo contains a large population of brook trout."
    },
    {
        'designation': 'D-20',
        'name': 'EMERALD',
        'text': "This lake has been stocked experimentally with brook trout but it is marginal fish habitat."
    },
    {
        'designation': 'Z-36',
        'name': 'EVERMAN',
        'text': "Everman has an irregular shoreline and is located in a small meadow within Naturalist Basin. It is 7.8 acres, 10,520 feet in elevation, with 7 feet maximum depth. Access is 5 1/4 miles east of the Highline Trailhead on the Highline and Naturalist Basin Pack Trails. Leave the trail at the head of the large meadow below Jordan Lake and proceed east for 200 yards to the lake. Campsites are established and spring water is available. Horse feed is present in a large park east of the lake. The lake is subject to sporadic winterkill. Everman is stocked with brook trout, and receives moderate fishing pressure."
    },
    {
        'designation': 'X-14',
        'name': 'FARNEY',
        'text': "Farney is located in rocky, timbered country at the head of Marsell Canyon. It is 12.6 acres, 10,320 feet in elevation, with 14 feet maximum depth. The northern lake margin abuts a large boulder field. Access is 5 miles north of the Grand View Trailhead on the Grandaddy Trail to Fish Hatchery Lake and then 1/2 mile west through downed timber with no trail (see Rock Creek Drainage Map). Farney can also be reached by following Marsell Canyon Creek southeast for 3 miles from the Duchesne River Trail above the East Portal of the Duchesne Tunnel. Camping areas are available, but horse feed is scarce. Spring water can be obtained at the lake. Farney is stocked with Arctic grayling and may winterkill on occasion. Fishing use is light."
    },
    {
        'designation': 'D-1',
        'name': 'FAXON',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'Z-7',
        'name': 'FEHR',
        'text': "Fehr is a natural meadow lake situated in thick timber at the foot of Murdock Mountain. It is 5.7 acres, 10,260 feet in elevation, with 27 feet maximum depth. Access is 1/4 mile east of U-150 on the well-marked Fehr Lake Trail which begins across the highway from Moosehorn Lake. Fehr is popular lake and experiences heavy pressure from day-use groups. Spring water is present early in the season. Fehr contains a large population of small brook trout."
    },
    {
        'designation': 'D-12',
        'name': 'GATMAN',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'Z-18',
        'name': 'GEM',
        'text': "Gem is an aesthetic meadow lake situated in thick conifers northeast of Joan Lake. It is 3.8 acres, 10,070 feet in elevation, with 14 feet maximum depth. Access is 1/2 mile northwest from the Echo Lake vicinity. Follow the major inlet stream. Gem Lake does not appear on USGS topographic maps. Campsites and spring water are available below the lake along the outlet stream. Horse feed is abundant but it is difficult to access Gem on horseback. Gem Lake contains brook trout and experiences light angling pressure."
    },
    {
        'designation': 'D-11',
        'name': 'HADES',
        'text': "Hades Lake is located 3/4 mile northwest of the Grandview Trailhead in Hades Canyon above the Defas' Dude Ranch. It is 6.3 acres, 9,980 feet in elevation, with 32 feet maximum depth. Trail access is not available, but the lake can be located at the foot of the steep talus ridge. Few campsites are present, and horse feed is limited. Spring water is unavailable. Hades is stocked with rainbow trout and may contain a few brook trout."
    },
    {
        'designation': 'Z-10',
        'name': 'HOOVER',
        'text': "Hoover is a natural lake surrounded by conifers with several areas of open shoreline. It is 18.6 acres, 9,900 feet in elevation, with 28 feet maximum depth. The major inlets originate from Shepard and Maba lakes. Several campsites are available, and there is a piped spring water source. Horse feed is limited. Access is 8 miles north and east of U-150 on the well-traveled Murdock Basin Road to the Hoover Lake turnoff. The lake is located 100 yards northwest of this point. Hoover Lake is managed for brook trout but it may also contain a few cutthroat trout. Fishing pressure is excessive."
    },
    {
        'designation': 'Z-37',
        'name': 'HYATT',
        'text': "Hyatt is a scenic lake situated on a rocky shelf 1/2 mile east of Everman Lake. It is 2.4 acres, 10,740 feet in elevation, with 10 feet maximum depth. The lake contains marginal fish habitat due to restricted inlet flows and limited depth. Direct access trails do not exist and the terrain is steep and rocky. Campsites are available with several acres of horse feed. Spring water is unavailable and water supplies must be packed in. This lake is not being managed to provide a fishery. Recreational pressure is light."
    },
    {
        'designation': 'D-33',
        'name': 'IRON MINE',
        'text': "This natural lake is located in a logged-over area in the vicinity of Iron Mine Mountain. It is 6.1 acres, 9,580 feet in elevation, with 21 feet maximum depth. Access is 7 1/2 miles south and east of U-150 on the Soapstone Basin and Iron Mine Roads to the main Iron Mine Fork and then 2 1/2 miles south. Campsites are available. Iron Mine Lake is subject to frequent winterkill and is no longer stocked."
    },
    {
        'designation': 'Z-19',
        'name': 'JOAN',
        'text': "Joan has an irregular shoreline and is located in rocky terrain 1/4 mile west of Echo Lake. It is 15.2 acres, 10,050 feet in elevation, with 20 feet maximum depth. The major inlet originates at Gem Lake and provides some fair stream fishing. Several good campsites are present and spring water and horse feed are available in the general vicinity. However, direct access on horseback is difficult due to the rough terrain and absence of trails. Joan receives a moderate level of angler use and contains a good population of brook trout."
    },
    {
        'designation': 'Z-35',
        'name': 'JORDAN',
        'text': "Jordan is a scenic lake situated in timbered country with scattered meadows in Naturalist Basin. It is 23.2 acres, 10,660 feet in elevation, with 30 feet maximum depth. Access is 5 3/4 miles east of the Highline Trailhead on the Highline and Naturalist Basin Pack trails. This popular lake receives heavy fishing pressure and excessive camping activity. Wood for fuel has become scarce and horse feed is often limited late in the season. Fisherman are encouraged to camp in outlying areas out of sight of the lakes, trails and streams in the vicinity. The lake is stocked on a regular basis with brook trout. Jordan outlet stream contains a large population of brook trout and provides some good fly-fishing opportunities."
    },
    {
        'designation': 'Z-33',
        'name': 'LECONTE',
        'text': "LeConte is a high lake situated above timberline in Naturalist Basin. It is 9.5 acres, 10,920 feet in elevation, with 15 feet maximum depth. The surrounding terrain is alpine tundra with scattered patches of low conifers. Campsites are not available, and horse feed is limited. Access is 1/2 mile northwest of Jordan Lake over steep and rocky terrain. Horsemen should take the Shaler Lake Trail to the top of the ridge and then head west to LeConte. LeConte Lake contains cutthroat trout but is subject to occasional winterkill. Angling pressure is moderate."
    },
    {
        'designation': 'Z-8',
        'name': 'MABA',
        'text': "This small natural lake is located in scattered timber at the head of Murdock Basin. It is 4.2 acres, 9,900 feet in elevation, with 20 feet maximum depth. Maba is situated 50 yards north of Hoover Lake and approximately 75 yards west of the Murdock Basin Road. Campsites and spring water are available at Hoover. Maba contains a small population of brook trout. Fishing pressure is heavy."
    },
    {
        'designation': 'X-11',
        'name': 'MARSELL',
        'text': "This natural lake is situated at the base of West Grandaddy Mountain in the Marsell Canyon Drainage. Marsell in 16.4 acres, 10,470 feet in elevation, with 50 feet maximum depth. The lake is accessible on the Grandaddy Trail north from the Grandview Trailhead (see Rock Creek Drainage Map). Leave the trail at a point 1/2 mile north of Betsy Lake and proceed west along the base of a talus ridge to Marsell. The total distance from the trailhead is 5 miles. Camping opportunities are available, but horse feed is limited in the immediate vicinity. Spring water sources are present. Marsell is stocked with cutthroat trout. Fishing pressure is moderate."
    },
    {
        'designation': 'Z-11',
        'name': 'MARSHALL',
        'text': "Marshall is a deep natural lake located in dense conifers in Murdock Basin. It is 18 acres, 9,980 feet in elevation, with 36 feet maximum depth. The western lake margin abuts a talus slope. Access 1/2 miles north and east on the Murdock Basin Road from U-150 to an unmarked turnoff and then 1/2 mile west on a system of logging roads. Access is also available on the Fehr Lake Trail from U-150. Campsites are present with no spring water sources. Marshall is stocked with brook and may still contain cutthroat trout. Angling pressure is heavy."
    },
    {
        'designation': 'Z-3',
        'name': 'MIRROR',
        'text': "Mirror is a picturesque natural lake located 32 miles northeast of Kamas on U-150 approximately 2 miles beyond Bald Mountain Pass. It is 42.0 acres, 10,200 feet in elevation with 37 feet maximum depth. Mirror Lake is one of the most widely know and popular lakes in the Uinta Mountains. Fishing and camping activity at Mirror is extremely heavy. The U.S. Forest Service maintains a full service campground, a picnic area for day use, and a surfaced boat ramp for launching small craft. Boats with any type of motor are prohibited. There is also a trailhead providing access to the Primitive Area on the Mirror and Duchesne River trails. Mirror Lake receives periodic stockings of catchable-sized rainbow and albino rainbow trout, as well as an annual stocking of brook trout fingerling."
    },
    {
        'designation': 'Z-4',
        'name': 'MOOSEHORN',
        'text': "Moosehorn is a popular natural lake which has been enlarged by the placement of a small dyke across the outlet. It is 8.0 acres, 10,400 feet in elevation, with 11 feet maximum depth. The lake sits in open conifers at the base of a steep shale ridge. Moosehorn is located at the foot of Bald Mountain 1/2 miles south of Mirror Lake on Highway U-150. The U.S. Forest Service maintains an overnight campground at Moosehorn with full service. Moosehorn receives a substantial amount of fishing pressure due to its proximity to the highway. The lake receives frequent plants of rainbow and albino catchables."
    },
    {
        'designation': 'Z-31',
        'name': 'MORAT #1',
        'text': "Morat #1 is a rocky shore lake located at the foot of the Blue Lake Ridge in Naturalist Basin. It is 5.4 acres, 10,740 feet in elevation, with 13 feet maximum depth. The watershed is composed of talus slopes with scattered conifers. Access is 5 miles east of U-150 on the Highline and Naturalist Basin Pack trails to the Blue/Jordan junction and then 1/2 mile north on the Blue Lake Trail. Morat #1 is the western most of the two Morat Lakes. There are several campsites present with limited horse feed. A spring water sources is available at Morat #2. Morat #1 is stocked with cutthroat trout. Angling pressure is moderate."
    },
    {
        'designation': 'Z-27',
        'name': 'MORAT #2',
        'text': "This shallow natural lake is located immediately east of Morat #1 in rocky timbered country. Morat #2 is 3.6 acres, 10,740 feet in elevation, with 5 feet maximum depth. Access is 5 miles east of the trailhead on the Highline and Naturalist Basin trails to the Blue/Jordan junction and then north for 1/2 mile on the steep Blue Lake Trail. Campsites with spring water and limited horse feed are available. Morat #2 occasionally produces some fair cutthroat trout fishing."
    },
    {
        'designation': 'Z-43',
        'name': 'OLGA',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'Z-26',
        'name': 'OLSEN',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'Z-15',
        'name': 'PACKARD',
        'text': "Packard is a scenic lake perched on a steep ledge overlooking the East Fork of the Duchesne River. It is 4.5 acres, 9,940 feet in elevation, with 10 feet maximum depth. Conifers flank the eastern and western lake margins. Good campsites are available with limited horse feed and spring water early in the year. Access is 2 1/2 miles southeast on the Highline Trail from the trailhead to the well-marked Packard Lake cutoff and then 1 mile south to the trails end. Packard contains a moderate population of brook trout and receives heavy fishing pressure."
    },
    {
        'designation': 'Z-5',
        'name': 'PASS',
        'text': "This shallow, natural lake sits immediately adjacent to Highway U-150, 1/2 mile north of the turnoff to the Mirror Lake Campground. It is 3.3 acres, 10,250 feet in elevation, with 8 feet maximum depth. The lake is a popular fishing spot for day fishermen and is heavily fished on weekends and holidays. There are no campground facilities, but sites are available for primitive camping and off-road parking. Pass provides some good fishing for rainbow, albino rainbow catchables and an occasional brook trout."
    },
    {
        'designation': 'Z-17',
        'name': 'PYRAMID',
        'text': "Pyramid is an aesthetic natural lake situated at the base of a talus slope in the Murdock Basin Area. The lake is 15 acres, 9,700 feet in elevation, with 36 feet maximum depth. There are several campsites along the northeastern margin, but spring water is unavailable. Access is 5 1/4 miles north and east of U-150 on the Murdock Basin Road to the Echo Lake turnoff. Proceed north on this road to the first left-hand turn and then west for 3/8 mile. The accessibility of this water promotes heavy fishing pressure. Pyramid contains a population of brook trout."
    },
    {
        'designation': 'Z-12',
        'name': 'SCOUT',
        'text': "Scout is a natural, glacial lake located in rocky, timbered country northwest of the Mirror Lake Highway. It is 30 acres, 10,300 feet in elevation, with 17 feet maximum depth. Camp Steiner, a Boy Scout summer camp, is located in the vicinity of Scout Lake. Access to the lake is 1/2 mile west of U-150 on a foot trail beginning at the Camp Steiner turn-off and parking area. The access road to Steiner is administrative and not open to public use. There are no camping areas at the lake. Scout is stocked with rainbow trout and sustains heavy fishing pressure."
    },
    {
        'designation': 'Z-21',
        'name': 'SCUDDER',
        'text': "Scudder is a productive lake located in thick conifers 2 miles southeast of the trailhead on the Highline Trail. It is 4.5 acres, 9,940 feet in elevation, with 10 feet maximum depth. The lake receives heavy overnight camping activity from stopover groups on this popular trail. However, drinking water and horse feed are unavailable. Scudder is subject to winterkill and does not sustain fish life."
    },
    {
        'designation': 'Z-34',
        'name': 'SHALER',
        'text': "Shaler is a high alpine lake located 3/4 mile northeast of Jordan Lake on the Naturalist Basin Trail. It is 13 acres, 10,920 feet in elevation, with 7 feet maximum depth. The total distance from the Highline Trailhead is 6 1/2 miles. The surrounding terrain is windswept tundra with scattered patches of grasses, willow and low conifers. Campsites are not available due to the open nature of the terrain and absence of wood for fuel. Spring water sources are present. The cutthroat trout population present in Shaler provides some excellent late season fly-fishing."
    },
    {
        'designation': 'Z-9',
        'name': 'SHEPARD',
        'text': "Shepard is a natural lake located in thick conifers 1/8 mile west of Hoover Lake in Murdock Basin. (See directions to Hoover.) The lake is 14.2 acres, 9,980 feet in elevation, with 32 feet maximum depth. Access is also possible on the Fehr Lake Trail from U-150. There are numerous small springs to the west and northeast. The outlet is a direct tributary to Hoover. Camping areas are available but horse feed is restricted. Shepherd contains a small population of brook, cutthroat, and rainbow trout. Fishing pressure is heavy."
    },
    {
        'designation': 'X-12',
        'name': 'SONNY',
        'text': "Sonny is a small natural lake located 150 yards northwest of Marsell Lake in Marsell Canyon. It is 5 acres, 10,460 feet in elevation, with 13 feet maximum depth. Some horse feed is available to the north, and several excellent campsites are present. However, spring water is not readily available. Sonny Lake is stocked with brook trout and receives light fishing pressure. This lake may winterkill occasionally."
    },
    {
        'designation': 'D-15',
        'name': 'TADPOLE',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'D-3',
        'name': 'TWIN #1',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'D-4',
        'name': 'TWIN #2',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'Z-13',
        'name': 'WILDER',
        'text': "Wilder is a meadow lake situated in thick timber south of the Highline Trail. It is 3.7 acres, 9,900 feet in elevation, with 14 feet maximum depth. Access is 2 1/2 miles southeast of the Highline Trailhead to the well-marked Packard Lake Trail and then 1/4 mile south. Wilder is the first lake encountered on the trail. There are several good camping areas for small groups. Horse feed is available. Spring water is unavailable. Wilder contains a good population of brook trout. Angler use is heavy."
    },
    {
        'designation': 'Z-14',
        'name': 'WYMAN',
        'text': "Wyman Lake is located in thick conifers 1/2 mile south of Wilder on the Packard Lake Trail. It is 6.5 acres, 9,980 feet in elevation, with 17 feet maximum depth. The total distance from the Highline Trailhead is 3 1/4 miles. There are numerous campsites with several acres of horse feed to the northeast in a large dry park. Spring water is unavailable. Wyman is subject to occasional winterkill but is stocked frequently with brook trout. Fishing use is moderate."
    },
    
    # PROVO-WEBER DRAINAGE - dwr-provo-weber-trimmed.pdf
    {
        'designation': 'A-1',
        'name': 'ALEXANDER',
        'text': "Alexander is an aesthetic natural lake located in heavily timbered country with very little open shoreline. It is 23 acres, 9,360 feet in elevation, with 28 feet maximum depth. Access is 3 miles north on the Spring Canyon Road from Highway U-150 and then mile southeast on a well-marked Forest Service trail. Several campsites are present along the northern lake margin, but spring water is unavailable. The fishery is sustained by aerial stocking of brook trout. Angling pressure is heavy, and litter is a problem around the lake."
    },
    {
        'designation': 'A-11',
        'name': 'AZURE',
        'text': "Azure is a natural lake located in a glacial basin formed by an end moraine of large boulders. It is 9 acres, 10,140 feet in elevation, with 23 feet maximum depth. The surrounding terrain is rocky and talus slopes flank the western and northern margins of the lake. Campsites, horse feed and spring water are not available at Azure. Better opportunities are present at nearby Rock Lake. Azure is located ¾ mile west of Haystack Lake and approximately 200 yards north and slightly west of Rock Lake. Access is limited to backpackers due to the presence of large rockslides. Recreational use is very light. Azure is not being managed for a fishery."
    },
    {
        'designation': 'A-17',
        'name': 'BEAVER',
        'text': "This remote natural lake is located ¼ mile southwest of Duck. It is 3.5 acres, 9,900 feet in elevation, with 15 feet maximum depth. Beaver is surrounded by thick timber. Several marginal campsites are present with no available spring water. Horse feed is limited to several acres of meadow grass along the outlet stream. Beaver is subject to winterkill. It is stocked every other year with brook trout. Fishing pressure is light."
    },
    {
        'designation': 'A-6',
        'name': 'BETH',
        'text': "Beth is a shallow, productive lake with an open shoreline and floating grassy banks. It is 5.4 acres, 9,780 feet in elevation, with 10 feet maximum depth. The lake is surrounded by wet meadows. Access is 6½ miles north on the Spring Canyon Road from U-150 and then west for ¼ mile on a marked spur road. There are several good campsites available with areas for mobile camping units. Spring water is unavailable. Horse pasture is present in surrounding meadows but is quite boggy. Beth contains a good population of brook trout. Fisherman use is heavy."
    },
    {
        'designation': 'A-18',
        'name': 'BIG ELK',
        'text': "Big Elk has a large dam across the outlet and is situated at the base of a steep ridge with talus slopes. It is 30 acres maximum, 10,020 feet in elevation, with 85 feet maximum depth. The two major routes of access are the Norway Flats Road and the Lake Country Trail. From U-150, proceed north on the Norway Flats Road for 7½ miles to the end and then ¾ mile beyond on the Norway Flats Trail. The last mile of road is passable to 4-wheel drive only. Access is also available from the Crystal Lake Trailhead on 7 miles of the Lake Country Trail. The trail becomes indistinct and difficult to negotiate on horseback between Island and Big Elk lakes. There are several camping areas to the south and east of the lake. Spring water and horse feed are unavailable in the immediate vicinity. Big Elk contains populations of brook and cutthroat trout. Fishing pressure is heavy."
    },
    {
        'designation': 'A-5',
        'name': 'BLUE',
        'text': "Blue is a natural lake situated at the base of a steep cliff and associated talus. It is 8 acres, 9,680 feet in elevation, with 26 feet maximum depth. The lake is surrounded by conifers with scattered small meadows around the perimeter. Access is 1½ miles beyond Buckeye Lake on a well-marked jeep trail. Campsites and spring water are available, but horse feed is limited. Blue Lake is stocked with brook trout. Fishing pressure is heavy."
    },
    {
        'designation': 'A-35',
        'name': 'BOOKER',
        'text': "Booker is one of 3 lakes situated on the Provo-Weber Drainage Divide at the foot of Mt. Watson. It is 4.1 acres, 10,460 feet in elevation, with 8 feet maximum depth. The surrounding terrain is composed of scattered conifers with large areas of exposed bedrock. Booker is located 200 yards northwest of Clyde Lake (see directions to Clyde). Campsites are present at the southeastern end. Spring water and horse feed are available at the nearby Divide #'s 1 and 2 lakes. Booker contains a small population of brook trout and sustains heavy fishing pressure."
    },
    {
        'designation': 'A-20',
        'name': 'BROOK',
        'text': "Brook is an aesthetic alpine lake situated in a small, wet meadow in timbered country. The lake is 1.1 acres, 9,720 feet in elevation, with 6 feet maximum depth. Access is 4 miles south and west of the Crystal Lake Trailhead on the Lake Country and the Weir Lake trails. The latter trail becomes indistinct beyond Weir Lake, and topographic maps may prove useful in attempts to locate Brook Lake. Campsites and spring water are available, but horse pasture is limited. Brook contains a moderate population of brook trout which may be subject to sporadic winterkill. Recreational use at Brook Lake is moderate."
    },
    {
        'designation': 'A-3',
        'name': 'BUCKEYE',
        'text': "Buckeye is a shallow, productive lake with floating, grass covered banks and islands. It is 5 acres, 9,660 feet in elevation, with 8 feet maximum depth. The lake is surrounded by a large wet meadow with conifers around the perimeter of the meadow. Buckeye receives intensive fishing pressure and brook trout are planted to supplement natural reproduction. Access is 4½ miles north of Highway U-150 on the Spring Canyon Road to the Buckeye Lake turnoff, and then ¼ mile north on a rough road to the lake. Excellent campsites with pasture and spring water are available. Users are encouraged to keep vehicles off the fragile meadow areas surrounding Buckeye."
    },
    {
        'designation': 'A-21',
        'name': 'CAROL',
        'text': "This lake does not sustain fish life. Carol Lake is a small, natural lake surrounded by a wet meadow and rocky, conifer-covered hills. It is just west of Washington Lake. The surface area is 2.9 acres, maximum depth is 7 feet and the elevation is 10,180 feet."
    },
    {
        'designation': 'A-47',
        'name': 'CLEGG',
        'text': "Clegg is a productive lake located in partly timbered country with scattered meadows and rocky shelves. It is 5.1 acres, 10,460 feet in elevation, with 12 feet maximum depth. The major portion of the lake is shallow and Clegg is subject to occasional winterkill. Fisherman pressure is primarily day use, but campsites are available with no spring water source. Scattered meadows in the vicinity provide horse feed. Access is 1¾ miles northwest of the Bald Mountain Trailhead on the Notch Mountain Trail. Clegg receives frequent plants of brook trout."
    },
    {
        'designation': 'A-34',
        'name': 'CLIFF',
        'text': "This natural lake is located in a small glacial basin surrounded by scattered conifers and meadows. Cliff is 9 acres, 10,230 feet in elevation, with 20 feet maximum depth. There are several good campsites to the north and east of the lake. Spring water is available throughout the season. Horse pasture is limited but can be located to the north in the vicinity of Petit Lake. Access is ¼ mile north of the Crystal Lake Trailhead on the Watson Clyde Trail. This trail is unmarked but can be located at the northwestern extremity of Upper Lily Lake. Cliff contains pan-sized cutthroat trout and sustains heavy angler use."
    },
    {
        'designation': 'A-28',
        'name': 'CLYDE',
        'text': "Clyde is an oblong lake located in a rocky basin at the foot of Mount Watson. It is 16 acres, 10,420 feet in elevation with 21 feet maximum depth. The shoreline is characterized by scattered conifers with large areas of exposed bedrock along the southeastern margin. Camping opportunities are limited due to the ruggedness and slope of the terrain. Spring water and horse feed are available in the Divide Lakes vicinity. Trail access is 1¼ miles north of the Crystal Lake Trailhead on the unmarked and indistinct Watson Clyde Trail. This trail begins near Upper Lily Lake. Fisherman use is heavy for pan-sized brook trout."
    },
    {
        'designation': 'A-51',
        'name': 'CRYSTAL',
        'text': "Crystal is a productive, reservoired lake surrounded by coniferous forests and small, wet meadows. The lake is 9.8 acres, 10,020 feet in elevation, with 7 feet maximum depth. Several good campsites are available with a piped water source and abundant horse pasture in large, dry parks to the south and southwest. The lake lies 200 yards west of the Crystal Lake Trailhead on the North Fork Trail. Crystal receives heavy fishing pressure from day and overnight groups. The lake is stocked with brook trout on an annual basis."
    },
    {
        'designation': 'A-40',
        'name': 'CUTTHROAT (CLINT)',
        'text': "Cutthroat is a meadow lake situated at the foot of a steep shale ridge in the North Fork Drainage. It is 3 acres, 9,940 feet in elevation, with 10 feet maximum depth. Cutthroat is located 1 mile west of the Long Lake Dam within sight of the Lake Country Trail. The total distance from the Crystal Lake Trailhead is 3 miles. The Forest Service sign at the lake indicates Clint rather than Cutthroat. Excellent campsites and abundant spring water are available. The surrounding meadow contains limited horse feed but cannot sustain intensive grazing. Angling pressure is light and fishing fast for small brook trout."
    },
    {
        'designation': 'A-22',
        'name': 'DIAMOND',
        'text': "Diamond is a productive lake which lies in a large meadow at the head of the eastern most tributary to Trial Lake. The lake is 3 acres, 9,900 feet in elevation, with 7 feet maximum depth. Limited overnight camping is available with spring water and horse feed. Improved campsites with tap water and rest room facilities are also present at the nearby Trial Lake campground. The fishery is composed of a small population of wary brook and cutthroat trout. Angling pressure is moderate."
    },
    {
        'designation': 'A-36',
        'name': 'DIVIDE #1',
        'text': "This shallow lake is located in a rugged basin between Watson and Notch mountains. Divide #1 is 3.5 acres, 10,460 feet in elevation, with 5 feet maximum depth. It is one of three lakes located on the drainage divide between the Weber and Provo basins. The surrounding terrain is extremely rocky with large areas of exposed bedrock and scattered conifers and meadows. Access is ¼ mile northwest of Clyde Lake on an indistinct trail. Good campsites with excellent spring water are available at the nearby Divide #2 Lake. Horse feed can be obtained from meadows adjacent to Divide #1 and from a large park north of the lake along the inlet stream. The lake contains brook trout, and fishing pressure is heavy."
    },
    {
        'designation': 'A-7',
        'name': 'DUCK',
        'text': "Duck is a reservoired lake located 1¼ miles beyond Long Lake on the Lake Country Trail. It is 12.7 acres, 9,780 feet in elevation, with 15 feet maximum depth. The total distance from the Crystal Lake Trailhead is 3¼ miles. The shoreline is predominantly timbered with scattered meadows and a talus ridge to the west. Duck contains brook and cutthroat trout and receives heavy fishing pressure. Several good campsites are present and limited horse feed is available from the peat meadow."
    },
    {
        'designation': 'A-16',
        'name': 'FAITH',
        'text': "Faith has been experimentally stocked with brook trout. This lake frequently winterkills and is no longer managed to provide a fishery."
    },
    {
        'designation': 'A-14',
        'name': 'FIRE',
        'text': "Fire Lake has a rock masonry dam across the outlet and is located in a steep, rocky basin with scattered conifers. It is 9 acres maximum, 10,200 feet in elevation, with 59 feet maximum depth. Access is 150 yards south of Junior Lake in the North Fork Drainage. Camping opportunities are limited due to the steep, rocky nature of the watershed. Spring water and horse feed are not available. Angling pressure is moderate for cutthroat trout."
    },
    {
        'designation': 'A-46',
        'name': 'FORKS',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'A-9',
        'name': 'HAYSTACK',
        'text': "Haystack is an aesthetic natural lake surrounded by thick coniferous forest and scattered meadows. It is 17 acres, 9,940 feet in elevation, with 29 feet maximum depth. The lake is nearly circular in outline. Access is ¼ mile west of the Spring Canyon Road on a side road limited to four-wheel drive vehicles. Campsites are plentiful along the eastern margin of the lake, but spring water is unavailable. Haystack contains populations of brook and cutthroat trout, and fishing pressure is heavy."
    },
    {
        'designation': 'A-15',
        'name': 'HIDDEN',
        'text': "Hidden is located in rocky, timbered country in the North Fork Drainage. It is 8.2 acres, 9,760 feet in elevation, with 25 feet maximum depth. Access is 2¼ miles south of Weir Lake on an indistinct segment of the Weir Lake Trail. The total distance from the Crystal Lake Trailhead is 5 miles. Hidden is situated in a small, remote basin and is difficult to locate. A topographic map may be helpful in locating this lake. Several marginal campsites are present with no available horse feed or spring water. Angling pressure is moderate for stocked brook trout."
    },
    {
        'designation': 'A-54',
        'name': 'HOPE',
        'text': "Hope is a shallow, productive, little lake located along the popular Notch Mountain Trail. It is located on a rock ledge overlooking Faith and Wall lakes. The surface area is 2.0 acres, maximum depth is 5 feet and the elevation is 10,340 feet. Camp sites are available with abundant horse feed but no spring water. Hope Lake is being experimentally stocked with brook trout."
    },
    {
        'designation': 'A-48',
        'name': 'HOURGLASS',
        'text': "Hourglass has an irregular shoreline and is situated at the base of a talus slope ¼ mile due west of Little Elk Lake in the Norway Flats vicinity. It is 5.7 acres, 9,980 feet in elevation, with 20 feet maximum depth. Conifers flank the eastern lake margin and are scattered among talus rocks to the west. Access trails to the lake do not exist. Campsites are available but horse feed and spring water are not present. The lake contains populations of stocked brook and cutthroat trout, and angling pressure is heavy."
    },
    {
        'designation': 'A-57',
        'name': 'ISLAND',
        'text': "Island Lake has a small dam across the outlet and is located 3¾ miles west of the Crystal Lake Trailhead on the Lake Country Trail. It is 28 acres maximum, 10,140 feet in elevation, with 40 feet maximum depth. The shoreline is characterized by rocky cliffs, open meadows and scattered conifers. Camping opportunities are available with some horse feed. There is no spring water. Island is a popular water and receives substantial fishing and camping activity. The lake contains populations of wary brook and cutthroat trout, and fishing is unpredictable."
    },
    {
        'designation': 'A-13',
        'name': 'JACKS',
        'text': "This small oblong lake is situated in timbered country with open shorelines. Jacks is 1.2 acres, 7,980 feet in elevation, with 23 feet maximum depth. The lake is located 700 yards east of Weir Lake in the North Fork Drainage (see directions to Weir Lake). There is one camp site present, but spring water is unavailable and horse feed restricted. Jacks Lake contains a small population of brook trout and is subject to occasional winterkill."
    },
    {
        'designation': 'A-31',
        'name': 'JAMES',
        'text': "James is a natural lake located in a small meadow surrounded by rocky shelves, bedrock and talus. It is 2.1 acres, 10,500 feet in elevation, with 8 feet maximum depth. There are scattered conifers around the lake margin. The inlet provides excellent spring water. Marginal campsites are present with some horse feed. Access is ¼ mile north of Divide #1 Lake along the inlet stream to the foot of Notch Mountain. Total distance from the Crystal Lake Trailhead is 2¼ miles. James is subject to occasional winterkill but is stocked with brook trout on a frequent basis."
    },
    {
        'designation': 'A-30',
        'name': 'JOHN',
        'text': "John is a shallow, natural water located on a rocky ridge ¼ mile northeast of Clyde Lake (see directions to Clyde Lake). It is 4 acres, 10,500 feet in elevation, with 10 feet maximum depth. The lake appears as Booker on USGS topographic maps. John is situated in a small meadow with scattered conifer patches and surrounded by rocky ledges. Campsites and horse feed are limited, and spring water is unavailable. Direct access for horses is difficult. John maintains a good population of pan-sized brook trout."
    },
    {
        'designation': 'A-56',
        'name': 'JUNIOR',
        'text': "This aesthetic meadow lake sits at the base of a steep, rocky ridge ¼ mile southwest of Island Lake (see directions to Island Lake). Direct access trails do not exist but horses can easily reach the lake. It is 2.8 acres, 10,200 feet in elevation, with 11 feet maximum depth. The outlet is a direct tributary to Fire Lake. Several campsites are present with up to 10 acres of horse feed. Available springs are too small to obtain water. Angling pressure is light. Junior Lake is subject to occasional winterkill, but has been known to produce some good cutthroat trout fishing."
    },
    {
        'designation': 'A-63',
        'name': 'KAREN',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'A-2',
        'name': 'LAMBERT',
        'text': "Lambert is a shallow, natural lake with floating banks. It is 2 acres, 9,630 feet in elevation, with 8 feet maximum depth. The lake is situated in a large wet meadow with conifers flanking the southern lake margin. Thick patches of pond lily are common in the shoal areas. Access is 2 miles north of Highway U-150 on the Spring Canyon Road to the Lambert Meadow turnoff. Proceed northwest on this road past the large meadow to a point where the road turns abruptly west, and then head northeast on foot for 300 yards to the lake. Camping opportunities are limited, and spring water is unavailable. Lambert Lake is stocked with brook trout."
    },
    {
        'designation': 'A-43',
        'name': 'LILLIAN',
        'text': "Lillian is a beautiful meadow lake located in timbered country immediately south of Long Reservoir. It is 2 acres, 10,100 feet in elevation, with 8 feet maximum depth. Excellent campsites with spring water are available. Horse pasture is present in adjacent and surrounding parks. Trail access is 2 miles west of the Crystal Lake Trailhead on the Lake Country and Weir Lake cutoff trails. Lillian sustains a small population of brook trout. Angling pressure is light."
    },
    {
        'designation': 'A-58',
        'name': 'LILLY',
        'text': "Lilly is located 300 yards east of Teapot Lake adjacent to the Mirror Lake Highway (U-150). It is 4.1 acres, 9,800 feet in elevation, with 13 feet maximum depth. The lake lies in a boggy meadow encompassed by conifers. The Forest Service maintains a full-service campground at Lilly with 14 units. Fishing pressure is heavy. Lilly is stocked frequently with catchable-sized rainbow trout. Anglers may also creel an occasional brook trout."
    },
    {
        'designation': 'A-25',
        'name': 'LILY, LOWER',
        'text': "Lower Lily is a productive meadow lake located 200 yards north of the Crystal Lake Trailhead on the Notch Mountain Trail. It is 3.2 acres, 10,030 feet in elevation with 16 feet maximum depth. Lower Lily is the eastern most of the two Lily lakes. The southern arm of the lake is very shallow and completely covered by pond lily. The northern arm is deep in spots. Fishing pressure is primarily day use with very little overnight camping activity. There are several potential areas for campsites, but drinking water must be carried in. Lower Lily contains brook trout and angling pressure is heavy."
    },
    {
        'designation': 'A-24',
        'name': 'LILY, UPPER',
        'text': "Upper Lily Lake is a natural meadow lake with a productive substrate and boggy banks. It is 3.2 acres, 10,020 feet in elevation, with 12 feet maximum depth. The lake meadow is surrounded on all sides by conifers. Access is 200 yards north of the Crystal Lake Trailhead on the Notch Mountain Trail which passes between Upper and Lower Lily lakes. Upper Lily lies west of the trail. There are several campsites situated along the western lake margin, but spring water is not present. Horse feed is available in limited supply. Upper Lily Lake is not stocked and has been set aside as a botanical station for Brigham Young University."
    },
    {
        'designation': 'A-19',
        'name': 'LITTLE ELK',
        'text': "Little Elk has an irregular shoreline and is located in a rocky basin in the Norway Flats vicinity. It is 13.2 acres, 9,780 feet in elevation, with 31 feet maximum depth. There are no inlets or outlets, and the water level drops about 10 feet annually. Access is 6½ miles north of Highway U-150 on the Norway Flats Road to the well-marked Little Elk turnoff and then north for ¼ mile. There are several campsites along the lake margin, but spring water is unavailable. Recreational pressure is moderate. The lake is subject to winterkills. It is stocked with cutthroat trout."
    },
    {
        'designation': 'A-62',
        'name': 'LONG POND',
        'text': "Long is a small, narrow pond located on the outlet stream immediately below Long Reservoir. It is 2 acres, 10,100 feet in elevation, with 5 feet maximum depth. Inlet and outlet flows are highly variable and controlled by the reservoir operation. During the winter, the outlet valve is shut down and flows are not sufficient to maintain fish populations. However during the summer Long Pond contains small numbers of brook and cutthroat trout recruited each year from Long Reservoir. Good campsites are available with limited horse feed. Fishing pressure is moderate."
    },
    {
        'designation': 'A-37',
        'name': 'LONG',
        'text': "This reservoired lake is located in a rocky basin with scattered patches of conifers. Long is 35 acres maximum, 10,100 feet in elevation, with 26 feet maximum depth. Access is 2 miles west of the Crystal Lake Trailhead on the Lake Country Trail. Excellent campsites with horse feed are available. However, a spring water source is not present. Long contains brook and cutthroat trout and sustains heavy angling pressure."
    },
    {
        'designation': 'A-59',
        'name': 'LOST',
        'text': "Lost is a large reservoir located immediately across the highway from Teapot and Lilly lakes. The reservoir is 62 acres maximum, 9,400 feet in elevation, with 22 feet maximum depth. Fishing is sustained by stocking catchable-sized rainbow trout throughout the summer. Lost is a popular camping area and the Forest Service has established an improved campground at the lake."
    },
    {
        'designation': 'A-12',
        'name': 'MARJORIE',
        'text': "Marjorie is a reservoired lake located on the ridge southeast of Weir Lake. It is 13 acres maximum, 9,980 feet in elevation, with 16 feet maximum depth. The shoreline is gently sloping with scattered conifers and meadows. Access is 2¼ miles west of the Crystal Lake Trailhead on the Lake Country and Weir Lake trails to Weir and then ¼ mile to the southeast. Campsites are present but spring water is unavailable. Marjorie contains Arctic grayling. Angling pressure is heavy."
    },
    {
        'designation': 'A-49',
        'name': 'MONA RAE',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'P-8',
        'name': 'NORWAY FLATS',
        'text': "Norway Flats Lake is located at the base of a talus ridge ¼ mile northwest of Little Elk Lake and immediately northeast of Hourglass. Direct trail access is not available. It is 3 acres, 9,900 feet in elevation, with 16 feet maximum depth. Conifers flank the southern and eastern lake margins. Camping opportunities at Norway Lake are limited, but several good sites are present between the lake and Hourglass along the interconnecting stream. Spring water and horse feed are unavailable. Experimental stocking of Norway Lake indicates that the lake winterkills and has no potential to sustain fish life."
    },
    {
        'designation': 'A-26',
        'name': 'PETIT (JUNIOR #5)',
        'text': "Petit is a productive meadow lake located on the ridge north of Cliff Lake. It is 2 acres, 10,300 feet in elevation, with 3 feet maximum depth. The lake is shallow throughout with no deep holes. Access is ¼ mile north of the Crystal Lake Trailhead on the unmarked Watson-Clyde Trail. Campsites and horse feed are available in the general lake vicinity, and spring water is present at Cliff Lake. Petit contains a small population of wary brook trout. Angling pressure is moderate."
    },
    {
        'designation': 'A-8',
        'name': 'POT',
        'text': "This reservoired lake is located ¼ mile southwest of Weir on the Weir Lake Cutoff Trail. Pot is 4 acres maximum, 9,940 feet in elevation, with 28 feet maximum depth. The total distance from the Crystal Lake Trailhead is 2¼ miles. The shoreline is rocky with scattered conifers. There are several campsites available, but spring water is not present. Horse pasture can be obtained from scattered meadows to the north and west. Angling pressure is heavy. Pot is stocked with brook trout."
    },
    {
        'designation': 'A-38',
        'name': 'RAMONA',
        'text': "Ramona is situated on the ridge ¼ mile northeast of Island Lake in the North Fork Drainage. It is 4.7 acres, 10,340 feet in elevation, with 21 feet maximum depth. Direct trail access is not available, but the terrain can be negotiated on horseback. The total distance from the Crystal Lake Trailhead is 3¾ miles. The lake is surrounded by large areas of exposed bedrock and scattered conifers. Marginal campsites are available, but spring water is not present. Horse feed is scarce. Ramona sustains moderate fishing pressure and is stocked with brook trout."
    },
    {
        'designation': 'A-10',
        'name': 'ROCK',
        'text': "Rock is a natural lake situated in rough terrain at the base of Haystack Mountain, ¼ mile west of Haystack Lake. It is 8 acres, 10,140 feet in elevation, with 14 feet maximum depth. Rock has a history of winterkill. Several good campsites are available with limited spring water. There are no clearly defined trails, and access is limited to backpackers due to the rough nature of the terrain and large rockslides. Angling pressure is moderate. Rock Lake receives frequent plants of brook trout, but fishing is unpredictable."
    },
    {
        'designation': 'A-52',
        'name': 'SHADOW',
        'text': "Shadow is located ¼ mile south of Washington Reservoir along the major drainage system. It is 14 acres, 10,060 feet in elevation, with 20 feet maximum depth. Campsites are present with an excellent source of spring water located along the southern margin of the lake. Horse feed is available but limited. Shadow contains a population of brook trout. Camping and fishing pressure is heavy."
    },
    {
        'designation': 'A-45',
        'name': 'SHALLOW (HAYSTACK #2)',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'A-39',
        'name': 'SHINGLE CREEK, EAST',
        'text': "East Shingle Creek Lake is a deep, natural body of water situated at the head of Shingle Creek. It is 7 acres, 9,700 feet in elevation, with 44 feet maximum depth. The lake is surrounded by thick timber with scattered small meadows. Access is 6½ miles north of U-150 on the improved Upper Setting Road to the trailhead and then 1¾ miles northeast on the Upper Setting Pack Trail. Access is also provided by the Shingle Creek Pack Trail from U-150, but hiking distance is much greater. Several campsites with spring water are available. Horse pasture is limited in the lake vicinity. Angling pressure is heavy due to the accessibility of this lake. In addition to brook trout, splake (a brook trout - lake trout hybrid) were introduced to help control a population of redside shiners."
    },
    {
        'designation': 'P-62',
        'name': 'SHINGLE CREEK, LOWER',
        'text': "Lower Shingle Creek is a shallow natural lake located in an isolated basin in the Shingle Creek Drainage. It is 4 acres, 9,620 feet in elevation, with 14 feet maximum depth. The shoreline is timbered with a large, open meadow to the northeast. Trails do not exist and horse access is difficult. Proceed east of the Upper Setting Trailhead for 1¾ miles over steep terrain to the lake. Lower Shingle is also accessible via the Shingle Creek Trail from U-150. Follow the trail north for 4½ miles to a large meadow and then head east for ¼ mile. Campsites are available, but spring water is present only in the early season. Lower Shingle Creek contains brook trout, and angling pressure is moderate."
    },
    {
        'designation': 'P-60',
        'name': 'SHINGLE CREEK, WEST',
        'text': "West Shingle Creek is a productive, spring-fed meadow lake with floating banks and islands. It is 5 acres, 9,940 feet in elevation, with 12 feet maximum depth. The lake is shallow and experiences water level fluctuation of 4 to 5 feet annually. Access is 1¾ miles north of the Upper Setting Trailhead along a logging road which has been blocked to vehicular access by the Forest Service. Campsites with spring water are available. West Shingle provides marginal fish habitat and receives little annual recreational use. The lake is stocked with brook trout."
    },
    {
        'designation': 'A-55',
        'name': 'SHOESTRING',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'A-44',
        'name': 'SPECTACLE (HOURGLASS)',
        'text': "This irregularly shaped, natural lake is situated in thick conifers with some floating banks and islands. Spectacle is 9.3 acres, 9,740 feet in elevation, with 17 feet maximum depth. The lake appears as Hourglass on USGS topographic maps. Large expanses of yellow pond lily cover the surface of this lake. Access is 4½ miles north of Highway U-150 on the Spring Canyon Road to a small roadside pond and then west for ¼ mile to Spectacle. There is no trail to the lake. Camping areas are limited, and spring water is not available. Angling pressure is moderate. Spectacle is stocked with brook trout."
    },
    {
        'designation': 'A-4',
        'name': 'SPRING CANYON',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'A-42',
        'name': 'STAR',
        'text': "Star is a reservoired lake located 1 mile northeast of Trial Lake. It is 16 acres maximum, 9,980 feet in elevation, with 35 feet maximum depth. Star is located in coniferous forest with scattered meadows to the north and northwest. There are few potential camping areas and no spring water. Horse feed is limited. From Trial Lake, follow the major inlet stream north to a small pond on a tributary. The reservoir is located at the top of this tributary stream. Star contains a limited population of cutthroat and brook trout and sustains heavy angling pressure. Star Lake contains a population of mountain suckers. It isn't known how these suckers got into the lake. One possibility is that they were brought in by anglers and used illegally as bait."
    },
    {
        'designation': 'A-53',
        'name': 'TAIL',
        'text': "Tail is a natural lake located south of Washington Reservoir in dense conifers. It is 9.8 acres, 9,980 feet in elevation, with 13 feet maximum depth. When Washington Reservoir is filled to capacity, there is a direct connection between the reservoir and Tail Lake. Access is ¼ mile southwest of the dam at Washington along the shoreline of the reservoir. There are several campsites but spring water is unavailable. Tail contains a good population of brook, cutthroat and rainbow trout. This lake isn't stocked. The fish either migrate from Washington Reservoir during high water or they are naturally produced. Angling pressure is heavy."
    },
    {
        'designation': 'A-60',
        'name': 'TEAPOT',
        'text': "Teapot is a natural lake which has been modified by the placement of a dam and a retaining dike at the eastern end. It is 13 acres, 9,950 feet in elevation, with 46 feet maximum depth. Teapot is located one mile east of the Trial Lake Turnoff on U-150 approximately 27 miles east of Kamas. The lake receives heavy fishing and camping activity due to its proximity to the Mirror Lake Highway. Teapot is stocked with rainbow and albino rainbow catchables, as well as brook trout."
    },
    {
        'designation': 'A-61',
        'name': 'TRIAL',
        'text': "Trial Reservoir is a popular fishing water located ¾ mile west of the Mirror Lake Highway on an improved Forest Service Road. It is 98 acres maximum, 9,800 feet in elevation, with 68 feet maximum depth. There is a large, developed campground at Trial providing full service. Fishing pressure is very heavy. Trial is stocked with rainbow and albino rainbow catchables, as well as brook trout fingerling."
    },
    {
        'designation': 'A-41',
        'name': 'TRIDENT',
        'text': "This shallow, productive lake is located immediately adjacent to the Spring Canyon Road 6½ miles north of U-150. Trident is 4 acres, 9,400 feet in elevation, with 5 feet maximum depth. The lake lies in a meadow surrounded by conifers. Camping areas are available with turn-offs for mobile camping units. Spring water is not present. Trident contains brook trout and receives heavy fishing pressure."
    },
    {
        'designation': 'A-33',
        'name': 'TWIN, LOWER',
        'text': "Lower Twin is a small lake situated in rocky terrain immediately south of Upper Twin Lake. It is 3 acres, 10,410 feet in elevation, with 14 feet maximum depth. The shoreline is characterized by low, rocky shelves and boulders with scattered conifers. Camping areas are present, but better sites are available at Upper Twin Lake. Spring water may be available at Upper Twin during the early summer months. Access is 2¾ miles north of the Crystal Lake Trailhead on the Notch Mountain Trail. Leave the trail at the point where it begins the last incline to Notch Pass and head directly west for ¼ mile to the Twin Lakes Basin. Lower Twin contains brook trout. Angling pressure is predominantly day use, but heavy."
    },
    {
        'designation': 'A-32',
        'name': 'TWIN, UPPER',
        'text': "Upper Twin is a natural lake located in rocky terrain at the base of Notch Mountain. It is 9 acres, 10,420 feet in elevation, with 13 feet maximum depth. The lake is surrounded by small meadow areas and sparse conifers. Campsites are available with limited horse feed. Spring water is present only during the early summer months. Access is 2¾ miles north of the Crystal Lake Trailhead on the Notch Mountain Trail. Leave the trail where it begins the last incline to Notch Pass and head directly west for ¼ mile to the Twin Lakes Basin. Direct access on horseback is difficult. The lake contains brook trout and angling pressure is heavy."
    },
    {
        'designation': 'A-29',
        'name': 'WALL',
        'text': "Wall is a sizeable reservoir located in a steep, rocky basin. It is 80 acres maximum, 10,140 feet in elevation, with 97 feet maximum depth. The shoreline is characterized by talus rocks and scattered conifers. Access is one mile north of the Crystal Lake Trailhead on the Notch Mountain Trail. There are several areas for camping along the eastern lake margin. However, horse feed is limited and spring water unavailable. Wall Reservoir has brook and cutthroat trout and angling pressure is heavy."
    },
    {
        'designation': 'A-23',
        'name': 'WASHINGTON',
        'text': "Washington is a large reservoired lake located in thick timber at the northern arm of Haystack Mountain. It is 106 acres maximum, 9,900 feet in elevation, with 70 feet maximum depth. Access is ¼ mile west of U-150 at the Trial Lake Turnoff to the Crystal Lake Road. Take an immediate left turn from the Crystal Lake Road and proceed west for ¼ mile over a rough road to Washington. Campsites are available but spring water is not present. Washington Lake contains populations of catchable-sized rainbow trout sustained by stocking, as well as brook and cutthroat trout. Angling pressure is heavy."
    },
    {
        'designation': 'A-27',
        'name': 'WATSON',
        'text': "This shallow, productive lake is located in thick coniferous forest at the base of Watson Mountain. Watson is 6 acres, 10,420 feet in elevation, with 10 feet maximum depth. The lake is irregular in outline with a large shallow bay to the southeast. Access is one mile north of the Crystal Lake Trailhead on the Watson Clyde Trail. Campsites are present with available spring water. Horse feed can be obtained to the south in the vicinity of Petit Lake. Angling pressure is moderate. The lake contains brook trout."
    },
    {
        'designation': 'A-50',
        'name': 'WEIR',
        'text': "Weir is a reservoired lake located in the North Fork Drainage directly downstream from Long Reservoir. It is 7 acres maximum, 9,940 feet in elevation, with 13 feet maximum depth. The shoreline is rocky and characterized by steep, timbered slopes. The dam is a rock masonry structure. Inlet flows sustain fish populations through the winter. Access is 2¼ miles west of the Crystal Lake Trailhead on the Lake Country and Weir Lake trails. Campsites are available, but horse feed is scarce. Spring water is present early in the season. Weir contains populations of cutthroat trout and Arctic grayling. Angling pressure is moderate."
    },
    
    # DRY GULCH AND UINTA DRAINAGE - dwr-dry-gulch-and-uinta-trimmed.pdf
    {
        'designation': 'DG-1',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'DG-3',
        'name': 'CROW',
        'text': "Crow is an irregular shaped lake located in steep rocky terrain. It is 18 acres, 10,350 feet in elevation, with 26 feet maximum depth. Access is via the Timothy Creek Road to Jackson Park, then down the steep sides of the basin to lakes DG 6,7 and 8: (a) Follow the outlet stream south 3/4 mile to Crow Lake. Good campsites, spring water and horse feed are available. This lake contains a good population of cutthroat trout. Angling pressure is moderate, and there is excessive litter around the shoreline."
    },
    {
        'designation': 'DG-4',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'DG-5',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'DG-6',
        'name': None,
        'text': "Lakes DG 6, 7 and 8 are shallow, interconnecting lakes located in a grassy meadow. DG-6 is 3 acres, 10,550 feet in elevation, with 5 feet maximum depth. Access is via Jackson Park north 1-1/2 miles, then descend over the canyon rim following an east-northeast direction. Good campsites, spring water and horse feed are available near the lake. Cutthroat trout are stocked and angling pressure is light."
    },
    {
        'designation': 'DG-7',
        'name': None,
        'text': "This is a very shallow lake located between lakes DG-6 and DG-8. It is 6 acres, 10,550 feet in elevation, with 4 feet maximum depth. Good campsites, spring water and horse feed are available. This lake has a small population of cutthroat trout which migrate from DG-6. The lake is not stocked because of winterkill. Fishing pressure is very light."
    },
    {
        'designation': 'DG-8',
        'name': None,
        'text': "DG-8 sits due east of DG-7 about 70 yards. It is 7 acres, 10,550 feet in elevation, with 8 feet maximum depth. Access by following the main basin stream north 3/4 mile from Crow Lake to DG-6. Campsites, spring water and horse feed are within 1/2-mile of the lake. DG-8 is too shallow to stock, but has a few cutthroat trout that migrate from DG-6. Fishing pressure is very light."
    },
    {
        'designation': 'DG-9',
        'name': None,
        'text': "This lake has a steep rock escarpment located just below the outlet. It is 10 acres, 10,750 feet in elevation, with 27 feet maximum depth. Access is via Timothy Creek Road to Jackson Park then east down the steep basin side to lakes DG 6, 7 and 8. Follow the DG-6 inlet north 1/2-mile and up the rock escarpment. Campsites and spring water are limited, but good horse feed is available. This lake contains a small population of cutthroat trout. Angling pressure is light."
    },
    {
        'designation': 'DG-10',
        'name': None,
        'text': "This natural lake is bounded by meadows on the north and south and rock ridges on the east and west. It is 10 acres, 10,750 feet in elevation, with 12 feet maximum depth. Access is to follow the DG-9 inlet north 1 mile. There is no spring water and campsites are marginal, but good horse feed is available to the north and south. A small population of healthy cutthroat trout inhabit the lake. Angling pressure is very light."
    },
    {
        'designation': 'DG-14',
        'name': None,
        'text': "DG-14 sits at the northeast head of the canyon 2 miles north of Crow Lake. It is 2 acres, 11,000 feet in elevation, with 10 feet maximum depth. There is no trail to the lake. No campsites or horse feed are available, but cold spring water is plentiful from the talus slope. This lake contains a fair population of cutthroat trout which are maintained through stocking. Angling pressure is very light."
    },
    {
        'designation': 'DG-15',
        'name': None,
        'text': "This lake sits at the base of the northwest rim at the head of Crow Canyon. The lake has a good fairy shrimp population but has extreme water level fluctuations. It is 3 acres, 10,950 feet in elevation, with 9 feet maximum depth. Campsites, spring water and horse feed are not available. It contains a small population of cutthroat trout which is subject to occasional winterkill. Angling pressure is very light."
    },
    {
        'designation': 'DG-16',
        'name': None,
        'text': "This is the second lake sitting against the northwest rim of the canyon located 100 feet south of DG-15. It is 3 acres, 10,950 feet in elevation, with 8 feet maximum depth. No campsites, spring water or horsefeed are available. A small population of cutthroat trout inhabit the lake, and it is subject to winterkill. Fishing pressure is very light."
    },
    {
        'designation': 'DG-17',
        'name': None,
        'text': "This is the third lake near the northwest rim at the head of the basin, and is 100 yards east of DG-16. It is 3 acres, 10,950 feet in elevation, with 12 feet maximum depth. No campsites, spring water or horsefeed are available. A large population of cutthroat is found in the lake, and it is partially sustained through natural reproduction. Angling pressure is very light."
    },
    {
        'designation': 'U-96',
        'name': 'BOLLIE',
        'text': "This natural lake is in the Uinta River drainage and is described in that section of this booklet. It is also listed in this section of the booklet because the Dry Gulch drainage map shows the access better than the Uinta drainage map does."
    },
    {
        'designation': 'DG-29',
        'name': None,
        'text': "DG-29 is a small beaver pond subject to an occasional winterkill. It is 2 acres, 9,500 feet in elevation, with 8 feet maximum depth. Access is via Heller Reservoir 1/4 mile northwest to a long park. Follow the park 1/2-mile then turn east 1/8 mile. Horse feed is excellent, but campsites and spring water are not available. This pond is presently not managed to provide a fishery. The lake habitat is not suitable for fish. Fishing pressure is very light."
    },
    {
        'designation': 'DG-30',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'DG-28',
        'name': 'HELLER RESERVOIR',
        'text': "Heller Reservoir has a small, high dam on the southwest outlet. It is 12 acres, 10,108 feet in elevation, with 37 feet maximum depth. Access is 4 miles north on the Dry Gulch Road. The road is closed at this point, so follow the jeep trail on foot 2 miles to the reservoir. Spring water and campsites are available, but there is no horse feed. The fishery is composed of a stable population of pan-sized brook trout. Angling pressure is heavy, and litter is a problem around the lake."
    },
    {
        'designation': 'DG-27',
        'name': 'HIDDEN',
        'text': "Hidden is isolated lake in the head of Heller basin. It is 10 acres, 9,520 feet in elevation, with 39 feet maximum depth. Access is 2 miles northeast on a poorly marked trail from Heller Reservoir. Spring water is abundant, but good campsites and horse feed are not available. This lake contains a fair population of healthy brook trout. Fishing pressure is light."
    },
    {
        'designation': 'DG-26',
        'name': 'LOWER LILY PAD',
        'text': "Lower Lily Pad is a productive meadow lake covered with aquatic vegetation. It is 9 acres, 10,275 feet in elevation with 11 feet maximum depth. Access is via the vague trail to Upper Lily Pad Lake, then, 1/8 mile due east. Campsites are available, horse feed is limited, and there is no spring water. A small population of brook trout are found in this lake. Fishing pressure is light."
    },
    {
        'designation': 'DG-25',
        'name': 'UPPER LILY PAD',
        'text': "Upper Lily Pad is a beautiful meadow lake surrounded by conifers. It is 12 acres, 10,280 feet in elevation, with 37 feet maximum depth. Access is 7.5 miles via the Dry Gulch Road and pack trail over Flat Top Mountain; or 2 miles northwest of Hellers Reservoir, cross-country. Excellent campsites and horse feed are found around the lake, but spring water is limited. This lake contains small populations of healthy brook and cutthroat trout. Angling pressure is heavy, and there is a litter problem."
    },
    {
        'designation': 'U-94',
        'name': 'ALBERT',
        'text': "This cirque lake is located in the far southwest corner of an extremely steep and rocky basin. It is 7 acres, 10,826 feet in elevation, with 8 feet maximum depth. Access is to go northwest up a ridge 2 miles from Bollie Lake, then turn north and climb down a steep talus slope into the basin. There are no trails, camping sites or horsefeed around the lake; horses cannot be taken into Albert. Many pan-sized cutthroat inhabit the lake. These fish are sustained by natural reproduction. The lake receives very little fishing pressure and is a must for the rugged outdoorsman."
    },
    {
        'designation': 'U-14',
        'name': 'ALLRED',
        'text': "This natural lake is located 18 miles from the Uinta River trailhead and 225 yards south of the Atwood Lake dam. It is 34 acres, 10,995 feet in elevation, with 30 feet maximum depth. The rocky trail is well marked but due to the numerous steep switchbacks the distance seems longer than it is. Campsites and horse pasture are both abundant around Allred Lake. Nice-sized brook trout are quite numerous in the lake and are sustained through natural reproduction. Fishing and camping pressure are moderate. Allred Lake is a must for those wanting a rugged wilderness experience and fast fly-fishing for plump brookies in the evening."
    },
    {
        'designation': 'U-16',
        'name': 'ATWOOD',
        'text': "Atwood Lake is the largest lake in the Uinta River drainage. It has an earthen dam on the west end and water levels fluctuate considerably each year. Atwood is approximately 200 acres, 11,030 feet in elevation, with 40 feet maximum depth. Access is 18 miles from U-Bar Ranch over a well-marked trail. Good campsites and horse feed are available around the lake. Atwood Lake has one of the largest brook trout populations in the Uinta Mountains. A few golden trout are also found in the lake. Camping and angling pressure are moderate."
    },
    {
        'designation': 'U-18',
        'name': 'B-29 LAKE',
        'text': "This natural lake sits in a wet meadow in the far southeast corner of Atwood Basin. It is 19 acres, 10,740 feet in elevation, with 7 feet maximum depth. There is no marked trail to B-29, but it can be reached from Carrot Lake by going east 1/4 mile after crossing Carrot Creek on the Atwood Lake trail. Total miles from the Uinta River trailhead is 17.5 miles. Camping sites and horse pasture are abundant around the lake; however, the pasture is quite boggy. A large brook trout population inhabits the lake. Camping and fishing pressure is light at B-29. Take plenty of insect repellent during July!"
    },
    {
        'designation': 'U-74',
        'name': 'BEARD',
        'text': "The high cirque lake sits way above timberline at the eastern base of South King Peak. It is 9 acres, 11,740 feet in elevation, with an estimated 15 feet maximum depth. Access is to follow the well marked Forest Service trail 22 miles through Atwood Basin to Trail Rider Pass. Follow the trail an additional 1/8 mile into Painter Basin, then turn southwest and go 150 yards into a small cirque basin to the lake. Horse access is fairly rugged over the rocky terrain (especially up Trail Rider Pass). There are no horse pastures or camping areas in the windswept tundra around the lake. Stocked brook trout grow well in Beard and fishing pressure is quite light."
    },
    {
        'designation': 'U-96',
        'name': 'BOLLIE',
        'text': "This natural lake is surrounded by beautiful meadows and open timber. It is 10 acres, 10,660 feet in elevation, with 15 feet maximum depth. Trail access is via a primitive logging road 3 miles north past Jefferson Park to the canyon rim. Follow the trail west for 2 miles along the rim until you reach the lake near the head of the basin. Excellent campsites and abundant horse feed are available around the lake. This lake contains cutthroat trout. Fishing pressure and camping use are light. (Refer to the Dry Gulch drainage map for a better illustration of the access route.)"
    },
    {
        'designation': 'U-32',
        'name': 'BOWDEN',
        'text': "Bowden is a shallow, natural lake located 1/2 mile southeast of the Kidney Lakes. It is 4.5 acres, 10,693 feet in elevation, with 14 feet maximum depth. Total distance from the U-Bar Ranch is 18.5 miles, the last half mile is trailless. Horse access is good, and numerous campsites and pasture are available around the lake. Bowden Lake contains stocked brook trout. Camping and fishing pressure is rated moderate. Bowden Lake has excellent food production and may occasionally winterkill, so fishing is generally not fast."
    },
    {
        'designation': 'U-54',
        'name': 'BROOK',
        'text': "This natural lake can be reached by following the trail east 1 mile along the north shore of Fox Lake. It is 10 acres, 10,950 feet in elevation, with 8 feet maximum depth. It can also be reached by following the Highline Trail west from Whiterocks drainage over North Pole Pass (first lake encountered). Some horse feed and campsites are available around the lake. Brook trout are stocked in Brook Lake and fishing pressure is rated light."
    },
    {
        'designation': 'U-17',
        'name': 'CARROT',
        'text': "This beautiful glacial lake sits along the rim of Atwood Basin and is located 1/2 mile southwest of the big meadow where the trail crosses Atwood Creek. It is 31 acres, 10,830 feet in elevation, with 31 feet maximum depth. Total distance from the U-Bar Ranch is 17.5 miles over a good trail. Good pasture and campsites are located on the north side of the lake. Fishing is generally good for stocked brook trout. Fishing pressure is rated light."
    },
    {
        'designation': 'U-3',
        'name': 'CHAIN 1 (LOWER)',
        'text': "Chain 1 is a fluctuating reservoir and is the lowest of the Chain lake series. Full pool is 62 acres, 10,580 feet in elevation, with 38 feet maximum depth. Access is 11.5 miles via a well-marked Forest Service trail from the U-Bar Ranch trailhead. Some camping sites are available around the lake. Limited horse pasture can be found on the east shore, and 1/4 mile southeast of the dam. Chain 1 contains a large population of pan-sized brook trout produced through natural reproduction. Fishing pressure is heavy during early summer but decreases later in the season as water drawdown occurs."
    },
    {
        'designation': 'U-2',
        'name': 'CHAIN 2 (MIDDLE)',
        'text': "Chain 2 is second lake in the Chain Lake series. It is 14.4 acres, 10,605 feet in elevation, with 13 feet maximum depth. It used to be a storage reservoir but the earthen dam has washed out. It sits 1/2 trail mile above Chain 1 and less than 100 yards below the Chain 3 dam. Total distance from U-Bar Ranch is 12 miles along a well-marked trail. Horse pasture is fairly good but limited, and there are a few camping sites. The abundant brook trout population in Chain 2 is self sustaining. Angling and camping pressure is moderate."
    },
    {
        'designation': 'U-1',
        'name': 'CHAIN 3 (UPPER)',
        'text': "This reservoir is the third lake in the Chain Lake series. It is 51 acres at full pool, 10,623 feet in elevation, with 44 feet maximum depth. Total distance is 12.5 miles from the U-Bar Ranch via a well-marked trail. Horse pasture and campsites are limited around the somewhat rocky shoreline. Pan-sized brook trout are very abundant in Chain 3 and are sustained through natural reproduction. Angling and camping pressure are moderate. Fishing is usually fast on flies and spinners."
    },
    {
        'designation': 'U-4',
        'name': 'CHAIN 4',
        'text': "Chain 4 is a natural lake that sits along the trail on a plateau located above Chain 3 Lake and below Roberts Pass. It is 13.5 acres, 10,870 feet in elevation, with 31 feet maximum depth. Total distance is 13.5 miles into Krebs Basin along a well-marked trail from U-Bar Ranch. Horse access is quite good though steep the last 1/2 mile. No horse pasture and very few campsites exist around the lake. This lake is managed with cutthroat trout. Fishing and camping pressure are light. Fishing generally improves in late summer."
    },
    {
        'designation': 'U-85',
        'name': 'CRAIG',
        'text': "This natural lake is the first large lake (and lower in elevation!) encountered in the Painter Lakes Basin. It is 9.3 acres, 10,848 feet in elevation, and about 14 feet maximum depth. Leave U-Bar Ranch and proceed via a well-marked trail 14 miles to North Fork Park (where the North and Center Forks of the Uinta River converge). Head due south for 2 very steep and rough miles up a vague trail (along a small creek) into the Painter Lakes Basin. There are good horse pastures and camping sites around the lake. Craig contains mostly cutthroat trout along with an occasional brook trout. Fishing and camping pressure are light."
    },
    {
        'designation': 'U-48',
        'name': 'CRESCENT',
        'text': "This long narrow reservoir fluctuates 4 feet annually. It is 31 acres, 10,830 feet in elevation, with 23 feet maximum depth. Access is very good via two well marked forest service trails: the shortest is about 8 miles over the Fox-Crescent Pass from the West Fork Whiterocks River trailhead, and the other is about 15.5 miles up the Shale Dugway from the U-Bar Ranch. Camping sites are available around the lake and good horse pasture can be found 1/2 mile north (Fox Lake) or west (large meadow) from Crescent. The Crescent Lake fishery is mainly cutthroat trout along with a few brook trout. Camping and fishing pressure is moderate to heavy, and the area is quite popular with large scout groups during mid summer."
    },
    {
        'designation': 'U-46',
        'name': 'DAVIS, NORTH',
        'text': "This natural lake sits about 250 yards due north of South Davis Lake, or about 1-1/4 miles north of the Kidney lakes. It is 7.3 acres, 11,060 feet in elevation, with 7 feet maximum depth. Good camping sites and abundant horse pasture are found to the south between South Davis and the Kidney lakes. North Davis contains small pan-sized brook trout that are hard to catch. These fish are stocked and can freely move between both Davis lakes. Fishing pressure is light, but camping pressure is moderate in the vicinity."
    },
    {
        'designation': 'U-34',
        'name': 'DAVIS, SOUTH',
        'text': "This shallow lake sits in a large, wet meadow 1 mile north of the Kidney lakes. It is 6.1 acres, 11,020 feet in elevation, with 4 feet maximum depth. Camping sites and horse feed are plentiful south of the lake. Pan-sized brook trout inhabit the lake. Camping pressure is moderate, but angling pressure is light. This lake is good for fly-fishing."
    },
    {
        'designation': 'U-59',
        'name': 'DIVIDE',
        'text': "This natural lake sits in windswept tundra below the mountain pass separating Uinta River drainage (south slope) from Burnt Fork drainage (north slope). It is 18.9 acres, 11,217 feet in elevation, with an estimated 39 feet maximum depth. Access is 2 miles north from Fox Lake via the trail which goes over the pass to Island Lake. No camping sites or horse feed are available around the lake or the vicinity. Divide Lake has been managed with cutthroat trout. Angling pressure is considered light and limited to day use."
    },
    {
        'designation': 'U-49',
        'name': 'DOLLAR',
        'text': "This pretty lake is located in a large meadow, and is occasionally called Al Dime Lake. It is 11.5 acres, 10,704 feet in elevation, with 6 feet maximum depth. Trail access is very good and the lake is located about 1 mile northwest of Fox Lake. Total distance from U-Bar Ranch is 15 miles. Excellent horse feed and camping sites are in the Dollar Lake vicinity. A natural population of pan-sized brook trout inhabits the lake. Camping and fishing pressure are generally rated moderate, though heavy use occasionally occurs from large groups. Brookies spook easily in the meadow stream below Dollar, and are quite a challenge for the fly fisherman."
    },
    {
        'designation': 'U-47',
        'name': 'FOX',
        'text': "This reservoired lake is popular despite 20-foot fluctuations annually. It is 102 surface acres at full pool, 10,790 feet in elevation, with 47 feet maximum depth. Trails are well marked; and distance is either 15 miles from the U-Bar Ranch to the south, or 8.5 miles from the West Fork Whiterocks River trailhead to the east. Horse feed and heavily used camping areas are located in the general area around the lake. Brook and cutthroat trout inhabit Fox. Recreational use is generally moderate, however, large groups frequently visit this lake, and the area has been abused."
    },
    {
        'designation': 'U-21',
        'name': 'GEORGE BEARD',
        'text': "This natural lake sits in open, windswept tundra. It is 7.4 acres, 11,420 feet in elevation, with 15 feet maximum depth. Access is 2 miles via a rocky trail from Atwood Lake and is located just below Trail Rider Pass. No camping areas or horse pasture exist around the lake. Brook trout have reproduced naturally at George Beard and can be quite abundant. Fishing pressure is limited to day-users and considered light."
    },
    {
        'designation': 'U-82',
        'name': 'GILBERT',
        'text': "This natural lake sits at the head of Gilbert Creek, a tributary to the Center Fork of the Uinta River. It is 14.6 acres, 11,459 feet in elevation, with 20 feet maximum depth. Good trail access exists heading northwest from North Fork Park for 6.5 miles. Total trail distance from U-Bar Ranch is 20.5 miles. Good camping and horse pasture exists 3 miles southeast of the lake. The lake is currently stocked with brook trout. Fishing pressure is light. Sheep grazing during late summer detracts from the aesthetic beauty of this meadowy alpine basin."
    },
    {
        'designation': 'U-25',
        'name': 'KIDNEY, EAST',
        'text': "This natural lake is located about 15 miles from the West Fork Whiterocks River trailhead, or just under 18 miles from U-Bar Ranch; both access trails are well marked. It is 13.7 acres, 10,850 feet in elevation, with 12 feet maximum depth. Horse pasture is abundant north of the lake. Camping areas are abundant, but overused in the area between the Kidney lakes. The lake contains brook trout. Both camping and angling pressure are quite heavy from large recreational groups."
    },
    {
        'designation': 'U-26',
        'name': 'KIDNEY, WEST',
        'text': "This natural lake is located 100 yards due west of Kidney, East. It is 20 acres, 10,850 feet in elevation, with 4 feet maximum depth. Trail access is quite good, and distance is 18 miles from the U-Bar Ranch or 15 miles from the West Fork Whiterocks River trailhead. Horse pasture is available north of the lake. Camping sites are found around the lake, but most are overused. The lake contains brook trout. Both camping and angling pressure are quite heavy from large recreational groups."
    },
    {
        'designation': 'U-23',
        'name': 'LILY',
        'text': "This pretty little lake is surrounded by yellow water lilies. It is 5.3 acres, 10,919 feet in elevation, with 15 feet maximum depth. Lily is located about 1/2 mile northeast of the Kidney lakes. There is no trail, but horse access is fairly easy over this somewhat open terrain. Campsites and horse pasture are available west of the lake. Brook trout are stocked into the lake. Angling pressure is generally light considering its close proximity to the Kidney lakes."
    },
    {
        'designation': 'U-8',
        'name': 'LILY PAD',
        'text': "Lily Pad is the first lake encountered on the Chain lakes trail approximately 8 miles from U-Bar Ranch. It is 3.7 acres, 10,818 feet in elevation, with 7 feet maximum depth. It sits in a small stream-fed valley 1/4 mile off the trail, located 1 mile east of Chain 1 and about 1/3 mile north of the Krebs Creek trail crossing. (A trail sign marking this lake may or may not be tacked to a pine tree near the trail turnoff.) Horse pasture is limited and a few camping sites are on the south shore. This lake contains abundant populations of brook and rainbow trout sustained through natural reproduction. Fishing pressure is moderate."
    },
    {
        'designation': 'U-73',
        'name': 'MILK',
        'text': "This isolated lake is located in a cirque basin on the talus ridge bordering the north part of Painter Basin. It is 13.1 acres, 11,236 feet in elevation, with 35 feet maximum depth. Milk is about 5 trail miles west of North Fork Park, or 7 trail miles northeast of Trail Rider Pass. The last mile is extremely rocky and trailless, and very difficult for horses. There are no campsites or horse pasture around the lake. Pan-sized brook and cutthroat trout are quite numerous. Fishing pressure is very light."
    },
    {
        'designation': 'U-13',
        'name': 'MT. EMMONS',
        'text': "This pretty lake is located 1/4 mile south of Allred Lake (Atwood Basin) through rocky timbered terrain. It is 15.5 acres, 10,990 feet in elevation, with 21 feet maximum depth. Total distance is about 18.5 miles from the U-Bar Ranch. Some pasture and limited camping areas are available along the fringes of the wet meadow east of the lake. Brook trout are common in the lake. This lake has had golden trout in the past but it is doubtful if any remain. Angling and camping pressure are light."
    },
    {
        'designation': 'U-5',
        'name': 'OKE DOKE',
        'text': "This pretty cirque lake is located at the eastern base of Mt. Emmons 1 mile due west of Roberts Pass. It has no inlet or outlet stream, and is 12.9 acres, 11,320 feet in elevation, with 38 feet maximum depth. Total distance by trail is 15 miles from U-Bar Ranch. Limited horse feed and marginal camping areas are located south of Roberts Pass. Cutthroat trout are stocked into Oke Doke. Fishing pressure is light. Oke Doke is ideal for a small group of one to three backpackers who want to get off the beaten trail."
    },
    {
        'designation': 'U-98',
        'name': 'PENNY NICKELL',
        'text': "This pretty cirque lake sits next to a steep talus slope 3.5 miles due south of Fox Lake. It is 11.5 acres, 10,710 feet in elevation, with 43 feet maximum depth. There is no trail to the lake and its best to use a U.S.G.S. map for directions. Various camping areas and horse feed exists in wet meadows between Fox and Penny Nickell lakes. The lake is stocked with cutthroat. Angling and camping pressure are light."
    },
    {
        'designation': 'U-9',
        'name': 'PIPPEN',
        'text': "This meadow lake has a small island near the south shore. It is 3.2 acres, 10,450 feet in elevation, with 3 feet maximum depth. Go west about 1 mile through the large meadow located 1/2 mile southwest of Chain 1. Total distance from U-Bar Ranch is 10 miles. Excellent horse pasture and camping sites exist around the lake. A natural population of brook trout inhabit the lake. Angling pressure is moderate, and Pippen is considered a good fly-fishing lake. This lake has been used as a base camp by commercial packers."
    },
    {
        'designation': 'U-33',
        'name': 'RAINBOW',
        'text': "This natural lake is located in a windswept tundra 1-1/4 miles northwest of the Kidney lakes along a well-marked trail. It is 35.1 acres, 11,130 feet in elevation, with 20 feet maximum depth. No campsites or horse pasture exist around this lake but they are available 1 mile to the east. Brook trout spawn naturally in the lake and it may contain a few rainbows and cutthroat trout. Fishing pressure is usually moderate, but heavy pressure does occasionally occur from large pack groups staying at the Kidney lakes."
    },
    {
        'designation': 'U-15',
        'name': 'ROBERTS',
        'text': "This deep natural lake is located in a high cirque basin 1 mile southwest of Atwood Lake. It is 23.3 acres, 11,550 feet in elevation, with 38 feet maximum depth. Follow a faint trail 1.5 miles west of Mt. Emmons Lake through a wet meadow, and zigzag a steep ravine to Roberts Lake. No camping or horse feed is available in this windswept tundra area. The lake contains mainly cutthroat trout along with a few brook trout. Angling pressure is light and fishing success is quite variable."
    },
    {
        'designation': 'U-27',
        'name': 'SAMUALS',
        'text': "This nice lake sits 1 mile north of the upper trail between Fox and Kidney lakes at the head of Samuals Creek. It is 4.8 acres, 10,995 feet in elevation, with 7 feet maximum depth. Horse pasture and camping areas are quite abundant around the lake and to the south. The lake contains an abundant population of brook trout. Angling pressure is light. Try this commonly 'passed up' lake and avoid the people usually present at the Kidney and Fox lakes."
    },
    {
        'designation': 'U-19',
        'name': None,
        'text': "This natural lake is located near the head of Atwood Basin in windswept tundra. It is 15 acres, 11,420 feet in elevation, with 8 feet maximum depth. It sits 1/2 mile south of George Beard Lake past U-22 Lake, or 2 miles due west of the Atwood Lake Dam. Horse pasture and camping are available 2 miles east at Atwood and Allred lakes. Horses should not be grazed in this fragile tundra. The lake contains a fine population of brook trout. Fishing pressure is light."
    },
    {
        'designation': 'U-35',
        'name': None,
        'text': "This natural lake sits in windswept tundra, and is located just over 100 yards northeast of Rainbow Lake; in fact, the outlet stream from Rainbow Lake flows into U-35. It is 4.4 acres, 11,110 feet in elevation, with 5 feet maximum depth. No horse pasture or camping are around the lake. This small lake holds only a few stocked cutthroat and brook trout. Fishing pressure is moderate from people camped near Kidney lakes."
    },
    {
        'designation': 'U-36',
        'name': None,
        'text': "This lake sits in windswept tundra about 100 yards southeast of U-35 and receives its outlet stream; or is located under 1 mile northwest of the Kidney lakes. It is 4.6 acres, 11,100 feet in elevation, with 7 feet maximum depth. The lake contains a natural brook trout population. Angling pressure is moderate, and there are no horse pasture or campsites in the immediate area."
    },
    {
        'designation': 'U-37',
        'name': None,
        'text': "This windswept tundra lake is located 1/2 mile northeast of Rainbow Lake and 1/2 mile southeast of U-38 in the basin above the Kidney lakes. It is 6.3 acres, 11,180 feet in elevation, with 12 feet maximum depth. There are no camping sites or pasture; these are available southeast 1-1/4 miles at the Kidney lakes. The lake is stocked with brook trout. Fishing pressure is light."
    },
    {
        'designation': 'U-38',
        'name': None,
        'text': "This windswept tundra lake sits 1/2 mile due north of Rainbow Lake past U-39 Lake. It is 15.7 acres, 11,218 feet in elevation, with 13 feet maximum depth. An intermittent inlet stream comes from U-42 Lake while the outlet stream flows into U-40 Lake. A little horse pasture is available northeast of the lake around U-40, but there are no camping sites. Cutthroat trout inhabit the lake. Fishing pressure varies from light to moderate."
    },
    {
        'designation': 'U-39',
        'name': None,
        'text': "This shallow lake sits in the tundra 1/4 mile due north of Rainbow Lake; in fact, the outlet stream flows into Rainbow Lake. It is 5.3 acres, 11,160 feet in elevation, with 9 feet maximum depth. No horse pasture or camping areas exist around the lake. This lake was experimentally stocked with brook trout but they did not survive. This lake is no longer managed to provide any recreational fishing. Fishing pressure is light."
    },
    {
        'designation': 'U-42',
        'name': None,
        'text': "This natural lake has some water level fluctuation and sits in windswept tundra. It is 7.6 acres, 11,350 feet in elevation, with 7 feet maximum depth. U-42 is located about 1 mile northwest of Rainbow Lake and 1/2 mile west of U-38. Camping and horse pasture are not available. The lake was experimentally stocked with cutthroat trout and only has marginal habitat. Fishing pressure is light."
    },
    {
        'designation': 'U-45',
        'name': None,
        'text': "This shallow lake is quite long and narrow, and sits next to the talus slope at the head of the basin 2.5 miles northwest of Kidney lakes. It is 5 acres, 11,425 feet in elevation, with 5 feet maximum depth. There are no horse pastures or camping sites near the lake. A few cutthroat inhabit the lake and fishing is slow. Fishing pressure is light."
    },
    {
        'designation': 'U-50',
        'name': None,
        'text': "This pretty lake is quite shallow for its size. It is 18 acres, 10,832 feet in elevation, with 8 feet maximum depth. It is located 1/4 mile northwest of Dollar Lake and horse access is easy. Camping and horse pasture are available in the vicinity. The lake is stocked with brook trout. Angling pressure is light."
    },
    {
        'designation': 'U-75',
        'name': None,
        'text': "This natural lake sits in open tundra in the extreme western end of Painter Basin. It is 6.9 acres, 11,390 feet in elevation, with 18 feet maximum depth. The lake is located about 1 trail mile northwest of Trail Rider Pass. It contains a fairly abundant population of pan-sized brook trout. No camping areas or horse feed exist around the lake; in fact, the area is usually windy and cold all season and the lake receives few anglers."
    },
    {
        'designation': 'U-76',
        'name': None,
        'text': "This cirque lake is located at the southwest base of Kings Peak in Upper Painter Basin in cold, windswept tundra. It is 6 acres, 11,475 feet in elevation, with 15 feet maximum depth. Access is about 2 miles northwest of Trail Rider Pass over open rocky terrain. The lake contains pan-sized brook and cutthroat trout. Angling pressure is very light at this remote lake, and a visit will provide a true wilderness experience."
    },
    {
        'designation': 'U-88',
        'name': None,
        'text': "This pretty, natural lake is the largest in the Painter Lakes Basin. (See access to Craig Lake.) It is 14 acres, 11,030 feet in elevation, with 18 feet maximum depth. U-88 sits 1 mile due west of Craig Lake over gentle, timbered terrain. Excellent camping areas and limited horse pasture are on the southwest shore. The lake contains a natural population of nice brook trout. Angling pressure is light."
    },
    {
        'designation': 'U-89',
        'name': None,
        'text': "The water level in this pretty lake fluctuates annually. It is 11.5 acres, 11,037 feet in elevation, with 15 feet maximum depth. (See access to Craig Lake.) This lake sits about 1 mile due west of Craig Lake and is 100 yards southwest of U-88. Excellent camping and limited horse pasture are around the lake. It contains a few brook trout. Angling pressure is light."
    },
    {
        'designation': 'U-93',
        'name': None,
        'text': "This natural lake is the highest and most westerly in the Painter Lakes Basin. It is 11.1 acres, 11,402 feet in elevation, with 8 feet maximum depth. (See access to Craig Lake.) U-93 sits 1.5 miles west of Craig Lake over somewhat steep but rolling terrain. The lake is stocked with cutthroat trout. No horse pasture or camping areas exist around the lake. Angling pressure is very low. This is one of the most remote lakes in the Uinta River drainage."
    },
    {
        'designation': 'U-41',
        'name': 'VERLIE',
        'text': "This natural lake sits due west of the Kidney lakes about 1 mile. It is 10.6 acres, 10,906 feet in elevation, with 12 feet maximum depth. The last several hundred yards are inaccessible to horses. Camping sites are marginal and quite limited. A natural population of brook trout inhabits the lake, along with an occasional cutthroat trout. Angling pressure is rated moderate."
    },
    {
        'designation': 'G-77',
        'name': 'DEAD HORSE',
        'text': "Dead Horse is a natural emerald green lake situated at the foot of Dead Horse Pass in rocky timberline terrain. It is 16.0 acres, 10,878 feet in elevation, with 41 feet maximum depth. Access is 7.5 miles south of the West Fork-Blacks Fork Trailhead on the West Fork Trail to the head of the basin. Campsites are available in the lake vicinity. Horse feed is present in large meadows to the northeast. Spring water is unavailable. The recreational appeal of the Dead Horse Basin is somewhat diminished by sheep grazing in the area. Dead Horse Lake is stocked with cutthroat trout and experiences moderate levels of angling pressure. Remember to pack out your refuse."
    },
    
    # BEAR RIVER AND BLACKS FORK DRAINAGE - dwr-bear-blacks-fork-trimmed.pdf
    {
        'designation': 'BR-42',
        'name': 'ALLSOP',
        'text': "Allsop is a beautiful natural lake situated in a small cirque basin at the head of the Left Hand Fork of the East Fork Drainage. It is 12.3 acres, 10,580 feet in elevation, with 22 feet maximum depth. The lake is in an alpine meadow with open shorelines and timbered slopes to the east and west. Access is 8¾ miles southeast of the East Fork-Bear River Trailhead on the East Fork and Left Hand Fork pack trails. Campsites are available with several excellent sources of spring water. Pasture is present in the lake vicinity and adjacent to the outlet stream for some distance below the lake. Allsop contains a population of cutthroat trout sustained by natural reproduction. Allsop is subject to moderate levels of angling pressure."
    },
    {
        'designation': 'BR-28',
        'name': 'AMETHYST',
        'text': "Amethyst is a striking natural lake situated within the timberline transition zone in a rugged cirque basin at the head of the Ostler Fork Drainage. It is 42.5 acres, 10,750 feet in elevation, with 59 feet maximum depth. The lake is emerald green in appearance due to a glacial turbidity. Access is 6¼ miles southeast of the Christmas Meadows Trailhead on the Stillwater and Amethyst Lake pack trails. The lake is situated at the head of the basin, 1 mile beyond the lower meadows. Campsites adjacent to the lake are poor and horse feed is restricted due to the windswept and rocky nature of the surrounding timberline terrain. Better sites are available in the vicinity of the lower meadows. Amethyst provides some fast fishing for pan-sized brook and cutthroat trout. Angling pressure has established at moderate levels."
    },
    {
        'designation': 'BR-45',
        'name': 'BAKER',
        'text': "This meadow lake is situated at the base of gently sloping timbered terrain in the Boundary Creek Drainage. It is 3.6 acres, 10,420 feet in elevation, with 8 feet maximum depth. The meadow surrounding Baker is large and quite boggy. Access is 4¼ miles southeast of the Bear River Boy Scout Camp on the unmarked Boundary Creek Trail past the old burn to the head of the drainage. The last ¾ mile of trail immediately below the lake is indistinct and difficult to locate. Good campsites are available with plentiful horse feed. A good spring water source is located ¼ mile downstream from the lake. Baker contains population of wary brook trout. Shorelines are open enough to permit fly casting."
    },
    {
        'designation': 'BR-10',
        'name': 'BEAVER',
        'text': "Beaver is a scenic meadow lake located in open terrain characterized by grassy slopes and scattered groves of conifers in the West Fork Drainage. The lake is 13.2 acres, 9,420 feet in elevation, with 32 feet maximum depth. Beaver is easily accessible on the Moffit Pass Road 1¾ miles southwest of the Whitney Reservoir dam. The total distance from U-150 in the Hayden Fork Drainage is about 9 miles. Excellent sites are available for camping activity, but spring water and fuelwood are scarce. Large shallow shelves and dense growths of aquatic vegetation around the lake perimeter make shore fishing very difficult. Anglers are encouraged to bring boats or rubber rafts. Beaver Lake is productive in nature and subject to frequent winterkill. As a result, the Forest Service has installed a water circulator on the surface of this lake in an attempt to improve winter survival. Beaver is currently stocked on an annual basis with catchable-sized rainbow trout and may contain brook and cutthroat trout."
    },
    {
        'designation': 'BR-1',
        'name': 'BOURBON (GOLD HILL)',
        'text': "Bourbon is a small crescent-shaped lake in timbered country at the foot of a steep, jagged peak and associated talus rock. It is 1.9 acres, 9,820 feet in elevation, with 8 feet maximum depth. Campsites are poor in the lake vicinity, but a spring water source is available. Bourbon is located 1 steep mile west of Highway U-150 on the Whiskey Creek Trail which begins across the highway from the Sulpher Campground. Access is also afforded by the Whiskey Creek Road which begins across the highway from and slightly north of the Kletting Peak Information Turnoff. Follow this road north and west for 2¼ miles to the end and then continue northwest on foot for ¼ mile to the lake. Bourbon, containing a population of brook trout, is a popular fishing spot."
    },
    {
        'designation': 'BR-2',
        'name': None,
        'text': "This productive meadow pond is located some 100 yards downstream from Bourbon Lake in the Hayden Fork of the Bear River Drainage. It is 0.7 acres, 9,780 feet in elevation, with 5 feet maximum depth. Small and quite shallow, BR-2 would not appear to provide suitable fish habitat. However, the lake contains a population of brook trout sustained by natural reproduction and downstream migration from Bourbon Lake. Camping opportunities are available with a limited supply of horse feed. Spring water is available at Bourbon. Fishing pressure is light despite the easy access afforded by the Whiskey Creek timber road."
    },
    {
        'designation': 'BR-4',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-5',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-6',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-16',
        'name': None,
        'text': "BR-16 is a small, narrow pond situated at the foot of a rocky ridge on the stream immediately below Ryder in the Stillwater Fork Drainage. It is 1.0 acre, 10,610 feet in elevation, with 5 feet maximum depth. Suitable camping areas are available in the lake vicinity with horse pasture in large parks to the east. Spring water can be obtained at the nearby Ryder Lake. BR-16 contains a population of brook and cutthroat trout maintained by natural reproduction and recruitment from Ryder. Fishing pressure is regarded as moderate to light."
    },
    {
        'designation': 'BR-17',
        'name': None,
        'text': "BR-17 is a small spring-fed lake located in sparsely timbered terrain in the Middle Basin of the Stillwater Fork Drainage. It is 2.8 acres, 10,630 feet in elevation, with 7 feet maximum depth. BR-17 is situated immediately south of Ryder Lake. Several good potential campsites are available with very little horse feed. Spring water can be obtained from any one of several sources feeding the lake. BR-17 contains a population of pan-sized brook trout sustained by natural reproduction. A major portion of the shoreline at this timberline lake is open enough to permit fly casting. Angling pressure is moderate to light."
    },
    {
        'designation': 'BR-18',
        'name': None,
        'text': "This spring-fed glacial lake is located in timberline terrain 200 yards southeast of Ryder Lake or immediately downstream from BR-17 in the Stillwater Fork Drainage. The lake is 4.8 acres, 10,610 feet in elevation, with 12 feet maximum depth. Good campsites are available with abundant spring water in the lake vicinity. Limited horse feed can be located in the general area. BR-18 contains a good population of brook trout and provides some fair fishing on occasion. Recreational use is generally light."
    },
    {
        'designation': 'BR-21',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-22',
        'name': None,
        'text': "BR-22 is not capable of sustaining a fishery. It is included on the map as a landmark."
    },
    {
        'designation': 'BR-23',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-24',
        'name': None,
        'text': "This small cirque lake abuts a rocky ledge and talus slope in Amethyst Basin. BR-24 is 2.4 acres, 10,460 feet in elevation, with 10 feet maximum depth. The lake is emerald green in color due to a glacial turbidity, and is quite shallow in overall depth. BR-24 is located within sight of the Amethyst Lake Trail 5¾ miles southeast of the Christmas Meadows Trailhead just beyond the lower meadows. Excellent campsites are available in the lake vicinity with ample horse feed in the lower meadows. Spring water is available from several inlet sources. BR-24 provides spotty fishing for cutthroat trout."
    },
    {
        'designation': 'BR-30',
        'name': None,
        'text': "BR-30 is a natural meadow lake abutting a talus slope at the head of the Hell Hole Basin. It is 1.2 acres, 10,580 feet in elevation with 6 feet maximum depth. The lake is brown in color with a glacial turbidity of pulverized rock. Access is ¼ mile southwest of Hell Hole Lake overland through wet meadows and timber following the major drainage system. Potential campsites are available with spring water early in the season. Horse feed is present to the east in a large, wet meadow. Stocking has been discontinued at BR-30 due to winterkill problems."
    },
    {
        'designation': 'BR-33',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-34',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-35',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-41',
        'name': None,
        'text': "BR-41 is an unproductive natural lake situated at the base of a steep talus ridge at the head of the Mill Creek Drainage. The lake is 3.4 acres maximum, 10,412 feet in elevation, with 19 feet maximum depth. Snowslides are common in the lake vicinity as indicated by the presence of stunted conifers and avalanche litter along the southern lake margin. Marginal campsites are present. Better opportunities are available lower in the drainage. Spring water sources are not available in the immediate lake vicinity. BR-41 is located 6 miles south of the Mill Creek Guard Station on the unimproved Mill Creek Road which degrades to a jeep trail for the last several miles. The lake is also accessible from the East Fork of the Bear River Trailhead east on the Bear River-Smiths Fork Trail over the top of Deadman Pass. BR-41 experiences extreme water level fluctuation and does not contain suitable habitat to sustain a fishery. The lake is not presently stocked."
    },
    {
        'designation': 'BR-43',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-44',
        'name': None,
        'text': "BR-44 is a natural glacial lake located in rugged timberline terrain in the Right Hand Fork of the East Fork Drainage. It is 3.6 acres, 10,900 feet in elevation, with 15 feet maximum depth. The lake abuts a steep talus ridge to the west and the remainder of the shoreline is composed of rocky slopes and sparse timber. BR-44 lies in an isolated basin and access is difficult. From the East Fork Trailhead, follow the East Fork Bear River Pack Trail southeast for 5¼ miles to a large trailside spring in the Right Hand Fork. Then proceed directly west for 1¾ miles up the steep hillside following the drainage system to the head of the basin. Potential campsites are available without horse feed or spring water sources. BR-44 is not easily accessible on horseback. This lake has been scheduled for experimental cutthroat trout stocking during 1983."
    },
    {
        'designation': 'BR-49',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-51',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-52',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-53',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-37',
        'name': 'CUTTHROAT',
        'text': "Cutthroat is a natural lake located near timberline in a rugged cirque basin at the head of the Hayden Fork Drainage. It is 5.8 acres, 10,390 feet in elevation, with 16 feet maximum depth. There is no direct trail to Cutthroat Lake. Access is 1 rough mile west of Ruth Lake through thick timber and boulder fields. Horse access is possible but difficult. Campsites in the immediate lake vicinity are limited and poor due to the open and windswept nature of the surrounding terrain, but good sites are available to the east in the vicinity of a wet meadow. Spring water can be obtained at the lake through at least mid-August. Cutthroat contains a wary population of brook trout and a few remaining cutthroat trout. Fisherman use is moderate."
    },
    {
        'designation': 'BR-36',
        'name': 'HAYDEN',
        'text': "Hayden is an irregular natural water located in rocky terrain ¾ mile due west of Ruth Lake in the Hayden Fork Drainage. There is no direct access trail, but the lake is readily accessible. It is 4.4 acres, 10,420 feet in elevation, with 5 feet maximum depth. The lake abuts a talus slope to the west and scattered conifers encompass the remainder of the shoreline. Campsites are available at Hayden with a good source of spring water. The lake contains a small population of cutthroat trout and sustains moderate levels of angling pressure."
    },
    {
        'designation': 'BR-29',
        'name': 'HELL HOLE',
        'text': "Hell Hole is a shallow lake with partly open shorelines situated centrally in the Hell Hole Basin near the head of the Main Fork Drainage. The lake is 8.5 acres, 10,340 feet in elevation with 9 feet maximum depth. The surrounding terrain is scenic and composed of large, boggy meadows and thick patches of timber. Access is 5 miles southeast of Highway U-150 on the Main Fork Stillwater Trail which begins as an unmarked jeep road across the highway from the Gold Hill turnoff. This trail, not well maintained, is difficult to follow at times. Campsites are excellent at Hell Hole with plenty of horse feed and running water. Several small springs are present as well. Hell Hole contains a good population of pan-sized cutthroat trout often overlooked by anglers. Fishermen are encouraged to bring plenty of mosquito repellent on trips to this basin."
    },
    {
        'designation': 'BR-38',
        'name': 'JEWELL',
        'text': "This natural glacial lake is situated in partially open, timbered country at the foot of a talus rockslide. Jewell is 2.4 acres, 10,300 feet in elevation, with 13 feet maximum depth. The lake is located ¾ mile northwest of Ruth Lake over rough terrain with no direct access trail. Several camping areas are available in the lake vicinity, and horse feed can be located to the southwest in a large, wet meadow. Spring water is not present. Jewell Lake is stocked with cutthroat trout and sustains moderate levels of fishing pressure. Jewell is a popular water for single day fisherman use."
    },
    {
        'designation': 'BR-20',
        'name': 'KERMSUH',
        'text': "Kermsuh is a long, narrow lake situated in rocky timbered country in the isolated West Basin of the Stillwater Fork Drainage. It is 12.4 acres, 10,300 feet in elevation, with 14 feet maximum depth. Campsites are poor due to the rocky nature of the surrounding terrain, but running water is abundant. Horse feed can be located in a small meadow to the south. Access is 1¾ miles south of Christmas Meadows on the Stillwater Pack Trail to the junction with the Kermsuh Lake Trail and then 2¼ miles southwest up the steep grade into West Basin. The cutthroat trout population is sustained by natural reproduction. This lake provides a good opportunity for users seeking solitude."
    },
    {
        'designation': 'BR-11',
        'name': 'LILY',
        'text': "Lily is an extremely large beaver pond situated in partly open, timbered terrain east of U-150 in the East Fork Drainage. It is 12.6 acres, 8,890 feet in elevation, with 20 feet maximum depth. Access is 1 mile north of the Bear River Ranger Station on U-150 to a well marked turnoff and then some miles southeast on the unimproved Lily Lake-Boundary Creek Road to the lake. Primitive camping areas are available with no source of spring water. A forest fire occurred in the vicinity of Lily Lake during 1980 burning much of the timber to the east of the lake. Lily is stocked on an annual basis with catchable rainbow trout. However, this productive water may stagnate late in the summer and the best fishing usually occurs prior to July 20. Lily sustains moderate levels of fisherman utilization."
    },
    {
        'designation': 'BR-46',
        'name': 'LORENA',
        'text': "Lorena is an irregular water situated in a small glacial cirque at the head of an isolated basin in the East Fork Drainage. The lake is 12.0 acres, 10,580 feet in elevation, with 20 feet maximum depth. Access is 2 miles southeast of the East Fork-Bear River Trailhead on the East Fork Trail to the old tie-hack cabin sites. From this point proceed south for 1¼ miles up the steep and rocky ridge to the head of basin. Access can be difficult and should not be attempted on horseback. Campsites are poor due to the rocky nature of the surrounding terrain. Horse feed is unavailable in the basin. A spring water source can be located about ¼ mile downstream from the lake. Lorena is stocked with brook trout. This remote lake provides a good opportunity for anglers seeking solitude in the Bear River Basin."
    },
    {
        'designation': 'BR-7',
        'name': 'LYM',
        'text': "Lym is a natural moraine lake located in thick conifers at the base of Table Top Mountain in the Mill Creek Drainage. The lake is 6.4 acres, 10,115 feet in elevation, with 20 feet maximum depth. Lym is long and narrow in outline. Access is 4 miles south of the Mill Creek Guard Station on the unimproved Mill Creek Road and then 2 miles northeast on the rough Lym Lake jeep trail to the lake. Be sure to take the left hand turn at the old tie-hack cabin sites in the large meadow. Numerous campsites are available along the lake perimeter with several sources of spring water. Limited horse feed is present to the north in a small, wet meadow. The population of brook trout present in Lym Lake is maintained by natural reproduction. Remember to carry out all refuse."
    },
    {
        'designation': 'BR-14',
        'name': 'MCPHETERS',
        'text': "This picturesque natural lake is situated near timberline at the head of the Middle Basin of the Stillwater Fork Drainage. McPheters is 28.8 acres, 10,860 feet in elevation, with 45 feet maximum depth. The surrounding terrain is composed of extensive bedrock shelves, windswept alpine meadows, and talus slopes. The lake is irregular in outline with a narrow, shallow arm to the east. Access is ¼ mile northwest of Ryder Lake to the top of the rocky ridge. The total distance from the Christmas Meadows Trailhead is 9 miles. Campsites and horse feed are not immediately available due to the open nature of the terrain and absence of fuelwood. However, good sites are present nearby. Spring water is plentiful. McPheters Lake is stocked with cutthroat trout."
    },
    {
        'designation': 'BR-19',
        'name': 'MEADOW',
        'text': "Meadow Lake is a shallow natural lake located in rocky, timbered country directly east of and downstream from BR-18 in the Stillwater Fork Drainage. It is 2.9 acres, 10,470 feet in elevation, with 5 feet maximum depth. There are several deep water channels running through the middle of the lake. Good camping opportunities are available with excellent sources of spring water. Horse feed is located to the north. The best route of access is to head ¼ mile southeast of the Stillwater Pack Trail from the vicinity of the large meadows due east of Ryder. Meadow contains a population of brook trout sustained by natural reproduction. The lake experiences light angling pressure and provides a good opportunity for anglers who wish to get away from the crowds."
    },
    {
        'designation': 'BR-8',
        'name': 'MT. ELIZABETH',
        'text': "Mt. Elizabeth Lake is a productive natural water located at the foot of Elizabeth Mountain in the Mill Creek Drainage. It is 3.1 acres, 9,984 feet in elevation, with 15 feet maximum depth. The surrounding terrain is composed of scattered patches of conifers and open meadows. Campsites are available with early season spring water. Access is 11¼ miles east of U-150 on the North Slope Road to Elizabeth Pass and then 4¾ miles north and west on the Elizabeth Mountain Road to the point overlooking Elizabeth Lake. Secondary logging routes provide direct vehicular access to the lake for 4-wheel drive vehicles. (see Blacks Fork Drainage map). Elizabeth Lake is stocked with cutthroat trout and received moderate levels of fishing pressure."
    },
    {
        'designation': 'BR-39',
        'name': 'NAOMI',
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'BR-47',
        'name': 'NORICE',
        'text': "This shallow meadow lake is situated near the head of the Right Hand Fork some 8¼ miles southeast of the East Fork Trailhead on the East Fork Bear River Pack Trail. Norice is 4.8 acres, 10,470 feet in elevation, with only 3 feet maximum depth. The pack trail is excellent to the forks but deteriorates beyond this point due to bogs and dead fall timber. Camping areas are available at Norice with ample feed in surrounding meadows, although this area is quite boggy. Spring water is not immediately available. Norice contains a good cutthroat trout population sustained by natural reproduction. This lake provides some good fly fishing on occasion."
    },
    {
        'designation': 'BR-27',
        'name': 'OSTLER',
        'text': "Ostler is an irregularly shaped natural lake located in a small glacial pocket in rocky timberline terrain at the western end of Amethyst Basin. The lake is 14.0 acres, 10,540 feet in elevation, with 14 feet maximum depth. Access is 5¼ miles southeast of the Christmas Meadows Trailhead on the Stillwater and Amethyst Lake pack trails to the lower meadows and then ¼ mile west up the steep hillside to Ostler. Some campsites with limited horse feed are available at the southwestern end of the lake. However, better sites are available in the vicinity of the lower meadows. Spring water is present at the lake through July. Ostler contains a population of brook and cutthroat trout and is a popular Boy Scout lake."
    },
    {
        'designation': 'BR-48',
        'name': 'PRIORD',
        'text': "Priord is an emerald green lake situated in a rugged cirque basin at the head of the East Fork Drainage. It is 12.0 acres, 10,860 feet in elevation, with 20 feet maximum depth. Access is 9 miles east and south of the East Fork-Bear River Trailhead on the East Fork Trail, 1 short mile beyond Norice Lake. This trail is well-traveled in the lower reaches of the drainage, but becomes difficult to locate in the vicinity of Norice. The aforementioned East Fork Trailhead is located ½ mile beyond the turnoff to the Boy Scout Camp on an improved Forest Service road. Campsites are available at Priord with good spring water sources and limited horse feed. The lake is situated in timberline terrain. Fuelwood is scarce. Priord is stocked with cutthroat trout and sustains moderate to light angling pressure."
    },
    {
        'designation': 'BR-40',
        'name': 'RUTH',
        'text': "Ruth is a popular alpine lake located ¾ mile west of U-150 on the Ruth Lake Trail from a well-marked highway turnoff and parking area. It is 9.7 acres, 10,340 feet in elevation, with 30 feet maximum depth. The surrounding terrain is composed of large areas of bedrock with sparse conifers and small meadows. There are several campsites available to the angler with some spring water. Horse feed is limited. Ruth experiences substantial fishing pressure from primarily day anglers. The lake is frequently stocked with brook trout."
    },
    {
        'designation': 'BR-15',
        'name': 'RYDER',
        'text': "This deep natural lake is situated in open timber with beautiful meadows and steep, rocky ledges. Ryder is 23.7 acres, 10,620 feet in elevation, with 55 feet maximum depth. Inlets cascade off cliffs to the west adding to the aesthetic qualities of this water. Access is 8¼ miles south of the Christmas Meadows Trailhead on the Stillwater Pack Trail. This trail becomes indistinct and difficult to locate in meadow areas immediately east of the lake, but the route is clearly marked with rock cairns. Campsites are present with spring water sources. Horse feed is available in limited supply, but is more abundant to the east adjacent to the access trail. Ryder contains a large population of brook trout and produces some fair fly fishing on occasion."
    },
    {
        'designation': 'BR-26',
        'name': 'SALAMANDER',
        'text': "Salamander is a productive natural lake with boggy banks situated atop a timbered ridge in the Ostler Fork Drainage. It is 4.1 acres, 10,020 feet in elevation, with 13 feet maximum depth. Access is 3¾ miles south and east of the Christmas Meadows Trailhead on the Stillwater and Amethyst Lake pack trails to the first meadow in Amethyst Basin. From this point, proceed southwest up the ridge to the lake. Salamander is surrounded by heavy timber and can be difficult to locate. Campsites are poor. Running water and horse feed are not available in the lake vicinity. Salamander is occasionally stocked with brook trout."
    },
    {
        'designation': 'BR-12',
        'name': 'SCOW',
        'text': "Scow is a spring-fed meadow lake located in heavy timber on the ridge between the Stillwater and Boundary Creek Drainages. It is 22.9 acres, 10,100 feet in elevation, with 6 feet maximum depth. Access is 2¾ miles south of the East Fork of the Bear River Boy Scout Camp on the Boundary Creek Trail past the old burn to a small off-stream meadow. From this point, continue south for ¾ mile through thick timber to the lake. Campsites are present with some horse feed in surrounding wet meadows. Spring water is readily available during the early summer months. Scow is stocked with brook trout, but fishing is unpredictable due to the occasional occurrence of winterkill."
    },
    {
        'designation': 'BR-31',
        'name': 'SEIDNER',
        'text': "Seidner is a small spring-fed lake which abuts a talus slope at the head of an isolated basin in the Stillwater Fork Drainage. It is 4.2 acres, 10,460 feet in elevation, with 8 feet maximum depth. Access is 2¾ miles south of the Christmas Meadows Trailhead on the Stillwater Pack Trail to a minor side drainage, and then some 2 steep miles west following this drainage to the head of the basin. Direct access trails are not available. Access on horseback can be difficult. The lake is immediately west of a large meadow where campsites and horse feed can be found. Spring water is available from any one of several inlet sources. Seidner presently contains a large population of brook trout sustained by natural reproduction."
    },
    {
        'designation': 'BR-32',
        'name': 'TEAL',
        'text': "Teal is a natural moraine lake situated at the base of a talus ridge in the Hayden Fork Drainage. It is 6.9 acres, 10,260 feet in elevation, with 14 feet maximum depth. Access is 1¼ miles northwest of Ruth Lake over rough and rocky terrain. Trails are not present and access on horseback can be difficult. Marginal campsites are available for small groups in the lake vicinity, but spring water and horse feed are not present. Teal is best suited for single day fishing trips. The lake is stocked on a regular basis with cutthroat trout."
    },
    {
        'designation': 'BR-25',
        'name': 'TOOMSET',
        'text': "This natural oval-shaped lake is located in a small glacial basin against sliderock ¼ mile north of Ostler Lake in Amethyst Basin. Toomset is 2.1 acres, 10,400 feet in elevation, with 11 feet maximum depth. Camping areas are poor in the vicinity of the lake with no available horse feed or spring water. Better sites for camping activity are located in the lower meadows due east of Ostler Lake. Toomset contains a brook trout population maintained by natural reproduction. The lake is often overlooked by anglers. Toomset provides a good opportunity to get away from the crowds in Amethyst Basin."
    },
    {
        'designation': 'BR-3',
        'name': 'WHISKEY ISLAND (GUY\'S)',
        'text': "Whiskey Island is a natural alpine lake situated in a rugged cirque basin at the foot of a steep talus ridge. It is 5 acres, 10,340 feet in elevation, with 19 feet maximum depth. The lake, characterized by a glacial turbidity, is green in color. Due to the frequent snowslides in the area, Whiskey Island is not usually free of ice and snow until mid-July. Access is 1¼ miles southwest of the Whiskey Creek timber road from a point approximately 1¼ miles northwest of U-150. The terrain is rough and composed of boulder fields and deadfall timber. There is no direct access trail. Whiskey Island is not accessible on horseback. Campsites, horse feed and spring water are not available in the lake vicinity. Whiskey Island is subject to winterkill, but experimental stocking of arctic grayling has been scheduled for 1985."
    },
    {
        'designation': 'G-73',
        'name': 'BOBS',
        'text': "Bobs is a scenic natural lake located in a glacial cirque at the base of Tokewanna Peak in the Middle Fork of the Blacks Fork Drainage. It is 6.6 acres, 11,150 feet in elevation, with 30 feet maximum depth. Access is 10¼ miles southwest of the East Fork Blacks Fork Road on the hit-and-miss Middle Fork Trail which begins as a jeep readjust south of the Blacks Fork bridge. This trail is blazed but receives limited use and can be indistinct and extremely difficult to locate in areas. The trail disappears in large headwater meadows, but Bobs can be located by following the tributary system towards the west. Bobs is situated well above timberline. Campsites are not available. However, an excellent spring water source is present at the lake. Better camping opportunities are situated lower in the basin. Bobs is stocked with cutthroat trout and fishing can be unpredictable."
    },
    {
        'designation': 'G-77',
        'name': 'DEAD HORSE',
        'text': "Dead Horse is a natural emerald green lake situated at the foot of Dead Horse Pass in rocky timberline terrain. It is 16.0 acres, 10,878 feet in elevation, with 41 feet maximum depth. Access is 7¼ miles south of the West Fork-Blacks Fork Trailhead on the West Fork Trail to the head of the basin. Campsites are available in the lake vicinity. Horse feed is present in large meadows to the northeast. Spring water is unavailable. The recreational appeal of the Dead Horse Basin is somewhat diminished by sheep grazing in the area. Dead Horse Lake is stocked with cutthroat trout and experiences moderate levels of angling pressure. Remember to pack out your refuse."
    },
    {
        'designation': 'G-37',
        'name': 'DUCK',
        'text': "Duck is an irregular natural lake situated in thick timber at the lower end of the East Fork Basin. It is 5.9 acres, 9,161 feet in elevation, with 5 feet maximum depth. The lake is a simple pothole located in a glacial catch-basin and there is no outlet. Access is ¼ mile northeast of the East Fork Blacks Fork Road on an unmarked logging road through a small meadow to the river. Cross the river at this point and proceed east for 200 yards to the lake. Marginal camping areas are available with some horse feed. Spring water sources are unavailable. Duck is shallow with very little inflow, and the lake provides marginal fish habitat. However, experimental stocking has been scheduled for 1985 to fully evaluate the potential of this lake."
    },
    {
        'designation': 'G-76',
        'name': 'EJOD',
        'text': "This rounded glacial lake is located in open country above timberline in the West Fork Drainage. It is 6.7 acres, 10,900 feet in elevation, with 12 feet maximum depth. The surrounding terrain is composed of alpine tundra and rocky shelves. Ejod is characterized by extensive shoal areas, with several deep water channels running through the lake. Ejod can be located by proceeding ¼ mile northwest of Dead Horse Lake to the top of the small ridge. Campsites are not available but suitable areas for camping activity can be located at Dead Horse. Horse feed is limited. Spring water is unavailable at Ejod. The lake contains a population of cutthroat trout sustained by natural recruitment and infrequent aerial stocking. Open shorelines at Ejod are ideal for fly casting. This lake is often overlooked by anglers."
    },
    {
        'designation': 'G-26',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-65',
        'name': None,
        'text': "G-65 is a shallow natural water with open shorelines located in partly timbered terrain in the Little East Fork Drainage. It is 5.0 acres, 10,900 feet in elevation, with 5 feet maximum depth. The lake abuts a steep talus slope to the west and a boggy meadow to the south. Access is 6 miles south of the East Fork-Blacks Fork Trailhead on the East Fork and Little East Fork trails to the large meadow (last meadow heading up country). From the lower end of this meadow, follow a minor tributary stream west for ¾ mile to the small basin containing G-65. The lake can also be located by heading south and slightly west of G-66 for ¼ mile up the steep timbered ridge. Marginal camping areas are available at G-65 with limited horse feed and no spring water sources. However, better camping opportunities are present in the vicinity of the large meadow to the east. G-65 contains a good brook trout population sustained by natural reproduction."
    },
    {
        'designation': 'G-66',
        'name': None,
        'text': "G-66 is a small natural lake located in dense conifers at the foot of a talus slope in the Little East Fork Drainage. It is 4.0 acres, 10,561 feet in elevation, with 12 feet maximum depth. The lake is characterized by a long, narrow arm to the north which is quite shallow. Access is 5 miles south of the East Fork-Blacks Fork Trailhead on the East Fork and Little East Fork trails to a large dry park (second major meadow heading up country in the Little East Fork Drainage). At the lower end of the park is a small stream coming from the west. An indistinct side trail follows this stream west and south for ¼ mile to the lake. Camping areas are available in the lake vicinity with several good sources of spring water. Horse feed is not present at the lake. G-66 contains a brook trout population sustained by natural reproduction. Angling pressure is moderate."
    },
    {
        'designation': 'G-67',
        'name': None,
        'text': "This deep natural water is located above timberline in a rugged cirque basin within the Little East Fork Drainage. G-67 is 7.7 acres, 11,158 feet in elevation, with 25 feet maximum depth. The surrounding terrain is composed of rocky alpine meadows, stunted low-growth conifers and willow, as well as talus slopes. G-67 is located 1 mile northwest of G-69 around the rocky point. Campsites and horse feed are not available in the lake vicinity due to the open timberline terrain. Spring water may be available early in the season. G-67 is occasionally stocked with brook trout."
    },
    {
        'designation': 'G-68',
        'name': None,
        'text': "G-68 is a small alpine lake situated in open windswept country ¼ mile northwest of G-69 in the Little East Fork Drainage. The lake is 4.1 acres, 11,421 feet in elevation, with 6 feet maximum depth. Campsites are not available due to the open nature of the surrounding terrain and absence of fuelwood. Horse feed is sparse and spring water unavailable. G-68 is shallow in overall depth and subject to frequent winterkill. As a result, stocking has been presently discontinued."
    },
    {
        'designation': 'G-69',
        'name': None,
        'text': "G-69 is a small natural lake situated in open alpine meadows above timberline in the Little East Fork Drainage. It is 4.8 acres, 11,109 feet in elevation, with 13 feet maximum depth. Camping areas are not available in the immediate lake vicinity. Fuelwood is extremely sparse, as is horse feed. Spring water is unavailable. Access is 7¼ miles south of the East Fork-Blacks Fork Trailhead on the East Fork and Little East Fork trails to the head of the large meadow, and then 1 mile west up the steep partially timbered slope to the lake. Although there is no direct trail access, G-69 is accessible on horseback. The lake contains a population of cutthroat trout sustained by natural reproduction."
    },
    {
        'designation': 'G-70',
        'name': None,
        'text': "This windswept alpine lake is situated well above timberline in the Little East Fork Drainage. G-70 is 3.8 acres, 11,450 feet in elevation, with 4 feet maximum depth. The lake is irregular in outline and very shallow in overall depth. Access is 1¼ miles south of G-69 along a rough and rocky ridge. Campsites are unavailable due to the open nature of the surrounding terrain and absence of fuelwood. Spring water is present in the lake vicinity. The recreational appeal of this basin is diminished somewhat by sheep grazing. G-70 has contained fish populations in the past. It is scheduled to receive experimental stocking of cutthroat trout during 1985."
    },
    {
        'designation': 'G-71',
        'name': None,
        'text': "G-71 is a small natural lake located above timberline in a cirque basin at the head of the Little East Fork Drainage. It is 4.8 acres maximum, 11,527 feet in elevation, with 14 feet maximum depth. The lake is milky in appearance due to a glacial turbidity. G-71 fluctuates 1-2 feet annually and at the minimum water level the lake separates into 3 distinct pools. Access is 9 miles south of the East Fork-Blacks Fork Trailhead on the East Fork and Little East Fork trails to the foot of Squaw Pass. Leave the trail at this point and proceed west for 1¼ miles over rough terrain to the lake. G-71 is not directly accessible on horseback. Campsites are not available, but spring water can be located ¾ mile below the lake on the outlet stream. G-71 is scheduled for continued experimental stocking of brook trout during 1984."
    },
    {
        'designation': 'G-72',
        'name': None,
        'text': "G-72 is a small natural lake situated in a rugged, glacial cirque above timberline at the head of the Middle Fork Drainage. It is 1.3 acres, 11,198 feet in elevation, with 6 feet maximum depth. The immediate watershed is composed of dense patches of willow and steep talus slopes to the south, and low stunted conifers in the moraine to the north. Access is ¼ mile south of G-74 up the steep grassy slope to the small basin containing G-72. Campsites and horse feed are not available. Spring water is present early in the season. G-72 has been scheduled for experimental stocking during 1984."
    },
    {
        'designation': 'G-74',
        'name': None,
        'text': "G-74 is a small moraine lake situated on a glacial shelf against a steep talus ridge. It is 3.4 acres, 10,934 feet in elevation, with 3 feet maximum depth. Access is 9¾ miles southwest of the East Fork Road on the Middle Fork Blacks Fork jeep road and trail to the head of the Middle Fork Basin. The trail is indistinct and extremely difficult to locate at times, and disappears in the headwater region about 1 mile short of the lake. However, G-74 can be located by following the easternmost drainage system in the upper basin. Good campsites are available with ample horse feed and good supplies of spring water. G-74 experiences very light angler use and limited camping activity. The lake is shallow and contains a population of wary brook trout. G-74 may be subject to at least partial winterkill."
    },
    {
        'designation': 'G-75',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-78',
        'name': None,
        'text': "G-78 is a small meadow lake characterized by partly open shorelines and an earth-colored glacial turbidity. It is 3.2 acres, 10,660 feet in elevation, with 9 feet maximum depth. The lake is subject to natural water level fluctuation of about 3 feet. Some marginal campsites are available in the lake vicinity, but spring water is not present. Access is 1 mile south of the West Fork-Blacks Fork Trailhead on the West Fork Trail to the first major tributary stream coming from the west. Follow this side drainage west and south for 1¼ miles to the lake. The terrain is steep and heavily timbered, and access on horseback can be difficult. Horse feed is available at the lake. G-78 was experimentally stocked with brook trout during 1984, but it may be subject to winterkill."
    },
    {
        'designation': 'G-79',
        'name': None,
        'text': "G-79 is a small glacial lake located in a narrow cirque at the base of a precipitous rock face which rises to 1,000 feet above the lake. It is 2.5 acres, 10,820 feet in elevation, with 5 feet maximum depth. G-79 is shallow and may be subject to some degree of natural water level fluctuation. Access is ¾ mile south of G-78 around the rocky ridge. The terrain is steep and rugged and should not be attempted on horseback. Suitable camping areas are available with a good source of spring water. G-79 was scheduled to receive experimental stocking of brook trout during 1983."
    },
    {
        'designation': 'G-80',
        'name': None,
        'text': "This remote glacial lake is located in rocky, timbered terrain high on the ridge overlooking the West Fork Drainage. It is 1.8 acres, 10,580 feet in elevation, with 8 feet maximum depth. The lake abuts a steep talus slope to the west which is prone to snowslides. Access is 2¼ miles south of the West Fork-Blacks Fork Trailhead on the West Fork Trail to the upper end of Buck Pasture and then ¾ mile west up the steep timbered slope to the small basin containing G-80. Access is difficult and should not be attempted on horseback. Marginal campsites are available with a good source of spring water. G-80 is stocked occasionally with brook trout and receives light fishing pressure."
    },
    {
        'designation': 'G-81',
        'name': None,
        'text': "G-81 is a small spring-fed lake located in partly timbered terrain in the West Fork Drainage. It is 1.6 acres, 10,665 feet in elevation, with 5 feet maximum depth. The lake is semi-circular in outline. It is turquoise in color due to a suspension of fine glacial material. G-81 is located ¾ mile southwest of G-82 at the southern end of the large cirque basin against a talus slope. The terrain is steep, there are no trails, and horse access may be difficult. Campsites are available with a good source of spring water. Horse feed is extremely limited. G-81 is stocked infrequently with cutthroat trout."
    },
    {
        'designation': 'G-82',
        'name': None,
        'text': "G-82 is a shallow natural lake located in a boggy meadow on the ridge overlooking the West Fork Drainage. The lake is 3.8 acres, 10,140 feet in elevation, with 6 feet maximum depth. The lake is irregular in outline and composed of 2 arms connected by a narrow channel. G-82 is brown in color due to a fine suspended glacial material. Access is ¼ mile southwest of the old scaler's cabin at the West Fork-Blacks Fork Trailhead up the steep timbered ridge. The lake is situated in thick timber, but it can be located by following the drainage system. Direct access on horseback is difficult. Camping areas are available. Spring water is not present. G-82 contains a small population of wary brook trout. The lake is subject to some water level fluctuation and may winterkill on occasion."
    },
    {
        'designation': 'G-83',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-84',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-85',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-86',
        'name': None,
        'text': "G-86 is a productive natural lake situated in dense timber ¾ mile northwest of Duck Lake in the East Fork of the Blacks Fork Drainage. It is 6.4 acres, 9,142 feet in elevation, with 7 feet maximum depth. The lake is irregular in outline and composed of 2 major arms connected by a narrow channel. Yellow pondlily completely encircles the lake. Potential campsites are available without horse feed or spring water. G-86 is scheduled for experimental stocking of brook trout during 1985 to evaluate the potential of this water to sustain a fishery."
    },
    {
        'designation': 'G-87',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-90',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-25',
        'name': 'LITTLE LYMAN',
        'text': "Little Lyman is a productive natural lake located in partly timbered terrain in the lower Blacks Fork Basin. It is 5.0 acres, 9,276 feet in elevation, with 25 feet maximum depth. Access is 16 miles east of U-150 on the North Slope Road or 24 miles southwest of Robertson, Wyoming on the Blacks Fork Road to a well marked turnoff, and then 4¾ mile north on the Lyman Lake Road to the lake. The Forest Service maintains a small full service campground at Little Lyman with 10 units. Little Lyman Lake is stocked on an annual basis with rainbow trout catchables and brook trout fingerling. Angling pressure is heavy due to the accessibility of this water."
    },
    {
        'designation': 'G-27',
        'name': 'LYMAN',
        'text': "This large scenic lake is situated immediately north and east of Little Lyman Lake in the West Fork Drainage (see directions to Little Lyman Lake). Lyman is 36.6 acres, 9,311 feet in elevation, with 30 feet maximum depth. A small dam has been placed across the outlet stream at Lyman to enlarge the original lake dimensions. Lyman is easily accessible and sustains heavy levels of fishing pressure. A summer youth camp has been established at the northeastern end of the lake. Good sites are available for primitive camping activity in the lake vicinity. However, a full service campground is maintained by the Forest Service at the nearby Little Lyman Lake with tap water and restroom facilities. Lyman has a history of winterkill and the fishery is sustained by periodic stockings of catchable-sized rainbow and albino rainbow trout. However, experimental stocking of brook trout was accomplished during 1983 and 1984 to evaluate the winterkill situation at this water."
    },
    {
        'designation': 'G-102',
        'name': 'MOSLANDER',
        'text': "Moslander is a productive reservoired lake located in the West Muddy Creek Drainage of the Blacks Fork Basin. It is 11.4 acres maximum, 9,691 feet in elevation, with 29 feet maximum depth. The immediate watershed is composed of gently sloping timbered ridges with scattered meadows. Reservoir operation at Moslander is capable of drawdown of up to 1 feet and surface area reduction of 50% annually. Moslander is directly accessible to 4-wheel drive vehicles. From the North Slope Road at Elizabeth Pass proceed northwest for 3¾ miles on the Elizabeth Mountain Road. From this point turn right on a jeep trail and proceed north and east for an additional 3¾ miles to the lake. Camping areas are available without spring water sources. Moslander Reservoir contains marginal habitat, but experimental stocking of brook trout is scheduled for 1985."
    },
    {
        'designation': 'G-37',
        'name': 'DUCK',
        'text': "Duck is an irregular natural lake situated in thick timber at the lower end of the East Fork Basin. It is 5.9 acres, 9,161 feet in elevation, with 5 feet maximum depth. The lake is a simple pothole located in a glacial catch-basin and there is no outlet. Access is 0.5 mile northeast of the East Fork Blacks Fork Road on an unmarked logging road through a small meadow to the river. Cross the river at this point and proceed east for 200 yards to the lake. Marginal camping areas are available with some horse feed. Spring water sources are unavailable. Duck is shallow with very little inflow, and the lake provides marginal fish habitat. However, experimental stocking has been scheduled for 1985 to fully evaluate the potential of this lake."
    },
    {
        'designation': 'G-76',
        'name': 'EJOD',
        'text': "This rounded glacial lake is located in open country above timberline in the West Fork Drainage. It is 6.7 acres, 10,900 feet in elevation, with 12 feet maximum depth. The surrounding terrain is composed of alpine tundra and rocky shelves. Ejod is characterized by extensive shoal areas, with several deep water channels running through the lake. Ejod can be located by proceeding 0.25 mile northwest of Dead Horse Lake to the top of the small ridge. Campsites are not available but suitable areas for camping activity can be located at Dead Horse. Horse feed is limited. Spring water is unavailable at Ejod. The lake contains a population of cutthroat trout sustained by natural recruitment and infrequent aerial stocking. Open shorelines at Ejod are ideal for fly casting. This lake is often overlooked by anglers."
    },
    {
        'designation': 'G-26',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-65',
        'name': None,
        'text': "G-65 is a shallow natural water with open shorelines located in partly timbered terrain in the Little East Fork Drainage. It is 5.0 acres, 10,900 feet in elevation, with 5 feet maximum depth. The lake abuts a steep talus slope to the west and a boggy meadow to the south. Access is 6 miles south of the East Fork-Blacks Fork Trailhead on the East Fork and Little East Fort trails to the large meadow (last meadow heading up country). From the lower end of this meadow, follow a minor tributary stream west for 0.75 mile to the small basin containing G-65. The lake can also be located by heading south and slightly west of G-66 for 0.5 mile up the steep timbered ridge. Marginal camping areas are available at G-65 with limited horse feed and no spring water sources. However, better camping opportunities are present in the vicinity of the large meadow to the east. G-65 contains a good brook trout population sustained by natural reproduction."
    },
    {
        'designation': 'G-66',
        'name': None,
        'text': "G-66 is a small natural lake located in dense conifers at the foot of a talus slope in the Little East Fork Drainage. It is 4.0 acres, 10,561 feet in elevation, with 12 feet maximum depth. The lake is characterized by a long, narrow arm to the north which is quite shallow. Access is 5 miles south of the East Fork-Blacks Fork Trailhead on the East Fork and Little East Fork trails to a large dry park (second major meadow heading up country in the Little East Fork Drainage). At the lower end of the park is a small stream coming from the west. An indistinct side trail follows this stream west and south for 0.75 mile to the lake. Camping areas are available in the lake vicinity with several good sources of spring water. Horse feed is not present at the lake. G-66 contains a brook trout population sustained by natural reproduction. Angling pressure is moderate."
    },
    {
        'designation': 'G-67',
        'name': None,
        'text': "This deep natural water is located above timberline in a rugged cirque basin within the Little East Fork Drainage. G-67 is 7.7 acres, 11,158 feet in elevation, with 25 feet maximum depth. The surrounding terrain is composed of rocky alpine meadows, stunted low-growth conifers and willow, as well as talus slopes. G-67 is located 1 mile northwest of G-69 around the rocky point. Campsites and horse feed are not available in the lake vicinity due to the open timberline terrain. Spring water may be available early in the season. G-67 is occasionally stocked with brook trout."
    },
    {
        'designation': 'G-68',
        'name': None,
        'text': "G-68 is a small alpine lake situated in open windswept country 0.75 mile northwest of G-69 in the Little East Fork Drainage. The lake is 4.1 acres, 11,421 feet in elevation, with 6 feet maximum depth. Campsites are not available due to the open nature of the surrounding terrain and absence of fuelwood. Horse feed is sparse and spring water unavailable. G-68 is shallow in overall depth and subject to frequent winterkill. As a result, stocking has been presently discontinued."
    },
    {
        'designation': 'G-69',
        'name': None,
        'text': "G-69 is a small natural lake situated in open alpine meadows above timberline in the Little East Fork Drainage. It is 4.8 acres, 11,109 feet in elevation, with 13 feet maximum depth. Camping areas are not available in the immediate lake vicinity. Fuelwood is extremely sparse, as is horse feed. Spring water is unavailable. Access is 7.25 miles south of the East Fork-Blacks Fork Trailhead on the East Fork and Little East Fork trails to the head of the large meadow, and then 1 mile west up the steep partially timbered slope to the lake. Although there is no direct trail access, G-69 is accessible on horseback. The lake contains a population of cutthroat trout sustained by natural reproduction."
    },
    {
        'designation': 'G-70',
        'name': None,
        'text': "This windswept alpine lake is situated well above timberline in the Little East Fork Drainage. G-70 is 3.8 acres, 11,450 feet in elevation, with 4 feet maximum depth. The lake is irregular in outline and very shallow in overall depth. Access is 1.25 miles south of G-69 along a rough and rocky ridge. Campsites are unavailable due to the open nature of the surrounding terrain and absence of fuelwood. Spring water is present in the lake vicinity. The recreational appeal of this basin is diminished somewhat by sheep grazing. G-70 has contained fish populations in the past. It is scheduled to receive experimental stocking of cutthroat trout during 1985."
    },
    {
        'designation': 'G-71',
        'name': None,
        'text': "G-71 is a small natural lake located above timberline in a cirque basin at the head of the Little East Fork Drainage. It is 4.8 acres maximum, 11,527 feet in elevation, with 14 feet maximum depth. The lake is milky in appearance due to a glacial turbidity. G-71 fluctuates 1-2 feet annually and at the minimum water level the lake separates into 3 distinct pools. Access is 9 miles south of the East Fork-Blacks Fork Trailhead on the East Fork and Little East Fork trails to the foot of Squaw Pass. Leave the trail at this point and proceed west for 1.25 miles over rough terrain to the lake. G-71 is not directly accessible on horseback. Campsites are not available, but spring water can be located 0.25 mile below the lake on the outlet stream. G-71 is scheduled for continued experimental stocking of brook trout during 1984."
    },
    {
        'designation': 'G-72',
        'name': None,
        'text': "G-72 is a small natural lake situated in a rugged, glacial cirque above timberline at the head of the Middle Fork Drainage. It is 1.3 acres, 11,198 feet in elevation, with 6 feet maximum depth. The immediate watershed is composed of dense patches of willow and steep talus slopes to the south, and low stunted conifers in the moraine to the north. Access is 0.25 mile south of G-74 up the steep grassy slope to the small basin containing G-72. Campsites and horse feed are not available. Spring water is present early in the season. G-72 has been scheduled for experimental stocking during 1984."
    },
    {
        'designation': 'G-74',
        'name': None,
        'text': "G-74 is a small moraine lake situated on a glacial shelf against a steep talus ridge. It is 3.4 acres, 10,934 feet in elevation, with 3 feet maximum depth. Access is 9.25 miles southwest of the East Fork Road on the Middle Fork Blacks Fork jeep road and trail to the head of the Middle Fork Basin. The trail is indistinct and extremely difficult to locate at times, and disappears in the headwater region about 1 mile short of the lake. However, G-74 can be located by following the easternmost drainage system in the upper basin. Good campsites are available with ample horse feed and good supplies of spring water. G-74 experiences very light angler use and limited camping activity. The lake is shallow and contains a population of wary brook trout. G-74 may be subject to at least partial winterkill."
    },
    {
        'designation': 'G-75',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-78',
        'name': None,
        'text': "G-78 is a small meadow lake characterized by partly open shorelines and an earth-colored glacial turbidity. It is 3.2 acres, 10,660 feet in elevation, with 9 feet maximum depth. The lake is subject to natural water level fluctuation of about 3 feet. Some marginal campsites are available in the lake vicinity, but spring water is not present. Access is 1 mile south of the West Fork-Blacks Fork Trailhead on the West Fork Trail to the first major tributary stream coming from the west. Follow this side drainage west and south for 1.25 miles to the lake. The terrain is steep and heavily timbered, and access on horseback can be difficult. Horse feed is available at the lake. G-78 was experimentally stocked with brook trout during 1984, but it may be subject to winterkill."
    },
    {
        'designation': 'G-79',
        'name': None,
        'text': "G-79 is a small glacial lake located in a narrow cirque at the base of a precipitous rock face which rises to 1,000 feet above the lake. It is 2.5 acres, 10,820 feet in elevation, with 5 feet maximum depth. G-79 is shallow and may be subject to some degree of natural water level fluctuation. Access isl.25 mile south of G-78 around the rocky ridge. The terrain is steep and rugged and should not be attempted on horseback. Suitable camping areas are available with a good soruce of spring water. G-79 was scheduled to receive experimental stocking of brook trout during 1983."
    },
    {
        'designation': 'G-80',
        'name': None,
        'text': "This remote glacial lake is located in rocky, timbered terrain high on the ridge overlooking the West Fork Drainage. It is 1.8 acres, 10,580 feet in elevation, with 8 feet maximum depth. The lake abuts a steep talus slope to the west which is prone to snowslides. Access is 2.5 miles south of the West Fork-Blacks Fork Trailhead on the West Fork Trail to the upper end of Buck Pasture and then 0.75 mile west up the steep timbered slope to the small basin containing G-80. Access is difficult and should not be attempted on horseback. Marginal campsites are available with a good source of spring water. G-80 is stocked occasionally with brook trout and receives light fishing pressure."
    },
    {
        'designation': 'G-81',
        'name': None,
        'text': "G-81 is a small spring-fed lake located in partly timbered terrain in the West Fork Drainage. It is 1.6 acres, 10,665 feet in elevation, with 5 feet maximum depth. The lake is semi-circular in outline. It is turquoise in color due to a suspension of fine glacial material. G-81 is located 0.75 mile southwest of G-82 at the southern end of the large cirque basin against a talus slope. The terrain is steep, there are no trails, and horse access may be difficult. Campsites are available with a good source of spring water. Horse feed is extremely limited. G-81 is stocked infrequently with cutthroat trout."
    },
    {
        'designation': 'G-82',
        'name': None,
        'text': "G-82 is a shallow natural lake located in a boggy meadow on the ridge overlooking the West Fork Drainage. The lake is 3.8 acres, 10,140 feet in elevation, with 6 feet maximum depth. The lake is irregular in outline and composed of 2 arms connected by a narrow channel. G-82 is brown in color due to a fine suspended glacial material. Access is 0.5 mile southwest of the old scaler's cabin at the West Fork-Blacks Fork Trailhead up the steep timbered ridge. The lake is situated in thick timber, but it can be located by following the drainage system. Direct access on horseback is difficult. Camping areas are available. Spring water is not present. G-82 contains a small population of wary brook trout. The lake is subject to some water level fluctuation and may winterkill on occasion."
    },
    {
        'designation': 'G-83',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-84',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-85',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-86',
        'name': None,
        'text': "G-86 is a productive natural lake situated in dense timber 0.75 mile northwest of Duck Lake in the East Fork of the Blacks Fork Drainage. It is 6.4 acres, 9,142 feet in elevation, with 7 feet maximum depth. The lake is irregular in outline and composed of 2 major arms connected by a narrow channel. Yellow pondlily completely encircles the lake. Potential campsites are available without horse feed or spring water. G-86 is scheduled for experimental stocking of brook trout during 1985 to evaluate the potential of this water to sustain a fishery."
    },
    {
        'designation': 'G-87',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-90',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-25',
        'name': 'LITTLE LYMAN',
        'text': "Little Lyman is a productive natural lake located in partly timbered terrain in the lower Blacks Fork Basin. It is 5.0 acres, 9,276 feet in elevation, with 25 feet maximum depth. Access is 16 miles east of U-150 on the North Slope Road or 24 miles southwest of Robertson, Wyoming on the Blacks Fork Road to a well marked turnoff, and then 0.5 mile north on the Lyman Lake Road to the lake. The Forest Service maintains a small full service campground at Little Lyman with 10 units. Little Lyman Lake is stocked on an annual basis with rainbow trout catchables and brook trout fingerling. Angling pressure is heavy due to the accessibility of this water."
    },
    {
        'designation': 'G-27',
        'name': 'LYMAN',
        'text': "This large scenic lake is situated immediately north and east of Little Lyman Lake in the West Fork Drainage (see directions to Little Lyman Lake). Lyman is 36.6 acres, 9,311 feet in elevation, with 30 feet maximum depth. A small dam has been placed across the outlet stream at Lyman to enlarge the original lake dimensions. Lyman is easily accessible and sustains heavy levels of fishing pressure. A summer youth camp has been established at the northeastern end of the lake. Good sites are available for primitive camping activity in the lake vicinity. However, a full service campground is maintained by the Forest Service at the nearby Little Lyman Lake with tap water and restroom facilities. Lyman has a history of winterkill and the fishery is sustained by periodic stockings of catchable-sized rainbow and albino rainbow trout. However, exprimental stocking of brook trout was accomplished during 1983 and 1984 to evaluate the winterkill situation at this water."
    },
    {
        'designation': 'G-102',
        'name': 'MOSLANDER',
        'text': "Moslander is a productive reservoired lake located in the West Muddy Creek Drainage of the Blacks Fork Basin. It is 11.4 acres maximum, 9,691 feet in elevation, with 29 feet maximum depth. The immediate watershed is composed of gently sloping timbered ridges with scattered meadows. Reservoir operation at Moslander is capable of drawdown of up to 12 feet and surface area reduction of 50% annually. Moslander is directly accessible to 4-wheel drive vehicles. From the North Slope Road at Elizabeth Pass proceed northwest for 3.25 miles on the Elizabeth Mountain Road. From this point turn right on a jeep trail and proceed north and east for an additional 3.25 miles to the lake. Camping areas are available without spring water sources. Moslander Reservoir contains marginal habitat, but experimental stocking of brook trout is scheduled for 1985."
    },
    
    # ========== Sheep Carter Burnt Fork Drainage ==========
    # Sheep/Carter Creek Drainage
    {
        'designation': 'GR-9',
        'name': 'ANSON, LOWER',
        'text': "Located at the end of the maintained trail into Weyman Lakes Basin, Lower Anson Lake is impossible to miss. Total distance from Spirit Lake and the Beaver Creek Trail head are 6.2 and 8.1 miles, respectively. The lake is 14.5 acres, 10,575 feet in elevation with a maximum depth of 20 feet. Good campsites are infrequent in rough, rocky terrain. The best spots are in the vicinity of the trail. Horse feed is spotty. If you plan an extended trip, it is probably a good idea to pasture horses in the meadows along the stream between Lower and Upper Anson lakes. There is no spring water at Lower Anson, but there is a large spring on the east side of the creek about 0.1 mile north of Upper Anson Lake. Lower Anson Lake has been stocked in the past with brook trout. Due to apparent success of natural reproduction, stocking of brook trout was discontinued. Fishing pressure is moderate to heavy on this fairly popular water. A few cutthroat trout are also available."
    },
    {
        'designation': 'GR-10',
        'name': 'ANSON, UPPER',
        'text': "Upper Anson is a natural lake just 0.2 miles south of Lower Anson Lake in the Weyman Lakes Basin. A maintained Forest Service trail drops down from higher country to Lower Anson. From there a faint trail leads south along the east side of the creek to Upper Anson. Total distance from the Beaver Creek Trail head and Spirit Lake is 8.8 and 6.9 miles, respectively. Upper Anson Lake is 7.7 acres, 10,660 feet in elevation with a maximum depth of 58 feet. Horses can travel within 100 yards of the lake but no further due to rocky terrain. There are no good campsites at the lake itself, however spring water is available. Campsites, horse feed and additional spring water are found between Upper and Lower Anson lakes. Upper Anson Lake contains a population of brook trout which sustains itself through natural reproduction. Fishing pressure is moderate."
    },
    {
        'designation': 'GR-22',
        'name': 'BUMMER',
        'text': "This small, shallow lake is located on the east side of Lamb Lakes Basin approximately 6.5 miles from Browne Lake. There is no maintained trail for the last 1.5 miles. The most direct access to lakes in this basin is cross-country from the junction of Forest Service trails 018-I and 017 southwest up the bottom of the basin. The going is rough through rocky timber and across boulder fields. Horse access is impossible by this route and should not be attempted. Supposedly, horses can get into Lamb Lakes Basin via two little-used trails, one which drops from the ridge southeast of Bummer Lake, the other which drops from the ridge northwest of Ewe Lake. The existence of these trails was not verified during this project. Horse use in Lamb Lakes Basin would be restricted due to the rocky terrain. Bummer Lake is 1.9 acres, 10,350 feet in elevation with a maximum depth of 6 feet. Wading can be an effective way to fish this lake. Use extreme caution, however, because footing is quite treacherous. The lake is periodically stocked with brook trout. Good campsites are rare, and there is no spring water. A little horse feed is found near the inlet. Fishing pressure is light."
    },
    {
        'designation': 'GR-17',
        'name': 'CANDY',
        'text': "Candy Lake is a rocky 5.5 acre pond lying in the northeast corner of Weyman Lakes Basin approximately 8.8 miles from the Beaver Creek Trail head. Follow the directions to Hidden Lake (GR-7). Candy lies 0.2 miles north through rocky timber. Horses can be taken as far as Lower Anson Lake. Candy Lake sits at an elevation of 10,290 feet and has a maximum depth of 29 feet. Campsites are rare in the immediate vicinity, but spring water is present. The lake does not overwinter fish due to poor inlet flows, and stocking has been discontinued indefinitely. The lake may be experimentally planted sometime in the future with Arctic grayling which may prove more tolerant of the harsh environment. Check with the Division of Wildlife Resources Office in Vernal for the current management of this lake."
    },
    {
        'designation': 'GR-12',
        'name': 'CLEAR',
        'text': "This pretty lake is aptly named. Located in Weyman Lakes Basin, Clear Lake lies 0.4 miles west of Lower Anson Lake, 8.5 miles from the Beaver Creek Trail head and 6.6 miles from Spirit Lake. The last 0.4 miles is through rocky timber, and horse access is impossible beyond Anson lakes. The lake is 10.2 acres, 10,780 feet in elevation with a maximum depth of 25 feet. No campsites or spring water are found in the immediate area. Fishing pressure is light. The lake may contain cutthroat trout."
    },
    {
        'designation': 'GR-116',
        'name': 'COLUMBINE',
        'text': "Columbine Lake sits on a rocky bench at the base of a talus slope 1.3 miles southwest of Spirit Lake. The lake is 5.7 acres and 10,550 feet in elevation. Follow the Middle Fork of Sheep Creek upstream from Spirit Lake until the stream goes underground. The lake lies across the boulder fields to the south. Horse access is impossible. Spring water is available at the lake, and a few campsites can be found in a grassy area on the lake's southwestern shore. Despite only a 5 foot maximum depth and a lake level that tends to fluctuate during drier years, Columbine Lake still manages to support a small population of brook trout maintained through periodic stocking. Fishing pressure is light."
    },
    {
        'designation': 'GR-6',
        'name': 'DAGGETT',
        'text': "Located only 2.6 miles southeast of Spirit Lake via a good trail, Daggett Lake is one of the more accessible and popular lakes in the Sheep Creek drainage. It is 42.6 acres, 10,462 feet in elevation with a maximum depth of 29 feet. Campsites are scattered around the lake. Spring water, although present, is not abundant. Horse feed can be found in a narrow meadow north of the lake or along the outlet below the dam. Daggett Lake is noted for hordes of mosquitoes that can quickly turn a pleasant hike into a real ordeal. Come prepared with lots of insect repellant. Fishing pressure is heavy for stocked rainbow trout. An occasional cutthroat can also be taken."
    },
    {
        'designation': 'GR-18',
        'name': 'EWE',
        'text': "Ewe Lake is located at the bottom of a talus slope in western Lamb Lake Basin. It is 3.0 acres, 10,750 feet in elevation with a maximum depth of 10 feet. Ewe Lake is 7.3 miles from Browne Lake. The last 2.3 miles is cross-country across rough terrain. See Bummer Lake for a more detailed description of general access to the Lamb Lakes area. Campsites are scarce, but spring water can be found at the lake. Trout stocked in Ewe Lake in the past have not been able to overwinter, and as of 1986 the lake is fishless. Grayling may be introduced in the future on an experimental basis. Fishing pressure is light."
    },
    {
        'designation': 'GR-115',
        'name': 'GAIL',
        'text': "Gail is a small, seldom visited lake which sits at the bottom of a rock slide approximately 1.1 miles southwest of Spirit Lake. Follow the trail to Jesson Lake. Gail lies 0.2 miles to the south across downed timber and rocky terrain. The lake is 4.5 acres, 10,420 feet in elevation with 25 feet maximum depth. There are no campsites in this rough country, and spring water is not available. Horse access is difficult, if not impossible. Gail supports a small population of cutthroat trout. An occasional brook trout may also be taken. Fishing pressure is very light."
    },
    {
        'designation': 'GR-11',
        'name': None,
        'text': "This 2.6 acre pothole lake sits 200 yards southwest of Upper Anson Lake. Campsites, horse feed and sources of spring water are as described for Anson Lakes. GR-11 is 10,635 feet in elevation and has a maximum depth of 8 feet. This lake provides only marginal fish habitat and may winterkill. Fishing pressure is quite light for stocked brook trout."
    },
    {
        'designation': 'GR-13',
        'name': None,
        'text': "This natural moraine lake is situated on a glacial shelf at the bottom of a cirque in western Weyman Lakes Basin. The east-west orientation of the cirque makes this 9.2 acre lake susceptible to severe winds. GR-13 is located at timberline at an elevation of 10,820 feet and is surrounded by boulder fields and weathered stands of sub-alpine fir. The lake lies 0.7 miles west of Anson Lakes up rock slides and across rough boulder fields. Total distance from Spirit Lake and Beaver Creek Trail head is 7.8 and 9.7 miles, respectively. Horses are best left at Anson Lakes. Campsites are nonexistent, and no spring water is available. GR-13 is rather unique in that the lakes underground outlet is a visible siphon found along the northeastern shore. Fishing pressure is very light for stocked brook trout."
    },
    {
        'designation': 'GR-14',
        'name': None,
        'text': "This lake does not support fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'GR-20',
        'name': None,
        'text': "GR-20 is a fairly shallow, rocky pond which sits a short distance southwest of Bummer Lake in Lamb Lakes Basin. This lake is 5.7 acres, 10,355 feet in elevation with a maximum depth of 8 feet. Access and camping are as described for Bummer Lake. The inlets and outlet of GR-20 are intermittent, and the lake provides only marginal fish habitat. Fishing is very light for stocked brook trout."
    },
    {
        'designation': 'GR-21',
        'name': None,
        'text': "Located less than 200 yards northwest of Bummer Lake, GR-21 is quite similar to GR-20. Habitat is marginal and the lake may winterkill. GR-21 is 3.7 acres, 10,355 feet in elevation with a maximum depth of 7 feet. Fishing is very light for stocked brook trout."
    },
    {
        'designation': 'GR-31',
        'name': None,
        'text': "This natural, irregular shaped lake is essentially an on stream portion of the Sheep Creek Canal, which supplies irrigation water to northern Daggett County. This makes the lake fairly easy to find. Simply follow the canal 1.2 miles northwest from its junction with the Leidy Peak Trail [012]. GR-31 is the first lake you come to directly below the canal's first major waterfall. Total distance from Browne Lake is approximately 4.1 miles. The lake is 6.0 acres, 9,270 feet in elevation with a maximum depth of 6 feet. There is no spring water, campsites, or horse feed in the immediate vicinity. Horse feed and a few campsites are available in a small meadow along the canal 0.3 miles upstream. Fishing pressure is very light for naturally produced brook trout."
    },
    {
        'designation': 'GR-104',
        'name': None,
        'text': "This 4.3 acre natural pond sits on a steep bench overlooking the Sheep Creek Canal approximately 3.1 miles from both the Beaver Creek Trail head and Spirit Lake. GR-104 is located 0.3 miles west of the junction of Forest Service trails 017 and 052. The lake lies at an elevation of 9,290 feet and is surrounded by rocky timber. Maximum depth is 19 feet. Campsites and spring water are not available in the immediate area. The lake does not have inlets or an outlet and does not overwinter trout. This is another water where grayling may be stocked sometime in the future. Contact the Division of Wildlife Resources Office in Vernal for up-to-date information. Fishing pressure is very light."
    },
    {
        'designation': 'GR-7',
        'name': 'HIDDEN',
        'text': "Hidden Lake is a picturesque, natural lake which lies at the bottom of a wet meadow 0.7 miles northwest of Lower Anson Lake in Weyman Lakes Basin. Total distance from the Beaver Creek Trail head is 9.0 miles. Horses should be ridden only as far as Anson Lakes. From that point access is cross-country through downed timber and across scattered boulder fields. The lake is 8.5 acres, 10,380 feet in elevation with a maximum depth of 26 feet. Spring water can be found on the lake's southwestern shore, but campsites are few and far between in the rough country which surrounds the lake. Fishing pressure is light for stocked brook trout. The lake also supports a small number of cutthroat trout."
    },
    {
        'designation': 'GR-112',
        'name': 'HIDDEN',
        'text': "This natural lake, not to be confused with another water of the same name in Weyman Lake Basin, is surrounded by heavy timber and rock slides 0.8 miles northwest of the Spirit Lake campground. Direct access is through downed timber and across scattered boulder fields. The going is a little easier if you travel to Lost Lake via the maintained trail and then north cross-country 0.2 miles to Hidden. Total distance for this route is 1.3 miles. The lake is 4.3 acres, 10,270 feet in elevation with a maximum depth of 8 feet. Campsites are limited due to the rough terrain, and there are no reliable sources of spring water. A small amount of horse feed is located on the lake's eastern shore. Hidden Lake is stocked with brook trout but also produces an occasional cutthroat trout. Fishing pressure is light."
    },
    {
        'designation': 'GR-1',
        'name': 'JESSON',
        'text': "Jesson Lake is a fairly large, popular water which lies approximately 1.0 mile southwest of Spirit Lake via a maintained but rocky trail. This natural lake is surrounded by rocky timber and good campsites are difficult to find. Spring water and a minute amount of horse feed are located on the west shoreline. Jesson Lake is 25.5 acres, 10,392 feet in elevation with a maximum depth of 56 feet. Brook trout are regularly stocked, but don't be surprised if you land an occasional cutthroat. Fishing pressure is heavy."
    },
    {
        'designation': 'GR-25',
        'name': 'JUDY',
        'text': "This seldom visited, picturesque pond sits on a high bench 0.4 miles south of Tamarack Lake. The most direct access is from the south shore of Tamarack. A hard scramble up 400 vertical feet puts you on top of the bench. Judy Lake lies a short distance further south at the base of the boulder fields. Total distance from Spirit Lake is 1.8 miles. The lake is 4.7 acres, 10,830 feet in elevation with a maximum depth of 24 feet. Horse access is difficult and there is no horse feed at the lake. No spring water is found in the immediate vicinity, and campsites are scarce due to the rough, rocky terrain. Fishing pressure is light for stocked brook trout."
    },
    {
        'designation': 'GR-19',
        'name': 'LAMB',
        'text': "Lamb Lake is located at the bottom of a small brushy meadow in the western lobe of Lamb Lakes Basin. Abutting a steep rock slide, this relatively murky lake is 6.0 acres, 10,540 feet in elevation with a maximum depth of 10 feet. There is no trail to the lake. Follow access directions to Bummer Lake. Lamb Lake lies to the west 0.9 miles across downed timber and rocks. The lake is surrounded by rocky timber but generally has an open shoreline. Horse feed and campsites are scarce due to the rough terrain; however, spring water is abundant. This lake has marginal fish habitat and may be fishless. Fishing pressure is light."
    },
    {
        'designation': 'GR-111',
        'name': 'LILY PAD',
        'text': "This lake does not support fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'GR-4',
        'name': 'LOST',
        'text': "This shallow pond is located just north of the trail between Spirit and Tamarack lakes. Approximately 0.3 miles past Lily Pad Lake (not stocked) turn north off the trail. Lost Lake is 0.1 miles down the slope. Total distance from Spirit Lake is 1.1 miles. The lake can also be reached by following the outlet of Tamarack Lake northeast 0.3 miles. Lost Lake is 3.2 acres, 10,300 feet in elevation with a maximum depth of only 7 feet. Good water exchange enables fish to survive the winter in Lost Lake despite the fairly shallow water. A handful of campsites are available at the lake. Horse feed is limited, however, and spring water is not available. Cutthroat trout are able to reproduce in Lost Lake so stocking has been discontinued for the time being. Fishing pressure is light."
    },
    {
        'designation': 'GR-101',
        'name': 'LOST (Mystery)',
        'text': "This pretty, elongated lake lies in a pocket formed by two oblique ridges and is surrounded by dense timber. There is a trail to the lake, but it can be difficult to find. Follow the south bank of the Sheep Creek Canal downstream from the Leidy Peak Trail. Approximately 0.2 miles upstream of GR-31 the trail cuts up the slope to the south. Lost Lake, also called Mystery Lake in some references, is 1.1 miles further along the trail. The lake is 10.2 acres, 9,750 feet in elevation with a maximum depth of 25 feet. Total distance from Browne Lake is 4.9 miles. Spring water is located on the lake's south shore. There is no horse feed, and decent campsites are difficult to find because of the rocky, timbered slopes around the lake. The lake is periodically stocked with brook trout. Cutthroat trout are also present in the lake. Fishing pressure is light to moderate."
    },
    {
        'designation': 'GR-23',
        'name': 'MUTTON',
        'text': "This natural lake abuts a rocky slope in the southern corner of Lamb Lakes Basin. There is no trail to the lake. Easiest access is to follow the inlet of Bummer Lake 0.6 miles south to Mutton. Total distance from Browne Lake is 7.0 miles. Mutton Lake is 3.8 acres, 10,570 feet in elevation with a maximum depth of 10 feet. Spring water is available at the lake, and a few campsites can be found around the inlet area. Horse feed is not abundant, and horse access to the lake, or anywhere in the basin, is difficult due to the rough terrain. Fishing pressure is very light for stocked brook trout."
    },
    {
        'designation': 'GR-32',
        'name': 'ONE FISH',
        'text': "One Fish Lake is located in heavy timber just a few yards north of the Sheep Creek Canal 0.3 miles downstream from where the canal crosses the Leidy Peak Trail. Total distance from Browne Lake is 3.0 miles. Campsites, horse feed and spring water are available in the large meadow 0.2 miles southeast of the canal. The lake is 4.5 acres, 9,350 feet in elevation with a maximum depth of 35 feet. Unless you are an expert don't bother taking a fly rod. The dense timber makes back casting almost impossible. Fishing pressure is light for stocked brook trout."
    },
    {
        'designation': 'GR-16',
        'name': 'PENGUIN',
        'text': "This small, boulder-strewn pond is located just a few yards west of Upper Anson Lake in Weyman Lakes Basin. Penguin Lake is surrounded by talus slopes and rocky moraines. The lake is 2.1 acres, 10,665 feet in elevation with a maximum depth of 20 feet. Total distances from Spirit Lake and the Beaver Creek Trail head are 7.1 and 9.0 miles, respectively. Campsites, spring water and horse feed are available in the vicinity of Anson lakes. Penguin supports a naturally reproducing population of pan-sized brook trout. Fishing pressure is light to moderate."
    },
    {
        'designation': 'GR-27',
        'name': 'POTTER, LOWER',
        'text': "This small circular pond is located just a few yards northeast of the much larger Upper Potter Lake. See the Upper Potter description for access instructions. Lower Potter Lake is 3.4 acres when full, 10,130 feet in elevation with a maximum depth of 16 feet. Campsites are practically nonexistent because of the extremely rocky terrain. Horse feed is scarce for the same reason, and there is no spring water in the immediate vicinity. Fishing pressure is moderate for brook trout sustained by natural reproduction."
    },
    {
        'designation': 'GR-27',
        'name': 'POTTER, UPPER',
        'text': "Upper Potter Lake is a fairly large, deep, elongated lake located at the base of a steep rock slide. Easiest access is from Browne Lake. Follow the trail from Browne Lake to the bottom of Lamb Lakes Basin. Approximately 1.0 mile beyond where the trail crosses the West Fork of Carter Creek a faint trail cuts off to the south. Upper Potter Lake lies at the end of this trail. Total distance from Browne Lake is approximately 6.5 miles. A topo map is a good thing to carry if you are not familiar with the country. Upper Potter Lake is 21.3 acres, 10,130 feet in elevation with a maximum depth of 75 feet. Campsites are not available in the immediate vicinity due to the rough terrain. There is no horse feed or spring water at the lake. Upper Potter is not stocked; however, the lake contains a self-sustaining population of brook trout. Fishing pressure is light."
    },
    {
        'designation': 'GR-24',
        'name': 'RAM',
        'text': "Ram Lake lies at the base of a rock slide approximately 0.6 miles west-southwest of Bummer Lake in Lamb Lakes Basin. See Bummer Lake for more detailed access instructions. Total distance from Browne Lake is 6.9 miles. There is no maintained trail into the basin. Ram Lake is 7.0 acres, 10,380 feet in elevation with a maximum depth of 27 feet. The rough, rocky terrain in the immediate area affords few good campsites. Spring water is found in good supply along the eastern margin of the talus while horse feed is available in wet meadows to the west. This lake may contain a small population of cutthroat trout. Fishing pressure is light."
    },
    {
        'designation': 'GR-33',
        'name': 'RED',
        'text': "This fairly large, irregular shaped lake is located at the end of a rough, rocky trail 1.2 miles south of the Teepee Lakes. The trail to Red Lake diverges from the Leidy Peak Trail just south of its junction with the Sheep Creek Canal. Total distance from Browne Lake is 4.4 miles. Leidy Peak, located south of the lake, provides a stunning backdrop. Red Lake is 20.9 acres, 9,850 feet in elevation with a maximum depth of 57 feet. Good campsites are very infrequent in the rough, timbered country surrounding the lake. Spring water is also unavailable. Sparse horse feed can be found in meadows to the north along the outlet. Deep sod-covered potholes abound in the meadow. You may want to picket horses on firmer ground rather than turning them loose with hobbles. Fishing pressure is light to moderate for stocked brook trout."
    },
    {
        'designation': 'GR-15',
        'name': 'SESAME',
        'text': "Surrounded by boulder fields and talus slopes, Sesame Lake lies in a shallow depression 0.4 miles west of Upper Anson Lake in Weyman Lakes Basin. The most direct access is due west from Penguin Lake up the rock slide and across some of the roughest boulder fields in the Uintas. Use caution when traversing the rocks. Even 5 ton boulders can sometimes shift when stepped on. The lake is located 7.4 and 9.3 miles, respectively from Spirit Lake and the Beaver Creek Trail head. Sesame Lake is 6.0 acres, 10,780 feet in elevation with a maximum depth of 7 feet. The nearest campsites, spring water and horse feed are found at Anson Lakes. Sesame Lake is occasionally stocked with brook trout. Fishing pressure is very light. Fishing can be spotty as the lake may experience partial winterkill during particularly harsh winters."
    },
    {
        'designation': 'GR-5',
        'name': 'SUMMIT',
        'text': "This pretty, hourglass shaped lake sits at the bottom of a steep talus slope a short mile south of Spirit Lake. Easiest access is to travel due south of Spirit Lake until you hit a line of steep cliffs. Follow the base of the slope to Summit. The lake is 9.9 acres, 10,460 feet in elevation with a maximum depth of only 7 feet. Winterkill has been a problem in the past and, as of this writing, the lake does not support a fishery. Future plans call for the stocking of Arctic grayling on an experimental basis. Contact the Division of Wildlife Resources office in Vernal to inquire about the lake's status before you plan a trip. Even without a fishery, the lake is worth a visit."
    },
    {
        'designation': 'GR-2',
        'name': 'TAMARACK',
        'text': "Tamarack Lake is by far the largest lake in the Sheep/Carter Creek Drainage system. Located 1.4 miles west of Spirit Lake via a rocky but maintained Forest Service trail, Tamarack is a popular fishing lake for day hikers and scout groups. The lake is 79.1 acres, 10,429 feet in elevation with a maximum depth of 90 feet. The best camping sites are found on the east side of the lake while a few springs can be found along the southern shoreline. A few small meadows east of the lake contain horse feed. Tamarack Lake supports a naturally reproducing population of brook trout. A small number of cutthroat also inhabit the lake. Fishing pressure is heavy."
    },
    {
        'designation': 'GR-28',
        'name': 'TEEPEE, LOWER',
        'text': "Lower Teepee Lake is a hourglass shaped lake surrounded by fairly heavy timber located at the head of the Sheep Creek Canal and 2.9 miles by trail from Browne Lake. Follow the canal upstream 0.2 miles from its junction with the Leidy Peak Trail. Lower Teepee Lake is 4.3 acres and sits at an elevation of 9,410 feet. The western basin of the lake is only 6 feet at its deepest point, but the larger eastern basin drops to 28 feet fairly quickly. Campsites, horse feed, and spring water are available in the vicinity of a long meadow 0.1 miles west of the lake across the trail. Fishing pressure is moderate to heavy for stocked brook trout."
    },
    {
        'designation': 'GR-30',
        'name': 'TEEPEE, UPPER',
        'text': "This circular lake is located in dense timber 150 yards southeast of Lower Teepee Lake (see Lower Teepee Lake access). Upper Teepee Lake is 6.5 acres, 9,430 feet in elevation with a maximum depth of 28 feet. Campsites are limited, and there are no springs or horse feed in the area. Fishing could be spotty as the lake winterkills occasionally. It may have a few cutthroat trout. Fishing pressure is moderate."
    },
    
    # Burnt Fork Drainage
    {
        'designation': 'GR-134',
        'name': 'BENNION, LOWER',
        'text': "Lower Bennion is a natural, somewhat elongated lake lying at the base of North Burro Peak in the southwestern corner of the Burnt Fork drainage. A maintained trail goes only as far as Island Lake. Lower Bennion, also called Bennion Lake in some texts, is located approximately 0.7 miles west of Island Lake across a large meadow and up a timbered slope. The lake lies 10.8 miles from Spirit Lake and 10.1 miles from Hoop Lake via Kabell Ridge. Lower Bennion is 7.7 acres, 10,950 feet in elevation with a maximum depth of 13 feet. Campsites and spring water are found at the lake. Horse feed is located in small meadows along the eastern shore or in the vicinity of Whitewall Lake, a short distance to the southeast. The lake is stocked cyclicly with brook trout but also contains a small self-sustaining population of cutthroat trout. Fishing pressure is light."
    },
    {
        'designation': 'GR-135',
        'name': 'BENNION, UPPER',
        'text': "This small shallow pond is located on the edge of a rocky meadow only a few hundred yards upstream of Lower Bennion Lake. Upper Bennion Lake is 2.0 acres, 10,970 feet in elevation with a maximum depth of 3 feet. Facilities and distances from major trail heads are as described for Lower Bennion. This lake is not stocked; however, both brook and cutthroat trout can migrate from Lower Bennion to Upper Bennion through the short connecting stream. Fishing pressure is light."
    },
    {
        'designation': 'GR-126',
        'name': 'BOXER',
        'text': "Boxer Lake is a relatively shallow, natural pond located against a talus slope at the head of a basin in the southeastern corner of the Burnt Fork drainage. A faint trail begins at the western end of Fish Lake (see Fish Lake access) and eventually cuts south across a ridge to Burnt Fork Lake. Boxer lies 0.3 miles to the southeast. The lake is 6.0 acres, 10,700 feet in elevation with a maximum depth of 11 feet. Total distance from Spirit Lake is 6.5 miles. The lake is 10.6 miles from Hoop Lake via the Burnt Fork Trail. Campsites are plentiful, and large areas of wet meadow supply excellent horse feed. Spring water is found along the west shore of Boxer Lake or along the meadow edge. Fishing pressure is moderate for cutthroat trout. There is some natural reproduction, and stocking has been discontinued on an experimental basis."
    },
    {
        'designation': 'GR-127',
        'name': 'BURNT FORK',
        'text': "Burnt Fork Lake lies one mile by faint trail from the western end of Fish Lake (see Fish Lake access). The trail winds westerly along the base of a ridge and then cuts south over the ridge to the lake. Burnt Fork Lake is 9.8 acres, 10,630 feet in elevation with a maximum depth of 25 feet. The lake abuts a rock slide on its east side and is located 6.1 and 10.2 miles from Spirit Lake and the Hoop Lake Campground, respectively. Campsites, horse feed and spring water are located in areas as described for Boxer Lake. Cutthroat trout reproduce naturally, and stocking has been discontinued. Fishing pressure is moderate."
    },
    {
        'designation': 'GR-128',
        'name': 'CRYSTAL',
        'text': "This shallow, natural pond is located at the bottom of a steep talus slope 0.6 miles southwest of Burnt Fork Lake. Direct access is down a fairly steep, timber covered slope. If your compass bearing is right, you will exit the trees at the lake. A longer but more sure access route is to follow the outlet of Burnt Fork Lake down the slope until you reach a wet grassy meadow. The outlet stream of Crystal Lake flows into Burnt Fork Creek on the west side of the meadow. Crystal is located 6.7 miles from Spirit Lake and 9.2 miles from Hoop Lake via the Burnt Fork Trail. The lake is 5.4 acres, 10,380 feet in elevation with a maximum depth of only 5 feet. The terrain is rough and sloping. Campsites are scarce, and horse feed is not plentiful. Spring water is located on the lake's south side. Cutthroat trout sustain themselves without stocking. A few brook trout also inhabit the lake. Fishing pressure is very light."
    },
    {
        'designation': 'GR-125',
        'name': 'FISH',
        'text': "Fish Lake is a relatively large, narrow lake bordered along its entire south shore by a steep rock slide. The lake sits atop the divide between the Burnt Fork and Sheep Creek drainage. A maintained Forest Service trail dead ends at the lake's western tip. Total distance from Spirit Lake and Hoop Lake via the Burnt Fork Trail is 5.1 and 9.2 miles, respectively. Fish Lake is 38.3 acres, 10,685 feet in elevation with a maximum depth of 23 feet. Campsites and spring water are available at the lake. The best horse feed is located in a large park 0.5 miles north along the trail. Fish Lake is periodically stocked with brook trout but also holds a few cutthroat. Fishing pressure is moderate to heavy."
    },
    {
        'designation': 'GR-132',
        'name': 'ISLAND',
        'text': "Island Lake is a large impounded water located in the southwest corner of the Burnt Fork drainage. The lake is used for water storage, and the water level fluctuates according to irrigation demand downstream. The area is quite popular with scout groups and other campers. Island Lake lies 8.9 miles from Hoop Lake via the trail across Kabell Ridge and 9.6 miles from Spirit Lake to the east. Lakes in the Uinta River drainage (Fox Lake area) are easily accessible across a Pass to the south of the lake. Island Lake is 117.8 acres at full pool, 10,777 feet in elevation with a maximum depth of 34 feet. Excellent campsites are in the vicinity. Spring water is located along the lake's south shore. The best horse feed is found around Whitewall Lake to the west or in a narrow meadow north of the lake. Island Lake contains a self-sustaining population of cutthroat trout and fair numbers of brook trout. Fishing pressure is heavy."
    },
    {
        'designation': 'GR-140',
        'name': 'KABELL',
        'text': "Kabell Lake is another popular lake with large hiking groups. From Hoop Lake a maintained trail leads south to Kabell Meadows. At the upper end of the meadows a trail splits off to the southeast and begins to climb the eastern tip of Kabell Ridge. A short distance down this trail a spur trail cuts to the right and terminates at Kabell Lake. Total distance from Hoop Lake is 5.2 miles. Kabell Lake is 14.7 acres, 10,348 feet in elevation with a maximum depth of 23 feet. The lake is almost completely surrounded by dense timber, and campsites are fairly scarce. Small meadows located to the north along the outlet provide horse feed and possible camping areas. Spring water is found along the south side of the lake. Fishing pressure is moderate for stocked cutthroat trout."
    },
    {
        'designation': 'GR-131',
        'name': 'ROUND',
        'text': "Round Lake is a natural, picturesque lake which sits 0.4 miles southeast of the Island Lake outlet through heavy timber. Total distance from Spirit Lake and Hoop Lake via Kabell Ridge is 10.2 and 9.3 miles, respectively. Round Lake is 24.3 acres, 10,662 feet in elevation with a maximum depth of 38 feet. Excellent campsites, horse feed and spring water are available in the immediate vicinity. Fishing pressure is moderate for stocked cutthroat trout."
    },
    {
        'designation': 'GR-130',
        'name': 'SNOW',
        'text': "This pretty lake is surrounded on three sides by talus slides and ledges. Snow Lake lies 0.3 miles east of Round Lake through a rocky draw. The lake is located 10.6 miles from Spirit Lake and 9.9 miles from Hoop Lake via Kabell Ridge. Horse access is impossible. Snow Lake, sometimes referred to as Andrea in older texts, is 9.4 acres, 10,550 feet in elevation with a maximum depth of 35 feet. No campsites are available due to the uneven rocky terrain. A number of springs are located on the west end of the lake. Cutthroat trout are planted cyclicly, and fishing pressure is light."
    },
    {
        'designation': 'GR-133',
        'name': 'WHITEWALL',
        'text': "Whitewall Lake is a shallow natural lake which sits in a large meadow 0.4 miles west of Island Lake. The lake is located 9.8 miles from Hoop Lake across Kabell Ridge and 10.5 miles from Spirit Lake. Campsites and horse feed are plentiful while a number of springs are located on the west shore. Whitewall Lake is 14.5 acres, 10,900 feet in elevation with a maximum depth of 3 feet. The lake is stocked periodically with cutthroat trout. Fishing pressure is light."
    },
    
    # ========== Smith Henry Beaver Drainage ==========
    # Smiths Fork Basin
    {
        'designation': 'G-63',
        'name': 'BALD',
        'text': "This natural cirque lake is situated in rugged timberline terrain at the base of Bald Mountain in the West Fork Smiths Fork Drainage. Bald is 6.4 acres, 11,030 feet in elevation, with 23-foot maximum depth. The immediate watershed is composed of steep talus slopes to the west and low stunted conifers in the glacial moraine to the north and east. Camping areas are available without horse feed or spring water sources. Access is 2 1/2 miles south of the Hewinta Guard Station on the Mansfield Meadows Road to the Wilderness Boundary and then 2 1/2 miles further south on the West Fork Smiths Fork Trail to the junction with the Highline Trail. Leave these trails and continue southwest for an additional 1 1/2 miles overland following the drainage system to the head of the basin and Bald Lake. Bald sustains moderate to light angling pressure and contains a large population of brook trout produced by natural reproduction."
    },
    {
        'designation': 'G-20',
        'name': 'BRIDGER',
        'text': "Bridger is a productive sub-alpine water situated in timbered terrain with open shorelines in the lower Smiths Fork Basin. This natural lake is 21.0 acres, 9,350 feet in elevation, with 15-foot maximum depth. Bridger is located 25 miles south of Mountain View, Wyoming, on Highway 410 and improved Forest Service Roads. The route is well marked with signs. The Forest Service maintains a full service campground with 25 units at the lake and a summer guard station is located nearby. Bridger is a popular lake and receives substantial levels of fishing pressure. Shore fishing is difficult due to extensive beds of yellow pondlilly growing in shoal areas around much of the lake's perimeter. Bridger is most effectively fished with a small boat or inflatable raft. There are no launching facilities for larger boats. Bridger Lake receives periodic stocking of rainbow trout catchables throughout the summer, and annual plants of brook trout fingerling."
    },
    {
        'designation': 'G-21',
        'name': 'CHINA',
        'text': "China Reservoir is a scenic sub-alpine water situated in thick timber in the lower Smiths Fork Basin. It is 31.2 acres maximum, 9,408 feet in elevation, with 45-foot maximum depth. The lake has been enlarged by a dam at the northern end. Reservoir operation is capable of annual fluctuation of up to 9 feet and surface area reduction of about 39 percent. Access to China Lake is 1/8 mile north of the North Slope Road on foot following an old timber road which has been closed to vehicular access. This route begins at a small turnoff and parking area 1/2 mile west of China Meadows. Primitive camping is available with no sources of spring water. China Lake experiences moderate to heavy levels of angling pressure. This lake was previously managed to produce cutthroat trout, but is presently scheduled to receive annual stocking of brook trout supplemented by occasional plants of arctic grayling."
    },
    {
        'designation': 'G-13',
        'name': None,
        'text': "G-13 is an elongated natural lake located in a heavily timbered basin directly east of Lower Red Castle Lake. It is 7.9 acres, 10,860 feet in elevation, with 17-foot maximum depth. Trail access is 1 mile southeast of the footbridge immediately below Lower Red Castle Lake on the Bald Mountain-Smiths Fork Pass Trail. G-13 lies to the south of and within sight of the aforementioned trail. Adjacent campsites are available with a limited amount of horse feed in wet meadows to the north. Running water is not present in the lake vicinity. G-13 is subject to occasional winterkill and fishing success can be quite variable. The lake receives frequent stocking of brook trout to compensate for winterkill losses and sustains moderate to light angling pressure."
    },
    {
        'designation': 'G-30',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-31',
        'name': None,
        'text': "This lake does not sustain fish life. It is shown on the map as a landmark."
    },
    {
        'designation': 'G-34',
        'name': None,
        'text': "This small reservoired lake is located near the junction of the China Meadows and North Slope Roads at the lower end of China Meadows. It is 1.0 acre in size, 9,390 feet in elevation, with 6-foot maximum depth. G-34 is fed by a large spring to the south and contains dense growths of aquatic vegetation. Camping opportunities are provided at the nearby China Meadows Campground. G-34 receives heavy recreational use due to the access afforded by improved Forest Service roads. The lake contains populations of brook and rainbow trout."
    },
    {
        'designation': 'G-36',
        'name': None,
        'text': "G-36 is an abandoned beaver pond located in a natural glacial depression in thick timber in the lower Smiths Fork Basin. It is 4.7 acres, 9,430 feet in elevation, with 11-foot maximum depth. The lake is easily accessible and located 1/8 mile east of the bridge at the lower end of China Meadows. Potential camping areas are available with no source of spring water. Experimental stocking was accomplished during 1985 to evaluate the potential of G-36 to sustain a fishery. At present G-36 experiences light recreational pressure."
    },
    
    # ========== Uintas Rock Creek Drainage ==========
    {
        'designation': 'Z-44',
        'name': 'ALLEN',
        'text': "This natural lake is situated in an open meadow approximately 3/4 mile east of Bedground Lake. It is 15.2 acres, 10,390 feet in elevation, with a maximum depth of 16 feet. The lake lies 10.8 miles from the Upper Stillwater Trailhead, 9.6 miles from Mirror Lake, and 9.0 miles from the Grandview Trailhead. There is no trail from Bedground to Allen Lake, but horse access is not difficult. Campsites and horse feed are plentiful, and numerous springs can be found in the area. Horseflies and mosquitoes can be bothersome at times, so bring plenty of repellent. Allen Lake contains a population of Arctic grayling and brook trout sustained through natural reproduction. Fishing pressure is light."
    },
    {
        'designation': 'X-9',
        'name': 'GRANDADDY',
        'text': "Of all the lakes in the High Uintas that are inaccessible by vehicle, Grandaddy Lake is probably the most popular. It is by far the largest natural lake in the Uintas, with 173 acres at 10,310 feet in elevation. Maximum depth is 40 feet. The lake is located 3.2 miles from the Grandview Trailhead and 13.4 miles from Mirror Lake. Campsites and horse feed are plentiful. A few springs are also located in the area. Grandaddy Lake is not stocked but nonetheless supports good numbers of brook and cutthroat trout sustained through natural reproduction. Fishing pressure is heavy, particularly during early summer. Keep in mind that, although the lake itself is open to year-round fishing, the tributaries to Grandaddy Lake are closed to fishing May 1 through mid-July. Check Fishing Proclamation for exact date, it may change slightly from year to year."
    },
    {
        'designation': 'X-132',
        'name': 'BLACK',
        'text': "Black Lake is a popular body of water located 15 miles from the Upper Stillwater Trailhead and 10.6 miles from Mirror Lake via Rocky Sea Pass. It is 11.8 acres, 10,403 feet in elevation, with 14 feet maximum depth. Well-marked access trails lead to the lake. Black Lake is often visited by Scout troops hiking the Highline Trail. An abundant population of brook trout is sustained by stocking and some natural reproduction. Some cutthroat trout are also present. Angling pressure is moderate to heavy. Campsites are plentiful in the general area, and springs are found along the west side of the lake. Horse feed may be found in open meadows 1/2 mile north of the lake. Black Lake is susceptible to overuse, especially during years when Rocky Sea Pass is snow-free most of the summer, allowing easier access from trailheads to the west."
    },
    {
        'designation': 'Z-39',
        'name': 'DALE',
        'text': "This natural lake, located in popular Four Lakes Basin, is surrounded by boggy meadows. It is 12.9 acres, 10,700 feet in elevation, with 25 feet maximum depth. Campsites, horse feed, and spring water are plentiful. The lake is located 9.0 and 10.8 miles respectively from the Grandview and Upper Stillwater Trailheads and 8.7 miles from Mirror Lake. Fishing pressure is fairly heavy for stocked brook trout."
    },
    {
        'designation': 'Z-25',
        'name': 'RAINBOW',
        'text': "Rainbow Lake is a popular water located in northern Grandaddy Basin. The lake is 17.9 acres, 9,930 feet in elevation, with a maximum depth of 15 feet. A number of major trail junctions occur in the immediate vicinity. Consequently, Rainbow Lake is a favorite camping spot for hiking groups. The lake is 9.8 miles from the Upper Stillwater Trailhead, 8.7 miles from Mirror Lake, and 7.0 miles from the Grandview Trailhead. Excellent campsites and horse feed are found in the area. Some spring water is also available. Rainbow Lake is periodically stocked with brook trout. Fishing pressure is heavy."
    },
    {
        'designation': 'X-95',
        'name': 'SQUAW',
        'text': "Squaw Lake is a diamond-shaped lake surrounded by open meadows. It is located in Squaw Basin, 9.8 miles from the Upper Stillwater Trailhead and 15.6 miles from Moon Lake via Tworoose Pass. It is 10.4 acres, 10,483 feet in elevation, with 9 feet maximum depth. This lake is quite popular with groups hiking the Highline Trail. Campsites, spring water and horse feed are plentiful. Fishing pressure is heavy for stocked brook trout."
    },
    
    # ========== Yellowstone Lake Fork Swift Drainage ==========
    # Yellowstone Drainage
    {
        'designation': 'X-110',
        'name': 'BLUEBELL',
        'text': "This lake sits next to a steep bald mountain and has an earthen dam which allows water levels to fluctuate 7 feet. It is 38.3 acres, 10,894 feet in elevation, with 32 feet maximum depth. Access is gained by following the east inlet stream from Spider Lake southwest 1/4 mile to Bluebell. The last 1/4 mile is thick willows, pines and large boulders, so it is best to leave horses at Spider and walk into Bluebell. Campsites near the lake are sparse and very little horse feed is available. Brook trout are very abundant and a few cutthroat are also present; both species reproduce naturally. Fishing pressure is moderate."
    },
    {
        'designation': 'Y-16',
        'name': 'DOLL',
        'text': "This natural lake sits in a shallow depression next to a talus ridge above timberline. It is 42.5 acres, 11,352 feet in elevation, with 47 feet maximum depth. Access is 3/4 mile west-northwest of Five Point Reservoir up a trailless ridge for a total distance of 13 miles from Swift Creek Campground. Horse access is very difficult the last 1/2 mile. There are few campsites and very limited horse pasture. This lake contains an abundant population of pan-size brook trout, and receives light fishing pressure."
    },
    {
        'designation': 'Y-34',
        'name': 'GEM',
        'text': "This natural lake is mostly surrounded by timber except for a wet meadow on the north side. It is 36.2 acres, 10,550 feet in elevation, with 30 feet maximum depth. Access is 10 miles from Swift Creek Campground via the Swift Creek Trail to Five Point Reservoir, then north and east on the Garfield Basin Trail for 1 3/4 miles. Excellent horse feed and campsites are available. Both brook and cutthroat trout reproduce naturally, and angling pressure is moderate to heavy."
    },
    {
        'designation': 'X-58',
        'name': 'SWASEY',
        'text': "This popular lake is located in scenic Swasey Hole and has an earthen dam on the northeast side. It is 24.6 acres, 10,810 feet in elevation, with 36 feet maximum depth. Access is 11 miles from Swift Creek Campground or 9 miles from the Hells Canyon Trailhead. Excellent horse feed is available in wet meadows around the lake. Campsites are abundant, and spring water is available. The lake is stocked with cutthroat trout and receives moderate to heavy angling pressure."
    },
    {
        'designation': 'X-109',
        'name': 'SPIDER',
        'text': "This pretty lake has several long, finger-like bays extending into wet meadows. It is 26.7 acres, 10,830 feet in elevation, with 27 feet maximum depth. Access is gained by following the Garfield Basin Trail from Five Point Reservoir for 1 1/2 miles. Excellent horse pasture exists in large wet meadows around the lake. Spring water and camping sites are abundant. The lake is stocked with cutthroat trout and receives moderate to heavy angling pressure."
    },
    
    # Lake Fork Drainage  
    {
        'designation': 'X-64',
        'name': 'ATWINE',
        'text': "This large natural lake is surrounded by timber and sits next to the trail. It is 32 acres, 10,150 feet in elevation, with 35 feet maximum depth. Good access is along the Brown Duck-Clements Lake Trail, approximately 9 miles from Moon Lake. Horse pasture is limited, but spring water and camping areas are available. Both stocking and natural reproduction contributes to an abundant brook trout population. Angling and camping pressure is moderate."
    },
    {
        'designation': 'X-31',
        'name': 'BROWN DUCK',
        'text': "Brown Duck has a dam across the outlet and fluctuates approximately 12 feet. It is the first lake on the Brown Duck Trail and is located 7 miles from the Moon Lake Campground. Maximum surface area is 30.7 acres, 10,186 feet in elevation, with 38 feet maximum depth. There is little horse feed or spring water, and the available camping areas around the lake are overused. Both natural and stocked cutthroat trout inhabit the lake and angling pressure is heavy."
    },
    {
        'designation': 'X-74',
        'name': 'CLEMENTS',
        'text': "This large reservoired lake is surrounded by timber and located in the northern part of Brown Duck Basin. It is 79.2 acres (maximum), 10,444 feet in elevation, with 50 feet maximum depth. Access is excellent along the Clements Lake Trail for 11 miles from Moon Lake. Horse feed is limited to small wet meadows around the lake. Spring water and camping areas are available. The lake is stocked with cutthroat trout. Angling pressure is moderate to heavy."
    },
    {
        'designation': 'LF-2',
        'name': 'CRATER',
        'text': "This large natural lake sits next to the trail in Lambert Meadows. It is 40.7 acres, 10,480 feet in elevation, with 20 feet maximum depth. Access is along the well-marked Lake Fork Trail for 11 miles from Moon Lake. Abundant horse feed exists in large wet meadows around the lake. Campsites and spring water are available. Cutthroat trout reproduce naturally and the lake also receives stocking. Angling pressure is moderate to heavy."
    },
    {
        'designation': 'LF-4',
        'name': 'PORCUPINE',
        'text': "This natural lake sits in a timbered basin and has a small earthen dam on the outlet. It is 11.4 acres, 10,540 feet in elevation, with 20 feet maximum depth. Access is 12 miles from Moon Lake via the Lake Fork Trail to Lambert Meadows, then cross-country southwest for 1 mile. Limited horse feed is available in small meadows near the lake. Both cutthroat and brook trout reproduce naturally. Angling pressure is moderate."
    }
]

# Continue with more entries from other pages...
def get_all_entries():
    """Return all manually extracted DWR lake entries"""
    # For now, return the entries from page 1
    # We can expand this as we extract more pages
    return DWR_LAKE_ENTRIES