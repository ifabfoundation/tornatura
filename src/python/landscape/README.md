# Landscape — il paesaggio agricolo intorno al campo

Terzo servizio modello del monorepo, dopo `bollettini` e `peronospora`. Fa due
cose:

- dato un punto e un raggio, dice **quali colture ci sono intorno** e in quale
  proporzione, e alimenta la pagina *"Il tuo paesaggio"* nella scheda del campo;
- serve i **pezzi dichiarati** con cui comporre il confine di un campo nuovo nel
  wizard "Aggiungi campo", invece di tracciarlo a mano.

Per la prima, posizione e coltura non si chiedono all'utente: la posizione è il
centroide del poligono del campo, la coltura è il suo `harvest` dichiarato.

## Due sorgenti, dichiarate

**AGREA** — i piani colturali che le aziende dichiarano per la PAC. Nomina 311
specie, copre anche la collina, e contiene bosco, siepi, margini e fossi. Ma
esiste solo per le aziende che presentano la dichiarazione, e non tutte ne hanno
l'obbligo. È la sorgente principale. Vive sul **volume runtime** (~1 GB).

**iColt (ARPAE)** — classificazione da immagini satellitari invernali. 16 classi,
minimo 0,5 ha, copre la pianura e praticamente nulla sopra i 200 m di quota. È il
**controllo indipendente**: non ha bias dichiarativo e la pagina mostra il
disaccordo fra le due come stima dell'incertezza. Viaggia dentro il pex (34 MB).

Se i file AGREA non sono sul volume, il servizio funziona sul solo iColt senza
errori.

## API

```
GET /v1/landscape/health
GET /v1/landscape/coverage
GET /v1/landscape/composition?lat=&lng=&radius_m=&crop=
GET /v1/landscape/parcels?lat=&lng=&radius_m=&crop=
GET /v1/landscape/pieces?lat=&lng=&radius_m=
GET /v1/landscape/parcel-at?lat=&lng=
```

`radius_m`: default 3000, ammessi 1000–20000 per `composition`, fino a 10000 per
`parcels` (il layer geometrico AGREA è cappato a 5000), fino a 3000 per `pieces`.

`parcels` serve il livello **grosso** — l'appezzamento dichiarato, per la pagina
del paesaggio. `pieces` serve il livello **fine** — il frammento come sta nel
dato, per disegnare il campo. Sono due granularità con due scopi, non un
doppione: vedi `CLAUDE.md`.

## Principio guida

**Contesto e consapevolezza, non rischio.** Il dato dice cosa c'è intorno, non
quanto sia probabile un'infezione. Ogni limite noto è dichiarato in interfaccia
invece di essere nascosto: la copertura parziale in collina, la sottostima di
vite e olivo in iColt, la soglia di disegno sulla mappa, e il disaccordo fra le
due sorgenti.

Per il disegno del campo vale l'altra metà dello stesso principio: **il disegno a
mano resta sempre possibile**, i pezzi mancano spesso e la loro assenza non deve
mai impedire di procedere. E quando l'unione dei pezzi scelti non entra nella
forma che il database può contenere — un anello solo, senza parti staccate e senza
buchi — l'interfaccia dice cosa ha scartato invece di troncare in silenzio.

## Documentazione

- `CLAUDE.md` — architettura, calcolo, limiti misurati, note operative
- `CHANGELOG.md` — storico e **note per il team**, incluso il problema del peso
  dei dati e cosa serve deciderne prima della produzione
- `MANIFEST.txt` — contenuto del package e istruzioni di build
