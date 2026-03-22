"""
Test script per analizzare i chunks generati dal bollettino 16 di Reggio Emilia.
Focus su Scafoideo (Scaphoideus titanus) e Flavescenza Dorata.
Salva un JSON con tutti i chunks e metadata per verifica.
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

# PDF da testare - Bollettino 16 Reggio Emilia
TEST_PDF = "Bollettino  16 del 29 Maggio 2025 Reggio Emilia.pdf"

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
    'LOTTA OBBLIGATORIA CONTRO FLAVESCENZA DORATA',
    'SCAPHOIDEUS', 'SCAFOIDEO'
}

# Keywords per identificare contenuti su flavescenza/scafoideo
FLAVESCENZA_KEYWORDS = [
    'scafoideo', 'scaphoideus', 'titanus',
    'flavescenza', 'flavescence', 'dorata', 'doree',
    'giallume', 'giallumi', 'fitoplasma', 'fitoplasmi',
    'lotta obbligatoria', 'trattamento obbligatorio',
    'candidatus phytoplasma', 'vitis'
]
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

    province_match = re.search(r"(?:di\s+)?([A-Za-z\s]+?)(?:\.(?:md|pdf))?$", filename, re.IGNORECASE)
    if province_match:
        province_str = province_match.group(1)
        province_list = re.split(r',|\se\s', province_str)
        metadata["province"] = [p.strip() for p in province_list if p.strip() and not p.strip().isdigit()]

    return metadata


def extract_sections_from_markdown(md_text: str) -> Dict[str, str]:
    """Estrae sezioni dal markdown basandosi sui titoli."""
    sections = {}
    current_section = "Introduzione"
    buffer = []

    lines = md_text.splitlines()

    for line in lines:
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
    """Verifica se una sezione è protetta"""
    title_upper = title.upper().strip()
    for protected in PROTECTED_SECTIONS:
        if protected in title_upper or title_upper in protected:
            return True
    return False


def contains_flavescenza_keywords(text: str) -> bool:
    """Verifica se il testo contiene keywords su flavescenza/scafoideo"""
    text_lower = text.lower()
    for keyword in FLAVESCENZA_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def merge_small_sections(sections: Dict[str, str]) -> List[Dict]:
    """Unisce sezioni piccole consecutive"""
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


def create_chunks_from_markdown(md_text: str, doc_name: str) -> List[Dict]:
    """Crea chunks dal testo markdown"""
    file_metadata = extract_metadata_from_filename(doc_name)
    sections = extract_sections_from_markdown(md_text)
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
            "has_flavescenza": contains_flavescenza_keywords(section["title"] + " " + content),
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
    """Test principale: processa bollettino e analizza chunks flavescenza"""

    pdf_path = INPUT_DIR / TEST_PDF

    if not pdf_path.exists():
        logger.error(f"File non trovato: {pdf_path}")
        return

    logger.info(f"=" * 70)
    logger.info(f"TEST CHUNKING FLAVESCENZA/SCAFOIDEO")
    logger.info(f"PDF: {TEST_PDF}")
    logger.info(f"=" * 70)

    # Step 1: PDF -> Markdown
    md_text = convert_pdf_to_markdown(pdf_path)
    if not md_text:
        return

    # Salva anche il markdown raw per analisi
    md_output = OUTPUT_DIR / "reggio_16_raw.md"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(md_output, "w", encoding="utf-8") as f:
        f.write(md_text)
    logger.info(f"Markdown salvato: {md_output}")

    # Step 2: Estrai metadata
    metadata = extract_metadata_from_filename(TEST_PDF)
    logger.info(f"Metadata estratti: {metadata}")

    # Step 3: Chunking
    doc_name = pdf_path.stem
    chunks = create_chunks_from_markdown(md_text, doc_name)

    # Statistiche
    total_chunks = len(chunks)
    valid_chunks = [c for c in chunks if not c['skipped']]
    flavescenza_chunks = [c for c in chunks if c['has_flavescenza']]

    logger.info(f"\n" + "=" * 70)
    logger.info(f"STATISTICHE CHUNKS:")
    logger.info(f"=" * 70)
    logger.info(f"Totale chunks: {total_chunks}")
    logger.info(f"Chunks validi (>= {MIN_CHUNK_WORDS} parole): {len(valid_chunks)}")
    logger.info(f"Chunks con Scafoideo/Flavescenza: {len(flavescenza_chunks)}")

    # Prepara output
    output = {
        "file": TEST_PDF,
        "metadata": metadata,
        "config": {
            "MIN_CHUNK_WORDS": MIN_CHUNK_WORDS,
            "MERGE_THRESHOLD": MERGE_THRESHOLD,
            "FLAVESCENZA_KEYWORDS": FLAVESCENZA_KEYWORDS
        },
        "stats": {
            "total_chunks": total_chunks,
            "valid_chunks": len(valid_chunks),
            "flavescenza_chunks": len(flavescenza_chunks)
        },
        "chunks": chunks,
        "markdown_raw": md_text
    }

    # Salva JSON completo
    output_file = OUTPUT_DIR / "reggio_16_chunks_flavescenza.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info(f"Output salvato: {output_file}")

    # Stampa riepilogo tutti i chunks
    logger.info("\n" + "=" * 70)
    logger.info("RIEPILOGO TUTTI I CHUNKS:")
    logger.info("-" * 70)
    for chunk in chunks:
        status = "SKIP" if chunk['skipped'] else "OK"
        flave = "[FLAV]" if chunk['has_flavescenza'] else ""
        title_display = chunk['section_title'][:50]
        logger.info(f"[{status}] {title_display:<50} {flave:>6} | {chunk['word_count']:>4} parole")

    # Mostra specificamente i chunks su flavescenza/scafoideo
    logger.info("\n" + "=" * 70)
    logger.info("CHUNKS SCAFOIDEO/FLAVESCENZA DORATA:")
    logger.info("=" * 70)

    for chunk in flavescenza_chunks:
        logger.info(f"\n{'─'*70}")
        logger.info(f"[{'SKIP' if chunk['skipped'] else 'OK'}] {chunk['section_title']}")
        logger.info(f"    Parole: {chunk['word_count']}")

        # Trova e evidenzia le keywords trovate
        content_lower = chunk['content'].lower()
        found_keywords = [kw for kw in FLAVESCENZA_KEYWORDS if kw in content_lower]
        logger.info(f"    Keywords trovate: {', '.join(found_keywords)}")

        # Mostra contenuto (primi 800 caratteri)
        logger.info(f"\n    CONTENUTO:")
        logger.info(f"    {chunk['content'][:800]}...")
        logger.info(f"{'─'*70}")

    # Salva anche un file markdown con solo i chunks flavescenza per facile lettura
    flavescenza_md = OUTPUT_DIR / "reggio_16_flavescenza_chunks.md"
    with open(flavescenza_md, "w", encoding="utf-8") as f:
        f.write("# Chunks Scafoideo/Flavescenza Dorata - Bollettino 16 Reggio Emilia\n\n")
        f.write(f"**Totale chunks con keywords flavescenza:** {len(flavescenza_chunks)}\n\n")
        f.write("---\n\n")

        for i, chunk in enumerate(flavescenza_chunks, 1):
            content_lower = chunk['content'].lower()
            found_keywords = [kw for kw in FLAVESCENZA_KEYWORDS if kw in content_lower]

            f.write(f"## {i}. {chunk['section_title']}\n\n")
            f.write(f"**Parole:** {chunk['word_count']} | **Keywords:** {', '.join(found_keywords)}\n\n")
            f.write(f"### Contenuto:\n\n")
            f.write(f"{chunk['content']}\n\n")
            f.write("---\n\n")

    logger.info(f"\nChunks flavescenza salvati in: {flavescenza_md}")
    logger.info(f"=" * 70)


if __name__ == "__main__":
    main()
