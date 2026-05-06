#!/usr/bin/env python3
"""
RAG Colture - Pipeline Orchestrator (multi-regione)

Coordina l'intera pipeline per l'estrazione di informazioni colturali:
1. Download nuovi bollettini (Emilia-Romagna via API, Campania via scraping)
2. Indicizzazione in ChromaDB
3. Query RAG per colture configurate per regione

Utilizzo:
    # Run completo tutte le regioni
    python run_pipeline.py

    # Solo Campania
    python run_pipeline.py --regione campania

    # Solo Emilia-Romagna
    python run_pipeline.py --regione emilia_romagna

    # Force: riesegui tutto ignorando cache
    python run_pipeline.py --force

    # Solo download (no processing/query)
    python run_pipeline.py --download-only

    # Solo query (skip download/processing)
    python run_pipeline.py --query-only

Exit codes:
    0 = Nuovi dati processati
    1 = Nessun nuovo dato (tutto aggiornato)
    2 = Errore
"""

import argparse
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Setup path per import moduli
sys.path.insert(0, str(Path(__file__).parent))

from bollettini.modules.config import REGIONI
from bollettini.modules.download_bollettini import BollettiniDownloader
from bollettini.modules.download_campania import CampaniaDownloader
from bollettini.modules.process_bollettini import BollettiniProcessor
from bollettini.modules.colture import ColtureQueryProcessor

from bollettini import paths

# Directory base
BASE_DIR = Path(__file__).parent

# Mappa regione -> (downloader_class, input_dir per processing)
REGIONE_CONFIG = {
    "emilia_romagna": {
        "downloader": BollettiniDownloader,
        "input_dir": paths.DATA_DIR / "input_bollettini" / "emilia_romagna" / "bollettini",
    },
    "campania": {
        "downloader": CampaniaDownloader,
        "input_dir": paths.DATA_DIR  / "input_bollettini" / "campania" / "bollettini",
    },
}


# ============= LOGGING =============
def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configura logging per l'orchestratore."""
    logger = logging.getLogger("pipeline_colture")

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    return logger


# ============= PIPELINE STEPS =============

def step_download(logger: logging.Logger, regione_id: str, force: bool = False) -> tuple[bool, dict]:
    """
    Step 1: Download nuovi bollettini PDF per una regione.

    Returns:
        (has_new, stats)
    """
    regione_nome = REGIONI[regione_id]["nome"]
    logger.info("=" * 70)
    logger.info(f"STEP 1: Download Bollettini - {regione_nome}")
    logger.info("=" * 70)

    try:
        config = REGIONE_CONFIG[regione_id]
        downloader = config["downloader"]()
        has_new, stats = downloader.download_all()

        logger.info(f"Download {regione_nome} completato:")
        logger.info(f"  - Trovati: {stats.get('total_found', 0)}")
        logger.info(f"  - Scaricati: {stats.get('downloaded', 0)}")
        logger.info(f"  - Skipped (cache): {stats.get('skipped', 0)}")
        logger.info(f"  - Errori: {stats.get('errors', 0)}")

        return has_new, stats

    except Exception as e:
        logger.error(f"Errore download {regione_nome}: {e}")
        return False, {'error': str(e)}


def step_process(logger: logging.Logger, regione_id: str, force: bool = False) -> tuple[bool, dict]:
    """
    Step 2: Indicizzazione PDF in ChromaDB per una regione.

    Returns:
        (has_processed, stats)
    """
    regione_nome = REGIONI[regione_id]["nome"]
    logger.info("=" * 70)
    logger.info(f"STEP 2: Indicizzazione ChromaDB - {regione_nome}")
    logger.info("=" * 70)

    try:
        config = REGIONE_CONFIG[regione_id]
        processor = BollettiniProcessor(input_dir=config["input_dir"])

        if force:
            has_processed, stats = processor.process_all(only_latest=False)
        else:
            has_processed, stats = processor.process_all(only_latest=True)

        logger.info(f"Indicizzazione {regione_nome} completata:")
        logger.info(f"  - Processati: {stats.get('processed', 0)}")
        logger.info(f"  - Totale: {stats.get('total', 0)}")
        logger.info(f"  - Cached: {stats.get('cached', 0)}")

        return has_processed, stats

    except Exception as e:
        logger.error(f"Errore processing {regione_nome}: {e}")
        return False, {'error': str(e)}


def step_query_colture(logger: logging.Logger, regione_id: str = None, force: bool = False) -> tuple[bool, dict]:
    """
    Step 3: Query RAG per colture.

    Args:
        regione_id: Se specificato, genera report solo per questa regione.
                    Se None, genera per tutte.

    Returns:
        (has_processed, stats)
    """
    regione_label = REGIONI[regione_id]["nome"] if regione_id else "tutte le regioni"
    logger.info("=" * 70)
    logger.info(f"STEP 3: Query Colture - {regione_label}")
    logger.info("=" * 70)

    try:
        processor = ColtureQueryProcessor(regione=regione_id)

        if force:
            has_processed, stats = processor.process_all(force=True)
        else:
            has_processed, stats = processor.process_new_only()

        logger.info(f"Query Colture completate:")
        logger.info(f"  - Report generati: {stats.get('processed', 0)}")
        logger.info(f"  - Bollettini processati: {stats.get('bollettini', 0)}")
        logger.info(f"  - Colture totali: {stats.get('colture', 0)}")

        return has_processed, stats

    except Exception as e:
        logger.error(f"Errore query colture: {e}")
        return False, {'error': str(e)}


# ============= MAIN PIPELINE =============

def run_pipeline(
    force: bool = False,
    download_only: bool = False,
    query_only: bool = False,
    verbose: bool = False,
    regione: str = None,
) -> int:
    """
    Esegue la pipeline completa.

    Args:
        force: Ignora cache e riesegui tutto
        download_only: Solo download, no processing/query
        query_only: Solo query, skip download/processing
        verbose: Output dettagliato
        regione: ID regione ("emilia_romagna", "campania") o None per tutte

    Returns:
        Exit code (0=nuovi dati, 1=nessun nuovo, 2=errore)
    """
    logger = setup_logging(verbose)
    start_time = time.time()

    # Determina regioni da processare
    if regione:
        if regione not in REGIONI:
            logger.error(f"Regione sconosciuta: '{regione}'. Disponibili: {list(REGIONI.keys())}")
            return 2
        regioni_da_processare = [regione]
    else:
        regioni_da_processare = list(REGIONI.keys())

    regioni_label = ", ".join(REGIONI[r]["nome"] for r in regioni_da_processare)

    logger.info("+" + "=" * 68 + "+")
    logger.info("|" + " RAG COLTURE - PIPELINE ".center(68) + "|")
    logger.info("|" + f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(68) + "|")
    logger.info("|" + f" Regioni: {regioni_label} ".center(68) + "|")
    logger.info("+" + "=" * 68 + "+")

    results = {}
    any_new_data = False
    has_error = False

    try:
        # STEP 1 & 2: Download + Processing per ogni regione
        for regione_id in regioni_da_processare:
            results[regione_id] = {'download': None, 'process': None, 'colture': None}

            # STEP 1: Download
            if not query_only:
                has_new, download_stats = step_download(logger, regione_id, force)
                results[regione_id]['download'] = download_stats

                if download_stats.get('error'):
                    has_error = True
                elif has_new:
                    any_new_data = True
                    logger.info(f"Nuovi bollettini scaricati per {REGIONI[regione_id]['nome']}")
                else:
                    logger.info(f"Nessun nuovo bollettino per {REGIONI[regione_id]['nome']}")

            # STEP 2: Processing
            if not query_only and not download_only:
                has_processed, process_stats = step_process(logger, regione_id, force)
                results[regione_id]['process'] = process_stats

                if process_stats.get('error'):
                    has_error = True
                elif has_processed:
                    any_new_data = True
                    logger.info(f"Nuovi bollettini indicizzati per {REGIONI[regione_id]['nome']}")

        # STEP 3: Query Colture
        run_queries = any_new_data or force or query_only

        if not download_only and run_queries:
            for regione_id in regioni_da_processare:
                has_colture, colture_stats = step_query_colture(logger, regione_id, force)
                results[regione_id]['colture'] = colture_stats

                if colture_stats.get('error'):
                    has_error = True
                elif has_colture:
                    any_new_data = True
                    logger.info(f"Report Colture generati per {REGIONI[regione_id]['nome']}")
        elif not download_only:
            logger.info("Skip query: nessun nuovo dato da processare")

    except KeyboardInterrupt:
        logger.warning("\nPipeline interrotta dall'utente")
        return 2

    except Exception as e:
        logger.error(f"\nErrore fatale: {e}")
        return 2

    # Summary
    duration = time.time() - start_time

    logger.info("")
    logger.info("+" + "=" * 68 + "+")
    logger.info("|" + " RIEPILOGO ".center(68) + "|")
    logger.info("+" + "=" * 68 + "+")

    for regione_id in regioni_da_processare:
        r = results.get(regione_id, {})
        regione_nome = REGIONI[regione_id]["nome"]
        logger.info(f"\n  {regione_nome}:")

        if r.get('download'):
            d = r['download']
            logger.info(f"    Download:   {d.get('downloaded', 0)} nuovi / {d.get('total_found', 0)} totali")

        if r.get('process'):
            p = r['process']
            logger.info(f"    Processing: {p.get('processed', 0)} indicizzati")

        if r.get('colture'):
            c = r['colture']
            logger.info(
                f"    Colture:    {c.get('processed', 0)} report "
                f"({c.get('bollettini', 0)} bollettini x {c.get('colture', 0)} colture)"
            )

    logger.info(f"\nDurata totale: {duration:.1f}s")

    if has_error:
        logger.error("\nPipeline completata con errori")
        return 2
    elif any_new_data:
        logger.info("\nPipeline completata: nuovi dati processati")
        return 0
    else:
        logger.info("\nPipeline completata: tutto aggiornato, nessuna azione necessaria")
        return 1


# ============= CLI =============

def main():
    parser = argparse.ArgumentParser(
        description="RAG Colture - Pipeline Orchestrator (multi-regione)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python run_pipeline.py                              # Run standard (tutte le regioni)
  python run_pipeline.py --regione campania           # Solo Campania
  python run_pipeline.py --regione emilia_romagna     # Solo Emilia-Romagna
  python run_pipeline.py --force                      # Riesegui tutto
  python run_pipeline.py --download-only              # Solo download
  python run_pipeline.py --query-only                 # Solo query

Exit codes:
  0 = Nuovi dati processati
  1 = Nessun nuovo dato (tutto aggiornato)
  2 = Errore
        """
    )

    parser.add_argument(
        '--regione',
        choices=list(REGIONI.keys()),
        default=None,
        help='Regione da processare (default: tutte)'
    )

    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Ignora cache e riesegui tutto'
    )

    parser.add_argument(
        '--download-only',
        action='store_true',
        help='Solo download, no processing/query'
    )

    parser.add_argument(
        '--query-only',
        action='store_true',
        help='Solo query, skip download/processing'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Output dettagliato'
    )

    args = parser.parse_args()

    exit_code = run_pipeline(
        force=args.force,
        download_only=args.download_only,
        query_only=args.query_only,
        verbose=args.verbose,
        regione=args.regione,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
