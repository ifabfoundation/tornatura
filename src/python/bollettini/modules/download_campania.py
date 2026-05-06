"""
Scraper per bollettini fitosanitari della Regione Campania.

Scarica i PDF dalle pagine HTML statiche del sito regionale.
Pagina indice: https://agricoltura.regione.campania.it/difesa/bollettini/bollettini_{anno}.html
Pagina area:   bollettini_{anno}/{slug}_{anno}.html
Pattern PDF:   bollettini_{anno}/pdf/{slug}-{DD}-{MM}.pdf

Uso:
    # Come script standalone
    python download_campania.py

    # Come modulo
    from modules.download_campania import CampaniaDownloader
    downloader = CampaniaDownloader()
    has_new, stats = downloader.download_all()
"""

import requests
import time
import re
import logging
from pathlib import Path
from datetime import datetime

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from bollettini.modules.downloaders.base import BaseDownloader
from bollettini.modules.config import REGIONI
from bollettini import paths

# ============= CONFIGURAZIONE =============
BASE_DIR = Path(__file__).parent.parent
CAMPANIA_CONFIG = REGIONI["campania"]
OUTPUT_DIR = paths.DATA_DIR / "input_bollettini" / "campania" / "bollettini"
LOG_DIR = BASE_DIR / "logs"
CACHE_FILE = paths.DATA_DIR / "input_bollettini" / "campania" / "cache_download.json"

DELAY_BETWEEN_DOWNLOADS = 2  # secondi
REQUEST_TIMEOUT = 15  # secondi
# ==========================================


# ============= LOGGING ====================
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
    log_file = LOG_DIR / f"download_campania_{timestamp}.log"

    logger = logging.getLogger("campania_downloader")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger
# ==========================================


class CampaniaDownloader(BaseDownloader):
    """Downloader per bollettini fitosanitari della Regione Campania."""

    def __init__(self, year: int = None):
        logger = get_logger()
        super().__init__(
            regione_id="campania",
            output_dir=OUTPUT_DIR,
            cache_file=CACHE_FILE,
            year=year,
            logger=logger,
        )

        if BeautifulSoup is None:
            raise ImportError(
                "beautifulsoup4 richiesto per CampaniaDownloader. "
                "Installa con: pip install beautifulsoup4"
            )

        self.base_url = CAMPANIA_CONFIG["base_url"]
        self.aree = CAMPANIA_CONFIG["aree"]
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

    def _get_area_page_url(self, slug: str) -> str:
        """URL della pagina HTML di un'area per l'anno corrente."""
        return f"{self.base_url}/bollettini_{self.year}/{slug}_{self.year}.html"

    def _get_pdf_url(self, slug: str, dd: str, mm: str) -> str:
        """URL di un PDF bollettino."""
        return f"{self.base_url}/bollettini_{self.year}/pdf/{slug}-{dd}-{mm}.pdf"

    def get_bollettini_list(self, area_slug: str) -> list[dict]:
        """
        Recupera la lista di bollettini per un'area parsando la pagina HTML.

        Returns:
            Lista di dict con chiavi: url, filename, date_str, area_slug
        """
        page_url = self._get_area_page_url(area_slug)
        self.logger.info(f"  Recupero lista da: {page_url}")

        try:
            response = requests.get(
                page_url, headers=self.headers, timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 404:
                self.logger.warning(f"  Pagina non trovata (404): {page_url}")
                return []
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.warning(f"  Errore accesso pagina {area_slug}: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # Cerca link a PDF con pattern: pdf/{slug}-{DD}-{MM}.pdf
        pdf_pattern = re.compile(
            rf'pdf/{re.escape(area_slug)}-(\d{{2}})-(\d{{2}})\.pdf'
        )

        bollettini = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            match = pdf_pattern.search(href)
            if match:
                dd, mm = match.group(1), match.group(2)
                pdf_url = self._get_pdf_url(area_slug, dd, mm)
                date_str = f"{dd}-{mm}-{self.year}"

                bollettini.append({
                    'url': pdf_url,
                    'filename': f"Campania_{area_slug}_{date_str}.pdf",
                    'date_str': date_str,
                    'area_slug': area_slug,
                    'dd': dd,
                    'mm': mm,
                })

        self.logger.info(f"  Trovati {len(bollettini)} bollettini PDF")
        self.stats['total_found'] += len(bollettini)
        return bollettini

    def _download_pdf(self, bollettino: dict, area_name: str) -> tuple[bool, Path | None]:
        """Scarica un singolo PDF."""
        url = bollettino['url']
        filename = bollettino['filename']
        area_slug = bollettino['area_slug']

        year_dir = self.output_dir / str(self.year)
        year_dir.mkdir(parents=True, exist_ok=True)
        filepath = year_dir / filename

        # Skip se in cache
        if self._is_in_cache(url, area_slug):
            self.logger.info(f"    In cache: {filename}")
            self.stats['skipped'] += 1
            return True, filepath

        # Skip se gia' scaricato (fallback filesystem)
        if filepath.exists():
            self.logger.info(f"    Gia' presente: {filename}")
            self._add_to_cache(url, area_slug)
            self.stats['skipped'] += 1
            return True, filepath

        self.logger.info(f"    Scaricamento: {filename}")

        try:
            response = requests.get(
                url, headers=self.headers, timeout=60,
                stream=True, allow_redirects=True
            )
            response.raise_for_status()

            # Scarica il file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verifica che sia un PDF valido
            with open(filepath, 'rb') as f:
                header = f.read(10)
                if not header.startswith(b'%PDF'):
                    self.logger.error(f"    File non valido (non e' un PDF)")
                    filepath.unlink()
                    self.stats['errors'] += 1
                    return False, None

            file_size = filepath.stat().st_size / 1024
            self.logger.info(f"    Salvato: {filename} ({file_size:.1f} KB)")
            self._add_to_cache(url, area_slug)
            self.stats['downloaded'] += 1

            self.new_bollettini.append({
                'filename': filename,
                'filepath': str(filepath),
                'area': area_name,
                'regione': 'campania',
                'date_str': bollettino['date_str'],
            })

            return True, filepath

        except Exception as e:
            self.logger.error(f"    Errore download {filename}: {e}")
            if filepath.exists():
                filepath.unlink()
            self.stats['errors'] += 1
            return False, None

    def download_area(self, area_name: str, area_slug: str):
        """Scarica tutti i bollettini per un'area."""
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"AREA: {area_name} ({area_slug})")
        self.logger.info(f"{'='*70}")

        bollettini = self.get_bollettini_list(area_slug)

        if not bollettini:
            self.logger.warning(f"  Nessun bollettino trovato per {area_name}")
            return

        # Ordina per data (piu' recenti prima)
        bollettini.sort(key=lambda x: (x['mm'], x['dd']), reverse=True)

        # Quick check: se tutti gia' in cache, skip
        area_cache = self._get_area_cache(area_slug)
        cached_urls = set(area_cache['downloaded_ids'])
        all_urls = {b['url'] for b in bollettini}

        if all_urls and all_urls.issubset(cached_urls):
            self.logger.info(
                f"  Tutti i {len(bollettini)} bollettini gia' in cache - skip area"
            )
            self.stats['skipped'] += len(bollettini)
            return

        for i, boll in enumerate(bollettini, 1):
            self.logger.info(f"  [{i}/{len(bollettini)}] {boll['filename']}")

            skipped_before = self.stats['skipped']
            self._download_pdf(boll, area_name)
            was_skipped = self.stats['skipped'] > skipped_before

            # Rate limiting solo se abbiamo scaricato qualcosa
            if not was_skipped and i < len(bollettini):
                time.sleep(DELAY_BETWEEN_DOWNLOADS)

        # Aggiorna last_check
        area_cache['last_check'] = datetime.now().isoformat()

    def download_all(self) -> tuple[bool, dict]:
        """Scarica bollettini da tutte le aree della Campania."""
        self.logger.info("=" * 70)
        self.logger.info(f"INIZIO DOWNLOAD BOLLETTINI CAMPANIA {self.year}")
        self.logger.info("=" * 70)

        start_time = datetime.now()

        for area_name, area_slug in self.aree.items():
            try:
                self.download_area(area_name, area_slug)
            except Exception as e:
                self.logger.error(f"Errore area {area_name}: {e}")
                self.stats['errors'] += 1

        self.logger.info("\n" + "=" * 70)
        self.logger.info("DOWNLOAD COMPLETATO")
        self.logger.info("=" * 70)

        return self._finalize_stats(start_time)


def main():
    """Scarica tutti i bollettini Campania. Exit code: 0 se nuovi, 1 altrimenti."""
    downloader = CampaniaDownloader()
    has_new, stats = downloader.download_all()
    exit(0 if has_new else 1)


if __name__ == "__main__":
    main()
