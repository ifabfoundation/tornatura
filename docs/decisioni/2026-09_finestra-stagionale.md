# La finestra stagionale: in che fase sono oggi gli ospiti intorno al campo

2026-09-25 · Vito Palmisano, con Claude · stato: **adottata**

## Contesto

Dal 25/09/2026 *Il tuo paesaggio* dice quante piante ospiti della cimice ci sono intorno a un
campo (`docs/decisioni/2026-09_paesaggio-organismi.md`). Da solo il dato e' fermo tutto l'anno:
mais e soia contano come ospiti anche a febbraio, mentre la cimice li attacca solo quando il seme
matura. Per usarlo in campo serve sapere **quali ospiti sono oggi nella fase che l'organismo
attacca, quali ci arrivano e da che parte stanno**.

La fase di una coltura in una zona e in una settimana e' scritta nei bollettini di produzione
integrata della Regione ("Fase fenologica: ingrossamento frutti"), che il servizio `bollettini`
scarica gia' ogni giorno. L'esperimento `esperimenti/cimice_landscape/fenologia/` ha misurato se
quell'informazione si puo' estrarre **senza errori**, e come.

## Decisione

1. **Il servizio `bollettini` estrae la fase di ogni coltura** (`modules/fenologia/`) con un
   estrattore deterministico, senza modelli linguistici, e la espone in
   `GET /v1/bollettini/fenologia?lat&lng&date`: diciture del bollettino e intervallo **BBCH**
   (dizionario dicitura -> codice sulla monografia BBCH). E' un'informazione generica, valida per
   qualsiasi organismo.
2. **Il servizio `landscape` confronta quelle fasi con la finestra dell'organismo**
   (`GET /v1/landscape/pest-season`): la finestra sta nella cartella dati dell'organismo
   (`data/pests/<codice>/meta.json`, chiave `season`, con le fonti), la corrispondenza specie
   AGREA -> coltura del bollettino e' generica (`data/phenology/agrea_bollettini.json`). Classi:
   nella fase che attacca, in arrivo, non ancora, conclusa, fase non disponibile, senza finestra.
   Direzione in otto settori.
3. **Il paesaggio chiama i bollettini via HTTP sulla rete interna, con riserva**: se il servizio
   non risponde entro 4 s si usa il calendario 2026 (la stessa tabella verificata, alla stessa data
   dell'anno) e la risposta lo dichiara (`source`). La pagina non si rompe mai per l'altro servizio.
4. **Nessuna dipendenza nuova.** Il testo del PDF si legge con pypdfium2, che il servizio ha gia'
   con Docling (vedi "Conseguenze").

## Perche' i bollettini e non altro

- Le date AGREA di inizio e fine utilizzo sono amministrative (93% inizia l'11/11/2025): non dicono
  la fase. Un modello a gradi-giorno per ogni coltura andrebbe tarato coltura per coltura; il
  bollettino e' l'osservazione dei tecnici della zona, settimanale, gia' in casa.
- **Verifica** (esperimento, 25/09/2026, 165 bollettini ER 2026, 5.142 righe di fase):
  tre letture testuali indipendenti, una lettura geometrica di **ogni** riga dal disegno del PDF,
  due letture visive alla cieca delle pagine corrette; campione casuale di 278 righe con errore
  < 1,07% al 95%; nessuna regressione stagionale su 88 serie. Due errori sistematici trovati e
  corretti: le **revisioni di Word rimaste visibili** nel PDF (testo cancellato ancora stampato,
  barrato, attaccato al nuovo: bollettino 6 del 18/03/2026 di Bologna e Ferrara) e il **trattino
  a fine riga** tolto da Poppler e Docling ("pre-seminasemina").
- L'**estrattore del servizio** (pypdfium2, barrato tolto dalla geometria, trattini rimessi)
  riproduce le 5.142 righe verificate **tutte**, senza agenti.
- **Dizionario BBCH**: 630 diciture delle colture ospiti tradotte alla cieca da due lettori sulla
  monografia (Meier 2001) e, nei 25 casi non concordi, da tre arbitri; 4 decisi con la
  progressione delle settimane (la fase non torna indietro). Correzioni venute dalla verifica: gemme
  di pomacee e drupacee sulla serie a fiore (51-53), allegagione 69 per olivo, kaki, noce e kiwi.

## Alternative scartate

- **Estrazione con un modello linguistico**: non verificabile riga per riga; le regole
  deterministiche portano file e riga di ogni fase.
- **Fenologia dentro `landscape`** (leggere i PDF li'): duplicherebbe download e archivio, e la
  fase servira' anche ad altre pagine (rilevamenti, peronospora).
- **Cultivar AGREA** (`DESC_VARI`, compilata per pero, melo, pesco, albicocco, susino, kiwi al
  56-82%): nei bollettini 2026 solo 42 righe ospiti su 1.750 distinguono per cultivar e, per le
  colture con varieta' in AGREA, le parti cadono sempre nella stessa classe. Servira' solo per
  prevedere la *fine* della finestra (raccolta per varieta'), con un calendario varietale con fonti.
- **Rigenerare il lockfile di `bollettini` per dichiarare pypdfium2**: il 25/09 avrebbe cambiato
  58 pacchetti (torch, docling-core, opencv 4 -> 5). Troppo rischio per la conversione dei report.

## Cuciture

- `bollettini`: `modules/fenologia/` (testo, regole, bbch, archivio, verifica), passo 2b in
  `run_pipeline.py` (un suo errore non cambia l'esito della pipeline), endpoint in `api.py`.
  Archivio `data/fenologia.sqlite` sul volume, costruito dallo scheduler.
- `landscape`: `modules/season.py`, endpoint in `api.py`, `data/phenology/`, chiave `season` in
  `data/pests/halyha/meta.json`, variabile `LANDSCAPE_BOLLETTINI_API_URL`.
- `web`: `PestSeasonBlock.tsx` dentro `PestHabitatSection`, `fetchLandscapePestSeason`.
- Il core non si tocca.

## Verifica

```
python -m bollettini.modules.fenologia.verifica <cartella PDF ER 2026>   # 630/630 e 5142/5142
GET /v1/bollettini/fenologia?lat=44.80951&lng=11.75644&date=2026-06-10
GET /v1/landscape/pest-season?lat=44.80951&lng=11.75644&radius_m=3000&pest=halyha&date=2026-06-10
```
Attesi a Ferrara, 3 km, 10/06/2026 (curva dell'esperimento): nella fase che attacca 35,5%
(pero e melo), in arrivo 32,4%.

## Conseguenze

- Tre immagini da rilasciare: `bollettini`, `landscape`, `web`. Lo scheduler dei bollettini
  costruisce l'archivio al primo avvio (circa 176 PDF, qualche minuto).
- pypdfium2 arriva **attraverso docling** (4.30.0 nel lock): chi aggiorna docling deve rilanciare
  `verifica` prima del rilascio.
- Il calendario di riserva e' del 2026: nel 2027, se i bollettini non rispondono, la pagina
  mostra la stagione dell'anno prima e lo dice.
