"""
Test STANDALONE del pipeline completo per la cimice asiatica.
Processa il bollettino, indicizza in ChromaDB locale, e testa il retrieval.

Questo script è autocontenuto e non modifica i dati di produzione.
"""

from pathlib import Path
import re
import json
import logging
import warnings
import os
import shutil
from typing import Dict, List
from datetime import datetime

# Suppress noisy loggers
os.environ["RAPIDOCR_LOGGING"] = "ERROR"
os.environ["ONNXRUNTIME_LOGGING_LEVEL"] = "ERROR"
logging.getLogger("docling").setLevel(logging.ERROR)
logging.getLogger("rapidocr").setLevel(logging.ERROR)
logging.getLogger("onnxruntime").setLevel(logging.ERROR)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
warnings.filterwarnings("ignore")

from docling.document_converter import DocumentConverter
from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

# ============= CONFIGURAZIONE =============
BASE_DIR = Path(__file__).parent.parent.parent
INPUT_DIR = BASE_DIR / "data" / "1_collections" / "bollettini" / "2025"
OUTPUT_DIR = Path(__file__).parent / "output"
TEST_CHROMADB_DIR = Path(__file__).parent / "chromadb_test"  # DB locale per test

# PDF da testare
TEST_PDF = "Bollettino 30 del 1° ottobre 2025 di Bologna e Ferrara.pdf"

# Modelli
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

# Parametri chunking
MIN_CHUNK_WORDS = 50
MERGE_THRESHOLD = 100
SECTION_PATTERN = re.compile(r"^#{1,3}\s+.+")

# Sezioni protette (non unire)
PROTECTED_SECTIONS = {
    'MELO', 'PERO', 'PESCO', 'SUSINO', 'CILIEGIO', 'ALBICOCCO',
    'ACTINIDIA', 'KAKI', 'VITE', 'NOCE', 'NOCCIOLO', 'OLIVO',
    'FRUMENTO', 'ORZO', 'COLZA', 'MAIS', 'SOIA',
    'POMODORO', 'PATATA', 'CIPOLLA', 'CAROTA',
    'INFORMAZIONI RIGUARDANTI LA CIMICE ASIATICA',
    'DEROGHE AI DISCIPLINARI DI PRODUZIONE INTEGRATA',
    'LOTTA OBBLIGATORIA CONTRO FLAVESCENZA DORATA'
}

# Parametri retrieval
TOP_K_RETRIEVAL = 10
TOP_K_RERANK = 5
# ==========================================


# ============= LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)
# ==========================================


# ============= QUERIES CIMICE =============
# Le query con "section_filter" cercano solo in sezioni specifiche
QUERIES = {
    "Q1_situazione": {
        "name": "Situazione generale cimice",
        "query": """Situazione cimice asiatica Halyomorpha halys: catture trappole monitoraggio,
fase biologica popolazione, adulti forme giovanili, spostamenti svernamento, BIG Monitoraggio Emilia-Romagna""",
        "keywords": ["cimice", "halyomorpha", "catture", "monitoraggio", "svernamento", "BIG", "settimana"],
        "section_filter": None  # Cerca ovunque
    },
    "Q2_trattamenti_melo": {
        "name": "Trattamenti cimice su MELO",
        "query": """MELO cimice asiatica Halyomorpha halys trattamenti prodotti fitosanitari
piretro tau-fluvalinate deltametrina etofenprox lambdacialotrina interventi""",
        "keywords": ["MELO", "cimice", "piretro", "tau-fluvalinate", "deltametrina", "etofenprox", "lambdacialotrina"],
        "section_filter": "MELO"  # Cerca SOLO nella sezione MELO
    },
    "Q3_trattamenti_actinidia": {
        "name": "Trattamenti cimice su ACTINIDIA",
        "query": """ACTINIDIA kiwi cimice asiatica Halyomorpha halys trattamenti prodotti
etofenprox deroga ATLAS KARATE lambdacialotrina""",
        "keywords": ["ACTINIDIA", "cimice", "etofenprox", "deroga", "ATLAS", "KARATE", "lambdacialotrina"],
        "section_filter": "ACTINIDIA"  # Cerca SOLO nella sezione ACTINIDIA
    },
    "Q4_deroghe": {
        "name": "Deroghe eccezionali cimice",
        "query": """Deroghe eccezionali cimice asiatica Halyomorpha halys ATLAS KARATE ZEON
lambdacialotrina uso eccezionale validità colture""",
        "keywords": ["deroga", "cimice", "ATLAS", "KARATE", "lambdacialotrina", "eccezionale", "validità"],
        "section_filter": None  # Cerca ovunque (deroghe possono essere in più sezioni)
    },
    "Q5_previsioni_hhal": {
        "name": "Previsioni modello HHAL-S",
        "query": """Modello HHAL-S previsioni cimice asiatica prossime settimane
forme giovanili generazione monitoraggio raccomandazioni""",
        "keywords": ["HHAL-S", "modello", "previsioni", "cimice", "forme giovanili", "generazione"],
        "section_filter": None  # Cerca ovunque
    }
}
# ==========================================


# ============= STEP 1: PDF TO MARKDOWN ============
def convert_pdf_to_markdown(pdf_path: Path) -> str | None:
    """Converte un PDF in Markdown usando Docling."""
    try:
        logger.info("  [1/4] Conversione PDF -> Markdown...")
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        return result.document.export_to_markdown()
    except Exception as e:
        logger.error(f"Errore conversione: {e}")
        return None


# ============= STEP 2: CHUNKING ============
def extract_metadata_from_filename(filename: str) -> Dict:
    """Estrae metadata dal nome file."""
    metadata = {
        "numero_bollettino": None,
        "data": None,
        "province": [],
        "tipo_documento": "bollettino"
    }

    numero_match = re.search(r"Bollettino\s+(\d+)", filename, re.IGNORECASE)
    if numero_match:
        metadata["numero_bollettino"] = int(numero_match.group(1))

    mesi = {
        'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
        'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
        'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
    }

    data_match = re.search(
        r"(\d{1,2})[°º]?\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})",
        filename, re.IGNORECASE
    )
    if data_match:
        giorno = int(data_match.group(1))
        mese = mesi[data_match.group(2).lower()]
        anno = int(data_match.group(3))
        metadata["data"] = f"{anno}-{mese:02d}-{giorno:02d}"

    province_match = re.search(r"di\s+(.+?)(?:\.(?:md|pdf))?$", filename, re.IGNORECASE)
    if province_match:
        province_str = province_match.group(1)
        province_list = re.split(r',|\se\s', province_str)
        metadata["province"] = [p.strip() for p in province_list if p.strip()]

    return metadata


def extract_sections_from_markdown(md_text: str) -> Dict[str, str]:
    """Estrae sezioni dal markdown, unendo duplicati."""
    sections = {}
    current_section = "Introduzione"
    buffer = []

    for line in md_text.splitlines():
        if SECTION_PATTERN.match(line.strip()):
            if buffer:
                content = "\n".join(buffer).strip()
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
    """Verifica se una sezione è protetta."""
    title_upper = title.upper().strip()
    for protected in PROTECTED_SECTIONS:
        if protected in title_upper or title_upper in protected:
            return True
    return False


def merge_small_sections(sections: Dict[str, str]) -> List[Dict]:
    """Unisce sezioni piccole, rispettando le sezioni protette."""
    section_list = list(sections.items())
    merged = []

    i = 0
    while i < len(section_list):
        title, content = section_list[i]
        word_count = len(content.split()) if content else 0

        if is_protected_section(title):
            merged.append({
                "title": title,
                "content": content,
                "original_titles": [title]
            })
            i += 1
            continue

        if word_count < MERGE_THRESHOLD and i < len(section_list) - 1:
            merged_titles = [title]
            merged_content = [content] if content else []

            j = i + 1
            while j < len(section_list):
                next_title, next_content = section_list[j]

                if is_protected_section(next_title):
                    break

                next_words = len(next_content.split()) if next_content else 0
                total_words = sum(len(c.split()) for c in merged_content) + next_words

                if total_words < 500:
                    merged_titles.append(next_title)
                    if next_content:
                        merged_content.append(f"### {next_title}\n{next_content}")
                    j += 1
                    if total_words >= MERGE_THRESHOLD:
                        break
                else:
                    break

            combined_title = merged_titles[0]
            if len(merged_titles) > 1:
                combined_title = f"{merged_titles[0]} (+{len(merged_titles)-1} sezioni)"

            merged.append({
                "title": combined_title,
                "content": "\n\n".join(merged_content),
                "original_titles": merged_titles
            })
            i = j
        else:
            merged.append({
                "title": title,
                "content": content,
                "original_titles": [title]
            })
            i += 1

    return merged


def create_chunks(md_text: str, doc_name: str) -> List[Dict]:
    """Crea chunks dal markdown."""
    file_metadata = extract_metadata_from_filename(doc_name)
    sections = extract_sections_from_markdown(md_text)
    merged_sections = merge_small_sections(sections)

    chunks = []
    for idx, section in enumerate(merged_sections):
        content = section["content"]
        if not content or len(content.split()) < MIN_CHUNK_WORDS:
            continue

        chunks.append({
            "chunk_id": f"{doc_name}_chunk_{idx}",
            "content": content,
            "metadata": {
                "doc_name": doc_name,
                "section_title": section["title"],
                "numero_bollettino": file_metadata["numero_bollettino"],
                "data": file_metadata["data"],
                "province": ",".join(file_metadata["province"]) if file_metadata["province"] else "",
                "tipo_documento": file_metadata["tipo_documento"]
            }
        })

    return chunks


# ============= STEP 3: CHROMADB ============
def setup_chromadb(chunks: List[Dict], embedding_model: SentenceTransformer) -> chromadb.Collection:
    """Crea un ChromaDB locale di test e indicizza i chunks."""
    logger.info("  [3/4] Indicizzazione in ChromaDB di test...")

    # Pulisci DB precedente
    if TEST_CHROMADB_DIR.exists():
        shutil.rmtree(TEST_CHROMADB_DIR)

    TEST_CHROMADB_DIR.mkdir(parents=True, exist_ok=True)

    # Crea client e collection
    client = chromadb.PersistentClient(path=str(TEST_CHROMADB_DIR))
    collection = client.create_collection(
        name="test_bollettini",
        metadata={"description": "Test cimice asiatica"}
    )

    # Genera embeddings
    contents = [c["content"] for c in chunks]
    embeddings = embedding_model.encode(contents, show_progress_bar=False, batch_size=32)

    # Prepara dati per ChromaDB
    ids = []
    metadatas = []
    documents = []

    for chunk, embedding in zip(chunks, embeddings):
        ids.append(chunk["chunk_id"])
        documents.append(chunk["content"])

        clean_meta = {}
        for k, v in chunk["metadata"].items():
            if v is None:
                clean_meta[k] = ""
            elif isinstance(v, (int, float, bool)):
                clean_meta[k] = v
            else:
                clean_meta[k] = str(v)
        metadatas.append(clean_meta)

    # Aggiungi a ChromaDB
    collection.add(
        ids=ids,
        embeddings=[e.tolist() for e in embeddings],
        metadatas=metadatas,
        documents=documents
    )

    logger.info(f"    Indicizzati {len(chunks)} chunks")
    return collection


# ============= STEP 4: RETRIEVAL & TEST ============
def retrieve_and_rerank(collection, embedding_model, reranker, query_text: str,
                        keywords: list, section_filter: str = None) -> List[Dict]:
    """Retrieval + Reranking con filtro opzionale per sezione."""
    enhanced_query = f"{query_text} {' '.join(keywords)}"
    query_embedding = embedding_model.encode(enhanced_query, show_progress_bar=False)

    query_args = {
        "query_embeddings": [query_embedding.tolist()],
        "n_results": TOP_K_RETRIEVAL,
        "include": ["documents", "metadatas", "distances"]
    }

    # Se c'è un filtro sezione, cerca solo in quella sezione
    if section_filter:
        query_args["where"] = {"section_title": section_filter}

    results = collection.query(**query_args)

    chunks = []
    for i in range(len(results['ids'][0])):
        chunks.append({
            "id": results['ids'][0][i],
            "content": results['documents'][0][i],
            "metadata": results['metadatas'][0][i],
            "distance": results['distances'][0][i]
        })

    # Reranking
    if chunks:
        pairs = [(query_text, c['content']) for c in chunks]
        scores = reranker.predict(pairs)
        for i, chunk in enumerate(chunks):
            chunk['rerank_score'] = float(scores[i])
        chunks = sorted(chunks, key=lambda x: x['rerank_score'], reverse=True)[:TOP_K_RERANK]

    return chunks


def generate_answer(query_text: str, chunks: list, openai_client: OpenAI) -> str:
    """Genera risposta con LLM."""
    context = ""
    for i, chunk in enumerate(chunks, 1):
        meta = chunk['metadata']
        context += f"\n--- FONTE {i}: {meta.get('section_title', 'N/A')} ---\n"
        context += chunk['content']
        context += "\n\n"

    system_prompt = """Sei un esperto fitosanitario. Estrai le informazioni richieste sulla Cimice Asiatica (Halyomorpha halys).

REGOLE:
1. Basati ESCLUSIVAMENTE sui documenti forniti.
2. Rispondi SOLO su Cimice Asiatica: ignora altre avversità.
3. Per ogni punto richiesto, riporta TUTTE le informazioni trovate.
4. Se non trovi informazioni, scrivi "Non indicato nel bollettino".
5. Cita la fonte (sezione) quando riporti informazioni."""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Contesto:\n{context}\n\nDomanda: {query_text}"}
        ],
        temperature=0
    )

    return response.choices[0].message.content


def test_queries(collection, embedding_model, reranker, openai_client) -> List[Dict]:
    """Testa tutte le query."""
    results = []

    for query_id, query_def in QUERIES.items():
        logger.info(f"\n{'─'*60}")
        logger.info(f"Query: {query_def['name']}")

        chunks = retrieve_and_rerank(
            collection, embedding_model, reranker,
            query_def['query'], query_def['keywords'],
            section_filter=query_def.get('section_filter')
        )

        logger.info(f"  Top chunks:")
        for i, c in enumerate(chunks[:3], 1):
            logger.info(f"    [{i}] {c['metadata'].get('section_title', 'N/A')[:40]} (score: {c['rerank_score']:.3f})")

        # Genera risposta
        answer = generate_answer(query_def['query'], chunks, openai_client)

        results.append({
            "query_id": query_id,
            "query_name": query_def['name'],
            "top_chunks": [
                {
                    "section": c['metadata'].get('section_title'),
                    "score": c['rerank_score']
                }
                for c in chunks
            ],
            "answer": answer
        })

        logger.info(f"  Risposta generata ({len(answer)} chars)")

    return results


# ============= MAIN ============
def main():
    load_dotenv()

    logger.info("=" * 70)
    logger.info("TEST PIPELINE CIMICE ASIATICA - STANDALONE")
    logger.info("=" * 70)

    pdf_path = INPUT_DIR / TEST_PDF
    if not pdf_path.exists():
        logger.error(f"File non trovato: {pdf_path}")
        return

    # Carica modelli
    logger.info("\nCaricamento modelli...")
    embedding_model = SentenceTransformer(MODEL_NAME)
    reranker = CrossEncoder(RERANKER_MODEL)
    openai_client = OpenAI()

    # STEP 1: PDF -> Markdown
    md_text = convert_pdf_to_markdown(pdf_path)
    if not md_text:
        return

    # STEP 2: Chunking
    logger.info("  [2/4] Creazione chunks...")
    doc_name = pdf_path.stem
    chunks = create_chunks(md_text, doc_name)
    logger.info(f"    Creati {len(chunks)} chunks")

    # Mostra chunks con cimice
    cimice_chunks = [c for c in chunks if 'cimice' in c['content'].lower()]
    logger.info(f"    Chunks con 'cimice': {len(cimice_chunks)}")
    for c in cimice_chunks:
        logger.info(f"      - {c['metadata']['section_title']}")

    # STEP 3: ChromaDB
    collection = setup_chromadb(chunks, embedding_model)

    # STEP 4: Test queries
    logger.info("  [4/4] Test retrieval queries...")
    results = test_queries(collection, embedding_model, reranker, openai_client)

    # Salva risultati
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "pipeline_test_results.json"

    output = {
        "timestamp": datetime.now().isoformat(),
        "pdf": TEST_PDF,
        "chunks_total": len(chunks),
        "chunks_with_cimice": len(cimice_chunks),
        "queries": results
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Salva anche markdown leggibile
    md_output = OUTPUT_DIR / "pipeline_test_results.md"
    with open(md_output, "w", encoding="utf-8") as f:
        f.write(f"# Test Pipeline Cimice Asiatica\n\n")
        f.write(f"**PDF:** {TEST_PDF}\n")
        f.write(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write(f"**Chunks totali:** {len(chunks)} | **Con cimice:** {len(cimice_chunks)}\n\n")
        f.write("---\n\n")

        for r in results:
            f.write(f"## {r['query_name']}\n\n")
            f.write(f"**Top chunks:**\n")
            for c in r['top_chunks'][:3]:
                f.write(f"- {c['section']} (score: {c['score']:.3f})\n")
            f.write(f"\n**Risposta:**\n\n{r['answer']}\n\n")
            f.write("---\n\n")

    logger.info(f"\n{'='*70}")
    logger.info(f"Test completato!")
    logger.info(f"  JSON: {output_file}")
    logger.info(f"  MD:   {md_output}")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()
