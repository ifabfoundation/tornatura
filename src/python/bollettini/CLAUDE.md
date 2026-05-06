# RAG Colture - Sistema di Produzione (Multi-regione)

## Descrizione
Sistema RAG per estrazione automatica informazioni colturali dai bollettini fitosanitari.
Supporta **Emilia-Romagna** (API REST Plone) e **Campania** (scraping HTML).

## Struttura Progetto

```
RAG_colture/
├── run_pipeline.py              # MAIN: orchestrator pipeline multi-regione
├── requirements.txt             # Dipendenze Python
├── CLAUDE.md                    # Documentazione
│
├── modules/
│   ├── config.py                # Configurazione multi-regione e colture
│   ├── downloaders/
│   │   ├── __init__.py
│   │   └── base.py              # Classe astratta BaseDownloader
│   ├── download_bollettini.py   # Downloader Emilia-Romagna (API Plone)
│   ├── download_campania.py     # Downloader Campania (scraping HTML)
│   ├── process_bollettini.py    # PDF -> Markdown -> ChromaDB
│   └── colture.py               # Query RAG per colture (multi-regione)
│
├── data/
│   ├── input_bollettini/
│   │   ├── emilia_romagna/
│   │   │   ├── bollettini/       # PDF (symlink -> RAG_bollettini)
│   │   │   └── cache_download.json
│   │   └── campania/
│   │       ├── bollettini/2026/  # PDF scaricati per anno
│   │       └── cache_download.json
│   ├── chromadb/                  # Symlink -> RAG_bollettini
│   ├── cache/
│   │   ├── processing_cache.json
│   │   ├── colture_emilia_romagna_processed.json
│   │   └── colture_campania_processed.json
│   └── output_bollettini/
│       ├── emilia_romagna/
│       │   ├── vite/          # Report ER per coltura
│       │   ├── pero/
│       │   ├── pesco/
│       │   ├── mais/
│       │   └── barbabietola/
│       └── campania/
│           ├── vite/          # Report Campania per coltura
│           ├── pesco/
│           ├── olivo/
│           ├── nocciolo/
│           ├── actinidia/
│           ├── melo/
│           ├── castagno/
│           ├── ciliegio/
│           ├── susino/
│           ├── agrumi/
│           └── pomodoro/
│
├── .env                         # File indipendente
└── venv/                        # Virtual environment indipendente
```

## Uso in Produzione

### Attivazione ambiente
```bash
cd /home/vito/projects/tornatura/RAG_colture
source venv/bin/activate
```

### Pipeline completa (consigliato)
```bash
# Tutte le regioni
python run_pipeline.py

# Solo una regione
python run_pipeline.py --regione campania
python run_pipeline.py --regione emilia_romagna
```

### Opzioni pipeline
```bash
python run_pipeline.py --force              # Ignora cache, riprocessa tutto
python run_pipeline.py --query-only         # Solo generazione report (no download)
python run_pipeline.py --download-only      # Solo download
```

### Modulo singolo (debug/test)
```bash
python modules/download_campania.py    # Download solo Campania
python modules/colture.py              # Solo report colture
```

## Regioni e Colture

### Emilia-Romagna (5 colture)
| ID | Nome |
|----|------|
| VITE | Vite |
| PERO | Pero |
| PESCO | Pesco |
| MAIS | Mais |
| BARBABIETOLA | Barbabietola |

### Campania (11 colture)
| ID | Nome |
|----|------|
| VITE | Vite |
| OLIVO | Olivo |
| PESCO | Pesco |
| ACTINIDIA | Actinidia |
| MELO | Melo |
| CASTAGNO | Castagno |
| CILIEGIO | Ciliegio |
| SUSINO | Susino |
| NOCCIOLO | Nocciolo |
| AGRUMI | Agrumi |
| POMODORO | Pomodoro |

## Pipeline di Esecuzione

```
Per ogni regione:
1. download (ER: API Plone / Campania: scraping HTML)
   └-> Scarica PDF nuovi

2. process_bollettini.py
   └-> PDF -> Markdown (Docling) -> Chunks -> ChromaDB (con metadata regione)

3. colture.py
   └-> Per ogni bollettino (filtrato per regione):
       └-> Per ogni coltura della regione:
           └-> Retrieval sezione-based -> GPT-4o-mini -> Report MD + HTML
```

## Approccio Retrieval

**Sezione-based con fallback keyword e filtro anti-contaminazione**:

1. **PRIMA**: Match esatto su `section_title` (alta precisione)
2. **POI**: Se pochi risultati (<2), cerca keywords nel contenuto
3. **FILTRA**: Escludi sezioni di ALTRE colture (anti-contaminazione)

## Differenze chiave tra regioni

| | Emilia-Romagna | Campania |
|--|----------------|----------|
| Fonte | API REST Plone | Pagine HTML statiche |
| Aree | 4 province raggruppate | 19 aree/comuni in 5 province |
| Formato PDF | `Bollettino N del data di Province.pdf` | `Campania_{area}_{DD-MM-YYYY}.pdf` |
| N. bollettino | Si | No (solo data) |

## Cache

- `data/bollettini_cache.json` - Download ER
- `data/campania_cache.json` - Download Campania
- `data/processing_cache.json` - Processing (tutte le regioni)
- `data/cache/colture_{regione}_processed.json` - Report per regione
- Per forzare riprocessamento: `python run_pipeline.py --force`

## Dipendenze da RAG_bollettini

- **ChromaDB**: Symlink a `../RAG_bollettini/data/chromadb/`
- **Collezione**: Usa `cimice_asiatica` (contiene tutti i bollettini)

## Note operative

1. **Frequenza bollettini ER**: ogni ~2 settimane
2. **Frequenza bollettini Campania**: variabile per area
3. Le colture Campania (OLIVO, AGRUMI, POMODORO, NOCCIOLO) vanno affinate dopo analisi PDF reali
