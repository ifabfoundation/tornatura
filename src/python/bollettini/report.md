# RAG Colture — Documentazione Tecnica

**Target**: handoff per sviluppatore back-end / front-end che integrerà questo sistema in un'applicazione web per agronomi.

**Ultima revisione**: 20 aprile 2026
**Repository**: `/home/vito/projects/tornatura/RAG_colture/`

---

## 1. Cosa fa il sistema

Pipeline automatica che trasforma **bollettini fitosanitari in PDF** pubblicati dalle Regioni in **report strutturati per coltura** (Markdown + HTML), pronti per essere consultati da agronomi.

**Input**: PDF dei bollettini fitosanitari (settimanali/bisettimanali) pubblicati da:
- Regione Emilia-Romagna (API REST Plone)
- Regione Campania (scraping HTML)

**Output**: per ogni coppia **(bollettino, coltura)** un file `.md` + `.html` con:
- Fase fenologica
- Avversità (malattie, insetti)
- Trattamenti consigliati (prodotto, dose max, condizioni)
- Note operative

**Pipeline a 3 fasi**: Download → Processing (PDF→chunks→ChromaDB) → Query RAG (GPT-4o-mini).

---

## 2. Stack tecnologico

| Componente | Tecnologia |
|---|---|
| Conversione PDF → Markdown | [Docling](https://github.com/DS4SD/docling) + [RapidOCR](https://github.com/RapidAI/RapidOCR) (solo Campania, scansioni) |
| Embedding (non usati per retrieval, solo storage) | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dim) |
| Vector DB | [ChromaDB](https://www.trychroma.com/) persistente su filesystem |
| LLM generation | OpenAI `gpt-4o-mini` (temperature=0) |
| HTML rendering | Python `markdown` lib |
| Scraping | `requests` + `beautifulsoup4` |
| Orchestrazione | Python puro, zero framework |

### Dipendenze (`requirements.txt`)
```
openai
chromadb
python-dotenv
requests
markdown
sentence-transformers
beautifulsoup4
```
Docling è trascinato transitivamente (installato separatamente se serve: `pip install docling`).

---

## 3. Struttura del repository

```
RAG_colture/
├── run_pipeline.py              # ENTRY POINT principale (orchestratore)
├── requirements.txt
├── CLAUDE.md                    # doc operativa
├── report.md                    # questo documento
├── .env                         # secrets (OPENAI_API_KEY)
│
├── modules/
│   ├── config.py                # REGIONI, COLTURE (sezioni + keywords)
│   ├── downloaders/
│   │   ├── __init__.py
│   │   └── base.py              # BaseDownloader (abstract)
│   ├── download_bollettini.py   # Downloader Emilia-Romagna
│   ├── download_campania.py     # Downloader Campania
│   ├── process_bollettini.py    # PDF → chunks → ChromaDB
│   └── colture.py               # Query RAG → report MD/HTML
│
├── data/
│   ├── input_bollettini/
│   │   ├── emilia_romagna/
│   │   │   ├── bollettini/      # PDF (symlink a RAG_bollettini)
│   │   │   └── cache_download.json
│   │   └── campania/
│   │       ├── bollettini/2026/
│   │       └── cache_download.json
│   │
│   ├── chromadb/                # symlink a RAG_bollettini/data/chromadb
│   │   └── [persist sqlite + vectors]
│   │
│   ├── cache/
│   │   ├── processing_cache.json             # PDF già ingested
│   │   ├── colture_emilia_romagna_processed.json
│   │   └── colture_campania_processed.json
│   │
│   └── output_bollettini/        # ← OUTPUT FINALE PER APP
│       ├── emilia_romagna/
│       │   ├── vite/
│       │   │   ├── bologna_ferrara_15-04-2026.md
│       │   │   ├── bologna_ferrara_15-04-2026.html
│       │   │   └── history/2026/bologna_ferrara/*.md
│       │   ├── pero/
│       │   ├── pesco/
│       │   ├── mais/
│       │   └── barbabietola/
│       └── campania/
│           ├── vite/ olivo/ pesco/ actinidia/ melo/
│           ├── castagno/ ciliegio/ susino/ nocciolo/
│           └── agrumi/ pomodoro/
│
└── venv/                         # virtualenv
```

---

## 4. Il dato di output (per back/front end)

### 4.1 Convenzione filesystem
```
data/output_bollettini/{regione}/{coltura}/{province_slug}_{DD-MM-YYYY}.md
data/output_bollettini/{regione}/{coltura}/{province_slug}_{DD-MM-YYYY}.html
```

- `regione` ∈ `{emilia_romagna, campania}`
- `coltura` ∈ `{vite, pero, pesco, mais, barbabietola, olivo, actinidia, melo, castagno, ciliegio, susino, nocciolo, agrumi, pomodoro}` (lowercase)
- `province_slug`: es. `bologna_ferrara`, `modena`, `sele`, `caserta` (underscore, no accenti)
- data formato italiano `DD-MM-YYYY`

**Storico**: i report precedenti vengono spostati in `history/{anno}/{province_slug}/{DD-MM-YYYY}.md` quando arriva un bollettino più recente.

### 4.2 Formato file Markdown

```markdown
# Vite - Bologna,Ferrara

**Bollettino N.10** | 15-04-2026

---

## Situazione Attuale
- **Fase fenologica**: da prime foglie distese a grappolini visibili
- **Periodo**: 2026-04-15

## Avversità e Difesa
### Malattie
| Patogeno | Rischio | Trattamento | Note |
|----------|---------|-------------|------|
| Peronospora | Alto | Folpet, Dithianon, Prodotti rameici, … | Monitorare impianti con germogliamento marcato. |

### Insetti
| Insetto | Presenza | Soglia | Trattamento |
|---------|----------|--------|-------------|
| Tignoletta | 1-60% a Bologna | N/A | Nessun intervento in prima generazione. |

## Trattamenti Consigliati
| Target | Prodotto | Max interventi | Condizioni |
|--------|----------|----------------|------------|
| Peronospora | Folpet | 12 | In previsione di pioggia. |

## Note Operative
- Monitorare gli impianti con germogliamento marcato.
- Programmare l'installazione degli erogatori per confusione sessuale.

---
*Report generato: 20/04/2026 10:48*
```

La struttura è **fissa e prevedibile** — 4 sezioni `##` sempre presenti in questo ordine:
`Situazione Attuale → Avversità e Difesa → Trattamenti Consigliati → Note Operative`.

Se non c'è info, l'LLM scrive `"Nessuna informazione specifica per questa coltura in questo bollettino."` o lascia le tabelle vuote. Se il bollettino intero non menziona la coltura: `"Nessuna informazione specifica per {nome_coltura} in questo bollettino."`

### 4.3 Formato HTML

HTML standalone (self-contained, CSS inline) con:
- Viewport responsive
- Colori theme (arancio `#e67e22`, navy `#2c3e50`)
- Tabelle con border-collapse, zebra-striping
- Generato da `modules/colture.py:convert_md_to_html()` usando `markdown` lib + template Jinja-like inline

**Può essere servito direttamente** dal back-end come risposta a una GET (`Content-Type: text/html`), o renderizzato lato client partendo dal `.md`.

### 4.4 Metadata utili (senza dover parsare il filename)

Il filename contiene tutte le info chiave:
```
regex: ^(?P<province_slug>.+?)_(?P<day>\d{2})-(?P<month>\d{2})-(?P<year>\d{4})\.md$
```

Lato app, la fonte più solida è **scorrere il filesystem** e costruire un indice: `(regione, coltura, province_slug, data) → path`.

### 4.5 Elenco completo regioni × colture

| Regione | Colture configurate |
|---|---|
| Emilia-Romagna | VITE, PERO, PESCO, MAIS, BARBABIETOLA |
| Campania | VITE, OLIVO, PESCO, NOCCIOLO, ACTINIDIA, MELO, CASTAGNO, CILIEGIO, SUSINO, AGRUMI, POMODORO |

ER ha 4 gruppi di province (Bologna-Ferrara, Forlì-Cesena-Ravenna-Rimini, Modena-Reggio-Emilia, Parma-Piacenza), ma i bollettini ER specificano una province concreta (es. "Modena" singola). In pratica si vedono 6 `province_slug` attivi: `bologna_ferrara, forli_cesena_ravenna_rimini, modena, reggio_emilia, parma, piacenza`.

Campania ha 19 aree configurate (vedere `modules/config.py:REGIONI["campania"]["aree"]`), nella pratica solo 9 sono attive al momento.

---

## 5. Pipeline di esecuzione

### 5.1 Entry point
```bash
cd /home/vito/projects/tornatura/RAG_colture
source venv/bin/activate
python run_pipeline.py [opzioni]
```

### 5.2 Flag disponibili

| Flag | Significato |
|---|---|
| (nessuno) | Pipeline completa per tutte le regioni (download + process + query, solo per bollettini nuovi) |
| `--regione emilia_romagna` \| `campania` | Processa solo la regione indicata |
| `--force` | Ignora tutte le cache e riprocessa tutto |
| `--download-only` | Solo fase 1 |
| `--query-only` | Solo fase 3 (utile se chromadb già popolato) |
| `--verbose` / `-v` | DEBUG logging |

### 5.3 Exit code

- `0`: nuovi dati processati
- `1`: tutto già aggiornato (niente di nuovo)
- `2`: errore

Utili per cron / systemd-timer / scheduler.

### 5.4 Cadenza consigliata in produzione

I bollettini ER escono ~2 volte a settimana; Campania variabile. Cron consigliato:
```cron
# Esegui ogni giorno alle 7:00
0 7 * * * cd /path/to/RAG_colture && ./venv/bin/python run_pipeline.py
```

Ogni run dura ~5-10 minuti se ci sono bollettini nuovi, ~1 minuto se niente di nuovo (passa tutti i check cache).

---

## 6. Dettaglio tecnico fase per fase

### FASE 1 — Download

**Emilia-Romagna** (`modules/download_bollettini.py`)
- Endpoint base: `https://agricoltura.regione.emilia-romagna.it/fitosanitario/difesa-sostenibile/bollettini/bollettini-interprovinciali-di-produzione-integrata-e-biologica-{ANNO}`
- Sub-endpoint per provincia: `/{slug}/@search` paginato (Plone REST API)
- Filtro PDF con titolo contenente "bollettino", esclude "allegato"/"orticole"
- Rate limiting: 2s tra download
- Fallback: se anno corrente non disponibile (404), retrocede all'anno precedente
- **Cache**: `data/input_bollettini/emilia_romagna/cache_download.json`

**Campania** (`modules/download_campania.py`)
- Base: `https://agricoltura.regione.campania.it/difesa/bollettini/bollettini_{ANNO}.html`
- Scraping HTML con BeautifulSoup, regex sui link PDF `{slug}-{DD}-{MM}.pdf`
- Rate limiting: 2s
- Filename normalizzato: `Campania_{area_slug}_{DD-MM-YYYY}.pdf`
- **Cache**: `data/input_bollettini/campania/cache_download.json`

Entrambi usano la stessa classe base `modules/downloaders/base.py:BaseDownloader` (template method: `download_all()`).

### FASE 2 — Processing PDF → ChromaDB

`modules/process_bollettini.py:BollettiniProcessor`

Per ogni PDF non in cache:
1. **Docling** converte PDF → Markdown. Per ER: converter standard. Per Campania: enhanced OCR (`RapidOcrOptions(force_full_page_ocr=True, lang=['it','en'])`, `images_scale=2.0`).
2. **Preprocessing Campania-specifico**: normalizza intestazioni inconsistenti (es. `"COLTURA: PESCO"`, `"COLTURA NOCCIOLO"`, `"| COLTURA | VITE |"` nelle tabelle) → `## PESCO` standardizzato.
3. **Chunking** (`create_chunks_from_markdown`):
   - Split su header `#{1,3}` (regex `SECTION_PATTERN`)
   - Merge sezioni < 100 parole
   - Sezioni protette (`VITE, PERO, PESCO, OLIVO, MELO, NOCCIOLO, ACTINIDIA`, …) non vengono mai unite
   - Max 500 parole per chunk merged
4. **Metadata estratti dal filename + chunking**:
   ```python
   {
       "chunk_id": "{doc_name}_chunk_{i}",
       "doc_name": "Bollettino 10 del 15 aprile 2026 di Bologna e Ferrara",
       "section_title": "## VITE",
       "numero_bollettino": 10,              # None per Campania
       "data": "2026-04-15",                 # ISO
       "province": "Bologna,Ferrara",        # o "sele" per Campania
       "tipo_documento": "bollettino",       # o "normativa"
       "regione": "emilia_romagna"           # o "campania"
   }
   ```
5. **Embedding** batch 32, vettori float 384d via SentenceTransformer
6. **Upload multi-collection**: i bollettini vanno in **tutte** le collezioni con `shared_sources: ["bollettino"]`. Oggi: `cimice_asiatica` (principale) + `flavescenza_dorata`. Documenti esclusivi (es. `testo_lotta_flavescenza`) vanno in una sola.

**Cache**: `data/cache/processing_cache.json` traccia doc già ingested.

### FASE 3 — Query RAG

`modules/colture.py:ColtureQueryProcessor`

Per ogni bollettino (solo l'ultimo per province/area, gestito da `get_latest_bollettini_by_province`):
1. **Carica tutti i chunk del bollettino** da ChromaDB in un'unica query:
   ```python
   chunks = collection.get(where={"doc_name": doc_name}, include=["documents","metadatas"])
   ```
2. Per ogni coltura:
   - **Sezione-based retrieval** (alta precisione): `section_matches()` con **prefix-match e word boundary**. Es. `"BARBABIETOLA DA ZUCCHERO"` matcha `"BARBABIETOLA"`.
   - **Fallback keyword** solo se `section_words < 200`: cerca keyword della coltura nel contenuto dei chunk che **non appartengono ad altre colture** (filtro via `is_other_coltura_section` + euristica `looks_like_coltura_heading` — esclude automaticamente sezioni MAIUSCOLE brevi di colture non configurate come ALBICOCCO, NOCE, PATATA, ERBA MEDICA).
   - **Filtro anti-contaminazione rafforzato**: se un chunk contiene più keyword di altre colture che della propria → scarta.
3. **GPT-4o-mini** genera il report con `SYSTEM_PROMPT` + `QUERY_TEMPLATE` (definiti in `modules/colture.py`):
   - `temperature=0` (deterministico)
   - Struttura output **fissa** (4 sezioni `##`)
   - Prompt rigoroso che vieta invenzioni e mix tra colture
4. **Salvataggio**: `.md` + `.html` nella cartella regione/coltura, e **move del report precedente** in `history/{anno}/{province_slug}/`.

**Cache**: `data/cache/colture_{regione}_processed.json` con chiave `"{doc_name}::{coltura_id}"`.

---

## 7. Ambiente / Secrets

### `.env`
```bash
OPENAI_API_KEY=sk-...      # per GPT-4o-mini
```

### Dipendenze esterne
- **Connessione a agricoltura.regione.emilia-romagna.it e agricoltura.regione.campania.it**: necessaria per download
- **api.openai.com**: necessaria per query RAG
- **ChromaDB filesystem**: persistente, symlink a `RAG_bollettini/data/chromadb` (shared con progetto gemello)

### Setup iniziale su una nuova macchina
```bash
git clone <repo>
cd RAG_colture
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install docling         # transitiva, installare a mano
cp .env.example .env        # e popolare OPENAI_API_KEY
mkdir -p data/cache
# Symlink ChromaDB (se c'è già una istanza condivisa):
ln -s /path/to/RAG_bollettini/data/chromadb data/chromadb
```

---

## 8. Punti di integrazione per l'applicazione

### 8.1 Scenario A — Serve file MD/HTML dal filesystem

Il modo più semplice: il back-end espone endpoint tipo
```
GET /api/bollettini/{regione}/{coltura}/{province}/latest        → .md
GET /api/bollettini/{regione}/{coltura}/{province}/latest.html   → .html preformattato
GET /api/bollettini/{regione}/{coltura}/{province}/history       → lista date
GET /api/bollettini/{regione}/{coltura}/{province}/{date}.md     → storico
```

Mapping a filesystem diretto:
- `latest` → ultimo file matching `{province_slug}_*.md` in `data/output_bollettini/{regione}/{coltura}/`
- `history` → `glob data/output_bollettini/{regione}/{coltura}/history/*/{province_slug}/*.md`

Il front-end può renderizzare il `.md` lato client (react-markdown, marked, etc.) o servire direttamente il `.html`.

### 8.2 Scenario B — API strutturata (raccomandato)

Se serve output più machine-readable, aggiungere uno **step di parsing del MD** lato back-end che produca JSON:

```json
{
  "regione": "emilia_romagna",
  "coltura": "VITE",
  "province": "Bologna,Ferrara",
  "data": "2026-04-15",
  "numero_bollettino": 10,
  "situazione": {
    "fase_fenologica": "da prime foglie distese a grappolini visibili",
    "periodo": "2026-04-15"
  },
  "malattie": [
    {"patogeno": "Peronospora", "rischio": "Alto", "trattamento": "Folpet, Dithianon, ...", "note": "..."}
  ],
  "insetti": [...],
  "trattamenti": [...],
  "note_operative": ["...", "..."]
}
```

Essendo il formato MD fisso (tabelle fisse in ordine fisso), un parser in ~50 righe Python (o TS con `marked` + AST traversal) è sufficiente. Alternativa: modificare `colture.py` per salvare anche una versione `.json` accanto al `.md`.

### 8.3 Scenario C — Webhook su aggiornamento

Oggi `run_pipeline.py` è pensato per essere invocato da cron. Si può estendere con:
- webhook HTTP a fine pipeline (POST con lista di `(regione, coltura, province, data)` aggiornati)
- messaggio su queue (Redis/RabbitMQ) per back-end reattivo

Hook d'attacco: dopo `_save_markdown()` in `modules/colture.py`, oppure alla fine di `run_pipeline.py:main()`.

### 8.4 Elenco bollettini disponibili (from ChromaDB)

Per una vista "lista bollettini" il back-end può interrogare ChromaDB direttamente:
```python
import chromadb
client = chromadb.PersistentClient(path='data/chromadb')
col = client.get_collection('cimice_asiatica')
# TUTTI senza limite (collezione può crescere, ma i metadata sono leggeri)
results = col.get(where={"regione": "emilia_romagna"}, include=["metadatas"])
# aggregare per doc_name
```

⚠️ **Nota importante**: **NON usare `limit=...`** nella query — un bug precedente tagliava fuori i bollettini più recenti perché venivano inseriti per ultimi. La collezione ha ~7k chunks e solo metadata, non crea problemi.

---

## 9. Costi operativi (OpenAI)

Modello: **GPT-4o-mini** (tariffe al 2026-04: $0.15/1M input, $0.60/1M output).

| Scenario | Chiamate LLM | Costo |
|---|---|---|
| Run quotidiano tipico (nuovi bollettini rari) | 0-30 | ~$0.00–0.03 |
| Rigenerazione completa tutti ER (`--force`) | 30 (6 prov × 5 colture) | ~$0.03 |
| Rigenerazione completa Campania (`--force`) | 99 (9 aree × 11 colture) | ~$0.10 |
| Rigenerazione totale ER+CA | 129 | ~$0.13 |

Dominato dai token di input (~1500 token/call dopo fix retrieval, prima erano ~6000+).

---

## 10. Caveat e limiti noti

1. **OCR Campania fragile**: alcuni PDF scansionati producono markdown sporco. Il preprocessing `preprocess_campania_markdown()` tenta di normalizzare ma non è garantito. Se un bollettino futuro cambia formato, i match di sezione possono fallire.
2. **Keyword pseudo-generiche**: keywords come `"pomacee"` nel config possono matchare chunks di contesto generale. Il fix recente limita l'impatto grazie alla soglia `section_words < 200` prima di attivare il fallback.
3. **Campania non pubblica numero bollettino**: `numero_bollettino` è `None` nei record Campania. Usare solo la `data` come chiave di ordinamento.
4. **Colture stagionali Campania**: AGRUMI, POMODORO, ACTINIDIA appaiono nei bollettini estivi — d'inverno i report sono giustamente vuoti ("Nessuna informazione specifica...").
5. **GPT non deterministico al 100%**: con `temperature=0` è molto stabile ma non bit-perfect. Piccole variazioni tra run sono normali.
6. **Colture non configurate nel PDF**: ALBICOCCO, NOCE, SUSINO EUROPEO, KAKI, PATATA, ERBA MEDICA, FRUMENTO, SOIA, SORGO, GIRASOLE, CIPOLLA, FRAGOLA, POMODORO DA INDUSTRIA, COLZA sono presenti nei bollettini ER ma **non sono generati come report separati**. Per aggiungerli: inserire in `modules/config.py:COLTURE` + assegnare a una regione in `REGIONI`.

---

## 11. Come aggiungere una nuova coltura

Editare `modules/config.py`:

```python
COLTURE = {
    # ...
    "MELO": {
        "nome": "Melo",
        "sezioni": ["MELO", "Melo", "COLTURA MELO", "COLTURA: MELO"],
        "keywords": [
            "melo", "mela", "meleto", "annurca",
            "ticchiolatura del melo", "venturia inequalis",
        ],
    },
}

REGIONI["emilia_romagna"]["colture"].append("MELO")  # se ER
```

Poi:
```bash
rm data/cache/colture_emilia_romagna_processed.json
python run_pipeline.py --regione emilia_romagna --query-only
```

Non serve reindicizzare ChromaDB.

---

## 12. Troubleshooting rapido

| Sintomo | Probabile causa | Fix |
|---|---|---|
| Report vuoto nonostante coltura nel PDF | `sezioni` in config non copre la variante usata nel PDF | Aggiungere variante o usare `section_matches` prefix-match |
| Report contaminato con info altra coltura | Fallback keyword troppo permissivo | Verifica `is_other_coltura_section`; aggiungi la coltura fake a `looks_like_coltura_heading` |
| Download fallisce con 404 | Anno cambiato o struttura URL cambiata | Controllare `PROVINCE_URLS` in `download_bollettini.py`, o pagine indice Campania |
| OpenAI rate limit | Troppi run in parallelo | Limitare parallelismo, oppure passare a batch API |
| "Nessun bollettino disponibile" in query | Metadata `regione` mancante in ChromaDB | Vedi migrazione metadata (script inline in README) |

---

## 13. File chiave da leggere (in ordine)

Per chi prende in mano il codice:

1. `run_pipeline.py` (~350 righe) — orchestrazione
2. `modules/config.py` (~250 righe) — configurazione
3. `modules/colture.py` (~820 righe) — **core logic**, leggere per prime:
   - `section_matches()`, `looks_like_coltura_heading()`, `is_other_coltura_section()`
   - `_retrieve_coltura_chunks()`
   - `_generate_report()` + `SYSTEM_PROMPT` + `QUERY_TEMPLATE`
   - `process_bollettino()` — single-fetch optimization
4. `modules/process_bollettini.py` (~600 righe) — chunking + ingest
5. `modules/download_bollettini.py` e `download_campania.py` — scraping

---

## 14. Audit qualità attuale

Risultati dell'audit eseguito il 2026-04-20:

| Metrica | Valore |
|---|---|
| Report totali | 159 (30 ER + 99 CA + 30 storici) |
| Contaminazione cross-coltura rilevata | **0** |
| Report vuoti giustificati (coltura non nel bollettino) | 69 CA |
| Report vuoti non giustificati | **0** |
| Query ChromaDB per bollettino | 1 (ottimizzato) |
| Token LLM input medio per call | ~1500 |
