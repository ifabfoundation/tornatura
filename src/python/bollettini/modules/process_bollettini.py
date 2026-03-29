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
from typing import Dict, List
from datetime import datetime

# Suppress noisy loggers and warnings before imports
os.environ["RAPIDOCR_LOGGING"] = "ERROR"
os.environ["ONNXRUNTIME_LOGGING_LEVEL"] = "ERROR"

logging.getLogger("docling").setLevel(logging.ERROR)
logging.getLogger("docling.pipeline").setLevel(logging.ERROR)
logging.getLogger("rapidocr").setLevel(logging.ERROR)
logging.getLogger("RapidOCR").setLevel(logging.ERROR)
logging.getLogger("onnxruntime").setLevel(logging.ERROR)
logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from docling.document_converter import DocumentConverter
from sentence_transformers import SentenceTransformer
import chromadb

from bollettini import paths

# ============= CONFIGURAZIONE =============
BASE_DIR = Path(__file__).parent.parent
INPUT_DIR = paths.DATA_DIR  / "1_collections" / "bollettini"
CHROMADB_DIR = paths.DATA_DIR  / "chromadb"
CACHE_FILE = paths.DATA_DIR / "processing_cache.json"

# ============= CONFIGURAZIONE MALATTIE =============
# Ogni malattia ha la sua collezione ChromaDB
# - shared_sources: tipi di documento che vanno in TUTTE le collezioni
# - exclusive_docs: documenti che vanno SOLO in questa collezione
DISEASE_CONFIG = {
    "cimice_asiatica": {
        "collection_name": "cimice_asiatica",
        "description": "Cimice Asiatica (Halyomorpha halys)",
        "shared_sources": ["bollettino"],  # I bollettini vanno in tutte le collezioni
        "exclusive_docs": []  # Nessun documento esclusivo per ora
    },
    "flavescenza_dorata": {
        "collection_name": "flavescenza_dorata",
        "description": "Flavescenza Dorata della vite",
        "shared_sources": ["bollettino"],
        "exclusive_docs": ["testo_lotta_flavescenza"]  # Va SOLO qui
    }
}

# Parametri chunking
MIN_CHUNK_WORDS = 50           # Minimo parole per chunk valido
MERGE_THRESHOLD = 100          # Sezioni sotto questa soglia vengono unite alla successiva
SECTION_PATTERN = re.compile(r"^#{1,3}\s+.+")

# Sezioni da NON unire (colture e sezioni importanti) - mantienile intere
PROTECTED_SECTIONS = {
    # Colture
    'MELO', 'PERO', 'PESCO', 'SUSINO', 'CILIEGIO', 'ALBICOCCO',
    'ACTINIDIA', 'KAKI', 'VITE', 'NOCE', 'NOCCIOLO', 'OLIVO',
    'FRUMENTO', 'ORZO', 'COLZA', 'MAIS', 'SOIA',
    'POMODORO', 'PATATA', 'CIPOLLA', 'CAROTA',
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

# Modello embedding
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
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
def convert_pdf_to_markdown(pdf_path: Path) -> str | None:
    """Converte un PDF in Markdown usando Docling (in memoria)"""
    try:
        logger.info(f"  Conversione PDF -> Markdown...")
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        doc = result.document
        return doc.export_to_markdown()
    except Exception as e:
        logger.error(f"  ✗ Errore conversione: {e}")
        return None
# ==========================================


# ============= CHUNKING ===================
def extract_metadata_from_filename(filename: str) -> Dict:
    """Estrae metadata dal nome del file"""
    metadata = {
        "numero_bollettino": None,
        "data": None,
        "province": [],
        "tipo_documento": "bollettino"
    }

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


def extract_sections_from_markdown(md_text: str) -> Dict[str, str]:
    """
    Estrae sezioni dal markdown basandosi sui titoli.
    Gestisce sezioni duplicate unendo il contenuto.
    """
    sections = {}
    current_section = "Introduzione"
    buffer = []

    lines = md_text.splitlines()

    for line in lines:
        if SECTION_PATTERN.match(line.strip()):
            if buffer:
                content = "\n".join(buffer).strip()
                # Se la sezione esiste già, unisci il contenuto
                if current_section in sections:
                    sections[current_section] += "\n\n" + content
                else:
                    sections[current_section] = content
                buffer = []
            current_section = line.strip().lstrip('#').strip()
        else:
            buffer.append(line)

    if buffer:
        content = "\n".join(buffer).strip()
        if current_section in sections:
            sections[current_section] += "\n\n" + content
        else:
            sections[current_section] = content

    return sections


def is_protected_section(title: str) -> bool:
    """Verifica se una sezione è protetta (non deve essere unita)"""
    title_upper = title.upper().strip()
    for protected in PROTECTED_SECTIONS:
        if protected in title_upper or title_upper in protected:
            return True
    return False


def merge_small_sections(sections: Dict[str, str]) -> List[Dict]:
    """
    Unisce sezioni consecutive piccole in chunks più grandi.
    Sezioni sotto MERGE_THRESHOLD vengono unite alla successiva.
    Le sezioni PROTETTE (colture, cimice, deroghe) NON vengono mai unite.
    """
    section_list = list(sections.items())
    merged = []

    i = 0
    while i < len(section_list):
        title, content = section_list[i]
        word_count = len(content.split()) if content else 0

        # Se è una sezione protetta, NON unirla mai
        if is_protected_section(title):
            merged.append({
                "title": title,
                "content": content,
                "original_titles": [title]
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
                next_title, next_content = section_list[j]

                # NON unire con sezioni protette
                if is_protected_section(next_title):
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
                "original_titles": merged_titles
            })
            i = j
        else:
            # Sezione abbastanza grande, tienila così
            merged.append({
                "title": title,
                "content": content,
                "original_titles": [title]
            })
            i += 1

    return merged


def create_chunks_from_markdown(md_text: str, doc_name: str) -> List[Dict]:
    """Crea chunks dal testo markdown con merging intelligente"""
    file_metadata = extract_metadata_from_filename(doc_name)

    # Pre-processa documenti normativi per estrarre sezioni importanti
    if file_metadata["tipo_documento"] == "normativa":
        md_text = preprocess_normativa_markdown(md_text)

    sections = extract_sections_from_markdown(md_text)

    # Unisci sezioni piccole
    merged_sections = merge_small_sections(sections)

    chunks = []
    chunk_index = 0

    for section in merged_sections:
        content = section["content"]
        # Sezioni protette vengono mantenute anche se piccole (es. SANZIONI)
        is_protected = is_protected_section(section["title"])
        if not content:
            continue
        if len(content.split()) < MIN_CHUNK_WORDS and not is_protected:
            continue

        chunk_id = f"{doc_name}_chunk_{chunk_index}"

        chunk = {
            "chunk_id": chunk_id,
            "content": content,
            "metadata": {
                "doc_name": doc_name,
                "section_title": section["title"],
                "numero_bollettino": file_metadata["numero_bollettino"],
                "data": file_metadata["data"],
                "province": ",".join(file_metadata["province"]) if file_metadata["province"] else "",
                "tipo_documento": file_metadata["tipo_documento"]
            }
        }

        chunks.append(chunk)
        chunk_index += 1

    return chunks
# ==========================================


# ============= EMBEDDINGS & CHROMADB ======
def generate_embeddings(chunks: List[Dict], model: SentenceTransformer) -> List[Dict]:
    """Genera embeddings per i chunks (batch per efficienza)"""
    contents = [chunk["content"] for chunk in chunks]
    vectors = model.encode(contents, show_progress_bar=False, batch_size=32)
    for chunk, vector in zip(chunks, vectors):
        chunk["vector"] = vector.tolist()
    return chunks


def get_or_create_collection(client: chromadb.PersistentClient, collection_name: str, description: str = ""):
    """Ottiene o crea una collection ChromaDB"""
    try:
        return client.get_collection(collection_name)
    except Exception:
        return client.create_collection(
            name=collection_name,
            metadata={"description": description or f"Collection {collection_name}"}
        )


def get_target_collections(doc_name: str, tipo_documento: str) -> List[str]:
    """
    Determina in quali collezioni deve andare un documento.

    Regole:
    1. Se il documento è in 'exclusive_docs' di una malattia → solo quella collezione
    2. Se il tipo_documento è in 'shared_sources' → tutte le collezioni che lo includono
    """
    target_collections = []

    # Prima controlla se è un documento esclusivo
    for disease_id, config in DISEASE_CONFIG.items():
        for exclusive_doc in config.get('exclusive_docs', []):
            if exclusive_doc.lower() in doc_name.lower():
                # Documento esclusivo: va SOLO in questa collezione
                return [config['collection_name']]

    # Altrimenti, routing basato su tipo_documento
    for disease_id, config in DISEASE_CONFIG.items():
        if tipo_documento in config.get('shared_sources', []):
            target_collections.append(config['collection_name'])

    return target_collections


def upload_chunks_to_chromadb(chunks: List[Dict], collection):
    """Carica chunks su ChromaDB"""
    ids = []
    embeddings = []
    metadatas = []
    documents = []

    for chunk in chunks:
        ids.append(chunk["chunk_id"])
        embeddings.append(chunk["vector"])

        clean_meta = {}
        for key, value in chunk["metadata"].items():
            if value is None:
                clean_meta[key] = ""
            elif isinstance(value, (int, float, bool)):
                clean_meta[key] = value
            else:
                clean_meta[key] = str(value)

        metadatas.append(clean_meta)
        documents.append(chunk["content"])

    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents
    )


# ==========================================


# ============= MAIN PROCESSING ============
def process_single_pdf(pdf_path: Path, model: SentenceTransformer, collections: Dict[str, any]) -> bool:
    """
    Processa un singolo PDF: conversione, chunking, embedding, upload a collezioni appropriate.

    Args:
        collections: Dict con nome_collezione -> oggetto collection ChromaDB
    """
    try:
        # Step 1: PDF -> Markdown (in memoria)
        md_text = convert_pdf_to_markdown(pdf_path)
        if not md_text:
            return False

        # Step 2: Chunking
        doc_name = pdf_path.stem
        chunks = create_chunks_from_markdown(md_text, doc_name)

        if not chunks:
            logger.warning(f"  Nessun chunk creato")
            return False

        # Step 3: Embeddings (una volta sola, riutilizzati per tutte le collezioni)
        chunks_with_embeddings = generate_embeddings(chunks, model)

        # Step 4: Determina collezioni target
        tipo_documento = chunks[0]['metadata'].get('tipo_documento', 'bollettino')
        target_collection_names = get_target_collections(doc_name, tipo_documento)

        if not target_collection_names:
            logger.warning(f"  Nessuna collezione target per {doc_name}")
            return False

        # Step 5: Upload a tutte le collezioni target
        for coll_name in target_collection_names:
            if coll_name in collections:
                upload_chunks_to_chromadb(chunks_with_embeddings, collections[coll_name])

        logger.info(f"  ✓ {len(chunks)} chunks -> {', '.join(target_collection_names)}")

        return True

    except Exception as e:
        logger.error(f"  ✗ Errore processing {pdf_path.name}: {e}")
        return False


class BollettiniProcessor:
    """
    Classe per processare i bollettini fitosanitari.
    Gestisce conversione PDF, chunking, embeddings e upload a ChromaDB.
    """
    
    def __init__(self):
        self.model = None  # Lazy loading
        self.client = None
        self.collections = None
        self.cache = load_cache()
    
    def _init_models(self):
        """Inizializza modelli e connessioni (lazy)."""
        if self.model is None:
            logger.info("Caricamento modello embedding...")
            self.model = SentenceTransformer(MODEL_NAME)
        
        if self.client is None:
            CHROMADB_DIR.mkdir(parents=True, exist_ok=True)
            logger.info("Inizializzazione ChromaDB...")
            self.client = chromadb.PersistentClient(path=str(CHROMADB_DIR))
            
            self.collections = {}
            for disease_id, config in DISEASE_CONFIG.items():
                coll_name = config['collection_name']
                self.collections[coll_name] = get_or_create_collection(
                    self.client, coll_name, config.get('description', '')
                )
                logger.info(f"  ✓ Collezione: {coll_name}")
    
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
            
            if process_single_pdf(pdf_path, self.model, self.collections):
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
        
        # Mostra configurazione
        logger.info(f"Collezioni configurate: {len(DISEASE_CONFIG)}")
        for disease_id, config in DISEASE_CONFIG.items():
            logger.info(f"  - {config['collection_name']}: {config['description']}")
        
        # Trova tutti i PDF (nelle sottocartelle anno)
        pdf_files = list(INPUT_DIR.glob("*/*.pdf"))
        
        if not pdf_files:
            logger.warning(f"Nessun PDF trovato in {INPUT_DIR}")
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
        
        collection_stats = {}
        if self.collections:
            for coll_name, coll in self.collections.items():
                count = coll.count()
                collection_stats[coll_name] = count
                logger.info(f"  {coll_name}: {count} chunks")
        
        logger.info("=" * 60)
        
        return success_count > 0, {
            'processed': success_count,
            'total': total,
            'cached': cached_count,
            'duration_seconds': duration,
            'collections': collection_stats
        }
    
    def _filter_latest_per_province(self, pdf_paths: List[Path]) -> List[Path]:
        """Filtra mantenendo solo l'ultimo bollettino per ogni provincia."""
        bollettini = []
        exclusive_docs = []
        
        all_exclusive = []
        for config in DISEASE_CONFIG.values():
            all_exclusive.extend(config.get('exclusive_docs', []))
        
        for pdf_path in pdf_paths:
            is_exclusive = any(exc.lower() in pdf_path.stem.lower() for exc in all_exclusive)
            if is_exclusive:
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
