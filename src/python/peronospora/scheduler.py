#!/usr/bin/env python3
"""
Peronospora Inference Pipeline Scheduler
=========================================

Scheduler automatico che esegue la pipeline di inferenza ogni giorno alle 09:00 CET.

ECMWF pubblica i dati forecast su S3 tra le 06:45 e le 08:34 CET, quindi
l'orario delle 09:00 garantisce un margine sicuro per la disponibilità dei dati.

COMPONENTI PRINCIPALI:
----------------------
1. CONFIGURAZIONE: Percorsi file, orario esecuzione, timezone
2. LOGGING: Sistema di log su file e console
3. DATA CHECK: Verifica disponibilità dati S3 prima dell'esecuzione
4. PIPELINE EXECUTION: Lancio della pipeline con gestione errori
5. SCHEDULER: APScheduler con trigger cron giornaliero
6. CLI: Interfaccia command-line con opzioni --run-now e --check-data

UTILIZZO:
---------
    python scheduler.py                 # Avvia scheduler (esegue alle 09:00)
    python scheduler.py --run-now       # Esegue pipeline subito (per test)
    python scheduler.py --check-data    # Verifica disponibilità dati S3

ESECUZIONE IN BACKGROUND:
-------------------------
    nohup python scheduler.py > logs/scheduler_output.log 2>&1 &

INTEGRAZIONE SYSTEMD:
---------------------
    Vedi DEVELOPER_GUIDE.md per configurazione servizio systemd

Author: Vito (with AI assistance)
Date: January 2026
Version: 2.0
"""

import os
import subprocess
import sys
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import boto3

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))
from peronospora import paths


# =============================================================================
# SEZIONE 1: CONFIGURAZIONE
# =============================================================================
# Definisce tutti i percorsi e parametri necessari per il funzionamento
# dello scheduler. Modificare questi valori per personalizzare il comportamento.

# Percorsi file
SCRIPT_DIR = Path(__file__).parent.resolve()      # Directory dello scheduler
PIPELINE_SCRIPT = SCRIPT_DIR / "run_inference_pipeline.py"  # Script principale
LOG_DIR = paths.RUNTIME_DIR / "logs"               # Directory per i log

# Configurazione orario esecuzione
SCHEDULE_HOUR = 9       # Ora di esecuzione (09:00)
SCHEDULE_MINUTE = 0     # Minuto di esecuzione
TIMEZONE = "Europe/Rome"  # Timezone CET/CEST

# Timeout pipeline (30 minuti)
PIPELINE_TIMEOUT = 1800


# =============================================================================
# SEZIONE 2: LOGGING
# =============================================================================
# Configura il sistema di logging per registrare tutte le operazioni.
# I log vengono salvati sia su file (mensile) che su console.

LOG_DIR.mkdir(exist_ok=True)

# Crea logger principale
logger = logging.getLogger("peronospora_scheduler")
logger.setLevel(logging.INFO)

# Handler per file (rotazione mensile tramite nome file)
# Es: scheduler_202601.log, scheduler_202602.log, ...
log_file = LOG_DIR / f"scheduler_{datetime.now().strftime('%Y%m')}.log"
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Handler per console (stdout)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Formato log: timestamp | livello | messaggio
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Aggiunge handler al logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# =============================================================================
# SEZIONE 3: VERIFICA DATI S3
# =============================================================================
# Funzioni per verificare la disponibilità dei dati meteo su S3.
# Controlla che ci siano almeno 100 file forecast per la data odierna.

def check_todays_data_available():
    """
    Verifica se i dati forecast di oggi sono disponibili su S3.
    
    ECMWF pubblica nuovi dati ogni giorno tra le 06:45-08:34 CET.
    Questa funzione controlla che ci siano almeno 100 file per
    la data odierna (240 step orari = ~240 file attesi).
    
    Returns:
        tuple: (bool, str) - (disponibilità, messaggio descrittivo)
        
    Esempio:
        >>> available, msg = check_todays_data_available()
        >>> print(f"Dati: {'OK' if available else 'NON DISPONIBILI'} - {msg}")
    """
    try:
        import boto3

        s3 = boto3.client('s3')
        bucket = 'ecmwf-data-forecast'
        today_str = datetime.now().strftime('%Y%m%d')

        # Usa paginazione per cercare tutti gli oggetti
        today_files = []
        continuation_token = None

        while True:
            # Richiesta paginata a S3
            if continuation_token:
                response = s3.list_objects_v2(
                    Bucket=bucket,
                    ContinuationToken=continuation_token
                )
            else:
                response = s3.list_objects_v2(Bucket=bucket)

            if 'Contents' not in response:
                break

            # Filtra file della data odierna con pattern forecast
            for obj in response['Contents']:
                if today_str in obj['Key'] and '_fc_' in obj['Key']:
                    today_files.append(obj['Key'])

            # Se abbiamo trovato abbastanza file, interrompi
            if len(today_files) >= 100:
                break

            # Continua se ci sono altre pagine
            if response.get('IsTruncated'):
                continuation_token = response['NextContinuationToken']
            else:
                break

        # Verifica quantità minima file
        if len(today_files) == 0:
            return False, f"Nessun file per {today_str}"

        if len(today_files) < 100:
            return False, f"Solo {len(today_files)} file per {today_str} (servono 100+)"

        return True, f"Trovati {len(today_files)}+ file per {today_str}"

    except Exception as e:
        return False, f"Errore verifica S3: {str(e)}"


# =============================================================================
# SEZIONE 4: ESECUZIONE PIPELINE
# =============================================================================
# Funzioni per eseguire la pipeline di inferenza come sottoprocesso.
# Include gestione errori, timeout, e logging dettagliato.
def run_inference_pipeline():
    """
    Esegue la pipeline di inferenza completa.
    
    Questa funzione:
    1. Verifica disponibilità dati S3 (warning se non disponibili)
    2. Controlla esistenza script pipeline
    3. Determina Python da usare (venv o sistema)
    4. Esegue run_inference_pipeline.py come sottoprocesso
    5. Cattura e logga stdout/stderr
    6. Gestisce timeout (30 min) e errori
    
    Returns:
        bool: True se pipeline completata con successo, False altrimenti
        
    Note:
        - La pipeline viene eseguita anche se i dati S3 non sono disponibili
          (userà la cache + dati disponibili)
        - Timeout di 30 minuti per evitare blocchi indefiniti
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("AVVIO PERONOSPORA INFERENCE PIPELINE")
    logger.info("=" * 60)

    # Step 1: Verifica disponibilità dati
    data_ok, data_msg = check_todays_data_available()
    logger.info(f"Verifica dati: {data_msg}")

    if not data_ok:
        logger.warning("Dati di oggi non ancora disponibili. "
                      "Esecuzione comunque (userà cache + dati disponibili)")

    # Step 2: Verifica esistenza script pipeline
    if not PIPELINE_SCRIPT.exists():
        logger.error(f"Script pipeline non trovato: {PIPELINE_SCRIPT}")
        return False

    # Step 3: Determina Python da usare
    python_exec = sys.executable
    env = os.environ.copy()
    env["PERONOSPORA_RUNTIME_DIR"] = paths.RUNTIME_DIR

    # Step 4: Esegue pipeline
    try:
        logger.info(f"Esecuzione: {PIPELINE_SCRIPT}")

        result = subprocess.run(
            [python_exec, str(PIPELINE_SCRIPT)],
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            env=env,
            timeout=PIPELINE_TIMEOUT
        )

        # Step 5: Log output pipeline
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                logger.info(f"[PIPELINE] {line}")

        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                if line.strip():
                    logger.warning(f"[PIPELINE STDERR] {line}")

        # Step 6: Verifica risultato
        if result.returncode == 0:
            elapsed = datetime.now() - start_time
            logger.info(f"Pipeline completata con successo in {elapsed.total_seconds():.1f}s")
            return True
        else:
            logger.error(f"Pipeline fallita con codice: {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"Pipeline timeout dopo {PIPELINE_TIMEOUT // 60} minuti")
        return False
    except Exception as e:
        logger.error(f"Errore esecuzione pipeline: {str(e)}")
        return False


def scheduled_job():
    """
    Wrapper per esecuzione schedulata con gestione errori.
    
    Questa funzione viene chiamata dallo scheduler alle 09:00.
    Cattura qualsiasi eccezione per evitare che lo scheduler si fermi.
    """
    try:
        success = run_inference_pipeline()
        if success:
            logger.info("✅ Job schedulato completato con successo")
        else:
            logger.error("❌ Job schedulato fallito")
    except Exception as e:
        logger.exception(f"Errore inaspettato nel job schedulato: {str(e)}")


# =============================================================================
# SEZIONE 5: SCHEDULER
# =============================================================================
# Configura e avvia APScheduler con trigger cron giornaliero.
# Lo scheduler rimane in esecuzione continua in foreground.

def start_scheduler():
    """
    Avvia lo scheduler APScheduler.
    
    Configura un job cron che esegue la pipeline ogni giorno
    all'orario configurato (default: 09:00 Europe/Rome).
    
    Lo scheduler:
    - Rimane in esecuzione in foreground (blocking)
    - Ha una grace period di 1 ora per job mancati
    - Mostra la prossima esecuzione pianificata
    - Si ferma con Ctrl+C o SIGTERM
    
    Note:
        Per esecuzione in background, usare:
        - nohup python scheduler.py > log 2>&1 &
        - systemd service (raccomandato)
    """
    logger.info("=" * 60)
    logger.info("PERONOSPORA INFERENCE SCHEDULER")
    logger.info("=" * 60)
    logger.info(f"Orario: Ogni giorno alle {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} {TIMEZONE}")
    logger.info(f"Pipeline: {PIPELINE_SCRIPT}")
    logger.info(f"Logs: {LOG_DIR}")
    logger.info("=" * 60)

    # Crea scheduler con timezone italiano
    scheduler = BlockingScheduler(timezone=TIMEZONE)

    # Aggiunge job giornaliero alle 09:00
    scheduler.add_job(
        scheduled_job,
        CronTrigger(
            hour=SCHEDULE_HOUR,
            minute=SCHEDULE_MINUTE,
            timezone=TIMEZONE
        ),
        id='daily_inference',
        name='Daily Peronospora Inference',
        misfire_grace_time=3600  # 1 ora di grace period
    )

    # Log prossima esecuzione
    jobs = scheduler.get_jobs()
    if jobs:
        job = jobs[0]
        if hasattr(job, 'next_run_time') and job.next_run_time:
            next_run = job.next_run_time
            logger.info(f"Prossima esecuzione: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            logger.info("Job schedulato con successo")

    logger.info("Scheduler avviato. Premi Ctrl+C per fermare.")

    # Avvia scheduler (blocking)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler fermato dall'utente")
        scheduler.shutdown()


# =============================================================================
# SEZIONE 6: CLI (Command Line Interface)
# =============================================================================
# Gestisce gli argomenti da linea di comando.
# Supporta modalità: scheduler, --run-now, --check-data

def main():
    """
    Entry point principale dello scheduler.
    
    Modalità di esecuzione:
    -----------------------
    1. Nessun argomento: Avvia scheduler (esegue alle 09:00 ogni giorno)
    2. --run-now: Esegue la pipeline immediatamente (per test)
    3. --check-data: Verifica se i dati S3 di oggi sono disponibili
    
    Exit codes:
    -----------
    0: Successo
    1: Errore (pipeline fallita o dati non disponibili)
    
    Esempi:
    -------
        python scheduler.py                 # Avvia scheduler
        python scheduler.py --run-now       # Esegui subito
        python scheduler.py --check-data    # Verifica dati
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Peronospora Inference Pipeline Scheduler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python scheduler.py                 # Avvia scheduler (esegue alle 09:00)
  python scheduler.py --run-now       # Esegue pipeline immediatamente
  python scheduler.py --check-data    # Verifica disponibilità dati S3

Esecuzione in background:
  nohup python scheduler.py > logs/scheduler_output.log 2>&1 &
        """
    )
    parser.add_argument(
        '--run-now', 
        action='store_true',
        help='Esegue la pipeline immediatamente (per test)'
    )
    parser.add_argument(
        '--check-data', 
        action='store_true',
        help='Verifica se i dati forecast di oggi sono disponibili su S3'
    )

    args = parser.parse_args()

    # Modalità: verifica dati
    if args.check_data:
        available, message = check_todays_data_available()
        status = "✅ DISPONIBILI" if available else "❌ NON DISPONIBILI"
        print(f"Dati di oggi: {status}")
        print(f"Dettagli: {message}")
        sys.exit(0 if available else 1)

    # Modalità: esecuzione immediata
    if args.run_now:
        logger.info("Esecuzione immediata pipeline (--run-now)")
        success = run_inference_pipeline()
        sys.exit(0 if success else 1)

    # Modalità default: avvia scheduler
    start_scheduler()


if __name__ == "__main__":
    main()
