# Landscape (paesaggio agricolo) — Sistema di Produzione

Componente del monorepo **tornatura** (`src/python/landscape`). Fa due cose:

1. Dato un punto e un raggio, calcola la **composizione colturale del paesaggio**
   circostante da due sorgenti indipendenti, e alimenta la pagina *"Il tuo
   paesaggio"* nella scheda del campo.
2. Serve i **pezzi dichiarati** con cui comporre il confine di un campo nuovo nel
   wizard "Aggiungi campo", invece di tracciarlo a mano.

Principio guida della prima: **contesto e consapevolezza, non rischio.** Il dato
dice cosa c'è intorno, non quanto sia probabile un'infezione.

Principio guida della seconda: **il disegno a mano resta sempre possibile.** I
pezzi mancano spesso e la loro assenza non deve mai impedire di procedere. Il
wizard parte in selezione (`simple_select`) perche' scegliere un confine
dichiarato e' la strada piu' breve e piu' precisa; il pulsante del poligono apre
il disegno a mano, e mentre lo si usa il click sui pezzi viene ignorato.

## Architettura

- **Terzo servizio modello**, gemello di `bollettini` e `peronospora`: FastAPI
  senza autenticazione, consumato dal frontend sotto lo stesso origin
  (`/v1/landscape/*`).
- **Nessuno scheduler**: i dataset sono annuali. Due `pex_binary`: `api` e
  `updater`, quest'ultimo gemello dello `scheduler` di peronospora ma invocato a
  mano invece che ogni giorno.
- **Il core non è coinvolto**: nessuna modifica a Mongo, Keycloak, permessi o SDK.
- **Due sorgenti** con ruoli diversi (sotto).

## Le due sorgenti

| | AGREA | iColt (ARPAE) |
|---|---|---|
| natura | dichiarazione per la PAC | classificazione satellitare, solo immagini invernali |
| ruolo | **principale** | **controllo indipendente** |
| granularità | 311 specie nominate | 16 classi |
| copertura | anche collina e Appennino | pianura; cieca sopra 200 m o 15% di pendenza |
| bosco, siepi | 179.460 + 34.460 ha | assenti |
| completezza | solo aziende che dichiarano | tutti i campi |
| licenza | **non dichiarata** | CC BY 4.0 |
| dove | volume `/data/landscape/agrea/` (~1 GB) | dentro il pex (34 MB) |

`modules/landscape.py` porta iColt e la funzione `composition_with_sources()` che
combina; `modules/agrea.py` porta AGREA. **Se i file AGREA mancano tutto ricade su
iColt**, senza errori: verificato avviando con un volume vuoto.

Perché tenere iColt: l'accordo geometrico particella per particella fra le due è
circa l'**80%**, non il 100%. In pianura, dove esistono entrambe, quel disaccordo
è l'unica stima onesta dell'incertezza che si può mostrare, e la pagina la scrive.

## Struttura del package

```
src/python/landscape/
├── api.py                  # FastAPI: health, coverage, composition, parcels,
│                           #   pieces, parcel-at
├── paths.py                # iColt statico nel pex; AGREA e log sul volume
├── updater.py              # CLI: prepara i dati AGREA sul volume
├── BUILD                   # target Pants (due pex_binary: api, updater)
├── data/
│   └── icolt2026_er.parquet # layer iColt 2026 (EPSG:4326, particelle > 0,5 ha)
└── modules/
    ├── config.py           # classi, famiglie, mappatura colture, soglie
    ├── landscape.py        # sorgente iColt + combinazione delle due
    ├── agrea.py            # sorgente AGREA, ai due livelli di granularità
    └── agrea_prepare.py    # dall'archivio pubblico ai tre GeoParquet
```

## Due granularità, due scopi

Il dato AGREA ha tre livelli e ne usiamo due. La riga dello shapefile è
l'**intersezione** fra l'appezzamento dichiarato e la particella catastale: il
file si chiama `Uti_Part` = *utilizzi per particella*.

| | appezzamento | pezzo |
|---|---|---|
| cos'è | frammenti dissolti per (azienda, `ID_APPEZ`) | il frammento come sta nel dato |
| file | `agrea<anno>_colture_er.parquet` | `agrea<anno>_parcelle_er.parquet` |
| soglia | 0,05 ha | 0,25 ha |
| semplificato | sì, 1 m | **no** (vedi sotto) |
| serve a | *"Il tuo paesaggio"* | disegnare il campo |
| endpoint | `/composition`, `/parcels` | `/pieces` |
| quanti (Ferrara) | 196.972 | 375.303 frammenti, 97.754 sopra soglia |
| quanti (regione) | 824.326 · 291 MB | 874.974 · 696 MB |

Controllo che giustifica l'appezzamento come unità agronomica: su 196.972, **zero**
contengono più di una coltura.

**Perché la soglia non è "il minimo assoluto".** Il frammento mediano misura 0,04
ha (400 m²) e il 51,8% dei frammenti sta sotto 0,05 ha valendo insieme l'1,27%
della superficie: sono le schegge dove una linea di *proprietà* taglia un campo di
sbieco, bordi che sul terreno non si vedono. A 0,25 ha si tiene il 94,5% della
superficie e i pezzi sono poligoni semplici nel 91,9% dei casi, contro il 71,6%
degli appezzamenti interi.

**Perché sui pezzi non si semplifica né si arrotonda.** `simplify` lavora un
poligono per volta: due pezzi confinanti verrebbero semplificati in modo
indipendente e il bordo comune si aprirebbe, riempiendo di fessure l'unione dei
pezzi scelti dall'utente. Nel dato grezzo i pezzi confinanti si toccano entro 1 cm
nel 99,8% dei casi (distanza minima mediana 0,000 m): è questa proprietà che rende
pulita l'unione. Vale anche per `set_precision`, in entrambe le modalità — vedi
`CHANGELOG.md`.

## L'unione dei pezzi e il vincolo del database

`AgriFieldModel.map` è `ListField(EmbeddedDocumentField(Point))`: **un anello
solo**, senza parti staccate e senza buchi. L'unione dei pezzi scelti va quindi
ridotta, e ciò che si perde va **detto**. `contornoDaPezzi()` nel frontend tiene
la parte più grande, chiude i buchi sotto 100 m² (rumore del calcolo) e riporta
quante parti ha scartato e quanti m² di vuoto reale ha inglobato.

Misurato su 3.000 campi con almeno due pezzi: unendo **tutti** i pezzi di un campo
dichiarato l'unione è un solo poligono nel 69,0% dei casi; unendo solo i pezzi
**adiacenti** a quello cliccato, nel **94,2%** (90,6% anche senza vuoti reali).
Per questo il click sceglie **un** pezzo e "Tutto il campo" è un pulsante e non il
comportamento predefinito: `ID_APPEZ` non garantisce la contiguità.

`app_id` dice quali pezzi formano lo stesso campo dichiarato, e nient'altro: è un
progressivo assegnato **dopo** l'ordinamento di Hilbert, non una funzione di
`COD_AZI`. Un identificativo derivabile da `COD_AZI` permetterebbe di raggruppare
tutti i terreni di un'azienda; rinumerando prima dell'ordinamento spaziale, dato
che l'archivio AGREA è ordinato per azienda, id consecutivi avrebbero rivelato la
stessa cosa.

## Le classi sono SPECIE, senza interpretazione

`DESC_COLT` di AGREA è la concatenazione di specie + destinazione + uso + varietà,
e AGREA fornisce gli altri tre in campi propri. **Sottraendoli resta la specie**,
per rimozione esatta di stringhe: nessuna regola a parole chiave, nessuna tabella
di raccordo da mantenere. Verificato su tutti i 778 codici regionali: 366 specie,
zero rimozioni fallite. I 14 codici del mais collassano su uno — sono destinazioni
dello stesso mais, non colture diverse.

Tutte e otto le colture del registro di tornatura hanno una riga propria.
`HARVEST_TO_AGREA_SPECIES` in `config.py` mappa `HarvestType.code` a un **insieme**
di specie: il pesco comprende le nettarine, gli agrumi si dichiarano per specie.

Nel disegno del campo quella mappatura fa anche da **filtro**: si sceglie solo un
pezzo la cui specie dichiarata corrisponde a una coltura del registro, perche' a
ogni coltura sono legate le sue avversita' e i suoi bollettini e un campo di soia
non avrebbe nulla da mostrare. L'autorita' su *quali* colture esistono resta il
database (`harvest_type`), non questo file: aggiungerne una li' la rende
selezionabile, purche' qui ci sia la riga con le sue specie AGREA. Gli esclusi si
disegnano comunque, a tratteggio, e restano usabili con una conferma esplicita —
AGREA dichiara la campagna in corso, quindi un impianto nuovo ha il confine giusto
e la coltura ancora vecchia. Misurato: a 1,5 km il filtro esclude il 58,7% dei
pezzi in pianura e l'89,9% sui Colli Bolognesi, dove domina il bosco.

## Il calcolo

1. Buffer circolare in **UTM 32N** (`EPSG:32632`): le superfici non si calcolano
   in gradi.
2. Lettura **per finestra** dal GeoParquet 1.1 con colonna bbox di copertura (non
   cache in memoria: 681 MB di RSS contro 5.983 MB, a parità di latenza).
3. **Ritaglio sul buffer**: un appezzamento a cavallo del bordo contribuisce solo
   per la parte interna, così gli ettari dichiarati coincidono con la superficie
   disegnata.
4. Percentuali sulle **superfici**, non sui conteggi.
5. Bosco, elementi del paesaggio e non agricolo restano **fuori** dal denominatore
   delle percentuali colturali: sono copertura del suolo, non colture.

## Quattro colori sulla mappa, non uno per specie

Vincolo misurato col validatore della palette: su fondo satellitare, dove
qualsiasi classe può confinare con qualsiasi altra, **oltre quattro colori le
coppie diventano indistinguibili anche a visione normale** (giallo↔arancio ΔE 13,7
contro una soglia di 15; con sei colori verde↔arancio scende a 3,2 per un
daltonico). Il quartetto in uso misura CVD 13,0 e visione normale 19,6.

Famiglie fisse — mai assegnate per posizione in classifica, altrimenti cambiare
raggio ridipingerebbe la mappa:

- **permanenti** (blu): frutteti e vigneti
- **erbacee** (giallo): seminativi, prati, pascoli, risaie
- **semi-naturale** (verde): bosco, siepi, margini, fossi
- **altro** (grigio) · **la coltura dell'utente** (magenta, sopra tutto)

Il verde va al semi-naturale e non ai prati perché la letteratura indica
l'habitat semi-naturale come driver per *Halyomorpha halys* e *Drosophila
suzukii*, mentre la distinzione prati/seminativi non cambia nessuna decisione. Il
dettaglio per specie sta nella **tabella** e nel **popup al click**, dove il nome
è scritto e il colore non porta l'informazione da solo.

## Il peso della risposta di `/pieces`

Il vincolo non e' il numero di pezzi ma il numero di **vertici**: a 3 km la
pianura ferrarese ha 2.442 pezzi per 53.098 vertici, Brisighella 2.186 pezzi per
188.238, perche' i bordi di collina seguono il terreno. Il rapporto misurato e'
stabile fra 6,0 e 6,6 byte compressi per vertice, quindi il tetto e' sui vertici
(`AGREA_PIECES_VERTEX_BUDGET = 30.000`, circa 195 kB) e si tengono i pezzi piu'
**grandi**: a vista larga i piccoli non sono cliccabili comunque.

Le coordinate si arrotondano a **7 decimali nella risposta** e non nel file: 1,1
cm, due ordini di grandezza sotto i 4 m di accuratezza del datum e sopra il lato
piu' corto presente nel dato (7,9 cm), quindi nessun vertice collassa e i bordi
condivisi restano condivisi. Dimezza il payload.

Quando il tetto scatta la risposta lo dichiara (`truncated`, `piece_min_ha`) e
l'interfaccia lo scrive: senza, i campi piccoli sembrerebbero non esistere.
Misurato: sotto 210 kB e 0,37 s in pianura come in collina.

## Limiti dichiarati in interfaccia

1. **Copertura.** `observability()` decide a **raggio fisso di 3 km**, non sul
   raggio scelto dall'utente: altrimenti il selettore annulla il controllo
   (misurato a Brisighella: 0,0% cartografato da iColt a 3 km ma 9,4% a 10 km, e
   quel 9,4% descrive la pianura di Faenza). Guarda anche la distribuzione per
   quadrante, per il caso pedecollinare.
2. **Vite e olivo in iColt sono sottostimati** anche dove la cartografia c'è:
   vite 38.595 ha contro 53.236 ufficiali (73%), olivo 282 contro ~4.500 (6%).
   `HARVEST_COVERAGE_NOTE` porta sempre la nota.
3. **`agri_ha` è un nome improprio**: il layer ARPAE distribuito non contiene i
   codici non agricoli (verificato: 10/11/15/16 assenti, `is_agri` sempre vero),
   quindi è la superficie **cartografata**. Usare `mapped_ha`.
4. **Classi sotto tre appezzamenti** accorpate in "altre colture" e conteggio non
   pubblicato: una riga con un appezzamento è il campo di un'azienda
   identificabile. Costo misurato: 0,1-0,9% della superficie.
5. **La mappa disegna sopra 0,2 ha** (96% della superficie); le percentuali
   contano tutto.

## Note operative

1. Il file iColt è caricato in memoria una volta (non ha la colonna bbox); AGREA
   si legge per finestra. Riscrivere iColt con `write_covering_bbox=True`
   permetterebbe di togliere anche quella cache.
2. **Attribuzione ARPAE obbligatoria** in interfaccia per iColt (CC BY 4.0). Per
   AGREA la licenza non è dichiarata: da chiarire con la Regione prima della
   produzione.
3. `GZipMiddleware` è essenziale, non decorativo: senza, il payload geometrico
   passa da 143 kB a 1,16 MB. **Il reverse proxy deve propagare
   `Accept-Encoding`** all'upstream.
4. Aggiornamento annuale di iColt: nuovo GeoParquet in `data/`, `ICOLT_PARQUET` in
   `paths.py`, `DATASET_YEAR` in `config.py`, poi ricostruire e rimisurare i
   valori di riferimento. Lo schema ARPAE cambia nome colonne ogni anno; vedi
   `CHANGELOG.md`.
5. **Dati AGREA sul volume**: si preparano con `updater.pex --run-now`, che li
   scarica dal sito pubblico di AGREA e li converte in `/data/landscape/agrea/`.
   E' lo stesso schema con cui peronospora scarica i GRIB di ECMWF: in git solo
   cio' che e' piccolo e stabile, il resto dalla fonte nel volume. Idempotente
   (confronta gli ETag), scrittura atomica, una volta l'anno. Vedi `CHANGELOG.md`
   per le misure e per le tre strade scartate.

## Verifica di non-regressione

```
GET /v1/landscape/composition?lat=44.80951&lng=11.75644&crop=pero   (3 km)

fonte             agrea
superficie agri   2.338,4 ha in 2.810 appezzamenti
la tua coltura    Pero 11,3%
controllo iColt   13,3% (2,0 punti di scarto)
semi-naturale     2,7%
specie nominate   34
```

Collina, dove iColt è cieca: Brisighella `olivo 11,8%`, semi-naturale `15,1%`
(350,8 ha di bosco); Colli Bolognesi `vite 9,0%`, semi-naturale `15,0%`. Con un
volume privo dei file AGREA la stessa chiamata deve tornare `fonte icolt` e 10
classi, senza errori.
