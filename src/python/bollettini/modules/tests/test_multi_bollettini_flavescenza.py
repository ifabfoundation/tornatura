"""
Test script per analizzare più bollettini e confrontare contenuti su Scafoideo/Flavescenza.
"""

from pathlib import Path
import re
import json
import logging
import warnings
import os
from typing import Dict, List

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

# PDF da confrontare
TEST_PDFS = [
    "Bollettino  22 del 10 Luglio 2025 Reggio Emilia.pdf",
    "Bollettino 18 del 10 giugno 2025 Modena.pdf",
]

MIN_CHUNK_WORDS = 50
MERGE_THRESHOLD = 100
SECTION_PATTERN = re.compile(r"^#{1,3}\s+.+")

PROTECTED_SECTIONS = {
    'MELO', 'PERO', 'PESCO', 'SUSINO', 'CILIEGIO', 'ALBICOCCO',
    'ACTINIDIA', 'KAKI', 'VITE', 'NOCE', 'NOCCIOLO', 'OLIVO',
    'LOTTA OBBLIGATORIA CONTRO FLAVESCENZA DORATA',
    'SCAPHOIDEUS', 'SCAFOIDEO'
}

FLAVESCENZA_KEYWORDS = [
    'scafoideo', 'scaphoideus', 'titanus',
    'flavescenza', 'flavescence', 'dorata',
    'giallume', 'fitoplasma',
    'lotta obbligatoria', 'trattamento obbligatorio'
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def convert_pdf_to_markdown(pdf_path: Path) -> str | None:
    try:
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        return result.document.export_to_markdown()
    except Exception as e:
        logger.error(f"Errore conversione {pdf_path.name}: {e}")
        return None


def extract_sections_from_markdown(md_text: str) -> Dict[str, str]:
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


def contains_flavescenza_keywords(text: str) -> List[str]:
    """Ritorna le keywords trovate nel testo"""
    text_lower = text.lower()
    found = []
    for keyword in FLAVESCENZA_KEYWORDS:
        if keyword in text_lower:
            found.append(keyword)
    return found


def analyze_bollettino(pdf_name: str) -> Dict:
    """Analizza un bollettino e ritorna le sezioni su flavescenza"""
    pdf_path = INPUT_DIR / pdf_name

    if not pdf_path.exists():
        logger.error(f"File non trovato: {pdf_name}")
        return None

    logger.info(f"\n{'='*70}")
    logger.info(f"Analizzando: {pdf_name}")
    logger.info(f"{'='*70}")

    md_text = convert_pdf_to_markdown(pdf_path)
    if not md_text:
        return None

    sections = extract_sections_from_markdown(md_text)

    flavescenza_sections = []
    for title, content in sections.items():
        full_text = title + " " + content
        keywords_found = contains_flavescenza_keywords(full_text)

        if keywords_found:
            flavescenza_sections.append({
                "title": title,
                "keywords": keywords_found,
                "word_count": len(content.split()),
                "content": content
            })

    return {
        "pdf_name": pdf_name,
        "total_sections": len(sections),
        "flavescenza_sections": len(flavescenza_sections),
        "sections": flavescenza_sections
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []
    all_unique_titles = set()
    all_unique_keywords_by_section = {}

    for pdf_name in TEST_PDFS:
        result = analyze_bollettino(pdf_name)
        if result:
            all_results.append(result)

            for section in result["sections"]:
                title_normalized = section["title"][:50]
                all_unique_titles.add(title_normalized)

                if title_normalized not in all_unique_keywords_by_section:
                    all_unique_keywords_by_section[title_normalized] = set()
                all_unique_keywords_by_section[title_normalized].update(section["keywords"])

    # Stampa riepilogo comparativo
    logger.info("\n" + "="*80)
    logger.info("RIEPILOGO COMPARATIVO SEZIONI FLAVESCENZA/SCAFOIDEO")
    logger.info("="*80)

    for result in all_results:
        logger.info(f"\n--- {result['pdf_name']} ---")
        logger.info(f"Sezioni totali: {result['total_sections']} | Con flavescenza: {result['flavescenza_sections']}")

        for section in result["sections"]:
            logger.info(f"  [{section['word_count']:>4} parole] {section['title'][:60]}")
            logger.info(f"              Keywords: {', '.join(section['keywords'])}")

    # Confronta i titoli delle sezioni tra bollettini
    logger.info("\n" + "="*80)
    logger.info("TITOLI UNICI SEZIONI FLAVESCENZA (tutti i bollettini)")
    logger.info("="*80)
    for title in sorted(all_unique_titles):
        logger.info(f"  - {title}")

    # Salva output dettagliato
    output_file = OUTPUT_DIR / "multi_bollettini_flavescenza.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    logger.info(f"\nRisultati salvati in: {output_file}")

    # Salva markdown comparativo
    md_file = OUTPUT_DIR / "multi_bollettini_flavescenza_comparison.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("# Confronto Sezioni Flavescenza/Scafoideo\n\n")

        for result in all_results:
            f.write(f"## {result['pdf_name']}\n\n")
            f.write(f"**Sezioni flavescenza:** {result['flavescenza_sections']}\n\n")

            for i, section in enumerate(result["sections"], 1):
                f.write(f"### {i}. {section['title']}\n\n")
                f.write(f"**Keywords:** {', '.join(section['keywords'])} | **Parole:** {section['word_count']}\n\n")
                f.write(f"```\n{section['content'][:2000]}{'...' if len(section['content']) > 2000 else ''}\n```\n\n")
                f.write("---\n\n")

    logger.info(f"Confronto MD salvato in: {md_file}")


if __name__ == "__main__":
    main()
