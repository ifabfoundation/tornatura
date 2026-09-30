# Le zone semi-naturali intorno al campo: tutte le fonti, ogni ettaro una volta

2026-09-28 · Vito Palmisano, con Claude · stato: **adottata**

## Contesto

*Il tuo paesaggio* misurava il semi-naturale solo con le dichiarazioni PAC (AGREA): bosco dichiarato
piu' siepi, margini e fossi. AGREA vede i terreni di chi presenta la domanda, non i boschi
pubblici, abbandonati o di non agricoltori: in regione dichiara 172.959 ha di bosco, la Carta
forestale regionale 2025 ne conta 598.593. Per la cimice asiatica sono proprio queste zone a contare
(Forresi et al. 2024, rete regionale: vegetazione spontanea, sponde e canali, siepi, boschetti,
edifici in primavera; Tamburini et al. 2023: semi-naturale a 3 km). Un conteggio che ne vede un terzo
non e' equo, e sbaglia di piu' proprio in collina.

L'esperimento `esperimenti/bosco_paesaggio/` (SCHEDA con tutti i numeri) ha confrontato otto fonti
sugli stessi 33 punti a 500 m, 1, 3 e 10 km e su tutta la regione.

## Decisione

1. **Sei categorie**, dalla letteratura: bosco; arbusteti e vegetazione spontanea; siepi, filari e
   boschetti; sponde, fossi e margini (sono il "semi-naturale" della pagina); impianti arborei
   (arboricoltura, pioppeti, castagneti e noccioleti non dichiarati); edifici e verde urbano, il
   rifugio invernale della cimice, tenuto **a parte**.
2. **Quattro fonti in ordine di priorita'**, e ogni ettaro appartiene alla prima che lo vede:
   AGREA 2026 (appezzamenti ed elementi, con la loro forma) > Carta forestale regionale 2025 > Uso
   del suolo di dettaglio 2023 > Copernicus Small Woody Features 2021 (solo i pixel di siepi e
   alberi che nessuna fonte precedente vede, fuori da vigneti, frutteti e oliveti). Le tabelle di
   classi stanno in `config.py` (`SEMINATURAL_*`).
3. **Il ritaglio si fa una volta, non a richiesta.** L'updater, dopo AGREA, scarica le fonti
   regionali e il raster europeo e scrive sul volume uno strato vettoriale gia' ritagliato fuori da
   AGREA e un raster dei pixel residui (`seminaturale/`). A richiesta si sommano superfici che non si
   toccano mai: `/composition` a 10 km in 0,6-2,1 s (al volo il bosco da solo costava 18 s).
4. **Il dato non cambia forma per chi lo usa**: `seminatural` (in `/composition`) e `reservoirs` (in
   `/pest-habitat`) tengono i campi di prima e aggiungono `categories` con ettari per categoria e per
   fonte. L'organismo sceglie nel suo `meta.json` quali categorie sono suoi serbatoi e quali rifugi
   invernali. La distanza dal "serbatoio piu' vicino" usa anche gli strati nuovi. La mappa disegna il
   bosco, gli arbusteti e gli edifici delle fonti regionali, con la fonte nel popup, e le siepi
   Copernicus come immagine.
5. **Se gli strati mancano** (volume vecchio, fonte non raggiungibile) il servizio risponde come
   prima con il solo AGREA, e la risposta lo dice (`layers`).

## Alternative scartate

- **Copernicus Forest Type / Tree Cover Density, ESA WorldCover per il bosco**: contano come alberi i
  frutteti. Ferrara 3 km: bosco della Carta forestale 3 ha, Forest Type 411, ESA 178.
- **Uso del suolo al posto della Carta forestale per il bosco**: concordano (82% di intersezione su
  unione in collina) ma dove non concordano ha ragione la Carta forestale (bosco ripariale, boschi
  dentro aree di servizio); e' piu' recente e separa per legge bosco, arboricoltura e frutteti.
- **Small Woody Features come fonte delle siepi, da solo**: un terzo dei suoi pixel in collina e'
  dentro il bosco e piu' della meta' fuori dai campi. Entra solo per il residuo che nessun'altra
  fonte vede.
- **Siepi del Database topografico regionale**: solo le siepi "di buona consistenza", linee senza
  larghezza, scaricabili per comune.
- **Ritaglio al volo**: 18 s a 10 km in collina.

## Cuciture

Solo `src/python/landscape` (nuovi `modules/seminaturale.py` e `modules/seminaturale_prepare.py`,
elementi AGREA salvati anche con la forma in `agrea_prepare.py`, dipendenza nuova `rasterio` nel
resolve `landscape`) e `src/typescript/web` (sezione "Ambienti semi-naturali", sezione della cimice,
popup della mappa). Il core non e' toccato.

## Verifica

Numeri a 3 km (percentuale del cerchio, semi-naturale = bosco + arbusteti + siepi + sponde), con i
dati AGREA locali: Ferrara 3,9%, Brisighella 36,3%, Colli Bolognesi 54,7% (prima 2,7%, 15,5%,
13,5%). Senza il residuo Copernicus coincidono con l'esperimento (3,1%, 34,5%, 53,2%). Nessun
punto sotto il valore di prima. Con la cartella `seminaturale/` vuota la risposta e' il solo AGREA
(Ferrara 2,9%) e lo dichiara. Il servizio resta entro 2,5 s a 10 km.

## Conseguenze

- Licenze: Carta forestale, Uso del suolo e Copernicus sono CC BY 4.0 o equivalenti: la pagina cita
  "Regione Emilia-Romagna, Carta forestale regionale 2025 e Uso del suolo 2023; Copernicus Land
  Monitoring Service, Small Woody Features 2021".
- Volume: circa 1,1 GB in piu' (`seminaturale/` 0,7 GB, forme degli elementi AGREA 0,35 GB);
  l'updater scarica circa 500 MB dalle fonti nuove.
- Memoria dell'updater: 5,9 GB di picco per AGREA e 4,3 GB per le zone semi-naturali (misurati),
  circa un'ora, una volta l'anno o quando AGREA cambia; sul server si lancia con un tetto di 8 GB,
  cosi' un imprevisto ferma solo lui.
- Una sola immagine del servizio `landscape` e una del `web`.
