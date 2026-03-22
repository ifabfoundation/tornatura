"""
Test script per analizzare i chunks generati dal bollettino 30 di Bologna.
Salva un JSON con tutti i chunks e metadata per verifica.
Include chunking intelligente con merge di sezioni piccole.
"""

from pathlib import Path
import re
import json
import logging
import warnings
import os
from typing import Dict, List

# Suppress noisy loggers and warnings before imports
os.environ["RAPIDOCR_LOGGING"] = "ERROR"
os.environ["ONNXRUNTIME_LOGGING_LEVEL"] = "ERROR"

logging.getLogger("docling").setLevel(logging.ERROR)
logging.getLogger("docling.pipeline").setLevel(logging.ERROR)
logging.getLogger("rapidocr").setLevel(logging.ERROR)
logging.getLogger("RapidOCR").setLevel(logging.ERROR)
logging.getLogger("onnxruntime").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from docling.document_converter import DocumentConverter

# ============= CONFIGURAZIONE =============
BASE_DIR = Path(__file__).parent.parent.parent
INPUT_DIR = BASE_DIR / "data" / "1_collections" / "bollettini" / "2025"
OUTPUT_DIR = Path(__file__).parent / "output"

# PDF da testare
TEST_PDF = "Bollettino 30 del 1° ottobre 2025 di Bologna e Ferrara.pdf"

# Parametri chunking (aggiornati)
MIN_CHUNK_WORDS = 50           # Minimo parole per chunk valido
MERGE_THRESHOLD = 100          # Sezioni sotto questa soglia vengono unite alla successiva
SECTION_PATTERN = re.compile(r"^#{1,3}\s+.+")

# Sezioni da NON unire (colture e sezioni importanti) - mantienile intere
PROTECTED_SECTIONS = {
    'MELO', 'PERO', 'PESCO', 'SUSINO', 'CILIEGIO', 'ALBICOCCO',
    'ACTINIDIA', 'KAKI', 'VITE', 'NOCE', 'NOCCIOLO', 'OLIVO',
    'FRUMENTO', 'ORZO', 'COLZA', 'MAIS', 'SOIA',
    'POMODORO', 'PATATA', 'CIPOLLA', 'CAROTA',
    'INFORMAZIONI RIGUARDANTI LA CIMICE ASIATICA',
    'DEROGHE AI DISCIPLINARI DI PRODUZIONE INTEGRATA',
    'LOTTA OBBLIGATORIA CONTRO FLAVESCENZA DORATA'
}
# ==========================================


# ============= LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)
# ==========================================


# ============= PDF TO MARKDOWN ============
def convert_pdf_to_markdown(pdf_path: Path) -> str | None:
    """Converte un PDF in Markdown usando Docling (in memoria)"""
    try:
        logger.info(f"Conversione PDF -> Markdown...")
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        doc = result.document
        return doc.export_to_markdown()
    except Exception as e:
        logger.error(f"Errore conversione: {e}")
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

    # Pattern per province
    province_match = re.search(r"di\s+(.+?)(?:\.(?:md|pdf))?$", filename, re.IGNORECASE)
    if province_match:
        province_str = province_match.group(1)
        province_list = re.split(r',|\se\s', province_str)
        metadata["province"] = [p.strip() for p in province_list if p.strip()]

    return metadata


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
    sections = extract_sections_from_markdown(md_text)

    # Unisci sezioni piccole
    merged_sections = merge_small_sections(sections)

    chunks = []
    chunk_index = 0

    for section in merged_sections:
        content = section["content"]
        word_count = len(content.split()) if content else 0

        chunk_id = f"{doc_name}_chunk_{chunk_index}"

        chunk = {
            "chunk_id": chunk_id,
            "chunk_index": chunk_index,
            "section_title": section["title"],
            "original_titles": section["original_titles"],
            "word_count": word_count,
            "char_count": len(content) if content else 0,
            "skipped": word_count < MIN_CHUNK_WORDS,
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


def main():
    """Test principale: processa il bollettino e salva JSON"""

    pdf_path = INPUT_DIR / TEST_PDF

    if not pdf_path.exists():
        logger.error(f"File non trovato: {pdf_path}")
        return

    logger.info(f"=" * 60)
    logger.info(f"TEST CHUNKING: {TEST_PDF}")
    logger.info(f"=" * 60)

    # Step 1: PDF -> Markdown
    md_text = convert_pdf_to_markdown(pdf_path)
    if not md_text:
        return

    # Step 2: Estrai metadata
    metadata = extract_metadata_from_filename(TEST_PDF)
    logger.info(f"Metadata estratti: {metadata}")

    # Step 3: Chunking con merge intelligente
    doc_name = pdf_path.stem
    chunks = create_chunks_from_markdown(md_text, doc_name)

    # Statistiche
    total_chunks = len(chunks)
    valid_chunks = [c for c in chunks if not c['skipped']]
    skipped_chunks = [c for c in chunks if c['skipped']]
    merged_chunks = [c for c in chunks if len(c['original_titles']) > 1]

    logger.info(f"Totale chunks (dopo merge): {total_chunks}")
    logger.info(f"Chunks validi (>= {MIN_CHUNK_WORDS} parole): {len(valid_chunks)}")
    logger.info(f"Chunks scartati (< {MIN_CHUNK_WORDS} parole): {len(skipped_chunks)}")
    logger.info(f"Chunks con sezioni unite: {len(merged_chunks)}")

    # Prepara output
    output = {
        "file": TEST_PDF,
        "metadata": metadata,
        "config": {
            "MIN_CHUNK_WORDS": MIN_CHUNK_WORDS,
            "MERGE_THRESHOLD": MERGE_THRESHOLD
        },
        "stats": {
            "total_chunks": total_chunks,
            "valid_chunks": len(valid_chunks),
            "skipped_chunks": len(skipped_chunks),
            "merged_chunks": len(merged_chunks)
        },
        "chunks": chunks,
        "markdown_raw": md_text
    }

    # Salva JSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "bologna_30_chunks_v3.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"=" * 60)
    logger.info(f"Output salvato: {output_file}")
    logger.info(f"=" * 60)

    # Stampa riepilogo chunks
    logger.info("\nRIEPILOGO CHUNKS:")
    logger.info("-" * 80)
    for chunk in chunks:
        status = "SKIP" if chunk['skipped'] else "OK"
        merged = f"[+{len(chunk['original_titles'])-1}]" if len(chunk['original_titles']) > 1 else ""
        title_display = chunk['section_title'][:45]
        logger.info(f"[{status}] {title_display:<45} {merged:>4} | {chunk['word_count']:>4} parole")

    # Mostra specificamente i chunks sulla cimice
    logger.info("\n" + "=" * 80)
    logger.info("CHUNKS CIMICE ASIATICA:")
    logger.info("-" * 80)
    for chunk in chunks:
        title_lower = chunk['section_title'].lower()
        content_lower = chunk['content'].lower() if chunk['content'] else ""
        if 'cimice' in title_lower or 'halyomorpha' in title_lower or 'cimice' in content_lower:
            logger.info(f"\n[{'SKIP' if chunk['skipped'] else 'OK'}] {chunk['section_title']}")
            logger.info(f"    Parole: {chunk['word_count']} | Sezioni unite: {len(chunk['original_titles'])}")
            if len(chunk['original_titles']) > 1:
                logger.info(f"    Titoli originali: {chunk['original_titles']}")
            logger.info(f"    Preview: {chunk['content'][:300]}...")


if __name__ == "__main__":
    main()
