#!/bin/bash
# Edits-server journal/media endpoint checks. Run by tests/journal/run.sh
# against a FRESH harness on :8899 whose scratch files live in $1
# (journal j.json, log x.jsonl, media/). Needs network for the link-title checks.
H=http://127.0.0.1:8899
S="$1"
pass=0; fail=0
ok() { if eval "$2"; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1"; echo "      got: ${R:0:300}"; fail=$((fail+1)); fi; }
post() { R=$(curl -s -X POST -H 'Content-Type: application/json' --data "$1" $H/api/journal); }

R=$(curl -s $H/api/ping); ok "ping" '[[ "$R" == *writer* ]]'

# --- journal: apply, LWW, errors, tombstones ---
post '{"device":"t","docs":[
 {"kind":"trip","doc":{"id":"t-lq2x9a-k3f1","updated":"2026-10-10T18:00:00.000Z","title":"Toomset + Amethyst","planned":false,"date":"2024-10-12","end_date":"2024-10-14","body":"hi","lakes":["BR-25","BR-28","BR-25"],"links":[{"url":"https://example.com/a","title":"A"}],"junk":1}},
 {"kind":"photo","doc":{"id":"p-lq2xb1-9d0e","updated":"2026-10-10T18:00:00.000Z","trip":"t-notyet-0000","lakes":["BR-28"],"caption":"c","taken":"2024-10-13T09:41:00","w":2048,"h":1536}},
 {"kind":"link","doc":{"id":"l-lq2xc1-aaaa","updated":"2026-10-10T18:00:00.000Z","lake":"BR-29","url":"https://example.com/b","title":"B","note":""}},
 {"kind":"trip","doc":{"id":"t-plan01-zzzz","updated":"2026-10-10T18:00:00.000Z","title":"Someday","planned":true,"date":"2025-01-01","when":"summer 2027","lakes":[]}}
]}'
ok "4 docs applied" '[[ $(echo "$R" | grep -o "\"applied\"" | wc -l) -eq 4 ]]'
ok "journal file sorted, deduped lakes, junk dropped" \
   'python3 -c "import json,sys; d=json.load(open(\"$S/j.json\")); t=d[\"trips\"]; assert [x[\"id\"] for x in t]==sorted(x[\"id\"] for x in t); a=[x for x in t if x[\"id\"]==\"t-lq2x9a-k3f1\"][0]; assert a[\"lakes\"]==[\"BR-25\",\"BR-28\"] and \"junk\" not in a; p=[x for x in t if x[\"planned\"]][0]; assert p[\"date\"] is None and p[\"when\"]==\"summer 2027\""'
ok "applied docs logged without payload" '[[ $(grep -c "\"kind\"" $S/x.jsonl) -eq 4 ]] && ! grep -q Toomset $S/x.jsonl'

post '{"device":"t","docs":[{"kind":"trip","doc":{"id":"t-lq2x9a-k3f1","updated":"2026-10-10T17:00:00.000Z","title":"OLDER"}}]}'
ok "older write superseded with current doc" '[[ "$R" == *superseded* && "$R" == *Toomset* ]]'
post '{"device":"t","docs":[{"kind":"trip","doc":{"id":"t-lq2x9a-k3f1","updated":"2026-10-10T18:00:00.000Z","title":"Toomset + Amethyst","lakes":["BR-25"]}}]}'
ok "equal timestamp re-send applies (idempotent)" '[[ "$R" == *applied* ]]'

post '{"device":"t","docs":[{"kind":"trip","doc":{"id":"t-badlak-0001","updated":"2026-10-10T18:00:00.000Z","title":"x","lakes":["ZZ-999"]}}]}'
ok "unknown lake -> error" '[[ "$R" == *error* && "$R" == *ZZ-999* ]]'
post '{"device":"t","docs":[{"kind":"link","doc":{"id":"l-badurl-0001","updated":"2026-10-10T18:00:00.000Z","lake":"BR-29","url":"javascript:alert(1)"}}]}'
ok "non-http url -> error" '[[ "$R" == *error* && "$R" == *http* ]]'
post "{\"device\":\"t\",\"docs\":[{\"kind\":\"link\",\"doc\":{\"id\":\"l-longur-0001\",\"updated\":\"2026-10-10T18:00:00.000Z\",\"lake\":\"BR-29\",\"url\":\"https://e.com/$(printf 'a%.0s' {1..2100})\"}}]}"
ok "url > 2000 chars -> error" '[[ "$R" == *error* && "$R" == *2000* ]]'
post '{"device":"t","docs":[{"kind":"lake","doc":{"id":"x"}},{"kind":"trip","doc":{"id":"t-BAD-1","updated":"x"}},{"kind":"trip","doc":{"id":"t-noupd-0001"}}]}'
ok "bad kind / bad id / missing updated -> 3 errors" '[[ $(echo "$R" | grep -o "\"error\"" | wc -l) -eq 3 ]]'
post "{\"device\":\"t\",\"docs\":[{\"kind\":\"trip\",\"doc\":{\"id\":\"t-toolng-0001\",\"updated\":\"2026-10-10T18:00:00.000Z\",\"title\":\"$(printf 'a%.0s' {1..201})\"}}]}"
ok "title > 200 -> error" '[[ "$R" == *error* && "$R" == *200* ]]'
R=$(curl -s -X POST -H 'Content-Type: application/json' --data 'nope' $H/api/journal)
ok "bad json -> 400 error" '[[ "$R" == *"bad json"* ]]'

post '{"device":"t","docs":[{"kind":"link","doc":{"id":"l-lq2xc1-aaaa","updated":"2026-10-10T19:00:00.000Z","deleted":true,"url":"https://leftover"}}]}'
ok "tombstone applied" '[[ "$R" == *applied* ]]'
ok "tombstone stored minimal" 'python3 -c "import json; d=json.load(open(\"$S/j.json\")); assert d[\"links\"]==[{\"id\":\"l-lq2xc1-aaaa\",\"updated\":\"2026-10-10T19:00:00.000Z\",\"deleted\":True}]"'
post '{"device":"t","docs":[{"kind":"link","doc":{"id":"l-lq2xc1-aaaa","updated":"2026-10-10T18:30:00.000Z","lake":"BR-29","url":"https://example.com/b"}}]}'
ok "stale write can't resurrect a tombstone" '[[ "$R" == *superseded* && "$R" == *deleted* ]]'

R=$(curl -s $H/api/user-data)
ok "user-data carries journal incl. tombstones + media_meta" \
   'echo "$R" | python3 -c "import json,sys; d=json.load(sys.stdin); j=d[\"journal\"]; assert len(j[\"trips\"])==2 and len(j[\"photos\"])==1 and j[\"links\"][0][\"deleted\"]; assert d[\"media_meta\"]=={}; assert \"lakes\" in d"'
post '{"device":"t","docs":[{"kind":"trip","doc":{"id":"t-month1-0001","updated":"2026-10-10T18:00:00.000Z","title":"m","date":"2024-10","end_date":"2024-11"}},{"kind":"trip","doc":{"id":"t-month2-0001","updated":"2026-10-10T18:00:00.000Z","title":"m","date":"2024-10","end_date":"2024-10-05"}},{"kind":"trip","doc":{"id":"t-month3-0001","updated":"2026-10-10T18:00:00.000Z","title":"m","date":"2024-13"}}]}'
ok "month-only date applied; mixed precision + month 13 -> errors" '[[ $(echo "$R" | grep -o "\"applied\"" | wc -l) -eq 1 && $(echo "$R" | grep -o "\"error\"" | wc -l) -eq 2 ]]'

# --- media ---
ID=p-lq2xb1-9d0e
printf '\xff\xd8\xff\xe0fakejpegbody' > $S/f.jpg
R=$(curl -s -X PUT -H 'Content-Type: image/jpeg' --data-binary @$S/f.jpg $H/api/media/$ID.jpg)
ok "PUT full jpg" '[[ "$R" == *\"ok\":\ true* ]] && cmp -s $S/f.jpg $S/media/$ID.jpg'
R=$(curl -s -X PUT -H 'Content-Type: image/jpeg' --data-binary @$S/f.jpg $H/api/media/${ID}_t.jpg)
ok "PUT thumb jpg" '[[ -f $S/media/${ID}_t.jpg ]]'
R=$(curl -s -X PUT -H 'Content-Type: image/jpeg' --data-binary @$S/f.jpg $H/api/media/$ID.jpg)
ok "PUT is idempotent" '[[ "$R" == *\"ok\":\ true* ]]'
ok "no tmp files left in media dir" '[[ $(ls -A $S/media | grep -c tmp) -eq 0 ]]'
R=$(curl -s -D - $H/api/media/$ID.jpg -o $S/got.jpg)
ok "GET full: 200, CORS *, immutable cache, bytes match" '[[ "$R" == *"200"* && "$R" == *"Access-Control-Allow-Origin: *"* && "$R" == *"private, max-age=31536000, immutable"* ]] && cmp -s $S/f.jpg $S/got.jpg'
R=$(curl -s -o /dev/null -w '%{http_code}' $H/api/media/p-nothere-0000_t.jpg)
ok "GET missing -> 404" '[[ "$R" == 404 ]]'
R=$(curl -s -o /dev/null -w '%{http_code}' -X PUT -H 'Content-Type: image/jpeg' --data-binary @$S/f.jpg $H/api/media/x-bad.jpg)
ok "PUT bad id -> 404" '[[ "$R" == 404 ]]'
R=$(curl -s -o /dev/null -w '%{http_code}' -X PUT -H 'Content-Type: image/png' --data-binary @$S/f.jpg $H/api/media/$ID.jpg)
ok "PUT wrong content-type -> 415" '[[ "$R" == 415 ]]'
printf 'notajpeg' > $S/n.jpg
R=$(curl -s -o /dev/null -w '%{http_code}' -X PUT -H 'Content-Type: image/jpeg' --data-binary @$S/n.jpg $H/api/media/$ID.jpg)
ok "PUT non-JPEG bytes -> 415" '[[ "$R" == 415 ]]'
head -c $((12*1024*1024+1)) /dev/zero > $S/big.bin
R=$(curl -s -o /dev/null -w '%{http_code}' -X PUT -H 'Content-Type: image/jpeg' --data-binary @$S/big.bin $H/api/media/p-bigone-0000.jpg)
ok "PUT > 12 MB -> 413, nothing written" '[[ "$R" == 413 ]] && [[ ! -f $S/media/p-bigone-0000.jpg ]]'
R=$(curl -s -o /dev/null -w '%{http_code}' $H/api/ping)
ok "server still healthy after the 413" '[[ "$R" == 200 ]]'

R=$(curl -s -X PUT -H 'Content-Type: application/json' --data '{"lat":40.6912,"lng":-110.8801,"alt":3150.5,"gps_time":"2024:10:13 15:41:00","taken":"2024-10-13T09:41:00","make":"Apple","model":"iPhone 15"}' $H/api/media/$ID.json)
ok "PUT sidecar" '[[ "$R" == *\"ok\":\ true* ]]'
R=$(curl -s -X PUT -H 'Content-Type: application/json' --data '{"lat":91,"lng":0}' $H/api/media/$ID.json)
ok "sidecar lat out of range -> error" '[[ "$R" == *"bad lat"* ]]'
R=$(curl -s -X PUT -H 'Content-Type: application/json' --data '{"lat":40,"lng":-110,"evil":"x"}' $H/api/media/$ID.json)
ok "sidecar extra key -> error" '[[ "$R" == *unexpected* ]]'
R=$(curl -s -o /dev/null -w '%{http_code}' -X PUT -H 'Content-Type: application/json' --data "{\"lat\":40,\"lng\":-110,\"make\":\"$(printf 'a%.0s' {1..5000})\"}" $H/api/media/$ID.json)
ok "sidecar > 4 KB -> 413" '[[ "$R" == 413 ]]'
R=$(curl -s -o /dev/null -w '%{http_code}' $H/api/media/$ID.json)
ok "sidecar NOT fetchable directly" '[[ "$R" == 404 ]]'
R=$(curl -s $H/api/user-data)
ok "user-data media_meta has the (unchanged, valid) sidecar" 'echo "$R" | python3 -c "import json,sys; m=json.load(sys.stdin)[\"media_meta\"]; assert m[\"$ID\"][\"lat\"]==40.6912 and m[\"$ID\"][\"model\"]==\"iPhone 15\""'

# --- static fence ---
for p in /data/push/vapid_private.pem /data/push/ /DATA/PUSH/x //data/push/x /data/./push/x /foo/../data/push/x /data%2fpush/x /data/media/ /data/Media/x.jpg; do
  R=$(curl -s -o /dev/null -w '%{http_code}' --path-as-is "$H$p"); ok "static fence 404: $p" '[[ "$R" == 404 ]]'
done
R=$(curl -s -o /dev/null -w '%{http_code}' -I --path-as-is "$H/data/push/x"); ok "HEAD fenced too" '[[ "$R" == 404 ]]'
R=$(curl -s -o /dev/null -w '%{http_code}' $H/manifest.json); ok "ordinary static file still served" '[[ "$R" == 200 ]]'

# --- link title ---
R=$(curl -s "$H/api/link-title?url=https%3A%2F%2Fjunesucker.com%2Flakes%2Fuintas%2Falexander-lake%2F")
ok "link-title junesucker.com (Cloudflare; network-dependent)" '[[ "$R" == *Alexander* ]]'
R=$(curl -s "$H/api/link-title?url=https%3A%2F%2Fexample.com%2F")
ok "link-title example.com" '[[ "$R" == *"Example Domain"* ]]'
R=$(curl -s "$H/api/link-title?url=http%3A%2F%2F127.0.0.1%3A8899%2Findex.html")
ok "link-title refuses loopback (blank title)" '[[ "$R" == "{\"title\": \"\"}" ]]'
R=$(curl -s -o /dev/null -w '%{http_code}' "$H/api/link-title?url=file%3A%2F%2F%2Fetc%2Fpasswd")
ok "link-title non-http -> 400" '[[ "$R" == 400 ]]'

# --- old endpoint unaffected ---
R=$(curl -s -X POST -H 'Content-Type: application/json' --data '{"device":"t","edits":[{"id":"e1","lake":"BR-25","field":"status","value":"CAUGHT","ts":"2026-10-10T18:00:00.000Z"}]}' $H/api/edits)
ok "/api/edits still applies" '[[ "$R" == *applied* ]]'

echo; echo "server: passed=$pass failed=$fail"
[[ $fail -eq 0 ]]
