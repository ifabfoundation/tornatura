# Changelog - Landscape (paesaggio agricolo)

Registro delle modifiche per il team backend.

---

## [2026-08-24] - v2.1.1: la soglia dei pezzi scende da 0,25 a 0,01 ha

### Perche'

La soglia del layer fine escludeva **campi veri**, non rumore. Il 2,75% di
superficie persa che la v2.1.0 dichiarava era un aggregato, e nascondeva la
distribuzione: un appezzamento e' **del tutto non selezionabile** se nessuno dei
suoi frammenti raggiunge la soglia, e succedeva molto piu' spesso di quanto quel
numero suggerisse.

| provincia | appezzamenti non selezionabili | valgono | campi >= 0,3 ha persi interi |
|---|---|---|---|
| FE (pianura) | 19.435 = **30,5%** | 1,05% della superficie | 813 |
| BO (mista) | 88.788 = **54,2%** | 3,29% | 2.579 |
| FC (collina) | 95.421 = **61,5%** | 6,56% | 2.753 |

Tanti in numero, pochissimi in superficie: quindi campi piccoli. Ma erano
**concentrati sulle colture di tornatura**, perche' le arboree si dichiarano in
appezzamenti minuscoli:

| coltura | non selezionabili (FE / BO / FC) | mediana |
|---|---|---|
| albicocco | 78% / 67% / 77% | 0,13-0,17 ha |
| pesco | 72% / 55% / 65% | 0,16-0,24 ha |
| olivo | — / 64% / 74% | 0,12-0,17 ha |
| pero | 38% / 53% / 69% | 0,17-0,38 ha |
| vite | 53% / 33% / 36% | 0,25-0,51 ha |
| mais | 10% / 9% / 15% | 1,2-2,8 ha |
| barbabietola | 7% / 11% / 22% | 1,0-3,0 ha |

In collina il **59% degli appezzamenti delle otto colture** non era selezionabile.
E a differenza del blocco sulle colture, la soglia **non aveva via d'uscita**: il
pezzo non arrivava al client, quindi non c'era nulla su cui cliccare e l'utente non
poteva sapere che mancasse qualcosa.

### L'errore di metodo, che vale piu' del numero

0,25 ha era stato scelto per contenere il **peso della risposta**, quando era
l'unica difesa disponibile. Poi, nella stessa versione, e' arrivato
`AGREA_PIECES_VERTEX_BUDGET`, che regola il peso da solo servendo i pezzi piu'
grandi e dichiarando la soglia effettiva. **Da quel momento la soglia nel file non
proteggeva piu' nulla, ma continuava a costare copertura** — e non e' stata
ricontrollata. Una scelta va rivista quando cambia l'architettura che la
giustificava.

### Perche' 0,01 ha e non zero

Copertura degli appezzamenti delle otto colture, misurata su Ferrara e
Forli'-Cesena:

| soglia | pianura | collina | file |
|---|---|---|---|
| 0,25 ha | 70,5% | 41,1% | 1,00x |
| 0,05 ha | 94,3% | 85,5% | 1,24x / 1,38x |
| **0,01 ha** | **99,3%** | **99,1%** | 1,35x / 1,53x |
| nessuna | 100% | 100% | 1,41x / 1,61x |

Da 0,01 a zero si guadagna meno di un punto e si prendono dentro **60.000
frammenti sotto i 100 m² per provincia di collina** (15.988 da 1-10 m², 44.001 da
10-100). Un frammento da 5 m² non e' un campo: e' la scheggia dove una linea di
PROPRIETA' taglia di sbieco l'angolo di un appezzamento. E fa un danno concreto,
non estetico: quelle schegge stanno **lungo i confini** dei campi veri, quindi
rubano il click a chi mira vicino al bordo, e ognuna aggiunge un contorno disegnato
proprio dove serve precisione.

La soglia diventa quindi un **pavimento del rumore** e non un giudizio su quanto un
campo debba essere grande per interessare all'utente.

### Effetto misurato

| | prima | dopo |
|---|---|---|
| pezzi in regione | 874.974 | **1.956.071** |
| file dei pezzi | 696 MB | **1.130 MB** |
| volume totale | 1,04 GB | **1,47 GB** |
| campi con almeno un pezzo | 506.275 | **989.107** |

`agrea2026_colture_er.parquet` e `agrea2026_elementi_er.parquet` sono rigenerati
**identici** (291,0 MB / 824.326 poligoni / 1.217.047,5 ha e 53,3 MB / 902.542):
la pagina del paesaggio non e' toccata, e la verifica di non-regressione torna gli
stessi numeri fino all'ultimo decimale.

Il payload non peggiora, perche' il tetto sui vertici fa il suo lavoro:

| raggio | soglia effettiva | troncato | payload |
|---|---|---|---|
| 300-1.200 m | **0,01 ha** | no | 4,8-197 kB |
| 2.000-3.000 m | 0,08-1,86 ha | si' | ~215 kB |

I pezzi piccoli arrivano **esattamente agli zoom in cui sono cliccabili**, e a
vista larga vengono rimandati con la soglia dichiarata in risposta.

Qualita' dell'unione invariata o migliore, verificata sui nuovi pezzi piccoli: zero
contorni nulli su pezzo singolo, zero errori, e l'unione dei fratelli risulta un
solo poligono nell'86,3% dei casi in pianura contro il 78,7% di prima — piu'
frammenti disponibili ricuciono meglio.

### Un difetto trovato nel rimisurare

`/pieces` riusava `MIN_RADIUS_M = 1000`, che esiste per `/composition` dove un
buffer di paesaggio sotto il chilometro non descrive niente. Qui il significato e'
opposto: la finestra segue la vista, e **a zoom alto — cioe' proprio quando si mira
a un pezzo piccolo — la mezza diagonale scende sotto il chilometro**. Quelle
richieste tornavano **422** e la mappa restava senza pezzi nel momento in cui
servivano di piu'.

Corretto con `AGREA_PIECES_MIN_RADIUS_M = 200`, e il frontend limita il raggio dal
basso a 250 m per non emettere richieste invalide.

---

## [2026-08-20] - v2.1.0: scelta del confine dai pezzi dichiarati

### In breve, per chi legge solo questo

Chi disegna un campo nuovo puo' ora **comporlo cliccando le superfici
dichiarate** invece di tracciarlo a mano: passando il cursore il pezzo si
illumina, il click lo sceglie, un secondo click lo toglie, e piu' pezzi si
uniscono. Serve un **terzo file** sul volume (`agrea2026_parcelle_er.parquet`,
**696 MB**, 874.974 pezzi, 506.275 campi di cui 170.000 scomponibili) e un **nuovo
endpoint** (`/v1/landscape/pieces`).

Il file del paesaggio e' rigenerato **byte per byte identico** (291,0 MB, 824.326
poligoni, 1.217.047,5 ha) e la verifica di non-regressione della pagina torna gli
stessi numeri fino all'ultimo decimale. Era la condizione da rispettare.

Nel farlo si e' corretto un difetto della v2.0.0 che dava all'utente un campo
sbagliato senza avvisarlo (sotto, "Il difetto corretto").

### Due granularita', due scopi

Il dato AGREA ha tre livelli, e prima ne usavamo uno solo.

| livello | cos'e' | chi lo disegna | quanti (Ferrara) |
|---|---|---|---|
| particella catastale | unita' di **proprieta'**: foglio + particella | Agenzia delle Entrate | 61.016 |
| **appezzamento** (`ID_APPEZ`) | unita' **agronomica** dichiarata: una coltura, contigua | l'agricoltore, per la PAC | 196.972 |
| **riga dello shapefile** | appezzamento **∩** particella catastale | nessuno: e' un'intersezione | 375.303 |

Il file si chiama `Uti_Part` = *utilizzi per particella*: la riga e' la
granularita' minima che il dato conosce. Controllo che conferma la bonta'
dell'appezzamento come unita' agronomica: su 196.972, **zero** contengono piu' di
una coltura.

Da qui in poi:

- **"Il tuo paesaggio" resta sull'appezzamento.** Deve dire cosa c'e' intorno,
  non disegnare un bordo: il file, la pagina e i valori di riferimento **non
  sono stati toccati**.
- **Il disegno del campo usa il pezzo.** Li' il bordo deve essere preciso, e chi
  disegna deve poter prendere una **porzione** invece di tutto il campo
  dichiarato.

### Perche' la soglia e' 0,25 ha e non "il minimo assoluto"

Il frammento mediano misura **0,04 ha (400 m²)**, e il **51,8%** dei frammenti
sta sotto 0,05 ha valendo insieme l'**1,27%** della superficie: sono le schegge
dove una linea di **proprieta'** taglia un campo di sbieco, bordi che sul terreno
non si vedono. Scendere al minimo assoluto darebbe 375.000 coriandoli cliccabili
nella sola Ferrara.

A **0,25 ha**:

- si tiene il **97,25%** della superficie che il servizio serve davvero, cioe' le
  righe SAU piu' il bosco. E' il 94,5% solo se a denominatore si prende ogni riga
  dell'archivio, comprese le non agricole che non serviamo mai: il primo numero
  e' quello che descrive il costo vero della soglia;
- i pezzi sono poligoni semplici nel **91,92%** dei casi, contro il 71,58% degli
  appezzamenti interi;
- il **58,8%** degli appezzamenti ha un solo pezzo, quindi per quelli
  l'esperienza e' identica a prima; nel restante **41,2%** c'e' una scelta vera,
  con mediana 2-3 pezzi;
- guardando solo i casi dove la scelta conta davvero (appezzamenti ≥ 1 ha con piu'
  di un frammento, il 12,1% del totale): mediana 4 pezzi, pezzo mediano 0,50 ha,
  e nell'**82,1%** ci sono almeno due pezzi sopra soglia.

### L'unione dei pezzi, e il vincolo che decide tutto

`AgriFieldModel.map` (`src/python/core/models.py`) e'
`ListField(EmbeddedDocumentField(Point))`: **una lista piatta di punti, cioe' un
anello solo**. Niente parti staccate, niente buchi. Il database non si tocca,
quindi l'unione va **ridotta**, e cio' che si perde va **detto**.

`contornoDaPezzi()` in `company-field-form.tsx` fa esattamente questo: unisce con
turf, tiene la **parte piu' grande**, chiude i buchi sotto **100 m²** (rumore del
calcolo) e riporta al chiamante quante parti ha scartato e quanti metri quadri di
vuoto reale ha inglobato. L'interfaccia scrive entrambe le cose.

Misure su 3.000 campi del ferrarese con almeno due pezzi:

| unione di... | un solo poligono | senza vuoti reali |
|---|---|---|
| **tutti** i pezzi del campo dichiarato | 69,0% | 68,2% |
| i pezzi **adiacenti** a quello cliccato | **94,2%** | **90,6%** |

La differenza e' il motivo per cui il pulsante si chiama "Tutto il campo" e non e'
il comportamento predefinito: `ID_APPEZ` **non garantisce la contiguita'**, e un
campo dichiarato puo' stare in due posti staccati. Il click sceglie un pezzo, il
resto lo aggiunge l'utente.

Quando un vuoto reale sopravvive misura **1.104 m² in mediana** (p90 3.592 m²,
massimo 339.116 m²): e' un'aia, un fabbricato, un laghetto. L'interfaccia dice
quanti metri quadri sono e di quanto cambia l'estensione.

Nota sull'adiacenza: si misura come **bordo condiviso di lunghezza positiva**, non
come semplice contatto. Due poligoni che si toccano in un vertice non formano un
campo unico, e contandoli come adiacenti la quota di unioni pulite scendeva dal
94,2% all'81,6%.

### Il difetto corretto

La v2.0.0 caricava il confine suggerito leggendo `geom.coordinates[0]`, cioe'
l'anello esterno della **prima** parte. Misurato sul dato servito (49.098
appezzamenti nella finestra ferrarese): il **21,84%** e' MultiPolygon e
l'**11,06%** ha buchi interni. Nei casi multiparte teneva un pezzo e buttava il
resto — mediana 0%, ma **p90 22,3% e massimo 70,2% della superficie** — e nei casi
con buchi gonfiava la superficie. Senza alcun avviso.

Ora la riduzione e' esplicita, misurata e scritta in pagina, e parte da geometrie
che sono poligoni semplici nel 91,92% dei casi invece del 71,58%.

### Sui pezzi non si semplifica e non si arrotonda

Due scelte che sembrano dimenticanze e non lo sono.

**Nessuna semplificazione.** `simplify` lavora un poligono per volta: due pezzi
confinanti verrebbero semplificati in modo indipendente e il bordo comune si
aprirebbe, riempiendo l'unione di fessure. Nel dato grezzo i pezzi confinanti si
toccano entro 1 cm nel **99,8%** dei casi (distanza minima mediana **0,000 m**),
ed e' questa proprieta' che rende pulita l'unione. Il layer del paesaggio invece
resta semplificato a 1 m, perche' li' serve un'indicazione e non un bordo.

**Nessun arrotondamento delle coordinate.** `set_precision` in modalita'
`valid_output` riallinea la topologia una geometria per volta, quindi aprirebbe i
bordi condivisi; in modalita' `pointwise` li conserva, ma degenera **6.057 pezzi
su 97.758 (6,2%)** in GeometryCollection irrecuperabili. Senza arrotondare si
perdono **4 pezzi su 97.758** e il file passa da 24,7 a 33,6 MB per provincia:
nove megabyte per non far sparire il 6% dei campi selezionabili.

### `app_id`: raggruppa i pezzi senza dire di chi sono

Ogni pezzo porta `app_id` (quali pezzi formano lo stesso campo dichiarato) e
`app_n` (quanti pezzi ha quel campo in tutto, anche fuori dalla vista).

`app_id` e' un **progressivo, non una funzione di `COD_AZI`**, e viene assegnato
**dopo** l'ordinamento di Hilbert. Le due cose sono deliberate: un identificativo
derivabile da `COD_AZI` — anche un hash, dato che le aziende per provincia sono
poche migliaia — permetterebbe di raggruppare tutti i terreni di un'azienda, che
e' proprio cio' che non dobbiamo servire; e rinumerando prima dell'ordinamento
spaziale, dato che l'archivio AGREA e' ordinato per azienda, id consecutivi
avrebbero rivelato terreni della stessa azienda. Rinumerando dopo, due id vicini
sono campi geograficamente vicini.

### Cosa e' cambiato nel codice

| file | modifica |
|---|---|
| `modules/config.py` | `AGREA_PIECE_MIN_HA`, `AGREA_PIECES_SIMPLIFY_M`, `AGREA_PIECES_MAX_RADIUS_M`, `MAX_PIECES` |
| `paths.py` | `AGREA_PARCELLE_PARQUET` |
| `modules/agrea_prepare.py` | terzo layer in `_lavora_provincia`; `_unisci(..., pezzi=True)` rinumera `app_id` e assegna `pid`/`app_n`; `stato()` e `aggiorna()` contano tre file |
| `modules/agrea.py` | `pieces_available()`, `pieces_geojson()`; `SPECIE_A_HARVEST` promossa a costante di modulo |
| `api.py` | `GET /v1/landscape/pieces` |
| `updater.py` | il controllo di completezza include il terzo file |
| `services/model-api.ts` | `LandscapePiece`, `LandscapePiecesResponse`, `fetchLandscapePieces`; geometrie tipizzate `Geometry`/`Polygon` invece di `any` |
| `company-field-form.tsx` | scelta a click, unione, guardia, pannello, modalita' di partenza |
| `field-dashboard.tsx` | il pulsante "Il tuo paesaggio" spostato dentro il contenitore della mappa: era nella colonna, che porta `me-md-4`, quindi il suo `w-100` misurava la colonna e il pulsante usciva piu' largo della foto |

Documentazione: `CLAUDE.md`, `README.md`, `MANIFEST.txt`.

**Il core non e' stato toccato**: nessuna modifica a Mongo, Keycloak, permessi o
SDK. Verificabile con `git diff main -- src/python/core src/typescript/coreapis-sdk`.

### `/v1/landscape/pieces`

```
GET /v1/landscape/pieces?lat&lng&radius_m     (raggio massimo 3 km)
```

Ogni feature: `pid`, `app_id`, `app_n`, `crop`, `harvest_code`, `family`, `ha`,
`is_crop_class`.

Due differenze sostanziali rispetto a `/parcels`, entrambe volute:

1. **Le geometrie non sono ritagliate sul buffer.** Su `/parcels` il ritaglio e'
   giusto, perche' gli ettari dichiarati devono coincidere con la superficie
   disegnata. Qui sarebbe un danno: un campo a cavallo del bordo della vista
   verrebbe troncato e l'utente accetterebbe come confine del proprio campo il
   bordo della finestra.
2. **Nessun accorpamento per anonimato.** Su `/parcels` le classi con meno di tre
   appezzamenti si accorpano. Qui la geometria serve proprio a scegliere un
   singolo pezzo, e chi disegna il proprio campo lo sta gia' guardando dalla foto
   satellitare: nascondere il confine non proteggerebbe nulla.

`count: 0` **non e' un errore**: significa che non c'e' nulla da proporre e si
disegna a mano. Se il file manca l'endpoint risponde `count: 0` e non 500.

### Interfaccia: cosa fa e cosa non fa

Il disegno a mano **resta esattamente come prima**. La scelta si aggiunge sopra.

- il cursore **illumina** il pezzo (tutto locale, nessuna chiamata al server per
  movimento del mouse: i pezzi stanno gia' sul client);
- il click **sceglie**, un secondo click **toglie**;
- l'anteprima e la scelta sono **stati separati**: una volta cliccato un pezzo,
  muovere il cursore verso il pulsante non cambia piu' cio' che si sta per usare.
  Prima cambiava, ed era il difetto d'uso piu' fastidioso;
- i **fratelli** (gli altri pezzi dello stesso campo dichiarato) si accendono
  tratteggiati, e "Tutto il campo" li aggiunge tutti;
- si possono unire pezzi di campi **diversi**: l'interfaccia lo dice invece di
  impedirlo;
- il **contorno** che verra' salvato e' disegnato con una linea piena, cosi' la
  riduzione a un anello unico si **vede** e non e' solo scritta;
- la coltura si preseleziona **solo se tutti** i pezzi scelti concordano.

**Cambio di comportamento predefinito, da segnalare.** Il wizard partiva in
`draw_polygon`: il primo click sulla mappa piazzava un vertice. Ora parte in
`simple_select`, cioe' **in selezione**: il click sceglie il confine dichiarato, e
chi vuole tracciare a mano preme il pulsante del poligono. Mentre si e' in
`draw_polygon` il click sui pezzi viene ignorato, cosi' non si toglie all'utente
lo strumento che ha scelto.

Conseguenza da non trascurare: con la selezione come modalita' di partenza, un
click sulla mappa **non disegna piu'**, e senza una riga di spiegazione sembra che
non funzioni nulla. Per questo il pannello distingue tre situazioni invece di una:
vista troppo larga per aver caricato i pezzi ("cerca la zona e avvicinati"), pezzi
caricati ("passa il cursore e clicca"), e vista abbastanza vicina ma senza nulla
da scegliere ("qui non risultano confini dichiarati: disegna col pulsante del
poligono"). Le prime due non vanno confuse: sono "non abbiamo ancora guardato" e
"qui non c'e' niente".

E se un poligono e' gia' stato disegnato a mano, il pannello della selezione
avverte che usare il confine dichiarato lo sostituisce.

Sorgenti mapbox distinte (`vicinato`, `fratelli`, `anteprima`, `selezione`,
`contorno`) invece di `feature-state`: un pezzo scelto deve restare disegnato
anche quando esce dalla vista e la sorgente dei pezzi viene ricaricata, cosa che
con lo stato per feature si perderebbe.

### Il peso, e cosa si potrebbe fare se diventasse un problema

Nella stessa finestra il layer fine e' **1,54x i poligoni e 2,40x i vertici** di
quello del paesaggio; e' il numero di vertici che pesa sul file. Misurato a
preparazione conclusa: il volume passa da **344 MB a 1.040 MB** per annata
(291 + 696 + 53). Per un server non e' un problema — la preparazione scarica
comunque 2 GB di archivi — ma va detto.

Due leve, non usate e con il loro costo:

1. **Salvare solo i pezzi dei campi scomponibili.** Il 58,8% dei campi ha un solo
   pezzo sopra soglia, e per quelli il layer del paesaggio basterebbe. Misurato:
   il 72% dei poligoni e il **64% dei vertici**, quindi circa 450 MB invece di
   700. Costa codice di composizione fra i due file e obbliga ad aggiungere
   `app_id` al layer del paesaggio, cioe' a toccare una pagina che funziona.
   **Scartata**: 250 MB su un volume non valgono quel rischio.
2. **`shapely.coverage_simplify()`** (esiste in shapely 2.1.2) semplifica una
   copertura poligonale **conservando i bordi condivisi**, che e' l'unico modo di
   semplificare questo layer senza aprire le fessure. Non e' stata usata: al
   primo tentativo solleva `TypeError: One of the Geometry inputs is of incorrect
   geometry type` e richiede di ripulire gli ingressi (MultiPolygon e
   GeometryCollection) prima di funzionare. Va valutata se il peso diventa un
   problema, misurando la differenza simmetrica come si e' fatto per la
   semplificazione a 1 m.

### Si scelgono solo le colture che tornatura segue

L'app e' costruita intorno a otto colture, ognuna con le sue avversita' e i suoi
bollettini. La mappa dei pezzi rischiava di rompere quella metodologia: invitava a
scegliere un campo di soia, e al passo dopo il modulo costringeva comunque a
dichiararne una delle otto. Ora **si sceglie solo cio' che l'app sa seguire**.

**Due verita' singole, nessun elenco duplicato nel codice.**

| domanda | dove sta la risposta | chi la cambia |
|---|---|---|
| quali colture segue tornatura | `harvest_type` nel database, letto con `selectActiveHarvestTypes` | il team, dall'app, come gia' fa |
| quale specie AGREA e' quella coltura | `HARVEST_TO_AGREA_SPECIES` in `modules/config.py` | una riga per coltura |

E' la stessa lista che riempie il menu della coltura al passo 2, quindi mappa e
modulo non possono divergere. Verificato: gli otto codici nel database
(`agrumi, albicocco, barbabietola, mais, olivo, pero, pesco, vite`) combaciano
esattamente con le otto chiavi della mappatura.

**Per aggiungere una coltura domani**: la si aggiunge in `harvest_type` come si fa
oggi, e si scrive **una riga** in `HARVEST_TO_AGREA_SPECIES` con le specie AGREA
corrispondenti. Nient'altro, in nessun file. Quel raccordo non e' automatizzabile —
nessuno puo' dedurre da solo che l'albicocco si dichiara `ALBICOCCO` e che il
pesco comprende anche `PESCO NETTARINA` — ma e' l'unica cosa da scrivere.

**Il blocco e' strutturale, non una condizione.** I pezzi ammessi e quelli esclusi
stanno su due layer distinti, e il gestore del click e' solo sul primo: non c'e'
un `if` che si possa dimenticare. La divisione avviene nell'effetto che riempie le
sorgenti e non nei gestori, perche' quelli si registrano una volta sola e
vedrebbero per sempre il registro colture del primo render — che al primo render
puo' essere ancora vuoto. E se il registro non e' ancora arrivato dal server la
regola **si apre invece di chiudere**: una corsa in caricamento non deve rendere la
mappa inutilizzabile.

**I pezzi esclusi restano disegnati**, a tratteggio: servono a riconoscere il
proprio campo, e togliendoli la mappa avrebbe dei buchi senza spiegazione.

**Con una via d'uscita esplicita, e non e' un cedimento.** AGREA dichiara la
campagna in corso: chi ha appena impiantato un pereto dove c'era frumento ha un
confine giusto e una coltura sbagliata, e bloccarlo del tutto gli impedirebbe di
registrare un campo che esiste. Quanto pesa il blocco, misurato a 1,5 km:

| luogo | selezionabili | bloccati | colture bloccate piu' frequenti |
|---|---|---|---|
| pianura ferrarese | 41,3% | 58,7% | frumento tenero, soia, erba medica |
| Brisighella | 39,2% | 60,8% | bosco, kiwi, ritirato dalla produzione |
| Colli Bolognesi | 10,1% | 89,9% | bosco, prato polifita, erba medica |

Con numeri cosi', un blocco secco senza uscita avrebbe reso la funzione inservibile
in collina. Il click su un pezzo escluso quindi **chiede conferma** invece di
selezionare di nascosto, dicendo perche' e ricordando che la coltura andra'
comunque scelta fra le otto.

**Un'invariante rende la regola estensibile ai fratelli.** Se il pezzo cliccato e'
ammesso, i suoi fratelli lo sono per costruzione: verificato che **0 su 506.275**
campi dichiarati contengono piu' di una coltura. "Tutto il campo" non ha quindi
bisogno di ricontrollare nulla.

### Il peso della risposta: tetto sui vertici, non sui pezzi

Il primo tentativo cappava il raggio, e non bastava: a 3 km la risposta pesava
**736 kB** compressi in pianura e **1.105 kB** a Brisighella, con 2.442 pezzi
contro 2.186 — cioe' il conteggio dei pezzi non predice il peso, perche' i bordi
di collina seguono il terreno e hanno molti piu' vertici (188.238 contro 53.098).

Due misure hanno risolto il problema.

**1. Coordinate a 7 decimali nella risposta** (il file resta a precisione piena).
Sette decimali sono 1,1 cm: due ordini di grandezza sotto i 4 m di accuratezza
del datum, e sopra il lato piu' corto presente nel dato (7,9 cm), quindi nessun
vertice collassa. Misurato: da 336 a 91 kB a 1,5 km, cioe' il **46%**, al costo di
22-91 ms.

**2. Tetto sui vertici** invece che sui pezzi. Il rapporto misurato e' stabile fra
**6,0 e 6,6 byte compressi per vertice**, in pianura come in collina, quindi il
numero di vertici e' un buon proxy del peso mentre il numero di pezzi non lo e'.
Si tengono i pezzi piu' grandi — a vista larga i piccoli non sono cliccabili
comunque — e la soglia effettivamente applicata viene **dichiarata nella
risposta** e scritta in interfaccia, altrimenti sembrerebbe che i campi piccoli
non esistano.

Risultato, con `AGREA_PIECES_VERTEX_BUDGET = 30.000`:

| luogo | 1 km | 2 km | 3 km |
|---|---|---|---|
| pianura ferrarese | 42 kB (0,25 ha) | 168 kB (0,25 ha) | 210 kB (**0,80 ha**) |
| Brisighella (collina) | 83 kB (0,25 ha) | 186 kB (**0,89 ha**) | 189 kB (**1,86 ha**) |
| Colli Bolognesi | 77 kB (0,25 ha) | 193 kB (**0,66 ha**) | 190 kB (**1,24 ha**) |

Fra parentesi la soglia effettiva. Il tetto tiene la risposta sotto **210 kB**
dappertutto, con latenza 0,10-0,37 s.

### Le fessure erano gia' nel dato, non le fa il nostro calcolo

Unendo due pezzi confinanti compare a volte un buco lunghissimo e sottilissimo:
una **fessura** fra due bordi che non combaciano perfettamente. Il sospetto
naturale e' che la colpa sia dell'arrotondamento delle coordinate. **Non lo e'**,
verificato con un A/B controllato sulla stessa finestra e sugli stessi pezzi:

| precisione | pianura | Brisighella | Colli Bolognesi |
|---|---|---|---|
| piena | 7,7% | 32,1% | 36,4% |
| 9 decimali (0,1 mm) | 7,8% | 31,7% | 35,8% |
| 7 decimali (1,1 cm) | 7,5% | 33,6% | 35,4% |

(quota di coppie con bordo condiviso in cui compare almeno una fessura)

Le fessure sono un difetto topologico degli archivi AGREA, piu' frequente in
collina dove i bordi hanno molti piu' vertici. Non hanno effetto sulla geometria
salvata, perche' il contorno e' comunque il solo anello esterno; hanno effetto sul
**messaggio** all'utente, e per quello si distinguono dai vuoti veri con due
criteri invece di uno: superficie ≥ 100 m² **e** compattezza `4π·area/perimetro²`
≥ 0,10, che vale 1 per un cerchio e tende a 0 per una scheggia. Misurato su 765
buchi in tre zone: l'88% sta sotto 100 m², e dei 93 sopra soglia solo 6 sono
schegge — che il secondo criterio esclude.

### Preparazione dei dati

```
python updater.pex --run-now                      scarica e prepara i tre file
python updater.pex --check                        cosa c'e' sul volume
python updater.pex --run-now --force --from-dir DIR   da archivi locali
```

Idempotente sugli ETag, scrittura atomica, una volta l'anno. `--from-dir` usa
archivi gia' su disco: serve in sviluppo per rigenerare senza riscaricare 2 GB.

### Rifiniture dopo la prova sul campo

Sei correzioni dalla prima sessione di prova, tutte in `company-field-form.tsx`.

**Leggibilita' dei pannelli.** Usavano `bg-glass`, che e'
`background-color: transparent` piu' `backdrop-filter: blur(10px)`: sfoca la foto
ma non da' contrasto, e su un satellitare il testo scuro sparisce. Passati a
`bg-white`. La barra in basso col pulsante "Avanti" resta `bg-glass`: e' un
pulsante, non un paragrafo.

**Confini piu' marcati sui pezzi utilizzabili.** `vicinato-line` da 0,8 px a 1,7 e
da 0,55 a 0,92 di opacita'. Gli esclusi restano tenui e tratteggiati: la differenza
fra "si puo' scegliere" e "sta qui solo per orientarsi" si legge dal tratto prima
che dal colore.

**"Coltura non seguita da tornatura" in evidenza**, non in nota: e' la ragione per
cui il pezzo non si sceglie, quindi sta nella riga in grassetto insieme al nome
della specie, mentre gli ettari e la spiegazione scendono nel testo piccolo.

**Il cestino riporta tutto alla partenza.** `draw.delete` cancellava il poligono ma
lasciava la scelta e l'avviso "confine caricato": dopo aver svuotato sembrava di
essere ancora a meta' di qualcosa.

**Un mini cestino per pezzo.** Deselezionare cliccando sulla mappa funziona ma e'
scomodo: i pezzi possono essere strisce di pochi metri di larghezza, e centrarne
una col cursore e' un esercizio di mira. Il pannello ora elenca i pezzi scelti,
ognuno col suo cestino. Tetto di sei righe, perche' "Tutto il campo" puo'
aggiungerne molti — il massimo misurato in regione e' 46 — e oltre il tetto si
togliono dalla mappa.

**Perche' due pezzi vicini a volte non si toccano.** Segnalato come possibile
errore di trasformazione delle coordinate. Non lo e', ed e' utile sapere perche'.
Misurato su due zone di pianura, coppie di pezzi entro 12 m:

| coppie di pezzi vicini | si toccano esatti | distanza mediana quando staccati |
|---|---|---|
| stesso campo dichiarato | 93-96% | — |
| campi dichiarati **diversi** | 24% | **5,2-5,6 m** |

Fra due campi dichiarati diversi c'e' quasi sempre una striscia non coltivata —
capezzagna o fosso, circa cinque metri — che non e' superficie dichiarata e quindi
non sta nel dato. Un errore di datum e' inoltre **matematicamente escluso**: i 4 m
di accuratezza sono uno scostamento *assoluto*, spostano tutte le geometrie nello
stesso modo e non possono aprire un varco *fra due vicini*. Il pannello adesso lo
dice quando la scelta tocca piu' di un campo dichiarato, invece di lasciare
l'utente col dubbio.

### La coltura si precompila al passo 2

Se il confine viene da un pezzo dichiarato, il menu "Scegli la coltura" al passo
dei dettagli parte gia' sulla coltura giusta. Resta modificabile: il dato AGREA
descrive la campagna in corso, non necessariamente cio' che l'utente sta
registrando.

Ha richiesto di cambiare **cosa il passo 1 consegna al passo 2**: prima il solo
elenco di punti, ora `{ map, harvest }` (tipo `DisegnoCompletato`). Tre dettagli
che non erano ovvi:

- `usaContorno` svuota la scelta, e con essa si perdeva `colturaScelta`: la
  coltura del confine effettivamente usato si tiene in uno stato a parte;
- si precompila **solo** una coltura del registro. Un pezzo forzato puo' portare
  una specie che il menu non contiene, e precompilarla darebbe un valore che il
  form non sa nemmeno rileggere. Verificato che ogni `harvest_code` servito
  esista nel registro del database, in tre zone diverse;
- chi ridisegna a mano non si porta dietro la coltura: `draw.create` e
  `draw.delete` la dimenticano, perche' un poligono tracciato a mano non viene da
  nessun pezzo dichiarato.

`initialValues` di formik si leggono al solo montaggio, e il passo 2 si monta dopo
che `formData` e' stato aggiornato: la precompilazione arriva quindi in tempo.

### Due difetti trovati alla seconda prova

**`turf.union` pretende almeno due geometrie.** Con un pezzo solo solleva
`Error: Must have at least 2 geometries`. `contornoDaPezzi()` catturava
l'eccezione e tornava `null`, e il pannello della scelta e' condizionato a
`contorno`: quindi **con un solo pezzo selezionato non compariva nulla** — nessun
pannello, nessun pulsante — pur essendo il pezzo disegnato in azzurro sulla mappa.
Era il caso piu' comune, il 58,8% degli appezzamenti ha un solo pezzo sopra
soglia. Il difetto e' sfuggito perche' tutte le verifiche erano state fatte su
coppie e gruppi: la scala 1..N non era stata provata. Ora con un pezzo solo
l'unione e' il pezzo stesso, e la verifica copre 300 Polygon e 25 MultiPolygon
singoli piu' la scala 1-2-3-4.

**Il fuoco della ricerca restava appeso.** Il canvas di mapbox non prende il fuoco
della tastiera, quindi dopo una ricerca l'input lo mantiene anche cliccando sulla
mappa: `onBlurCapture` non scattava e `ricercaAttiva` restava vero, tenendo
nascosti tutti i pannelli a tempo indeterminato. Ora qualunque interazione con la
mappa (`click`, `movestart`) chiude la ricerca.

### Come si e' verificato

1. **Non-regressione della pagina del paesaggio**: `agrea`, 2.355,8 ha in 1.401
   appezzamenti, pero 11,4%, controllo iColt 13,3% (1,9 punti), semi-naturale
   2,7%, 29 specie. Identico prima e dopo, e il file rigenerato ha la stessa
   dimensione al byte.
2. **Contratto dei cinque endpoint** (`health`, `coverage`, `composition`,
   `parcels`, `pieces`, `parcel-at`): tutti 200.
3. **Unione lato client**, eseguita con turf sulle geometrie realmente servite e
   non su un campione teorico: nessun errore su 1.677 coppie in tre zone, e l'A/B
   sulle fessure descritto sopra.
4. **Peso e latenza** della risposta nelle tre zone, tabella sopra.
5. `tsc -b` e `vite build` a zero errori; `pants fmt lint src/python/landscape::`
   pulito; nessun avviso di dipendenza non inferibile (per questo il tetto sui
   vertici usa i metodi dell'array di shapely e non `numpy`, che nel resolve
   arriva solo di rimbalzo da pandas).
6. `git status` mostra solo i file previsti.

### Da comunicare al collega

1. **Volume piu' grande**: `/data/landscape` passa da 344 MB a **1.040 MB** per
   annata.
2. Il terzo file si crea con `updater.pex --run-now`, come i primi due. Se manca,
   il disegno del campo torna a essere solo manuale e **nessuna pagina si rompe**.
3. Nessuna nuova regola di proxy: `/v1/landscape/pieces` sta sotto il prefisso
   `/v1/landscape/*` gia' previsto.
4. **Il wizard "Aggiungi campo" parte in selezione e non in disegno.** E' un
   cambio di comportamento visibile a chi usa l'app oggi: il primo click sulla
   mappa non piazza piu' un vertice. Il disegno a mano si apre col pulsante del
   poligono, che era ed e' sempre presente.

### Resta aperto

- **La licenza AGREA non e' dichiarata.** Vale per questa funzione come per la
  pagina del paesaggio, e ora la geometria dichiarata non e' solo mostrata ma
  diventa il confine di un campo registrato: la richiesta alla Regione va fatta
  prima della produzione.
- `/v1/landscape/parcel-at` non e' piu' usato dal frontend (lo sostituisce
  `/pieces`) ma resta come contratto pubblico.
- Nomi di specie lunghi e brutti nel dato AGREA (*"Erba medica (sp. medicago
  sativa l. (varieta'))"*): si mostrano cosi' come sono, senza accorciarli.

---

## [2026-08-19] - v2.0.0: seconda sorgente AGREA, mappa interattiva, correzioni

### In breve, per chi legge solo questo

Il servizio ora ha **due sorgenti** invece di una, la pagina ha una **mappa
interattiva** invece di un'immagine statica, e sono corretti **cinque difetti**
della versione precedente, uno dei quali esponeva agli utenti un'affermazione
falsa (un campo di collina leggeva "superficie agricola 0%").

**Serve una decisione prima della produzione**: i dati AGREA pesano 387 MB per
annata e non stanno nell'immagine ne' in git. Vedi "Il problema del peso".

### Le due sorgenti, e perche' due

| | iColt (ARPAE) | AGREA |
|---|---|---|
| natura | classificazione da satellite, immagini solo invernali | dichiarazione amministrativa per la PAC |
| dove | pianura; cieca sopra 200 m di quota o 15% di pendenza | anche collina e Appennino |
| granularita' | 16 classi, minimo 0,5 ha | 311 specie nominate |
| bosco e siepi | assenti | 179.460 ha di bosco, 34.460 ha di elementi del paesaggio |
| completezza | tutti i campi | solo le aziende che presentano il piano colturale |
| licenza | **CC BY 4.0** | **non dichiarata** |
| dove sta | nel pex (34 MB) | sul volume (387 MB) |

Misure che hanno deciso l'impianto, su 24 punti di prova in tutta la regione:
- AGREA copre piu' di iColt in **21 punti su 24**; nei 3 contrari il margine e'
  0,1-4,2 punti percentuali;
- aderenza alle statistiche ufficiali: AGREA **97,6%** della SAU censita,
  iColt 74,1%; vite entro 0,4-5,9% contro -22/-26%;
- l'**89% di iColt e' contenuto in AGREA**, ma il **51% di AGREA e' fuori da
  iColt**. In pianura sono ridondanti (IoU 0,77), in collina c'e' solo AGREA
  (IoU 0,067, e zero in 9 punti su 13);
- correlazione del rapporto di copertura con la pendenza mediana: **Pearson -0,92**.
  La provincia non predice nulla, la topografia si'.

**Quindi: AGREA guida, iColt resta come controllo indipendente.** Non si butta
perche' e' l'unica fonte senza bias dichiarativo e senza soggetto, e perche'
l'accordo geometrico fra le due e' circa l'80%, non il 100%: in pianura quel
disaccordo e' l'unica stima onesta dell'incertezza da mostrare all'utente. La
pagina lo scrive: "la classificazione satellitare dice 13,3%, cioe' 2,0 punti di
scarto".

**Se i file AGREA non sono sul volume tutto ricade su iColt**, senza errori e
senza pagine rotte. Verificato avviando il servizio con un volume vuoto.

### Le classi sono SPECIE, ricavate senza interpretazione

`DESC_COLT` di AGREA e' la concatenazione di specie + destinazione + uso +
varieta', e AGREA fornisce gli altri tre in campi propri (`DESC_DEST`,
`DESC_USO`, `DESC_QUAL`). Sottraendoli resta il nome della specie, per **rimozione
esatta di stringhe**: nessuna regola a parole chiave, nessuna tabella di raccordo
da verificare a mano, nessuna interpretazione.

Verificato su **tutti i 778 codici** regionali: **366 specie distinte, zero
rimozioni fallite**. I 14 codici del mais (granella, insilato, energetico, da
seme, dolce, pastone, popcorn) collassano su un'unica specie, che e' l'unico
accorpamento sensato: sono destinazioni dello stesso mais.

Tutte e otto le colture del registro di tornatura hanno una riga propria e
nessuna resta dentro un aggregato:

    mais 95.554 ha · vite 52.824 · barbabietola 18.852 · pero 9.542
    pesco 6.688 (PESCO + PESCO NETTARINA) · albicocco 4.157 · olivo 3.697
    agrumi presenti nello schema ma ~0 ha in regione

In un raggio di 3 km compaiono 45-73 specie, di cui 34-46 con almeno tre
appezzamenti. `HARVEST_TO_AGREA_SPECIES` in `modules/config.py` e' la mappa da
`HarvestType.code` all'insieme di specie: e' un insieme perche' il pesco
comprende le nettarine e gli agrumi si dichiarano per specie.

### Cosa e' cambiato nel codice

**Nuovi file**
- `modules/agrea.py` — la sorgente AGREA: lettura per finestra, composizione,
  quota semi-naturale, geometrie per la mappa.
- `src/typescript/web/src/components/MapLandscapeCrops.tsx` — la mappa mapbox-gl.
- `src/typescript/web/src/features/fields/pages/field-landscape.tsx` — la pagina.

**Endpoint**
- `/v1/landscape/parcels` (**nuovo**): geometrie ritagliate sul buffer, il
  poligono del buffer, la classe e gli ettari per appezzamento.
- `/v1/landscape/composition`: aggiunge `source`, `crosscheck`, `seminatural`,
  `observability`, `coverage_note`, `mapped_ha`. `agri_ha` resta per
  compatibilita' ma il nome e' improprio (vedi sotto).

**Middleware**: aggiunto `GZipMiddleware(minimum_size=1000)`. Non e' un
dettaglio: senza compressione il payload geometrico passa da 143 kB a 1,16 MB.
**Il reverse proxy deve propagare `Accept-Encoding` all'upstream**, altrimenti la
funzione risulta lenta solo in produzione e solo sulle connessioni peggiori.

### Cinque difetti corretti della versione precedente

1. **Copertura di collina.** `is_covered()` confrontava il punto col *bounding
   box* del dataset, ma iColt cartografa la pianura: misurato **0 ettari entro
   3 km da Brisighella e dai Colli Bolognesi**, dove la pagina mostrava
   "superficie agricola 0%". Ora `observability()` decide a **raggio fisso di
   3 km**, indipendente dal selettore dell'utente — prima bastava premere "10 km"
   per ottenere una pagina piena che descriveva la pianura di Faenza — e guarda
   anche la distribuzione per quadrante, per il caso pedecollinare.
2. **Righe che erano singole aziende.** Misurato: al raggio di default il **72%**
   delle posizioni aveva almeno una classe sostenuta da UN solo appezzamento,
   mentre il piede della pagina dichiarava "descrive il paesaggio, non singole
   aziende". Ora le classi sotto tre appezzamenti si accorpano in "altre colture"
   e il conteggio non si pubblica. Costo misurato: 0,1-0,9% della superficie.
3. **L'indicatore di presenza e' stato rimosso.** Era una scala ordinale a tre
   gradini (soglie 20% e 50%) con icone crescenti, collocata subito dopo
   "Modelli previsionali" e "Bollettini fitosanitari": un indice di rischio in
   tutto tranne il nome. **Le soglie non avevano fonte.** La ricerca
   bibliografica non ha trovato alcuna soglia pubblicata di concentrazione
   dell'ospite per nessuna coppia coltura/organismo di questa app, e per la
   peronospora, la flavescenza e il colpo di fuoco il meccanismo va in direzione
   diversa da quella suggerita. Argomento aggiuntivo: il solo passaggio da iColt
   2025 a 2026 ha spostato il pero dal 9,6% all'8,6%, quindi un'azienda vicina a
   una soglia cambierebbe etichetta al solo aggiornamento del dataset.
4. **Etichetta "superficie agricola".** Il layer ARPAE distribuito NON contiene i
   codici non agricoli (10/11/15/16): verificato, `NON_AGRI_CODES` non scatta mai
   e `is_agri` e' sempre vero. Quindi quel numero e' la superficie
   **cartografata**, non la superficie agricola. Aggiunto `mapped_ha`; `agri_ha`
   resta per compatibilita'.
5. **Raggio predefinito a 3 km** (era 5). E' l'unico dei tre raggi offerti per cui
   esistano studi che vi trovino un effetto di paesaggio; per i 10 km non ne
   esiste nessuno.

### Difetti preesistenti segnalati e NON corretti

1. `getFieldCentroid` in `field-model-bollettini.tsx` e
   `field-model-peronospora.tsx` **solleva un'eccezione sui campi con poligono
   non chiuso**, e dentro `useMemo` questo rende la pagina bianca. Verificato con
   un campo reale in archivio. Le due pagine servono la produzione e non sono
   state toccate; la pagina nuova chiude l'anello e ha un try/catch.
2. `mapModelApiError` nomina "Bollettino" e "servizio bollettini" nei fallback
   generici 404 e 5xx, che sono condivisi da tutti i model API.
3. `field-model-bollettini.tsx` chiama `getFieldMapGeoJson(currentField)` fuori
   dalle guardie, mentre la firma non accetta `undefined`.
4. `hadolint` segnala DL3008 sul Dockerfile (versioni apt non fissate): e'
   **preesistente su entrambi** i Dockerfile di bollettini e peronospora.

### Il peso dei dati, e come e' risolto

I due file AGREA pesano **387 MB per annata** (334 colture + 53 elementi). Tre
strade sono state misurate e scartate:

- **Dentro l'immagine Docker: NO.** L'immagine passerebbe da 1,11 a ~1,8 GB, ma il
  costo peggiore e' un altro ed e' misurato: con `execution_mode="venv"` e
  `layout="packed"` il pex materializza i dati in **due copie aggiuntive** dentro
  `PEX_ROOT` (489 MB oggi con i soli 34 MB di iColt), e `PEX_ROOT` sta sotto
  `~/.pex`, **fuori dal volume dichiarato**, quindi viene riestratto a ogni
  ricreazione del container.
- **In git: NO.** 387 MB per annata, per sempre; GitHub rifiuta i file oltre
  100 MB e servirebbe LFS. I 34 MB di iColt sono committati e vanno bene cosi'.
- **Dissolvere per classe per ridurre i poligoni: NO.** Misurato: le query
  passano da 102 ms a **48 secondi** a 3 km (470 volte piu' lente: dentro un
  multipolygon non c'e' indice spaziale), la RAM sale e si perdono popup e
  conteggi.

**La soluzione adottata e' quella che il monorepo usa gia'**, e non richiede
nessuna scelta di infrastruttura. Peronospora scarica ogni giorno i GRIB di ECMWF
dal bucket S3 pubblico `ecmwf-data-forecast` in `weather/cache/` e
`weather/temp_grib/`, che sono gitignorate; bollettini fa lo stesso con
`data/input_bollettini/` e `data/cache/`. In git ci va solo cio' che e' piccolo e
stabile (shapefile e modelli, max 2,4 MB), il resto si scarica dalla fonte nel
`*_RUNTIME_DIR`.

Landscape fa la stessa cosa: **`updater.py` scarica gli archivi dal sito pubblico
di AGREA** e prepara i parquet in `/data/landscape/agrea/`.

    https://agreagestione.regione.emilia-romagna.it/agrea-file/UtilizziGrafici/2026/

Verificato: HTTP 200 senza autenticazione, un file per provincia, con `ETag` per
sapere se sono cambiati. Non serve ospitare niente da nessuna parte.

**Come si usa** (secondo `pex_binary`, gemello dello `scheduler` di peronospora):

    python /bin/landscape-updater.pex --check       stato del volume
    python /bin/landscape-updater.pex --run-now     scarica e prepara se serve
    python /bin/landscape-updater.pex --run-now --force
    python /bin/landscape-updater.pex --run-now --provinces FE,RA

**E' idempotente**: confronta gli `ETag` remoti con quelli registrati nel manifest
e se combaciano non fa nulla, quindi si puo' invocare a ogni avvio senza costo.
Verificato. La scrittura e' **atomica** (file temporaneo piu' rename): un'interruzione
non lascia un parquet mezzo scritto. Gli archivi si scaricano una provincia alla
volta e **si buttano subito dopo la conversione**, quindi non servono 2 GB liberi
in contemporanea.

Differenza di frequenza rispetto a peronospora: quello gira ogni giorno, questo
**una volta l'anno**, perche' AGREA pubblica una campagna per anno. Per questo non
c'e' nessuno scheduler.

**Tempi misurati** su due province: 109 MB scaricati in 396 s e 151 MB in 80 s (il
server AGREA e' molto variabile), piu' 14-17 s di conversione per provincia. Per
tutte e nove le province il grosso del tempo e' lo scaricamento.

**Se l'updater non gira mai, il servizio funziona sul solo iColt**: nessuna pagina
si rompe. Verificato avviando con un volume vuoto.

### Come si preparano i dati AGREA

Gli archivi si scaricano da
`https://agreagestione.regione.emilia-romagna.it/agrea-file/UtilizziGrafici/<anno>/`
— pubblici, senza autenticazione, un file per provincia piu' `XX` per le
particelle fuori regione (da escludere). Sono disponibili le annate 2021-2026.

Lo script di preparazione (oggi fuori dal repository) fa, per provincia:
lettura con `/vsizip` senza estrarre, specie per sottrazione, riproiezione da
**EPSG:3003 Monte Mario** a 4326 (trasformazione di datum verificata: 85% di
sovrapposizione geometrica con iColt sulle superfici a pero), `make_valid`,
`simplify(1 m)`, arrotondamento a 6 decimali, filtro SAU + bosco e >= 0,05 ha.
Poi unisce, ordina per curva di Hilbert e scrive GeoParquet 1.1 con
`write_covering_bbox=True` e `row_group_size=10.000`. Circa 5 minuti per tutte e
nove le province.

Scelte misurate, da non cambiare a occhio:
- `simplify(1 m)` fa **-57% di byte per -0,05% di superficie**. Su AGREA conviene
  molto (geometrie ritagliate sul catasto, molti vertici quasi collineari), al
  contrario di iColt dove non conveniva.
- arrotondamento a **6 decimali e non oltre**: a 5 decimali si perde il 3,1% dei
  poligoni e a 4 un terzo, perche' annichila gli elementi lineari.
- lettura **per finestra da file** e non cache in memoria: misurato 681 MB di RSS
  contro **5.983 MB** della cache, a parita' di latenza e senza avvio a freddo di
  6 secondi. La colonna bbox e' cio' che lo rende possibile: **il file iColt
  attuale non la ha**, e per questo resta in RAM.
- gli **elementi del paesaggio** si conservano come centroide piu' superficie, non
  come poligono: sono 902.542 oggetti con mediana 166 m2, servono solo al numero
  aggregato e mai al client. Scarto misurato contro il ritaglio esatto: 0,0-2,0%.

### Dipendenze

`geopandas>=1.0` (alzato da `>=0.14.0`): la lettura per finestra da GeoParquet 1.1
richiede la 1.0. Con un vincolo piu' basso una futura rigenerazione del lock
potrebbe risolvere una 0.x e il servizio tornerebbe a caricare tutto in RAM, in
silenzio. Lockfile rigenerato: geopandas 1.1.4, shapely 2.1.2, pyarrow 25.0.1.

### Prestazioni misurate

| | 3 km | 5 km |
|---|---|---|
| payload mappa (gzip) | 143 kB | 373 kB |
| tempo di risposta | 0,26 s | 0,63 s |
| poligoni disegnati | 1.997 | 5.202 |

La mappa disegna gli appezzamenti sopra **0,2 ha** = 96% della superficie; le
percentuali li contano tutti, e l'interfaccia dichiara la differenza. Il layer
geometrico AGREA e' cappato a 5 km (sopra, si ricade su iColt); `/composition`
regge fino a 20 km perche' restituisce solo numeri.

### Invariato

Nessuna modifica al `core`: modello dati, permessi, Keycloak, MinIO e SDK generato
sono intatti (`git diff main -- src/python/core src/typescript/coreapis-sdk` e'
vuoto). Nessuna modifica ai servizi `bollettini` e `peronospora`, ne' alle pagine
frontend esistenti. Nessuna modifica al database: nessun indice, nessuna
collezione, nessuna migrazione.

---

## [2026-08-19] - Passaggio all'annata iColt 2026

Sostituzione del dataset: `data/icolt2025_er.parquet` → `data/icolt2026_er.parquet`.
Nessuna modifica alla logica, agli endpoint o al contratto della risposta.

### Cosa cambia

| | 2025 | 2026 |
|---|---|---|
| particelle | 114.841 | **117.696** |
| superficie cartografata | 776.850 ha | **772.960 ha** (−0,5%) |
| classi | 16 | 16 (stesse) |
| particella minima | 0,5 ha | 0,5 ha |
| file | ~31 MB | ~34 MB |

Variazioni sulle classi arboree, piccole e plausibili: vigneti +2%, melo +4%,
susino +8%, pero −5%, pesco −3%, ciliegio −5%. Le due variazioni grosse sono
`prati e medica` −15% e `colture autunno-vernine` +10%, che si compensano, e
`arboricoltura da legno` +87% (1.074 → 2.093 particelle), che ha il profilo di
una riclassificazione più che di nuovi impianti: da non leggere come cambiamento
reale del paesaggio.

### Note sulla conversione (per il prossimo anno)

Lo schema ARPAE **cambia di anno in anno**. Il 2026 arriva come `Id, ID_CROP,
Area, ID_CLASS, Anno` in EPSG:32632, mentre il 2025 era `Id, gridcode, Area_HA,
ID_CLASS, ID_CROP, ANNO` in EPSG:4326. È stato normalizzato allo schema
precedente (rinominando `Area`→`Area_HA` e `Anno`→`ANNO`, scartando `gridcode`
che il codice non usa) e riproiettato in 4326, così il codice non cambia.

Qualità del dato 2026: superficie dichiarata e superficie geometrica coincidono
allo 0,000%; 9.140 geometrie non valide, riparate con `make_valid()` prima della
scrittura del parquet. Il layer distribuito è, come nel 2025, privo dei codici
non agricoli (nubi, neve, aree non acquisite).

### Aggiornamento dei valori di riferimento

Il test di non-regressione in `CLAUDE.md` è stato rimisurato sull'annata nuova:
6.053,3 ha cartografati, 953 appezzamenti, pero 520,8 ha = 8,6% (era 581,5 =
9,6%). Il calo del pero prosegue e è coerente con la tendenza regionale.

---

## [2026-08-18] - Primo rilascio: composizione colturale del paesaggio

### Overview per il team

Nuovo servizio modello `landscape`, il terzo dopo `bollettini` e `peronospora`.
Dato un punto e un raggio, restituisce la **composizione colturale del paesaggio
agricolo** circostante (ettari e percentuali per coltura) usando la
classificazione satellitare **iColt** di ARPAE Emilia-Romagna.

Alimenta la nuova voce *"Il tuo paesaggio"* nella scheda del campo: posizione =
centroide del poligono del campo, coltura = `harvest` dichiarato. Nessun input
aggiuntivo per l'utente.

Origine: prototipo Streamlit `crop_class_map`, di cui è stata portata la logica di
analisi (invariata nella geometria del calcolo) scartando tutta la parte di
interfaccia e il geocoding degli indirizzi, non più necessario.

### Cosa cambia

1. **Nuovo servizio** `src/python/landscape` (FastAPI, senza autenticazione come
   gli altri model API), esposto su `/v1/landscape/*` **sotto lo stesso origin**
   dei model API esistenti: nessuna variabile d'ambiente nuova nel frontend.
2. **Endpoint**: `/v1/landscape/health`, `/v1/landscape/coverage`,
   `/v1/landscape/composition?lat&lng&radius_m&crop`.
3. **Dataset incluso nel package** (`data/icolt2026_er.parquet`, ~34 MB, 117.696
   particelle, EPSG:4326): il container è autosufficiente, niente provisioning.
4. **Mappatura colture esplicita**: solo `vite`, `pero`, `pesco`, `olivo`,
   `albicocco` hanno una classe iColt dedicata. `mais` e `barbabietola` ricadono
   nella classe aggregata "colture estive" e `agrumi` è assente dal dataset: in
   questi casi la risposta espone `crop.mappable = false` con il motivo, e
   l'interfaccia lo dichiara invece di mostrare un numero fuorviante.
5. **Nessuno scheduler** — differenza voluta rispetto a bollettini e peronospora:
   iColt è annuale e si aggiorna a mano, non c'è nulla da schedulare. L'immagine
   contiene un solo PEX (`api`) e il `CMD` avvia direttamente l'API.

### Dipendenze (Pants)

- Nuovo resolve `landscape` in `pants.toml`, requirements in
  `3rdparty/python/landscape-requirements.txt`, lockfile
  `3rdparty/python/landscape.lock`.
- `fastapi`, `uvicorn`, `geopandas`, `shapely`, `pandas`, **`pyarrow`**.
  `pyarrow` è obbligatoria e non inferibile: `geopandas.read_parquet` la richiede.
- `modules/BUILD` dichiara **`resolve="landscape"`**. È una differenza rispetto a
  `bollettini`, dove `modules/` viaggia dentro il target `resources` e il
  `python_sources()` della sottocartella resta sul resolve `default`: in quel caso
  l'inferenza delle dipendenze di Pants lo **scarta silenziosamente**, perché
  considera solo i target con resolve compatibile. Dichiarando il resolve i moduli
  entrano nel pex come codice Python vero e il grafo delle dipendenze è verificabile
  con `pants dependencies --transitive src/python/landscape:api`.

### Dettagli del contratto verificati sul servizio in esecuzione

- Raggio o coordinate fuori range danno **422** (validazione Pydantic di `Query`,
  con `detail` come **array**), non 400: è lo stesso comportamento di bollettini e
  peronospora. Il frontend, che invia solo raggi da un elenco chiuso, non lo incontra.
- Se `crop` non è indicato la risposta ha `crop: null` — assenza della domanda, da
  non confondere con una coltura non mappabile.
- Coltura mappabile ma con zero ettari nel raggio (es. `vite` in un'area senza
  vigneti) restituisce `pct_of_agri: 0` e `presence: null`: zero non è "presenza
  limitata", e l'interfaccia lo dice come assenza.
- Prestazioni misurate: prima richiesta 0,38 s (caricamento del GeoParquet),
  successive 0,03 s. Nessun bisogno di warm-up all'avvio.

### Frontend (`src/typescript/web`)

Quattro innesti, nessuna modifica a `store.ts`, `hooks.ts`, `fields-slice.ts`,
`App.tsx`, `vite.config.ts` o ai file `.env`:

1. `src/services/model-api.ts`: tipo `LandscapeResponse`, tre voci nella mappa di
   traduzione degli errori, funzione `fetchLandscapeComposition`.
2. `src/features/fields/pages/field-landscape.tsx` (**nuovo**): la pagina, modellata
   su `field-model-bollettini.tsx`.
3. `src/routes.tsx`: rotta `landscape` sotto la scheda campo.
4. `src/features/fields/pages/field-detail.tsx`: voce di menu "Il tuo paesaggio"
   (icona `sprout`), autonoma e non sotto "Modelli previsionali" — non è una
   previsione, è contesto.

La pagina si discosta dai due modelli in un punto, deliberatamente: `getFieldCentroid`
**chiude l'anello del poligono** prima di passarlo a `turf.polygon` ed è protetta da
`try/catch`. In archivio esistono campi con anello non chiuso (`map` con primo e
ultimo vertice diversi) e `turf.polygon` in quel caso solleva
`"First and last Position are not equivalent"`: dentro `useMemo` l'eccezione farebbe
cadere l'intero render. Vedi le note per il team più sotto.

### Invariato

Il `core` non è toccato: nessuna modifica a modello dati, permessi, Keycloak o
SDK generato. Nessuna modifica ai servizi `bollettini` e `peronospora`, né alle
pagine frontend esistenti.

### Segnalazioni al team (difetti preesistenti, NON corretti qui)

1. **`getFieldCentroid` in `field-model-bollettini.tsx` e `field-model-peronospora.tsx`
   va in eccezione sui campi con poligono non chiuso.** Verificato: con l'anello
   aperto di un campo reale in archivio, `turf.polygon` solleva un'eccezione; con
   l'anello chiuso il centroide è corretto. Essendo dentro `useMemo`, la pagina
   diventa bianca. Le due pagine non sono state toccate perché servono la produzione.
2. **`mapModelApiError` nomina "Bollettino"/"servizio bollettini" nei fallback
   generici 404 e 5xx**, che sono condivisi da tutti i model API. Mitigato qui
   mappando esplicitamente i `detail` del nuovo servizio, così il fallback non
   scatta; la correzione della funzione va concordata.
3. `field-model-bollettini.tsx` chiama `getFieldMapGeoJson(currentField)` **fuori
   dalle guardie** su `currentField`, mentre la firma non accetta `undefined`. La
   pagina nuova mette la guardia prima.

### Impatto sul deploy

1. Serve **una regola nel reverse proxy**: `/v1/landscape/*` → nuovo container.
   Senza, la pagina non funziona in produzione.
2. Volume `/data/landscape` (usato solo per i log; i dati sono nell'immagine).
3. Nuova immagine `darkform/tornatura.landscape:1.0.0`, **solo API**.

### Limiti noti e dichiarati

- **Copertura solo Emilia-Romagna**: fuori area l'API risponde `404 Location
  outside data coverage` e la pagina mostra un messaggio esplicito che nomina il
  limite. La voce di menu resta **sempre visibile**: nasconderla richiederebbe una
  chiamata asincrona a `/coverage` dentro `field-detail.tsx`, che è la pagina
  condivisa da tutte le schede campo, e non valeva il rischio in questa prima
  fetta. L'endpoint `/coverage` esiste già per farlo quando si deciderà.
- Dati da classificazione satellitare: robusti sugli aggregati, meno sulla
  singola particella. Le affermazioni restano su percentuali e classi.
- Dato **annuale**, non in tempo reale: l'anno è sempre esposto nella risposta.
- L'indicatore di presenza è **divulgativo, non un indice di rischio**.
