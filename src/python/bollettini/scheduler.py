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

import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from bollettini import paths
from bollettini.modules.config import REGIONI

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
LOG_DIR = paths.RUNTIME_DIR / "logs"
CACHE_DIR = paths.DATA_DIR / "cache"

# Scheduler settings
SCHEDULE_HOUR = 8
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

    status = {
        "downloads_by_region": {},
        "reports_by_region": {},
        "bollettini_downloaded": 0,
        "bollettini_indexed": 0,
        "colture_reports": 0,
        "last_download_check": "Never",
        "last_processing": "Never",
        "last_report_run": "Never",
    }

    last_download_checks: list[str] = []
    last_report_runs: list[str] = []

    for region_id in REGIONI:
        download_cache = paths.DATA_DIR / "input_bollettini" / region_id / "cache_download.json"
        downloaded = 0
        if download_cache.exists():
            with open(download_cache, encoding="utf-8") as f:
                data = json.load(f)
            downloaded = sum(len(entry.get("downloaded_ids", [])) for entry in data.get("provinces", {}).values())
            if data.get("last_updated"):
                last_download_checks.append(data["last_updated"])
        status["downloads_by_region"][region_id] = downloaded
        status["bollettini_downloaded"] += downloaded

        report_cache = CACHE_DIR / f"colture_{region_id}_processed.json"
        report_count = 0
        if report_cache.exists():
            with open(report_cache, encoding="utf-8") as f:
                data = json.load(f)
            report_count = len(data.get("processed", {}))
            if data.get("last_run"):
                last_report_runs.append(data["last_run"])
        status["reports_by_region"][region_id] = report_count
        status["colture_reports"] += report_count

    processing_cache = CACHE_DIR / "processing_cache.json"
    if processing_cache.exists():
        with open(processing_cache, encoding="utf-8") as f:
            data = json.load(f)
        status["bollettini_indexed"] = len(data.get("processed_files", []))
        status["last_processing"] = data.get("last_updated", "Never")

    if last_download_checks:
        status["last_download_check"] = max(last_download_checks)
    if last_report_runs:
        status["last_report_run"] = max(last_report_runs)

    return status


def print_status():
    """Print current system status"""
    status = get_cache_status()
    
    print("\n" + "="*60)
    print("RAG BOLLETTINI - SYSTEM STATUS")
    print("="*60)
    print(f"Bollettini scaricati:    {status['bollettini_downloaded']}")
    print(f"Bollettini indicizzati:  {status['bollettini_indexed']}")
    print(f"Report colture:          {status['colture_reports']}")
    print("-"*60)
    for region_id, region_data in REGIONI.items():
        print(
            f"{region_data['nome']:<22}"
            f"download={status['downloads_by_region'][region_id]:<4} "
            f"report={status['reports_by_region'][region_id]}"
        )
    print("-"*60)
    print(f"Ultimo check download:   {status['last_download_check']}")
    print(f"Ultimo processing:       {status['last_processing']}")
    print(f"Ultima query colture:    {status['last_report_run']}")
    print("="*60 + "\n")


# =============================================================================
# PIPELINE EXECUTION
# =============================================================================

def run_pipeline_job():
    """Execute the RAG pipeline"""
    start_time = datetime.now()
    logger.info("="*60)
    logger.info("STARTING RAG BOLLETTINI PIPELINE")
    logger.info("="*60)

    try:
        logger.info("Executing bollettini.run_pipeline")
        from bollettini.run_pipeline import run_pipeline as execute_pipeline

        exit_code = execute_pipeline()
        elapsed = datetime.now() - start_time

        if exit_code == 0:
            logger.info(f"Pipeline completed: NEW DATA PROCESSED ({elapsed.total_seconds():.1f}s)")
            return True, "New data processed"
        if exit_code == 1:
            logger.info(f"Pipeline completed: No new data ({elapsed.total_seconds():.1f}s)")
            return True, "No new data"

        logger.error(f"Pipeline failed with return code: {exit_code}")
        return False, f"Failed with code {exit_code}"
    except Exception as e:
        logger.exception(f"Pipeline execution error: {str(e)}")
        return False, str(e)


def scheduled_job():
    """Wrapper for scheduled execution with error handling"""
    try:
        success, message = run_pipeline_job()
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
    logger.info("Pipeline: bollettini.run_pipeline")
    logger.info(f"Logs: {LOG_DIR}")
    
    # Print current status
    status = get_cache_status()
    logger.info(f"Current status: {status['bollettini_downloaded']} downloaded, "
                f"{status['bollettini_indexed']} indexed, "
                f"{status['colture_reports']} culture reports")
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
        success, message = run_pipeline_job()
        print(f"\nResult: {'SUCCESS' if success else 'FAILED'} - {message}")
        sys.exit(0 if success else 1)
    
    # Default: start scheduler
    start_scheduler()


if __name__ == "__main__":
    main()
