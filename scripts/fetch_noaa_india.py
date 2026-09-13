#!/usr/bin/env python3
"""
fetch_noaa_india.py - Complete Historical NOAA Global Hourly Weather Collector for India via AWS S3
Part of SkyGuard AI Project (SIH073)

Features:
1. Downloads & filters NOAA ISD station inventory exclusively for India (CTRY == 'IN').
2. Saves `Datasets/indian_aws_locations.csv` (545 Indian stations with lat, lon, elevation, start/end dates).
3. Primary Data Source: AWS S3 Public Open Data Registry (s3://noaa-isd-pds/data/{year}/{usaf}-{wban}-{year}.gz).
4. Fallback Data Source: NOAA NCEI Global Hourly CSV (https://www.ncei.noaa.gov/data/global-hourly/access/).
5. Fast parallel downloading & parsing using ThreadPoolExecutor.
6. Decodes temperature, pressure, dew point, calculates Relative Humidity (%), and outputs clean standardized CSVs.
"""

import os
import sys
import math
import gzip
import urllib.request
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BASE_DIR, "Datasets")
OUTPUT_CSV_STATIONS = os.path.join(DATASETS_DIR, "indian_aws_locations.csv")
PROCESSED_DIR = os.path.join(DATASETS_DIR, "noaa_india_hourly_processed")

AWS_ISD_BASE_URL = "https://noaa-isd-pds.s3.amazonaws.com/data"
NOAA_ISD_HISTORY_URL = "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv"
NOAA_DATA_BASE_URL = "https://www.ncei.noaa.gov/data/global-hourly/access"

def ensure_dirs():
    os.makedirs(DATASETS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

def calculate_relative_humidity(temp_c, dew_c):
    if pd.isna(temp_c) or pd.isna(dew_c):
        return np.nan
    try:
        a = 17.625
        b = 243.04
        alpha_t = (a * temp_c) / (b + temp_c)
        alpha_td = (a * dew_c) / (b + dew_c)
        rh = 100.0 * math.exp(alpha_td - alpha_t)
        return round(min(100.0, max(0.0, rh)), 2)
    except Exception:
        return np.nan

def parse_isd_raw_line(line, station_id, station_name):
    """
    Parses a single line of NOAA ISD fixed-width format.
    Offsets (0-indexed):
      Timestamp: 15-27 (YYYYMMDDHHMM)
      Lat: 28-34 (/1000)
      Lon: 34-41 (/1000)
      Air Temp: 87-92 (/10)
      Dew Point: 93-98 (/10)
      SLP: 99-104 (/10)
    """
    if len(line) < 105:
        return None

    year, month, day, hr, min_ = line[15:19], line[19:21], line[21:23], line[23:25], line[25:27]
    ts_str = f"{year}-{month}-{day}T{hr}:{min_}:00"

    try:
        lat = float(line[28:34]) / 1000.0
        lon = float(line[34:41]) / 1000.0
    except ValueError:
        lat, lon = np.nan, np.nan

    # Air Temp
    try:
        t_raw = float(line[87:92])
        temp_c = t_raw / 10.0 if t_raw != 9999 else np.nan
    except ValueError:
        temp_c = np.nan

    # Dew Point
    try:
        d_raw = float(line[93:98])
        dew_c = d_raw / 10.0 if d_raw != 9999 else np.nan
    except ValueError:
        dew_c = np.nan

    # Sea Level Pressure
    try:
        p_raw = float(line[99:104])
        slp_hpa = p_raw / 10.0 if p_raw != 99999 else np.nan
    except ValueError:
        slp_hpa = np.nan

    if pd.isna(temp_c) and pd.isna(dew_c) and pd.isna(slp_hpa):
        return None

    rh_pct = calculate_relative_humidity(temp_c, dew_c)

    return {
        'timestamp': ts_str,
        'station_id': station_id,
        'station_name': station_name,
        'latitude': lat,
        'longitude': lon,
        'temperature': temp_c,
        'pressure': slp_hpa,
        'humidity': rh_pct
    }

def fetch_station_inventory():
    """
    Downloads NOAA ISD station history and extracts exclusively Indian weather stations (CTRY == 'IN').
    """
    ensure_dirs()
    print("[1/3] Fetching NOAA ISD Station Inventory for India...")
    
    local_inventory_file = os.path.join(DATASETS_DIR, "isd-history.csv")
    if not os.path.exists(local_inventory_file):
        print(f"Downloading from {NOAA_ISD_HISTORY_URL} ...")
        urllib.request.urlretrieve(NOAA_ISD_HISTORY_URL, local_inventory_file)
        print("Downloaded isd-history.csv.")

    df = pd.read_csv(local_inventory_file, dtype=str)
    df.columns = [c.strip().replace('"', '').upper() for c in df.columns]

    df['LAT_NUM'] = pd.to_numeric(df['LAT'], errors='coerce')
    df['LON_NUM'] = pd.to_numeric(df['LON'], errors='coerce')

    # Strictly filter for Country code 'IN'
    india_df = df[df['CTRY'] == 'IN'].copy()

    india_df['USAF'] = india_df['USAF'].str.strip().str.zfill(6)
    india_df['WBAN'] = india_df['WBAN'].str.strip().str.zfill(5)
    india_df['STATION_ID'] = india_df['USAF'] + india_df['WBAN']

    india_df = india_df.rename(columns={
        'STATION NAME': 'STATION_NAME',
        'LAT_NUM': 'LATITUDE',
        'LON_NUM': 'LONGITUDE',
        'ELEV(M)': 'ELEVATION_M',
        'BEGIN': 'BEGIN_DATE',
        'END': 'END_DATE'
    })

    india_df = india_df.sort_values(by=['END_DATE', 'STATION_NAME'], ascending=[False, True])

    cols = ['STATION_ID', 'USAF', 'WBAN', 'STATION_NAME', 'CTRY', 'STATE', 'LATITUDE', 'LONGITUDE', 'ELEVATION_M', 'BEGIN_DATE', 'END_DATE']
    india_df = india_df[cols]

    india_df.to_csv(OUTPUT_CSV_STATIONS, index=False)
    print(f"[OK] Saved {len(india_df)} Indian AWS stations metadata to: {OUTPUT_CSV_STATIONS}")
    return india_df

def fetch_hourly_data_job(job_args):
    """
    Worker task to fetch hourly data from AWS S3 ISD (with NCEI CSV fallback).
    """
    usaf, wban, station_id, year, station_name, lat, lon = job_args
    out_file = os.path.join(PROCESSED_DIR, f"{station_id}_{year}.csv")

    if os.path.exists(out_file) and os.path.getsize(out_file) > 100:
        return {'station_id': station_id, 'year': year, 'status': 'cached', 'rows': 0, 'file': out_file}

    # Primary: AWS S3 GZ endpoint
    aws_url = f"{AWS_ISD_BASE_URL}/{year}/{usaf}-{wban}-{year}.gz"
    parsed_records = []
    
    try:
        req = urllib.request.Request(aws_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=12) as response:
            decompressed = gzip.decompress(response.read()).decode('utf-8', errors='ignore')
            for line in decompressed.splitlines():
                rec = parse_isd_raw_line(line, station_id, station_name)
                if rec:
                    parsed_records.append(rec)
    except urllib.error.HTTPError as e:
        # Fallback to NCEI CSV endpoint
        csv_url = f"{NOAA_DATA_BASE_URL}/{year}/{station_id}.csv"
        try:
            req = urllib.request.Request(csv_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=12) as response:
                df = pd.read_csv(response, low_memory=False)
                # Parse NCEI CSV
                for _, row in df.iterrows():
                    ts_str = str(row.get('DATE', ''))
                    # simple parsing
                    t_val = row.get('TMP', '')
                    d_val = row.get('DEW', '')
                    s_val = row.get('SLP', '')
                    
                    try:
                        temp_c = float(str(t_val).split(',')[0]) / 10.0 if str(t_val).split(',')[0] not in ('9999', '+9999', '') else np.nan
                    except Exception: temp_c = np.nan
                    
                    try:
                        dew_c = float(str(d_val).split(',')[0]) / 10.0 if str(d_val).split(',')[0] not in ('9999', '+9999', '') else np.nan
                    except Exception: dew_c = np.nan

                    try:
                        slp_hpa = float(str(s_val).split(',')[0]) / 10.0 if str(s_val).split(',')[0] not in ('99999', '') else np.nan
                    except Exception: slp_hpa = np.nan

                    if pd.isna(temp_c) and pd.isna(dew_c) and pd.isna(slp_hpa):
                        continue

                    rh_pct = calculate_relative_humidity(temp_c, dew_c)
                    parsed_records.append({
                        'timestamp': ts_str,
                        'station_id': station_id,
                        'station_name': station_name,
                        'latitude': lat,
                        'longitude': lon,
                        'temperature': temp_c,
                        'pressure': slp_hpa,
                        'humidity': rh_pct
                    })
        except Exception:
            return {'station_id': station_id, 'year': year, 'status': '404 Not Found', 'rows': 0}
    except Exception as e:
        return {'station_id': station_id, 'year': year, 'status': f'Error ({str(e)})', 'rows': 0}

    if not parsed_records:
        return {'station_id': station_id, 'year': year, 'status': 'empty', 'rows': 0}

    clean_df = pd.DataFrame(parsed_records)
    clean_df.to_csv(out_file, index=False)
    return {'station_id': station_id, 'year': year, 'status': 'success', 'rows': len(clean_df), 'file': out_file}

def download_all_historical_india(inventory_df, max_workers=16):
    """
    Downloads historical data for all Indian stations from earliest available BEGIN_DATE to END_DATE using AWS S3.
    """
    print("\n[2/3] Generating AWS S3 download tasks for ALL Indian stations (earliest available dates)...")

    jobs = []
    for _, row in inventory_df.iterrows():
        st_id = row['STATION_ID']
        usaf = row['USAF']
        wban = row['WBAN']
        st_name = row['STATION_NAME']
        lat = row['LATITUDE']
        lon = row['LONGITUDE']

        begin_str = str(row['BEGIN_DATE']).strip()
        end_str = str(row['END_DATE']).strip()

        start_year = int(begin_str[:4]) if len(begin_str) >= 4 and begin_str[:4].isdigit() else 2000
        end_year = int(end_str[:4]) if len(end_str) >= 4 and end_str[:4].isdigit() else datetime.now().year

        start_year = max(1942, start_year)
        end_year = min(datetime.now().year, end_year)

        for yr in range(start_year, end_year + 1):
            jobs.append((usaf, wban, st_id, yr, st_name, lat, lon))

    print(f"Total station-year tasks: {len(jobs)} across {len(inventory_df)} Indian stations.")
    print(f"Launching parallel AWS S3 downloads with {max_workers} threads...\n")

    successful_files = []
    total_records = 0
    completed_jobs = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_hourly_data_job, job): job for job in jobs}
        for future in as_completed(futures):
            completed_jobs += 1
            res = future.result()
            if res['status'] in ('success', 'cached'):
                if 'file' in res:
                    successful_files.append(res['file'])
                total_records += res['rows']
                if res['status'] == 'success':
                    print(f"[{completed_jobs}/{len(jobs)}] Saved {res['station_id']} ({res['year']}) -> {res['rows']} records.")
            elif '404' not in res['status']:
                print(f"[{completed_jobs}/{len(jobs)}] {res['station_id']} ({res['year']}) -> {res['status']}")

    print(f"\n[3/3] Download complete! Processed datasets for {len(successful_files)} station-years.")

def main():
    inventory_df = fetch_station_inventory()
    download_all_historical_india(inventory_df, max_workers=16)

if __name__ == "__main__":
    main()
