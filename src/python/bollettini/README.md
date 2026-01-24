# RAG Bollettini - Sistema di Produzione

Sistema RAG per estrazione automatica informazioni dai bollettini fitosanitari
della Regione Emilia-Romagna.

## Quick Start

```bash
# 1. Setup
./setup.sh
# oppure manualmente:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configura API key
cp .env.example .env
# Modifica .env con la tua OPENAI_API_KEY

# 3. Test
python run_pipeline.py --query-only

# 4. Produzione (scheduler giornaliero)
python scheduler.py
```

## Documentazione Completa

Vedi **CLAUDE.md** per la documentazione tecnica completa.

## Struttura

```
.
├── run_pipeline.py      # Pipeline principale
├── scheduler.py         # Scheduler giornaliero (08:00)
├── modules/             # Moduli Python
├── data/
│   ├── 1_collections/   # PDF bollettini
│   ├── chromadb/        # Vector database
│   └── output/          # Report generati
└── logs/                # Log scheduler
```

## Output

I report vengono generati in:
- `data/output/cimice/` - Report Cimice Asiatica
- `data/output/flavescenza/` - Report Flavescenza Dorata

Formato: `{provincia}_{DD-MM-YYYY}.md`
