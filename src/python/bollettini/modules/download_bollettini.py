"""
Script per scaricare automaticamente i bollettini fitosanitari dalla Regione Emilia-Romagna.
Usa Plone REST API per recuperare la lista dei PDF e scaricarli.

Uso:
    # Come script standalone
    python download_bollettini.py
    
    # Come modulo (per scheduler/orchestrator)
    from modules.download_bollettini import BollettiniDownloader
    downloader = BollettiniDownloader()
    has_new, stats = downloader.download_all()
"""

import requests
import time
from pathlib import Path
import logging
import json
from datetime import datetime
import re

# ============= CONFIGURAZIONE =============
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "1_collections" / "bollettini"
LOG_DIR = BASE_DIR / "logs"
CACHE_FILE = BASE_DIR / "data" / "bollettini_cache.json"

# Province disponibili (slug URL)
PROVINCE_URLS = {
    "Bologna-Ferrara": "bologna-e-ferrara",
    "Forli-Cesena-Ravenna-Rimini": "forli-cesena-ravenna-rimini",
    "Modena-Reggio-Emilia": "modena-reggio-emilia",
    "Parma-Piacenza": "parma-piacenza",
}

# URL dinamico basato sull'anno corrente (con fallback all'anno precedente)
BASE_URL = "https://agricoltura.regione.emilia-romagna.it"
CURRENT_YEAR = datetime.now().year

def get_bollettini_base_url(year: int) -> str:
    """Genera URL base per i bollettini di un anno specifico."""
    return (
        f"https://agricoltura.regione.emilia-romagna.it/fitosanitario/"
        f"difesa-sostenibile/bollettini/bollettini-interprovinciali-di-"
        f"produzione-integrata-e-biologica-{year}"
    )

# URL di default (anno corrente, con fallback gestito nella classe)
BOLLETTINI_BASE = get_bollettini_base_url(CURRENT_YEAR)

# Rate limiting
DELAY_BETWEEN_DOWNLOADS = 2  # secondi

# ==========================================


# ============= LOGGING ====================
# Logger configurato lazy (solo quando serve)
_logger = None

def get_logger():
    """Ritorna il logger, inizializzandolo solo al primo uso."""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger

def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"download_bollettini_{timestamp}.log"
    
    logger = logging.getLogger("bollettini_downloader")
    logger.setLevel(logging.INFO)
    
    # Evita handler duplicati
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    
    return logger
# ==========================================


class BollettiniDownloader:
    def __init__(self, year: int = None):
        """
        Inizializza il downloader.
        
        Args:
            year: Anno dei bollettini da scaricare. Se None, usa l'anno corrente
                  con fallback automatico all'anno precedente se non ci sono bollettini.
        """
        self.logger = get_logger()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        self.stats = {
            'total_found': 0,
            'downloaded': 0,
            'skipped': 0,
            'errors': 0
        }
        self.new_bollettini = []  # Lista dei nuovi bollettini scaricati
        self.year = year or CURRENT_YEAR
        self.bollettini_base = get_bollettini_base_url(self.year)
        self._year_validated = False  # Flag per evitare check multipli
        self.cache = self._load_cache()

    def _load_cache(self):
        """Carica la cache dei bollettini già scaricati"""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                self.logger.info(f"Cache caricata: {sum(len(v.get('downloaded_ids', [])) for v in cache.get('provinces', {}).values())} bollettini in cache")
                return cache
            except Exception as e:
                self.logger.warning(f"Errore caricamento cache: {e}")
        return {'provinces': {}, 'version': 1}

    def _save_cache(self):
        """Salva la cache su disco"""
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.cache['last_updated'] = datetime.now().isoformat()
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f, indent=2)
        self.logger.info("Cache salvata")

    def _get_province_cache(self, provincia_slug):
        """Ottiene la cache per una provincia specifica"""
        if 'provinces' not in self.cache:
            self.cache['provinces'] = {}
        if provincia_slug not in self.cache['provinces']:
            self.cache['provinces'][provincia_slug] = {
                'downloaded_ids': [],
                'latest_id': None,
                'last_check': None
            }
        return self.cache['provinces'][provincia_slug]

    def _is_in_cache(self, item_id, provincia_slug):
        """Verifica se un bollettino è già in cache"""
        cache = self._get_province_cache(provincia_slug)
        return item_id in cache['downloaded_ids']

    def _add_to_cache(self, item_id, provincia_slug):
        """Aggiunge un bollettino alla cache"""
        cache = self._get_province_cache(provincia_slug)
        if item_id not in cache['downloaded_ids']:
            cache['downloaded_ids'].append(item_id)
    
    def _try_fallback_year(self):
        """
        Se l'anno corrente non ha bollettini, prova con l'anno precedente.
        Viene chiamato solo una volta.
        """
        if self._year_validated:
            return
            
        # Prova a fare una richiesta di test
        test_url = f"{self.bollettini_base}/bologna-e-ferrara/@search"
        try:
            response = requests.get(test_url, headers=self.headers, timeout=10)
            if response.status_code == 404 and self.year == CURRENT_YEAR:
                # Fallback all'anno precedente
                self.year = CURRENT_YEAR - 1
                self.bollettini_base = get_bollettini_base_url(self.year)
                self.logger.info(f"⚠️ Anno {CURRENT_YEAR} non disponibile, uso {self.year}")
        except Exception:
            pass
        
        self._year_validated = True

    def get_bollettini_list(self, provincia_slug):
        """
        Recupera la lista completa di bollettini per una provincia usando Plone REST API
        """
        # Verifica anno disponibile (solo alla prima chiamata)
        self._try_fallback_year()
        
        api_url = f"{self.bollettini_base}/{provincia_slug}/@search"
        all_items = []
        current_url = api_url
        page = 1
        
        self.logger.info(f"Recupero lista bollettini da API: {provincia_slug}")
        
        while current_url and page <= 10:  # Limite di sicurezza
            try:
                response = requests.get(current_url, headers=self.headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                items = data.get('items', [])
                all_items.extend(items)
                
                self.logger.info(f"  Pagina {page}: {len(items)} items")
                
                # Controlla paginazione
                next_url = data.get('batching', {}).get('next')
                if next_url:
                    current_url = next_url
                    page += 1
                else:
                    break
                    
            except Exception as e:
                self.logger.error(f"Errore recupero API pagina {page}: {e}")
                break
        
        # Filtra solo i PDF di bollettini (non allegati)
        bollettini = []
        for item in all_items:
            if item.get('@type') == 'File' and item.get('mime_type') == 'application/pdf':
                title = item.get('title', '').lower()
                # Filtra: prendi bollettini, escludi allegati orticole
                if 'bollettino' in title and 'allegato' not in title and 'orticole' not in title:
                    bollettini.append(item)
        
        self.logger.info(f"  Trovati {len(bollettini)} bollettini (esclusi allegati)")
        self.stats['total_found'] += len(bollettini)
        
        return bollettini
    
    def extract_metadata(self, item, provincia_name):
        """
        Estrae metadata dal nome del bollettino
        """
        title = item.get('title', '')
        
        # Estrai numero bollettino
        numero_match = re.search(r'bollettino\s+n?\.?\s*(\d+)', title, re.IGNORECASE)
        numero = int(numero_match.group(1)) if numero_match else None
        
        # Estrai data dal titolo (es. "1° ottobre 2025", "11 giugno 2025")
        date_match = re.search(r'(\d+)[°\s]+(\w+)\s+(\d{4})', title)
        data_str = None
        if date_match:
            giorno = date_match.group(1)
            mese = date_match.group(2)
            anno = date_match.group(3)
            data_str = f"{giorno} {mese} {anno}"
        
        return {
            'numero_bollettino': numero,
            'data_bollettino': data_str,
            'provincia': provincia_name,
            'title': item.get('title'),
            'date_published': item.get('Date'),
            'size': item.get('getObjSize'),
            'original_url': item.get('@id')
        }
    
    def generate_filename(self, metadata):
        """
        Genera nome file standardizzato
        Es: Bollettino 30 del 1° ottobre 2025 di Bologna e Ferrara.pdf
        """
        title = metadata['title']
        
        # Sanitizza il nome file
        filename = title
        # Rimuovi caratteri non validi
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Aggiungi .pdf se manca
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        return filename
    
    def download_pdf(self, item, provincia_name, provincia_slug, output_dir):
        """
        Scarica un singolo PDF usando l'endpoint @@download/file di Plone
        
        Returns:
            tuple: (success: bool, filepath: Path | None)
        """
        item_id = item['@id']
        metadata = self.extract_metadata(item, provincia_name)
        filename = self.generate_filename(metadata)
        filepath = output_dir / filename

        # Skip se in cache (controllo veloce senza accesso al filesystem)
        if self._is_in_cache(item_id, provincia_slug):
            self.logger.info(f"  ✓ In cache: {filename}")
            self.stats['skipped'] += 1
            return True, filepath

        # Skip se già scaricato (fallback filesystem)
        if filepath.exists():
            self.logger.info(f"  ✓ Già presente: {filename}")
            self._add_to_cache(item_id, provincia_slug)
            self.stats['skipped'] += 1
            return True, filepath
        
        # URL per download diretto
        pdf_url = item['@id']
        if not pdf_url.endswith('/@@download/file'):
            pdf_url = f"{pdf_url}/@@download/file"
        
        self.logger.info(f"  ⬇ Scaricamento: {filename}")
        
        try:
            response = requests.get(
                pdf_url,
                headers=self.headers,
                timeout=60,
                stream=True,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Verifica Content-Type
            content_type = response.headers.get('Content-Type', '')
            if 'application/pdf' not in content_type:
                self.logger.warning(f"  ⚠ Content-Type inatteso: {content_type}")
            
            # Scarica il file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verifica che sia un PDF valido
            with open(filepath, 'rb') as f:
                header = f.read(10)
                if not header.startswith(b'%PDF'):
                    self.logger.error(f"  ✗ File non valido (non è un PDF)")
                    filepath.unlink()  # Rimuovi file corrotto
                    self.stats['errors'] += 1
                    return False, None
            
            file_size = filepath.stat().st_size / 1024  # KB
            self.logger.info(f"  ✓ Salvato: {filepath.name} ({file_size:.1f} KB)")
            self._add_to_cache(item_id, provincia_slug)
            self.stats['downloaded'] += 1
            
            # Traccia nuovo bollettino per lo scheduler
            self.new_bollettini.append({
                'filename': filename,
                'filepath': str(filepath),
                'provincia': provincia_name,
                'metadata': metadata
            })

            return True, filepath
            
        except Exception as e:
            self.logger.error(f"  ✗ Errore download {filename}: {e}")
            if filepath.exists():
                filepath.unlink()
            self.stats['errors'] += 1
            return False, None
    
    def download_provincia(self, provincia_name, provincia_slug):
        """
        Scarica tutti i bollettini per una provincia
        """
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"PROVINCIA: {provincia_name}")
        self.logger.info(f"{'='*70}\n")

        # Crea directory output
        output_dir = OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        # Recupera lista bollettini
        bollettini = self.get_bollettini_list(provincia_slug)

        if not bollettini:
            self.logger.warning(f"Nessun bollettino trovato per {provincia_name}")
            return

        # Ordina per data (più recenti prima)
        bollettini.sort(key=lambda x: x.get('Date', ''), reverse=True)

        # Quick check: se il bollettino più recente è già in cache, verifica se sono tutti in cache
        province_cache = self._get_province_cache(provincia_slug)
        cached_ids = set(province_cache['downloaded_ids'])
        api_ids = {item['@id'] for item in bollettini}

        if api_ids and api_ids.issubset(cached_ids):
            self.logger.info(f"  ⚡ Tutti i {len(bollettini)} bollettini sono già in cache - skip provincia")
            self.stats['skipped'] += len(bollettini)
            return

        # Conta quanti sono già in cache per logging
        already_cached = len(api_ids & cached_ids)
        if already_cached > 0:
            self.logger.info(f"  📋 {already_cached}/{len(bollettini)} già in cache")

        # Early exit optimization: conta quanti bollettini consecutivi già esistenti
        consecutive_existing = 0
        max_consecutive_before_exit = 5  # Se trovo 5 bollettini consecutivi già scaricati, esco

        # Scarica ogni bollettino
        for i, item in enumerate(bollettini, 1):
            self.logger.info(f"\n[{i}/{len(bollettini)}] {item['title']}")

            # Traccia skipped prima della chiamata
            skipped_before = self.stats['skipped']

            success, filepath = self.download_pdf(item, provincia_name, provincia_slug, output_dir)
            was_skipped = self.stats['skipped'] > skipped_before

            # Verifica se questo file era già presente (skipped è aumentato)
            if was_skipped:
                consecutive_existing += 1
            else:
                # Reset counter se scaricato un nuovo file o errore
                consecutive_existing = 0

            # Early exit: se trovo troppi file consecutivi già scaricati, probabilmente ho tutto
            if consecutive_existing >= max_consecutive_before_exit:
                remaining = len(bollettini) - i
                self.logger.info(f"\n  ⚡ Early exit: {consecutive_existing} bollettini consecutivi già presenti")
                self.logger.info(f"  ⏭  Saltati {remaining} bollettini rimanenti (probabilmente già scaricati)")
                # Aggiungi tutti i rimanenti alla cache
                for remaining_item in bollettini[i:]:
                    self._add_to_cache(remaining_item['@id'], provincia_slug)
                self.stats['skipped'] += remaining
                break

            # Rate limiting - solo se abbiamo scaricato qualcosa (non per skip da cache)
            if not was_skipped and i < len(bollettini):
                time.sleep(DELAY_BETWEEN_DOWNLOADS)

        # Aggiorna last_check per la provincia
        province_cache['last_check'] = datetime.now().isoformat()
    
    def download_all(self) -> tuple[bool, dict]:
        """
        Scarica bollettini da tutte le province.
        
        Returns:
            tuple: (has_new_bollettini: bool, stats: dict)
                - has_new_bollettini: True se sono stati scaricati nuovi bollettini
                - stats: dizionario con statistiche del download
        """
        self.logger.info("=" * 70)
        self.logger.info(f"INIZIO DOWNLOAD BOLLETTINI EMILIA-ROMAGNA {self.year}")
        self.logger.info("=" * 70)

        start_time = datetime.now()

        for provincia_name, provincia_slug in PROVINCE_URLS.items():
            try:
                self.download_provincia(provincia_name, provincia_slug)
            except Exception as e:
                self.logger.error(f"Errore provincia {provincia_name}: {e}")
                self.stats['errors'] += 1

        # Salva cache alla fine
        self._save_cache()

        # Report finale
        duration = (datetime.now() - start_time).total_seconds()

        self.logger.info("\n" + "=" * 70)
        self.logger.info("DOWNLOAD COMPLETATO")
        self.logger.info("=" * 70)
        self.logger.info(f"Durata: {duration:.1f} secondi")
        self.logger.info(f"Bollettini trovati: {self.stats['total_found']}")
        self.logger.info(f"Scaricati: {self.stats['downloaded']}")
        self.logger.info(f"Già presenti (skipped): {self.stats['skipped']}")
        self.logger.info(f"Errori: {self.stats['errors']}")
        self.logger.info("=" * 70)
        
        # Ritorna risultati per lo scheduler
        has_new = self.stats['downloaded'] > 0
        return has_new, {
            **self.stats,
            'duration_seconds': duration,
            'new_bollettini': self.new_bollettini
        }
    
    def check_for_new_bollettini(self) -> list[dict]:
        """
        Controlla se ci sono nuovi bollettini senza scaricarli.
        Utile per lo scheduler per decidere se eseguire la pipeline.
        
        Returns:
            list: Lista di bollettini nuovi trovati (non ancora scaricati)
        """
        new_items = []
        
        for provincia_name, provincia_slug in PROVINCE_URLS.items():
            try:
                bollettini = self.get_bollettini_list(provincia_slug)
                
                for item in bollettini:
                    if not self._is_in_cache(item['@id'], provincia_slug):
                        new_items.append({
                            'title': item.get('title'),
                            'provincia': provincia_name,
                            'url': item.get('@id'),
                            'date': item.get('Date')
                        })
                        
            except Exception as e:
                self.logger.error(f"Errore check provincia {provincia_name}: {e}")
        
        return new_items


def main():
    """
    Scarica tutti i bollettini.
    Exit code: 0 se ci sono nuovi bollettini, 1 altrimenti.
    """
    downloader = BollettiniDownloader()
    has_new, stats = downloader.download_all()
    
    # Exit code per uso in script/cron
    exit(0 if has_new else 1)


if __name__ == "__main__":
    main()

