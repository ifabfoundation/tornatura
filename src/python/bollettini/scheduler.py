#!/usr/bin/env python3
"""
RAG Bollettini - Scheduler
==========================
Runs the pipeline daily at 08:00 CET to check for new bulletins.

Bulletins are published bi-weekly, but we run daily to catch them
on the exact day they're released.

Usage:
    python scheduler.py                 # Run scheduler (foreground)
    python scheduler.py --run-now       # Run pipeline immediately (for testing)
    python scheduler.py --status        # Show cache status

To run as a background service:
    nohup python scheduler.py > scheduler.log 2>&1 &

Author: Vito (with AI assistance)
Date: January 2026
"""

import os
import sys
import subprocess
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
PIPELINE_SCRIPT = SCRIPT_DIR / "run_pipeline.py"
LOG_DIR = SCRIPT_DIR / "logs"
VENV_PYTHON = SCRIPT_DIR / "venv" / "bin" / "python"
CACHE_DIR = SCRIPT_DIR / "data" / "cache"

# Scheduler settings
SCHEDULE_HOUR = 7
SCHEDULE_MINUTE = 0
TIMEZONE = "Europe/Rome"  # CET/CEST

# =============================================================================
# LOGGING SETUP
# =============================================================================

LOG_DIR.mkdir(exist_ok=True)

# Create logger
logger = logging.getLogger("rag_bollettini_scheduler")
logger.setLevel(logging.INFO)

# Prevent duplicate handlers
if not logger.handlers:
    # File handler (monthly rotation via filename)
    log_file = LOG_DIR / f"scheduler_{datetime.now().strftime('%Y%m')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# =============================================================================
# STATUS CHECK FUNCTIONS
# =============================================================================

def get_cache_status():
    """Get status of all caches"""
    import json
    
    status = {}
    data_dir = SCRIPT_DIR / "data"
    
    # Bollettini download cache (in data/, not data/cache/)
    bollettini_cache = data_dir / "bollettini_cache.json"
    if bollettini_cache.exists():
        with open(bollettini_cache) as f:
            data = json.load(f)
        total = sum(len(p.get('downloaded_ids', [])) for p in data.get('provinces', {}).values())
        status['bollettini_downloaded'] = total
        status['last_download_check'] = data.get('last_updated', 'N/A')
    else:
        status['bollettini_downloaded'] = 0
        status['last_download_check'] = 'Never'
    
    # Processing cache (in data/, not data/cache/)
    processing_cache = data_dir / "processing_cache.json"
    if processing_cache.exists():
        with open(processing_cache) as f:
            data = json.load(f)
        status['bollettini_indexed'] = len(data.get('processed_files', []))
        status['last_processing'] = data.get('last_updated', 'N/A')
    else:
        status['bollettini_indexed'] = 0
        status['last_processing'] = 'Never'
    
    # Cimice query cache (in data/cache/)
    cimice_cache = CACHE_DIR / "cimice_processed.json"
    if cimice_cache.exists():
        with open(cimice_cache) as f:
            data = json.load(f)
        status['cimice_reports'] = len(data.get('processed', {}))
    else:
        status['cimice_reports'] = 0
    
    # Flavescenza query cache
    flavescenza_cache = CACHE_DIR / "flavescenza_processed.json"
    if flavescenza_cache.exists():
        with open(flavescenza_cache) as f:
            data = json.load(f)
        status['flavescenza_reports'] = len(data.get('processed', {}))
    else:
        status['flavescenza_reports'] = 0
    
    return status


def print_status():
    """Print current system status"""
    status = get_cache_status()
    
    print("\n" + "="*60)
    print("RAG BOLLETTINI - SYSTEM STATUS")
    print("="*60)
    print(f"Bollettini scaricati:    {status['bollettini_downloaded']}")
    print(f"Bollettini indicizzati:  {status['bollettini_indexed']}")
    print(f"Report Cimice:           {status['cimice_reports']}")
    print(f"Report Flavescenza:      {status['flavescenza_reports']}")
    print("-"*60)
    print(f"Ultimo check download:   {status['last_download_check']}")
    print(f"Ultimo processing:       {status['last_processing']}")
    print("="*60 + "\n")


# =============================================================================
# PIPELINE EXECUTION
# =============================================================================

def run_pipeline():
    """Execute the RAG pipeline"""
    start_time = datetime.now()
    logger.info("="*60)
    logger.info("STARTING RAG BOLLETTINI PIPELINE")
    logger.info("="*60)
    
    # Check if pipeline script exists
    if not PIPELINE_SCRIPT.exists():
        logger.error(f"Pipeline script not found: {PIPELINE_SCRIPT}")
        return False, "Pipeline script not found"
    
    # Check if venv python exists
    python_exec = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    logger.info(f"Using Python: {python_exec}")
    
    # Run the pipeline
    try:
        logger.info(f"Executing: {PIPELINE_SCRIPT}")
        
        result = subprocess.run(
            [python_exec, str(PIPELINE_SCRIPT)],
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        # Log output (summarized)
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            # Log only key lines (skip duplicates and verbose OCR logs)
            seen = set()
            for line in lines:
                # Skip OCR/RapidOCR verbose logs
                if '[RapidOCR]' in line or 'onnxruntime' in line:
                    continue
                # Skip duplicate lines
                clean_line = line.split(' - ')[-1] if ' - ' in line else line
                if clean_line in seen:
                    continue
                seen.add(clean_line)
                logger.info(f"[PIPELINE] {line[:200]}")  # Truncate long lines
        
        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                if line.strip() and 'RapidOCR' not in line and 'onnxruntime' not in line:
                    logger.warning(f"[STDERR] {line[:200]}")
        
        elapsed = datetime.now() - start_time
        
        if result.returncode == 0:
            logger.info(f"Pipeline completed: NEW DATA PROCESSED ({elapsed.total_seconds():.1f}s)")
            return True, "New data processed"
        elif result.returncode == 1:
            logger.info(f"Pipeline completed: No new data ({elapsed.total_seconds():.1f}s)")
            return True, "No new data"
        else:
            logger.error(f"Pipeline failed with return code: {result.returncode}")
            return False, f"Failed with code {result.returncode}"
    
    except subprocess.TimeoutExpired:
        logger.error("Pipeline timed out after 30 minutes")
        return False, "Timeout"
    except Exception as e:
        logger.error(f"Pipeline execution error: {str(e)}")
        return False, str(e)


def scheduled_job():
    """Wrapper for scheduled execution with error handling"""
    try:
        success, message = run_pipeline()
        if success:
            logger.info(f"Scheduled job completed: {message}")
        else:
            logger.error(f"Scheduled job failed: {message}")
    except Exception as e:
        logger.exception(f"Unexpected error in scheduled job: {str(e)}")


# =============================================================================
# SCHEDULER
# =============================================================================

def start_scheduler():
    """Start the APScheduler"""
    logger.info("="*60)
    logger.info("RAG BOLLETTINI SCHEDULER")
    logger.info("="*60)
    logger.info(f"Schedule: Daily at {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} {TIMEZONE}")
    logger.info(f"Pipeline: {PIPELINE_SCRIPT}")
    logger.info(f"Logs: {LOG_DIR}")
    
    # Print current status
    status = get_cache_status()
    logger.info(f"Current status: {status['bollettini_downloaded']} downloaded, "
                f"{status['bollettini_indexed']} indexed, "
                f"{status['cimice_reports']} cimice reports, "
                f"{status['flavescenza_reports']} flavescenza reports")
    logger.info("="*60)
    
    scheduler = BlockingScheduler(timezone=TIMEZONE)
    
    # Add daily job
    scheduler.add_job(
        scheduled_job,
        CronTrigger(
            hour=SCHEDULE_HOUR,
            minute=SCHEDULE_MINUTE,
            timezone=TIMEZONE
        ),
        id='daily_bollettini',
        name='Daily RAG Bollettini Pipeline',
        misfire_grace_time=3600  # 1 hour grace period
    )
    
    # Log next run time
    jobs = scheduler.get_jobs()
    if jobs:
        job = jobs[0]
        if hasattr(job, 'next_run_time') and job.next_run_time:
            next_run = job.next_run_time
            logger.info(f"Next scheduled run: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            logger.info("Job scheduled successfully")
    
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user")
        scheduler.shutdown()


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='RAG Bollettini Scheduler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scheduler.py                 # Start scheduler (runs at 08:00 daily)
  python scheduler.py --run-now       # Run pipeline immediately
  python scheduler.py --status        # Show current cache status
        """
    )
    parser.add_argument('--run-now', action='store_true',
                       help='Run the pipeline immediately (for testing)')
    parser.add_argument('--status', action='store_true',
                       help='Show current cache and system status')
    
    args = parser.parse_args()
    
    if args.status:
        print_status()
        sys.exit(0)
    
    if args.run_now:
        logger.info("Running pipeline immediately (--run-now)")
        success, message = run_pipeline()
        print(f"\nResult: {'SUCCESS' if success else 'FAILED'} - {message}")
        sys.exit(0 if success else 1)
    
    # Default: start scheduler
    start_scheduler()


if __name__ == "__main__":
    main()
