# Il paesaggio letto per organismo: la cimice asiatica come primo caso

2026-09-24 · Vito Palmisano, con Claude · stato: **adottata**

## Contesto

La pagina *Il tuo paesaggio* dice cosa c'e' intorno a un campo: colture dichiarate, quota della
coltura dell'utente, ambienti semi-naturali. Alla riunione del 23/09/2026 (Vito, Agata Morelli,
Francesco Solimei) si e' deciso di farle dire anche **quanto quell'intorno e' favorevole a un
organismo**, partendo dalla cimice asiatica (*Halyomorpha halys*): quante piante ospiti ci sono,
quanto sono vicine, quanti rifugi. In prospettiva e' un ingresso di un indice di idoneita' insieme
ai gradi-giorno del servizio `hhalys`. Il perche' ora: la cimice e' l'avversita' su cui l'app ha
gia' rilevamenti e bollettini, e i dati AGREA nominano le specie con la granularita' necessaria.

Prima di scrivere codice si e' fatto un esperimento (`esperimenti/cimice_landscape/`, 33 punti,
raggi 500 m-5 km) che ha deciso **quali metriche** e **quale lista ospiti**.

## Decisione

1. **Una funzionalita' per qualsiasi organismo, non per la cimice.** Ogni organismo e' una cartella
   di dati in `src/python/landscape/data/pests/<codice>/` (tabella ospiti + descrizione); il
   calcolo (`modules/pests.py`), l'endpoint (`/v1/landscape/pest-habitat?pest=`) e la sezione in
   pagina sono unici. Scafoideo, peronospora e diabrotica seguiranno aggiungendo una cartella.
2. **Le metriche sono tre**: % di superficie dichiarata per livello ospite (a 500 m, 1, 3, 5,
   10 km, separando frutteti ed erbacee), serbatoi semi-naturali, distanza in **classi** dal
   frutteto ospite e dalla siepe o bosco piu' vicini. La sezione e' descrittiva: nessun punteggio,
   nessun semaforo ("consapevolezza, non rischio").
3. **La lista ospiti discende da fonti, non da un giudizio.** Regola dichiarata su una matrice di
   evidenze (23 fonti, 230 righe): principale = danno documentato in Italia o Europa da almeno
   due fonti indipendenti; secondario = almeno un'evidenza di ospite; non ospite = nessuna o
   negativa. Gli agronomi rivedono le fonti, non i livelli. La versione della tabella viaggia
   nella risposta.

## Alternative scartate

- **Indice di connettivita' a kernel** (aree ospiti pesate per la distanza) e **metriche
  FRAGSTATS** (pylandstats): misurate ridondanti con la % ospiti (correlazioni 0,85-0,97 e
  0,67-0,94 su 33 punti). Coerente con Moilanen & Nieminen 2002 e con gli studi sulla cimice,
  che usano tutti la composizione in buffer. Rientrano solo se un dato di catture lo giustifica.
- **Distanza dal patch piu' vicino come metrica di paesaggio**: la misura meno capace di trovare
  effetti (Moilanen & Nieminen 2002); tenuta solo come indicazione locale, in classi.
- **Pagina separata sotto "Modelli previsionali"**: costa di piu' e separa due cose che l'utente
  legge insieme; la sezione dentro *Il tuo paesaggio* riusa mappa, raggio e tabella.
- **Blocco dentro `/composition`** invece di un endpoint proprio: avrebbe richiesto di passare il
  contorno del campo a un endpoint che oggi riceve un punto, e avrebbe legato la risposta a un
  solo organismo. L'endpoint proprio e' riusabile dalla futura pagina GDD.
- **Livelli decisi da un esperto**: non riproducibile e non difendibile; sostituito dalla matrice
  di evidenze.
- **Un quinto colore sulla mappa** per gli ospiti: fuori dal vincolo dei quattro colori misurato
  (`landscape/CLAUDE.md`); si usa una modalita' esclusiva che ricolora per livello con i colori
  gia' validati.

## Cuciture

- **`landscape`** (servizio modello, senza autenticazione): nuovo modulo `modules/pests.py`,
  cartella `data/pests/`, due endpoint nuovi, `host_level` e `declared` nelle feature di
  `/parcels` quando si passa `pest=`, `MIN_RADIUS_M` da 1000 a 500 m. Nessuna dipendenza nuova.
- **`web`**: raggi 500 m e 1 km, terza chiamata nella pagina del paesaggio, componente
  `PestHabitatSection`, modalita' "ospiti" nella mappa.
- **Il core NON e' toccato**: nessuna modifica a Mongo, Keycloak, permessi, SDK. La pagina invia
  al servizio il contorno del campo (`ring`) per le distanze bordo a bordo: e' un dato che oggi
  il servizio riceve gia' come centroide, e non viene conservato.
- **Anonimato**: totali aggregati; prime specie con la regola dei tre appezzamenti; distanze in
  classi e mai in metri.

## Verifica

Servizio (dati AGREA sul volume, `strumenti/tornatura-dev.sh start`):

```
GET /v1/landscape/pests?crop=pero                          -> un organismo: halyha
GET /v1/landscape/pest-habitat?lat=44.80951&lng=11.75644&radius_m=3000&crop=pero&pest=halyha
GET /v1/landscape/pest-habitat?lat=44.80951&lng=11.75644&radius_m=500&crop=pero&pest=halyha
GET /v1/landscape/composition?lat=44.80951&lng=11.75644&radius_m=500&crop=pero   (ora 200, prima 422)
```

Attesi a Ferrara, 3 km (dall'esperimento, stessi dati): ospiti 63% del dichiarato, principali
59% (erbacee 43%, frutteti 20%), serbatoi 2,7% del cerchio, frutteto ospite piu' vicino "entro
100 m", prime specie mais, soia, pero (268 ha, cioe' l'11,3% che la pagina gia' mostra), melo,
pomodoro. Brisighella: serbatoi ~15%, principali ~9%, secondari ~38% (vite, olivo, kiwi). Con il
volume AGREA vuoto: `available: false`, pagina intera funzionante su iColt. La risposta non
contiene mai distanze in metri ne' identificativi.

Frontend: `npm run build`; nel browser i raggi 500 m e 1 km muovono cerchio, tabella e sezione;
il chip "Ospiti della cimice" ricolora la mappa senza colori nuovi; con AGREA assente la sezione
non compare.

## Conseguenze

- **Rilascio**: due immagini, `landscape` e `web`. La tabella ospiti viaggia nel pex; i parquet
  restano sul volume (in staging ci sono gia').
- **Dati**: nessun dato nuovo da scaricare. La licenza AGREA non dichiarata resta la condizione
  gia' nota prima della produzione.
- **Utenti**: la pagina del paesaggio guadagna due raggi e una sezione; nessuna pagina nuova.
- **Prossimi passi gia' previsti**: finestra fenologica per coltura e data (BBCH dei bollettini o
  date AGREA) come moltiplicatore 0-1; verde urbano da una fonte esterna; altri organismi come
  cartelle in `data/pests/`.
