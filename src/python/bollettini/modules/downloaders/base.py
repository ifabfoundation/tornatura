"""
Classe astratta BaseDownloader per i downloader regionali.

Definisce l'interfaccia comune e gestisce cache/stats in modo standardizzato.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import json
import logging


class BaseDownloader(ABC):
    """Classe base astratta per i downloader regionali."""

    def __init__(self, regione_id: str, output_dir: Path, cache_file: Path,
                 year: int = None, logger: logging.Logger = None):
        self.regione_id = regione_id
        self.output_dir = output_dir
        self.cache_file = cache_file
        self.year = year or datetime.now().year
        self.logger = logger or logging.getLogger(f"downloader_{regione_id}")
        self.stats = {
            'total_found': 0,
            'downloaded': 0,
            'skipped': 0,
            'errors': 0,
        }
        self.new_bollettini: List[dict] = []
        self.cache = self._load_cache()

    # ============= CACHE =============

    def _load_cache(self) -> dict:
        """Carica la cache dei bollettini gia' scaricati."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                total = sum(
                    len(v.get('downloaded_ids', []))
                    for v in cache.get('aree', {}).values()
                )
                self.logger.info(f"Cache caricata: {total} bollettini in cache")
                return cache
            except Exception as e:
                self.logger.warning(f"Errore caricamento cache: {e}")
        return {'aree': {}, 'version': 1}

    def _save_cache(self):
        """Salva la cache su disco."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache['last_updated'] = datetime.now().isoformat()
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
        self.logger.info("Cache salvata")

    def _get_area_cache(self, area_slug: str) -> dict:
        """Ottiene la cache per un'area specifica."""
        if 'aree' not in self.cache:
            self.cache['aree'] = {}
        if area_slug not in self.cache['aree']:
            self.cache['aree'][area_slug] = {
                'downloaded_ids': [],
                'latest_id': None,
                'last_check': None,
            }
        return self.cache['aree'][area_slug]

    def _is_in_cache(self, item_id: str, area_slug: str) -> bool:
        """Verifica se un bollettino e' gia' in cache."""
        cache = self._get_area_cache(area_slug)
        return item_id in cache['downloaded_ids']

    def _add_to_cache(self, item_id: str, area_slug: str):
        """Aggiunge un bollettino alla cache."""
        cache = self._get_area_cache(area_slug)
        if item_id not in cache['downloaded_ids']:
            cache['downloaded_ids'].append(item_id)

    # ============= INTERFACCIA ASTRATTA =============

    @abstractmethod
    def get_bollettini_list(self, area_slug: str) -> List[dict]:
        """Recupera la lista dei bollettini per un'area."""
        ...

    @abstractmethod
    def download_all(self) -> Tuple[bool, dict]:
        """
        Scarica bollettini da tutte le aree.

        Returns:
            (has_new_bollettini, stats_dict)
        """
        ...

    def _finalize_stats(self, start_time: datetime) -> Tuple[bool, dict]:
        """Calcola stats finali e salva cache."""
        self._save_cache()

        duration = (datetime.now() - start_time).total_seconds()

        self.logger.info(f"Durata: {duration:.1f} secondi")
        self.logger.info(f"Bollettini trovati: {self.stats['total_found']}")
        self.logger.info(f"Scaricati: {self.stats['downloaded']}")
        self.logger.info(f"Gia' presenti (skipped): {self.stats['skipped']}")
        self.logger.info(f"Errori: {self.stats['errors']}")

        has_new = self.stats['downloaded'] > 0
        return has_new, {
            **self.stats,
            'duration_seconds': duration,
            'new_bollettini': self.new_bollettini,
        }
