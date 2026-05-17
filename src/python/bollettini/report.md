# RAG Bollettini - Report Tecnico Completo

## Panoramica del Sistema

RAG Bollettini è un sistema di **Retrieval-Augmented Generation** che automatizza l'estrazione di informazioni fitosanitarie dai bollettini della Regione Emilia-Romagna. Il sistema genera report operativi per agronomi su due avversità principali:

1. **Cimice Asiatica** (Halyomorpha halys)
2. **Flavescenza Dorata** e il suo vettore **Scaphoideus titanus**

---

## Architettura Generale

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PIPELINE COMPLETA                               │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │   DOWNLOAD   │ ───> │   PROCESS    │ ───> │    QUERY     │
    │  bollettini  │      │  (indexing)  │      │  (reports)   │
    └──────────────┘      └──────────────┘      └──────────────┘
           │                     │                     │
           ▼                     ▼                     ▼
    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │  PDF files   │      │   ChromaDB   │      │  MD + HTML   │
    │  (181 docs)  │      │ (vector DB)  │      │   reports    │
    └──────────────┘      └──────────────┘      └──────────────┘
```

---

## Struttura File e Interazioni

### 1. Entry Points (Punti di Ingresso)

#### `run_pipeline.py` - Orchestratore Principale
**Ruolo**: Coordina l'intera pipeline in sequenza.

**Flusso di esecuzione**:
```python
def main():
    # STEP 1: Download nuovi bollettini
    download_bollettini.download_all_provinces()

    # STEP 2: Indicizza in ChromaDB
    process_bollettini.process_new_bollettini()

    # STEP 3: Genera report Cimice
    cimice.CimiceQueryProcessor().process_new_only()

    # STEP 4: Genera report Flavescenza
    flavescenza.FlavescenzaQueryProcessor().process_new_only()
```

**Opzioni CLI**:
- `python run_pipeline.py` → Pipeline completa
- `python run_pipeline.py --force` → Ignora cache, riprocessa tutto
- `python run_pipeline.py --query-only` → Solo generazione report (skip download/indexing)

#### `scheduler.py` - Esecuzione Automatica
**Ruolo**: Esegue la pipeline giornalmente alle 08:00.

**Tecnologia**: APScheduler (BackgroundScheduler)

**Flusso**:
```python
scheduler = BackgroundScheduler()
scheduler.add_job(run_pipeline, 'cron', hour=8, minute=0)
scheduler.start()
```

---

### 2. Moduli di Processing

#### `modules/download_bollettini.py`
**Ruolo**: Scarica PDF dei bollettini dall'API della Regione Emilia-Romagna.

**Input**: API REST Regione (https://agricoltura.regione.emilia-romagna.it)

**Output**: `data/1_collections/bollettini/*.pdf`

**Logica**:
```
Per ogni provincia (Bologna-Ferrara, Modena-RE, Parma-Piacenza, Forlì-Cesena-Ravenna-Rimini):
    1. Chiama API per lista bollettini anno corrente
    2. Filtra: solo bollettini (no allegati)
    3. Per ogni bollettino non in cache:
        - Scarica PDF
        - Estrai metadati (numero, data, provincia)
        - Salva in data/1_collections/bollettini/
        - Aggiorna bollettini_cache.json
```

**Cache**: `data/bollettini_cache.json`
```json
{
  "bollettino_N30_bologna_ferrara.pdf": {
    "downloaded_at": "2025-10-01T10:30:00",
    "numero": 30,
    "provincia": "Bologna,Ferrara"
  }
}
```

---

#### `modules/process_bollettini.py`
**Ruolo**: Converte PDF in chunks vettoriali e li indicizza in ChromaDB.

**Input**: PDF da `data/1_collections/bollettini/`

**Output**: Due collezioni ChromaDB in `data/chromadb/`

**Tecnologie**:
- **Docling**: Conversione PDF → Markdown (preserva struttura)
- **ChromaDB**: Vector database per embedding
- **OpenAI Embeddings**: text-embedding-ada-002

**Flusso dettagliato**:
```
Per ogni PDF non in processing_cache.json:
    1. Docling converte PDF → Markdown strutturato

    2. Parser estrae sezioni:
       - Titolo bollettino
       - Data pubblicazione
       - Numero bollettino
       - Sezioni per coltura/avversità

    3. Chunking intelligente:
       - Chunk size: ~1000 caratteri
       - Overlap: 200 caratteri
       - Preserva contesto sezione

    4. Per ogni chunk:
       - Genera embedding via OpenAI
       - Aggiunge metadati:
         {
           "doc_name": "bollettino_N30_bologna.pdf",
           "provincia": "Bologna,Ferrara",
           "numero_bollettino": 30,
           "data": "2025-10-01",
           "section_title": "Vite - Flavescenza dorata"
         }

    5. Inserisce in collezioni ChromaDB:
       - "cimice_asiatica" → chunks con keyword cimice
       - "flavescenza_dorata" → chunks con keyword flavescenza
```

**Cache**: `data/processing_cache.json`

---

#### `modules/cimice.py`
**Ruolo**: Genera report sulla Cimice Asiatica per ogni provincia.

**Input**:
- ChromaDB collezione "cimice_asiatica"
- Ultimo bollettino per provincia

**Output**:
- `data/output/cimice/{provincia}_{DD-MM-YYYY}.md`
- `data/output/cimice/{provincia}_{DD-MM-YYYY}.html`

**Keywords per retrieval**:
```python
CIMICE_KEYWORDS = ['cimice', 'halyomorpha', 'halys', 'hhal', 'cimici']
```

**Flusso**:
```
1. Recupera ultimo bollettino per provincia da ChromaDB
2. Filtra chunks con keywords cimice
3. Costruisce prompt con:
   - System prompt (template output)
   - Context (chunks filtrati)
   - Query aggregata
4. Chiama GPT-4o-mini (temperature=0)
5. Salva MD + HTML
6. Se esiste report precedente → sposta in history/
```

---

#### `modules/flavescenza.py`
**Ruolo**: Genera report su Flavescenza Dorata e Scaphoideus titanus.

**Input**:
- ChromaDB collezione "flavescenza_dorata"
- Normativa strutturata da `normativa_flavescenza.py`
- Ultimo bollettino per provincia

**Output**:
- `data/output/flavescenza/{provincia}_{DD-MM-YYYY}.md`
- `data/output/flavescenza/{provincia}_{DD-MM-YYYY}.html`

**Keywords per retrieval**:
```python
FLAVESCENZA_KEYWORDS = ['flavescenza', 'scaphoideus', 'scafoideo', 'titanus', 'giallumi', 'fitoplasm']
```

**Differenza chiave da cimice.py**:
La Flavescenza ha una **normativa regionale complessa** che viene gestita separatamente dal modulo `normativa_flavescenza.py` e iniettata nel context LLM.

**Flusso**:
```
1. Recupera ultimo bollettino per provincia da ChromaDB
2. Filtra chunks con keywords flavescenza
3. Recupera normativa strutturata per provincia:
   - formatta_normativa_per_llm(provincia)
4. Costruisce context combinato:
   [BOLLETTINO] + [NORMATIVA REGIONALE]
5. Chiama GPT-4o-mini
6. Salva MD + HTML con warning se normativa obsoleta
7. Gestione history
```

---

#### `modules/normativa_flavescenza.py`
**Ruolo**: Contiene dati normativi strutturati in Python (NON in ChromaDB).

**Perché separato?**
- La normativa è **uguale per tutte le province** (dati regionali)
- Cambia solo annualmente (maggio)
- Serve precisione 100% (date, prodotti, limitazioni)
- Zero query al database

**Struttura dati**:
```python
NORMATIVA_2025 = {
    "anno": 2025,
    "determinazione": "N.9016 del 14/05/2025",

    # Obblighi generali
    "obblighi_generali": {
        "trattamenti_vigneti": "Almeno 2 trattamenti...",
        "estirpo_zona_infestata": "Obbligo immediato...",
        "sanzioni_min": 1000,
        "sanzioni_max": 6000
    },

    # Scadenze trattamenti
    "scadenze_trattamenti": {
        "inizio_lotta": "5 giugno 2025",
        "integrata": {
            "primo_trattamento": "entro 20 giugno 2025",
            "secondo_trattamento": "entro 31 luglio 2025"
        },
        "biologica": {
            "primo_trattamento": "entro 20 giugno 2025",
            "secondo_trattamento": "entro 15 luglio 2025"
        }
    },

    # Insetticidi ammessi con limitazioni
    "insetticidi_ammessi": {
        "difesa_integrata": [
            {"sostanza": "Acetamiprid", "limitazioni": "max 1 int/anno", "bio": False},
            {"sostanza": "Piretrine pure", "limitazioni": None, "bio": True},
            # ...
        ]
    },

    # Strategie raccomandate
    "strategie_difesa": {
        "integrata": {
            "primo_trattamento": ["Acetamiprid", "Flupyradifurone", "Sulfoxaflor"],
            "secondo_trattamento": ["Tau-fluvalinate", "Deltametrina", ...]
        },
        "biologica": {
            "primo_trattamento": ["Azadiractina", "Beauveria", ...],
            "secondo_trattamento": ["Piretrine pure (OBBLIGATORIO)"]
        }
    },

    # Accorgimenti operativi
    "accorgimenti_operativi": [
        "Volume minimo acqua: 400 lt/ha",
        "pH soluzione < 7",
        "Prodotti fotolabili: ore serali"
    ],

    # Tutela api
    "tutela_api": {
        "divieto_fioritura": "Vietato durante fioritura vite",
        "riferimento": "L.R. 2/2019"
    },

    # Zone delimitate per provincia
    "province": {
        "Bologna": {
            "zona_infestata": ["Anzola", "Bologna", ...],
            "zona_cuscinetto": ["Pianoro", "Ozzano", ...]
        },
        # ...altre province
    }
}
```

**Funzioni esposte**:
```python
# Formatta tutto per il context LLM
formatta_normativa_per_llm("Bologna,Ferrara") → stringa formattata

# Accesso dati specifici
get_obblighi_generali() → dict
get_zone_provincia("Modena") → dict
get_province_disponibili() → ["Bologna", "Ferrara", ...]
```

**Aggiornamento annuale (Maggio)**:
```python
# Quando esce nuova Determinazione Regionale:
NORMATIVA_2026 = { ... }  # Copia e aggiorna dati
NORMATIVA_CORRENTE = NORMATIVA_2026  # Punta alla nuova
```

---

## Flusso Dati Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUSSO DATI DETTAGLIATO                           │
└─────────────────────────────────────────────────────────────────────────────┘

                         API Regione ER
                              │
                              ▼
                   ┌─────────────────────┐
                   │ download_bollettini │
                   │    (requests)       │
                   └──────────┬──────────┘
                              │
            ┌─────────────────┴─────────────────┐
            │                                   │
            ▼                                   ▼
    ┌───────────────┐                  ┌───────────────┐
    │  PDF files    │                  │ bollettini_   │
    │  181 docs     │                  │ cache.json    │
    └───────┬───────┘                  └───────────────┘
            │
            ▼
    ┌─────────────────────┐
    │ process_bollettini  │
    │  (Docling + OpenAI) │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌─────────┐         ┌─────────┐
│ChromaDB │         │ChromaDB │
│cimice_  │         │flaves_  │
│asiatica │         │cenza_   │
└────┬────┘         │dorata   │
     │              └────┬────┘
     │                   │
     ▼                   ▼
┌─────────┐         ┌─────────────────────────┐
│cimice.py│         │    flavescenza.py       │
│         │         │           +             │
│         │         │ normativa_flavescenza.py│
└────┬────┘         └────────────┬────────────┘
     │                           │
     │         ┌─────────────────┴─────────────────┐
     │         │                                   │
     ▼         ▼                                   ▼
┌─────────────────┐                      ┌─────────────────┐
│ output/cimice/  │                      │output/flavescen/│
│ • MD reports    │                      │ • MD reports    │
│ • HTML reports  │                      │ • HTML reports  │
│ • history/      │                      │ • history/      │
└─────────────────┘                      └─────────────────┘
```

---

## Sistema di Cache

Il sistema usa **4 livelli di cache** per evitare riprocessamento:

| Cache | File | Scopo |
|-------|------|-------|
| Download | `data/bollettini_cache.json` | PDF già scaricati |
| Indexing | `data/processing_cache.json` | PDF già indicizzati in ChromaDB |
| Cimice | `data/cache/cimice_processed.json` | Bollettini già processati |
| Flavescenza | `data/cache/flavescenza_processed.json` | Bollettini già processati |

**Flag `--force`**: Pulisce tutte le cache e riprocessa tutto.

---

## Gestione History

Quando arriva un **nuovo bollettino**, il report precedente viene spostato automaticamente:

```
output/flavescenza/
├── bologna_ferrara_15-10-2025.md      ← report CORRENTE
├── bologna_ferrara_15-10-2025.html
└── history/
    └── 2025/
        └── bologna_ferrara/
            ├── 01-10-2025.md          ← report PRECEDENTE
            └── 01-10-2025.html
```

**Logica** (in `move_to_history()`):
```python
1. Trova report esistente per provincia
2. Confronta data: se data_esistente < data_nuovo_bollettino
3. Crea struttura history/{anno}/{provincia}/
4. Sposta MD + HTML
```

---

## Conversione MD → HTML

Ogni report viene salvato in **due formati**:
- `.md` - Markdown per visualizzazione/editing
- `.html` - HTML con CSS embedded per browser

**CSS differenziato**:
- Cimice: tema **blu** (#3498db)
- Flavescenza: tema **verde** (#27ae60)

---

## Integrazione con App

### Per lo sviluppatore:

**1. Endpoint da esporre**:
```python
# Ritorna ultimo report per provincia
GET /api/bollettini/cimice/{provincia}
GET /api/bollettini/flavescenza/{provincia}

# Ritorna lista province disponibili
GET /api/bollettini/province

# Forza refresh (chiama run_pipeline)
POST /api/bollettini/refresh
```

**2. Lettura report**:
```python
from pathlib import Path

def get_latest_report(tipo: str, provincia: str) -> dict:
    """
    tipo: 'cimice' o 'flavescenza'
    provincia: slug normalizzato (es. 'bologna_ferrara')
    """
    output_dir = Path(f"data/output/{tipo}")

    # Trova file più recente per provincia
    files = list(output_dir.glob(f"{provincia}_*.md"))
    if not files:
        return None

    latest = max(files, key=lambda f: f.stat().st_mtime)

    return {
        "content_md": latest.read_text(),
        "content_html": latest.with_suffix('.html').read_text(),
        "filename": latest.name,
        "last_modified": latest.stat().st_mtime
    }
```

**3. Scheduler**:
```python
# Opzione A: Usa scheduler.py incluso (APScheduler)
python scheduler.py

# Opzione B: Cron job esterno
0 8 * * * cd /path/to/rag_bollettini && ./venv/bin/python run_pipeline.py
```

**4. Notifiche nuovo bollettino**:
```python
# In run_pipeline.py, dopo process_bollettini:
if has_new_bollettini:
    notify_app(new_bollettini_list)
```

---

## Dipendenze Chiave

| Libreria | Versione | Uso |
|----------|----------|-----|
| openai | ≥1.0 | Embeddings + GPT-4o-mini |
| chromadb | ≥0.4 | Vector database |
| docling | ≥1.0 | PDF → Markdown |
| python-dotenv | * | Variabili ambiente |
| apscheduler | ≥3.10 | Scheduler |
| markdown | * | MD → HTML |
| requests | * | Download PDF |

---

## Costi Operativi

| Operazione | Costo stimato |
|------------|---------------|
| Embedding 1 PDF | ~$0.001 |
| Query GPT-4o-mini | ~$0.002 |
| Pipeline completa (6 province) | ~$0.02 |
| Mese (30 esecuzioni) | ~$0.60 |

---

## Troubleshooting

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| Report non generati | Cache | `python run_pipeline.py --force` |
| Normativa obsoleta | Anno nuovo | Aggiornare `normativa_flavescenza.py` a maggio |
| ChromaDB corrotto | Interruzione | Eliminare `data/chromadb/` e riprocessare |
| API Regione down | Temporaneo | Retry automatico, altrimenti skip |

---

## Aggiornamento Annuale (Maggio)

Quando esce la nuova **Determinazione Regionale**:

1. **Scaricare** i nuovi PDF normativi
2. **Aggiornare** `modules/normativa_flavescenza.py`:
   ```python
   NORMATIVA_2026 = {
       "anno": 2026,
       "determinazione": "N.XXXX del XX/05/2026",
       # ... nuovi dati
   }
   NORMATIVA_CORRENTE = NORMATIVA_2026
   ```
3. **Testare**: `python modules/normativa_flavescenza.py`
4. **Rigenerare**: `python run_pipeline.py --force`

---

## Contatti

Per domande tecniche sul codice, consultare `CLAUDE.md` per la documentazione di sviluppo.
