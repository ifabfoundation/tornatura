"""
Script per processare i bollettini fitosanitari:
1. Converte PDF in Markdown in memoria (usando Docling)
2. Chunking per sezioni
3. Genera embeddings e carica direttamente su ChromaDB

Include cache per evitare di riprocessare bollettini già indicizzati.
Nessun file intermedio (markdown/json) viene salvato su disco.

Uso:
    # Come script (processa tutti i nuovi bollettini)
    python process_bollettini.py
    
    # Come modulo (per scheduler/orchestrator)
    from modules.process_bollettini import BollettiniProcessor
    processor = BollettiniProcessor()
    has_new, stats = processor.process_all()
    
    # Processare file specifici (dopo download)
    processor.process_files([Path("file1.pdf"), Path("file2.pdf")])
"""

from pathlib import Path
import re
import json
import logging
import warnings
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Suppress noisy loggers and warnings before imports
os.environ["RAPIDOCR_LOGGING"] = "ERROR"
os.environ["ONNXRUNTIME_LOGGING_LEVEL"] = "ERROR"

logging.getLogger("docling").setLevel(logging.ERROR)
logging.getLogger("docling.pipeline").setLevel(logging.ERROR)
logging.getLogger("rapidocr").setLevel(logging.ERROR)
logging.getLogger("RapidOCR").setLevel(logging.ERROR)
logging.getLogger("onnxruntime").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from docling.document_converter import DocumentConverter, PdfFormatOption

from bollettini import paths
from bollettini.modules.chunk_store import ChunkStore

# ============= CONFIGURAZIONE =============
INPUT_DIR = paths.DATA_DIR / "input_bollettini" / "emilia_romagna" / "bollettini"
CHUNKSTORE_DB = paths.DATA_DIR / "chunks.db"
CACHE_FILE = paths.DATA_DIR / "cache" / "processing_cache.json"

# Parametri chunking
MIN_CHUNK_WORDS = 50           # Minimo parole per chunk valido
MERGE_THRESHOLD = 100          # Sezioni sotto questa soglia vengono unite alla successiva
SECTION_PATTERN = re.compile(r"^#{1,3}\s+.+")

# Sezioni da NON unire (colture e sezioni importanti) - mantienile intere
PROTECTED_SECTIONS = {
    # Colture (ER + Campania)
    'MELO', 'PERO', 'PESCO', 'SUSINO', 'CILIEGIO', 'ALBICOCCO',
    'ACTINIDIA', 'KAKI', 'VITE', 'NOCE', 'NOCCIOLO', 'OLIVO',
    'FRUMENTO', 'ORZO', 'COLZA', 'MAIS', 'SOIA',
    'POMODORO', 'PATATA', 'CIPOLLA', 'CAROTA',
    'AGRUMI', 'CASTAGNO', 'OLIVICOLTURA', 'CORILICOLTURA',
    # Varianti Campania con prefisso "COLTURA:"
    'COLTURA: PESCO', 'COLTURA:PESCO',
    'COLTURA: OLIVO', 'COLTURA:OLIVO',
    'COLTURA:ACTINIDIA', 'COLTURA: ACTINIDIA',
    'COLTURA MELO', 'COLTURA: MELO',
    'COLTURA NOCCIOLO', 'COLTURA: NOCCIOLO',
    'COLTURA CASTAGNO', 'COLTURA: CASTAGNO',
    'COLTURA CILIEGIO', 'COLTURA: CILIEGIO',
    'COLTURA SUSINO', 'COLTURA: SUSINO',
    # Cimice asiatica
    'INFORMAZIONI RIGUARDANTI LA CIMICE ASIATICA',
    # Flavescenza dorata e Scafoideo
    'LOTTA OBBLIGATORIA CONTRO FLAVESCENZA DORATA',
    'TRATTAMENTI INSETTICIDI OBBLIGATORI',
    'SOSTANZE ATTIVE CONTRO LO SCAFOIDEO',
    'STRATEGIA DI INTERVENTO',
    'ACCORGIMENTI PER AUMENTARE L\'EFFICACIA',
    'AZIENDE IN DIFESA INTEGRATA',
    # Deroghe
    'DEROGHE AI DISCIPLINARI DI PRODUZIONE INTEGRATA',
    # Normativa
    'SANZIONI',
    'D E T E R M I N A'
}

# ============= GROUP DIVIDERS (ER) =============
# Nei bollettini ER le colture sono raggruppate in: ARBOREE -> ERBACEE -> ORTICOLE
# (sempre in quest'ordine). Questi divisori chiudono comunque la coltura corrente
# anche se non c'e' una nuova coltura subito dopo.
GROUP_DIVIDERS = {
    'COLTURE ARBOREE',
    'COLTURE ERBACEE',
    'COLTURE ORTICOLE',
    'DISERBO ARBOREE',
    'DISERBO ERBACEE',
    'DIFESA ARBOREE',
}

# Marker che chiude la parte di Produzione Integrata (per ER).
# Tutto cio' che segue (Produzione Biologica) viene scartato per ora.
PI_END_MARKER = re.compile(
    r'^#{1,3}\s+BOLLETTINO\s+DI\s+PRODUZIONE\s+BIOLOGICA',
    re.M | re.I,
)
# ==========================================


# ============= PARENT COLTURA TRACKING =============
# Mappa header sezione -> coltura ID (canonical).
# Header NON in questa mappa NON cambiano la coltura corrente: le sotto-sezioni
# (Difesa, Diserbo, Tecniche agronomiche, Vincoli, ecc.) ereditano cosi'
# automaticamente la coltura padre vista a monte.
#
# Coltura ID prefissato con '_' = coltura ER non configurata (frumento, mais,
# colza...) - serve solo a "consumare" il flusso, le sezioni con questi parent
# non verranno mai recuperate dal retrieval (che matcha solo ID configurati).
COLTURA_HEADER_TO_ID = {
    # === Configurate (ER + Campania) ===
    'VITE': 'VITE',
    'PERO': 'PERO',
    'PESCO': 'PESCO',
    'PESCO E NETTARINE': 'PESCO',
    'MAIS': 'MAIS',
    'GRANOTURCO': 'MAIS',
    'BARBABIETOLA': 'BARBABIETOLA',
    'BARBABIETOLA DA ZUCCHERO': 'BARBABIETOLA',
    'BIETOLA': 'BARBABIETOLA',
    'OLIVO': 'OLIVO',
    'AGRUMI': 'AGRUMI',
    'ACTINIDIA': 'ACTINIDIA',
    'NOCCIOLO': 'NOCCIOLO',
    'NOCE': 'NOCE',
    'CIPOLLA': 'CIPOLLA',
    'POMODORO': 'POMODORO',
    'POMODORO DA INDUSTRIA': 'POMODORO',
    'FRAGOLA': 'FRAGOLA',
    'CASTAGNO': 'CASTAGNO',
    'CILIEGIO': 'CILIEGIO',
    'MELO': 'MELO',
    'PATATA': 'PATATA',
    'SUSINO': 'SUSINO',
    'SUSINO CINO-GIAPPONESE ED EUROPEO': 'SUSINO',
    'ALBICOCCO': 'ALBICOCCO',
    # === ER non configurate (consumano il flusso) ===
    'KAKI': '_KAKI',
    'COLZA': '_COLZA',
    'ERBA MEDICA': '_ERBA_MEDICA',
    'FRUMENTO': '_FRUMENTO',
    'GIRASOLE': '_GIRASOLE',
    'RISO': '_RISO',
    'SOIA': '_SOIA',
    'SORGO': '_SORGO',
    'AGLIO': '_AGLIO',
    'ANGURIA': '_ANGURIA',
    'ANGURIA (COLTURA SEMI FORZATA)': '_ANGURIA',
    'ANGURIA (COLTURA SEMIFORZATA)': '_ANGURIA',
    'ASPARAGO': '_ASPARAGO',
    'CAROTA': '_CAROTA',
    'MELONE': '_MELONE',
    'MELONE (COLTURA SEMI FORZATA)': '_MELONE',
    'PISELLO': '_PISELLO',
    'ORZO': '_ORZO',
}
# ==========================================


# ============= SEZIONI TRASVERSALI (modello a due assi) =============
# Sezioni che NON sono blocchi-coltura ma contengono informazioni operative valide
# per piu' colture (lotta obbligatoria, deroghe, revoche, rame, diserbo, ecc.).
# Lo slice-by-coltura le scartava: qui le catturiamo e le attacchiamo alle colture
# pertinenti via il campo metadata `applies_to`.
#
# Match per PREFISSO sul titolo header normalizzato (uppercase, senza ':' finale).
# Valore: lista di coltura_id ER configurate, oppure la stringa "ALL" (tutte).
# Mappatura curata sull'analisi di 8 bollettini (2 province x 4 stagioni).
#
# Valori di applies_to:
#   - "PER_VOCE": sezione-LISTA dove ogni voce nomina la propria coltura (es. DEROGHE).
#                 A query-time viene FILTRATA per-voce: a ogni coltura arrivano solo le
#                 voci che la nominano (filtro deterministico, vedi colture.py). Cosi' niente
#                 mis-attribuzione e niente voci perse.
#   - "" (vuota): sezione riconosciuta solo come CONFINE (per non farla inghiottire da/in
#                 altri chunk), ma NON attaccata ad alcuna coltura.
#
# Le altre trasversali "per categoria" o "regola generale senza coltura" (RAME, FIORITURA,
# DISERBO ARBOREE/ERBACEE, CIMICE, GELATE, AFLATOSSINE, CAVALLETTE) sono volutamente ESCLUSE
# dai report-coltura: andranno esposte come "Avvisi generali" UNA volta per bollettino (TODO).
CROSS_CUTTING_SECTIONS = {
    'DEROGHE AI DISCIPLINARI DI PRODUZIONE INTEGRATA': 'PER_VOCE',
    'REVOCA PRODOTTI FITOSANITARI': '',
}
# ==========================================


# ============= LOGGING ====================
_logger = None

def get_logger():
    """Ritorna il logger, inizializzandolo solo al primo uso."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger("bollettini_processor")
        _logger.setLevel(logging.INFO)
        if not _logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
            _logger.addHandler(handler)
    return _logger

# Alias per compatibilità con codice esistente
class _LoggerProxy:
    """Proxy per logger lazy."""
    def __getattr__(self, name):
        return getattr(get_logger(), name)

logger = _LoggerProxy()
# ==========================================


# ============= CACHE ======================
def load_cache() -> Dict:
    """Carica la cache dei bollettini già processati"""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Errore caricamento cache: {e}")
    return {'processed_files': [], 'version': 1}


def save_cache(cache: Dict):
    """Salva la cache su disco"""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache['last_updated'] = datetime.now().isoformat()
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def is_processed(cache: Dict, pdf_name: str) -> bool:
    """Verifica se un PDF è già stato processato"""
    return pdf_name in cache.get('processed_files', [])


def mark_processed(cache: Dict, pdf_name: str):
    """Marca un PDF come processato"""
    if 'processed_files' not in cache:
        cache['processed_files'] = []
    if pdf_name not in cache['processed_files']:
        cache['processed_files'].append(pdf_name)
# ==========================================


# ============= PDF TO MARKDOWN ============

# Converter Docling con OCR DISATTIVATO (lazy init, riusato tra conversioni).
#
# OCR rimosso dopo verifica empirica (8 bollettini ER + Campania, giugno 2026):
# do_ocr=True vs do_ocr=False producono output IDENTICO (>=99.9%) su questi PDF, che
# sono digitali (testo nativo); l'OCR aggiungeva solo latenza (+40-65% di tempo).
# Le immagini presenti sono solo loghi decorativi, ignorati come <!-- image -->.
# Se in futuro dovesse arrivare un bollettino SCANSIONATO (senza testo nativo),
# riabilitare l'OCR rimettendo do_ocr=True qui sotto.
_converter = None


def _get_converter() -> DocumentConverter:
    """Ritorna il DocumentConverter (OCR off), creandolo solo al primo uso."""
    global _converter
    if _converter is None:
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.base_models import InputFormat

        pipeline_options = PdfPipelineOptions(do_ocr=False)
        _converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
    return _converter


def convert_pdf_to_markdown(pdf_path: Path) -> str | None:
    """Converte un PDF in Markdown usando Docling (in memoria, OCR off)."""
    try:
        logger.info("  Conversione PDF -> Markdown...")
        result = _get_converter().convert(str(pdf_path))
        return result.document.export_to_markdown()
    except Exception as e:
        logger.error(f"  ✗ Errore conversione: {e}")
        return None
# ==========================================


# ============= CHUNKING ===================
def extract_metadata_from_filename(filename: str) -> Dict:
    """
    Estrae metadata dal nome del file.

    Supporta due formati:
    - Emilia-Romagna: "Bollettino 30 del 1° ottobre 2025 di Bologna e Ferrara.pdf"
    - Campania: "Campania_{area}_{DD-MM-YYYY}.pdf"
    """
    metadata = {
        "numero_bollettino": None,
        "data": None,
        "province": [],
        "tipo_documento": "bollettino",
        "regione": None,
    }

    # === Formato Campania: Campania_{area}_{DD-MM-YYYY}.pdf ===
    campania_match = re.match(
        r"Campania_([^_]+)_(\d{2})-(\d{2})-(\d{4})(?:\.pdf)?$",
        filename, re.IGNORECASE
    )
    if campania_match:
        area = campania_match.group(1)
        dd = campania_match.group(2)
        mm = campania_match.group(3)
        yyyy = campania_match.group(4)
        metadata["regione"] = "campania"
        metadata["province"] = [area]
        metadata["data"] = f"{yyyy}-{mm}-{dd}"
        return metadata

    # === Formato Emilia-Romagna (originale) ===
    metadata["regione"] = "emilia_romagna"

    # Pattern per numero bollettino
    numero_match = re.search(r"Bollettino\s+(\d+)", filename, re.IGNORECASE)
    if numero_match:
        metadata["numero_bollettino"] = int(numero_match.group(1))

    # Pattern per data
    mesi = {
        'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
        'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
        'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
    }

    # Formato: "1 ottobre 2025" o "1° ottobre 2025"
    data_match = re.search(
        r"(\d{1,2})[°º]?\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})",
        filename, re.IGNORECASE
    )
    if data_match:
        giorno = int(data_match.group(1))
        mese = mesi[data_match.group(2).lower()]
        anno = int(data_match.group(3))
        metadata["data"] = f"{anno}-{mese:02d}-{giorno:02d}"

    # Formato: "30-09-2025"
    if not metadata["data"]:
        data_match2 = re.search(r"(\d{2})-(\d{2})-(\d{4})", filename)
        if data_match2:
            metadata["data"] = f"{data_match2.group(3)}-{data_match2.group(2)}-{data_match2.group(1)}"

    # Pattern per province (supporta sia con che senza estensione .pdf/.md)
    province_match = re.search(r"di\s+(.+?)(?:\.(?:md|pdf))?$", filename, re.IGNORECASE)
    if province_match:
        province_str = province_match.group(1)
        province_list = re.split(r',|\se\s', province_str)
        metadata["province"] = [p.strip() for p in province_list if p.strip()]
    else:
        # Formato: "2025 Modena" o "2025 Reggio Emilia" (senza "di")
        province_match_no_di = re.search(r"\d{4}\s+(.+?)(?:\.(?:md|pdf))?$", filename, re.IGNORECASE)
        if province_match_no_di:
            province_str = province_match_no_di.group(1).strip()
            province_str = re.sub(r'^(del|di|da)\s+', '', province_str, flags=re.IGNORECASE)
            province_list = re.split(r',|\se\s', province_str)
            metadata["province"] = [p.strip() for p in province_list if p.strip()]

    # Documento normativo
    if "lotta" in filename.lower() or "determinazione" in filename.lower():
        metadata["tipo_documento"] = "normativa"

    return metadata


def preprocess_normativa_markdown(md_text: str) -> str:
    """
    Pre-processa il markdown dei documenti normativi per estrarre
    sezioni importanti (es. sanzioni) che altrimenti verrebbero perse.
    """
    # Cerca il paragrafo delle sanzioni e crea una sezione esplicita
    sanzione_pattern = re.compile(
        r"(L'inosservanza delle prescrizioni.*?sanzione amministrativa pecuniaria.*?n\.\s*\d+\.)",
        re.DOTALL | re.IGNORECASE
    )

    match = sanzione_pattern.search(md_text)
    if match:
        sanzione_text = match.group(1)
        # Inserisci un titolo di sezione prima delle sanzioni
        md_text = md_text.replace(
            sanzione_text,
            f"\n## SANZIONI\n\n{sanzione_text}\n"
        )

    return md_text


def preprocess_campania_markdown(md_text: str) -> str:
    """
    Pre-processa markdown dei bollettini Campania per segmentare correttamente
    le sezioni coltura.

    Approccio a due passate:
    1. PASSATA 1 - Trova i confini delle sezioni coltura usando due marker:
       a) Tabelle di monitoraggio (contengono "Stadio" - ogni coltura ne ha una)
       b) Header/testo con nomi coltura (## COLTURA: X, COLTURA X, etc.)
    2. PASSATA 2 - Per ogni confine trovato, determina il nome della coltura
       dal contesto circostante e inserisce un header ## NOMECOLTURA normalizzato.

    Ogni sezione coltura in un bollettino Campania segue questo pattern:
      [COLTURA header/marker]  <- variabile, inconsistente
      [Tabella monitoraggio]   <- SEMPRE presente (N°, Comune, Varietà, Stadio)
      [CONSIGLI DI DIFESA]     <- contenuto difesa fitosanitaria
      ...contenuto fino alla prossima coltura...
    """
    lines = md_text.splitlines()

    # Nomi colture conosciute (uppercase). Aggiungi qui se nuove colture appaiono.
    CROP_NAMES = {
        'PESCO', 'OLIVO', 'VITE', 'NOCCIOLO', 'ACTINIDIA', 'MELO',
        'CASTAGNO', 'CILIEGIO', 'SUSINO', 'AGRUMI', 'POMODORO',
        'PERO', 'ALBICOCCO', 'KAKI', 'NOCE',
        'CIPOLLA', 'FRAGOLA', 'PATATA',
    }

    # Varieta' note -> coltura (per identificazione da tabella dati)
    VARIETA_TO_CROP = {
        'hayward': 'ACTINIDIA', 'soreli': 'ACTINIDIA',
        'annurca': 'MELO', 'golden': 'MELO', 'fuji': 'MELO', 'gala': 'MELO',
        'red delicious': 'MELO',
        # NOTA: 'Lady Alice' rimossa - ambigua (mela rossa O patata).
        # Nel bollettino NA e' patata: lasciamo che il riconoscimento via
        # patogeno univoco (Tignola della patata, Alternaria Solani) attribuisca.
        'aglianico': 'VITE', 'falanghina': 'VITE', 'fiano': 'VITE',
        'greco': 'VITE', 'piedirosso': 'VITE', 'coda di volpe': 'VITE',
        'tonda di giffoni': 'NOCCIOLO', 'san giovanni': 'NOCCIOLO',
        'mortarella': 'NOCCIOLO', 'camponica': 'NOCCIOLO',
        'napoletana': 'CASTAGNO', 'bouche de betizac': 'CASTAGNO',
        'durone': 'CILIEGIO', 'ferrovia': 'CILIEGIO',
        'rotondella': 'OLIVO', 'carpellese': 'OLIVO', 'sessana': 'OLIVO',
        'frantoio': 'OLIVO', 'leccino': 'OLIVO', 'olivella': 'OLIVO',
        'tonda': 'OLIVO',  # Tonda senza "di Giffoni" = Olivo in contesto olivicolo
        'olivicola': 'OLIVO',
        # Fragola: Redsayra e' la fragola tipica di Giugliano (NA)
        'redsayra': 'FRAGOLA',
        'sabrosa': 'FRAGOLA', 'albion': 'FRAGOLA', 'monterey': 'FRAGOLA',
        'candonga': 'FRAGOLA',
    }

    # Patogeni / fitofagi univoci -> coltura. Usati come ultimo fallback per
    # identificare colture senza header esplicito e senza varieta' nota
    # (es. PATATA in bollettino NA: solo "Tignola della patata", "Phytophthora
    # infestans", "Alternaria Solani" identificano la coltura).
    # SOLO marker UNIVOCI (non condivisi tra colture).
    PATOGENO_TO_CROP = {
        'tignola della patata': 'PATATA',
        'phthorimacea operculella': 'PATATA',
        'alternaria solani': 'PATATA',
        'rizottoniosi della patata': 'PATATA',
        'rhizoctonia solani': 'PATATA',
        # Pomodoro
        'tuta absoluta': 'POMODORO',
        # Cipolla
        'mosca dei bulbi': 'CIPOLLA',
        'tripidi della cipolla': 'CIPOLLA',
        'thrips tabaci': 'CIPOLLA',
        # Fragola
        'antracnosi della fragola': 'FRAGOLA',
        'oidio della fragola': 'FRAGOLA',
        'phytoseiulus persimilis': 'FRAGOLA',  # predatore tipico fragola
        'orius laevigatus': 'FRAGOLA',  # predatore tripidi in fragola
        # Olivo
        'mosca dell\'olivo': 'OLIVO',
        'bactrocera oleae': 'OLIVO',
        'occhio di pavone': 'OLIVO',
        # Castagno
        'cinipide galligeno': 'CASTAGNO',
        'dryocosmus kuriphilus': 'CASTAGNO',
        # Nocciolo
        'eriofide del nocciolo': 'NOCCIOLO',
        'phytocoptella avellanae': 'NOCCIOLO',
        # Vite
        'flavescenza dorata': 'VITE',
        'scaphoideus titanus': 'VITE',
        'tignoletta della vite': 'VITE',
        # Pesco
        'bolla del pesco': 'PESCO',
        'taphrina deformans': 'PESCO',
        'cydia molesta': 'PESCO',
        'anarsia lineatella': 'PESCO',
        # Melo
        'ticchiolatura del melo': 'MELO',
        'venturia inaequalis': 'MELO',
        # Pero
        'psilla del pero': 'PERO',
        'cacopsylla pyri': 'PERO',
        # Noce (univoci: separano la sezione noce dall'albicocco che la precede in CE)
        'juglandis': 'NOCE',
        'mosca delle noci': 'NOCE',
        'rhagoletis completa': 'NOCE',
        'gnomonia leptostyla': 'NOCE',
    }

    def _leading_crop(text_upper: str):
        """Nome-coltura INIZIALE in una stringa uppercase (es. 'AGRUMI (ARANCIO E
        MANDARINO)' -> 'AGRUMI'), o None. Gestisce i suffissi descrittivi tra parentesi
        che il match esatto perderebbe."""
        for _name in CROP_NAMES:
            if (text_upper == _name
                    or text_upper.startswith(_name + ' ')
                    or text_upper.startswith(_name + '(')):
                return _name
        return None

    # === PRE-PASS A: "## COLTURA" standalone + nome coltura su riga successiva ===
    # Es. (CE 22/04/2026):
    #   ## COLTURA
    #   <vuoto>
    #   PESCO
    # Rimpiazziamo con "## COLTURA PESCO" su un'unica riga affinche' i
    # marker successivi lo riconoscano. Il nome puo' avere un suffisso descrittivo
    # (es. "AGRUMI (Arancio e mandarino)"): in tal caso teniamo solo il nome-coltura.
    _new_lines = []
    _i = 0
    while _i < len(lines):
        line = lines[_i]
        if line.strip().upper() == '## COLTURA':
            # Guarda le prossime 5 righe non vuote per un nome coltura
            for _j in range(_i + 1, min(_i + 6, len(lines))):
                _candidate = lines[_j].strip().upper().rstrip(':').strip()
                if not _candidate:
                    continue
                # Considera valido se è una coltura conosciuta o forma
                # "COLTURA <NAME>" / "<NAME>" plain (anche con suffisso tra parentesi)
                _candidate = re.sub(r'^COLTURA[\s:]*', '', _candidate).strip()
                _crop = _leading_crop(_candidate)
                if _crop:
                    # Sostituisci la riga "## COLTURA" con "## COLTURA <NAME>"
                    _new_lines.append(f"## COLTURA {_crop.title()}")
                    # Salta righe vuote e la riga contenente il nome
                    _i = _j + 1
                    break
                # Se non e' una coltura ma e' un nome lungo, smetti di cercare
                if len(_candidate) > 0 and not _candidate.isspace():
                    _new_lines.append(line)
                    _i += 1
                    break
            else:
                _new_lines.append(line)
                _i += 1
        else:
            _new_lines.append(line)
            _i += 1
    lines = _new_lines

    def _is_monitoring_table_header(line: str) -> bool:
        """Riga header di tabella con 'Stadio' = inizio sezione monitoraggio."""
        return '|' in line and 'stadio' in line.lower()

    def _is_table_separator(line: str) -> bool:
        return line.strip().startswith('|') and set(line.strip().replace('|', '').strip()) <= {'-', ' ', ':'}

    def _extract_crop_from_context(line_idx: int) -> str | None:
        """
        Determina il nome coltura guardando il contesto attorno a una tabella di monitoraggio.
        Cerca nelle 8 righe precedenti e nella tabella stessa.
        """
        # 1. Cerca nelle righe precedenti (header o testo)
        for j in range(line_idx - 1, max(line_idx - 8, -1), -1):
            prev = lines[j].strip()
            if not prev or prev.startswith('<!--') or _is_table_separator(prev):
                continue
            if prev.startswith('|'):
                # Potrebbe essere un'altra tabella - ferma
                break

            prev_upper = prev.lstrip('#').strip().upper()

            # "COLTURA: PESCO" o "COLTURA:ACTINIDIA"
            m = re.match(r'COLTURA\s*:?\s*(\w+)', prev_upper)
            if m and m.group(1) in CROP_NAMES:
                return m.group(1)

            # "## PESCO" o "PESCO" standalone
            for name in CROP_NAMES:
                if prev_upper == name:
                    return name
                # "CONSIGLI DI DIFESA FITOSANITARIA INTEGRATA DEL CASTAGNO"
                # Ma NON "Ticchiolatura del melo" o "Bolla del pesco" (nomi malattie)
                if (f'DEL {name}' in prev_upper or f"DELL'{name}" in prev_upper):
                    if 'DIFESA' in prev_upper or 'CONSIGLI' in prev_upper:
                        return name

            # Se troviamo "COLTURA" generico, continuiamo a cercare
            if prev_upper == 'COLTURA':
                continue
            # Se troviamo un altro ## header non-coltura, ferma
            if prev.startswith('##'):
                break

        # 2. Cerca nella tabella stessa (righe dati con varietà)
        for j in range(line_idx, min(line_idx + 5, len(lines))):
            row = lines[j].strip()
            if not row.startswith('|'):
                break
            # Controlla nella riga per nomi coltura espliciti
            row_upper = row.upper()
            for name in CROP_NAMES:
                # Match esatto in cella tabella: "| VITE |" o "| COLTURA | VITE |"
                if re.search(rf'\|\s*{name}\s*\|', row_upper):
                    return name

            # Controlla per varietà conosciute
            row_lower = row.lower()
            for varieta, crop in VARIETA_TO_CROP.items():
                if varieta in row_lower:
                    return crop

        return None

    # === PASSATA 1: Trova tutti i confini di sezione coltura ===
    # Un confine e' definito da: tabella monitoraggio (con Stadio) O header coltura esplicito
    boundaries = []  # lista di (line_idx, crop_name)

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Tabella di monitoraggio = confine affidabile
        if _is_monitoring_table_header(stripped):
            crop = _extract_crop_from_context(i)
            if crop:
                boundaries.append((i, crop))
            continue

        # Header espliciti come confine secondario (per colture senza tabella)
        stripped_upper = stripped.lstrip('#').strip().upper()

        # "## COLTURA: PESCO"
        m = re.match(r'^#+\s+COLTURA\s*:\s*(\w+)', stripped, re.IGNORECASE)
        if m and m.group(1).upper() in CROP_NAMES:
            boundaries.append((i, m.group(1).upper()))
            continue

        # "## COLTURA NOCCIOLO" (con spazio dopo COLTURA)
        m = re.match(r'^#+\s+COLTURA\s+(\w+)', stripped, re.IGNORECASE)
        if m and m.group(1).upper() in CROP_NAMES:
            boundaries.append((i, m.group(1).upper()))
            continue

        # "## COLTURAOlivo" (no-spazio, OCR sporco). Test ogni nome coltura.
        m = re.match(r'^#+\s+COLTURA(\w+)', stripped, re.IGNORECASE)
        if m:
            candidate = m.group(1).upper()
            if candidate in CROP_NAMES:
                boundaries.append((i, candidate))
                continue
            # Fuzzy: "OlivO" o suffisso parziale
            for name in CROP_NAMES:
                if candidate.startswith(name) or candidate == name:
                    boundaries.append((i, name))
                    break
            else:
                continue
            continue

        # "## NOMECOLTURA" da solo (es. "## SUSINO", "## CASTAGNO")
        if stripped.startswith('##'):
            content = stripped.lstrip('#').strip().upper()
            if content in CROP_NAMES:
                boundaries.append((i, content))
                continue

    # === PASSATA 1b: Identifica colture da patogeni univoci nelle aree orfane ===
    # Cerca tabelle di monitoraggio NON attribuite in PASSATA 1 e prova a inferire
    # la coltura dai patogeni citati nei ~80 righe successivi.
    # Es. PATATA in NA: header e varietà sconosciute, ma "Tignola della patata",
    # "Alternaria Solani", "Phytophthora infestans" identificano univocamente PATATA.
    attributed_lines = {idx for idx, _ in boundaries}

    for i, line in enumerate(lines):
        if not _is_monitoring_table_header(line.strip()):
            continue
        if i in attributed_lines:
            continue
        # Tabella orfana: scansiona contenuto seguente per patogeni univoci
        scan_end = min(i + 80, len(lines))
        next_boundary = next(
            (b_i for b_i, _ in boundaries if b_i > i),
            scan_end,
        )
        scan_end = min(scan_end, next_boundary)
        scan_text = '\n'.join(lines[i:scan_end]).lower()

        # Conta hits per coltura
        hits_by_crop = {}
        for patogeno, crop in PATOGENO_TO_CROP.items():
            if patogeno in scan_text:
                hits_by_crop[crop] = hits_by_crop.get(crop, 0) + 1

        if hits_by_crop:
            # Prendi la coltura con piu' hits
            best_crop = max(hits_by_crop.items(), key=lambda x: x[1])[0]
            boundaries.append((i, best_crop))
            attributed_lines.add(i)

    # === PASSATA 2: Ricostruisci il markdown con header normalizzati ===
    # Strategia: per ogni boundary, inseriamo un header "## NOMECOLTURA" e
    # rimuoviamo le righe "COLTURA"/"## COLTURA" ridondanti che precedono la tabella.

    # Calcola la posizione di inserimento per ogni boundary:
    # L'header va PRIMA della tabella, ma DOPO il preambolo del bollettino
    # Cerchiamo il punto piu' in alto dove inizia il blocco coltura
    insert_points = {}  # line_idx -> crop_name (dove inserire l'header)
    lines_to_remove = set()  # righe da rimuovere (COLTURA generici)

    for bound_idx, crop_name in boundaries:
        # Risali dalle righe sopra la tabella per trovare il punto di inserimento
        # e rimuovi le righe "COLTURA" ridondanti
        insert_at = bound_idx
        for j in range(bound_idx - 1, max(bound_idx - 8, -1), -1):
            prev = lines[j].strip()
            if not prev or prev.startswith('<!--'):
                continue
            prev_clean = prev.lstrip('#').strip().upper()

            # Righe da rimuovere: "COLTURA", "## COLTURA", "## COLTURA: X", "## X"
            if prev_clean == 'COLTURA':
                lines_to_remove.add(j)
                insert_at = j
            elif re.match(r'COLTURA\s*:?\s*\w*', prev_clean) and any(
                n in prev_clean for n in CROP_NAMES | {'COLTURA'}
            ):
                lines_to_remove.add(j)
                insert_at = j
            elif prev_clean in CROP_NAMES:
                lines_to_remove.add(j)
                insert_at = j
            elif prev.startswith('## Stato fitosanitario'):
                # Non rimuovere, ma l'header coltura va subito dopo
                insert_at = j + 1
                break
            else:
                break

        insert_points[insert_at] = crop_name

    # Ricostruisci l'output: inseriamo gli header coltura normalizzati e
    # rimuoviamo le righe COLTURA ridondanti. NON declassiamo gli ## interni
    # alle zone coltura: slice_markdown_by_coltura usa COLTURA_HEADER_TO_ID
    # per filtrare i boundaries, quindi gli ## sub-sezione (Difesa, Diserbo,
    # Consigli, ecc.) non aprono nuovi chunks anche se rimangono "##".
    result = []
    for i, line in enumerate(lines):
        if i in insert_points:
            result.append(f"\n## {insert_points[i]}\n")
        if i in lines_to_remove:
            continue
        result.append(line)

    return "\n".join(result)


def extract_sections_from_markdown(md_text: str) -> List[Tuple[str, str]]:
    """
    Estrae sezioni dal markdown basandosi sui titoli.

    Ritorna una lista ordinata di tuple (title, content). Sezioni con titolo
    duplicato (es. piu' "## Difesa") vengono mantenute separate, preservando
    l'ordine di apparizione.
    """
    sections: List[Tuple[str, str]] = []
    current_section = "Introduzione"
    buffer = []

    lines = md_text.splitlines()

    for line in lines:
        if SECTION_PATTERN.match(line.strip()):
            if buffer:
                content = "\n".join(buffer).strip()
                sections.append((current_section, content))
                buffer = []
            current_section = line.strip().lstrip('#').strip()
        else:
            buffer.append(line)

    if buffer:
        content = "\n".join(buffer).strip()
        sections.append((current_section, content))

    return sections


def _normalize_header(title: str) -> str:
    """Normalizza un titolo header per match contro COLTURA_HEADER_TO_ID."""
    t = title.upper().strip()
    # Rimuovi colon finali e spazi
    t = t.rstrip(':').strip()
    # Collassa spazi multipli
    t = re.sub(r'\s+', ' ', t)
    return t


def assign_parent_coltura(
    sections: List[Tuple[str, str]],
) -> List[Tuple[str, str, Optional[str]]]:
    """
    Walk delle sezioni in ordine, assegna parent_coltura a ognuna.

    Regola:
    - Se il titolo matcha un coltura header (COLTURA_HEADER_TO_ID) ->
      parent corrente = coltura ID, anche per la sezione stessa.
    - Altrimenti la sezione eredita il parent corrente.

    Le sotto-sezioni con titolo generico (## Difesa, ## Diserbo, ## Tecniche
    agronomiche, ## Vincoli, ## Post-emergenza, ## Fase fenologica: ...) che
    seguono un header coltura vengono cosi' attribuite alla coltura giusta.

    Le sezioni prima del primo coltura header hanno parent=None.
    """
    result = []
    current = None
    for title, content in sections:
        norm = _normalize_header(title)
        new_parent = COLTURA_HEADER_TO_ID.get(norm)
        if new_parent is not None:
            current = new_parent
        result.append((title, content, current))
    return result


def is_protected_section(title: str) -> bool:
    """Verifica se una sezione è protetta (non deve essere unita)"""
    title_upper = title.upper().strip()
    for protected in PROTECTED_SECTIONS:
        if protected in title_upper or title_upper in protected:
            return True
    return False


def merge_small_sections(
    sections: List[Tuple[str, str, Optional[str]]],
) -> List[Dict]:
    """
    Unisce sezioni consecutive piccole in chunks più grandi.
    Sezioni sotto MERGE_THRESHOLD vengono unite alla successiva.
    Le sezioni PROTETTE (colture, cimice, deroghe) NON vengono mai unite.

    Mantiene parent_coltura del chunk principale (la prima sezione del merge).
    Non unisce mai sezioni con parent_coltura diverso (no cross-contamination).
    """
    section_list = sections
    merged = []

    i = 0
    while i < len(section_list):
        title, content, parent = section_list[i]
        word_count = len(content.split()) if content else 0

        # Se è una sezione protetta, NON unirla mai
        if is_protected_section(title):
            merged.append({
                "title": title,
                "content": content,
                "original_titles": [title],
                "parent_coltura": parent,
            })
            i += 1
            continue

        # Se la sezione è piccola, prova a unirla con le successive (non protette)
        if word_count < MERGE_THRESHOLD and i < len(section_list) - 1:
            merged_titles = [title]
            merged_content = [content] if content else []

            # Continua a unire finché il totale è sotto MERGE_THRESHOLD
            j = i + 1
            while j < len(section_list):
                next_title, next_content, next_parent = section_list[j]

                # NON unire con sezioni protette
                if is_protected_section(next_title):
                    break

                # NON unire sezioni con parent_coltura diverso (anti-contaminazione)
                if next_parent != parent:
                    break

                next_words = len(next_content.split()) if next_content else 0
                total_words = sum(len(c.split()) for c in merged_content) + next_words

                # Unisci se il totale rimane gestibile (max 500 parole)
                if total_words < 500:
                    merged_titles.append(next_title)
                    if next_content:
                        merged_content.append(f"### {next_title}\n{next_content}")
                    j += 1

                    # Se abbiamo raggiunto abbastanza parole, fermati
                    if total_words >= MERGE_THRESHOLD:
                        break
                else:
                    break

            # Crea il chunk unito
            combined_title = merged_titles[0]  # Usa il primo titolo come principale
            if len(merged_titles) > 1:
                combined_title = f"{merged_titles[0]} (+{len(merged_titles)-1} sezioni)"

            merged.append({
                "title": combined_title,
                "content": "\n\n".join(merged_content),
                "original_titles": merged_titles,
                "parent_coltura": parent,
            })
            i = j
        else:
            # Sezione abbastanza grande, tienila così
            merged.append({
                "title": title,
                "content": content,
                "original_titles": [title],
                "parent_coltura": parent,
            })
            i += 1

    return merged


def trim_pi_section(md_text: str) -> str:
    """
    Per i bollettini ER: ritorna solo la parte 'Produzione Integrata',
    troncando al primo header che inizia con 'BOLLETTINO DI PRODUZIONE BIOLOGICA'.

    Se il marker non e' presente, ritorna il testo invariato.
    """
    match = PI_END_MARKER.search(md_text)
    if match:
        return md_text[:match.start()].rstrip()
    return md_text


# ============= PROMOZIONE HEADER-COLTURA NON RICONOSCIUTI (ER) =============
# Su alcuni PDF ER Docling NON emette il nome della coltura come header markdown: la coltura
# compare come paragrafo di testo semplice. Siccome slice_markdown_by_coltura riconosce solo gli
# header '## ', quel blocco non apre un nuovo chunk e viene ASSORBITO nel chunk della coltura
# precedente (osservato: il chunk CILIEGIO di "Bollettino 12 del 28 aprile 2026 di Modena" da 22k
# caratteri inghiotte KAKI, MELO, OLIVO e PERO; in Modena n.13 KAKI inghiotte MELO e PERO
# inghiotte PESCO; in Reggio Emilia n.12 MELO inghiotte OLIVO). Effetto: report vuoti per le
# colture assorbite e report contaminati per quella che le assorbe.
#
# Qui quelle righe vengono promosse a '## NOME'. Regole deterministiche e volutamente STRETTE,
# tarate sui markdown ER reali in test/**/raw*.md:
#   1. la riga, normalizzata, e' esattamente una chiave di COLTURA_HEADER_TO_ID;
#   2. e' TUTTA MAIUSCOLA, come gli header-coltura dei bollettini ER. Vincolo indispensabile:
#      nei bollettini invernali esistono elenchi in Title Case ("Melo", "Pesco e Nettarine")
#      che sono VOCI di una lista ("Melo" + ": bottoni rosa"), non sezioni-coltura;
#   3. e' un paragrafo a se' stante (riga vuota, o inizio/fine documento, prima e dopo);
#   4. la prima riga non vuota successiva non inizia con ':' (ulteriore protezione contro le
#      voci "NOME: valore" che Docling spezza su due righe);
#   5. non siamo dentro una sezione trasversale (DEROGHE/REVOCA), che elenca nomi di coltura.
# Righe di tabella ('|') e artefatti Docling ('<!-- ... -->') sono sempre esclusi.
def promote_plaintext_coltura_headers(md_text: str) -> str:
    """Promuove a '## NOME' le righe che sono un nome-coltura non emesso come header. Vedi sopra."""
    lines = md_text.splitlines()
    promoted: List[str] = []
    in_cross_cutting = False

    def _next_non_empty(idx: int) -> Optional[str]:
        for l in lines[idx + 1:]:
            if l.strip():
                return l.strip()
        return None

    for i, line in enumerate(lines):
        s_line = line.strip()

        if s_line.startswith('#'):
            norm_hdr = _normalize_header(s_line.lstrip('#').strip())
            in_cross_cutting = any(
                norm_hdr == key or norm_hdr.startswith(key) for key in CROSS_CUTTING_SECTIONS
            )
            continue

        if not s_line or '|' in s_line or '<!--' in s_line:
            continue
        if in_cross_cutting:                                   # regola 5
            continue
        if s_line != s_line.upper():                           # regola 2
            continue
        if _normalize_header(s_line) not in COLTURA_HEADER_TO_ID:   # regola 1
            continue
        prev_blank = i == 0 or not lines[i - 1].strip()         # regola 3
        next_blank = i + 1 >= len(lines) or not lines[i + 1].strip()
        if not (prev_blank and next_blank):
            continue
        nxt = _next_non_empty(i)                               # regola 4
        if nxt and nxt.startswith(':'):
            continue

        lines[i] = f'## {s_line}'
        promoted.append(s_line)

    if promoted:
        logger.info(f"  header-coltura promossi (non emessi da Docling): {promoted}")
    return '\n'.join(lines)
# ==========================================


def _merge_consecutive_same_coltura(chunks: List[Dict]) -> List[Dict]:
    """
    Unisce chunks consecutivi con lo stesso coltura_id in un unico chunk.

    Necessario per Campania dove preprocess_campania_markdown puo' inserire
    header duplicati ravvicinati (es. 2x ## NOCCIOLO per le 2 righe header
    della tabella di monitoraggio). Anche per ER risolve casi tipo "VITE iniziale
    + VITE reale" che diventano un unico chunk piu' pulito.

    Mantiene il primo title (di solito il piu' rappresentativo).
    """
    if not chunks:
        return chunks

    merged = [chunks[0]]
    for ch in chunks[1:]:
        last = merged[-1]
        if ch['coltura_id'] and ch['coltura_id'] == last['coltura_id']:
            last['content'] = last['content'].rstrip() + '\n\n' + ch['content'].lstrip()
        else:
            merged.append(ch)
    return merged


def slice_markdown_by_coltura(md_text: str) -> List[Dict]:
    """
    Strategia di chunking per ER: una coltura = un chunk.

    Algoritmo:
    1. Identifica tutti gli header `## ` che sono:
       - Coltura header (in COLTURA_HEADER_TO_ID) -> avvia un chunk
       - Group divider (COLTURE ARBOREE/ERBACEE/ORTICOLE/DISERBO ARBOREE/...) ->
         chiude la coltura corrente ma non avvia un nuovo chunk
    2. Per ogni coltura header, raccoglie tutto il contenuto (incluse sotto-sezioni
       come ## Difesa, ## Diserbo, ## Tecniche agronomiche) fino al prossimo
       confine (altra coltura, divisore, fine documento).
    3. Ritorna list di dict {title, content, coltura_id}.

    Le sezioni di preambolo (prima della prima coltura) e quelle non riconducibili
    a una coltura specifica vengono ignorate per ora.
    """
    lines = md_text.splitlines()

    # Trova tutti i confini (## headers che sono coltura o divider)
    boundaries = []  # (line_idx, kind, coltura_id_or_none)
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.startswith('## ') or s.startswith('###'):
            continue
        title = s.lstrip('#').strip()
        norm = _normalize_header(title)

        if norm in COLTURA_HEADER_TO_ID:
            boundaries.append((i, 'coltura', COLTURA_HEADER_TO_ID[norm]))
        elif norm in GROUP_DIVIDERS:
            boundaries.append((i, 'divider', None))

    # Aggiungi sentinella di fine documento
    boundaries.append((len(lines), 'end', None))

    # Genera un chunk per ogni coltura, contenuto da line_idx a prossimo confine
    chunks = []
    for idx, (line_idx, kind, cid) in enumerate(boundaries):
        if kind != 'coltura':
            continue
        end_idx = boundaries[idx + 1][0]
        # Titolo originale dell'header (prima riga)
        title = lines[line_idx].strip().lstrip('#').strip()
        content = '\n'.join(lines[line_idx:end_idx]).strip()
        chunks.append({
            'title': title,
            'content': content,
            'coltura_id': cid,
        })

    return chunks


def slice_cross_cutting_sections(md_text: str) -> List[Dict]:
    """
    Estrae le sezioni TRASVERSALI (non blocchi-coltura) che valgono per piu' colture
    (lotta obbligatoria, deroghe, revoche, rame, diserbo, cimice, ecc.).

    Una sezione trasversale va dal suo header al prossimo CONFINE (header coltura,
    divisore di gruppo, altra sezione trasversale, o "PARTE SPECIFICA"): cosi' le sue
    eventuali sotto-sezioni (## Tempistica, ## Vigneto, ...) vengono assorbite e non la
    troncano. Ritorna lista di dict {title, content, applies_to}.
    """
    lines = md_text.splitlines()

    def _cc_key(title: str):
        t = _normalize_header(title)
        for key in CROSS_CUTTING_SECTIONS:
            if t == key or t.startswith(key):
                return key
        return None

    boundaries = []  # (line_idx, cc_key_or_None, title)
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.startswith('## ') or s.startswith('###'):
            continue
        title = s.lstrip('#').strip()
        norm = _normalize_header(title)
        cc = _cc_key(title)
        is_boundary = (
            norm in COLTURA_HEADER_TO_ID
            or norm in GROUP_DIVIDERS
            or cc is not None
            or norm.startswith('PARTE SPECIFICA')
        )
        if is_boundary:
            boundaries.append((i, cc, title))

    boundaries.append((len(lines), None, None))

    sections = []
    for idx in range(len(boundaries) - 1):
        line_idx, cc, title = boundaries[idx]
        if cc is None:
            continue
        end_idx = boundaries[idx + 1][0]
        content = '\n'.join(lines[line_idx:end_idx]).strip()
        if len(content.split()) < 8:  # scarta header senza contenuto reale
            continue
        sections.append({
            'title': title,
            'content': content,
            'applies_to': CROSS_CUTTING_SECTIONS[cc],
        })
    return sections


def create_chunks_from_markdown(md_text: str, doc_name: str) -> List[Dict]:
    """
    Crea chunks dal testo markdown.

    Strategia per regione:
    - Emilia-Romagna: slice-by-coltura (un chunk per coltura, include tutte le
      sotto-sezioni, niente filtri). Trim della parte BIO.
    - Campania: chunking sezione-based con merge (logica originale).
    - Documenti normativi: preprocessing dedicato + chunking standard.
    """
    file_metadata = extract_metadata_from_filename(doc_name)
    regione = file_metadata.get("regione") or "emilia_romagna"

    # Pre-processa documenti normativi per estrarre sezioni importanti
    if file_metadata["tipo_documento"] == "normativa":
        md_text = preprocess_normativa_markdown(md_text)

    # === STRATEGIA ER: slice-by-coltura ===
    if regione == "emilia_romagna":
        # Trim della parte di Produzione Biologica (per ora ignorata)
        md_text = trim_pi_section(md_text)
        # Recupera le colture il cui nome Docling non ha emesso come header markdown:
        # senza questo passaggio verrebbero assorbite nel chunk della coltura precedente.
        md_text = promote_plaintext_coltura_headers(md_text)

        coltura_chunks = slice_markdown_by_coltura(md_text)
        coltura_chunks = _merge_consecutive_same_coltura(coltura_chunks)

        chunks = []
        for idx, ch in enumerate(coltura_chunks):
            chunks.append({
                "chunk_id": f"{doc_name}_chunk_{idx}",
                "content": ch["content"],
                "metadata": {
                    "doc_name": doc_name,
                    "section_title": ch["title"],
                    "numero_bollettino": file_metadata["numero_bollettino"],
                    "data": file_metadata["data"],
                    "province": ",".join(file_metadata["province"]) if file_metadata["province"] else "",
                    "tipo_documento": file_metadata["tipo_documento"],
                    "regione": regione,
                    "parent_coltura": ch["coltura_id"] or "",
                },
            })

        # Sezioni trasversali (modello a due assi): attaccate alle colture pertinenti
        # via `applies_to` (lista coltura_id o "ALL"). Vedi docs/redesign_er.md.
        for j, cc in enumerate(slice_cross_cutting_sections(md_text)):
            applies = cc["applies_to"]
            applies_str = ",".join(applies) if isinstance(applies, list) else applies
            chunks.append({
                "chunk_id": f"{doc_name}_cc_{j}",
                "content": cc["content"],
                "metadata": {
                    "doc_name": doc_name,
                    "section_title": cc["title"],
                    "numero_bollettino": file_metadata["numero_bollettino"],
                    "data": file_metadata["data"],
                    "province": ",".join(file_metadata["province"]) if file_metadata["province"] else "",
                    "tipo_documento": file_metadata["tipo_documento"],
                    "regione": regione,
                    "parent_coltura": "",
                    "applies_to": applies_str,
                },
            })
        return chunks

    # === STRATEGIA CAMPANIA: stesso slice-by-coltura di ER, ma con preprocess
    # che normalizza gli header inconsistenti del bollettino provinciale
    # ("COLTURA X", "## COLTURA: X", tabelle senza header esplicito, varieta'
    # come marker, ecc.). Post-merge per collassare header duplicati.
    if regione == "campania":
        md_text = preprocess_campania_markdown(md_text)

        coltura_chunks = slice_markdown_by_coltura(md_text)
        coltura_chunks = _merge_consecutive_same_coltura(coltura_chunks)

        chunks = []
        for idx, ch in enumerate(coltura_chunks):
            chunks.append({
                "chunk_id": f"{doc_name}_chunk_{idx}",
                "content": ch["content"],
                "metadata": {
                    "doc_name": doc_name,
                    "section_title": ch["title"],
                    "numero_bollettino": file_metadata["numero_bollettino"],
                    "data": file_metadata["data"],
                    "province": ",".join(file_metadata["province"]) if file_metadata["province"] else "",
                    "tipo_documento": file_metadata["tipo_documento"],
                    "regione": regione,
                    "parent_coltura": ch["coltura_id"] or "",
                },
            })
        return chunks

    # === FALLBACK: chunking sezione-based con merge (documenti normativi o altro) ===
    sections = extract_sections_from_markdown(md_text)
    sections_with_parent = assign_parent_coltura(sections)
    merged_sections = merge_small_sections(sections_with_parent)

    chunks = []
    chunk_index = 0

    for section in merged_sections:
        content = section["content"]
        is_protected = is_protected_section(section["title"])
        if not content:
            continue
        if len(content.split()) < MIN_CHUNK_WORDS and not is_protected:
            continue

        chunks.append({
            "chunk_id": f"{doc_name}_chunk_{chunk_index}",
            "content": content,
            "metadata": {
                "doc_name": doc_name,
                "section_title": section["title"],
                "numero_bollettino": file_metadata["numero_bollettino"],
                "data": file_metadata["data"],
                "province": ",".join(file_metadata["province"]) if file_metadata["province"] else "",
                "tipo_documento": file_metadata["tipo_documento"],
                "regione": regione,
                "parent_coltura": section.get("parent_coltura") or "",
            },
        })
        chunk_index += 1

    return chunks
# ==========================================


# ============= MAIN PROCESSING ============
def process_single_pdf(pdf_path: Path, store) -> bool:
    """
    Processa un singolo PDF: conversione, chunking, scrittura nel ChunkStore.
    (Niente embedding/vettori: il retrieval e' per match esatto su metadati.)
    """
    try:
        # Step 1: PDF -> Markdown (in memoria, OCR off - vedi nota su _get_converter)
        md_text = convert_pdf_to_markdown(pdf_path)
        if not md_text:
            return False

        # Step 2: Chunking
        doc_name = pdf_path.stem
        chunks = create_chunks_from_markdown(md_text, doc_name)

        if not chunks:
            logger.warning(f"  Nessun chunk creato")
            return False

        # Step 3: Scrittura nel ChunkStore (sovrascrive eventuali chunk dello stesso doc).
        store.delete_doc(doc_name)
        store.upsert_chunks(chunks)
        logger.info(f"  ✓ {len(chunks)} chunks -> ChunkStore")

        return True

    except Exception as e:
        logger.error(f"  ✗ Errore processing {pdf_path.name}: {e}")
        return False


class BollettiniProcessor:
    """
    Classe per processare i bollettini fitosanitari.
    Gestisce conversione PDF, chunking, embeddings e upload a ChromaDB.
    """

    def __init__(self, input_dir: Path = None):
        """
        Args:
            input_dir: Directory con i PDF da processare.
                       Se None, usa INPUT_DIR di default (Emilia-Romagna).
        """
        self.input_dir = input_dir or INPUT_DIR
        self.store = None  # Lazy loading (ChunkStore SQLite)
        self.cache = load_cache()

    def _init_models(self):
        """Inizializza lo store (lazy)."""
        if self.store is None:
            logger.info(f"Apertura ChunkStore: {CHUNKSTORE_DB}")
            self.store = ChunkStore(CHUNKSTORE_DB)
    
    def process_files(self, pdf_paths: List[Path], skip_cache: bool = False) -> tuple[int, int]:
        """
        Processa una lista specifica di file PDF.
        
        Args:
            pdf_paths: Lista di Path ai PDF da processare
            skip_cache: Se True, processa anche file già in cache
            
        Returns:
            tuple: (success_count, total_count)
        """
        self._init_models()
        
        # Filtra già processati (se non skip_cache)
        if not skip_cache:
            pdf_paths = [p for p in pdf_paths if not is_processed(self.cache, p.name)]
        
        if not pdf_paths:
            logger.info("Nessun nuovo file da processare")
            return 0, 0
        
        success_count = 0
        for i, pdf_path in enumerate(pdf_paths, 1):
            logger.info(f"[{i}/{len(pdf_paths)}] {pdf_path.name}")
            
            if process_single_pdf(pdf_path, self.store):
                mark_processed(self.cache, pdf_path.name)
                success_count += 1
        
        save_cache(self.cache)
        return success_count, len(pdf_paths)
    
    def process_all(self, only_latest: bool = True) -> tuple[bool, dict]:
        """
        Processa tutti i bollettini PDF non ancora processati.
        
        Args:
            only_latest: Se True, processa solo l'ultimo bollettino per ogni provincia
            
        Returns:
            tuple: (has_processed: bool, stats: dict)
        """
        logger.info("=" * 60)
        logger.info("PROCESSING BOLLETTINI")
        logger.info("=" * 60)
        
        self._init_models()
        logger.info(f"Store: {CHUNKSTORE_DB}")

        # Trova tutti i PDF (supporta anche sottodirectory per anno)
        pdf_files = list(self.input_dir.glob("*.pdf"))
        pdf_files.extend(self.input_dir.glob("*/*.pdf"))
        
        if not pdf_files:
            logger.warning(f"Nessun PDF trovato in {self.input_dir}")
            return False, {'processed': 0, 'total': 0, 'cached': 0}
        
        # Filtra già processati
        to_process = [p for p in pdf_files if not is_processed(self.cache, p.name)]
        cached_count = len(pdf_files) - len(to_process)
        
        if cached_count > 0:
            logger.info(f"In cache: {cached_count} bollettini")
        
        if not to_process:
            logger.info(f"⚡ Tutti i {len(pdf_files)} bollettini sono già processati")
            return False, {'processed': 0, 'total': len(pdf_files), 'cached': cached_count}
        
        # Filtra solo ultimo per provincia se richiesto
        if only_latest and len(to_process) > 1:
            to_process = self._filter_latest_per_province(to_process)
        
        logger.info(f"Totale da processare: {len(to_process)} PDF")
        
        # Processa
        start_time = datetime.now()
        success_count, total = self.process_files(to_process, skip_cache=True)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Report
        logger.info("=" * 60)
        logger.info(f"COMPLETATO in {duration:.1f}s | Processati: {success_count}/{total}")
        logger.info(f"Totale in cache: {len(self.cache.get('processed_files', []))}")
        
        store_count = self.store.count() if self.store else 0
        logger.info(f"  ChunkStore: {store_count} chunks totali")
        logger.info("=" * 60)

        return success_count > 0, {
            'processed': success_count,
            'total': total,
            'cached': cached_count,
            'duration_seconds': duration,
            'store_chunks': store_count,
        }
    
    def _filter_latest_per_province(self, pdf_paths: List[Path]) -> List[Path]:
        """Filtra mantenendo solo l'ultimo bollettino per ogni provincia.
        I documenti 'normativa' (es. testo lotta flavescenza) sono sempre inclusi."""
        bollettini = []
        exclusive_docs = []  # documenti normativa: sempre inclusi

        for pdf_path in pdf_paths:
            meta = extract_metadata_from_filename(pdf_path.name)
            if meta.get('tipo_documento') == 'normativa':
                exclusive_docs.append(pdf_path)
            else:
                bollettini.append(pdf_path)

        if bollettini:
            province_latest: Dict[str, tuple[Path, str]] = {}
            
            for pdf_path in bollettini:
                metadata = extract_metadata_from_filename(pdf_path.name)
                pub_date = metadata.get("data") or "0000-00-00"
                provinces = metadata.get("province", [])
                
                if not provinces:
                    provinces = ["unknown"]
                
                for provincia in provinces:
                    provincia_key = provincia.lower().strip()
                    if provincia_key not in province_latest:
                        province_latest[provincia_key] = (pdf_path, pub_date)
                    else:
                        _, existing_date = province_latest[provincia_key]
                        if pub_date > existing_date:
                            province_latest[provincia_key] = (pdf_path, pub_date)
            
            bollettini = list({path for path, _ in province_latest.values()})
            logger.info(f"Modalità 'solo ultimo per provincia': {len(province_latest)} province -> {len(bollettini)} bollettini")
        
        if exclusive_docs:
            logger.info(f"Documenti esclusivi: {len(exclusive_docs)}")
        
        return bollettini + exclusive_docs


# ============= FUNZIONE LEGACY =============
def process_all_bollettini(only_latest: bool = True) -> tuple[bool, dict]:
    """
    Funzione legacy per retrocompatibilità.
    Usa BollettiniProcessor internamente.
    """
    processor = BollettiniProcessor()
    return processor.process_all(only_latest=only_latest)


def main():
    """Entry point per esecuzione da linea di comando."""
    processor = BollettiniProcessor()
    has_processed, stats = processor.process_all(only_latest=True)
    
    # Exit code: 0 se processato qualcosa, 1 altrimenti
    exit(0 if has_processed else 1)


if __name__ == "__main__":
    main()
