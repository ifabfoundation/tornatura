# Changelog - Peronospora Inference Pipeline

Registro delle modifiche per il team backend.

---

## [2026-03-10] - Transfer Package v2.0 - Riepilogo Completo Aggiornamenti

### Overview per il Backend Developer

Questo e' il secondo trasferimento del package di inferenza. Rispetto alla versione precedente (v1.0, Gennaio 2026), sono state apportate le seguenti modifiche significative.

### Riepilogo di TUTTI i cambiamenti dalla v1.0

#### 1. Espansione da 9 Province ER a 107 Province Italiane (2026-02-27)
- **Output CSV**: `predictions/lead_0.csv` e `lead_1.csv` ora contengono **107 righe** (una per provincia) invece di 9
- **Nuovo file**: `data/provinces_italy.json` - Configurazione centralizzata di tutte le 107 province con slug, display_name, sigla, regione, bounding box
- **Nuovo file**: `data/generate_provinces_config.py` - Script per rigenerare il config
- **Nuovo shapefile**: `data/weather/shapefiles/province_italia.*` - Confini di tutte le province italiane
- **Performance**: Pipeline da ~30s a ~5-6 minuti, cache cresce ~1.2 GB/anno

#### 2. Cambio Scala Rischio da 1-5 a 0-4 (2026-02-25)
- `risk_score`: ora float 0.00-4.00 (era 1.00-5.00)
- `risk_level`: ora int 0-4 (era 1-5)
- Formula: `nuovo = vecchio - 1`
- `risk_levels.json`: chiavi cambiate da "1"-"5" a "0"-"4"

#### 3. Nuova Mappatura Livelli a Range (2026-02-25)
- NON piu' rounding (`round(score)`) ma range-based:
  - 0.0 - 1.0 → Livello 0 (Verde - Nessun rischio)
  - 1.0 - 2.0 → Livello 1 (Giallo - Sorveglianza)
  - 2.0 - 3.0 → Livello 2 (Arancione - Attenzione)
  - 3.0 - 3.5 → Livello 3 (Arancione scuro - Rischio elevato)
  - 3.5 - 4.0 → Livello 4 (Rosso - Rischio molto elevato)

#### 4. Miglioramenti Mappa (2026-02-25)
- Mappa centrata su tutta Italia (non solo ER)
- Navigazione settimane con bottoni (non piu' dropdown)
- Solo layer Satellite Esri
- Label con solo numero rischio

### File MODIFICATI rispetto alla v1.0

| File | Tipo Modifica | Descrizione |
|------|--------------|-------------|
| `model.py` | MODIFICATO | Scala 0-4, risk_level con range |
| `plot_risk_map.py` | MODIFICATO | Mappa Italia, bottoni navigazione, province da JSON |
| `data/prepare_inference_data.py` | MODIFICATO | TARGET_PROVINCES caricato da provinces_italy.json (107 province) |
| `backfill_predictions.py` | MODIFICATO | Scala 0-4, risk_level con range |
| `scheduler.py` | MODIFICATO | Documentazione estesa con sezioni, versione 2.0 |
| `risk_levels.json` | MODIFICATO | Chiavi 0-4, aggiunto range_min/range_max |
| `requirements.txt` | INVARIATO | Nessuna modifica |
| `run_inference_pipeline.py` | INVARIATO | Nessuna modifica |

### File NUOVI rispetto alla v1.0

| File | Descrizione |
|------|-------------|
| `data/provinces_italy.json` | Config centralizzata 107 province italiane |
| `data/generate_provinces_config.py` | Script per rigenerare config da GeoJSON |
| `data/weather/shapefiles/province_italia.*` | Shapefile confini tutte le province |
| `CHANGELOG.md` | Questo file - registro modifiche |

### Impatto sullo Scheduler / Backend

Se il backend aveva gia' integrato la v1.0:
1. **CSV output**: Ora 107 righe invece di 9 - aggiornare eventuali parser che assumevano 9 province
2. **NUTS_3 values**: Nuovi slug per tutte le province (es. `roma`, `milano`, `napoli`). Il mapping slug→display_name e' in `data/provinces_italy.json`
3. **risk_score range**: Ora 0-4 invece di 1-5. Aggiornare eventuali soglie/condizioni
4. **risk_level**: Ora 0-4 con mapping a range (non rounding). Aggiornare eventuali switch/case
5. **Scheduler**: Nessun cambiamento nell'interfaccia, stesse opzioni CLI

### Formato Output CSV (Attuale)

```csv
NUTS_3,forecast_base,target_period_start,target_period_end,lead_weeks,risk_score,risk_level,risk_label,bbch_code,plant_susceptibility,temp,prec,rh,lw
bologna,2026-03-10,2026-03-09,2026-03-15,0,0.45,0,Nessun rischio rilevato,3,0.00,8.2,12.3,78.5,45
roma,2026-03-10,2026-03-09,2026-03-15,0,0.62,0,Nessun rischio rilevato,5,0.01,11.4,8.7,72.1,32
```

---

## [2026-02-27] - Espansione a tutte le province italiane

### Motivazione
Il modello era limitato alle 9 province dell'Emilia-Romagna. Ora copre tutte le 107 province italiane per fornire una copertura nazionale.

### Cosa cambia per il backend

**Output CSV**: i file `predictions/lead_0.csv` e `lead_1.csv` ora contengono **107 righe** (una per provincia) invece di 9.

Il formato dei campi resta identico. I nuovi valori `NUTS_3` sono slug come `roma`, `milano`, `napoli`, `palermo`, `l_aquila`, `forli_cesena` ecc.

### File di configurazione centralizzato

Nuovo file `data/provinces_italy.json` con tutte le 107 province:
```json
{
  "roma": {
    "display_name": "Roma",
    "prov_acr": "RM",
    "reg_name": "Lazio",
    "bbox": [11.7338, 41.4101, 13.2963, 42.296]
  },
  ...
}
```

Il backend puo' usare questo file per:
- Mappare slug -> nome display (`roma` -> `"Roma"`)
- Ottenere la sigla provincia (`"RM"`)
- Conoscere la regione di appartenenza (`"Lazio"`)

### File modificati

| File | Modifica |
|------|----------|
| `data/provinces_italy.json` | NUOVO - Config centralizzata 107 province |
| `data/generate_provinces_config.py` | NUOVO - Script per generare il config dal GeoJSON |
| `data/prepare_inference_data.py` | `TARGET_PROVINCES` caricato da `provinces_italy.json` |
| `plot_risk_map.py` | Mappa ora mostra tutta Italia, shapefile completo |

### File NON modificati
- `model.py` - Nessuna modifica (il modello non usa la provincia come feature)
- `backfill_predictions.py` - Si aggiorna automaticamente via import

### Performance
- Tempo pipeline: da ~30s a ~5-6 minuti (107 province invece di 9)
- Cache: cresce ~12x (circa 1.2 GB/anno)

### Mappa
- Centro mappa spostato su Italia (42.0, 12.5) con zoom 6
- Label sulle province: solo numero rischio (non nome, per leggibilita)
- Nome provincia visibile nel tooltip al hover

---

## [2026-02-25] - Cambio scala rischio da 1-5 a 0-4

### Motivazione
Gli agronomi trovano più intuitivo vedere valori bassi (es. 0.2) durante i periodi di dormienza della vite (gennaio-febbraio) piuttosto che valori come 1.2 che potrebbero sembrare già un rischio minimo.

### Modifiche effettuate

| File | Modifica |
|------|----------|
| `model.py` | `risk_score` ora in scala 0-4 (era 1-5) |
| `model.py` | `risk_level` ora 0-4 (era 1-5) |
| `risk_levels.json` | Chiavi cambiate da "1"-"5" a "0"-"4" |
| `backfill_predictions.py` | Stesso cambio scala 0-4 |
| `plot_risk_map.py` | Legenda aggiornata per scala 0-4 |

### Impatto sui dati

**Formula di conversione:**
```
nuovo_valore = vecchio_valore - 1
```

**Esempio:**
| Prima (1-5) | Dopo (0-4) | Label |
|-------------|------------|-------|
| 1.0 | 0.0 | Nessun rischio rilevato |
| 1.2 | 0.2 | Nessun rischio rilevato |
| 2.5 | 1.5 | Sorveglianza |
| 4.0 | 3.0 | Rischio elevato |
| 5.0 | 4.0 | Rischio molto elevato |

### Mapping livelli discreti

| Livello | Label | Colore |
|---------|-------|--------|
| 0 | Nessun rischio rilevato | Verde (#00cc00) |
| 1 | Sorveglianza | Giallo (#ffff00) |
| 2 | Attenzione | Arancione (#ffa500) |
| 3 | Rischio elevato | Arancione scuro (#ff6600) |
| 4 | Rischio molto elevato | Rosso (#ff0000) |

### Note per il backend
- I file CSV in `predictions/` e `predictions/history/` ora contengono valori 0-4
- Il campo `risk_score` è float (0.00-4.00)
- Il campo `risk_level` è int (0-4)
- Il campo `risk_label` rimane invariato (testo descrittivo)

### File NON modificati
- `model/` - I modelli XGBoost rimangono invariati (predizione interna 1-5)
- `data/` - I dati di input rimangono invariati

---

## [2026-02-25] - Miglioramenti UI Mappa

### Modifiche effettuate

| Modifica | Prima | Dopo |
|----------|-------|------|
| **Zoom iniziale** | Nord Italia visibile | Zoom automatico su Emilia-Romagna |
| **Font province** | 12px nome, 16px numero | 15px nome, 20px numero |
| **Legenda** | 200px, con footer | 240px, senza footer |
| **Titolo** | "Rischio Peronospora - Emilia-Romagna" | "Modello Previsionale Rischio Peronospora" |
| **Formato data** | YYYY-MM-DD | DD.MM.YYYY |
| **Layer satellite** | 3 opzioni con selector | Solo Esri Satellite (default) |
| **Navigazione settimane** | Dropdown layer control | Bottoni con date (es. "23.02.2026 - 01.03.2026") |

### Elementi rimossi
- Layer "Google Satellite"
- Layer "Labels"
- Layer Control (dropdown in alto a destra)
- Scritta "Peronospora Risk Model" nella legenda
- "Emilia-Romagna" dal titolo

### Nuova navigazione
Due bottoni sotto il titolo permettono di passare tra:
- **Bottone sinistro (◀)**: Settimana corrente con date
- **Bottone destro (▶)**: Prossima settimana con date

---

## [2026-02-25] - Nuova mappatura colori per range

### Motivazione
Con la mappatura precedente (rounding), un valore come 0.6 veniva arrotondato a 1 e mostrato in giallo, creando confusione. Ora i colori riflettono accuratamente i range di rischio.

### Nuova logica risk_level

| Range score | Livello | Colore | Label |
|-------------|---------|--------|-------|
| **0.0 - 1.0** | 0 | Verde (#00cc00) | Nessun rischio rilevato |
| **1.0 - 2.0** | 1 | Giallo (#ffff00) | Sorveglianza |
| **2.0 - 3.0** | 2 | Arancione (#ffa500) | Attenzione |
| **3.0 - 3.5** | 3 | Arancione scuro (#ff6600) | Rischio elevato |
| **3.5 - 4.0** | 4 | Rosso (#ff0000) | Rischio molto elevato |

### Differenza dalla versione precedente

| Score | Prima (rounding) | Dopo (range) |
|-------|------------------|--------------|
| 0.6 | Livello 1 (giallo) | **Livello 0 (verde)** |
| 1.4 | Livello 1 (giallo) | Livello 1 (giallo) |
| 2.8 | Livello 3 (arancione scuro) | **Livello 2 (arancione)** |
| 3.2 | Livello 3 (arancione scuro) | Livello 3 (arancione scuro) |

### File modificati
- `model.py` - funzione `get_risk_level()` usa range invece di rounding
- `backfill_predictions.py` - stessa logica
- `risk_levels.json` - aggiunto `range_min` e `range_max` per ogni livello
- `plot_risk_map.py` - nuova funzione `get_color_from_score()`, legenda mostra range

### Note per il backend
- Il campo `risk_level` ora usa la logica a range
- I colori nella mappa sono determinati dal `risk_score` continuo
- La legenda mostra i range (es. "0.0 - 1.0" invece di solo "0")

---
