#!/usr/bin/env python3
"""
Backfill Historical Predictions
================================
Generates predictions for EVERY DAY from January 1st to current date.

Each day gets its own prediction file, simulating daily pipeline runs.
This allows tracking how predictions evolve during a week as more
real data becomes available (T+24h replaces forecast).

- Automatically SKIPS days that already have predictions
- Run periodically to fill in missing days
- Use --force to regenerate all predictions

IMPORTANT: This uses ONLY cached historical data (T+24h forecasts), 
so predictions will be more accurate than real-time predictions would have been.

Usage:
    python backfill_predictions.py                  # Fill missing only
    python backfill_predictions.py --start-week 5   # Start from week 5
    python backfill_predictions.py --force          # Regenerate ALL
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Setup paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
PHENOLOGY_DIR = DATA_DIR / "phenology"
CACHE_DIR = DATA_DIR / "weather" / "cache"
INFERENCE_DIR = DATA_DIR / "dataframe_inference"
MODEL_DIR = SCRIPT_DIR / "model"
HISTORY_DIR = SCRIPT_DIR / "predictions" / "history"

# Add paths for imports
sys.path.insert(0, str(DATA_DIR))  # For prepare_inference_data
sys.path.insert(0, str(PHENOLOGY_DIR))
sys.path.insert(0, str(PHENOLOGY_DIR / 'infections'))


def log_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")


def log_step(msg):
    print(f"→ {msg}")


def log_info(msg):
    print(f"  {msg}")


def get_cached_date_range():
    """Get min and max dates from cache"""
    cache_file = CACHE_DIR / "hourly" / "bologna.csv"
    if not cache_file.exists():
        return None, None
    
    df = pd.read_csv(cache_file)
    df['date'] = pd.to_datetime(df['valid_time']).dt.date
    return df['date'].min(), df['date'].max()


def load_cached_data_for_period(end_date):
    """Load cached data from Jan 1st up to end_date"""
    from prepare_inference_data import (
        TARGET_PROVINCES, calculate_phenology_from_jan1,
        load_from_cache
    )
    
    all_weekly = []
    jan1 = datetime(end_date.year, 1, 1)
    
    for prov_name in TARGET_PROVINCES.keys():
        # Load cached data
        cached_hourly, cached_daily = load_from_cache(prov_name)
        
        if cached_hourly is None or len(cached_hourly) == 0:
            continue
        
        # Filter up to end_date
        cached_hourly['valid_time'] = pd.to_datetime(cached_hourly['valid_time'])
        cached_daily['date'] = pd.to_datetime(cached_daily['date'])
        
        filtered_hourly = cached_hourly[cached_hourly['valid_time'].dt.date <= end_date]
        filtered_daily = cached_daily[cached_daily['date'].dt.date <= end_date]
        
        if len(filtered_daily) == 0:
            continue
        
        # Calculate phenology
        df_phenology = calculate_phenology_from_jan1(prov_name, filtered_daily, filtered_hourly)
        
        if df_phenology is None or len(df_phenology) == 0:
            continue
        
        # Aggregate to weekly
        from prepare_inference_data import aggregate_to_weekly
        df_weekly = aggregate_to_weekly(df_phenology, prov_name)
        
        all_weekly.append(df_weekly)
    
    if not all_weekly:
        return None
    
    return pd.concat(all_weekly, ignore_index=True)


def create_inference_dataset(df_weekly, forecast_date, lead):
    """Create inference dataset for a specific lead time"""
    # Get forecast ISO week
    forecast_iso_week = forecast_date.isocalendar()[1]
    target_week = forecast_iso_week + lead
    
    # Filter to target week
    df_target = df_weekly[df_weekly['iso_week'] == target_week].copy()
    
    if len(df_target) == 0:
        # For debugging: show what weeks we have
        if lead == 1:
            available_weeks = sorted(df_weekly['iso_week'].unique())
            log_info(f"    Lead 1: Need week {target_week}, have weeks {available_weeks}")
        return None
    
    # Add metadata
    target_start = forecast_date + timedelta(days=lead * 7)
    # Adjust to Monday of the week
    target_start = target_start - timedelta(days=target_start.weekday())
    target_end = target_start + timedelta(days=6)
    
    df_target['forecast_base'] = forecast_date.strftime('%Y-%m-%d')
    df_target['target_period_start'] = target_start.strftime('%Y-%m-%d')
    df_target['target_period_end'] = target_end.strftime('%Y-%m-%d')
    df_target['lead_weeks'] = lead
    
    return df_target


def run_backfill(start_week=1, end_date=None, force=False):
    """Run backfill for all weeks"""
    import xgboost as xgb
    import json
    
    log_header("Backfill Historical Predictions")
    
    if force:
        log_info("⚠️  FORCE mode: will regenerate ALL predictions")
    
    # Get cache range
    cache_min, cache_max = get_cached_date_range()
    if cache_min is None:
        log_info("No cached data found!")
        return
    
    log_info(f"Cache range: {cache_min} to {cache_max}")
    
    if end_date is None:
        end_date = cache_max
    
    # Load models
    log_step("Loading models...")
    models = {}
    configs = {}
    
    for lead in [0, 1]:
        model_path = MODEL_DIR / f"near_term_lead_{lead}"
        model = xgb.Booster()
        model.load_model(str(model_path / "model.json"))
        with open(model_path / "config.json") as f:
            config = json.load(f)
        models[lead] = model
        configs[lead] = config
    
    log_info("Models loaded: Lead 0, Lead 1")
    
    # Create history directory
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all days from January 1st to end_date
    year = datetime.strptime(str(cache_min), '%Y-%m-%d').year if isinstance(cache_min, str) else cache_min.year
    jan1 = datetime(year, 1, 1)
    
    # Start from January 1st (or later if start_week > 1)
    if start_week > 1:
        # Find first Monday of start_week
        first_monday = jan1 + timedelta(days=(7 - jan1.weekday()) % 7)
        first_day = first_monday + timedelta(weeks=start_week - 1)
    else:
        first_day = jan1  # Start from January 1st
    
    # Generate all forecast dates (EVERY DAY)
    forecast_dates = []
    current = first_day
    end_dt = datetime.combine(end_date, datetime.min.time()) if isinstance(end_date, type(cache_max)) else end_date
    
    while current <= end_dt:
        forecast_dates.append(current)
        current += timedelta(days=1)  # Every day!
    
    log_info(f"Will generate predictions for {len(forecast_dates)} days")
    
    # Check existing predictions (unless force mode)
    if force:
        dates_to_process = forecast_dates
        log_info(f"Will regenerate ALL {len(dates_to_process)} days")
    else:
        existing_dates = set()
        for f in HISTORY_DIR.glob("*_lead_0.csv"):
            date_str = f.stem.replace("_lead_0", "")
            existing_dates.add(date_str)
        
        log_info(f"Existing predictions: {len(existing_dates)} days")
        
        # Filter out already processed dates
        dates_to_process = [d for d in forecast_dates 
                            if d.strftime('%Y-%m-%d') not in existing_dates]
        
        if not dates_to_process:
            log_info("All predictions already exist! Nothing to do.")
            log_info("Use --force to regenerate all predictions.")
            return
        
        log_info(f"Missing predictions: {len(dates_to_process)} days")
    
    # Process each day
    for i, forecast_date in enumerate(dates_to_process):
        log_step(f"[{i+1}/{len(dates_to_process)}] Processing {forecast_date.strftime('%Y-%m-%d')}...")
        
        # Load data up to this date
        df_weekly = load_cached_data_for_period(forecast_date.date())
        
        if df_weekly is None or len(df_weekly) == 0:
            log_info("  No data available, skipping")
            continue
        
        # Generate predictions for each lead
        for lead in [0, 1]:
            df_inference = create_inference_dataset(df_weekly, forecast_date, lead)
            
            if df_inference is None or len(df_inference) == 0:
                continue
            
            # Prepare features
            features = configs[lead]['features']
            for f in features:
                if f not in df_inference.columns:
                    df_inference[f] = 0
            
            X = df_inference[features].values
            dmatrix = xgb.DMatrix(X, feature_names=features)
            
            # Predict
            predictions = models[lead].predict(dmatrix)
            df_inference['risk_score'] = np.clip(predictions, 1, 5).round(2)
            df_inference['risk_level'] = df_inference['risk_score'].apply(lambda x: int(np.clip(np.round(x), 1, 5)))
            
            # Save to history
            history_file = HISTORY_DIR / f"{forecast_date.strftime('%Y-%m-%d')}_lead_{lead}.csv"
            
            # Select output columns
            output_cols = ['NUTS_3', 'forecast_base', 'target_period_start', 'target_period_end',
                          'lead_weeks', 'risk_score', 'risk_level', 'temp', 'prec', 'rh', 'lw']
            output_cols = [c for c in output_cols if c in df_inference.columns]
            
            df_inference[output_cols].to_csv(history_file, index=False)
        
        n_saved = sum([1 for lead in [0, 1] if (HISTORY_DIR / f"{forecast_date.strftime('%Y-%m-%d')}_lead_{lead}.csv").exists()])
        if n_saved == 2:
            log_info(f"  ✓ Saved predictions for {forecast_date.strftime('%Y-%m-%d')} (Lead 0, Lead 1)")
        elif n_saved == 1:
            log_info(f"  ⚠ Saved only Lead 0 for {forecast_date.strftime('%Y-%m-%d')} (Lead 1: data not available)")
    
    log_header("Backfill Complete!")
    log_info(f"Predictions saved to: {HISTORY_DIR}")
    
    # Summary
    n_files = len(list(HISTORY_DIR.glob("*.csv")))
    log_info(f"Total prediction files: {n_files}")


def main():
    parser = argparse.ArgumentParser(description='Backfill historical predictions')
    parser.add_argument('--start-week', type=int, default=1,
                       help='Starting ISO week (default: 1)')
    parser.add_argument('--end-date', type=str, default=None,
                       help='End date in YYYY-MM-DD format (default: latest cached)')
    parser.add_argument('--force', action='store_true',
                       help='Force regeneration of all predictions (ignore existing)')
    
    args = parser.parse_args()
    
    end_date = None
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    
    run_backfill(start_week=args.start_week, end_date=end_date, force=args.force)


if __name__ == "__main__":
    main()
