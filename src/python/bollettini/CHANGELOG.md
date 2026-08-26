# Changelog - RAG Bollettini

Registro delle modifiche per il team backend.

---

## [2026-08-26] - MELO in Emilia-Romagna + tre fix di fedelta' del contenuto

### Overview per il team
Allineamento del package allo standalone `RAG_colture` alla data del 2026-08-25. Aggiunge **MELO**
come sesta coltura ER e porta tre correzioni che riguardano la **fedelta' del report alla fonte**
(non la struttura). Modifiche **additive**: nessuna firma cambiata, nessun endpoint nuovo,
`api.py` / `scheduler.py` / `run_pipeline.py` / geopandas / Docker **intatti**.

### Cosa cambia
1. **MELO, sesta coltura ER** (`modules/config.py`). I chunk erano **gia' nello store**
   (`parent_coltura='MELO'`, header `## MELO` negli ultimi bollettini delle 6 province): non serve
   ri-processare i PDF. Le 21 keyword includono le avversita' specifiche ER (colpo di fuoco
   batterico/*Erwinia amylovora*, glomerella/*Colletotrichum*, afide lanigero/*Eriosoma lanigerum*,
   carpocapsa, cemiostoma, litocollete, eulia). Report ER: da 30 a **36** (6 province x 6 colture).
   In `DEROGA_TERMS` il melo ha il solo termine `'melo'`: nelle deroghe ER convivono `'melone'` e
   `'meloidogyne'`, che il match **per parola intera** esclude correttamente.
2. **Chunking ER: recupero delle colture che Docling non emette come header**
   (`modules/process_bollettini.py`, `promote_plaintext_coltura_headers`). Su alcuni PDF il nome
   della coltura compare come **paragrafo di testo** invece che come `## NOME`: `slice_markdown_by_coltura`
   non apre un nuovo chunk e il blocco viene **assorbito nella coltura precedente** (report vuoto per
   la coltura assorbita, report contaminato per quella che assorbe; osservato: il chunk CILIEGIO di
   Modena n.12 da 22k caratteri inghiottiva KAKI, MELO, OLIVO e PERO). Promozione **deterministica**
   con cinque regole strette, la piu' importante delle quali e' *tutta maiuscola*: nei bollettini
   invernali esistono elenchi in Title Case (`Melo` + `: bottoni rosa`) che sono **voci di lista**, non
   sezioni-coltura. Righe di tabella e artefatti Docling sempre esclusi.
3. **Deroghe: pruning delle clausole di altre colture** (`modules/colture.py`,
   `_prune_clausole_altre_colture`). Alcune voci-deroga sono **elenchi multi-coltura** e consegnarle
   intere all'LLM faceva **mis-attribuire i limiti** delle altre colture (osservato in produzione: 3
   report PESCO su 6 riportavano un `"effettuare massimo 1 trattamento"` che nella fonte e' di
   ciliegio/kaki/actinidia/pomodoro). Ora si tiene il preambolo **verbatim** (prodotto, sostanza
   attiva, date di validita') e le sole clausole la cui **etichetta** nomina la coltura; le clausole
   **senza** etichetta-coltura non vengono mai scartate (es. `"margaronia (…) sulla coltura
   dell'olivo"`) e restano a carico del prompt. Se non c'e' nulla da togliere, la voce e' ritornata
   **byte-identica**.
4. **Prompt ER: esempi numerici sostituiti da schemi** (`modules/colture.py`, 3 punti). I limiti
   cumulativi erano illustrati con **valori concreti** (`"Tra gli SDHI Max 4"`, `"Tra Ditianon e
   Captano Max 16"`, …): l'LLM li riportava anche quando la fonte non li conteneva. Ora il prompt usa
   **segnaposto** (`"Tra i <gruppo chimico> Max <numero>"`) e dichiara esplicitamente che sono schemi
   di riconoscimento, non dati, e che non vanno mai riportati. Anti-allucinazione, nessun cambio di
   struttura del report.
5. **Chiave OpenAI: una sola fonte, fuori dal repo** (`modules/config.py`, `modules/colture.py`).
   Al posto di `load_dotenv()` su un `.env` di package, `load_openai_key()` cerca la chiave in ordine:
   variabile d'ambiente, poi i file-chiave nella **home** (`~/.config/openai/key.env`). Verifica i
   permessi del file e **avvisa** se una chiave viene trovata dentro il repository. Complementare alla
   rimozione di `.env` dalle `resources()` del BUILD (vedi voce precedente): i segreti si passano ai
   container dall'esterno (`env_file` nel compose), non dentro l'immagine.

### Verifica eseguita
- I tre moduli toccati differiscono dallo standalone **solo** per l'adattamento monorepo
  (`from bollettini.modules.*`, `paths.DATA_DIR` / `paths.OUTPUT_DIR`); `config.py` e' byte-identico.
- `promote_plaintext_coltura_headers`: output **identico** a quello dello standalone su **405**
  markdown reali (0 differenze). Sui 9 `raw*.md` di test recupera 4 sezioni-coltura reali
  (SOIA, VITE, POMODORO DA INDUSTRIA, MAIS), tutte verificate come sezioni autentiche.
- `_prune_clausole_altre_colture`: preambolo verbatim, clausola della coltura tenuta, clausole di
  ciliegio/kaki scartate, clausola senza etichetta tenuta, voce senza marcatore ritornata byte-identica.
- `MELO` non intercetta `'melone'` ne' `'meloidogyne'`; nessun esempio numerico concreto residuo nei prompt.
- `pants package src/python/bollettini:scheduler src/python/bollettini:api` → **exit 0**.

### Nota
`black` e `isort` falliscono su **tutto** il package `bollettini` (11 file, inclusi `api.py` e
`chunk_store.py`, mai toccati qui): e' **preesistente** e identico su `main`. Non e' stato lanciato
`pants fmt`, che avrebbe riformattato l'intero package mescolando la formattazione con queste
modifiche. La formattazione va concordata come intervento a se'.

---

## [2026-06-24] - Migrazione a SQLite + due prompt dedicati + Campania completa

### Overview per il team
Allineamento del package `bollettini` alla versione avanzata e **validata** dello standalone
RAG_colture. Cambia il motore di retrieval/generazione (niente più ChromaDB) e si amplia la
Campania. **L'integrazione di produzione resta intatta** (api/scheduler/run_pipeline/geopandas/Docker).

### Cosa cambia
1. **Storage: da ChromaDB a SQLite.** Rimossi ChromaDB ed embeddings (`sentence-transformers`): il
   retrieval è per **match esatto sui metadati** (una coltura = un chunk), un vettoriale non serviva.
   Nuovo `modules/chunk_store.py` (`ChunkStore`, solo `sqlite3` stdlib, file `data/chunks.db`); ritorna
   la stessa forma di `ChromaDB.get()` per compatibilità coi consumatori.
2. **Due system prompt per regione** (`SYSTEM_PROMPT` ER quantitativo/regolatorio,
   `SYSTEM_PROMPT_CAMPANIA` qualitativo). Il prompt unico era stato testato e scartato (su Campania
   induceva l'invenzione di numeri). **Non vanno ri-unificati.**
3. **Pass di verifica/revisione** indipendente dopo la generazione (`VERIFY_PROMPT`/`REVISE_PROMPT`):
   recupera i fatti mancanti e rimuove le affermazioni inventate (anti-perdita + anti-allucinazione).
4. **Campania:** tabella di monitoraggio **iniettata deterministicamente** dal codice
   (`extract_campania_monitoring`/`inject_monitoring`), non scritta dall'LLM; coda istituzionale
   rimossa (`strip_campania_appendix`); fix del chunking (`preprocess_campania_markdown`).
5. **ER:** deroghe filtrate **per-voce** (`filter_deroghe_per_voce`, deterministico).
6. **Colture Campania: da 11 a 17** (`config.py`): aggiunte NOCE, CIPOLLA, FRAGOLA, PATATA, ALBICOCCO,
   PERO. Modifica **additiva**: `api.py` itera su `COLTURE` in modo generico, non si rompe.
7. **OCR disattivato** (`do_ocr=False`) in Docling: su questi PDF (testo nativo) l'output è identico
   ed è più veloce.
8. **`api.py` — report Campania servibili per posizione.** `_shapefile_candidates` ora preferisce
   `province_italia.shp` (tutta Italia, 107 province) invece di `province_emilia_romagna.shp` (solo 9
   province ER): un lat/lng in Campania prima dava **404**. Verificato: Napoli/Salerno/Avellino →
   `region_id=campania`, Bologna/Parma → `emilia_romagna`. **Una sola riga** cambiata in `api.py`.

### Dipendenze (Pants)
- Rimossi `chromadb` e `sentence-transformers` da `3rdparty/python/bollettini-requirements.txt`, da
  `src/python/bollettini/requirements.txt` e dalla dep-list di `src/python/bollettini/BUILD`.
- **DA FARE prima del merge:** rigenerare il lockfile → `pants generate-lockfiles --resolve=bollettini`
  (gira su Linux/CI, non su Windows). `docling`/`torch` restano (necessari a Docling).
- **Dichiarare `beautifulsoup4`**: è importata da `modules/download_campania.py` (scraping HTML) ma
  NON era elencata in `bollettini-requirements.txt` (lo standalone la dichiara). Aggiungerla alla
  rigenerazione del lockfile, altrimenti il download Campania fallisce ("beautifulsoup4 richiesto").
- `.gitignore`: ora ignora `data/chunks.db`.

### Invariato (integrazione di produzione)
`scheduler.py`, `run_pipeline.py`, la logica di `api.py` (a parte l'ordine degli shapefile), geopandas
e gli shapefile, il `Dockerfile` (solo più leggero senza ChromaDB). I path passano sempre da `paths.py`
(`chunks.db` vive in `paths.DATA_DIR`, quindi nel volume runtime).

### Validazione
- Run completo dello standalone su bollettini freschi (giugno): 115 report, **0 errori gravi**.
- Package portato: test di cablaggio + campione end-to-end sotto il layout tornatura OK.
- Geo-lookup verificato per Campania ed Emilia-Romagna.

### Note ambiente (solo Windows, non bug)
- Emoji nei messaggi di log → errore di logging su console cp1252: impostare `PYTHONUTF8=1` nei run
  Windows (su Linux/AWS non accade).
- Docling `std::bad_alloc` sulle pagine alte di PDF molto lunghi (memoria): dimensionare bene il
  container; il contenuto-coltura non è impattato (pagine della Produzione Biologica, comunque scartate).

---

## [2026-03-10] - Transfer Package v2.0 - Riepilogo Completo Aggiornamenti

### Overview per il Backend Developer

Questo e' il secondo trasferimento del package RAG Bollettini. Rispetto alla versione precedente (v1.0, 21 Gennaio 2026), sono state apportate le seguenti modifiche.

### Riepilogo di TUTTI i cambiamenti dalla v1.0

#### 1. Organizzazione PDF per anno (download_bollettini.py)
- **Prima**: tutti i PDF venivano salvati in `data/1_collections/bollettini/` in un'unica cartella piatta
- **Dopo**: i PDF vengono salvati in sottocartelle per anno: `data/1_collections/bollettini/2025/`, `data/1_collections/bollettini/2026/`, ecc.
- **Nota**: i PDF del 2026 scaricati prima di questa modifica sono rimasti nella cartella root (non spostati automaticamente). Nuovi download vanno nella cartella dell'anno corretto.

#### 2. Fix ricerca ultimo bollettino per provincia (cimice.py, flavescenza.py)
- **Prima**: il confronto tra bollettini usava `numero_bollettino` (intero). Questo causava problemi al cambio anno, perche' il bollettino N.1 del 2026 era considerato piu' vecchio del N.30 del 2025.
- **Dopo**: il confronto usa il campo `data` (formato `YYYY-MM-DD`), che e' univoco e ordinabile correttamente anche tra anni diversi.

#### 3. Gestione bollettini invernali senza dati (cimice.py)
- **Prima**: se un bollettino non conteneva chunks con keyword cimice, il modulo restituiva `None` e non generava report.
- **Dopo**: viene generato un report con messaggio "Periodo di svernamento - nessuna attivita' cimice rilevata". Questo evita gap nei report durante i mesi invernali (gen-apr).

#### 4. Ristrutturazione prompt flavescenza (flavescenza.py)
- **Prima**: il prompt LLM mescolava dati bollettino e normativa in un unico flusso, con lista numerata di 11 punti di estrazione.
- **Dopo**: il report ha ora **DUE PARTI distinte**:
  - **PARTE 1 - DAL BOLLETTINO**: riporta SOLO le informazioni trovate nel bollettino provinciale (monitoraggio, indicazioni operative, deroghe). Se non ci sono info, lo dichiara esplicitamente invece di generare placeholder.
  - **PARTE 2 - DALLA NORMATIVA**: riporta le disposizioni dalla Determinazione Regionale (trattamenti, prodotti, zone delimitate, sanzioni).
- La sezione "Deroghe" e' ora opzionale (omessa se assente nel bollettino).
- Rimosso il rounding nella query: query piu' concisa e strutturata.

#### 5. Fix glob PDF in process_bollettini.py
- **Prima**: `INPUT_DIR.glob("*.pdf")` cercava PDF solo nella root della cartella bollettini.
- **Dopo**: `INPUT_DIR.glob("*/*.pdf")` cerca PDF nelle sottocartelle anno (coerente con la nuova organizzazione per anno).

#### 6. Nuovi file di test (modules/tests/)
- Aggiunti test per debug/sviluppo (NON necessari per produzione):
  - `test_chunking_bologna.py` - Test chunking specifico Bologna
  - `test_chunking_flavescenza.py` - Test chunking flavescenza
  - `test_multi_bollettini_flavescenza.py` - Test multi-bollettino
  - `test_pipeline_cimice.py` - Test pipeline cimice

### File MODIFICATI rispetto alla v1.0

| File | Tipo Modifica | Descrizione |
|------|--------------|-------------|
| `modules/download_bollettini.py` | MODIFICATO | Salvataggio PDF in sottocartelle per anno |
| `modules/process_bollettini.py` | MODIFICATO | Glob `*/*.pdf` per trovare PDF nelle sottocartelle anno |
| `modules/cimice.py` | MODIFICATO | Confronto per data, gestione bollettini invernali vuoti |
| `modules/flavescenza.py` | MODIFICATO | Confronto per data, prompt ristrutturato in 2 parti |
| `modules/normativa_flavescenza.py` | INVARIATO | Nessuna modifica |
| `run_pipeline.py` | INVARIATO | Nessuna modifica |
| `scheduler.py` | INVARIATO | Nessuna modifica |
| `requirements.txt` | INVARIATO | Nessuna modifica |

### File NUOVI rispetto alla v1.0

| File | Descrizione |
|------|-------------|
| `modules/tests/*.py` | Test di debug/sviluppo (4 file) |
| `CHANGELOG.md` | Questo file - registro modifiche |

### Dati aggiornati

- **PDF bollettini 2025**: 181 file (in `data/1_collections/bollettini/2025/`)
- **PDF bollettini 2026**: 24 file nuovi (in `data/1_collections/bollettini/2026/` + 20 nella root)
- **ChromaDB**: aggiornato con tutti i bollettini 2025 e 2026 indicizzati

### Impatto sul Backend

Se il backend aveva gia' integrato la v1.0:
1. **Nessuna modifica all'interfaccia CLI**: `run_pipeline.py` e `scheduler.py` funzionano esattamente come prima
2. **Output report identico formato**: stessa struttura `{provincia}_{DD-MM-YYYY}.md` nelle stesse cartelle
3. **Report flavescenza piu' leggibili**: la separazione bollettino/normativa facilita il parsing se il backend estrae dati dai report
4. **Report invernali cimice**: ora vengono generati anche in inverno (prima erano assenti)
5. **requirements.txt invariato**: nessuna nuova dipendenza

---
