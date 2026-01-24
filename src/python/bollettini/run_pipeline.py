#!/usr/bin/env python3
"""
RAG Bollettini - Pipeline Orchestrator

Coordina l'intera pipeline:
1. Download nuovi bollettini (modules/download_bollettini.py)
2. Indicizzazione in ChromaDB (modules/process_bollettini.py)
3. Query RAG per Cimice e Flavescenza (solo se ci sono nuovi dati)

Utilizzo:
    # Run completo (solo nuovi bollettini)
    python run_pipeline.py
    
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

from modules.download_bollettini import BollettiniDownloader
from modules.process_bollettini import BollettiniProcessor
from modules.cimice import CimiceQueryProcessor
from modules.flavescenza import FlavescenzaQueryProcessor


# ============= LOGGING =============
def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configura logging per l'orchestratore."""
    logger = logging.getLogger("pipeline")
    
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

def step_download(logger: logging.Logger, force: bool = False) -> tuple[bool, dict]:
    """
    Step 1: Download nuovi bollettini PDF.
    
    Returns:
        (has_new, stats)
    """
    logger.info("=" * 70)
    logger.info("STEP 1: Download Bollettini")
    logger.info("=" * 70)
    
    try:
        downloader = BollettiniDownloader()
        has_new, stats = downloader.download_all()
        
        logger.info(f"Download completato:")
        logger.info(f"  - Trovati: {stats.get('total_found', 0)}")
        logger.info(f"  - Scaricati: {stats.get('downloaded', 0)}")
        logger.info(f"  - Skipped (cache): {stats.get('skipped', 0)}")
        logger.info(f"  - Errori: {stats.get('errors', 0)}")
        
        return has_new, stats
        
    except Exception as e:
        logger.error(f"Errore download: {e}")
        return False, {'error': str(e)}


def step_process(logger: logging.Logger, force: bool = False, 
                 new_files: list = None) -> tuple[bool, dict]:
    """
    Step 2: Indicizzazione PDF in ChromaDB.
    
    Args:
        force: Se True, riprocessa tutto
        new_files: Lista di file specifici da processare (se None, processa tutti i nuovi)
    
    Returns:
        (has_processed, stats)
    """
    logger.info("=" * 70)
    logger.info("STEP 2: Indicizzazione ChromaDB")
    logger.info("=" * 70)
    
    try:
        processor = BollettiniProcessor()
        
        if force:
            # Riprocessa tutto
            has_processed, stats = processor.process_all(only_latest=False)
        else:
            # Processa solo nuovi
            has_processed, stats = processor.process_all(only_latest=True)
        
        logger.info(f"Indicizzazione completata:")
        logger.info(f"  - Processati: {stats.get('processed', 0)}")
        logger.info(f"  - Totale: {stats.get('total', 0)}")
        logger.info(f"  - Cached: {stats.get('cached', 0)}")
        
        return has_processed, stats
        
    except Exception as e:
        logger.error(f"Errore processing: {e}")
        return False, {'error': str(e)}


def step_query_cimice(logger: logging.Logger, force: bool = False) -> tuple[bool, dict]:
    """
    Step 3a: Query RAG per Cimice Asiatica.
    
    Returns:
        (has_processed, stats)
    """
    logger.info("=" * 70)
    logger.info("STEP 3a: Query Cimice Asiatica")
    logger.info("=" * 70)
    
    try:
        processor = CimiceQueryProcessor()
        
        if force:
            has_processed, stats = processor.process_all(force=True)
        else:
            has_processed, stats = processor.process_new_only()
        
        logger.info(f"Query Cimice completate:")
        logger.info(f"  - Processati: {stats.get('processed', 0)}")
        logger.info(f"  - Totale: {stats.get('total', 0)}")
        
        return has_processed, stats
        
    except Exception as e:
        logger.error(f"Errore query cimice: {e}")
        return False, {'error': str(e)}


def step_query_flavescenza(logger: logging.Logger, force: bool = False) -> tuple[bool, dict]:
    """
    Step 3b: Query RAG per Flavescenza Dorata.
    
    Returns:
        (has_processed, stats)
    """
    logger.info("=" * 70)
    logger.info("STEP 3b: Query Flavescenza Dorata")
    logger.info("=" * 70)
    
    try:
        processor = FlavescenzaQueryProcessor()
        
        if force:
            has_processed, stats = processor.process_all(force=True)
        else:
            has_processed, stats = processor.process_new_only()
        
        logger.info(f"Query Flavescenza completate:")
        logger.info(f"  - Processati: {stats.get('processed', 0)}")
        logger.info(f"  - Totale: {stats.get('total', 0)}")
        
        return has_processed, stats
        
    except Exception as e:
        logger.error(f"Errore query flavescenza: {e}")
        return False, {'error': str(e)}


# ============= MAIN PIPELINE =============

def run_pipeline(
    force: bool = False,
    download_only: bool = False,
    query_only: bool = False,
    skip_cimice: bool = False,
    skip_flavescenza: bool = False,
    verbose: bool = False
) -> int:
    """
    Esegue la pipeline completa.
    
    Args:
        force: Ignora cache e riesegui tutto
        download_only: Solo download, no processing/query
        query_only: Solo query, skip download/processing
        skip_cimice: Salta query cimice
        skip_flavescenza: Salta query flavescenza
        verbose: Output dettagliato
    
    Returns:
        Exit code (0=nuovi dati, 1=nessun nuovo, 2=errore)
    """
    logger = setup_logging(verbose)
    start_time = time.time()
    
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " RAG BOLLETTINI - PIPELINE ".center(68) + "║")
    logger.info("║" + f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(68) + "║")
    logger.info("╚" + "═" * 68 + "╝")
    
    results = {
        'download': None,
        'process': None,
        'cimice': None,
        'flavescenza': None
    }
    
    any_new_data = False
    has_error = False
    
    try:
        # STEP 1: Download
        if not query_only:
            has_new_downloads, download_stats = step_download(logger, force)
            results['download'] = download_stats
            
            if download_stats.get('error'):
                has_error = True
            elif has_new_downloads:
                any_new_data = True
                logger.info("✓ Nuovi bollettini scaricati")
            else:
                logger.info("→ Nessun nuovo bollettino da scaricare")
        
        # STEP 2: Processing
        if not query_only and not download_only:
            has_processed, process_stats = step_process(logger, force)
            results['process'] = process_stats
            
            if process_stats.get('error'):
                has_error = True
            elif has_processed:
                any_new_data = True
                logger.info("✓ Nuovi bollettini indicizzati")
            else:
                logger.info("→ Nessun nuovo bollettino da indicizzare")
        
        # STEP 3: Query (solo se ci sono nuovi dati O force O query_only)
        run_queries = any_new_data or force or query_only
        
        if not download_only and run_queries:
            # 3a: Cimice
            if not skip_cimice:
                has_cimice, cimice_stats = step_query_cimice(logger, force)
                results['cimice'] = cimice_stats
                
                if cimice_stats.get('error'):
                    has_error = True
                elif has_cimice:
                    any_new_data = True
                    logger.info("✓ Report Cimice generati")
                else:
                    logger.info("→ Nessun nuovo report Cimice")
            
            # 3b: Flavescenza
            if not skip_flavescenza:
                has_flav, flav_stats = step_query_flavescenza(logger, force)
                results['flavescenza'] = flav_stats
                
                if flav_stats.get('error'):
                    has_error = True
                elif has_flav:
                    any_new_data = True
                    logger.info("✓ Report Flavescenza generati")
                else:
                    logger.info("→ Nessun nuovo report Flavescenza")
        elif not download_only:
            logger.info("→ Skip query: nessun nuovo dato da processare")
    
    except KeyboardInterrupt:
        logger.warning("\n⚠ Pipeline interrotta dall'utente")
        return 2
    
    except Exception as e:
        logger.error(f"\n❌ Errore fatale: {e}")
        return 2
    
    # Summary
    duration = time.time() - start_time
    
    logger.info("")
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " RIEPILOGO ".center(68) + "║")
    logger.info("╚" + "═" * 68 + "╝")
    
    if results['download']:
        d = results['download']
        logger.info(f"Download:    {d.get('downloaded', 0)} nuovi / {d.get('total_found', 0)} totali")
    
    if results['process']:
        p = results['process']
        logger.info(f"Processing:  {p.get('processed', 0)} indicizzati")
    
    if results['cimice']:
        c = results['cimice']
        logger.info(f"Cimice:      {c.get('processed', 0)} report generati")
    
    if results['flavescenza']:
        f = results['flavescenza']
        logger.info(f"Flavescenza: {f.get('processed', 0)} report generati")
    
    logger.info(f"\nDurata totale: {duration:.1f}s")
    
    if has_error:
        logger.error("\n❌ Pipeline completata con errori")
        return 2
    elif any_new_data:
        logger.info("\n✅ Pipeline completata: nuovi dati processati")
        return 0
    else:
        logger.info("\n✓ Pipeline completata: tutto aggiornato, nessuna azione necessaria")
        return 1


# ============= CLI =============

def main():
    parser = argparse.ArgumentParser(
        description="RAG Bollettini - Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python run_pipeline.py                    # Run standard (solo nuovi)
  python run_pipeline.py --force            # Riesegui tutto
  python run_pipeline.py --download-only    # Solo download
  python run_pipeline.py --query-only       # Solo query (skip download/processing)
  python run_pipeline.py --skip-cimice      # Salta query cimice

Exit codes:
  0 = Nuovi dati processati
  1 = Nessun nuovo dato (tutto aggiornato)
  2 = Errore
        """
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
        '--skip-cimice',
        action='store_true',
        help='Salta query Cimice Asiatica'
    )
    
    parser.add_argument(
        '--skip-flavescenza',
        action='store_true',
        help='Salta query Flavescenza Dorata'
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
        skip_cimice=args.skip_cimice,
        skip_flavescenza=args.skip_flavescenza,
        verbose=args.verbose
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
