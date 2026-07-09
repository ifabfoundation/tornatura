# RAG Colture (bollettini)

Componente del monorepo **tornatura** (`src/python/bollettini`): estrae informazioni per coltura dai
bollettini fitosanitari (**Emilia-Romagna** via API Plone, **Campania** via scraping HTML) e genera
report Markdown + HTML, esposti via API per posizione (lat/lng).

## Esecuzione
In **produzione** gira come immagine Docker (`src/docker/bollettini`): lo **scheduler** esegue la
pipeline ogni giorno e l'**API** serve i report. Build via **Pants** (target `scheduler` e `api`).

Pipeline da riga di comando (sviluppo/debug):
```bash
python -m bollettini.run_pipeline                  # tutte le regioni, solo bollettini nuovi
python -m bollettini.run_pipeline --regione campania
python -m bollettini.run_pipeline --force          # ignora cache, rigenera tutto
python -m bollettini.run_pipeline --query-only     # solo generazione dai chunk esistenti
```
Exit code: `0` = nuovi dati · `1` = niente di nuovo · `2` = errore.

## API
```
GET /v1/bollettini/culture/{coltura}/location?lat=<lat>&lng=<lng>
GET /v1/bollettini/health
```
Restituisce il report della coltura per la provincia che contiene il punto (Emilia-Romagna e Campania).

## Storage & dati runtime
**SQLite** (`data/chunks.db`, modulo `chunk_store.py`) — niente ChromaDB/embedding, retrieval per match
esatto sui metadati. I path runtime derivano da `paths.py` (`BOLLETTINI_RUNTIME_DIR`; in Docker il
volume è `/data/bollettini`). `data/**` non è versionato.

## Output
```
data/output_bollettini/{regione}/{coltura}/{province}_{DD-MM-YYYY}.md (+ .html)
```

## Documentazione
- **`CLAUDE.md`** — doc operativa (architettura, struttura, comandi).
- **`REPORT.md`** — doc tecnica completa (pipeline, prompt, validazione, integrazione, costi).
- **`CHANGELOG.md`** — storico modifiche (vedi la voce **2026-06** per la migrazione a SQLite + due prompt).
