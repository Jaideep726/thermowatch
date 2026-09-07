import requests, json

name = 'uttarakhand'
s, w, n, e = (29.5, 78.0, 31.0, 80.0)
OVERPASS_URL = 'https://overpass-api.de/api/interpreter'
query = f"""
[out:json][timeout:90];
(
  way["landuse"="industrial"]({s},{w},{n},{e});
  relation["landuse"="industrial"]({s},{w},{n},{e});
  node["industrial"="factory"]({s},{w},{n},{e});
);
out center;
"""
headers = {'User-Agent': 'ThermoWatch-Script/1.0', 'Accept': '*/*'}
r = requests.post(OVERPASS_URL, data={'data': query}, headers=headers, timeout=120)
if r.status_code == 200:
    data = r.json()
    sites = []
    for el in data['elements']:
        lat = el.get('center', {}).get('lat') or el.get('lat')
        lon = el.get('center', {}).get('lon') or el.get('lon')
        if lat:
            sites.append({'lat': lat, 'lon': lon})
    with open(f'data/processed/{name}_osm_industrial.json', 'w') as f:
        json.dump(sites, f)
    print(f'OK -- {len(sites)} sites')
else:
    print(f'ERROR {r.status_code} {r.text[:100]}')
