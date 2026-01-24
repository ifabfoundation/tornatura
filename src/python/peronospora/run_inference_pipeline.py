#!/usr/bin/env python3
"""
Complete Inference Pipeline for Peronospora Risk Prediction
============================================================
This script runs the entire inference pipeline:
1. Prepares inference data from ECMWF forecasts
2. Runs model predictions for all lead times
3. Generates risk maps

Usage:
    python run_inference_pipeline.py
    python run_inference_pipeline.py --skip-data-prep  # Skip data preparation
    python run_inference_pipeline.py --no-map          # Skip map generation
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import argparse


def print_step(step_num, title):
    """Print a formatted step header"""
    print("\n" + "="*80)
    print(f"STEP {step_num}: {title}")
    print("="*80 + "\n")


def run_command(cmd, description, check=True):
    """Run a shell command and handle errors"""
    print(f"→ {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ {description} completed successfully")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"✗ {description} failed")
            if result.stderr:
                print("Error:", result.stderr)
            return False
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with error:")
        print(e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Run complete inference pipeline for Peronospora risk prediction',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--skip-data-prep',
        action='store_true',
        help='Skip data preparation step (use existing data)'
    )

    parser.add_argument(
        '--no-map',
        action='store_true',
        help='Skip map generation'
    )

    parser.add_argument(
        '--lead',
        type=int,
        choices=[0, 1],
        default=None,
        help='Run prediction for specific lead only (default: all leads)'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent

    print("\n" + "="*80)
    print("PERONOSPORA RISK PREDICTION - COMPLETE INFERENCE PIPELINE")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {script_dir}")

    # Step 1: Prepare inference data (with cache)
    if not args.skip_data_prep:
        print_step(1, "PREPARE INFERENCE DATA")
        success = run_command(
            f"cd {script_dir} && python data/prepare_inference_data.py",
            "Preparing inference data (historical + forecast, with cache)"
        )
        if not success:
            print("\n❌ Pipeline failed at data preparation step")
            return 1
    else:
        print_step(1, "PREPARE INFERENCE DATA (SKIPPED)")
        print("Using existing inference data")

    # Step 2: Run model predictions
    print_step(2, "RUN MODEL PREDICTIONS")

    if args.lead is None:
        # Run all leads
        success = run_command(
            f"cd {script_dir} && python model.py --all",
            "Running predictions for all lead times (0, 1 weeks)"
        )
    else:
        # Run specific lead
        success = run_command(
            f"cd {script_dir} && python model.py --lead {args.lead}",
            f"Running predictions for lead {args.lead}"
        )

    if not success:
        print("\n❌ Pipeline failed at model prediction step")
        return 1

    # Step 3: Generate risk map
    if not args.no_map:
        print_step(3, "GENERATE RISK MAP")
        success = run_command(
            f"cd {script_dir} && python plot_risk_map.py",
            "Creating interactive satellite risk map"
        )
        if not success:
            print("\n⚠️ Warning: Map generation failed, but continuing...")
    else:
        print_step(3, "GENERATE RISK MAP (SKIPPED)")

    # Summary
    print("\n" + "="*80)
    print("✓ PIPELINE COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n📊 OUTPUT FILES:")
    print(f"  • Predictions:  {script_dir}/predictions/lead_0.csv, lead_1.csv")

    if not args.no_map:
        print(f"  • Risk Map:     {script_dir}/risk_map_satellite.html")

    print("\n📖 NEXT STEPS:")
    print("  1. Open 'risk_map_satellite.html' in your browser to view the interactive map")
    print("  2. Use predictions CSV files for further analysis")

    return 0


if __name__ == "__main__":
    sys.exit(main())
