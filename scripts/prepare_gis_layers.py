import os
import json
import urllib.request
from pathlib import Path

GIS_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "gis"
DISTRICTS_GEOJSON = GIS_DIR / "india_districts.geojson"
INFRA_GEOJSON = GIS_DIR / "infrastructure_assets.geojson"

# Primary and backup URLs for India district boundaries GeoJSON
DISTRICT_SOURCES = [
    "https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist.geojson",
    "https://raw.githubusercontent.com/geohacker/india/master/district/india_district.geojson"
]

def prepare_districts():
    GIS_DIR.mkdir(parents=True, exist_ok=True)
    if DISTRICTS_GEOJSON.exists() and DISTRICTS_GEOJSON.stat().st_size > 50000:
        print(f"India districts GeoJSON already exists: {DISTRICTS_GEOJSON}")
        return True

    print("Attempting to fetch official/curated India districts GeoJSON...")
    for url in DISTRICT_SOURCES:
        try:
            print(f"Trying: {url}")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                # Verify valid json
                parsed = json.loads(data.decode('utf-8'))
                if "features" in parsed and len(parsed["features"]) > 50:
                    with open(DISTRICTS_GEOJSON, 'wb') as f:
                        f.write(data)
                    print(f"Saved {len(parsed['features'])} districts to {DISTRICTS_GEOJSON}")
                    return True
        except Exception as e:
            print(f"Failed from {url}: {e}")

    return False

if __name__ == "__main__":
    prepare_districts()
