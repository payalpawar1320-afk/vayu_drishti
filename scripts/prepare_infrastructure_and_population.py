import json
from pathlib import Path

GIS_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "gis"

# Verified Census 2011 population data for coastal & cyclone vulnerable districts (in persons)
# Reference: Census of India / WorldPop India District Aggregations
POPULATION_DATA = {
    # West Bengal
    "South 24 Parganas": 8161961,
    "North 24 Parganas": 10009781,
    "East Midnapore": 5095875,
    "West Midnapore": 5913457,
    "Haora": 4850029,
    "Hugli": 5519145,
    "Kolkata": 4496694,
    "Nadia": 5167600,
    # Odisha
    "Baleshwar": 2317419,
    "Bhadrak": 1506522,
    "Kendrapara": 1440218,
    "Jagatsinghpur": 1136971,
    "Puri": 1698730,
    "Ganjam": 3529031,
    "Cuttack": 2624470,
    "Khordha": 2251673,
    "Jajapur": 1826275,
    "Mayurbhanj": 2519738,
    # Andhra Pradesh
    "Srikakulam": 2703114,
    "Vizianagaram": 2344474,
    "Visakhapatnam": 4290586,
    "East Godavari": 5154296,
    "West Godavari": 3936966,
    "Krishna": 4517398,
    "Guntur": 4887813,
    "Prakasam": 3397448,
    "Sri Potti Sriramulu Nellore": 2963557,
    # Tamil Nadu
    "Chennai": 4646732,
    "Tiruvallur": 3728104,
    "Kancheepuram": 3998252,
    "Cuddalore": 2605914,
    "Nagapattinam": 1616450,
    "Thanjavur": 2405890,
    "Ramanathapuram": 1353445,
    # Gujarat
    "Kachchh": 2092371,
    "Jamnagar": 2160119,
    "Porbandar": 585449,
    "Junagadh": 2743082,
    "Bhavnagar": 2880365,
    "Amreli": 1514190,
    "Devbhumi Dwarka": 752484,
    "Gir Somnath": 1217477,
    # Maharashtra
    "Mumbai": 3085411,
    "Mumbai Suburban": 9356962,
    "Thane": 11060148,
    "Palghar": 2990116,
    "Raigarh": 2634200,
    "Ratnagiri": 1615069,
    "Sindhudurg": 849651
}

# Real critical infrastructure coordinates and metadata (Ports, Airports, Hospitals, Key Highways)
INFRASTRUCTURE_FEATURES = [
    # Major Ports
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [88.0833, 22.0333]}, "properties": {"name": "Haldia Port", "category": "PORT", "state": "West Bengal", "district": "East Midnapore"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [88.3128, 22.5444]}, "properties": {"name": "Kolkata Port (Syama Prasad Mookerjee)", "category": "PORT", "state": "West Bengal", "district": "Kolkata"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [86.6800, 20.2600]}, "properties": {"name": "Paradip Port", "category": "PORT", "state": "Odisha", "district": "Jagatsinghpur"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [86.9744, 20.8033]}, "properties": {"name": "Dhamra Port", "category": "PORT", "state": "Odisha", "district": "Bhadrak"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [83.2847, 17.6975]}, "properties": {"name": "Visakhapatnam Port", "category": "PORT", "state": "Andhra Pradesh", "district": "Visakhapatnam"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [80.2974, 13.0850]}, "properties": {"name": "Chennai Port", "category": "PORT", "state": "Tamil Nadu", "district": "Chennai"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [70.2198, 23.0033]}, "properties": {"name": "Kandla (Deendayal) Port", "category": "PORT", "state": "Gujarat", "district": "Kachchh"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [72.9500, 18.9500]}, "properties": {"name": "Jawaharlal Nehru Port (JNPT)", "category": "PORT", "state": "Maharashtra", "district": "Raigarh"}},

    # Major Airports
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [88.4467, 22.6547]}, "properties": {"name": "Netaji Subhash Chandra Bose Intl Airport", "category": "AIRPORT", "state": "West Bengal", "district": "North 24 Parganas"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [85.8178, 20.2444]}, "properties": {"name": "Biju Patnaik International Airport", "category": "AIRPORT", "state": "Odisha", "district": "Khordha"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [83.2245, 17.7212]}, "properties": {"name": "Visakhapatnam International Airport", "category": "AIRPORT", "state": "Andhra Pradesh", "district": "Visakhapatnam"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [80.1693, 12.9941]}, "properties": {"name": "Chennai International Airport", "category": "AIRPORT", "state": "Tamil Nadu", "district": "Chennai"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [72.8679, 19.0896]}, "properties": {"name": "Chhatrapati Shivaji Maharaj Intl Airport", "category": "AIRPORT", "state": "Maharashtra", "district": "Mumbai Suburban"}},

    # Major Trauma & Healthcare Facilities
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [88.3426, 22.5385]}, "properties": {"name": "SSKM Hospital & IPGMER", "category": "HOSPITAL", "beds": 1775, "state": "West Bengal", "district": "Kolkata"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [88.2045, 21.8211]}, "properties": {"name": "Kakdwip Sub-Divisional Hospital (Coastal)", "category": "HOSPITAL", "beds": 250, "state": "West Bengal", "district": "South 24 Parganas"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [87.9254, 21.6266]}, "properties": {"name": "Digha State General Hospital", "category": "HOSPITAL", "beds": 150, "state": "West Bengal", "district": "East Midnapore"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [85.7766, 20.2312]}, "properties": {"name": "AIIMS Bhubaneswar", "category": "HOSPITAL", "beds": 960, "state": "Odisha", "district": "Khordha"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [86.9324, 21.4921]}, "properties": {"name": "Fakir Mohan Medical College & Hospital", "category": "HOSPITAL", "beds": 650, "state": "Odisha", "district": "Baleshwar"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [86.5123, 21.0543]}, "properties": {"name": "Bhadrak District Headquarters Hospital", "category": "HOSPITAL", "beds": 350, "state": "Odisha", "district": "Bhadrak"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [85.8312, 19.8134]}, "properties": {"name": "Puri District Headquarters Hospital", "category": "HOSPITAL", "beds": 420, "state": "Odisha", "district": "Puri"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [83.3045, 17.7123]}, "properties": {"name": "King George Hospital", "category": "HOSPITAL", "beds": 1200, "state": "Andhra Pradesh", "district": "Visakhapatnam"}},

    # Strategic Coastal National Highways
    {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[88.3639, 22.5726], [87.9167, 22.0000], [86.9324, 21.4921], [85.8178, 20.2444], [83.2245, 17.7212], [80.2707, 13.0827]]}, "properties": {"name": "NH-16 (Golden Quadrilateral Coastal Corridor)", "category": "HIGHWAY", "length_km": 1530.0}}
]

def build_data():
    GIS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save population reference
    pop_file = GIS_DIR / "district_population_reference.json"
    with open(pop_file, "w", encoding="utf-8") as f:
        json.dump(POPULATION_DATA, f, indent=2)
    print(f"Saved {len(POPULATION_DATA)} district population references to {pop_file}")

    # Save infrastructure GeoJSON
    infra_file = GIS_DIR / "coastal_infrastructure.geojson"
    geojson = {
        "type": "FeatureCollection",
        "features": INFRASTRUCTURE_FEATURES
    }
    with open(infra_file, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2)
    print(f"Saved {len(INFRASTRUCTURE_FEATURES)} infrastructure features to {infra_file}")

if __name__ == "__main__":
    build_data()
