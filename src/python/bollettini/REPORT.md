# RAG Colture — Documentazione Tecnica

**Target**: handoff per sviluppatore / collaboratore che integrerà o manterrà questo sistema, e baseline condivisa per gli aggiornamenti futuri.

**Ultima revisione**: 2026-06-15 (riscrittura completa dopo il refactor architetturale: SQLite al posto di ChromaDB, due prompt lean dedicati, tabella di monitoraggio deterministica, fix chunking Campania, OCR disattivato).
**Ultima rigenerazione output reale**: 2026-06-15 (deploy dei 115 report con i nuovi prompt).
**Posizione**: package `src/python/bollettini/` nel monorepo **tornatura** (`github.com/ifabfoundation/tornatura`, build **Pants**, deploy AWS). Nello stesso package vive l'integrazione di produzione: `api.py` (FastAPI), `scheduler.py` (APScheduler), `paths.py`, geopandas/shapefiles, `Dockerfile`.

> Dove codice e documentazione divergono, **fa fede il codice**.

---

## 1. Cosa fa il sistema

Pipeline automatica che trasforma i **bollettini fitosanitari in PDF** pubblicati dalle Regioni in **report strutturati per coltura** (Markdown + HTML), pronti per essere consultati da agronomi.

**Input** — PDF dei bollettini di:
- **Emilia-Romagna** — API REST Plone.
- **Campania** — scraping di pagine HTML statiche, una per provincia.

**Output** — per ogni coppia **(bollettino, coltura)** un file `.md` + `.html`, generato da un LLM (`gpt-4o-mini`).

**Pipeline a 3 fasi**: Download → Processing (PDF → chunk → store SQLite) → Query/Generazione (LLM).

**Principio guida del progetto**: *estrazione fedele* ("non possiamo sbagliare"). Il report deve **riportare tutto** ciò che la fonte dice per quella coltura, **senza perdere** dati operativi e **senza inventarne**. Per questo la generazione è seguita da un **pass di verifica/revisione** indipendente, e per la Campania la tabella di monitoraggio è inserita **deterministicamente** (non riscritta dall'LLM).

---

## 2. Stack tecnologico

| Componente | Tecnologia |
|---|---|
| Conversione PDF → Markdown | [Docling](https://github.com/DS4SD/docling) (`DocumentConverter`, `do_ocr=False`) |
| Storage chunk | **SQLite** (`modules/chunk_store.py`, file `data/chunks.db`) — niente embedding, niente vettori |
| Retrieval | **Match esatto sui metadati** (slice-by-coltura). NON c'è ricerca semantica/vettoriale |
| LLM generation | OpenAI `gpt-4o-mini` (`temperature=0`, `timeout=60s`, `max_retries=4`) |
| HTML rendering | Python `markdown` (estensioni `tables`, `fenced_code`) |
| Scraping | `requests` + `beautifulsoup4` |
| Orchestrazione | Python puro, zero framework |

> **Niente più ChromaDB né embedding.** Il retrieval di questo progetto è per match esatto su metadati (una coltura = un chunk): un vettoriale non serviva. ChromaDB e `sentence-transformers` sono stati **rimossi** (dalle dipendenze Pants e dal lockfile `bollettini.lock`). `ChunkStore` (SQLite, `sqlite3` è stdlib) ritorna la stessa forma di `ChromaDB.get()` (`{"documents":[...], "metadatas":[...]}`) per compatibilità coi consumatori.

> **OCR disattivato.** `_get_converter()` usa `PdfPipelineOptions(do_ocr=False)`. Su questi PDF (testo digitale) `do_ocr=True` e `do_ocr=False` producono output identico (≥99.9%), ma l'OCR è molto più lento; per riattivarlo basta rimettere `do_ocr=True`.

### Dipendenze (Pants)
Gestite via **Pants**: dichiarate in `3rdparty/python/bollettini-requirements.txt` (resolve `bollettini`), congelate nel lockfile `3rdparty/python/bollettini.lock`. Dopo una modifica: `pants generate-lockfiles --resolve=bollettini`. Principali:
```
openai · python-dotenv · requests · markdown · beautifulsoup4 · docling
fastapi · uvicorn · geopandas · shapely · APScheduler   # integrazione: api.py / scheduler.py
```
> `docling` traina dipendenze pesanti (torch, torchvision, onnxruntime, huggingface_hub, pillow): footprint di centinaia di MB, alcuni GB una volta impacchettato nel `.pex`. `torch` resta necessario (lo usa Docling) anche senza OCR. **Rimossi** `chromadb` e `sentence-transformers`.

---

## 3. Struttura del repository

```
src/python/bollettini/           # package nel monorepo tornatura
├── api.py                       # FastAPI: report per lat/lng (geopandas+shapefiles) → /v1/bollettini/...
├── scheduler.py                 # APScheduler: esegue la pipeline (giornaliera, 08:00 Europe/Rome)
├── run_pipeline.py              # ENTRY POINT pipeline (orchestratore 3 fasi)
├── paths.py                     # path runtime da BOLLETTINI_RUNTIME_DIR (DATA_DIR/OUTPUT_DIR/SHAPEFILE_DIR)
├── BUILD                        # target Pants (pex_binary: scheduler, api; resources)
├── requirements.txt             # mirror leggibile (la fonte per Pants è 3rdparty/python/bollettini-requirements.txt)
├── CLAUDE.md / REPORT.md / CHANGELOG.md   # documentazione
├── .env.example                 # il .env reale (OPENAI_API_KEY) è gitignorato
│
├── modules/
│   ├── config.py                # REGIONI, COLTURE (ER 5, Campania 17)
│   ├── chunk_store.py           # ChunkStore: store SQLite dei chunk (NO embedding)
│   ├── downloaders/base.py      # BaseDownloader (astratto)
│   ├── download_bollettini.py   # Downloader Emilia-Romagna (API Plone)
│   ├── download_campania.py     # Downloader Campania (scraping HTML, usa beautifulsoup4)
│   ├── process_bollettini.py    # PDF → Markdown → chunk → SQLite
│   └── colture.py               # Retrieval + generazione LLM → report MD/HTML
│
├── shapefiles/                  # province_italia.shp (usato dall'API), province_emilia_romagna.shp
│
└── data/                        # RUNTIME, NON in git (.gitignore) — deriva da BOLLETTINI_RUNTIME_DIR (paths.py)
    ├── input_bollettini/{emilia_romagna,campania}/   # PDF + cache_download.json
    ├── chunks.db                # ← STORE SQLITE (chunk + metadati)
    ├── cache/                   # processing_cache.json, colture_{regione}_processed.json
    └── output_bollettini/       # ← OUTPUT FINALE
        ├── emilia_romagna/      # 5 colture: vite pero pesco mais barbabietola
        └── campania/            # 17 colture: vite olivo pesco agrumi actinidia nocciolo
                                 #   noce cipolla pomodoro fragola castagno ciliegio melo
                                 #   pero patata susino albicocco
            └── {coltura}/{province_slug}_{DD-MM-YYYY}.md / .html  (+ history/{anno}/...)
```
> In Docker il volume runtime è `/data/bollettini` (`BOLLETTINI_RUNTIME_DIR`). Gli shapefile, invece, sono **risorse del package** (`shapefiles/`), non runtime.

---

## 4. Il dato di output

### 4.1 Convenzione filesystem
```
data/output_bollettini/{regione}/{coltura}/{province_slug}_{DD-MM-YYYY}.md (+ .html)
```
- `regione` ∈ `{emilia_romagna, campania}`.
- `coltura` (lowercase): ER → `vite, pero, pesco, mais, barbabietola`; Campania → 17 (vedi struttura).
- `province_slug` da `normalize_province_slug()` (lowercase, separatori → `_`, accenti rimossi). ER: `bologna_ferrara, forli_cesena_ravenna_rimini, modena, reggio_emilia, parma, piacenza`. Campania: `av, bn, ce, na, sa`.
- data in formato italiano `DD-MM-YYYY`.
- **Storico**: all'arrivo di un report più recente per la stessa (coltura, provincia), il precedente è spostato in `history/{anno}/{province_slug}/` da `move_to_history()`.

### 4.2 Struttura del Markdown — **due formati per regione**

A differenza delle versioni precedenti (che imponevano "5 sezioni fisse"), oggi i due `system prompt` sono **distinti** e usano sezioni **opzionali** (una sezione si **omette** del tutto se la fonte non ne parla — niente header vuoti, niente placeholder).

**Emilia-Romagna** (`SYSTEM_PROMPT`):
```
## Stato della coltura
## Avversità e difesa
   ### Malattie / Patogeni
   ### Insetti / Acari / Fitofagi
## Difesa obbligatoria e scadenze      (solo se c'è lotta obbligatoria/quarantena)
## Pratiche agronomiche                (rotazione, fertilizzazione, diserbo, ...)
## Vincoli e deroghe                   (limiti cumulativi, CS, deroghe con date)
## Note operative
```

**Campania** (`SYSTEM_PROMPT_CAMPANIA`):
```
## Stato della coltura
   ### Monitoraggio                    (tabella rilievi — INIETTATA dal codice, vedi §6)
## Avversità e difesa
   ### Malattie / ### Insetti/Acari
## Difesa obbligatoria                 (solo se citata: es. Xylella, flavescenza)
## Altre indicazioni                   (solo se presenti)
## Note operative
```

Il testo completo dei due prompt è in **§7**.

Casi "vuoti": se una coltura è **totalmente assente** dai chunk, **non si chiama l'LLM** → report statico `"Nessuna informazione specifica per {coltura} in questo bollettino."` (costo zero).

> **Fix di rendering post-LLM**: una regex inserisce una riga vuota tra un header e una tabella attaccata (alcuni renderer non parsano le tabelle senza riga vuota).

### 4.3 HTML
HTML standalone con CSS inline (`convert_md_to_html()`): servibile direttamente come `text/html`, oppure il client renderizza il `.md`.

### 4.4 Metadata dal filename
```
^(?P<province_slug>.+?)_(?P<day>\d{2})-(?P<month>\d{2})-(?P<year>\d{4})\.(md|html)$
```
Lato app, l'indice più solido è **scorrere il filesystem**: `(regione, coltura, province_slug, data) → path`.

---

## 5. Pipeline di esecuzione

```bash
python -m bollettini.run_pipeline [opzioni]
```

| Flag | Significato |
|---|---|
| (nessuno) | Pipeline completa, tutte le regioni, solo bollettini nuovi |
| `--regione emilia_romagna` \| `campania` | Solo la regione indicata |
| `--force` / `-f` | Ignora le cache e riprocessa/rigenera tutto |
| `--download-only` | Solo Fase 1 |
| `--query-only` | Solo Fase 3 (genera i report dai chunk già nello store; niente download/chunking) |
| `--verbose` / `-v` | DEBUG logging |

**Comando di deploy tipico** (rigenera i report dai chunk esistenti con i prompt correnti):
```bash
python -m bollettini.run_pipeline --query-only --force
```

**Exit code**: `0` nuovi dati · `1` niente di nuovo · `2` errore.

**Cadenza consigliata**: run giornaliera via cron. ~15–30 min in caso di rigenerazione completa (dominato dalle chiamate LLM: generazione + verifica per ~115 report); ~1 min se niente di nuovo.

---

## 6. Dettaglio tecnico fase per fase

### FASE 1 — Download

**Emilia-Romagna** (`download_bollettini.py`, `BollettiniDownloader`, standalone)
- API REST Plone. **4 slug di download** (raggruppamenti): `bologna-e-ferrara`, `forli-cesena-ravenna-rimini`, `modena-reggio-emilia`, `parma-piacenza`; sub-endpoint `/{slug}/@search` paginato.
- I PDF interni specificano **province concrete distinte** → nei filename/metadata si vedono 6 valori (Bologna-Ferrara, Forlì-Cesena-Ravenna-Rimini, Modena, Reggio Emilia, Parma, Piacenza), da cui i **30 report ER** (6 province × 5 colture).
- Fallback anno (solo 404, un anno indietro), quick-check/early-exit, rate-limit 2s. Cache: `…/emilia_romagna/cache_download.json`.

**Campania** (`download_campania.py`, `CampaniaDownloader`, estende `BaseDownloader`)
- Scraping di **5 pagine provinciali** `bollettini_{ANNO}/{XX}_{ANNO}.html`, `XX ∈ {AV, BN, CE, NA, SA}`. L'anno è assunto = anno corrente (nessun fallback). Cache: `…/campania/cache_download.json`.

### FASE 2 — Processing PDF → chunk → SQLite

`process_bollettini.py`. Per ogni PDF non in cache:

1. **Docling** PDF → Markdown in memoria (`do_ocr=False`).
2. **Chunking "slice-by-coltura"** (`create_chunks_from_markdown`) — **un chunk = una coltura intera**:
   - **ER**: `trim_pi_section()` (taglia la parte "Produzione Biologica") → `slice_markdown_by_coltura()` → `_merge_consecutive_same_coltura()`. Inoltre `slice_cross_cutting_sections()` estrae le sezioni **trasversali** ER (`CROSS_CUTTING_SECTIONS`): `DEROGHE AI DISCIPLINARI…` → `applies_to="PER_VOCE"`, `REVOCA PRODOTTI FITOSANITARI` → `applies_to=""`.
   - **Campania**: `preprocess_campania_markdown()` (vedi sotto) → `slice_markdown_by_coltura()` → `_merge_consecutive_same_coltura()`. **Niente sezioni trasversali** (la Campania non le ha).
   - `slice_markdown_by_coltura()` scorre gli header `## `: un header in `COLTURA_HEADER_TO_ID` apre un chunk che raccoglie tutto fino al confine successivo (altra coltura / *group divider* / fine doc). `COLTURA_HEADER_TO_ID` normalizza gli alias (`PESCO E NETTARINE → PESCO`, `GRANOTURCO → MAIS`); le colture non configurate sono mappate a `_ID` (consumano il flusso ma non vengono mai recuperate).
3. **Preprocessing Campania** (`preprocess_campania_markdown`) — normalizza gli header inconsistenti dei PDF provinciali, a più passate:
   - *Pre-pass A*: `## COLTURA` + nome sulla riga successiva → `## COLTURA <Nome>`. Riconosce il nome-coltura **iniziale** anche con suffisso tra parentesi (es. `AGRUMI (Arancio e mandarino)`) via `_leading_crop`.
   - *Passata 1*: confini dalle **tabelle di monitoraggio** (header con "Stadio") + `_extract_crop_from_context` (header / `VARIETA_TO_CROP` / `PATOGENO_TO_CROP`).
   - *Passata 1b*: tabelle "orfane" → coltura inferita da **patogeni univoci** (`PATOGENO_TO_CROP`, include i marcatori NOCE: *juglandis, mosca delle noci, …*).
   - *Passata 2*: inserisce header `## NOMECOLTURA` puliti e rimuove i `## COLTURA` ridondanti.
4. **Scrittura su SQLite** (`store.delete_doc(doc)` + `store.upsert_chunks(chunks)`). Metadati per chunk (`ChunkStore.META_FIELDS`):
   `doc_name, regione, data, province, numero_bollettino, tipo_documento, section_title, parent_coltura, applies_to`.
   (`numero_bollettino` è `""` per Campania; `parent_coltura` è il campo chiave del retrieval; `applies_to` valorizzato solo per le trasversali ER.)

> Niente più embedding, niente multi-collezione (`DISEASE_CONFIG` rimosso). `process_single_pdf(pdf, store)` fa solo delete+upsert.

### FASE 3 — Retrieval

`colture.py:_retrieve_coltura_chunks` — **match esatto sui metadati, niente similarity, niente keyword fallback**.
- **own_chunks** (blocchi propri della coltura):
  `section_matches(section_title, sezioni)` **OR** `parent_coltura == coltura_id`.
  `section_matches()` = match esatto o **prefisso con word boundary** (`"BARBABIETOLA DA ZUCCHERO"` matcha `"BARBABIETOLA"`; `"PEROXIDE"` no).
- **cross_chunks** (solo ER, arricchimento) per `applies_to`:
  - `"PER_VOCE"` (deroghe): `filter_deroghe_per_voce()` — filtro **deterministico** che spezza la sezione in voci (`"In data …"`) e tiene **solo** quelle che nominano la coltura (match per parola intera, mappa `DEROGA_TERMS`). Niente top-k, niente embedding.
  - `"ALL"` o coltura presente nella lista `applies_to`.
- **Gate anti-resurrezione**: le trasversali arricchiscono **solo** una coltura che ha già un blocco proprio nel bollettino. Coltura assente → ritorna vuoto → report statico (nessuna chiamata LLM).

### FASE 4 — Generazione + verifica

`colture.py:_generate_report`:
1. **Prompt per-regione**: `SYSTEM_PROMPT` (ER) o `SYSTEM_PROMPT_CAMPANIA`, + relativo `QUERY_TEMPLATE`. `gpt-4o-mini`, `temperature=0`.
2. `_fix_table_spacing` (rendering).
3. **Pass di verifica/revisione** (`_verify_and_revise`, 1 iterazione): un confronto indipendente FONTE↔REPORT (`VERIFY_PROMPT` / `VERIFY_PROMPT_CAMPANIA`) restituisce in JSON i **fatti mancanti** e le **affermazioni inventate**; se ce ne sono, `REVISE_PROMPT` rigenera integrando/correggendo. È la rete **anti-perdita + anti-allucinazione**.
4. **Campania — tabella di monitoraggio deterministica**: l'LLM **non** la scrive. `extract_campania_monitoring()` la estrae **verbatim** dalla fonte (parte prima di "CONSIGLI DI DIFESA"; prende il blocco-tabella con più righe-dati; `_normalize_md_table` aggiunge il separatore markdown se manca), poi `inject_monitoring()` la inserisce sotto `### Monitoraggio` in "## Stato della coltura" (rimuovendo qualsiasi tabella eventualmente prodotta dall'LLM). → tabella **sempre fedele**.
5. **Campania — strip della coda istituzionale**: `strip_campania_appendix()` rimuove (a monte, in retrieval) la coda che il chunker accoda all'ultima coltura: controlli/taratura attrezzature, AVVISI sostanze in scadenza, tabella **deroghe territoriali generali**, firma redazionale, data prossimo bollettino.
6. **Salvataggio** (`_save_markdown`): `.md` + `.html`, sposta il precedente in `history/`.

**Cache report**: `data/cache/colture_{regione}_processed.json` (`{doc_name}::{coltura_id}`). Salvata a fine batch.

---

## 7. I due system prompt (chiave dell'estrazione)

**Perché due prompt e non uno.** ER e Campania hanno contenuti **opposti**: l'ER è **quantitativo/regolatorio** (soglie, Max interventi, intervalli di sicurezza, limiti cumulativi, deroghe con date); la Campania è in gran parte **qualitativa** (consigli senza numeri). Un prompt unico è stato testato e **scartato**: l'enfasi ER su "preserva Max/intervalli/limiti" (necessaria al *recall* ER) induce `gpt-4o-mini` a **inventare** numeri/soglie sul contenuto qualitativo Campania. Quindi: due prompt dedicati, entrambi **struttura-first** (definiscono la struttura e pretendono fedeltà, senza "spingere" il contenuto: niente elenchi di malattie da cercare, niente campi obbligatori).

### 7.1 `SYSTEM_PROMPT` (Emilia-Romagna)
Filosofia: estrai TUTTO il crop-specifico, fedele, senza inventare; la lista dei *tipi di dato da conservare* (date, soglie, sostanze coi Max, limiti cumulativi, deroghe con date, accorgimenti) è una **rete anti-perdita** ("conserva **quando** presente"), non un obbligo di emetterli. Le sezioni **Difesa obbligatoria** e **Vincoli e deroghe** sono rinforzate per non comprimere il protocollo scafoideo e i limiti cumulativi ripetuti.

```text
Sei un redattore tecnico fitosanitario. Ricevi il testo di un bollettino
relativo a UNA coltura. Riorganizzalo nella struttura sotto, restando FEDELE: trasferisci TUTTE
le informazioni di QUELLA coltura cosi' come sono, senza perderne nessuna e senza aggiungerne.
Non riassumere; togli solo ripetizioni, intestazioni/pie' di pagina e frasi di collegamento.

PRINCIPIO — FEDELTA' TOTALE, NIENTE INVENZIONI:
- Riporta SOLO cio' che e' scritto nella fonte, ma riportalo TUTTO: se un dato non c'e', non
  scriverlo; se c'e', non perderlo.
- Conserva con precisione, QUANDO la fonte li riporta: date e scadenze; soglie di intervento
  (anche quantitative — ore di bagnatura, gradi-giorno, % — o diverse per varieta'); sostanze
  attive con i loro limiti (Max interventi, intervalli di sicurezza); i limiti CUMULATIVI per
  gruppo chimico o insieme di sostanze (es. "Tra gli SDHI Max 4", "Tra Ditianon e Captano Max
  16"); le sostanze candidate alla sostituzione (*); gli accorgimenti agronomici (es. taglio a
  una certa distanza dal sintomo, disinfezione attrezzi, fitotossicita'/distanziamenti); la
  salvaguardia delle api; le deroghe/usi eccezionali con le DATE e il loro significato esatto
  (distingui la data di CONCESSIONE da quella di SCADENZA/fine validita').
- NON imporre questi campi se la fonte non li contiene. Molte fonti (es. i bollettini Campania)
  danno consigli solo QUALITATIVI (es. "intervenire preventivamente con prodotti di copertura",
  senza numeri): riportali COSI' come sono. E' un ERRORE GRAVE aggiungere "Max interventi: N",
  "Intervallo di sicurezza: N giorni", soglie in % o qualsiasi altro numero quando la fonte NON
  lo riporta per quella voce: NON farlo MAI.
- Le TABELLE si COPIANO integralmente come tabelle markdown, riga per riga, senza aggiungerne,
  perderne o modificarne nessuna (es. tabelle rischio->prodotto, schemi di diserbo). UNICA
  ECCEZIONE: la tabella dei rilievi di monitoraggio in campo (colonne tipo Comune/Localita'/
  Varieta'/Stadio fenologico/Stato fitosanitario, tipica dei bollettini Campania) NON va
  riprodotta: viene inserita automaticamente.

STRUTTURA (usa questi titoli; OMETTI ogni sezione di cui la fonte non parla per questa coltura:
niente header vuoti, niente "nessuna indicazione"):

## Stato della coltura
Fase fenologica e situazione generale della coltura, se presenti.

## Avversita' e difesa
Una voce per ogni avversita' citata (malattia o insetto). Sotto ciascuna riporta FEDELMENTE cio'
che la fonte dice (stato, criteri agronomico/chimico/biologico, soglie, sostanze attive con i
loro limiti, accorgimenti), esattamente come scritto, senza inventarne e senza spostarli da
un'avversita' all'altra. Se la fonte raggruppa piu' agenti sotto un titolo, conservali TUTTI.
Suddividi in "### Malattie / Patogeni" (funghi, batteri, virus, fitoplasmi) e "### Insetti /
Acari / Fitofagi" (organismi animali).

## Difesa obbligatoria e scadenze
Solo se la fonte impone per QUESTA coltura misure di lotta OBBLIGATORIA / organismi da quarantena
(es. flavescenza dorata e il vettore scafoideo, colpo di fuoco, estirpi obbligatori). E' lotta
obbligatoria: riporta TUTTO il protocollo senza comprimere — organismo e riferimento normativo;
la SEQUENZA e il numero dei trattamenti con le DATE/finestre temporali esatte; le sostanze ammesse
coi relativi Max; le fasce di rispetto; le precondizioni; la salvaguardia delle api; gli estirpi.

## Pratiche agronomiche
Solo se la fonte da' indicazioni agronomiche per QUESTA coltura: successione/rotazione,
fertilizzazione, diserbo (lista COMPLETA delle sostanze erbicide come da documento, coi gruppi
chimico/HRAC se indicati), irrigazione/gestione del suolo, cautele operative.

## Vincoli e deroghe
Solo se citati per QUESTA coltura:
- limiti annuali e CUMULATIVI per gruppo chimico o sostanza: riportali TUTTI (es. "Tra gli SDHI
  Max 4", "Tra gli IBE Max 6", "Tra Ditianon e Captano Max 16", "Tra Fosetil Al e Fosfonato di K
  Max 10", tetti tipo "max 3 interventi insetticidi/anno"). Se la fonte li RIPETE piu' volte,
  raccoglili UNA sola volta ma senza ometterne NESSUNO;
- sostanze candidate alla sostituzione (*);
- deroghe/usi eccezionali con prodotto + sostanza attiva + DATE (concessione e scadenza, distinte).

## Note operative
2-4 azioni prioritarie della settimana, in bullet di una riga (richiami sintetici).

REGOLE
- Una sola coltura: ignora ogni riferimento ad ALTRE colture e le regole generali NON riferite a
  questa coltura.
- Fedelta' assoluta: nessuna invenzione e nessuna perdita. Niente placeholder ([N/A],
  [da verificare], [non specificato]): ometti la voce.
- Ogni avversita' compare UNA sola volta (Malattie OPPURE Insetti). Un organismo a lotta
  obbligatoria: stato in "Avversita' e difesa", protocollo in "Difesa obbligatoria e scadenze".
- Se la fonte non ha informazioni su questa coltura, scrivi un solo paragrafo: "Nessuna
  informazione specifica per questa coltura in questo bollettino." e ometti le sezioni.
```

### 7.2 `SYSTEM_PROMPT_CAMPANIA`
Filosofia: la Campania è qualitativa → il prompt **vieta** l'invenzione di numeri/soglie/Max. La tabella di monitoraggio NON la scrive l'LLM (iniettata dal codice, §6).

```text
Sei un redattore tecnico fitosanitario. Ricevi il testo di un
bollettino relativo a UNA coltura. Riorganizzalo nella struttura indicata sotto, restando
FEDELE: trasferisci le informazioni cosi' come sono, senza aggiungere e senza perdere nulla.
Non riassumere; togli solo ripetizioni, intestazioni/pie' di pagina e frasi di collegamento.

PRINCIPIO (il piu' importante): riporta SOLO cio' che e' scritto nella fonte. Non aggiungere
campi, numeri, soglie, sostanze, date, livelli di rischio o consigli che la fonte non contiene.
Se la fonte e' qualitativa, resta qualitativo. Se un dato non c'e', non scriverlo. Le TABELLE si
COPIANO integralmente come tabelle markdown, riga per riga, senza aggiungerne, perderne o
modificarne nessuna.

STRUTTURA (usa questi titoli; OMETTI ogni sezione di cui la fonte non parla: niente header
vuoti, niente "nessuna indicazione"):

## Stato della coltura
Riporta eventuali note testuali sulla fase fenologica o sulla situazione generale presenti nella
fonte. NON riprodurre qui la tabella dei rilievi di monitoraggio: viene inserita automaticamente
sotto un sotto-titolo "### Monitoraggio". Se non ci sono note testuali oltre alla tabella, scrivi
solo l'header della sezione.

## Avversita' e difesa
Una voce per ogni avversita' citata. Sotto ciascuna, riporta FEDELMENTE cio' che la fonte dice:
stato, criteri di difesa (agronomico/chimico/biologico), soglie, sostanze attive, campionamenti,
accorgimenti, limiti -- esattamente come scritti, senza inventarne e senza spostarli da
un'avversita' all'altra. Se la fonte raggruppa piu' agenti/avversita' sotto un titolo,
conservali TUTTI. Puoi suddividere in "### Malattie" e "### Insetti/Acari".

## Difesa obbligatoria
Solo se la fonte cita obblighi di legge, lotta obbligatoria o organismi da quarantena:
organismo, azione richiesta, riferimenti/scadenze citati.

## Altre indicazioni
Solo se presenti nella fonte: pratiche agronomiche generali, vincoli annuali/cumulativi,
deroghe/usi eccezionali con le loro date esatte. Riportale come sono.

## Note operative
2-4 azioni prioritarie della settimana, bullet di una riga (richiami sintetici).

REGOLE
- Una sola coltura: ignora ogni riferimento ad altre colture.
- Fedelta' assoluta: nessuna invenzione (vedi PRINCIPIO). Niente placeholder ([N/A],
  [da verificare], [non specificato]) e niente frasi tipo "non sono previsti / non specificato":
  se manca, OMETTI la voce o la sezione.
- Classifica: funghi/batteri/virus/fitoplasmi = malattie; organismi animali = insetti/acari.
- Se la fonte non ha informazioni sulla coltura, scrivi un solo paragrafo: "Nessuna informazione
  specifica per questa coltura in questo bollettino."
```

Esiste anche un `VERIFY_PROMPT` / `VERIFY_PROMPT_CAMPANIA` (per il pass di verifica) e un `REVISE_PROMPT` condiviso (per la revisione).

---

## 8. Ambiente / Secrets / Setup

`.env`: `OPENAI_API_KEY=sk-...` (obbligatoria; in produzione fornita come secret, è gitignorata).

**Sviluppo (Pants, su Linux):**
```bash
pants generate-lockfiles --resolve=bollettini    # solo se cambiano le dipendenze
pants check ::                                    # coerenza dei target
pants package src/python/bollettini:scheduler src/python/bollettini:api   # build dei .pex
python -m bollettini.run_pipeline --query-only --force   # esecuzione locale della pipeline
```
**Produzione:** scheduler e API girano dai `.pex` nell'immagine Docker (`src/docker/bollettini`); i path runtime derivano da `BOLLETTINI_RUNTIME_DIR` (volume `/data/bollettini`). `data/chunks.db` viene creato automaticamente al primo processing.

Dipendenze di rete: `agricoltura.regione.emilia-romagna.it`, `agricoltura.regione.campania.it`, `api.openai.com`.

---

## 9. Punti di integrazione per l'applicazione

**A — API HTTP (`api.py`, già in produzione)** — FastAPI servita da `uvicorn` (default porta 8080):
```
GET /v1/bollettini/health
GET /v1/bollettini/culture/{coltura}/location?lat=<lat>&lng=<lng>
```
Il punto lat/lng è risolto a provincia/regione via geopandas + `shapefiles/province_italia.shp` (copre ER **e** Campania), poi restituisce in JSON il report `.md` più recente per (coltura, provincia), letto da `OUTPUT_DIR`.

**B — File MD/HTML dal filesystem**: scorrere `OUTPUT_DIR`; `latest` = unico file `{province_slug}_*.md` nella cartella coltura, lo storico è in `history/`.

**C — Webhook**: agganciare dopo `_save_markdown()` o a fine `run_pipeline.py`.

**Elenco bollettini disponibili** (da SQLite):
```python
from bollettini import paths
from bollettini.modules.chunk_store import ChunkStore
s = ChunkStore(str(paths.DATA_DIR / "chunks.db"))
s.get_all("emilia_romagna")   # {"documents":[...], "metadatas":[...]} — aggregare per doc_name
s.distinct_docs()             # lista doc_name
```

---

## 10. Costi operativi (OpenAI)

`gpt-4o-mini` (tariffe 2026: $0.15/1M input, $0.60/1M output). Per report: **2 chiamate** (generazione + verifica), **3** se la verifica trova qualcosa da correggere (revisione).

| Scenario | Report | Ordine di grandezza |
|---|---|---|
| Rigenerazione completa ER (`--query-only --force --regione emilia_romagna`) | 30 | pochi centesimi |
| Rigenerazione completa Campania | 85 | ~$0.1 |
| Rigenerazione totale ER+CA | **115** | ~$0.1–0.2 |

Le colture assenti non chiamano l'LLM (report statico).

---

## 11. Stato runtime di riferimento

I dati runtime (`data/`: `chunks.db`, PDF, report) **non sono versionati** (`.gitignore`): la pipeline li produce nel volume `BOLLETTINI_RUNTIME_DIR`. Valori di riferimento dall'ultima esecuzione completa validata (standalone, 2026-06-15, bollettini di giugno):
- **Store** SQLite: ~**500 chunk**, ~35 `doc_name` distinti (ER + Campania).
- **Output**: **115 report** correnti (30 ER + 85 Campania), `.md` + `.html`; i precedenti in `history/`.
- Campania: i bollettini più recenti (10-06-2026, AV/BN/CE/NA/SA) sono ri-chunkati col fix del preprocess; i più vecchi hanno il chunking precedente e alimentano solo lo storico (vedi §13).

---

## 12. Validazione qualità (2026-06-15)

Metodo: snapshot in `test/` (fonte recuperata + report generato per le **colture-progetto**), valutati da **grader agronomici indipendenti** su recall (fatti catturati/totali), fedeltà tabelle, avversità raggruppate, **numeri inventati**.

- **Campania** (colture-progetto VITE/PERO/PESCO/OLIVO/AGRUMI/ALBICOCCO su NA/SA/AV/CE): **0 gravi**, 0 fabbricazioni, tabelle di monitoraggio fedeli (deterministiche). Residui minori: una mis-attribuzione di campionamento (CE PESCO), un paio di etichette imprecise.
- **Emilia-Romagna** (VITE/PERO/PESCO/MAIS/BARBABIETOLA su 3 bollettini/2 province): **0 gravi**; precisione ottima (nessun valore regolatorio inventato); limiti cumulativi e deroghe con date preservati. Residuo: per la VITE il *dettaglio* della strategia scafoideo (composizione 1°/2° trattamento, fasce di rispetto, date d'emergenza) viene a volte compresso (verdict *moderata*).

Gli artefatti di validazione e i grader sono in `test/` (`snapshot_er.py`, `snapshot_campania.py`, `grade_*.json`).

---

## 13. Caveat e limiti noti

1. **Due regioni, due prompt**: l'unificazione è stata testata e scartata (vedi §7). Modifiche al prompt vanno fatte e validate **per regione**.
2. **Format Campania fragile**: gli header dei PDF provinciali sono inconsistenti; `preprocess_campania_markdown` li normalizza con euristiche (header + varietà + patogeni univoci). Un formato nuovo può far fallire la segmentazione → aggiornare `CROP_NAMES`/`VARIETA_TO_CROP`/`PATOGENO_TO_CROP`.
3. **Salvaguardia api (ER)**: è una regola **generale** (L.R. 2/2019), non specifica della coltura → per scelta di progetto ("niente sezioni non-crop") **non** viene riportata nei report. È legale/safety-critical: se la si vuole reintrodurre, è una decisione di prodotto.
4. **Storico Campania**: i bollettini più vecchi nello store hanno il chunking pre-fix; per riallinearli serve un reprocessing completo (`--regione campania --force`).
5. **Solo l'ultimo bollettino per provincia** viene rigenerato; i precedenti restano in `history/`.
6. **Determinismo LLM**: `temperature=0` è stabile ma non bit-perfect.

---

## 14. Debito tecnico / disallineamenti residui

- Commento header sopra `SYSTEM_PROMPT` in `colture.py` dice ancora "ER + Campania" (residuo del tentativo di unificazione) → è solo ER; da correggere.
- `colture.py`: `looks_like_coltura_heading()` / `is_other_coltura_section()` e le `keywords` di `config.py` restano **dead code** (l'anti-contaminazione è garantita dal chunking). Rimuovibili dopo verifica.
- Riferimenti residui a "ChromaDB/embeddings" in alcuni docstring/commenti/log (es. `process_bollettini.py`, `run_pipeline.py`) sono **obsoleti**: il codice non importa più ChromaDB (rimossa da dipendenze e lockfile). Da ripulire.
- `test/` contiene molti script di lavoro/validazione (snapshot, reprocess, grader, trace): da ripulire/archiviare.
- VITE scafoideo: residuo di compressione del protocollo obbligatorio (vedi §12) — eventuale ulteriore rinforzo del prompt.

---

## 15. Come aggiungere / modificare una coltura

1. `modules/config.py`: aggiungere la voce a `COLTURE` (con `nome`, `sezioni`) e l'ID alla lista `colture` della regione in `REGIONI`.
2. `modules/process_bollettini.py` (perché lo **slicing** la riconosca):
   - aggiungere l'header a `COLTURA_HEADER_TO_ID` (+ alias);
   - per Campania: aggiornare `CROP_NAMES` e, se serve, `VARIETA_TO_CROP` / `PATOGENO_TO_CROP`.
3. Rigenerare:
   ```bash
   # se cambia solo la generazione (chunk già corretti):
   python -m bollettini.run_pipeline --regione <reg> --query-only --force
   # se cambia lo slicing/preprocess (serve ri-chunkare):
   python -m bollettini.run_pipeline --regione <reg> --force
   ```

---

## 16. Troubleshooting rapido

| Sintomo | Causa probabile | Fix |
|---|---|---|
| Report vuoto nonostante coltura nel PDF | header non coperto da `COLTURA_HEADER_TO_ID`/`sezioni`, o preprocess Campania non ha segmentato | aggiungere variante header; verificare `parent_coltura` nei chunk |
| Coltura X contaminata da coltura Y (Campania) | confine di sezione non rilevato | aggiungere marcatori univoci a `PATOGENO_TO_CROP`/`VARIETA_TO_CROP` o gestire l'header `## COLTURA` |
| Numeri/soglie inventati in un report Campania | prompt/verifica non hanno bloccato l'invenzione | è un bug: la fonte è qualitativa → rafforzare il `PRINCIPIO` del prompt Campania |
| Doppia tabella di monitoraggio | `inject_monitoring` + tabella prodotta dall'LLM | già gestito (lo strip rimuove quella dell'LLM); verificare `inject_monitoring` |
| `ImportError: docling` | resolve non costruito | `pants generate-lockfiles --resolve=bollettini` poi `pants package …` |
| "Nessun bollettino disponibile" | store vuoto o `regione` mancante | rifare il processing (`--force`) |

---

## 17. File chiave (in ordine di lettura)

1. `run_pipeline.py` — orchestrazione, flag, exit code.
2. `modules/config.py` — `REGIONI`, `COLTURE`.
3. `modules/colture.py` — **core query**: `SYSTEM_PROMPT` / `SYSTEM_PROMPT_CAMPANIA` / `VERIFY_*` / `REVISE_PROMPT`; `_retrieve_coltura_chunks` (own + cross-cutting + gate); `filter_deroghe_per_voce`; `extract_campania_monitoring` / `inject_monitoring`; `strip_campania_appendix`; `_generate_report` / `_verify_and_revise`.
4. `modules/process_bollettini.py` — **core ingest**: `slice_markdown_by_coltura`, `COLTURA_HEADER_TO_ID`, `GROUP_DIVIDERS`, `CROSS_CUTTING_SECTIONS`, `trim_pi_section`, `preprocess_campania_markdown` (`_leading_crop`, `VARIETA_TO_CROP`, `PATOGENO_TO_CROP`), `process_single_pdf`.
5. `modules/chunk_store.py` — `ChunkStore` (SQLite), `META_FIELDS`.
6. `modules/download_bollettini.py` (ER) e `modules/download_campania.py` (estende `downloaders/base.py`).
7. **Integrazione di produzione** (non parte del core RAG): `api.py` (FastAPI, lat/lng→report), `scheduler.py` (APScheduler), `paths.py` (path runtime), `BUILD` (target Pants), `shapefiles/`, `Dockerfile`.
