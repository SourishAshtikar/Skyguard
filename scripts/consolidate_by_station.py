#!/usr/bin/env python3
"""
consolidate_by_station.py - Consolidates yearly NOAA station CSVs into single station historical CSV files.
Part of SkyGuard AI Project (SIH073)

Transforms:
13,166 yearly station CSVs (e.g. 43003099999_1944.csv, 43003099999_1945.csv ...)
-> 543 consolidated station CSVs (e.g. Datasets/noaa_india_by_station/43003099999_MUMBAI_SANTACRUZ.csv)
"""

import os
import glob
import re
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BASE_DIR, "Datasets")
SOURCE_DIR = os.path.join(DATASETS_DIR, "noaa_india_hourly_processed")
TARGET_DIR = os.path.join(DATASETS_DIR, "noaa_india_by_station")

def ensure_dirs():
    os.makedirs(TARGET_DIR, exist_ok=True)

def sanitize_filename(name):
    clean = re.sub(r'[^A-Za-z0-9_]+', '_', str(name)).strip('_')
    return clean[:40]

def consolidate_station(st_id, st_files, inventory_dict):
    st_info = inventory_dict.get(st_id, {})
    st_name = st_info.get('STATION_NAME', 'UNKNOWN')
    clean_name = sanitize_filename(st_name)
    
    out_filename = f"{st_id}_{clean_name}.csv" if clean_name else f"{st_id}.csv"
    out_path = os.path.join(TARGET_DIR, out_filename)
    
    dfs = []
    for f in st_files:
        try:
            df = pd.read_csv(f)
            if not df.empty:
                dfs.append(df)
        except Exception:
            pass
            
    if not dfs:
        return None

    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Sort chronologically by timestamp
    combined_df = combined_df.sort_values(by='timestamp').drop_duplicates(subset=['timestamp'])
    
    combined_df.to_csv(out_path, index=False)
    
    start_year = str(combined_df['timestamp'].iloc[0])[:4]
    end_year = str(combined_df['timestamp'].iloc[-1])[:4]
    
    return {
        'station_id': st_id,
        'station_name': st_name,
        'records': len(combined_df),
        'start_year': start_year,
        'end_year': end_year,
        'file_path': out_path
    }

def main():
    ensure_dirs()
    print("[1/2] Indexing yearly files and station inventory...")
    
    # Read station inventory for metadata
    inventory_path = os.path.join(DATASETS_DIR, "indian_aws_locations.csv")
    inventory_dict = {}
    if os.path.exists(inventory_path):
        inv_df = pd.read_csv(inventory_path, dtype=str)
        for _, row in inv_df.iterrows():
            inventory_dict[row['STATION_ID']] = row.to_dict()

    files = glob.glob(os.path.join(SOURCE_DIR, "*.csv"))
    print(f"Total yearly files to process: {len(files)}")
    
    # Group files by station_id
    grouped_files = {}
    for f in files:
        basename = os.path.basename(f)
        st_id = basename.split('_')[0]
        grouped_files.setdefault(st_id, []).append(f)
        
    print(f"Grouped into {len(grouped_files)} unique Indian weather stations.")
    print(f"[2/2] Merging yearly files into single consolidated CSV per station...")

    results = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(consolidate_station, st_id, st_files, inventory_dict): st_id
            for st_id, st_files in grouped_files.items()
        }
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    print(f"\n[SUCCESS] Successfully consolidated {len(results)} station CSV files under: {TARGET_DIR}")
    
    # Print sample top stations summary
    results_df = pd.DataFrame(results).sort_values(by='records', ascending=False)
    print("\n--- Top Indian Stations Consolidated ---")
    print(results_df[['station_id', 'station_name', 'start_year', 'end_year', 'records']].head(10).to_string(index=False))

if __name__ == "__main__":
    main()
