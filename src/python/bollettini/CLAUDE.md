# RAG Colture (bollettini) — Sistema di Produzione

Componente del monorepo **tornatura** (`src/python/bollettini`) che estrae informazioni per coltura
dai bollettini fitosanitari e genera report (Markdown + HTML).
Regioni: **Emilia-Romagna** (API REST Plone) e **Campania** (scraping HTML).

Principio guida: **estrazione fedele** — riportare TUTTO il crop-specifico della fonte, senza perdere
dati e senza inventarne. Dettaglio tecnico completo: `report.md`. Storico modifiche: `CHANGELOG.md`.

## Architettura (aggiornata 2026-06)
- **Storage: SQLite** (`modules/chunk_store.py`, `ChunkStore`, file `data/chunks.db`). **Niente
  ChromaDB, niente embedding**: il retrieval è **match esatto sui metadati** (una coltura = un chunk).
  `ChunkStore` ritorna la stessa forma di `ChromaDB.get()` per compatibilità coi consumatori.
- **Due system prompt dedicati per regione** (`SYSTEM_PROMPT` ER quantitativo/regolatorio,
  `SYSTEM_PROMPT_CAMPANIA` qualitativo) + **pass di verifica/revisione** indipendente (anti-perdita +
  anti-allucinazione). I due prompt **non vanno ri-unificati** (un prompt unico, su Campania, induce
  numeri inventati).
- **Campania**: tabella di monitoraggio **iniettata deterministicamente** dal codice
  (`extract_campania_monitoring`/`inject_monitoring`), non scritta dall'LLM; coda istituzionale rimossa
  (`strip_campania_appendix`). **ER**: deroghe filtrate per-voce (`filter_deroghe_per_voce`).
- Conversione PDF con **Docling, OCR disattivato** (`do_ocr=False`). Generazione `gpt-4o-mini`
  (`temperature=0`).

## Struttura del package
```
src/python/bollettini/
├── api.py            # FastAPI: report per lat/lng (geopandas + shapefiles); /v1/bollettini/...
├── scheduler.py      # APScheduler: esegue la pipeline ogni giorno (08:00 Europe/Rome)
├── run_pipeline.py   # Orchestratore: download → process → query (exit 0/1/2)
├── paths.py          # Path runtime: BOLLETTINI_RUNTIME_DIR → DATA_DIR/OUTPUT_DIR/SHAPEFILE_DIR
├── modules/
│   ├── config.py             # REGIONI + COLTURE (ER 5, Campania 17)
│   ├── chunk_store.py        # ChunkStore SQLite (no embedding)
│   ├── downloaders/base.py   # BaseDownloader (astratto)
│   ├── download_bollettini.py# Downloader Emilia-Romagna (API Plone)
│   ├── download_campania.py  # Downloader Campania (scraping HTML, usa beautifulsoup4)
│   ├── process_bollettini.py # PDF → Markdown (Docling) → chunk → SQLite
│   └── colture.py            # Retrieval + generazione LLM → report MD/HTML (+ history/)
├── shapefiles/       # province_italia.shp (usato), province_emilia_romagna.shp
├── BUILD             # target Pants (pex_binary: scheduler, api)
└── data/             # runtime, NON in git: chunks.db, input_bollettini/, cache/, output_bollettini/
```

## Dati runtime e path (`paths.py`)
Tutto deriva da `RUNTIME_DIR` (env `BOLLETTINI_RUNTIME_DIR`, default = cartella del package):
`DATA_DIR = RUNTIME_DIR/data`, `OUTPUT_DIR = DATA_DIR/output_bollettini`, `chunks.db` in `DATA_DIR`,
`SHAPEFILE_DIR = <package>/shapefiles`. In Docker il volume è `/data/bollettini`. `data/**` è
in `.gitignore` (artefatti runtime, non versionati).

## Esecuzione
**Produzione (Docker/AWS):** l'immagine `src/docker/bollettini` avvia lo **scheduler**
(`--run-now` all'avvio, poi giornaliero) e l'**API**. Build via Pants (`pex_binary` `scheduler`/`api`).

**Pipeline (CLI, per sviluppo):**
```bash
python -m bollettini.run_pipeline                 # tutte le regioni, solo bollettini nuovi
python -m bollettini.run_pipeline --regione campania
python -m bollettini.run_pipeline --force         # ignora cache, rigenera tutto
python -m bollettini.run_pipeline --query-only    # solo generazione dai chunk esistenti
```
Exit code: `0` nuovi dati · `1` niente di nuovo · `2` errore.

**API:**
```
GET /v1/bollettini/culture/{coltura}/location?lat=<lat>&lng=<lng>
GET /v1/bollettini/health
```
Restituisce il report della coltura per la provincia che contiene il punto. Copre **Emilia-Romagna
e Campania** (usa `province_italia.shp`).

## Regioni e colture
- **Emilia-Romagna (5):** VITE, PERO, PESCO, MAIS, BARBABIETOLA.
- **Campania (17):** VITE, OLIVO, PESCO, AGRUMI, ACTINIDIA, NOCCIOLO, NOCE, CIPOLLA, POMODORO,
  FRAGOLA, CASTAGNO, CILIEGIO, MELO, PERO, PATATA, SUSINO, ALBICOCCO.

## Dipendenze (Pants)
Dichiarate in `3rdparty/python/bollettini-requirements.txt` (resolve `bollettini`, lockfile
`bollettini.lock`). Principali: `docling`, `openai`, `markdown`, `requests`, `fastapi`, `uvicorn`,
`geopandas`, `shapely`, `APScheduler`, `python-dotenv`. **Rimossi** `chromadb` e `sentence-transformers`.
Dopo modifiche alle dipendenze: `pants generate-lockfiles --resolve=bollettini` (Linux/CI).
> Nota: `download_campania.py` usa `beautifulsoup4` — assicurarsi che sia dichiarata (vedi CHANGELOG).

## Note operative
1. Solo l'**ultimo bollettino per provincia** viene rigenerato; i precedenti vanno in `history/`.
2. Le colture fuori stagione producono report statici "Nessuna informazione…" (nessuna chiamata LLM).
3. Per prompt completi, validazione, integrazione e costi: `report.md`. Modifiche recenti: `CHANGELOG.md`.
