"""
Modulo per query RAG su tutte le colture dei bollettini fitosanitari.

Estrae informazioni specifiche per ogni coltura usando:
- Filtraggio sezione-based (match esatto su section_title)
- Fallback keyword-based (solo se pochi risultati)
- Filtro anti-contaminazione (escludi sezioni altre colture)
- Generazione risposte con GPT-4o-mini

Supporta multi-regione (Emilia-Romagna, Campania).

Output: Report per ogni coltura in data/output_bollettini/{regione}/{coltura}/

Utilizzo:
    # Da scheduler (processa solo nuovi bollettini)
    processor = ColtureQueryProcessor()
    has_new, stats = processor.process_new_only()

    # Con filtro regione
    processor = ColtureQueryProcessor(regione="campania")
    has_new, stats = processor.process_new_only()

    # Da linea di comando
    python colture.py
"""

from pathlib import Path
from datetime import datetime
import json
import time
import shutil
import re
import chromadb
import markdown
from openai import OpenAI
from dotenv import load_dotenv
import logging
from typing import List, Dict, Optional, Tuple
from bollettini import paths

# ============= CONFIGURAZIONE =============
BASE_DIR = Path(__file__).parent.parent
CHROMADB_DIR = paths.DATA_DIR / "chromadb"
OUTPUT_DIR = paths.OUTPUT_DIR
CACHE_FILE = paths.DATA_DIR / "cache" / "colture_processed.json"
HISTORY_BASE_DIR = OUTPUT_DIR  # history lives under each regione/coltura dir

# Usa la stessa collezione di cimice_asiatica (contiene tutti i bollettini)
COLLECTION_NAME = "cimice_asiatica"

# Modello LLM
LLM_MODEL = "gpt-4o-mini"
# ==========================================


# ============= LOGGING (Lazy) =============
_logger = None

def get_logger():
    """Lazy logger initialization."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger(__name__)
        if not _logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            _logger.addHandler(handler)
            _logger.setLevel(logging.INFO)
    return _logger
# ==========================================


# ============= COLTURE DA CONFIG =============
from modules.config import COLTURE, REGIONI, get_colture_per_regione, get_area_display_name
# ==========================================


# ============= SYSTEM PROMPT UNICO =============
SYSTEM_PROMPT = """Sei un esperto fitosanitario che prepara report concisi per agronomi.
Estrai dai documenti TUTTE le informazioni sulla coltura specificata.

FORMATO OUTPUT (usa esattamente questa struttura Markdown):

## Situazione Attuale
- **Fase fenologica**: [stadio]
- **Periodo**: [date bollettino]

## Avversità e Difesa
### Malattie
| Patogeno | Rischio | Trattamento | Note |
|----------|---------|-------------|------|

### Insetti
| Insetto | Presenza | Soglia | Trattamento |
|---------|----------|--------|-------------|

## Trattamenti Consigliati
| Target | Prodotto | Max interventi | Condizioni |
|--------|----------|----------------|------------|

## Note Operative
[2-3 punti chiave per la settimana]

REGOLE:
1. Estrai SOLO info per la coltura specificata
2. Basati SOLO sui documenti forniti - NON inventare dati
3. NON usare placeholder tipo [non specificato], [da verificare], [N/A]
4. Se non ci sono info specifiche per la coltura, scrivi:
   "Nessuna informazione specifica per questa coltura in questo bollettino."
5. NON mischiare con altre colture
6. Sii CONCISO: info operative, non testi lunghi
7. Tabelle: SOLO righe con dati reali trovati nel bollettino
8. Include soglie numeriche quando disponibili
9. Bollettini invernali (gen-mar): se poche info, è normale - scrivi solo quello che c'è, non inventare"""

QUERY_TEMPLATE = """Coltura: {coltura_nome}
Bollettino N.{numero} del {data}
Province: {province}

DOCUMENTI:
{context}

---
Estrai TUTTE le informazioni specifiche per {coltura_nome} presenti nel bollettino.
Focus su: fenologia, avversità, trattamenti consigliati, deroghe attive."""
# ==========================================


def parse_date_from_filename(filename: str) -> Optional[datetime]:
    """Estrae la data dal nome file nel formato DD-MM-YYYY."""
    match = re.search(r'(\d{2})-(\d{2})-(\d{4})\.md$', filename)
    if match:
        giorno, mese, anno = match.groups()
        return datetime(int(anno), int(mese), int(giorno))
    return None


def move_to_history(file_path: Path, province_slug: str, coltura_dir: Path, logger) -> bool:
    """
    Sposta un file report (MD e HTML) nella cartella history.

    Struttura: {coltura_dir}/history/{anno}/{provincia}/{DD-MM-YYYY.md}
    """
    if not file_path.exists():
        return False

    file_date = parse_date_from_filename(file_path.name)
    if not file_date:
        logger.warning(f"  Impossibile estrarre data da {file_path.name}, skip history")
        return False

    anno = str(file_date.year)

    history_path = coltura_dir / "history" / anno / province_slug
    history_path.mkdir(parents=True, exist_ok=True)

    # Nome file in history: solo la data (DD-MM-YYYY.md)
    date_str = file_path.name.split('_')[-1]  # "01-10-2025.md"
    dest_path = history_path / date_str

    shutil.move(str(file_path), str(dest_path))
    logger.info(f"  → History: {dest_path.relative_to(OUTPUT_DIR)}")

    # Sposta anche il file HTML se esiste
    html_path = file_path.with_suffix('.html')
    if html_path.exists():
        html_dest = dest_path.with_suffix('.html')
        shutil.move(str(html_path), str(html_dest))

    return True


def find_existing_report(province_slug: str, coltura_dir: Path) -> Optional[Path]:
    """Trova un report esistente per la provincia nella cartella coltura."""
    pattern = f"{province_slug}_*.md"
    existing = list(coltura_dir.glob(pattern))
    existing = [f for f in existing if "history" not in str(f)]
    if existing:
        return existing[0]
    return None


def convert_md_to_html(md_content: str, title: str) -> str:
    """Converte contenuto Markdown in HTML con stile CSS."""
    html_body = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code']
    )

    html_template = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #e67e22;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #e67e22;
            padding-left: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #e67e22;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        strong {{
            color: #2c3e50;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 30px 0;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin: 8px 0;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .footer {{
            font-size: 0.85em;
            color: #7f8c8d;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    return html_template


def normalize_province_slug(province: str) -> str:
    """Normalizza il nome della provincia per il nome file."""
    slug = province.lower().replace(' ', '_').replace(',', '_').replace('-', '_').replace('/', '_')
    slug = slug.replace('à', 'a').replace('è', 'e').replace('ì', 'i').replace('ò', 'o').replace('ù', 'u')
    while '__' in slug:
        slug = slug.replace('__', '_')
    return slug.strip('_')


def section_matches(section_title: str, sezioni: List[str]) -> bool:
    """
    Match esatto o prefix-match con word boundary.

    Esempi:
      "BARBABIETOLA DA ZUCCHERO" matcha sezione "BARBABIETOLA"
      "PESCO E NETTARINE" matcha sezione "PESCO"
      "PEROXIDE" NON matcha sezione "PERO"
    """
    # Strip annotazioni "(+N sezioni)" che il chunker aggiunge ai titoli mergiati
    st = re.sub(r'\s*\(\+\d+\s+sezion[ei]\)\s*', '', section_title).upper().strip()
    if not st:
        return False
    for s in sezioni:
        su = s.upper().strip()
        if st == su or st.startswith(su + " "):
            return True
    return False


def looks_like_coltura_heading(section_title: str) -> bool:
    """
    Euristica: titoli SHORT in MAIUSCOLO sono nomi di colture o sotto-colture.
    Usato per escludere sezioni di colture NON configurate (ALBICOCCO, NOCE,
    PATATA, ERBA MEDICA, etc.) dal fallback keyword.
    """
    st = re.sub(r'\s*\(\+\d+\s+sezion[ei]\)\s*', '', section_title).strip()
    if not st:
        return False
    # Tutto uppercase, max 5 parole, alfabetico
    if len(st.split()) <= 5 and st == st.upper() and any(c.isalpha() for c in st):
        return True
    return False


def is_other_coltura_section(section_title: str, current_coltura_id: str) -> bool:
    """
    Verifica se una sezione appartiene a un'ALTRA coltura.

    1. Match contro sezioni di colture configurate (escluse correnti)
    2. Euristica: titolo MAIUSCOLO short non appartenente alla coltura corrente
       → probabilmente un'altra coltura non configurata (ALBICOCCO, NOCE, ...)
    """
    current_sezioni = COLTURE.get(current_coltura_id, {}).get("sezioni", [])

    # 1. Sezione esplicita di altra coltura configurata
    for coltura_id, coltura_data in COLTURE.items():
        if coltura_id == current_coltura_id:
            continue
        if section_matches(section_title, coltura_data["sezioni"]):
            return True

    # 2. Euristica: titolo MAIUSCOLO breve che non matcha la coltura corrente
    if looks_like_coltura_heading(section_title) and not section_matches(section_title, current_sezioni):
        return True

    return False


class ColtureQueryProcessor:
    """
    Processore query RAG per tutte le colture.

    Genera report per ogni coltura trovata nel bollettino.
    Usa retrieval sezione-based con fallback keyword.
    Supporta filtro per regione.
    """

    def __init__(self, regione: str = None):
        """
        Args:
            regione: ID regione (es. "emilia_romagna", "campania").
                     Se None, processa tutte le regioni.
        """
        self.logger = get_logger()
        self.regione = regione

        # Filtra colture per regione
        if regione:
            self.colture = get_colture_per_regione(regione)
            if not self.colture:
                self.logger.warning(f"Nessuna coltura configurata per regione '{regione}'")
                self.colture = COLTURE
        else:
            self.colture = COLTURE

        # Cache separata per regione
        if regione:
            self._cache_file = BASE_DIR / "data" / "cache" / f"colture_{regione}_processed.json"
        else:
            self._cache_file = CACHE_FILE
        self.cache = self._load_cache()

        # Lazy loading
        self._openai_client = None
        self._chromadb_client = None
        self._collection = None

    # ============= CACHE MANAGEMENT =============

    def _load_cache(self) -> dict:
        """Carica cache dei bollettini già processati per ogni coltura."""
        if self._cache_file.exists():
            try:
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Errore caricamento cache: {e}")
        return {"processed": {}, "last_run": None}

    def _save_cache(self):
        """Salva cache su disco."""
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache["last_run"] = datetime.now().isoformat()
        with open(self._cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def _get_cache_key(self, doc_name: str, coltura_id: str) -> str:
        """Genera chiave cache per combinazione bollettino+coltura."""
        return f"{doc_name}::{coltura_id}"

    def _mark_processed(self, doc_name: str, coltura_id: str, output_file: str):
        """Segna una combinazione bollettino+coltura come processata."""
        cache_key = self._get_cache_key(doc_name, coltura_id)
        self.cache["processed"][cache_key] = {
            "processed_at": datetime.now().isoformat(),
            "output_file": output_file
        }
        # Non salvare qui, salva alla fine del batch

    def is_processed(self, doc_name: str, coltura_id: str) -> bool:
        """Verifica se una combinazione è già stata processata."""
        cache_key = self._get_cache_key(doc_name, coltura_id)
        return cache_key in self.cache.get("processed", {})

    def clear_cache(self):
        """Pulisce la cache (forza riprocessamento)."""
        self.cache = {"processed": {}, "last_run": None}
        self._save_cache()
        self.logger.info("Cache cleared")

    # ============= LAZY MODEL LOADING =============

    def _init_models(self):
        """Inizializza modelli solo quando necessario."""
        if self._openai_client is None:
            load_dotenv()

            self.logger.info("Initializing OpenAI client...")
            self._openai_client = OpenAI()

            self.logger.info(f"Connecting to ChromaDB: {COLLECTION_NAME}")
            self._chromadb_client = chromadb.PersistentClient(path=str(CHROMADB_DIR))
            self._collection = self._chromadb_client.get_collection(COLLECTION_NAME)

    # ============= BOLLETTINI RETRIEVAL =============

    def get_available_bollettini(self) -> List[Dict]:
        """Recupera lista bollettini disponibili da ChromaDB, con filtro regione."""
        self._init_models()

        # Filtra per regione se specificata. Nessun limit: la collezione cresce nel tempo
        # e limitare tagliava fuori i bollettini più recenti (inseriti per ultimi).
        if self.regione:
            all_docs = self._collection.get(
                where={"regione": self.regione},
                include=["metadatas"]
            )
        else:
            all_docs = self._collection.get(include=["metadatas"])

        bollettini_map = {}
        for meta in all_docs['metadatas']:
            doc_name = meta.get('doc_name', '')
            province = meta.get('province', '')
            numero = meta.get('numero_bollettino', None)
            data = meta.get('data', '')
            regione = meta.get('regione', 'emilia_romagna')

            if (doc_name
                and doc_name not in bollettini_map
                and province):
                # Per Campania: numero_bollettino puo' essere None
                # Per ER: deve avere numero
                if regione == 'campania' or (numero is not None and numero != ''):
                    bollettini_map[doc_name] = {
                        'doc_name': doc_name,
                        'province': province,
                        'numero_bollettino': numero,
                        'data': data,
                        'regione': regione,
                    }

        return list(bollettini_map.values())

    def get_latest_bollettini_by_province(self) -> List[Dict]:
        """Recupera solo l'ultimo bollettino per ogni provincia."""
        bollettini = self.get_available_bollettini()

        def _safe_numero(val):
            """Converte numero_bollettino in int, gestendo None e '' (Campania)."""
            if val is None or val == '':
                return 0
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        latest_by_province = {}
        for b in bollettini:
            province = b['province']
            sort_key = (b.get('data', ''), _safe_numero(b.get('numero_bollettino')))
            if province not in latest_by_province:
                latest_by_province[province] = b
            else:
                existing = latest_by_province[province]
                existing_key = (existing.get('data', ''), _safe_numero(existing.get('numero_bollettino')))
                if sort_key > existing_key:
                    latest_by_province[province] = b

        return list(latest_by_province.values())

    # ============= RETRIEVAL (SEZIONE + KEYWORD) =============

    def _retrieve_coltura_chunks(self, results: Dict, coltura_id: str) -> List[Dict]:
        """
        Recupera chunks che contengono informazioni sulla coltura specifica.

        Accetta i chunks del bollettino già pre-caricati (fetch ChromaDB unico
        per bollettino in process_bollettino, riusato per tutte le colture).

        Strategy (in ordine di priorità):
        1. Match esatto su section_title (alta precisione)
        2. Se pochi risultati, cerca keywords nel contenuto
        3. FILTRA: Escludi sezioni di ALTRE colture (anti-contaminazione)
        """
        coltura = self.colture[coltura_id]
        sezioni = coltura["sezioni"]
        keywords = coltura["keywords"]

        coltura_chunks = []
        seen_contents = set()  # Evita duplicati

        # Step 1: Match su sezione (alta priorità). Prefix-match con word boundary
        # per catturare varianti come "BARBABIETOLA DA ZUCCHERO" o "PESCO E NETTARINE".
        for doc, meta in zip(results['documents'], results['metadatas']):
            section_title = meta.get('section_title', '')

            if section_matches(section_title, sezioni):
                content_key = doc[:200]
                if content_key not in seen_contents:
                    seen_contents.add(content_key)
                    coltura_chunks.append({
                        "content": doc,
                        "metadata": meta,
                        "match_type": "section"
                    })

        # Step 2: Fallback keyword. Soglia su parole totali (200) invece di chunk count:
        # se il section match ha già contenuto sostanziale, non serve raccogliere chunks
        # rumorosi via keyword (es. PERO con 1951 parole non aveva bisogno del fallback).
        section_words = sum(len(c['content'].split()) for c in coltura_chunks)
        if section_words < 200:
            # Prepara keywords di TUTTE le altre colture per filtro anti-contaminazione
            other_crop_keywords = set()
            for other_id, other_data in COLTURE.items():
                if other_id == coltura_id:
                    continue
                for kw in other_data.get("keywords", [])[:3]:  # prime 3 kw piu' specifiche
                    other_crop_keywords.add(kw.lower())
            # Rimuovi keywords condivise (es. una keyword potrebbe essere in piu' colture)
            my_keywords_set = {kw.lower() for kw in keywords}
            other_crop_keywords -= my_keywords_set

            for doc, meta in zip(results['documents'], results['metadatas']):
                section_title = meta.get('section_title', '')

                # Skip se già incluso
                content_key = doc[:200]
                if content_key in seen_contents:
                    continue

                # FILTRO ANTI-CONTAMINAZIONE: escludi sezioni di altre colture
                if is_other_coltura_section(section_title, coltura_id):
                    continue

                # Match su keywords nel contenuto
                doc_lower = doc.lower()
                content_match = any(kw.lower() in doc_lower for kw in keywords)

                if content_match:
                    # Filtro anti-contaminazione rafforzato:
                    # Se il chunk contiene anche keywords di ALTRE colture,
                    # e' probabilmente un chunk misto (es. "Stato fitosanitario delle colture")
                    # Conta quante keywords nostre vs altre sono presenti
                    my_hits = sum(1 for kw in keywords if kw.lower() in doc_lower)
                    other_hits = sum(1 for kw in other_crop_keywords if kw in doc_lower)
                    if other_hits > my_hits:
                        # Piu' keywords di altre colture che nostre -> chunk contaminato, skip
                        continue
                    seen_contents.add(content_key)
                    coltura_chunks.append({
                        "content": doc,
                        "metadata": meta,
                        "match_type": "keyword"
                    })

        return coltura_chunks

    # ============= LLM GENERATION =============

    def _generate_report(self, bollettino: Dict, coltura_id: str, chunks: List[Dict]) -> str:
        """Genera report per una coltura specifica."""
        coltura = self.colture[coltura_id]

        # Prepara contesto
        context = ""
        for chunk in chunks:
            meta = chunk['metadata']
            section = meta.get('section_title', 'Generale')
            match_type = chunk.get('match_type', 'unknown')
            context += f"\n--- [{section}] (match: {match_type}) ---\n"
            context += chunk['content']
            context += "\n"

        numero = bollettino.get('numero_bollettino')
        numero_str = str(numero) if numero else "N/D"

        user_prompt = QUERY_TEMPLATE.format(
            coltura_nome=coltura['nome'],
            numero=numero_str,
            data=bollettino['data'],
            province=bollettino['province'],
            context=context
        )

        response = self._openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )

        return response.choices[0].message.content

    # ============= OUTPUT =============

    def _save_markdown(self, coltura_id: str, province: str, bollettino: Dict, report_content: str) -> Path:
        """Salva report markdown e HTML per una coltura, spostando il precedente in history."""
        regione = bollettino.get('regione', 'emilia_romagna')
        # Struttura: output_bollettini/{regione}/{coltura}/
        coltura_dir = OUTPUT_DIR / regione / coltura_id.lower()
        coltura_dir.mkdir(parents=True, exist_ok=True)

        province_slug = normalize_province_slug(province)
        data_bollettino = bollettino['data']
        # Converti da ISO (YYYY-MM-DD) a formato italiano (DD-MM-YYYY)
        data_ita = '-'.join(reversed(data_bollettino.split('-')))
        filename = f"{province_slug}_{data_ita}.md"
        md_path = coltura_dir / filename

        # Sposta report precedente in history (se esiste e diverso dal nuovo)
        existing = find_existing_report(province_slug, coltura_dir)
        if existing and existing != md_path:
            move_to_history(existing, province_slug, coltura_dir, self.logger)

        coltura = self.colture[coltura_id]

        # Nome visualizzazione: usa nome completo area se disponibile
        display_name = get_area_display_name(province) if province else province

        md_content = f"""# {coltura['nome']} - {display_name}

**Bollettino{' N.' + str(bollettino['numero_bollettino']) if bollettino.get('numero_bollettino') else ''}** | {data_ita}

---

{report_content}

---
*Report generato: {datetime.now().strftime('%d/%m/%Y %H:%M')}*
"""

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Genera HTML
        title = f"{coltura['nome']} - {display_name}"
        html_content = convert_md_to_html(md_content, title)
        html_path = md_path.with_suffix('.html')
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return md_path

    # ============= MAIN PROCESSING =============

    def process_bollettino_coltura(self, bollettino: Dict, coltura_id: str, bollettino_chunks: Dict) -> Optional[Path]:
        """
        Processa un singolo bollettino per una coltura specifica.

        Args:
            bollettino_chunks: Chunks del bollettino pre-caricati da ChromaDB
                (evita N query ripetute, una per coltura).

        Returns:
            Path del file markdown generato, o None se no chunks trovati
        """
        doc_name = bollettino['doc_name']
        province = bollettino['province']

        # Retrieval sezione-based + keyword fallback sui chunks già caricati
        chunks = self._retrieve_coltura_chunks(bollettino_chunks, coltura_id)
        coltura = self.colture[coltura_id]

        if not chunks:
            # Report statico senza chiamata LLM
            report_content = f"Nessuna informazione specifica per {coltura['nome']} in questo bollettino."
        else:
            # LLM Generation
            report_content = self._generate_report(bollettino, coltura_id, chunks)

        # Salva markdown + HTML (anche se contiene "nessuna informazione")
        md_path = self._save_markdown(coltura_id, province, bollettino, report_content)

        # Aggiorna cache
        self._mark_processed(doc_name, coltura_id, md_path.name)

        return md_path

    def process_bollettino(self, bollettino: Dict, force: bool = False) -> Tuple[int, int]:
        """
        Processa un bollettino per TUTTE le colture.

        Returns:
            (success_count, total_count)
        """
        doc_name = bollettino['doc_name']
        province = bollettino['province']

        self.logger.info(f"Processing: {province} (Bollettino {bollettino['numero_bollettino']})")

        # Fetch chunks del bollettino UNA VOLTA, riusati per tutte le colture
        bollettino_chunks = self._collection.get(
            where={"doc_name": doc_name},
            include=["documents", "metadatas"]
        )

        success = 0
        skipped = 0

        for coltura_id in self.colture:
            # Check cache
            if not force and self.is_processed(doc_name, coltura_id):
                skipped += 1
                continue

            try:
                result = self.process_bollettino_coltura(bollettino, coltura_id, bollettino_chunks)
                if result:
                    success += 1
                    self.logger.info(f"  {coltura_id}: {result.name}")
            except Exception as e:
                self.logger.error(f"  {coltura_id}: {e}")

        if skipped > 0:
            self.logger.info(f"  -> {skipped} colture gia in cache")

        return success, len(self.colture)

    def process_new_only(self) -> Tuple[bool, Dict]:
        """Processa solo bollettini nuovi (non completamente in cache)."""
        start_time = time.time()

        self.logger.info("=" * 60)
        self.logger.info("COLTURE - Report per tutte le colture")
        self.logger.info("=" * 60)

        self._init_models()

        bollettini = self.get_latest_bollettini_by_province()

        if not bollettini:
            self.logger.info("Nessun bollettino disponibile")
            return False, {
                'processed': 0,
                'total': 0,
                'reason': 'no_bollettini',
                'duration_seconds': time.time() - start_time
            }

        self.logger.info(f"Bollettini da processare: {len(bollettini)}")
        self.logger.info(f"Colture: {len(self.colture)}")

        total_success = 0
        total_processed = 0

        for bollettino in bollettini:
            success, total = self.process_bollettino(bollettino)
            total_success += success
            total_processed += total

        # Salva cache una volta alla fine
        self._save_cache()

        duration = time.time() - start_time

        self.logger.info("=" * 60)
        self.logger.info(f"Completato: {total_success} report generati in {duration:.1f}s")
        self.logger.info("=" * 60)

        return total_success > 0, {
            'processed': total_success,
            'total': total_processed,
            'bollettini': len(bollettini),
            'colture': len(COLTURE),
            'duration_seconds': duration
        }

    def process_all(self, force: bool = False) -> Tuple[bool, Dict]:
        """Processa tutti i bollettini (ultimo per provincia)."""
        start_time = time.time()

        if force:
            self.clear_cache()

        self.logger.info("=" * 60)
        self.logger.info("COLTURE - Report per tutte le colture (ALL)")
        self.logger.info("=" * 60)

        self._init_models()

        bollettini = self.get_latest_bollettini_by_province()

        if not bollettini:
            self.logger.info("Nessun bollettino disponibile")
            return False, {
                'processed': 0,
                'total': 0,
                'reason': 'no_bollettini',
                'duration_seconds': time.time() - start_time
            }

        self.logger.info(f"Bollettini: {len(bollettini)}")
        self.logger.info(f"Colture: {len(self.colture)}")

        total_success = 0
        total_processed = 0

        for bollettino in bollettini:
            success, total = self.process_bollettino(bollettino, force=force)
            total_success += success
            total_processed += total

        # Salva cache
        self._save_cache()

        duration = time.time() - start_time

        self.logger.info("=" * 60)
        self.logger.info(f"Completato: {total_success} report in {duration:.1f}s")
        self.logger.info("=" * 60)

        return total_success > 0, {
            'processed': total_success,
            'total': total_processed,
            'bollettini': len(bollettini),
            'colture': len(COLTURE),
            'duration_seconds': duration
        }


def main() -> int:
    """Entry point CLI."""
    processor = ColtureQueryProcessor()
    has_processed, stats = processor.process_new_only()
    return 0 if has_processed else 1


if __name__ == "__main__":
    exit(main())
