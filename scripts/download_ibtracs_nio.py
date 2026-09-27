import os
import urllib.request
from pathlib import Path

# Correct official URL with 'access/csv'
IBTRACS_NI_URL = "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NI.list.v04r01.csv"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "ibtracs"
TARGET_CSV = OUTPUT_DIR / "ibtracs_NI_latest.csv"

def download_ibtracs_nio():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Target file: {TARGET_CSV}")
    
    if TARGET_CSV.exists() and TARGET_CSV.stat().st_size > 10000:
        print(f"IBTrACS North Indian Ocean dataset already cached locally ({TARGET_CSV.stat().st_size} bytes).")
        return TARGET_CSV

    print(f"Downloading official NOAA IBTrACS NI dataset from:\n  {IBTRACS_NI_URL}")
    req = urllib.request.Request(
        IBTRACS_NI_URL,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req, timeout=60) as response, open(TARGET_CSV, 'wb') as out_file:
        data = response.read()
        out_file.write(data)
    print(f"Download complete! Saved {len(data)} bytes to {TARGET_CSV}")
    return TARGET_CSV

if __name__ == "__main__":
    download_ibtracs_nio()
