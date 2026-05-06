# RAG Colture — Transfer Package

Sistema RAG per l'estrazione automatica di informazioni per coltura dai
bollettini fitosanitari (Emilia-Romagna + Campania).

## Quick Start

```bash
# 1. Setup (crea venv + installa dipendenze)
./setup.sh

# 2. Configura API key
# Modifica .env e inserisci OPENAI_API_KEY

# 3. Test (solo query RAG, senza download)
source venv/bin/activate
python run_pipeline.py --query-only

# 4. Run completo (download + process + query)
python run_pipeline.py
```

## Documentazione tecnica

- **`report.md`** — documento completo per handoff back/front end
  (architettura, formati dati, punti di integrazione, API, costi)
- **`CLAUDE.md`** — documentazione operativa sintetica

## Output

Report generati in:
```
data/output_bollettini/{regione}/{coltura}/{province}_{DD-MM-YYYY}.md
data/output_bollettini/{regione}/{coltura}/{province}_{DD-MM-YYYY}.html
```

Vedi `report.md` sezione 4 per il formato dettagliato.

## Struttura

```
.
├── run_pipeline.py           # Entry point (orchestratore)
├── modules/                  # Moduli Python
├── data/
│   ├── input_bollettini/     # PDF sorgenti
│   ├── chromadb/             # Vector DB pre-indicizzato
│   ├── cache/                # JSON cache (download/processing/query)
│   └── output_bollettini/    # Report generati per coltura
├── report.md                 # Doc tecnica
├── CLAUDE.md                 # Doc operativa
└── requirements.txt
```
