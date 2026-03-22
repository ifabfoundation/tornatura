"""
Test script per testare il retrieval delle informazioni su Flavescenza Dorata e Scaphoideus titanus.
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
QUERIES_FILE = BASE_DIR / "modules" / "queries_flavescenza.json"
COLLECTION_NAME = "flavescenza_dorata"

# Documento normativo
NORMATIVA_DOC_NAME = "testo_lotta_flavescenza"

# Modelli
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

# Parametri retrieval
TOP_K_RETRIEVAL = 10   # Chunks da bollettino
TOP_K_NORMATIVA = 6    # Chunks da normativa
TOP_K_RERANK = 5       # Chunks finali dopo reranking

# Bollettino di test (opzionale - None per usare tutti)
TEST_DOC_NAME = None  # Es: "Bollettino  16 del 29 Maggio 2025 Reggio Emilia"
# ==========================================


# ============= LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)
# ==========================================


def load_queries() -> list:
    """Carica le queries dal file JSON."""
    with open(QUERIES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def retrieve_chunks(collection, embedding_model, query_text: str, keywords: list,
                   doc_name: str = None, top_k: int = TOP_K_RETRIEVAL,
                   top_k_normativa: int = TOP_K_NORMATIVA) -> list:
    """
    Retrieval ibrido: bollettino + normativa.
    """
    # Arricchisci query con keywords
    enhanced_query = f"{query_text} {' '.join(keywords)}"

    # Genera embedding
    query_embedding = embedding_model.encode(enhanced_query, show_progress_bar=False)

    all_chunks = []

    # 1. Recupera chunks dal BOLLETTINO
    query_args = {
        "query_embeddings": [query_embedding.tolist()],
        "n_results": top_k + 6,
        "include": ["documents", "metadatas", "distances"]
    }

    # Filtra per documento specifico se richiesto
    if doc_name:
        query_args["where"] = {"doc_name": doc_name}
    else:
        # Escludi normativa dalla ricerca bollettini
        query_args["where"] = {"doc_name": {"$ne": NORMATIVA_DOC_NAME}}

    results = collection.query(**query_args)

    for i in range(len(results['ids'][0])):
        content = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        section_title = meta.get('section_title', '').lower()

        # Salta sezioni sulla cimice
        is_cimice_section = any(kw in section_title for kw in ['cimice', 'halyomorpha'])
        if is_cimice_section:
            continue

        # Verifica rilevanza
        is_relevant = any(kw.lower() in content.lower() for kw in
                         ['flavescenza', 'scaphoideus', 'scafoideo', 'titanus', 'vite', 'vigneto'])

        chunk = {
            "id": results['ids'][0][i],
            "content": content,
            "metadata": meta,
            "distance": results['distances'][0][i],
            "source_type": "bollettino",
            "is_relevant": is_relevant
        }
        all_chunks.append(chunk)

    # 2. Recupera chunks dalla NORMATIVA
    try:
        query_args_norm = {
            "query_embeddings": [query_embedding.tolist()],
            "n_results": top_k_normativa,
            "include": ["documents", "metadatas", "distances"],
            "where": {"doc_name": NORMATIVA_DOC_NAME}
        }

        results_norm = collection.query(**query_args_norm)

        for i in range(len(results_norm['ids'][0])):
            chunk = {
                "id": results_norm['ids'][0][i],
                "content": results_norm['documents'][0][i],
                "metadata": results_norm['metadatas'][0][i],
                "distance": results_norm['distances'][0][i],
                "source_type": "normativa",
                "is_relevant": True
            }
            all_chunks.append(chunk)

        logger.info(f"    Normativa chunks: {len(results_norm['ids'][0])}")
    except Exception as e:
        logger.warning(f"    Normativa non trovata: {e}")

    # Ordina per rilevanza e distanza
    all_chunks.sort(key=lambda x: (not x['is_relevant'], x['distance']))

    return all_chunks[:top_k + top_k_normativa]


def rerank_chunks(query_text: str, chunks: list, reranker: CrossEncoder, top_k: int = TOP_K_RERANK) -> list:
    """Reranking dei chunks usando cross-encoder."""
    if not chunks:
        return []

    pairs = [(query_text, chunk['content']) for chunk in chunks]
    scores = reranker.predict(pairs)

    for i, chunk in enumerate(chunks):
        chunk['rerank_score'] = float(scores[i])

    chunks_sorted = sorted(chunks, key=lambda x: x['rerank_score'], reverse=True)
    return chunks_sorted[:top_k]


def generate_llm_answer(query_text: str, chunks: list, client: OpenAI) -> str:
    """Genera risposta con LLM."""
    context = ""
    for i, chunk in enumerate(chunks, 1):
        meta = chunk['metadata']
        source_type = chunk.get('source_type', 'bollettino')

        if source_type == "normativa":
            fonte = "Determinazione N.9016 del 14/05/2025 (Normativa)"
        else:
            fonte = f"Bollettino N.{meta.get('numero_bollettino', '?')}"
            if meta.get('data'):
                fonte += f" del {meta.get('data')}"
            if meta.get('province'):
                fonte += f" ({meta.get('province')})"

        context += f"\n--- FONTE {i}: {fonte} ---\n"
        context += f"Sezione: {meta.get('section_title', 'N/A')}\n"
        context += chunk['content']
        context += "\n\n"

    system_prompt = """Sei un esperto fitosanitario. Estrai dai documenti le informazioni su Flavescenza Dorata e Scaphoideus titanus.

REGOLE:
1. Basati SOLO sui documenti forniti.
2. Rispondi SOLO su Flavescenza/Scaphoideus: ignora cimice asiatica e altre avversità.
3. Se non trovi informazioni, scrivi "Non indicato".
4. Cita sempre la fonte.
5. Distingui tra OBBLIGHI NORMATIVI e RACCOMANDAZIONI TECNICHE."""

    user_prompt = f"""Basandoti su questi estratti:

{context}

{query_text}

Rispondi in modo strutturato, citando le fonti."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content


def test_single_query(query_def: dict, collection, embedding_model, reranker,
                      openai_client, doc_name: str = None) -> dict:
    """Testa una singola query."""
    query_id = query_def['query_id']
    query_name = query_def['query_name']
    query_text = query_def['query_text']
    keywords = query_def.get('keywords', [])

    logger.info(f"\n{'='*70}")
    logger.info(f"QUERY: {query_name}")
    logger.info(f"{'='*70}")
    logger.info(f"Query text: {query_text[:150]}...")

    # Retrieval
    chunks = retrieve_chunks(
        collection=collection,
        embedding_model=embedding_model,
        query_text=query_text,
        keywords=keywords,
        doc_name=doc_name,
        top_k=TOP_K_RETRIEVAL,
        top_k_normativa=TOP_K_NORMATIVA
    )

    logger.info(f"Chunks recuperati: {len(chunks)} (bollettino + normativa)")

    # Conta per fonte
    bollettino_count = sum(1 for c in chunks if c['source_type'] == 'bollettino')
    normativa_count = sum(1 for c in chunks if c['source_type'] == 'normativa')
    logger.info(f"  - Bollettino: {bollettino_count}")
    logger.info(f"  - Normativa: {normativa_count}")

    # Reranking
    chunks_reranked = rerank_chunks(
        query_text=query_text,
        chunks=chunks,
        reranker=reranker,
        top_k=TOP_K_RERANK
    )

    logger.info(f"Chunks dopo reranking: {len(chunks_reranked)}")

    # Mostra top chunks
    logger.info(f"\n{'─'*70}")
    logger.info("TOP CHUNKS (dopo reranking):")
    logger.info(f"{'─'*70}")

    for i, chunk in enumerate(chunks_reranked, 1):
        meta = chunk['metadata']
        source = "[NORM]" if chunk['source_type'] == 'normativa' else "[BOLL]"
        logger.info(f"\n[{i}] {source} Score: {chunk['rerank_score']:.4f} | Dist: {chunk['distance']:.4f}")
        logger.info(f"    Sezione: {meta.get('section_title', 'N/A')[:60]}")

        # Mostra excerpt rilevante
        content = chunk['content']
        for kw in ['scafoideo', 'scaphoideus', 'flavescenza', 'titanus']:
            if kw in content.lower():
                idx = content.lower().find(kw)
                excerpt = content[max(0, idx-30):idx+200]
                logger.info(f"    Excerpt: ...{excerpt}...")
                break
        else:
            logger.info(f"    Excerpt: {content[:150]}...")

    # Genera risposta LLM
    logger.info(f"\n{'─'*70}")
    logger.info("RISPOSTA LLM:")
    logger.info(f"{'─'*70}")

    answer = generate_llm_answer(
        query_text=query_text,
        chunks=chunks_reranked,
        client=openai_client
    )

    # Stampa risposta (prime 1000 chars)
    logger.info(f"\n{answer[:1500]}{'...' if len(answer) > 1500 else ''}")

    return {
        "query_id": query_id,
        "query_name": query_name,
        "query_text": query_text,
        "chunks_retrieved": len(chunks),
        "chunks_reranked": len(chunks_reranked),
        "answer": answer,
        "top_chunks": [
            {
                "source_type": c['source_type'],
                "section": c['metadata'].get('section_title'),
                "rerank_score": c['rerank_score'],
                "distance": c['distance'],
                "content_preview": c['content'][:500]
            }
            for c in chunks_reranked
        ]
    }


def main():
    """Test principale del retrieval flavescenza."""
    load_dotenv()

    logger.info("=" * 70)
    logger.info("TEST RETRIEVAL FLAVESCENZA DORATA / SCAPHOIDEUS TITANUS")
    logger.info("=" * 70)

    # Carica queries
    logger.info(f"Loading queries from: {QUERIES_FILE}")
    queries = load_queries()
    logger.info(f"Loaded {len(queries)} queries")

    # Carica modelli
    logger.info("Loading embedding model...")
    embedding_model = SentenceTransformer(MODEL_NAME)

    logger.info("Loading reranker model...")
    reranker = CrossEncoder(RERANKER_MODEL)

    logger.info("Initializing OpenAI client...")
    openai_client = OpenAI()

    # Connetti a ChromaDB
    logger.info(f"Connecting to ChromaDB: {CHROMADB_DIR}")
    client = chromadb.PersistentClient(path=str(CHROMADB_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    # Verifica se esiste la normativa
    try:
        norm_check = collection.get(where={"doc_name": NORMATIVA_DOC_NAME}, limit=1)
        if norm_check['ids']:
            logger.info(f"Normativa trovata: {NORMATIVA_DOC_NAME}")
        else:
            logger.warning(f"ATTENZIONE: Normativa non trovata: {NORMATIVA_DOC_NAME}")
    except Exception as e:
        logger.warning(f"Errore verifica normativa: {e}")

    # Test tutte le query
    results = []
    for query_def in queries:
        result = test_single_query(
            query_def=query_def,
            collection=collection,
            embedding_model=embedding_model,
            reranker=reranker,
            openai_client=openai_client,
            doc_name=TEST_DOC_NAME
        )
        results.append(result)

    # Salva risultati JSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "flavescenza_retrieval_test.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "config": {
                "TOP_K_RETRIEVAL": TOP_K_RETRIEVAL,
                "TOP_K_NORMATIVA": TOP_K_NORMATIVA,
                "TOP_K_RERANK": TOP_K_RERANK,
                "doc_filter": TEST_DOC_NAME
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)

    # Salva anche markdown riepilogativo
    md_file = OUTPUT_DIR / "flavescenza_retrieval_test.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("# Test Retrieval Flavescenza Dorata\n\n")
        f.write(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write(f"**Chunks bollettino:** {TOP_K_RETRIEVAL} | **Chunks normativa:** {TOP_K_NORMATIVA} | **Dopo rerank:** {TOP_K_RERANK}\n\n")
        f.write("---\n\n")

        for result in results:
            f.write(f"## {result['query_name']}\n\n")
            f.write(f"**Top chunks:**\n")
            for chunk in result['top_chunks'][:3]:
                source = "NORM" if chunk['source_type'] == 'normativa' else "BOLL"
                f.write(f"- [{source}] {chunk['section'][:50]} (score: {chunk['rerank_score']:.3f})\n")
            f.write(f"\n**Risposta:**\n\n{result['answer']}\n\n")
            f.write("---\n\n")

    logger.info(f"\n{'='*70}")
    logger.info(f"Test completato!")
    logger.info(f"JSON: {output_file}")
    logger.info(f"MD: {md_file}")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()
