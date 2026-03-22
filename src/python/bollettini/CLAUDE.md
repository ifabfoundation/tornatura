# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# RAG Bollettini - Sistema di Produzione

## Descrizione
Sistema RAG per estrazione automatica informazioni dai bollettini fitosanitari della Regione Emilia-Romagna.
Estrae informazioni su **Cimice Asiatica** e **Flavescenza Dorata/Scaphoideus titanus**.

## Setup

```bash
# Clona e entra nella directory
cd RAG_bollettini

# Crea virtual environment
python3 -m venv venv
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Configura API key
cp .env.example .env
# Modifica .env con la tua OPENAI_API_KEY
```

## Struttura Progetto

```
RAG_bollettini/
├── run_pipeline.py              # MAIN: orchestrator pipeline completa
├── scheduler.py                 # Scheduler giornaliero (APScheduler)
├── requirements.txt             # Dipendenze Python
├── .env.example                 # Template variabili ambiente
├── CLAUDE.md                    # Documentazione
│
├── modules/
│   ├── download_bollettini.py   # Download PDF da sito Regione
│   ├── process_bollettini.py    # Conversione PDF → ChromaDB
│   ├── cimice.py                # Query RAG Cimice Asiatica
│   ├── flavescenza.py           # Query RAG Flavescenza Dorata
│   └── normativa_flavescenza.py # Dati normativa strutturati
│
├── data/
│   ├── 1_collections/bollettini/  # PDF scaricati (organizzati per anno)
│   │   ├── 2025/                  # PDF del 2025
│   │   └── 2026/                  # PDF del 2026
│   ├── chromadb/                  # Vector database
│   ├── cache/                     # Cache query
│   ├── output/
│   │   ├── cimice/              # Report MD + history/
│   │   └── flavescenza/         # Report MD + history/
│   ├── bollettini_cache.json    # Cache download
│   └── processing_cache.json    # Cache indicizzazione
│
└── venv/                        # Virtual environment
```

## Uso in Produzione

### Attivazione ambiente
```bash
cd RAG_bollettini
source venv/bin/activate
```

### Pipeline completa (consigliato)
```bash
# Esegue: download → indicizzazione → generazione report
python run_pipeline.py
```

### Opzioni pipeline
```bash
python run_pipeline.py --force      # Ignora cache, riprocessa tutto
python run_pipeline.py --query-only # Solo generazione report (no download)
```

### Scheduler automatico
```bash
python scheduler.py --start         # Avvia scheduler giornaliero
```

### Moduli singoli (debug/test)
```bash
python modules/download_bollettini.py   # Solo download nuovi PDF
python modules/process_bollettini.py    # Solo indicizzazione in ChromaDB
python modules/cimice.py                # Solo report cimice
python modules/flavescenza.py           # Solo report flavescenza
```

## Pipeline di Esecuzione

```
1. download_bollettini.py
   └─> Scarica PDF da API Regione → data/1_collections/bollettini/{anno}/

2. process_bollettini.py
   └─> PDF → Markdown (Docling) → Chunks → ChromaDB

3. cimice.py / flavescenza.py
   └─> Retrieval keyword-based → GPT-4o-mini → Report MD
```

## Approccio Retrieval

**Keyword-based** (non semantic search):
- Recupera chunks del bollettino
- Filtra per keywords specifiche
- Passa al LLM senza reranking

| Modulo | Keywords |
|--------|----------|
| cimice.py | `cimice, halyomorpha, halys, hhal, cimici` |
| flavescenza.py | `flavescenza, scaphoideus, scafoideo, titanus, giallumi, fitoplasm` |

## Normativa Flavescenza

La normativa (Determinazione Regionale) è gestita da `normativa_flavescenza.py`:
- Dati strutturati in Python (non in ChromaDB)
- Filtrati per provincia prima del LLM
- Zero query database per la normativa

### Aggiornamento annuale (Maggio)
Quando esce la nuova Determinazione:
```python
# In modules/normativa_flavescenza.py
NORMATIVA_2026 = { ... }  # Aggiorna con nuovi dati
NORMATIVA_CORRENTE = NORMATIVA_2026
```

## Collezioni ChromaDB

| Collezione | Contenuto |
|------------|-----------|
| `cimice_asiatica` | Chunks bollettini |
| `flavescenza_dorata` | Chunks bollettini |

## Output

I report vengono salvati in:
- `data/output/cimice/` - Report cimice per provincia
- `data/output/flavescenza/` - Report flavescenza per provincia

Formato nome file: `{provincia}_{DD-MM-YYYY}.md` (data in formato italiano)

### History automatica

Quando arriva un nuovo bollettino, il report precedente viene spostato automaticamente in history:

```
output/
├── cimice/
│   ├── bologna_ferrara_15-11-2025.md      ← report corrente
│   └── history/
│       └── 2025/
│           └── bologna_ferrara/
│               └── 01-10-2025.md          ← report precedente
```

La history è organizzata per `{anno}/{provincia}/` e viene creata dinamicamente.

## Cache

Il sistema usa cache per evitare riprocessamento:
- `data/bollettini_cache.json` - PDF già scaricati
- `data/processing_cache.json` - PDF già indicizzati
- `data/cache/cimice_processed.json` - Bollettini già processati (cimice)
- `data/cache/flavescenza_processed.json` - Bollettini già processati (flavescenza)

Per forzare riprocessamento: `python run_pipeline.py --force`

## Note operative

1. **Frequenza bollettini**: ogni ~2 settimane
2. **Scheduler**: gira giornalmente, processa solo novità
3. **Costi LLM**: ~$0.002 per query con GPT-4o-mini
4. **Pattern stagionali**:
   - Inverno (N.1-8): poche info scafoideo/cimice
   - Primavera (N.9-15): inizio monitoraggio
   - Estate (N.16-23): PICCO attività
   - Autunno (N.24-30): declino
