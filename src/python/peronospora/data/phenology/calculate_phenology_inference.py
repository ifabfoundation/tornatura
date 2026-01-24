"""
Phenology Calculation for Inference
=====================================
Calculates plant phenology states from current NetCDF weather forecast data
for use in disease risk prediction.

This script:
1. Reads NetCDF forecast data from ../province_netcdf/
2. Extracts daily min/max temperatures
3. Runs dormancy and forcing models
4. Outputs phenology CSV files to phenology_csv/

Usage:
    python calculate_phenology_inference.py
"""

import os
import sys
import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from peronospora.data.phenology.data_structures import InputDaily, Output
from peronospora.data.phenology.parameters_loader import load_parameters
from peronospora.data.phenology.dormancy import Dormancy
from peronospora.data.phenology.forcing import Forcing


def extract_daily_temperatures(ds: xr.Dataset) -> pd.DataFrame:
    """
    Extract daily min/max temperatures from NetCDF hourly data.

    For inference, we typically have a single forecast with multiple steps.
    """
    print("  Extracting daily temperatures from forecast...")

    # Check if time is a dimension or a scalar coordinate
    if 'time' in ds.dims:
        # time is a dimension (old format)
        forecast_base = ds.time.values[0] if len(ds.time) > 0 else ds.time.values
        t2m_spatial_mean = ds.t2m.isel(time=0).mean(dim=['latitude', 'longitude'])
        t2m_vals = t2m_spatial_mean.values - 273.15  # K to °C
        valid_times = forecast_base + ds.step.values
    else:
        # time is a scalar coordinate (new AWS S3 format)
        forecast_base = pd.Timestamp(ds.time.values)
        # Extract hourly temperature data - shape is (step, lat, lon)
        t2m_spatial_mean = ds.t2m.mean(dim=['latitude', 'longitude'])
        t2m_vals = t2m_spatial_mean.values - 273.15  # K to °C
        # valid_times from step coordinate
        valid_times = forecast_base + pd.to_timedelta(ds.step.values)
    
    # Create hourly DataFrame
    df_hourly = pd.DataFrame({
        'valid_time': pd.to_datetime(valid_times),
        't2m': t2m_vals
    })
    
    # Extract date components
    df_hourly['date'] = df_hourly['valid_time'].dt.date
    df_hourly['year'] = df_hourly['valid_time'].dt.year
    df_hourly['month'] = df_hourly['valid_time'].dt.month
    df_hourly['day'] = df_hourly['valid_time'].dt.day
    df_hourly['forecast_day'] = ((df_hourly['valid_time'] - pd.Timestamp(forecast_base)).dt.total_seconds() / 86400).astype(int) + 1
    
    # Group by date and calculate daily min/max
    daily = df_hourly.groupby(['date', 'year', 'month', 'day', 'forecast_day']).agg({
        't2m': ['min', 'max']
    }).reset_index()
    
    # Flatten column names
    daily.columns = ['date', 'year', 'month', 'day', 'forecast_day', 'temp_min', 'temp_max']
    daily['forecast_base'] = forecast_base
    
    return daily


def process_province_phenology_inference(province_name: str, nc_file: str, parameters, output_dir: str) -> bool:
    """
    Process phenology for a single province for inference.
    
    Unlike training, we don't reset states at Jan 1st. Instead, we:
    1. Need to load previous phenology state OR
    2. Calculate from start of year up to current forecast
    """
    print(f"Processing {province_name}...")
    
    try:
        # Load NetCDF dataset
        ds = xr.open_dataset(nc_file)
        
        # Check if required variables exist
        if 't2m' not in ds.variables:
            print(f"  Error: t2m variable not found")
            ds.close()
            return False
        
        # Extract daily temperatures
        df_daily = extract_daily_temperatures(ds)
        ds.close()
        
        print(f"  Forecast days: {df_daily['forecast_day'].min()} to {df_daily['forecast_day'].max()}")
        print(f"  Date range: {df_daily['date'].min()} to {df_daily['date'].max()}")
        
        # Initialize phenology state
        # For inference, we need to calculate state from Jan 1st to current date
        # This ensures continuity across forecasts
        
        forecast_start_date = pd.to_datetime(df_daily['date'].min())
        year = forecast_start_date.year
        
        # We need historical data from Jan 1 to current date to build up state
        # For now, we'll initialize from the forecast start
        # In production, you'd want to persist state between runs
        
        output = Output()
        results = []
        
        # Sort by date to process sequentially
        df_daily = df_daily.sort_values('date')
        
        for _, row in df_daily.iterrows():
            # Create input for this day
            input_daily = InputDaily(temp_min=row['temp_min'], temp_max=row['temp_max'])
            
            # Run dormancy model
            Dormancy.run_dormancy(input_daily, parameters, output)
            
            # Run forcing model
            Forcing.run_forcing(input_daily, parameters, output)
            
            # Store results
            result = {
                'site': province_name.lower().replace(' ', '_'),
                'forecast_base': row['forecast_base'],
                'forecast_day': row['forecast_day'],
                'year': row['year'],
                'month': row['month'],
                'day': row['day'],
                'chill_state': round(output.outputs_phenology.chill_state, 2),
                'anti_chill_state': round(output.outputs_phenology.anti_chill_state, 2),
                'forcing_state': round(output.outputs_phenology.forcing_state, 1),
                'bbch_code': round(output.outputs_phenology.bbch_phenophase_code, 1),
                'plant_susceptibility': round(output.outputs_phenology.plant_susceptibility, 3)
            }
            results.append(result)
        
        # Create DataFrame
        df_results = pd.DataFrame(results)
        
        # Save to CSV
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{province_name.lower().replace(' ', '_')}_phenology.csv")
        df_results.to_csv(output_file, index=False)
        
        print(f"  ✓ Saved {len(df_results)} records")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution pipeline for inference phenology calculation."""
    print("="*80)
    print("PHENOLOGY CALCULATION - INFERENCE")
    print("="*80)
    
    # Define paths
    script_dir = Path(__file__).parent
    parameters_dir = script_dir / "parameters"
    netcdf_dir = script_dir.parent / "province_netcdf"
    output_dir = script_dir / "phenology_csv"
    
    print(f"\nParameters directory: {parameters_dir}")
    print(f"NetCDF directory: {netcdf_dir}")
    print(f"Output directory: {output_dir}")
    
    # Load parameters
    print("\n" + "="*80)
    print("LOADING PARAMETERS")
    print("="*80)
    parameters = load_parameters(str(parameters_dir))
    print("✓ Parameters loaded successfully")
    
    # Find all NetCDF files
    print("\n" + "="*80)
    print("FINDING NETCDF FILES")
    print("="*80)
    
    if not netcdf_dir.exists():
        print(f"❌ NetCDF directory not found: {netcdf_dir}")
        print("   Please run grib_to_provinces.py first!")
        return
    
    nc_files = list(netcdf_dir.glob("*.nc"))
    
    if not nc_files:
        print(f"❌ No NetCDF files found in {netcdf_dir}")
        return
    
    print(f"Found {len(nc_files)} NetCDF files")
    
    # Process each province
    print("\n" + "="*80)
    print("PROCESSING PROVINCES")
    print("="*80)
    
    successful = []
    failed = []
    
    for i, nc_file in enumerate(sorted(nc_files), 1):
        # Extract province name from filename
        province_name = nc_file.stem.replace('_', ' ').title()
        
        print(f"\n[{i}/{len(nc_files)}] {province_name}")
        
        success = process_province_phenology_inference(province_name, str(nc_file), parameters, str(output_dir))
        
        if success:
            successful.append(province_name)
        else:
            failed.append(province_name)
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n✅ Successfully processed: {len(successful)} provinces")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)} provinces")
        for province in failed:
            print(f"  - {province}")
    
    print("\n" + "="*80)
    print("DONE!")
    print("="*80)
    print(f"\nPhenology CSV files saved to: {output_dir}/")
    print("Ready to merge with weather data for inference.")


if __name__ == "__main__":
    main()

