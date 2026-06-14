---
name: baidu-map-poi
description: Collect Chinese geographic POI (Points of Interest) data from Baidu Maps without an API key. Anonymous webapp endpoint returns up to 50 results per call with name/address/phone/coordinates. Use for venue/business inventory in mainland China when Gaode is blocked or you need a quick public-data sweep.
version: 1.0.0
author: hermes
license: MIT
metadata:
  hermes:
    tags: [maps, china, scraping, poi, geocoding]
---

# Baidu Map POI Collection

Scrape public Baidu Maps POI search results without an API key. Useful when:
- You need to inventory businesses/venues in a Chinese city
- Gaode (高德) is blocking with `puzzle-captcha`
- You don't want to register a developer key

## Why Baidu over Gaode

| Aspect | Gaode | Baidu (this skill) |
|---|---|---|
| Anti-scraping | Aggressive (puzzle CAPTCHA) | Minimal on webapp endpoint |
| Auth needed | API key required | None |
| Result limit | 25/page via API | ~10/page anonymous, paginate 0-5+ |
| Coordinates | GCJ02 native | BD09MC (Mercator) — needs conversion |

## Endpoint

```
GET https://map.baidu.com/?newmap=1&reqflag=pcmap&biz=1&from=webmap&qt=s
    &da_par=direct&pcevaname=pc4.1
    &wd=KEYWORD              # e.g. "深圳羽毛球馆"
    &c=340                   # city code: 340=Shenzhen, 131=Beijing, 289=Shanghai, 257=Guangzhou
    &src=0&wd2=&pn=PAGE      # 0-based page index
    &sug=0&l=11&b=()&from=webmap&biz_forward={}&sug_forward=
    &auth=...
    &device_ratio=2
```

Set headers:
```
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...
Referer: https://map.baidu.com/
```

Response is JSON with `content` array. Each item has:
- `name` — POI name
- `addr` — address
- `tel` — phone (sometimes)
- `uid` — Baidu's stable POI id (use for dedup)
- `x`, `y` — coordinates in **BD09MC Mercator projection** (must convert)
- `area_name` — district name (extracted via regex from `addr`)
- `std_tag` — category tag

## City codes (`c=` parameter)

Common cities:
- 131 北京 / 257 广州 / 289 上海 / 340 深圳 / 218 成都 / 224 武汉
- 158 杭州 / 179 南京 / 233 西安 / 132 天津 / 75 苏州 / 167 重庆

Full list: search `baidu map city code china` or inspect requests in browser DevTools.

## Coordinate conversion (CRITICAL)

Baidu returns BD09MC (墨卡托). To get usable lat/lng for Notion/Google/leaflet:

**Step 1: BD09MC → BD09LL** (use Baidu's 6-segment polynomial inverse)

```python
MCBAND = [12890594.86, 8362377.87, 5591021, 3481989.83, 1678043.12, 0]
LLBAND = [75, 60, 45, 30, 15, 0]
MC2LL = [
    [-0.0015702102444, 111320.7020616939, 1704480524535203, -10338987376042340, 26112667856603880, -35149669176653700, 26595700718403920, -10725012454188240, 1800819912950474, 82.5],
    [0.0008277824516172526, 111320.7020463578, 647795574.6671607, -4082003173.641316, 10774905663.51142, -15171875531.51559, 12053065338.62167, -5124939663.577472, 913311935.9512032, 67.5],
    [0.00337398766765, 111320.7020202162, 4481351.045890365, -23393751.19931662, 79682215.47186455, -115964993.2797253, 97236711.15602145, -43661946.33752821, 8477230.501135234, 52.5],
    [0.00220636496208, 111320.7020209128, 51751.86112841131, 3796837.749470245, 992013.7397791013, -1221952.21711287, 1340652.697009075, -620943.6990984312, 144416.9293806241, 37.5],
    [-0.0003441963504368392, 111320.7020576856, 278.2353980772752, 2485758.690035394, 6070.750963243378, 54821.18345352118, 9540.606633304236, -2710.55326746645, 1405.483844121726, 22.5],
    [-0.0003218135878613132, 111320.7020701615, 0.00369383431289, 823725.6402795718, 0.46104986909093, 2351.343141331292, 1.58060784298199, 8.77738589078284, 0.37238884252424, 7.45]
]

def bd09mc_to_bd09ll(x, y):
    for i, lb in enumerate(MCBAND):
        if abs(y) >= lb:
            cE = MC2LL[i]
            break
    return _convertor(x, y, cE)

def _convertor(x, y, cE):
    cF = cE[0] + cE[1] * abs(x)
    cG = abs(y) / cE[9]
    cH = cE[2] + cE[3]*cG + cE[4]*cG**2 + cE[5]*cG**3 + cE[6]*cG**4 + cE[7]*cG**5 + cE[8]*cG**6
    lng = cF * (1 if x >= 0 else -1)
    lat = cH * (1 if y >= 0 else -1)
    return lng, lat
```

**Step 2 (optional): BD09LL → GCJ02** (Baidu adds an extra offset on top of GCJ02)

```python
import math
PI_X = math.pi * 3000.0 / 180.0

def bd09ll_to_gcj02(bd_lng, bd_lat):
    x = bd_lng - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x*x + y*y) - 0.00002 * math.sin(y * PI_X)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * PI_X)
    return z * math.cos(theta), z * math.sin(theta)
```

**Step 3 (optional): GCJ02 → WGS84** if you need true global standard (Google Maps outside China, OpenStreetMap). Skip if data stays in China apps.

**Sanity check**: for Shenzhen, valid lng ∈ [113.7, 114.7], lat ∈ [22.4, 22.9]. If you see numbers like `1e+31`, your conversion is wrong — debug Step 1 first.

## Pagination & dedup pattern

```python
import urllib.request, urllib.parse, json, time, csv

CITY_CODE = 340  # Shenzhen
KEYWORDS = ["羽毛球馆", "羽毛球场", "羽毛球俱乐部"]
DISTRICTS = ["福田", "南山", "罗湖", "宝安", "龙岗", "龙华", "盐田", "光明", "坪山", "大鹏"]

seen_uids = set()
results = []

for kw in KEYWORDS:
    for district in [""] + DISTRICTS:  # global + per-district sweeps
        query = f"{district}{kw}" if district else kw
        for page in range(6):  # 0..5
            url = (f"https://map.baidu.com/?newmap=1&reqflag=pcmap&biz=1"
                   f"&from=webmap&qt=s&da_par=direct&pcevaname=pc4.1"
                   f"&wd={urllib.parse.quote(query)}&c={CITY_CODE}&src=0"
                   f"&wd2=&pn={page}&sug=0&l=11&b=()&from=webmap"
                   f"&biz_forward=%7B%22scaler%22:2,%22styles%22:%22pl%22%7D"
                   f"&sug_forward=&device_ratio=2")
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 ...",
                "Referer": "https://map.baidu.com/",
            })
            try:
                data = json.loads(urllib.request.urlopen(req, timeout=10).read())
            except Exception as e:
                print(f"skip {query} pn={page}: {e}")
                continue
            for item in data.get("content", []):
                uid = item.get("uid")
                if not uid or uid in seen_uids:
                    continue
                seen_uids.add(uid)
                x, y = item.get("x"), item.get("y")
                if x and y:
                    # Baidu returns x,y * 100 in some responses — check magnitude
                    if abs(x) > 1e9:
                        x, y = x / 100, y / 100
                    lng, lat = bd09mc_to_bd09ll(x, y)
                else:
                    lng = lat = None
                results.append({
                    "name": item.get("name"),
                    "addr": item.get("addr"),
                    "tel": item.get("tel", ""),
                    "uid": uid,
                    "lng": lng,
                    "lat": lat,
                    "tag": item.get("std_tag", ""),
                })
            time.sleep(0.4)  # be polite

print(f"collected {len(results)} unique POIs")
```

## Noise filtering

POI search returns lots of unrelated entries (training centers, equipment stores, restringing shops). Filter by negative keywords in `name` and `tag`:

```python
NOISE = ["用品", "穿线", "培训中心", "球拍", "卖场", "器材", "装备", "教练"]
clean = [r for r in results if not any(n in (r["name"] + r["tag"]) for n in NOISE)]
```

## Quotas allocation when bulk-writing to a database

If your downstream system (Notion, Airtable) charges per row or you want balanced coverage, allocate per-district quotas by population density rather than raw POI count. Example for Shenzhen badminton (target ~120 venues across 10 districts):

```python
QUOTA = {"福田":14, "南山":18, "罗湖":15, "宝安":18, "龙岗":18, "龙华":15, "盐田":8, "光明":12, "坪山":10, "大鹏":6}
# then within each district, sort by Baidu rating descending, take top N
```

## Pitfalls

1. **`x` and `y` magnitude varies**: sometimes Baidu returns MC * 100, sometimes raw. Always sanity-check: Shenzhen MC `x` should be ~12,680,000–12,780,000. If you see `1.27e9`, divide by 100.

2. **District extraction**: Baidu's `area_name` may be empty. Fall back to regex on `addr`: `re.search(r"(福田|南山|罗湖|宝安|龙岗|龙华|盐田|光明|坪山|大鹏)", addr)`.

3. **Anti-bot**: if you see HTML instead of JSON, you've been rate-limited. Add `time.sleep(0.5)` between calls and rotate User-Agent.

4. **Phone fields often empty**: only ~30% of POIs have `tel`. Don't assume.

5. **Stale POIs**: Baidu data lags ~3-12 months. Verify hot venues with a separate channel before publishing.

6. **`c=` code matters**: passing the wrong city code returns POIs from random cities. Always verify `area_name` contains expected district names.

## Verification

After scraping, spot-check 3 random POIs:
- Open `https://map.baidu.com/?wd={uid}` — should resolve to the same place
- Cross-check coordinates: paste `lat,lng` into Google Maps or AMap, confirm location matches address

## Legal note

Public POI display is allowed under Baidu Maps ToS for personal/research use. Don't:
- Rebuild a commercial map product directly from this data
- Hit the endpoint faster than ~3 req/s
- Republish coordinates without attribution

For commercial use, get an official Baidu/Gaode API key.
