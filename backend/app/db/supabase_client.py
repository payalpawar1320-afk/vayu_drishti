"""
Supabase Database Client & Repository Layer for VAYU-DRISHTI.
Provides clean REST-based PostgreSQL operations without requiring heavy native drivers.
"""

import os
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
# Load .env without external dependencies
base_dir = Path(__file__).resolve().parents[3]
env_path = base_dir / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()


SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gskfrlfiddesajleotxh.supabase.co").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")

class SupabaseService:
    def __init__(self, url: str = SUPABASE_URL, key: str = SUPABASE_KEY):
        self.url = url
        self.key = key
        self.rest_url = f"{self.url}/rest/v1"
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation,resolution=merge-duplicates"
        }

    def _check_config(self):
        if not self.key or not self.url:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be configured in .env")

    # =========================================================================
    # STORMS & TRACK POINTS
    # =========================================================================
    def insert_storms(self, storms: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._check_config()
        res = requests.post(f"{self.rest_url}/storms", headers=self.headers, json=storms)
        res.raise_for_status()
        return {"inserted": len(storms)}

    def insert_track_points(self, points: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._check_config()
        # PostgREST handles batch inserts in chunks of 500
        chunk_size = 500
        total = 0
        for i in range(0, len(points), chunk_size):
            chunk = points[i:i + chunk_size]
            res = requests.post(f"{self.rest_url}/storm_track_points", headers=self.headers, json=chunk)
            res.raise_for_status()
            total += len(chunk)
        return {"inserted": total}

    def get_storms(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        self._check_config()
        url = f"{self.rest_url}/storms?select=*"
        if year:
            url += f"&year=eq.{year}"
        url += "&order=start_time.desc"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        return res.json()

    def get_storm_detail(self, storm_id: str) -> Optional[Dict[str, Any]]:
        self._check_config()
        url = f"{self.rest_url}/storms?id=eq.{storm_id}&select=*,storm_track_points(*)"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        items = res.json()
        return items[0] if items else None

    # =========================================================================
    # DISTRICTS & INFRASTRUCTURE
    # =========================================================================
    def insert_districts(self, districts: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._check_config()
        chunk_size = 500
        total = 0
        for i in range(0, len(districts), chunk_size):
            chunk = districts[i:i + chunk_size]
            res = requests.post(f"{self.rest_url}/districts", headers=self.headers, json=chunk)
            res.raise_for_status()
            total += len(chunk)
        return {"inserted": total}

    def get_districts(self) -> List[Dict[str, Any]]:
        self._check_config()
        res = requests.get(f"{self.rest_url}/districts?select=*&order=population.desc", headers=self.headers)
        res.raise_for_status()
        return res.json()

    def insert_infrastructure(self, infra_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._check_config()
        res = requests.post(f"{self.rest_url}/critical_infrastructure", headers=self.headers, json=infra_list)
        res.raise_for_status()
        return {"inserted": len(infra_list)}

    def get_infrastructure(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        self._check_config()
        url = f"{self.rest_url}/critical_infrastructure?select=*"
        if category:
            url += f"&category=eq.{category}"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        return res.json()

    # =========================================================================
    # EVACUATION SITREPS (AUTHORITY ACTIONS)
    # =========================================================================
    def log_evacuation_sitrep(self, sitrep_data: Dict[str, Any]) -> Dict[str, Any]:
        self._check_config()
        res = requests.post(f"{self.rest_url}/evacuation_sitreps", headers=self.headers, json=sitrep_data)
        res.raise_for_status()
        return res.json()

    def get_evacuation_sitreps(self) -> List[Dict[str, Any]]:
        self._check_config()
        res = requests.get(f"{self.rest_url}/evacuation_sitreps?select=*&order=pdf_generated_at.desc", headers=self.headers)
        res.raise_for_status()
        return res.json()

    # =========================================================================
    # CITIZEN SOS & ALERTS (CITIZEN ACTIONS)
    # =========================================================================
    def create_citizen_sos(self, sos_data: Dict[str, Any]) -> Dict[str, Any]:
        self._check_config()
        res = requests.post(f"{self.rest_url}/citizen_sos_alerts", headers=self.headers, json=sos_data)
        res.raise_for_status()
        return res.json()

    def get_citizen_sos_alerts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        self._check_config()
        url = f"{self.rest_url}/citizen_sos_alerts?select=*&order=created_at.desc"
        if status:
            url += f"&status=eq.{status}"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        return res.json()

    # =========================================================================
    # USERS (AUTHORITIES & CITIZENS)
    # =========================================================================
    def insert_users(self, users: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._check_config()
        res = requests.post(f"{self.rest_url}/app_users", headers=self.headers, json=users)
        res.raise_for_status()
        return {"inserted": len(users)}

    def get_users(self) -> List[Dict[str, Any]]:
        self._check_config()
        res = requests.get(f"{self.rest_url}/app_users?select=*", headers=self.headers)
        res.raise_for_status()
        return res.json()

# Global Singleton
supabase_db = SupabaseService()
