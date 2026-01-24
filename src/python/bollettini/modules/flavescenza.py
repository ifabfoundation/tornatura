"""
Modulo per query RAG sulla Flavescenza Dorata e Scaphoideus titanus.

Estrae informazioni dai bollettini fitosanitari e dalla normativa regionale usando:
- Retrieval keyword-based: chunks con keywords specifiche dal bollettino
- Normativa strutturata: dati pre-processati filtrati per provincia
- Generazione risposte con GPT-4o-mini

Output: Report condensato per agronomi viticoltori con tutte le info essenziali.

Utilizzo:
    # Da scheduler (processa solo nuovi bollettini)
    processor = FlavescenzaQueryProcessor()
    has_new, stats = processor.process_new_only()

    # Da linea di comando
    python flavescenza.py
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

# Import normativa strutturata (gestisce sia import come modulo che esecuzione diretta)
try:
    from .normativa_flavescenza import formatta_normativa_per_llm, get_info_normativa
except ImportError:
    from normativa_flavescenza import formatta_normativa_per_llm, get_info_normativa

# ============= CONFIGURAZIONE =============
BASE_DIR = Path(__file__).parent.parent
CHROMADB_DIR = BASE_DIR / "data" / "chromadb"
OUTPUT_DIR = paths.OUTPUT_FLAVESCENZA_DIR
HISTORY_DIR = OUTPUT_DIR / "history"
CACHE_FILE = BASE_DIR / "data" / "cache" / "flavescenza_processed.json"
COLLECTION_NAME = "flavescenza_dorata"

# Modello LLM
LLM_MODEL = "gpt-4o-mini"

# Keywords per identificare chunks rilevanti nel bollettino
# (basate sull'analisi di 29 bollettini Bologna-Ferrara)
FLAVESCENZA_KEYWORDS = [
    'flavescenza', 'scaphoideus', 'scafoideo', 'titanus',
    'giallumi', 'fitoplasm'  # fitoplasma/fitoplasmi
]
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


# ============= SYSTEM PROMPT OTTIMIZZATO =============
SYSTEM_PROMPT = """Sei un esperto fitosanitario che prepara report concisi per agronomi viticoltori.
Estrai dai documenti TUTTE le informazioni su Flavescenza Dorata e Scaphoideus titanus.

FORMATO OUTPUT (usa esattamente questa struttura Markdown):

## 📊 Monitoraggio Scafoideo
- **Forme giovanili**: [stadio, presenza, trend ↑↓→]
- **Catture adulti**: [livello, trend ↑↓→]
- **Fase biologica**: [neanidi | ninfe | adulti | svernamento]

RIFERIMENTO STAGIONALE:
- Primavera (mag-giu): neanidi → ninfe, inizio trattamenti
- Estate (lug-ago): adulti, PICCO trattamenti
- Autunno (set-ott): declino, focus su estirpo sintomatiche

## ⚠️ Scadenze Trattamenti Obbligatori
| Tipo azienda | 1° trattamento | 2° trattamento |
|--------------|----------------|----------------|
| Integrata | [data] | [data] |
| Biologica | [data] | [data] |

**Inizio lotta obbligatoria**: [data]
**Condizioni**: [sfioritura completa + sfalcio fioriture sottostanti]

## 💊 Prodotti Autorizzati
### Difesa Integrata
| Sostanza attiva | Limitazioni |
|-----------------|-------------|
| [nome] | [max interventi/anno, note] |

### Difesa Biologica
| Sostanza attiva | Limitazioni |
|-----------------|-------------|
| [nome] | [note] |

**NOTA piretroidi**: Max 4 interventi/anno complessivi

## 🎯 Strategia Difesa Raccomandata
**Integrata**:
- 1° trattamento: [prodotti consigliati]
- 2° trattamento: [prodotti consigliati]

**Biologica**:
- 1° trattamento: [prodotti consigliati]
- 2° trattamento: Piretrine pure (OBBLIGATORIO)
- ⚠️ Almeno 1 dei 2 trattamenti DEVE essere con piretrine

## 📋 Deroghe Attive
| Prodotto (s.a.) | Coltura | Validità |
|-----------------|---------|----------|
| [nome + s.a.] | VITE | [dal-al] |

## 🔧 Accorgimenti Operativi
- Volume acqua: [minimo lt/ha]
- pH soluzione: [requisito]
- Timing: [ore consigliate per prodotti fotolabili]
- Preparazione: [cimatura, spollonatura, etc.]

## 🐝 Tutela Api
- Divieto trattamento durante fioritura vite
- Divieto in presenza fioriture spontanee sottostanti (sfalciare prima)
- Trattare nelle ore serali

## 🗺️ Zone Delimitate (da Determinazione N.9016)
- **Zona infestata**: [comuni principali o "vedi determinazione"]
- **Zona cuscinetto**: [comuni o "500m perimetrale"]

## 🌿 Gestione Piante Sintomatiche
- **Obbligo estirpo**: [SI - immediato / entro data]
- **Capitozzatura**: [ammessa come alternativa temporanea]
- **Piante madri/barbatellai**: [obblighi specifici se presenti]

## ⚖️ Sanzioni
€1.000 - €6.000 (D.Lgs. 19/2021, art. 55)

## ✅ Azione Consigliata
[2-3 frasi operative: cosa deve fare l'agronomo ADESSO]

REGOLE:
1. Basati SOLO sui documenti forniti (bollettino + normativa)
2. Ignora altre avversità (cimice, oidio, peronospora, etc.)
3. INVERNO/INIZIO PRIMAVERA (gen-apr): se non ci sono info scafoideo, scrivi:
   "📅 Periodo pre-volo - monitoraggio scafoideo inizia a maggio."
4. NON ripetere le stesse informazioni in sezioni diverse
5. DISTINGUI tra info da [BOLLETTINO] e info da [NORMATIVA]
6. Sii CONCISO: l'agronomo vuole info operative, non testi lunghi
7. Tabelle: SOLO righe con dati reali trovati
8. Per zone delimitate con molti comuni, indica "Vedi Determinazione N.9016"
9. Per strategie difesa: indica SEMPRE quale prodotto per quale trattamento
"""

QUERY_AGGREGATA = """Estrai dal bollettino e dalla normativa TUTTE le informazioni su Flavescenza Dorata e Scaphoideus titanus:

1. MONITORAGGIO SCAFOIDEO:
   - Presenza/stadio forme giovanili (neanidi, ninfe)
   - Catture adulti (livello, trend)
   - Fase biologica attuale

2. SCADENZE TRATTAMENTI:
   - Data inizio lotta obbligatoria
   - Condizioni preliminari (sfioritura, sfalcio)
   - Scadenza 1° trattamento (integrata e biologica)
   - Scadenza 2° trattamento (integrata e biologica)

3. PRODOTTI AUTORIZZATI:
   - Lista prodotti difesa INTEGRATA con limitazioni
   - Lista prodotti difesa BIOLOGICA con limitazioni
   - Note su piretroidi (max interventi/anno)

4. STRATEGIA DIFESA:
   - Quali prodotti per 1° trattamento (integrata vs biologica)
   - Quali prodotti per 2° trattamento (integrata vs biologica)
   - Obbligo piretrine per biologico

5. DEROGHE ATTIVE:
   - Nome formulato + sostanza attiva
   - Date validità (dal-al)

6. ACCORGIMENTI OPERATIVI:
   - Volume acqua minimo (lt/ha)
   - Correzione pH
   - Timing trattamento (ore serali per fotolabili)
   - Preparazione (cimatura, spollonatura)

7. TUTELA API:
   - Divieti durante fioritura
   - Sfalcio fioriture spontanee
   - Orario trattamenti

8. ZONE DELIMITATE (da normativa):
   - Comuni zona infestata
   - Comuni zona cuscinetto

9. PIANTE SINTOMATICHE:
   - Obbligo estirpo (quando, come)
   - Capitozzatura ammessa?
   - Obblighi per piante madri/barbatellai

10. SANZIONI:
    - Importo min-max
    - Riferimento normativo

11. AZIONE CONSIGLIATA:
    - Monitoraggio (quando, come)
    - Trattamenti (se previsti nel periodo)
    - Ispezione piante (se post-raccolta)

NOTA: Bollettini N.1-12 (gen-apr) tipicamente hanno poche info scafoideo (pre-volo).
      Bollettini N.13+ (mag-ott) hanno info complete su lotta obbligatoria."""
# ==========================================


def normalize_province_slug(province: str) -> str:
    """Normalizza il nome della provincia per il nome file."""
    slug = province.lower().replace(' ', '_').replace(',', '_').replace('-', '_').replace('/', '_')
    slug = slug.replace('à', 'a').replace('è', 'e').replace('ì', 'i').replace('ò', 'o').replace('ù', 'u')
    while '__' in slug:
        slug = slug.replace('__', '_')
    return slug.strip('_')


def parse_date_from_filename(filename: str) -> Optional[datetime]:
    """
    Estrae la data dal nome file nel formato DD-MM-YYYY.

    Es: bologna_ferrara_01-10-2025.md -> datetime(2025, 10, 1)
    """
    match = re.search(r'(\d{2})-(\d{2})-(\d{4})\.md$', filename)
    if match:
        giorno, mese, anno = match.groups()
        return datetime(int(anno), int(mese), int(giorno))
    return None


def move_to_history(file_path: Path, province_slug: str, logger) -> bool:
    """
    Sposta un file report (MD e HTML) nella cartella history.

    Struttura: history/{anno}/{provincia}/{nome_file}
    """
    if not file_path.exists():
        return False

    # Estrai anno dalla data nel nome file
    file_date = parse_date_from_filename(file_path.name)
    if not file_date:
        logger.warning(f"  Impossibile estrarre data da {file_path.name}, skip history")
        return False

    anno = str(file_date.year)

    # Crea struttura history/{anno}/{provincia}/
    history_path = HISTORY_DIR / anno / province_slug
    history_path.mkdir(parents=True, exist_ok=True)

    # Nome file in history: solo la data (DD-MM-YYYY.md)
    date_str = file_path.name.split('_')[-1]  # "01-10-2025.md"
    dest_path = history_path / date_str

    # Sposta il file MD
    shutil.move(str(file_path), str(dest_path))
    logger.info(f"  → History: {dest_path.relative_to(OUTPUT_DIR)}")

    # Sposta anche il file HTML se esiste
    html_path = file_path.with_suffix('.html')
    if html_path.exists():
        html_dest = dest_path.with_suffix('.html')
        shutil.move(str(html_path), str(html_dest))

    return True


def find_existing_report(province_slug: str) -> Optional[Path]:
    """
    Trova un report esistente per la provincia nella cartella output.

    Returns:
        Path del file esistente o None
    """
    pattern = f"{province_slug}_*.md"
    existing = list(OUTPUT_DIR.glob(pattern))

    # Escludi file nella cartella history
    existing = [f for f in existing if "history" not in str(f)]

    if existing:
        return existing[0]  # Dovrebbe essercene solo uno
    return None


def convert_md_to_html(md_content: str, title: str) -> str:
    """
    Converte contenuto Markdown in HTML con stile CSS.
    """
    # Converti MD in HTML
    html_body = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code']
    )

    # Template HTML con CSS embedded
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
            border-bottom: 3px solid #27ae60;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #27ae60;
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
            background-color: #27ae60;
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


class FlavescenzaQueryProcessor:
    """
    Processore query RAG per Flavescenza Dorata e Scaphoideus titanus.
    
    Genera report condensati con retrieval ibrido:
    - Keywords dal bollettino provinciale
    - Tutti i chunks dal documento normativo
    """
    
    def __init__(self):
        self.logger = get_logger()
        self.cache = self._load_cache()
        
        # Lazy loading
        self._openai_client = None
        self._chromadb_client = None
        self._collection = None
    
    # ============= CACHE MANAGEMENT =============
    
    def _load_cache(self) -> dict:
        """Carica cache dei bollettini già processati."""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Errore caricamento cache: {e}")
        return {"processed": {}, "last_run": None}
    
    def _save_cache(self):
        """Salva cache su disco."""
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.cache["last_run"] = datetime.now().isoformat()
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def _mark_processed(self, doc_name: str, output_file: str):
        """Segna un bollettino come processato."""
        self.cache["processed"][doc_name] = {
            "processed_at": datetime.now().isoformat(),
            "output_file": output_file
        }
        self._save_cache()
    
    def is_processed(self, doc_name: str) -> bool:
        """Verifica se un bollettino è già stato processato."""
        return doc_name in self.cache.get("processed", {})
    
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
        """Recupera lista bollettini disponibili da ChromaDB (esclusa normativa)."""
        self._init_models()
        
        all_docs = self._collection.get(limit=5000, include=["metadatas"])
        
        bollettini_map = {}
        for meta in all_docs['metadatas']:
            doc_name = meta.get('doc_name', '')
            province = meta.get('province', '')
            numero = meta.get('numero_bollettino', None)
            data = meta.get('data', '')
            
            if (doc_name
                and doc_name not in bollettini_map
                and numero is not None
                and numero != ''
                and province):
                bollettini_map[doc_name] = {
                    'doc_name': doc_name,
                    'province': province,
                    'numero_bollettino': numero,
                    'data': data
                }
        
        return list(bollettini_map.values())
    
    def get_latest_bollettini_by_province(self) -> List[Dict]:
        """Recupera solo l'ultimo bollettino per ogni provincia."""
        bollettini = self.get_available_bollettini()
        
        latest_by_province = {}
        for b in bollettini:
            province = b['province']
            numero = int(b['numero_bollettino'])
            if province not in latest_by_province or numero > int(latest_by_province[province]['numero_bollettino']):
                latest_by_province[province] = b
        
        return list(latest_by_province.values())
    
    def get_new_bollettini(self) -> List[Dict]:
        """Recupera bollettini non ancora processati."""
        latest = self.get_latest_bollettini_by_province()
        return [b for b in latest if not self.is_processed(b['doc_name'])]
    
    # ============= KEYWORD-BASED RETRIEVAL =============
    
    def _retrieve_bollettino_chunks(self, doc_name: str) -> List[Dict]:
        """
        Recupera chunks con info su flavescenza/scafoideo dal BOLLETTINO.

        Solo chunks con keywords specifiche (flavescenza, scaphoideus, etc.).
        La normativa viene gestita separatamente dal modulo normativa_flavescenza.
        """
        chunks = []

        results = self._collection.get(
            where={"doc_name": doc_name},
            include=["documents", "metadatas"]
        )

        for doc, meta in zip(results['documents'], results['metadatas']):
            section_title = meta.get('section_title', '').lower()

            # Salta sezioni cimice
            if any(kw in section_title for kw in ['cimice', 'halyomorpha']):
                continue

            # Include solo chunks con keywords flavescenza
            has_flavescenza_info = any(kw.lower() in doc.lower() for kw in FLAVESCENZA_KEYWORDS)
            if has_flavescenza_info:
                chunks.append({
                    "content": doc,
                    "metadata": meta
                })

        self.logger.info(f"  Found {len(chunks)} bollettino chunks with flavescenza keywords")

        return chunks
    
    # ============= LLM GENERATION =============
    
    def _generate_report(self, bollettino: Dict, chunks: List[Dict]) -> str:
        """
        Genera report condensato con una singola chiamata LLM.

        Combina:
        - Chunks dal bollettino (retrieval keyword-based)
        - Normativa strutturata filtrata per provincia (da normativa_flavescenza.py)
        """
        province = bollettino['province']
        context = ""

        # 1. Chunks del bollettino
        if chunks:
            context += "\n=== BOLLETTINO PROVINCIALE ===\n"
            for chunk in chunks:
                section = chunk['metadata'].get('section_title', 'Generale')
                context += f"\n--- {section} ---\n"
                context += chunk['content']
                context += "\n"

        # 2. Normativa strutturata (filtrata per provincia)
        normativa_text = formatta_normativa_per_llm(province)
        if normativa_text:
            context += f"\n{normativa_text}\n"
        else:
            self.logger.warning(f"  Normativa non trovata per provincia: {province}")

        user_prompt = f"""Bollettino N.{bollettino['numero_bollettino']} del {bollettino['data']}
Provincia: {province}

DOCUMENTI:
{context}

---
{QUERY_AGGREGATA}"""

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
    
    def _save_markdown(self, province: str, bollettino: Dict, report_content: str) -> Path:
        """Salva report markdown, spostando eventuale report precedente in history."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        province_slug = normalize_province_slug(province)
        data_bollettino = bollettino['data']
        # Converti da ISO (YYYY-MM-DD) a formato italiano (DD-MM-YYYY)
        data_ita = '-'.join(reversed(data_bollettino.split('-')))
        filename = f"{province_slug}_{data_ita}.md"
        md_path = OUTPUT_DIR / filename

        # Gestione history: sposta report precedente se esiste e ha data diversa
        existing_report = find_existing_report(province_slug)
        if existing_report and existing_report.name != filename:
            # Data diversa = bollettino diverso, sposta in history
            existing_date = parse_date_from_filename(existing_report.name)
            new_date = datetime.strptime(data_bollettino, '%Y-%m-%d')

            if existing_date and existing_date < new_date:
                move_to_history(existing_report, province_slug, self.logger)

        # Info normativa dinamica
        normativa_info = get_info_normativa()

        # Warning se normativa è dell'anno precedente
        anno_corrente = datetime.now().year
        normativa_warning = ""
        if normativa_info['anno'] < anno_corrente:
            normativa_warning = f"\n\n> **Nota**: Normativa {normativa_info['anno']} - in attesa della Determinazione {anno_corrente} (prevista maggio)\n"

        md_content = f"""# Flavescenza Dorata - {province}

**Bollettino N.{bollettino['numero_bollettino']}** | {data_ita}
**Normativa**: Determinazione Regionale {normativa_info['determinazione']}{normativa_warning}

---

{report_content}

---
*Report generato: {datetime.now().strftime('%d/%m/%Y %H:%M')}*
"""

        # Salva Markdown
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Salva HTML
        html_path = md_path.with_suffix('.html')
        html_content = convert_md_to_html(md_content, f"Flavescenza Dorata - {province}")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return md_path
    
    # ============= MAIN PROCESSING =============
    
    def process_bollettino(self, bollettino: Dict) -> Optional[Path]:
        """
        Processa un singolo bollettino.

        Returns:
            Path del file markdown generato, o None se errore
        """
        doc_name = bollettino['doc_name']
        province = bollettino['province']

        self.logger.info(f"Processing: {province} (Bollettino {bollettino['numero_bollettino']})")

        # Retrieval keyword-based (solo bollettino, normativa da modulo Python)
        chunks = self._retrieve_bollettino_chunks(doc_name)

        # Nota: chunks vuoti sono OK per bollettini invernali (gen-apr)
        # La normativa viene sempre inclusa dal modulo normativa_flavescenza

        # LLM Generation (singola chiamata)
        report_content = self._generate_report(bollettino, chunks)

        # Salva markdown
        md_path = self._save_markdown(province, bollettino, report_content)

        # Aggiorna cache
        self._mark_processed(doc_name, md_path.name)

        self.logger.info(f"  Saved: {md_path.name}")
        return md_path
    
    def process_bollettini(self, bollettini: List[Dict]) -> Tuple[int, int]:
        """Processa una lista di bollettini."""
        if not bollettini:
            self.logger.info("Nessun bollettino da processare")
            return 0, 0
        
        self._init_models()
        
        success = 0
        for bollettino in bollettini:
            try:
                result = self.process_bollettino(bollettino)
                if result:
                    success += 1
            except Exception as e:
                self.logger.error(f"Errore processing {bollettino['doc_name']}: {e}")
        
        return success, len(bollettini)
    
    def process_new_only(self) -> Tuple[bool, Dict]:
        """Processa solo bollettini nuovi (non in cache)."""
        start_time = time.time()
        
        self.logger.info("=" * 60)
        self.logger.info("FLAVESCENZA DORATA - Report Condensati")
        self.logger.info("=" * 60)
        
        new_bollettini = self.get_new_bollettini()
        
        if not new_bollettini:
            self.logger.info("Nessun nuovo bollettino da processare")
            return False, {
                'processed': 0,
                'total': 0,
                'reason': 'no_new_bollettini',
                'duration_seconds': time.time() - start_time
            }
        
        self.logger.info(f"Trovati {len(new_bollettini)} nuovi bollettini")
        
        success, total = self.process_bollettini(new_bollettini)
        duration = time.time() - start_time
        
        self.logger.info("=" * 60)
        self.logger.info(f"Completato: {success}/{total} in {duration:.1f}s")
        self.logger.info("=" * 60)
        
        return success > 0, {
            'processed': success,
            'total': total,
            'duration_seconds': duration,
            'bollettini': [b['doc_name'] for b in new_bollettini[:success]]
        }
    
    def process_all(self, force: bool = False) -> Tuple[bool, Dict]:
        """Processa tutti i bollettini (ultimo per provincia)."""
        start_time = time.time()
        
        if force:
            self.clear_cache()
        
        self.logger.info("=" * 60)
        self.logger.info("FLAVESCENZA DORATA - Report Condensati (ALL)")
        self.logger.info("=" * 60)
        
        bollettini = self.get_latest_bollettini_by_province()
        
        if not force:
            bollettini = [b for b in bollettini if not self.is_processed(b['doc_name'])]
        
        if not bollettini:
            self.logger.info("Nessun bollettino da processare")
            return False, {
                'processed': 0,
                'total': 0,
                'reason': 'all_cached',
                'duration_seconds': time.time() - start_time
            }
        
        self.logger.info(f"Processing {len(bollettini)} bollettini")
        
        success, total = self.process_bollettini(bollettini)
        duration = time.time() - start_time
        
        self.logger.info("=" * 60)
        self.logger.info(f"Completato: {success}/{total} in {duration:.1f}s")
        self.logger.info("=" * 60)
        
        return success > 0, {
            'processed': success,
            'total': total,
            'duration_seconds': duration
        }


def main() -> int:
    """Entry point CLI."""
    processor = FlavescenzaQueryProcessor()
    has_processed, stats = processor.process_new_only()
    return 0 if has_processed else 1


if __name__ == "__main__":
    exit(main())
