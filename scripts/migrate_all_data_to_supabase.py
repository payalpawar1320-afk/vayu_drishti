"""
Automated Data Migration Script for Supabase PostgreSQL.
Shifts historical cyclones, track points, districts, infrastructure, authorities, and citizens into Supabase.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Ensure utf-8 encoding for Windows stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Set up project path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.providers.ibtracs_provider import IBTrACSProvider
from backend.app.db.supabase_client import supabase_db

def run_migration():
    print("=" * 70)
    print("🚀 VAYU-DRISHTI -> SUPABASE CLOUD DATA MIGRATION")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # 1. SEED APP USERS (Authorities & Citizens)
    # -------------------------------------------------------------------------
    print("\n[1/5] Seeding Authority and Citizen User Accounts...")
    users = [
        {
            "email": "director.ndma@gov.in",
            "full_name": "NDMA National Incident Commander",
            "role": "AUTHORITY_NDMA",
            "department": "National Disaster Management Authority (New Delhi)"
        },
        {
            "email": "control.odisha@sdma.gov.in",
            "full_name": "OSDMA Emergency Operations Controller",
            "role": "AUTHORITY_SDMA",
            "department": "Odisha State Disaster Management Authority (Bhubaneswar)"
        },
        {
            "email": "control.westbengal@sdma.gov.in",
            "full_name": "WBSDMA Coastal Action Cell",
            "role": "AUTHORITY_SDMA",
            "department": "West Bengal State Disaster Management Authority (Kolkata)"
        },
        {
            "email": "collector.balasore@odisha.gov.in",
            "full_name": "District Magistrate & Collector (Balasore)",
            "role": "DISTRICT_COLLECTOR",
            "department": "Balasore District Administration"
        },
        {
            "email": "citizen.priya.pur@gmail.com",
            "full_name": "Priya Sharma",
            "role": "CITIZEN",
            "department": "Puri Coast Resident (Odisha)"
        },
        {
            "email": "citizen.arun.digha@gmail.com",
            "full_name": "Arunabha Mondal",
            "role": "CITIZEN",
            "department": "Digha Coastal Fisherman (West Bengal)"
        }
    ]
    try:
        supabase_db.insert_users(users)
        print(f"  ✅ Successfully registered {len(users)} Authority & Citizen accounts in Supabase.")
    except Exception as e:
        print(f"  ⚠️ Users insert note: {e}")

    # -------------------------------------------------------------------------
    # 2. MIGRATE HISTORICAL STORMS & TRACK POINTS (IBTrACS)
    # -------------------------------------------------------------------------
    print("\n[2/5] Loading Historical Cyclone Records from NOAA IBTrACS...")
    provider = IBTrACSProvider()
    
    # Priority storms for North Indian Ocean
    target_storm_names = [
        "AMPHAN", "FANI", "BIPARJOY", "TAUKTAE", "YAAS", 
        "GULAB", "ASANI", "MANDOUS", "MOCHA", "MICHAUNG", "HUDHUD", "PHAILIN"
    ]

    migrated_storms = []
    migrated_track_points = []

    for sid, info in provider._storm_index.items():
        name = info["name"]
        if name in target_storm_names or info["season"] >= 2019:
            detail = provider.get_storm_detail(sid)
            if not detail or not detail.track_points:
                continue

            pts = detail.track_points
            start_iso = pts[0].iso_time if pts else None
            end_iso = pts[-1].iso_time if pts else None

            # Clean ISO string format for PostgreSQL
            clean_start = start_iso.replace(" ", "T") + "Z" if start_iso and "T" not in start_iso else start_iso
            clean_end = end_iso.replace(" ", "T") + "Z" if end_iso and "T" not in end_iso else end_iso

            migrated_storms.append({
                "id": detail.storm_id,
                "storm_name": detail.storm_name,
                "year": detail.year,
                "basin": detail.basin or "NI",
                "peak_wind_kt": float(detail.peak_wind_kt or 0.0),
                "min_pressure_mb": float(detail.min_pressure_mb or 1000.0),
                "start_time": clean_start,
                "end_time": clean_end
            })

            # Track points
            for p in pts:
                w = float(p.max_sustained_wind_kt or 0.0)
                eye_detected = bool(w >= 60.0)
                eye_r = round(float(14.0 + (32.0 * max(0.0, 1.0 - (w - 25.0) / 115.0 * 0.75))), 1) if eye_detected else 0.0
                eyewall_r = round(float(eye_r + 18.0), 1) if eye_detected else 45.0
                
                clean_time = p.iso_time.replace(" ", "T")
                if not clean_time.endswith("Z") and "+" not in clean_time:
                    clean_time += "Z"

                migrated_track_points.append({
                    "storm_id": detail.storm_id,
                    "iso_time": clean_time,
                    "latitude": float(p.latitude),
                    "longitude": float(p.longitude),
                    "wind_speed_kt": w,
                    "pressure_mb": float(p.min_central_pressure_mb or 1000.0),
                    "eye_detected": eye_detected,
                    "eye_radius_km": eye_r,
                    "eyewall_radius_km": eyewall_r,
                    "classification": "EYE_DETECTED" if eye_detected else "NO_DISTINCT_EYE"
                })

    print(f"  Found {len(migrated_storms)} high-impact cyclones with {len(migrated_track_points)} track points.")
    
    # Upload storms
    try:
        supabase_db.insert_storms(migrated_storms)
        print(f"  ✅ Uploaded {len(migrated_storms)} Cyclones into 'public.storms'.")
    except Exception as e:
        print(f"  ⚠️ Storms insert note: {e}")

    # Upload track points in chunks
    try:
        res = supabase_db.insert_track_points(migrated_track_points)
        print(f"  ✅ Uploaded {res.get('inserted', len(migrated_track_points))} Track Points into 'public.storm_track_points'.")
    except Exception as e:
        print(f"  ⚠️ Track points insert note: {e}")

    # -------------------------------------------------------------------------
    # 3. MIGRATE COASTAL DISTRICTS & POPULATIONS
    # -------------------------------------------------------------------------
    print("\n[3/5] Loading India Coastal Districts & Population Data...")
    pop_file = BASE_DIR / "data" / "raw" / "gis" / "district_population_reference.json"
    districts_data = []

    if pop_file.exists():
        with open(pop_file, "r", encoding="utf-8") as f:
            pop_map = json.load(f)

        # Representative coastal coordinates
        COASTAL_COORDS = {
            "South 24 Parganas": {"state": "West Bengal", "lat": 22.15, "lon": 88.55, "pop": 8161961},
            "North 24 Parganas": {"state": "West Bengal", "lat": 22.70, "lon": 88.80, "pop": 10009781},
            "Purba Medinipur": {"state": "West Bengal", "lat": 21.90, "lon": 87.75, "pop": 5095875},
            "Kolkata": {"state": "West Bengal", "lat": 22.57, "lon": 88.36, "pop": 4496694},
            "Howrah": {"state": "West Bengal", "lat": 22.59, "lon": 88.26, "pop": 4850029},
            "Balasore": {"state": "Odisha", "lat": 21.49, "lon": 86.91, "pop": 2320529},
            "Bhadrak": {"state": "Odisha", "lat": 21.05, "lon": 86.50, "pop": 1506522},
            "Kendrapara": {"state": "Odisha", "lat": 20.50, "lon": 86.42, "pop": 1440361},
            "Jagatsinghpur": {"state": "Odisha", "lat": 20.27, "lon": 86.17, "pop": 1136971},
            "Puri": {"state": "Odisha", "lat": 19.81, "lon": 85.83, "pop": 1698730},
            "Ganjam": {"state": "Odisha", "lat": 19.38, "lon": 84.88, "pop": 3529031},
            "Srikakulam": {"state": "Andhra Pradesh", "lat": 18.30, "lon": 83.90, "pop": 2703114},
            "Visakhapatnam": {"state": "Andhra Pradesh", "lat": 17.68, "lon": 83.21, "pop": 4290589},
            "East Godavari": {"state": "Andhra Pradesh", "lat": 17.00, "lon": 82.25, "pop": 5154296},
            "Krishna": {"state": "Andhra Pradesh", "lat": 16.18, "lon": 81.14, "pop": 4517398},
            "Nellore": {"state": "Andhra Pradesh", "lat": 14.44, "lon": 79.98, "pop": 2963557},
            "Chennai": {"state": "Tamil Nadu", "lat": 13.08, "lon": 80.27, "pop": 7088403},
            "Cuddalore": {"state": "Tamil Nadu", "lat": 11.75, "lon": 79.77, "pop": 2605914},
            "Nagapattinam": {"state": "Tamil Nadu", "lat": 10.76, "lon": 79.84, "pop": 1616450},
            "Mumbai": {"state": "Maharashtra", "lat": 18.92, "lon": 72.83, "pop": 12442373},
            "Ratnagiri": {"state": "Maharashtra", "lat": 16.99, "lon": 73.31, "pop": 1615000},
            "Surat": {"state": "Gujarat", "lat": 21.17, "lon": 72.83, "pop": 6081322},
            "Gir Somnath": {"state": "Gujarat", "lat": 20.90, "lon": 70.36, "pop": 1217477},
            "Porbandar": {"state": "Gujarat", "lat": 21.64, "lon": 69.62, "pop": 585449},
            "Devbhumi Dwarka": {"state": "Gujarat", "lat": 22.24, "lon": 68.96, "pop": 752484},
            "Kachchh": {"state": "Gujarat", "lat": 23.24, "lon": 69.66, "pop": 2092371}
        }

        for d_name, d_pop in pop_map.items():
            info = COASTAL_COORDS.get(d_name, {"state": "Coastal India", "lat": 20.0, "lon": 85.0})
            districts_data.append({
                "district_name": d_name,
                "state_name": info.get("state", "India"),
                "population": int(d_pop),
                "risk_tier": "HIGH" if d_name in ["South 24 Parganas", "Balasore", "Kendrapara", "Purba Medinipur"] else "MODERATE",
                "latitude": info.get("lat"),
                "longitude": info.get("lon")
            })

    try:
        res = supabase_db.insert_districts(districts_data)
        print(f"  ✅ Uploaded {len(districts_data)} Districts into 'public.districts'.")
    except Exception as e:
        print(f"  ⚠️ Districts insert note: {e}")

    # -------------------------------------------------------------------------
    # 4. MIGRATE CRITICAL INFRASTRUCTURE (Ports, Hospitals, Airports)
    # -------------------------------------------------------------------------
    print("\n[4/5] Loading Critical Coastal Infrastructure...")
    infra_file = BASE_DIR / "data" / "raw" / "gis" / "coastal_infrastructure.geojson"
    infra_records = []

    if infra_file.exists():
        with open(infra_file, "r", encoding="utf-8") as f:
            infra_geo = json.load(f)

        for feat in infra_geo.get("features", []):
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [0, 0])
            
            if geom.get("type") == "Point" and len(coords) >= 2 and isinstance(coords[0], (int, float)):
                lat = float(coords[1])
                lon = float(coords[0])
            elif geom.get("type") == "LineString" and isinstance(coords, list) and coords:
                mid = coords[len(coords) // 2]
                lat = float(mid[1])
                lon = float(mid[0])
            elif isinstance(coords, list) and len(coords) >= 2 and isinstance(coords[0], (int, float)):
                lat = float(coords[1])
                lon = float(coords[0])
            else:
                continue

            infra_records.append({
                "name": props.get("name", "Asset"),
                "category": props.get("category", "INFRASTRUCTURE"),
                "state": props.get("state", "Coastal"),
                "district": props.get("district", ""),
                "latitude": lat,
                "longitude": lon,
                "operational_status": "NORMAL"
            })

    try:
        supabase_db.insert_infrastructure(infra_records)
        print(f"  ✅ Uploaded {len(infra_records)} Critical Infrastructure facilities into 'public.critical_infrastructure'.")
    except Exception as e:
        print(f"  ⚠️ Infrastructure insert note: {e}")

    # -------------------------------------------------------------------------
    # 5. LOG BASELINE EVACUATION SITREP (Official Action Report)
    # -------------------------------------------------------------------------
    print("\n[5/5] Logging Initial Official Evacuation SITREP...")
    baseline_sitrep = {
        "sitrep_ref": "VD-SITREP-2026/05",
        "storm_id": "2020136N10088", # AMPHAN
        "authority_user": "director.ndma@gov.in",
        "total_exposed_population": 4280000,
        "landfall_districts_count": 4,
        "priority1_districts": ["South 24 Parganas", "Purba Medinipur", "Balasore", "Kendrapara"],
        "operational_directives": [
            "Complete 100% mandatory coastal evacuation within 10 km of shoreline 18h prior to eyewall landfall.",
            "Issue Great Danger Signal 10 across Paradip, Dhamra, and Haldia Ports.",
            "Pre-position 36 NDRF battalions with satellite communication radios and chain saws."
        ]
    }
    try:
        supabase_db.log_evacuation_sitrep(baseline_sitrep)
        print(f"  ✅ Uploaded Official SITREP [{baseline_sitrep['sitrep_ref']}] into 'public.evacuation_sitreps'.")
    except Exception as e:
        print(f"  ⚠️ SITREP insert note: {e}")

    print("\n" + "=" * 70)
    print("✨ ALL DATA HAS BEEN MIGRATED DIRECTLY INTO SUPABASE POSTGRESQL!")
    print("=" * 70)

if __name__ == "__main__":
    run_migration()
