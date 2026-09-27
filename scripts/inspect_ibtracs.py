import pandas as pd
from pathlib import Path

csv_path = Path("data/raw/ibtracs/ibtracs_NI_latest.csv")

# IBTrACS row 0 is column headers, row 1 is units
df = pd.read_csv(csv_path, skiprows=[1], low_memory=False)

print("Total observations:", len(df))
print("Available columns:", len(df.columns))

# Filter for recent iconic NIO storms: AMPHAN, FANI, TAUKTAE, YAAS, BIPARJOY
recent_storms = df[df['NAME'].str.upper().isin(['AMPHAN', 'FANI', 'TAUKTAE', 'YAAS', 'BIPARJOY', 'MICHAUNG'])][['SID', 'NAME', 'SEASON', 'ISO_TIME', 'LAT', 'LON', 'WMO_WIND', 'WMO_PRES', 'SUBBASIN', 'NATURE']].dropna(subset=['LAT', 'LON'])

print("\nSummary of recent North Indian Ocean storms found in official NOAA IBTrACS:")
for name, group in recent_storms.groupby('NAME'):
    print(f"- Cyclone {name}: SID={group['SID'].iloc[0]}, Season={group['SEASON'].iloc[0]}, Points={len(group)}, Peak Wind={group['WMO_WIND'].max()} kt, Min Pres={group['WMO_PRES'].min()} mb")
