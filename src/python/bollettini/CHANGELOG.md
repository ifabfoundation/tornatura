# Changelog - RAG Bollettini

Registro delle modifiche per il team backend.

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
