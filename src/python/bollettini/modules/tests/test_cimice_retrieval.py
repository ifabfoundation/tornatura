"""
Test script per testare il retrieval delle informazioni sulla cimice asiatica.
Usa ChromaDB locale per testare le query prima di applicarle allo script ufficiale.
"""

from pathlib import Path
import json
from datetime import datetime
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from openai import OpenAI
from dotenv import load_dotenv
import logging

# ============= CONFIGURAZIONE =============
BASE_DIR = Path(__file__).parent.parent.parent
CHROMADB_DIR = BASE_DIR / "data" / "chromadb"
OUTPUT_DIR = Path(__file__).parent / "output"
COLLECTION_NAME = "bollettini"

# Modelli
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

# Parametri retrieval
TOP_K_RETRIEVAL = 10   # Chunks da recuperare inizialmente
TOP_K_RERANK = 5       # Chunks da tenere dopo reranking
# ==========================================


# ============= LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)
# ==========================================


# ============= QUERIES DI TEST =============
# Query specifiche per estrarre informazioni sulla cimice

QUERIES = {
    "Q1_situazione": {
        "name": "Situazione generale cimice",
        "query": """Estrai le informazioni sulla situazione della cimice asiatica (Halyomorpha halys):
- Periodo di riferimento (settimana, date)
- Andamento catture (in calo, in aumento, vicine al picco)
- Fase biologica (adulti, forme giovanili, ovideposizioni)
- Spostamenti verso siti di svernamento
- Link o riferimenti al BIG Monitoraggio Emilia-Romagna""",
        "keywords": ["cimice", "halyomorpha", "catture", "monitoraggio", "svernamento", "BIG"]
    },

    "Q2_trattamenti_melo": {
        "name": "Trattamenti cimice su MELO",
        "query": """Quali sono i trattamenti consigliati contro la cimice asiatica (Halyomorpha halys) sulla coltura del MELO?
Elenca tutti i prodotti autorizzati con dosi e numero massimo interventi.""",
        "keywords": ["cimice", "melo", "piretro", "tau-fluvalinate", "deltametrina", "etofenprox", "lambdacialotrina"]
    },

    "Q3_trattamenti_actinidia": {
        "name": "Trattamenti cimice su ACTINIDIA",
        "query": """Quali sono i trattamenti consigliati contro la cimice asiatica (Halyomorpha halys) sulla coltura dell'ACTINIDIA (kiwi)?
Includi anche eventuali deroghe eccezionali con date di validità.""",
        "keywords": ["cimice", "actinidia", "kiwi", "etofenprox", "deroga", "ATLAS", "KARATE", "lambdacialotrina"]
    },

    "Q4_deroghe": {
        "name": "Deroghe eccezionali cimice",
        "query": """Quali deroghe eccezionali sono state concesse per il controllo della cimice asiatica (Halyomorpha halys)?
Per ogni deroga indica: prodotto, principio attivo, colture, date di validità.""",
        "keywords": ["deroga", "cimice", "halyomorpha", "ATLAS", "KARATE ZEON", "lambdacialotrina", "eccezionale"]
    },

    "Q5_previsioni_hhal": {
        "name": "Previsioni modello HHAL-S",
        "query": """Cosa prevede il modello HHAL-S per la cimice asiatica nelle prossime settimane?
Quali sono le raccomandazioni per il monitoraggio?""",
        "keywords": ["HHAL-S", "modello", "previsioni", "cimice", "monitoraggio", "forme giovanili"]
    }
}
# ==============================================


def retrieve_chunks(collection, embedding_model, query_text: str, keywords: list,
                   doc_name: str = None, top_k: int = TOP_K_RETRIEVAL) -> list:
    """
    Retrieval dei chunks rilevanti per la query.
    """
    # Arricchisci query con keywords
    enhanced_query = f"{query_text} {' '.join(keywords)}"

    # Genera embedding
    query_embedding = embedding_model.encode(enhanced_query, show_progress_bar=False)

    # Query ChromaDB
    query_args = {
        "query_embeddings": [query_embedding.tolist()],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"]
    }

    # Filtra per documento specifico se richiesto
    if doc_name:
        query_args["where"] = {"doc_name": doc_name}

    results = collection.query(**query_args)

    chunks = []
    for i in range(len(results['ids'][0])):
        chunk = {
            "id": results['ids'][0][i],
            "content": results['documents'][0][i],
            "metadata": results['metadatas'][0][i],
            "distance": results['distances'][0][i]
        }
        chunks.append(chunk)

    return chunks


def rerank_chunks(query_text: str, chunks: list, reranker: CrossEncoder, top_k: int = TOP_K_RERANK) -> list:
    """
    Reranking dei chunks usando cross-encoder.
    """
    if not chunks:
        return []

    pairs = [(query_text, chunk['content']) for chunk in chunks]
    scores = reranker.predict(pairs)

    for i, chunk in enumerate(chunks):
        chunk['rerank_score'] = float(scores[i])

    chunks_sorted = sorted(chunks, key=lambda x: x['rerank_score'], reverse=True)
    return chunks_sorted[:top_k]


def test_single_query(query_id: str, query_def: dict, collection, embedding_model, reranker, doc_name: str = None):
    """
    Testa una singola query e mostra i risultati.
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"QUERY: {query_def['name']}")
    logger.info(f"{'='*70}")
    logger.info(f"Query text: {query_def['query'][:100]}...")

    # Retrieval
    chunks = retrieve_chunks(
        collection=collection,
        embedding_model=embedding_model,
        query_text=query_def['query'],
        keywords=query_def['keywords'],
        doc_name=doc_name,
        top_k=TOP_K_RETRIEVAL
    )

    logger.info(f"\nChunks recuperati: {len(chunks)}")

    # Reranking
    chunks_reranked = rerank_chunks(
        query_text=query_def['query'],
        chunks=chunks,
        reranker=reranker,
        top_k=TOP_K_RERANK
    )

    logger.info(f"Chunks dopo reranking: {len(chunks_reranked)}")

    # Mostra risultati
    logger.info(f"\n{'─'*70}")
    logger.info("TOP CHUNKS (dopo reranking):")
    logger.info(f"{'─'*70}")

    for i, chunk in enumerate(chunks_reranked, 1):
        meta = chunk['metadata']
        logger.info(f"\n[{i}] Score: {chunk['rerank_score']:.4f} | Dist: {chunk['distance']:.4f}")
        logger.info(f"    Sezione: {meta.get('section_title', 'N/A')}")
        logger.info(f"    Doc: {meta.get('doc_name', 'N/A')}")

        # Mostra parte rilevante del contenuto
        content = chunk['content']
        if 'cimice' in content.lower():
            idx = content.lower().find('cimice')
            excerpt = content[max(0, idx-50):idx+300]
            logger.info(f"    Excerpt: ...{excerpt}...")
        else:
            logger.info(f"    Excerpt: {content[:200]}...")

    return {
        "query_id": query_id,
        "query_name": query_def['name'],
        "chunks_retrieved": len(chunks),
        "chunks_reranked": len(chunks_reranked),
        "top_chunks": [
            {
                "section": c['metadata'].get('section_title'),
                "doc": c['metadata'].get('doc_name'),
                "rerank_score": c['rerank_score'],
                "distance": c['distance'],
                "content_preview": c['content'][:500]
            }
            for c in chunks_reranked
        ]
    }


def main():
    """Test principale del retrieval cimice."""

    load_dotenv()

    logger.info("=" * 70)
    logger.info("TEST RETRIEVAL CIMICE ASIATICA")
    logger.info("=" * 70)

    # Carica modelli
    logger.info("Caricamento modelli...")
    embedding_model = SentenceTransformer(MODEL_NAME)
    reranker = CrossEncoder(RERANKER_MODEL)

    # Connetti a ChromaDB
    logger.info(f"Connessione a ChromaDB: {CHROMADB_DIR}")
    client = chromadb.PersistentClient(path=str(CHROMADB_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    # Opzionale: filtra per un documento specifico
    # doc_name = "Bollettino 30 del 1° ottobre 2025 di Bologna e Ferrara"
    doc_name = None  # Cerca in tutti i documenti

    # Test tutte le query
    results = []
    for query_id, query_def in QUERIES.items():
        result = test_single_query(
            query_id=query_id,
            query_def=query_def,
            collection=collection,
            embedding_model=embedding_model,
            reranker=reranker,
            doc_name=doc_name
        )
        results.append(result)

    # Salva risultati
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "cimice_retrieval_test.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "config": {
                "TOP_K_RETRIEVAL": TOP_K_RETRIEVAL,
                "TOP_K_RERANK": TOP_K_RERANK,
                "doc_filter": doc_name
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"\n{'='*70}")
    logger.info(f"Test completato! Risultati salvati in: {output_file}")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()
