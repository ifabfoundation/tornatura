# Peronospora Risk Prediction - Developer Guide
## Guida Tecnica Completa per Sviluppatori

**Versione**: 2.0
**Data**: Marzo 2026
**Copertura**: tutte le 107 province italiane
**Sistema**: Pipeline di inferenza per predizione rischio peronospora su vite

---

## 📋 Indice

1. [Architettura del Sistema](#architettura)
2. [Script Principali](#script-principali)
3. [Flusso Operativo](#flusso-operativo)
4. [Struttura Dati](#struttura-dati)
5. [API e Interfacce](#api-interfacce)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

---

## 1. Architettura del Sistema {#architettura}

### Overview

Il sistema è composto da 3 componenti principali:

```
┌─────────────────────────────────────────────────────────────┐
│                    ECMWF S3 Bucket                          │
│              (Dati meteo forecast giornalieri)              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  DATA PREPARATION                            │
│  prepare_inference_data.py                                   │
│  • Scarica dati da S3                                        │
│  • Cache dati storici (T+24h)                               │
│  • Calcola fenologia (dormancy, forcing, BBCH)              │
│  • Calcola infezioni (Rule310, DMCast, Misfits)            │
│  • Aggrega a settimane ISO                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   MODEL INFERENCE                            │
│  model.py                                                    │
│  • Carica modelli XGBoost (Lead 0, Lead 1)                 │
│  • Genera predizioni rischio (0-4)                          │
│  • Salva in predictions/ + history/                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  VISUALIZATION                               │
│  plot_risk_map.py                                           │
│  • Genera mappa interattiva HTML                            │
│  • Overlay su satellite                                     │
└─────────────────────────────────────────────────────────────┘
```

### Modello Temporale

**ISO Week Based**: Il modello predice il rischio aggregato per settimane ISO.

```
ISO Week = Settimana che va da Lunedì a Domenica
Week 1 = Prima settimana dell'anno con almeno 4 giorni
```

**Lead Times**:
- **Lead 0**: Settimana corrente (0-6 giorni avanti)
- **Lead 1**: Settimana successiva (7-13 giorni avanti)

**Miglioramento Progressivo**: Ogni giorno della settimana, più dati reali (T+24h) sostituiscono il forecast, migliorando l'accuratezza.

| Giorno | Dati Reali | Forecast | Accuratezza |
|--------|-----------|----------|-------------|
| Lunedì | 0% | 100% | ⭐ |
| Venerdì | 57% | 43% | ⭐⭐⭐⭐ |
| Domenica | 86% | 14% | ⭐⭐⭐⭐⭐ |

---

## 2. Script Principali {#script-principali}

### 2.1 `run_inference_pipeline.py`

**Scopo**: Script principale che orchestra l'intera pipeline.

**Cosa fa**:
1. Scarica dati meteo aggiornati (chiama `prepare_inference_data.py`)
2. Genera predizioni (chiama `model.py`)
3. Crea mappa interattiva (chiama `plot_risk_map.py`)

**Uso**:
```bash
# Run completo
python run_inference_pipeline.py

# Opzioni
python run_inference_pipeline.py --skip-data-prep  # Salta download dati
python run_inference_pipeline.py --no-map          # Salta mappa
python run_inference_pipeline.py --lead 0          # Solo Lead 0
```

**Output**:
- `predictions/lead_0.csv` - Predizioni Lead 0 (corrente)
- `predictions/lead_1.csv` - Predizioni Lead 1 (prossima settimana)
- `predictions/history/YYYY-MM-DD_lead_X.csv` - Storico
- `risk_map_satellite.html` - Mappa interattiva

**Frequenza**: **Giornaliera** (idealmente ogni mattina)

---

### 2.2 `data/prepare_inference_data.py`

**Scopo**: Scarica dati meteo, calcola fenologia e prepara feature per il modello.

**Cosa fa**:

#### Step 1: Download Intelligente da S3
```python
# Identifica file su S3
files_by_date = list_all_s3_files()
sorted_dates = sorted(files_by_date.keys())
latest_date = sorted_dates[-1]  # Ultima data disponibile

# Separa storico da forecast
historical = tutte le date tranne ultima  # T+24h → CACHE
forecast = ultima data                    # T+0 a T+240h → NO CACHE
```

**Logica Caching**:
- **Dati storici** (T+24h): Salvati in `data/weather/cache/`
  - Sono previsioni fatte ieri per oggi → molto accurate
  - Persistenti, non riscaricati
- **Forecast recente** (T+0 a T+240h): NON cached
  - Usato per calcoli e buttato
  - Riscaricato ogni volta

#### Step 2: Calcoli Fenologici

Per ogni provincia:
1. **Dormancy Model**: Accumulo freddo invernale
2. **Forcing Model**: Accumulo calore primaverile → BBCH code
3. **Plant Susceptibility**: Vulnerabilità della pianta (0-1)

#### Step 3: Modelli di Infezione

Tre modelli eseguiti ogni ora:
- **Rule310**: Basato su temperatura + umidità
- **DMCast**: Disease Management Cast
- **Misfits**: Leaf wetness based

#### Step 4: Aggregazione Settimanale

Dati giornalieri → ISO Week:
- Temperature: medie
- Precipitazioni: somma
- BBCH: ultimo valore
- Infezioni: somma eventi

#### Step 5: Feature Engineering

20 features per il modello:
```python
features = [
    'bbch_code',                           # Stadio fenologico
    'plant_susceptibility',                # Suscettibilità
    'bbch_code_velocity',                  # Δ BBCH settimanale
    'plant_susceptibility_velocity',       # Δ Suscettibilità
    'forcing_state_velocity',              # Δ Forcing
    'bbch_code_acceleration',              # ΔΔ BBCH
    'plant_susceptibility_acceleration',   # ΔΔ Suscettibilità
    'temp', 'temp_dew', 'prec',           # Meteo settimanale
    'rh', 'wind_10m', 'lw',               # Meteo
    'rule310', 'rule310_cum',             # Infezioni
    'dmcast', 'dmcast_cum',               # Infezioni
    'misfits', 'misfits_cum',             # Infezioni
    'week_cos'                             # Stagionalità
]
```

**Output**:
- `data/weather/cache/` - Cache meteo storico
- `data/weather/forecast/` - Forecast 10gg per app
- `data/phenology/phenology_csv/` - Fenologia giornaliera
- `data/dataframe_inference/lead_0.csv` - Dataset per modello Lead 0
- `data/dataframe_inference/lead_1.csv` - Dataset per modello Lead 1

**Uso**:
```bash
python data/prepare_inference_data.py
python data/prepare_inference_data.py --clear-cache  # Forza re-download
python data/prepare_inference_data.py --list-only    # Solo lista date S3
```

---

### 2.3 `model.py`

**Scopo**: Esegue inferenza con modelli XGBoost addestrati.

**Cosa fa**:
1. Carica modelli da `model/near_term_lead_X/`
2. Legge dataset da `data/dataframe_inference/lead_X.csv`
3. Genera predizioni (0-4)
4. Salva risultati

**Architettura Modello**:
```
XGBoost Regressor
├─ Input: 20 features
├─ Output interno: 1-5 (continuo)
├─ Output finale: risk_score (0-4, continuo) = output_interno - 1
├─ Discretizzazione: range-based mapping → risk_level (0-4)
│    0.0-1.0 → 0, 1.0-2.0 → 1, 2.0-3.0 → 2, 3.0-3.5 → 3, 3.5-4.0 → 4
└─ Training: 2012, 2013, 2014, 2016, 2017 (LOYO CV)
```

**Metriche Performance** (Test 2015):
- Lead 0: MAE=0.661, R²=0.352
- Lead 1: MAE=0.660, R²=0.353

**Output**:
```csv
NUTS_3,forecast_base,target_period_start,target_period_end,lead_weeks,risk_score,risk_level,risk_label,temp,prec,rh,lw
bologna,2026-01-14,2026-01-12,2026-01-18,0,1.24,1,Sorveglianza,4.6,20.4,91.4,83
```

**Livelli di rischio** (da `risk_levels.json`):
- Level 0: "Nessun rischio rilevato"
- Level 1: "Sorveglianza"
- Level 2: "Attenzione"
- Level 3: "Rischio elevato"
- Level 4: "Rischio molto elevato"

**Mappatura risk_score → risk_level** (range-based):
- 0.0-1.0 → Level 0
- 1.0-2.0 → Level 1
- 2.0-3.0 → Level 2
- 3.0-3.5 → Level 3
- 3.5-4.0 → Level 4

**Uso**:
```bash
python model.py --all              # Tutti i lead
python model.py --lead 0           # Solo Lead 0
python model.py --no_summary       # Senza stampa summary
```

---

### 2.4 `plot_risk_map.py`

**Scopo**: Crea mappa interattiva HTML con rischio per provincia.

**Cosa fa**:
1. Legge predizioni da `predictions/lead_0.csv`
2. Legge `data/provinces_italy.json` per mappatura nomi province
3. Carica shapefile `province_italia.shp` da `data/weather/shapefiles/`
4. Crea mappa Folium con overlay satellite (centro: 42.0, 12.5, zoom 6)
5. Colora province per livello rischio
6. Fit bounds su Emilia-Romagna per default

**Legenda Colori**:
```
0 - Verde:        Nessun rischio rilevato
1 - Giallo:       Sorveglianza
2 - Arancione:    Attenzione
3 - Arancione scuro: Rischio elevato
4 - Rosso:        Rischio molto elevato
```

**Output**: `risk_map_satellite.html`

---

### 2.5 `backfill_predictions.py`

**Scopo**: Genera predizioni storiche per tutti i giorni dal 1 Gennaio.

**Perché serve**:
- Popolare lo storico predizioni
- Consentire analisi retrospettive
- Tracking evoluzione predizioni durante la settimana

**Cosa fa**:
1. Legge cache meteo (solo dati già scaricati)
2. Per ogni giorno: calcola fenologia + inferenza
3. Genera file `history/YYYY-MM-DD_lead_X.csv`
4. **Salta automaticamente** giorni già processati

**IMPORTANTE**: 
- Usa SOLO dati in cache (non scarica nulla)
- Lanciare DOPO `prepare_inference_data.py`
- Le predizioni sono "ideali" (con dati reali T+24h)

**Uso**:
```bash
python backfill_predictions.py                # Riempie buchi
python backfill_predictions.py --force        # Rigenera tutto
python backfill_predictions.py --start-week 5 # Dalla settimana 5
```

**Limitazioni Lead_1**:
Lead 1 può mancare per giorni vicini alla fine della cache (settimana target non disponibile).

---

### 2.6 `scheduler.py`

**Scopo**: Scheduler automatico per esecuzione giornaliera della pipeline.

**Architettura**: Usa APScheduler con BlockingScheduler e CronTrigger per esecuzione affidabile.

**Sezioni del Codice**:

| Sezione | Descrizione |
|---------|-------------|
| **1. CONFIGURAZIONE** | Percorsi file, orario esecuzione (09:00 CET), timezone |
| **2. LOGGING** | Sistema log su file (mensile) + console |
| **3. VERIFICA DATI S3** | Controlla disponibilità dati meteo prima dell'esecuzione |
| **4. ESECUZIONE PIPELINE** | Lancio run_inference_pipeline.py con gestione errori/timeout |
| **5. SCHEDULER** | APScheduler con trigger cron giornaliero |
| **6. CLI** | Argomenti command-line (--run-now, --check-data) |

**Configurazione Orario**:
```python
# L'esecuzione avviene alle 09:00 CET/CEST
# ECMWF pubblica i dati tra 06:45-08:34, quindi 09:00 è sicuro
SCHEDULE_HOUR = 9
SCHEDULE_MINUTE = 0
TIMEZONE = "Europe/Rome"
```

**Modalità di Esecuzione**:
```bash
# 1. Avvia scheduler (esegue alle 09:00 ogni giorno)
python scheduler.py

# 2. Esegui pipeline immediatamente (per test)
python scheduler.py --run-now

# 3. Verifica disponibilità dati S3
python scheduler.py --check-data
```

**Esecuzione in Background**:
```bash
# Con nohup (semplice)
nohup python scheduler.py > logs/scheduler_output.log 2>&1 &

# Con systemd (raccomandato - vedi sezione Deployment)
sudo systemctl start peronospora-inference
```

**Log Files**:
- Directory: `logs/`
- Nome: `scheduler_YYYYMM.log` (rotazione mensile)
- Formato: `TIMESTAMP | LEVEL | MESSAGE`

**Gestione Errori**:
- Timeout pipeline: 30 minuti
- Grace period job mancati: 1 ora
- La pipeline esegue anche se dati S3 non disponibili (usa cache)

---

## 3. Flusso Operativo {#flusso-operativo}

### 3.1 Setup Iniziale (Prima Volta)

```bash
# 1. Clona/ricevi la cartella inference
cd /path/to/inference

# 2. Crea virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Installa dipendenze
pip install -r requirements.txt

# 4. Scarica dati dal 1 Gennaio
python data/prepare_inference_data.py

# 5. Genera predizioni storiche
python backfill_predictions.py

# 6. Test pipeline completa
python run_inference_pipeline.py
```

### 3.2 Operazione Giornaliera

**Opzione 1: Scheduler Python (raccomandato)**:
```bash
# Avvia scheduler in background (esegue alle 09:00 ogni giorno)
cd /path/to/inference
source venv/bin/activate
nohup python scheduler.py > logs/scheduler_output.log 2>&1 &
```

**Opzione 2: Cron job**:
```bash
crontab -e
# Aggiungi (esecuzione alle 09:00 CET):
0 9 * * * cd /path/to/inference && source venv/bin/activate && python run_inference_pipeline.py >> logs/cron.log 2>&1
```

**Opzione 3: Manuale (per test)**:
```bash
cd /path/to/inference
source venv/bin/activate
python run_inference_pipeline.py
# oppure
python scheduler.py --run-now
```

### 3.3 Recovery Dopo Interruzione

Se la pipeline non gira per N giorni:

```bash
# 1. Scarica dati mancanti
python data/prepare_inference_data.py

# 2. Riempie buchi nello storico
python backfill_predictions.py

# 3. Riprendi operazione normale
python run_inference_pipeline.py
```

---

## 4. Struttura Dati {#struttura-dati}

### 4.1 Directory Tree

```
inference/
├── data/
│   ├── weather/
│   │   ├── cache/              # Dati storici T+24h (PERSISTENTE)
│   │   │   ├── hourly/
│   │   │   │   └── bologna.csv (24h * N giorni)
│   │   │   └── daily/
│   │   │       └── bologna.csv (N giorni)
│   │   ├── forecast/           # Forecast 10gg per app (GIORNALIERO)
│   │   │   └── bologna_forecast.csv
│   │   └── shapefiles/         # Confini province (STATICO)
│   │       └── province_italia.*  # Shapefile tutte le 107 province italiane
│   ├── phenology/              # Moduli calcolo fenologia
│   │   ├── dormancy.py
│   │   ├── forcing.py
│   │   ├── infections/
│   │   │   ├── rule310.py
│   │   │   ├── dmcast.py
│   │   │   └── misfits.py
│   │   ├── parameters/         # Parametri modelli (STATICO)
│   │   │   ├── octoPusParameters.csv
│   │   │   └── hostSusceptibilityParameters.csv
│   │   └── phenology_csv/      # Output fenologia (TEMP)
│   │       └── bologna_2026.csv
│   ├── provinces_italy.json    # Config centralizzata 107 province
│   ├── generate_provinces_config.py  # Script generazione config
│   └── dataframe_inference/    # Dataset per modello (TEMP)
│       ├── lead_0.csv
│       └── lead_1.csv
├── model/
│   ├── near_term_lead_0/
│   │   ├── model.json          # XGBoost model (STATICO)
│   │   ├── config.json         # Feature list + params
│   │   └── metrics.json        # Performance metrics
│   └── near_term_lead_1/
│       └── ...
├── predictions/
│   ├── lead_0.csv              # Ultima predizione (AGGIORNATO)
│   ├── lead_1.csv
│   └── history/                # Storico giornaliero (APPEND)
│       ├── 2026-01-01_lead_0.csv
│       ├── 2026-01-01_lead_1.csv
│       └── ...
├── risk_map_satellite.html     # Mappa interattiva (AGGIORNATO)
├── requirements.txt
├── CHANGELOG.md                # Registro modifiche per il backend
├── logs/                       # Log scheduler (rotazione mensile)
│   └── scheduler_YYYYMM.log
└── venv/                       # NON INCLUDERE NEL PACKAGE
```

### 4.2 File Persistenti vs Temporanei

| Tipo | Esempi | Persistenza |
|------|--------|-------------|
| **STATICI** | `model/`, `parameters/`, `shapefiles/` | Mai cambiare |
| **CACHE** | `weather/cache/` | Append-only, cresce nel tempo |
| **STORICO** | `predictions/history/` | Append-only, cresce nel tempo |
| **CORRENTI** | `predictions/lead_X.csv`, `risk_map.html` | Sovrascitto giornalmente |
| **TEMP** | `phenology_csv/`, `dataframe_inference/` | Rigenerato ogni run |

### 4.3 Formato Predizioni

**Corrente** (`predictions/lead_0.csv`):
```csv
NUTS_3,forecast_base,target_period_start,target_period_end,lead_weeks,risk_score,risk_level,risk_label,temp,prec,rh,lw
bologna,2026-01-14,2026-01-12,2026-01-18,0,1.24,1,Sorveglianza,4.6,20.4,91.4,83
ferrara,2026-01-14,2026-01-12,2026-01-18,0,1.26,1,Sorveglianza,5.0,17.7,91.7,81
...
```

**Campi**:
- `NUTS_3`: Codice provincia
- `forecast_base`: Data in cui è stata fatta la predizione
- `target_period_start/end`: Periodo di riferimento (settimana ISO)
- `lead_weeks`: 0 o 1
- `risk_score`: Rischio continuo (0.00-4.00)
- `risk_level`: Rischio discreto (0-4)
- `risk_label`: Testo descrittivo
- `temp, prec, rh, lw`: Feature meteo aggregate sulla settimana

---

## 5. API e Interfacce {#api-interfacce}

### 5.1 Uso Programmatico di `model.py`

```python
from model import PeronospotaPredictor

# Inizializza predictor
predictor = PeronospotaPredictor(model_dir="model", verbose=True)

# Carica modelli
predictor.load_all_models(horizon="near_term")

# Predici per un dataset custom
predictions_lead0 = predictor.predict(
    data_path="path/to/data.csv",
    lead=0
)

# Salva risultati
predictor.save_predictions(
    predictions_lead0,
    output_path="output/predictions.csv",
    lead=0
)
```

### 5.2 Integrazione App

**Endpoint suggeriti**:

```
GET /api/risk/current
→ Restituisce predictions/lead_0.csv

GET /api/risk/forecast
→ Restituisce predictions/lead_1.csv

GET /api/risk/history?start=2026-01-01&end=2026-01-14
→ Restituisce range da predictions/history/

GET /api/weather/forecast/{province}
→ Restituisce data/weather/forecast/{province}_forecast.csv

GET /api/map
→ Restituisce risk_map_satellite.html

GET /api/provinces
→ Restituisce data/provinces_italy.json
```

### 5.3 Formato JSON per App

Esempio conversione:
```python
import pandas as pd
import json

df = pd.read_csv('predictions/lead_0.csv')
output = {
    "forecast_date": df['forecast_base'].iloc[0],
    "target_week": {
        "start": df['target_period_start'].iloc[0],
        "end": df['target_period_end'].iloc[0]
    },
    "provinces": df.to_dict(orient='records')
}

with open('api_response.json', 'w') as f:
    json.dump(output, f, indent=2)
```

---

## 6. Deployment {#deployment}

### 6.1 Requisiti Sistema

**Minimi**:
- CPU: 2 cores
- RAM: 4 GB
- Disco: 20 GB (cache cresce ~1.2 GB/anno per 107 province)
- OS: Linux (Ubuntu 20.04+, Debian 11+)

**Dipendenze**:
```
Python 3.8+
pandas >= 2.0.0
numpy >= 1.24.0
xgboost >= 2.0.0
xarray >= 2023.1.0
cfgrib >= 0.9.10
boto3 >= 1.28.0
folium >= 0.14.0
geopandas >= 0.14.0
scipy >= 1.10.0  # Usato da phenology (forcing/dormancy)
```

### 6.2 Credenziali AWS S3

**Necessarie** per accesso bucket ECMWF:
```bash
# Metodo 1: Environment variables
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=yyy
export AWS_DEFAULT_REGION=eu-west-1

# Metodo 2: AWS CLI config
aws configure
```

### 6.3 Containerizzazione (Docker)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Installa dipendenze sistema
RUN apt-get update && apt-get install -y \
    libeccodes0 \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia applicazione
COPY . .

# Volume per cache persistente
VOLUME ["/app/data/weather/cache", "/app/predictions/history"]

# Comando default
CMD ["python", "run_inference_pipeline.py"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  inference:
    build: .
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    volumes:
      - ./data/weather/cache:/app/data/weather/cache
      - ./predictions/history:/app/predictions/history
    restart: unless-stopped
```

### 6.4 Systemd Service

**Opzione A: Usare scheduler.py (Raccomandato)**

Lo scheduler Python gestisce internamente l'esecuzione alle 09:00 CET.

```ini
# /etc/systemd/system/peronospora-scheduler.service
[Unit]
Description=Peronospora Inference Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/inference
Environment="PATH=/path/to/inference/venv/bin"
ExecStart=/path/to/inference/venv/bin/python scheduler.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

```bash
# Attiva servizio
sudo systemctl daemon-reload
sudo systemctl enable peronospora-scheduler
sudo systemctl start peronospora-scheduler

# Controlla stato
sudo systemctl status peronospora-scheduler

# Visualizza logs
sudo journalctl -u peronospora-scheduler -f
```

**Opzione B: Usare systemd Timer**

Timer separato per esecuzione diretta della pipeline.

```ini
# /etc/systemd/system/peronospora-inference.service
[Unit]
Description=Peronospora Inference Pipeline (One-shot)
After=network.target

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/inference
Environment="PATH=/path/to/inference/venv/bin"
ExecStart=/path/to/inference/venv/bin/python run_inference_pipeline.py
```

```ini
# /etc/systemd/system/peronospora-inference.timer
[Unit]
Description=Run Peronospora Inference daily at 09:00 CET

[Timer]
OnCalendar=*-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# Attiva timer
sudo systemctl daemon-reload
sudo systemctl enable peronospora-inference.timer
sudo systemctl start peronospora-inference.timer

# Verifica prossima esecuzione
sudo systemctl list-timers peronospora-inference.timer
```

---

## 7. Troubleshooting {#troubleshooting}

### 7.1 Problemi Comuni

#### "No module named 'cfgrib'"
```bash
# Installa eccodes
sudo apt-get install libeccodes0
pip install cfgrib
```

#### "AWS credentials not found"
```bash
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=yyy
```

#### "No files found in S3"
```bash
# Verifica connessione S3
python data/prepare_inference_data.py --list-only
```

#### "Cache too old"
```bash
# Forza re-download
python data/prepare_inference_data.py --clear-cache
```

#### "Lead_1 predictions missing"
**Normale** - Lead 1 richiede dati della settimana successiva. Per giorni vicini alla fine dei dati disponibili, lead_1 sarà assente.

### 7.2 Logs e Debugging

**Aumenta verbosità**:
```python
# In prepare_inference_data.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Controlla cache**:
```bash
python -c "
import pandas as pd
df = pd.read_csv('data/weather/cache/daily/bologna.csv')
print(f'Cache: {df[\"date\"].min()} to {df[\"date\"].max()}')
print(f'Days: {len(df)}')
"
```

**Valida predizioni**:
```bash
python -c "
import pandas as pd
df = pd.read_csv('predictions/lead_0.csv')
print(df.describe())
print(df['risk_level'].value_counts())
"
```

### 7.3 Performance

**Tempi Tipici**:
- `prepare_inference_data.py`: 5-6 min (incrementale con 107 province)
- `backfill_predictions.py`: 1-2 min/giorno
- `model.py`: <10s
- `plot_risk_map.py`: <5s

**Nota**: Con 107 province il tempo di elaborazione incrementale e' significativamente maggiore rispetto alle precedenti 9 province dell'Emilia-Romagna.

**Ottimizzazioni**:
- Cache già popolato → molto più veloce
- Usare `--skip-data-prep` se dati già pronti
- Parallelizzare calcolo fenologia (TODO)

---

## 8. Note Finali

### 8.1 Limitazioni Note

1. **Dati storici S3**: Il bucket ECMWF deve mantenere dati tutto l'anno
2. **Lead_1 giorni iniziali**: Può mancare per settimane incomplete
3. **Fenologia fissa**: Parametri da `octoPusParameters.csv` non dinamici
4. **Training anni**: Modello addestrato 2012-2017, testato su 2015

### 8.2 Prossimi Sviluppi

- [x] Espansione a tutte le 107 province italiane (DONE - Marzo 2026)
- [ ] Calcolo fenologia parallelizzato
- [ ] Archivio forecast originali per simulazioni realistiche
- [ ] API REST nativa
- [ ] Dashboard web real-time
- [ ] Notifiche automatiche (email/SMS) su alto rischio
- [ ] ML model retraining pipeline

### 8.3 Contatti Supporto

**Tecnico**: [Da definire]  
**Repository**: [Da definire]  
**Documentazione**: Questo file + docstrings nel codice

---

**Fine Developer Guide**
