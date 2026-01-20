"""
Unified Inference Data Preparation Pipeline v2
===============================================
Complete pipeline that:
1. Downloads historical weather (Jan 1st to yesterday) - WITH CACHE
2. Downloads latest forecast (today to +10 days)
3. Calculates phenology from Jan 1st
4. Creates inference datasets with 19 features

Cache logic:
- Historical data (day-1 forecasts) is cached and not re-downloaded
- Only missing dates are downloaded
- Latest forecast is always downloaded fresh

Usage:
    python prepare_inference_data_v2.py
    python prepare_inference_data_v2.py --clear-cache  # Force re-download all
    python prepare_inference_data_v2.py --list-only    # Show available dates
"""

import os
import sys
import re
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import argparse

import boto3
import numpy as np
import pandas as pd
import xarray as xr
import warnings

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
WEATHER_DIR = SCRIPT_DIR / "weather"
CACHE_DIR = WEATHER_DIR / "cache"
CACHE_HOURLY_DIR = CACHE_DIR / "hourly"
CACHE_DAILY_DIR = CACHE_DIR / "daily"
PHENOLOGY_CSV_DIR = SCRIPT_DIR / "phenology" / "phenology_csv"
INFERENCE_DIR = SCRIPT_DIR / "dataframe_inference"
TEMP_DIR = WEATHER_DIR / "temp_grib"

S3_BUCKET = 'ecmwf-data-forecast'

# Target provinces - Emilia-Romagna
TARGET_PROVINCES = {
    "bologna": (10.5, 44.0, 12.0, 45.0),
    "ferrara": (11.0, 44.5, 12.5, 45.0),
    "forli_cesena": (11.5, 43.7, 12.5, 44.3),
    "modena": (10.5, 44.0, 11.5, 44.8),
    "parma": (9.5, 44.3, 10.5, 45.0),
    "piacenza": (9.0, 44.5, 10.0, 45.2),
    "ravenna": (11.5, 44.0, 12.5, 44.7),
    "reggio_nell_emilia": (10.0, 44.3, 11.0, 44.9),
    "rimini": (12.0, 43.8, 12.8, 44.2)
}

HISTORICAL_MAX_HOURS = 24
FORECAST_MAX_HOURS = 240

# Add phenology module path
PHENOLOGY_DIR = SCRIPT_DIR / "phenology"
sys.path.insert(0, str(PHENOLOGY_DIR))
sys.path.insert(0, str(PHENOLOGY_DIR / 'infections'))


# =============================================================================
# LOGGING
# =============================================================================

def log_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")

def log_step(msg):
    print(f"→ {msg}")

def log_info(msg):
    print(f"  {msg}")

def log_success(msg):
    print(f"  ✓ {msg}")

def log_error(msg):
    print(f"  ✗ ERROR: {msg}")


# =============================================================================
# WEATHER CALCULATIONS
# =============================================================================

def sat_vapour_pressure(T_c):
    return 0.6108 * np.exp(17.27 * T_c / (T_c + 237.3))

def relative_humidity(T_c, Tdp_c):
    es = sat_vapour_pressure(T_c)
    ea = sat_vapour_pressure(Tdp_c)
    rh = 100.0 * ea / es
    return np.clip(rh, 0, 100)

def wind_10m_to_z_speed(u10, v10, z_target=0.3, h_canopy=0.3, z_ref=10.0):
    """
    Convert 10m wind speed to wind speed at target height using log wind profile.
    Matches training/data/weather/rh_lw.py exactly.
    """
    u10_speed = np.hypot(u10, v10).astype(float)
    h = float(h_canopy)
    d = 0.67 * h  # displacement height
    z0 = 0.10 * h  # roughness length
    num = np.log(np.maximum((z_target - d) / z0, 1e-6))
    den = np.log(np.maximum((z_ref - d) / z0, 1e-6))
    factor = num / den
    w_target = np.clip(u10_speed * factor, 0.0, None)
    return w_target


def calculate_leaf_wetness(t2m, d2m, rh, wind_03m, prec):
    """
    Calculate leaf wetness using decision tree model.
    Matches training/data/weather/rh_lw.py exactly.

    Decision tree:
    1. If DPD >= 3.7: DRY
    2. If wind >= 2.5 AND RH < 87.8: DRY
    3. If wind < 2.5: Use inequality_1
    4. If wind >= 2.5 AND RH >= 87.8: Use inequality_2
    5. Override: If precipitation >= 0.25mm: WET
    """
    # Ensure arrays
    T = np.asarray(t2m, dtype=float)
    Tdp = np.asarray(d2m, dtype=float)
    RH = np.asarray(rh, dtype=float)
    W = np.asarray(wind_03m, dtype=float)
    P = np.asarray(prec, dtype=float)

    # Calculate DPD (Dew Point Depression)
    DPD = T - Tdp

    # Decision tree nodes
    node1_dry = DPD >= 3.7
    node2_dry = (W >= 2.5) & (RH < 87.8)

    # Masks for undecided cases
    mask_undecided = (~node1_dry) & (~node2_dry)
    mask2 = mask_undecided & (W < 2.5)
    mask3 = mask_undecided & (W >= 2.5) & (RH >= 87.8)

    # Compute derived variables
    sqrtT = np.sqrt(np.clip(T, 0, None))
    T2 = T**2
    T_RH = T * RH
    T_W = T * W
    W_DPD = W * DPD

    # Compute inequalities
    inequity_1 = (1.6064 * sqrtT) + (0.0036 * T2) + (0.1531 * RH) - (0.4599 * W_DPD) - (0.0035 * T_RH)
    inequity_2 = (0.7921 * sqrtT) + (0.0046 * RH) - (2.3889 * W) - (0.0390 * T_W) + (1.0613 * W_DPD)

    # Initialize leaf wetness array
    LW = np.zeros(len(T), dtype=float)

    # Apply decision rules
    LW[node1_dry | node2_dry] = 0
    LW[mask2 & (inequity_1 > 14.4674)] = 1
    LW[mask3 & (inequity_2 > 37.0)] = 1

    # Override with precipitation
    LW = np.where(np.isfinite(P) & (P >= 0.25), 1, LW)

    # Handle missing data
    needed = np.isfinite(T) & np.isfinite(RH) & np.isfinite(W) & np.isfinite(DPD)
    LW = np.where(needed, LW, 0)  # Default to 0 if missing

    return LW


# =============================================================================
# CACHE MANAGEMENT
# =============================================================================

def get_cached_dates():
    """Get list of dates already in cache"""
    cached = set()
    if CACHE_DAILY_DIR.exists():
        # Check any province file for dates
        for csv_file in CACHE_DAILY_DIR.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file)
                if 'date' in df.columns:
                    dates = pd.to_datetime(df['date']).dt.strftime('%Y%m%d').tolist()
                    cached.update(dates)
            except:
                pass
            break  # Only need to check one file
    return cached


def save_to_cache(province_name, df_hourly, df_daily, date_str):
    """Save a single date's data to cache"""
    CACHE_HOURLY_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DAILY_DIR.mkdir(parents=True, exist_ok=True)

    # Hourly cache
    hourly_file = CACHE_HOURLY_DIR / f"{province_name}.csv"
    if hourly_file.exists():
        existing = pd.read_csv(hourly_file)
        existing['valid_time'] = pd.to_datetime(existing['valid_time'])
        df_hourly['valid_time'] = pd.to_datetime(df_hourly['valid_time'])
        combined = pd.concat([existing, df_hourly], ignore_index=True)
        combined = combined.drop_duplicates(subset='valid_time', keep='last')
        combined = combined.sort_values('valid_time')
        combined.to_csv(hourly_file, index=False)
    else:
        df_hourly.to_csv(hourly_file, index=False)

    # Daily cache
    daily_file = CACHE_DAILY_DIR / f"{province_name}.csv"
    if daily_file.exists():
        existing = pd.read_csv(daily_file)
        existing['date'] = pd.to_datetime(existing['date'])
        df_daily['date'] = pd.to_datetime(df_daily['date'])
        combined = pd.concat([existing, df_daily], ignore_index=True)
        combined = combined.drop_duplicates(subset='date', keep='last')
        combined = combined.sort_values('date')
        combined.to_csv(daily_file, index=False)
    else:
        df_daily.to_csv(daily_file, index=False)


def load_from_cache(province_name):
    """Load cached data for a province, handling legacy cache without forecast_base"""
    hourly_file = CACHE_HOURLY_DIR / f"{province_name}.csv"
    daily_file = CACHE_DAILY_DIR / f"{province_name}.csv"

    if hourly_file.exists():
        df_hourly = pd.read_csv(hourly_file)
        df_hourly['valid_time'] = pd.to_datetime(df_hourly['valid_time'])
        # Handle legacy cache without forecast_base: infer from valid_time
        # Cache data is T+24h forecast, so forecast_base = valid_time - 1 day
        if 'forecast_base' not in df_hourly.columns:
            df_hourly['forecast_base'] = df_hourly['valid_time'] - pd.Timedelta(days=1)
    else:
        df_hourly = pd.DataFrame()

    if daily_file.exists():
        df_daily = pd.read_csv(daily_file)
        df_daily['date'] = pd.to_datetime(df_daily['date'])
        # Handle legacy cache without forecast_base
        if 'forecast_base' not in df_daily.columns:
            df_daily['forecast_base'] = df_daily['date'] - pd.Timedelta(days=1)
    else:
        df_daily = pd.DataFrame()

    return df_hourly, df_daily


def clear_cache():
    """Clear all cached data"""
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        log_info("Cache cleared")


# =============================================================================
# S3 FUNCTIONS
# =============================================================================

def list_all_s3_files():
    """List ALL forecast files in S3 bucket with pagination"""
    log_step(f"Connecting to S3 bucket '{S3_BUCKET}'...")

    s3 = boto3.client('s3')
    all_files = []
    continuation_token = None

    while True:
        if continuation_token:
            response = s3.list_objects_v2(Bucket=S3_BUCKET, ContinuationToken=continuation_token)
        else:
            response = s3.list_objects_v2(Bucket=S3_BUCKET)

        if 'Contents' not in response:
            break

        for obj in response['Contents']:
            key = obj['Key']
            if '_fc_' in key and key.endswith('h'):
                date_match = re.search(r'(\d{8})T\d{6}Z', key)
                step_match = re.search(r'_(\d+)h$', key)

                if date_match and step_match:
                    all_files.append({
                        'key': key,
                        'date_str': date_match.group(1),
                        'step_hours': int(step_match.group(1)),
                        'size_mb': obj['Size'] / (1024 * 1024)
                    })

        if response.get('IsTruncated'):
            continuation_token = response['NextContinuationToken']
        else:
            break

    # Group by date
    files_by_date = defaultdict(list)
    for f in all_files:
        files_by_date[f['date_str']].append(f)

    for date_str in files_by_date:
        files_by_date[date_str].sort(key=lambda x: x['step_hours'])

    log_info(f"Found {len(files_by_date)} dates in S3")
    return dict(files_by_date)


def download_and_merge_date(s3_client, files_for_date, date_str, max_hours):
    """Download and merge GRIB files for a single date"""
    files_to_use = [f for f in files_for_date if f['step_hours'] <= max_hours]

    if not files_to_use:
        return None

    TEMP_DIR.mkdir(exist_ok=True)
    datasets = []

    for file_info in files_to_use:
        temp_file = TEMP_DIR / f"temp_{file_info['step_hours']:03d}h.grib"

        try:
            s3_client.download_file(S3_BUCKET, file_info['key'], str(temp_file))
            ds = xr.open_dataset(temp_file, engine="cfgrib")
            ds = ds.load()
            datasets.append(ds)
            temp_file.unlink()
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            continue

    if not datasets:
        return None

    try:
        merged_ds = xr.concat(datasets, dim='step')
    except:
        merged_ds = datasets[0]

    return merged_ds


def process_province_from_dataset(ds, province_name, bounds):
    """Extract province data from merged dataset"""
    try:
        lon_min, lat_min, lon_max, lat_max = bounds

        ds_prov = ds.sel(
            latitude=slice(lat_max, lat_min),
            longitude=slice(lon_min, lon_max)
        )

        if len(ds_prov.latitude) == 0 or len(ds_prov.longitude) == 0:
            return None, None

        forecast_base = pd.Timestamp(ds_prov.time.values)

        t2m = ds_prov.t2m.mean(dim=['latitude', 'longitude']).values - 273.15
        d2m = ds_prov.d2m.mean(dim=['latitude', 'longitude']).values - 273.15
        u10 = ds_prov.u10.mean(dim=['latitude', 'longitude']).values
        v10 = ds_prov.v10.mean(dim=['latitude', 'longitude']).values

        if 'tp' in ds_prov:
            tp_cumulative = ds_prov.tp.mean(dim=['latitude', 'longitude']).values * 1000
            tp = np.diff(tp_cumulative, prepend=0)
            tp = np.maximum(tp, 0)
        else:
            tp = np.zeros_like(t2m)

        wind_10m = np.hypot(u10, v10)
        rh = relative_humidity(t2m, d2m)

        # Calculate wind at 0.3m for leaf wetness model (matches training)
        wind_03m = wind_10m_to_z_speed(u10, v10, z_target=0.3, h_canopy=0.3, z_ref=10.0)

        # Calculate leaf wetness using decision tree model (matches training)
        lw = calculate_leaf_wetness(t2m, d2m, rh, wind_03m, tp)

        step_values = ds_prov.step.values
        if ds_prov.step.dtype.kind == 'm':
            valid_times = forecast_base + pd.to_timedelta(step_values)
        else:
            valid_times = forecast_base + pd.to_timedelta(step_values, unit='h')

        df_hourly = pd.DataFrame({
            'valid_time': valid_times,
            'forecast_base': forecast_base,
            'temp': np.round(t2m, 2),
            'temp_dew': np.round(d2m, 2),
            'prec': np.round(tp, 2),
            'wind_10m': np.round(wind_10m, 2),
            'rh': np.round(rh, 2),
            'lw': lw.astype(int),
            'site': province_name
        })

        # Aggregate to daily
        df_hourly['date'] = pd.to_datetime(df_hourly['valid_time']).dt.date

        daily = df_hourly.groupby('date').agg({
            'temp': ['mean', 'min', 'max'],
            'temp_dew': 'mean',
            'prec': 'sum',
            'wind_10m': 'mean',
            'rh': 'mean',
            'lw': 'sum'
        }).reset_index()

        daily.columns = ['date', 'temp_mean', 'temp_min', 'temp_max',
                        'temp_dew_mean', 'prec_sum', 'wind_10m_mean',
                        'rh_mean', 'lw_hours']
        daily['site'] = province_name
        daily['forecast_base'] = forecast_base  # Keep track of source for smart merging

        return df_hourly, daily

    except Exception as e:
        return None, None


# =============================================================================
# PHENOLOGY CALCULATION
# =============================================================================

def calculate_phenology_from_jan1(province_name, df_daily, df_hourly):
    """
    Calculate phenology and infections from January 1st.
    """
    from dormancy import Dormancy
    from forcing import Forcing
    from infections.rule310 import Rule310
    from infections.misfits import Misfits
    from infections.dmcast import DMCast
    from data_structures import InputDaily, Input, Output
    from readers import ParametersReader

    # Load parameters
    params_file = str(PHENOLOGY_DIR / "parameters" / "octoPusParameters.csv")
    susceptibility_file = str(PHENOLOGY_DIR / "parameters" / "hostSusceptibilityParameters.csv")
    parameters = ParametersReader.read_all_parameters(params_file, susceptibility_file)

    # Initialize models
    output = Output()
    rule310 = Rule310()
    misfits = Misfits()
    dmcast = DMCast()

    # Prepare data
    df_daily = df_daily.copy()
    df_daily['date'] = pd.to_datetime(df_daily['date'])
    df_daily = df_daily.sort_values('date').reset_index(drop=True)

    # Prepare hourly lookup
    if df_hourly is not None and len(df_hourly) > 0:
        df_hourly = df_hourly.copy()
        df_hourly['valid_time'] = pd.to_datetime(df_hourly['valid_time'])
        df_hourly['date_only'] = df_hourly['valid_time'].dt.date
        hourly_by_date = {date: group for date, group in df_hourly.groupby('date_only')}
    else:
        hourly_by_date = {}

    results = []

    for _, day_row in df_daily.iterrows():
        current_date = day_row['date']

        temp_mean = day_row.get('temp_mean', 10.0)
        temp_min = day_row.get('temp_min', temp_mean - 5)
        temp_max = day_row.get('temp_max', temp_mean + 5)
        prec = day_row.get('prec_sum', 0.0)
        lw = day_row.get('lw_hours', 0)
        rh = day_row.get('rh_mean', 70.0)

        # Daily input for phenology
        input_daily = InputDaily(
            date=current_date,
            temp_max=temp_max,
            temp_min=temp_min,
            prec=prec,
            lw=lw,
            rh=rh,
            site=province_name
        )

        # Run phenology models
        Dormancy.run_dormancy(input_daily, parameters, output)
        Forcing.run_forcing(input_daily, parameters, output)

        # Track daily infections
        daily_rule310 = 0
        daily_misfits = 0
        daily_dmcast = 0

        # Process hourly for infections
        day_hourly = hourly_by_date.get(current_date.date(), pd.DataFrame())

        if not day_hourly.empty:
            for _, hour_row in day_hourly.iterrows():
                input_hourly = Input(
                    date=pd.to_datetime(hour_row['valid_time']),
                    temp=hour_row.get('temp', temp_mean),
                    prec=hour_row.get('prec', 0),
                    lw=hour_row.get('lw', 0),
                    rh=hour_row.get('rh', rh)
                )

                prev_rule310 = len(output.outputs_rule310.infection_events)
                prev_misfits = len(output.outputs_misfits.infection_events)
                prev_dmcast = len(output.outputs_dmcast.infection_events)

                rule310.run(input_hourly, parameters, output)
                misfits.run(input_hourly, parameters, output)
                dmcast.run(input_hourly, parameters, output)

                daily_rule310 += len(output.outputs_rule310.infection_events) - prev_rule310
                daily_misfits += len(output.outputs_misfits.infection_events) - prev_misfits
                daily_dmcast += len(output.outputs_dmcast.infection_events) - prev_dmcast

        output.pressure_rule310 += daily_rule310
        output.pressure_misfits += daily_misfits
        output.pressure_dmcast += daily_dmcast

        result = {
            'date': current_date,
            'site': province_name,
            # Weather
            'temp': round(temp_mean, 1),
            'temp_dew': round(day_row.get('temp_dew_mean', temp_mean - 5), 1),
            'prec': round(prec, 1),
            'rh': round(rh, 1),
            'wind_10m': round(day_row.get('wind_10m_mean', 2.0), 1),
            'lw': int(lw),
            # Phenology
            'chill_state': round(output.outputs_phenology.chill_state, 2),
            'forcing_state': round(output.outputs_phenology.forcing_state, 1),
            'bbch_code': round(output.outputs_phenology.bbch_phenophase_code, 1),
            'plant_susceptibility': round(output.outputs_phenology.plant_susceptibility, 3),
            # Infections
            'rule310': 1 if daily_rule310 > 0 else 0,
            'misfits': 1 if daily_misfits > 0 else 0,
            'dmcast': 1 if daily_dmcast > 0 else 0,
            'rule310_cum': output.pressure_rule310,
            'misfits_cum': output.pressure_misfits,
            'dmcast_cum': output.pressure_dmcast
        }
        results.append(result)

    return pd.DataFrame(results)


# =============================================================================
# WEEKLY AGGREGATION & INFERENCE DATASETS
# =============================================================================

def aggregate_to_weekly(df_phenology, province_name):
    """Aggregate daily phenology to weekly with velocity features"""
    df = df_phenology.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['iso_year'] = df['date'].dt.isocalendar().year.astype(int)
    df['iso_week'] = df['date'].dt.isocalendar().week.astype(int)

    agg_dict = {
        'temp': 'mean', 'temp_dew': 'mean', 'prec': 'sum',
        'rh': 'mean', 'wind_10m': 'mean', 'lw': 'sum',
        'chill_state': 'mean', 'forcing_state': 'mean',
        'bbch_code': 'mean', 'plant_susceptibility': 'mean',
        'rule310': 'sum', 'misfits': 'sum', 'dmcast': 'sum',
        'rule310_cum': 'max', 'misfits_cum': 'max', 'dmcast_cum': 'max',
        'date': 'first'
    }

    weekly = df.groupby(['iso_year', 'iso_week']).agg(agg_dict).reset_index()
    weekly['NUTS_3'] = province_name
    weekly = weekly.sort_values(['iso_year', 'iso_week']).reset_index(drop=True)

    # Velocity features
    weekly['bbch_code_velocity'] = weekly['bbch_code'].diff().fillna(0)
    weekly['plant_susceptibility_velocity'] = weekly['plant_susceptibility'].diff().fillna(0)
    weekly['forcing_state_velocity'] = weekly['forcing_state'].diff().fillna(0)
    weekly['bbch_code_acceleration'] = weekly['bbch_code_velocity'].diff().fillna(0)
    weekly['plant_susceptibility_acceleration'] = weekly['plant_susceptibility_velocity'].diff().fillna(0)

    # Round
    for col in weekly.columns:
        if weekly[col].dtype == 'float64':
            weekly[col] = weekly[col].round(3)

    return weekly


def create_inference_datasets(combined_weekly, forecast_date):
    """
    Create lead_0.csv and lead_1.csv with CORRECT week filtering.

    Lead 0: Features from current week → predict current week risk
    Lead 1: Features from current week → predict next week risk

    Each province should have exactly 1 row per lead (not multiple weeks!)
    """
    INFERENCE_DIR.mkdir(exist_ok=True)

    FEATURE_COLS = [
        'bbch_code', 'plant_susceptibility',
        'bbch_code_velocity', 'plant_susceptibility_velocity', 'forcing_state_velocity',
        'bbch_code_acceleration', 'plant_susceptibility_acceleration',
        'temp', 'temp_dew', 'prec', 'rh', 'wind_10m', 'lw',
        'rule310', 'rule310_cum', 'dmcast', 'dmcast_cum', 'misfits', 'misfits_cum',
        'week_cos'
    ]

    # Get the ISO week of the forecast date (this is the "current" week)
    forecast_iso = forecast_date.isocalendar()
    forecast_iso_year = forecast_iso[0]
    forecast_iso_week = forecast_iso[1]

    log_info(f"Forecast date: {forecast_date.strftime('%Y-%m-%d')} (ISO week {forecast_iso_week}, year {forecast_iso_year})")

    for lead in [0, 1]:
        df = combined_weekly.copy()

        # CRITICAL FIX: Filter to ONLY the current week's data
        # For both lead 0 and lead 1, features come from the CURRENT week
        df = df[(df['iso_week'] == forecast_iso_week) &
                (df['iso_year'] == forecast_iso_year)]

        if len(df) == 0:
            log_error(f"No data for week {forecast_iso_week}! Available weeks: {combined_weekly['iso_week'].unique()}")
            # Fallback: use the latest available week
            latest_week = combined_weekly['iso_week'].max()
            df = combined_weekly[combined_weekly['iso_week'] == latest_week].copy()
            log_info(f"Using fallback week {latest_week}")

        df['forecast_week'] = forecast_iso_week
        df['forecast_year'] = forecast_iso_year
        df['lead_weeks'] = lead

        # Calculate target week
        target_week = forecast_iso_week + lead
        target_year = forecast_iso_year

        # Handle year boundary (some years have 53 ISO weeks)
        # Check how many weeks the target year has
        from datetime import date
        dec_28 = date(target_year, 12, 28)
        max_weeks_in_year = dec_28.isocalendar()[1]  # Week of Dec 28 = last week of year

        if target_week > max_weeks_in_year:
            target_year += 1
            target_week -= max_weeks_in_year

        df['target_week'] = target_week
        df['target_year'] = target_year

        # Calculate actual target period dates based on ISO week
        # ISO week 1 starts on the Monday of the week containing Jan 4th
        from datetime import date
        jan4 = date(target_year, 1, 4)
        # Find Monday of week 1
        week1_monday = jan4 - timedelta(days=jan4.weekday())
        # Calculate Monday of target week
        target_monday = week1_monday + timedelta(weeks=target_week - 1)
        target_sunday = target_monday + timedelta(days=6)

        df['forecast_base'] = forecast_date.strftime("%Y-%m-%d")
        df['target_period_start'] = target_monday.strftime("%Y-%m-%d")
        df['target_period_end'] = target_sunday.strftime("%Y-%m-%d")

        # Add cyclical week encoding (same as training)
        df['week_cos'] = np.cos(2 * np.pi * forecast_iso_week / 52.0)

        for col in FEATURE_COLS:
            if col not in df.columns:
                df[col] = 0

        id_cols = ['NUTS_3', 'forecast_base', 'lead_weeks', 'target_period_start', 'target_period_end']
        output_cols = id_cols + FEATURE_COLS

        model_ready = df[output_cols].copy()
        output_file = INFERENCE_DIR / f'lead_{lead}.csv'
        model_ready.to_csv(output_file, index=False)
        log_info(f"Saved lead_{lead}.csv: {len(model_ready)} records (1 per province)")


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_pipeline(clear_cache_flag=False):
    """Run the complete inference preparation pipeline"""

    log_header("INFERENCE DATA PREPARATION PIPELINE v2")

    # Clear cache if requested
    if clear_cache_flag:
        clear_cache()

    # Create directories
    CACHE_DIR.mkdir(exist_ok=True)
    CACHE_HOURLY_DIR.mkdir(exist_ok=True)
    CACHE_DAILY_DIR.mkdir(exist_ok=True)
    PHENOLOGY_CSV_DIR.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # STEP 1: Determine what to download
    # =========================================================================
    log_step("Step 1: Checking S3 and cache...")

    files_by_date = list_all_s3_files()
    if not files_by_date:
        log_error("No files found in S3")
        return 1

    sorted_dates = sorted(files_by_date.keys())
    latest_date = sorted_dates[-1]

    # Get current year's Jan 1st
    current_year = datetime.strptime(latest_date, '%Y%m%d').year
    jan1_str = f"{current_year}0101"

    # Filter dates from Jan 1st
    available_dates = [d for d in sorted_dates if d >= jan1_str]

    if not available_dates:
        log_error(f"No data available from {jan1_str}")
        return 1

    log_info(f"S3 data: {available_dates[0]} to {available_dates[-1]}")

    # Check cache
    cached_dates = get_cached_dates()
    log_info(f"Cached dates: {len(cached_dates)}")

    # Determine what to download
    # Historical = all except latest (these get cached)
    # Forecast = latest only (always download fresh)
    historical_dates = [d for d in available_dates if d != latest_date]
    dates_to_download = [d for d in historical_dates if d not in cached_dates]

    log_info(f"Historical dates to download: {len(dates_to_download)}")
    log_info(f"Forecast date: {latest_date}")

    # =========================================================================
    # STEP 2: Download missing historical data
    # =========================================================================
    if dates_to_download:
        log_step(f"Step 2: Downloading {len(dates_to_download)} missing historical dates...")

        s3 = boto3.client('s3')

        for i, date_str in enumerate(dates_to_download):
            log_info(f"[{i+1}/{len(dates_to_download)}] {date_str} (24h)...")

            merged_ds = download_and_merge_date(s3, files_by_date[date_str], date_str, HISTORICAL_MAX_HOURS)

            if merged_ds is None:
                continue

            for prov_name, bounds in TARGET_PROVINCES.items():
                df_hourly, df_daily = process_province_from_dataset(merged_ds, prov_name, bounds)
                if df_hourly is not None:
                    save_to_cache(prov_name, df_hourly, df_daily, date_str)

            merged_ds.close()

        log_success(f"Downloaded and cached {len(dates_to_download)} dates")
    else:
        log_step("Step 2: All historical data already cached")

    # =========================================================================
    # STEP 3: Download latest forecast
    # =========================================================================
    log_step(f"Step 3: Downloading latest forecast ({latest_date}, 240h)...")

    s3 = boto3.client('s3')
    merged_ds = download_and_merge_date(s3, files_by_date[latest_date], latest_date, FORECAST_MAX_HOURS)

    if merged_ds is None:
        log_error("Failed to download forecast")
        return 1

    forecast_data = {}
    for prov_name, bounds in TARGET_PROVINCES.items():
        df_hourly, df_daily = process_province_from_dataset(merged_ds, prov_name, bounds)
        if df_hourly is not None:
            forecast_data[prov_name] = (df_hourly, df_daily)

    merged_ds.close()
    forecast_date = datetime.strptime(latest_date, '%Y%m%d')
    log_success(f"Forecast downloaded: {len(forecast_data)} provinces")

    # Save forecast data for app visualization (10-day forecast)
    FORECAST_DIR = WEATHER_DIR / "forecast"
    FORECAST_DIR.mkdir(parents=True, exist_ok=True)
    
    for prov_name, (fc_hourly, fc_daily) in forecast_data.items():
        # Save daily forecast (useful for app)
        fc_daily_file = FORECAST_DIR / f"{prov_name}_forecast.csv"
        fc_daily.to_csv(fc_daily_file, index=False)
    
    log_success(f"Forecast saved for app: {FORECAST_DIR}")

    # Clean up temp
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)

    # =========================================================================
    # STEP 4: Combine cache + forecast and calculate phenology
    # =========================================================================
    log_step("Step 4: Calculating phenology from January 1st...")

    all_weekly_data = []

    for prov_name in TARGET_PROVINCES.keys():
        # Load cached historical
        cached_hourly, cached_daily = load_from_cache(prov_name)

        # Get forecast
        if prov_name in forecast_data:
            fc_hourly, fc_daily = forecast_data[prov_name]
        else:
            continue

        # Combine cache + forecast with smart duplicate handling
        # Strategy: For past days, prefer cache (T+24h forecasts are more accurate)
        #           For today and future, use fresh forecast
        if len(cached_hourly) > 0:
            combined_hourly = pd.concat([cached_hourly, fc_hourly], ignore_index=True)
            combined_daily = pd.concat([cached_daily, fc_daily], ignore_index=True)
        else:
            combined_hourly = fc_hourly
            combined_daily = fc_daily

        # Smart duplicate removal: prefer cache for past, forecast for future
        combined_hourly['valid_time'] = pd.to_datetime(combined_hourly['valid_time'])
        combined_hourly['forecast_base'] = pd.to_datetime(combined_hourly['forecast_base'], format='mixed')

        # Add source indicator: 'cache' if forecast_base < forecast_date, else 'forecast'
        combined_hourly['is_from_cache'] = combined_hourly['forecast_base'].dt.date < forecast_date.date()

        # For each valid_time, prefer:
        # - If valid_time.date < forecast_date: cache data (more accurate T+24h)
        # - If valid_time.date >= forecast_date: fresh forecast data
        combined_hourly['prefer_cache'] = combined_hourly['valid_time'].dt.date < forecast_date.date()

        # Sort so that the preferred source comes last (will be kept by drop_duplicates)
        # For past days: cache=True should be last, so sort is_from_cache ascending (False first)
        # For future days: cache=False should be last, so sort is_from_cache descending (True first)
        # Solution: Create a priority column
        combined_hourly['priority'] = combined_hourly.apply(
            lambda row: 1 if (row['prefer_cache'] == row['is_from_cache']) else 0, axis=1
        )
        combined_hourly = combined_hourly.sort_values(['valid_time', 'priority'])
        combined_hourly = combined_hourly.drop_duplicates(subset='valid_time', keep='last')
        combined_hourly = combined_hourly.drop(columns=['is_from_cache', 'prefer_cache', 'priority'])

        # Same smart logic for daily data
        combined_daily['date'] = pd.to_datetime(combined_daily['date'])
        combined_daily['forecast_base'] = pd.to_datetime(combined_daily['forecast_base'], format='mixed')

        combined_daily['is_from_cache'] = combined_daily['forecast_base'].dt.date < forecast_date.date()
        combined_daily['prefer_cache'] = combined_daily['date'].dt.date < forecast_date.date()
        combined_daily['priority'] = combined_daily.apply(
            lambda row: 1 if (row['prefer_cache'] == row['is_from_cache']) else 0, axis=1
        )
        combined_daily = combined_daily.sort_values(['date', 'priority'])
        combined_daily = combined_daily.drop_duplicates(subset='date', keep='last')
        combined_daily = combined_daily.drop(columns=['is_from_cache', 'prefer_cache', 'priority', 'forecast_base'])

        # Filter from Jan 1st
        jan1 = datetime(forecast_date.year, 1, 1)
        combined_hourly = combined_hourly[combined_hourly['valid_time'] >= jan1]
        combined_daily = combined_daily[combined_daily['date'] >= jan1]

        log_info(f"{prov_name}: {len(combined_daily)} days (Jan 1 to forecast end)")

        # Calculate phenology
        df_phenology = calculate_phenology_from_jan1(prov_name, combined_daily, combined_hourly)

        # Save phenology CSV
        pheno_file = PHENOLOGY_CSV_DIR / f"{prov_name}_{forecast_date.year}.csv"
        df_phenology.to_csv(pheno_file, index=False)

        # Aggregate to weekly
        weekly = aggregate_to_weekly(df_phenology, prov_name)
        all_weekly_data.append(weekly)

    log_success(f"Phenology calculated for {len(all_weekly_data)} provinces")

    # =========================================================================
    # STEP 5: Create inference datasets
    # =========================================================================
    log_step("Step 5: Creating inference datasets...")

    combined_weekly = pd.concat(all_weekly_data, ignore_index=True)
    create_inference_datasets(combined_weekly, forecast_date)

    log_success("Inference datasets ready")

    # Summary
    log_header("PIPELINE COMPLETE")
    log_info(f"Forecast date: {forecast_date.strftime('%Y-%m-%d')}")
    log_info(f"Phenology CSVs: {PHENOLOGY_CSV_DIR}/")
    log_info(f"Inference data: {INFERENCE_DIR}/")

    return 0


def main():
    parser = argparse.ArgumentParser(description='Unified Inference Data Preparation')
    parser.add_argument('--clear-cache', action='store_true', help='Clear cache and re-download all')
    parser.add_argument('--list-only', action='store_true', help='Only list available dates')
    args = parser.parse_args()

    if args.list_only:
        files_by_date = list_all_s3_files()
        sorted_dates = sorted(files_by_date.keys())
        print(f"\nAvailable dates: {sorted_dates}")
        cached = get_cached_dates()
        print(f"Cached dates: {sorted(cached)}")
        return 0

    return run_pipeline(clear_cache_flag=args.clear_cache)


if __name__ == "__main__":
    sys.exit(main())
