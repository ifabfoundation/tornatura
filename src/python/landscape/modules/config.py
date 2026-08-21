"""Configurazione del servizio landscape.

Dataset: classificazione colturale iColt di ARPAE (Agenzia regionale per la
prevenzione, l'ambiente e l'energia dell'Emilia-Romagna), derivata da immagini
satellitari. Copre la sola Emilia-Romagna, con aggiornamento annuale.
"""

# --- Dataset ------------------------------------------------------------------

DATASET_SOURCE = "ARPAE iColt"
DATASET_YEAR = 2026
COVERAGE_REGION = "emilia_romagna"

# Soglia minima di superficie delle particelle nel dataset (documentata da ARPAE).
MIN_PARCEL_HA = 0.5

# --- Classi colturali iColt (colonna ID_CROP) ---------------------------------

CROP_CLASS_MAP = {
    1: "colture estive",
    2: "colture autunno-vernine",
    3: "prati e medica",
    8: "risaie",
    10: "nubi e neve",
    11: "aree non acquisite",
    12: "vigneti",
    13: "frutteti misti",
    14: "olivo",
    15: "nubi",
    16: "neve",
    17: "arboricoltura da legno",
    20: "kiwi",
    21: "albicocco",
    22: "ciliegio",
    23: "kaki",
    24: "melo",
    25: "pero",
    26: "pesco",
    27: "susino",
}

# Classi non agricole: artefatti della classificazione satellitare, escluse dai
# calcoli di superficie agricola.
NON_AGRI_CODES = {10, 11, 15, 16}

UNKNOWN_CLASS = "altro/sconosciuto"

# --- Famiglie di classi, per la colorazione della mappa ------------------------
#
# La mappa NON puo' dare un colore a ognuna delle 16 classi: su un fondo
# satellitare, dove qualsiasi classe puo' confinare con qualsiasi altra, oltre
# quattro colori le coppie diventano indistinguibili anche per chi vede bene
# (misurato con il validatore: giallo/arancio ΔE 13,7 contro una soglia di 15).
# Quindi quattro famiglie con colore FISSO, piu' la coltura dell'utente che ha il
# suo. Il colore non segue mai la posizione in classifica: cambiare raggio non
# deve ridipingere le classi. Il dettaglio per specie vive nella tabella e nel
# popup, dove il nome e' scritto e il colore non porta l'informazione da solo.
FAMILY_PERMANENT = "permanenti"
FAMILY_ANNUAL = "erbacee"
FAMILY_GRASS = "prati"
FAMILY_OTHER = "altro"

CLASS_FAMILY = {
    "vigneti": FAMILY_PERMANENT,
    "pero": FAMILY_PERMANENT,
    "pesco": FAMILY_PERMANENT,
    "melo": FAMILY_PERMANENT,
    "susino": FAMILY_PERMANENT,
    "albicocco": FAMILY_PERMANENT,
    "ciliegio": FAMILY_PERMANENT,
    "kiwi": FAMILY_PERMANENT,
    "kaki": FAMILY_PERMANENT,
    "frutteti misti": FAMILY_PERMANENT,
    "olivo": FAMILY_PERMANENT,
    "arboricoltura da legno": FAMILY_PERMANENT,
    "colture estive": FAMILY_ANNUAL,
    "colture autunno-vernine": FAMILY_ANNUAL,
    "risaie": FAMILY_ANNUAL,
    "prati e medica": FAMILY_GRASS,
}

# --- Soglia di pubblicazione delle righe --------------------------------------
#
# Misurato: al raggio di default il 72% delle posizioni ha almeno una classe
# sostenuta da un SOLO appezzamento. Una riga "olivo - 1 appezzamento - 2,3 ha"
# non descrive il paesaggio, descrive il campo di quel signore. Le classi sotto
# soglia si accorpano e il conteggio non si pubblica. I poligoni restano
# disegnati sulla mappa: quello e' il senso della funzione, ed e' cio' che iColt
# gia' fa.
MIN_PARCELS_PER_ROW = 3
OTHER_ROW_LABEL = "altre colture"

# --- Osservabilita' -----------------------------------------------------------
#
# iColt cartografa la PIANURA, non la regione: misurato 0 ettari entro 3 km da
# Brisighella e dai Colli Bolognesi. Lo stato va deciso a raggio FISSO sulla
# posizione del campo, altrimenti il selettore di raggio lo annulla (a
# Brisighella: 0,0% a 3 km ma 9,4% a 10 km, che descrive la pianura di Faenza).
OBSERVABILITY_RADIUS_M = 3000
OBSERVABILITY_SUPPRESS_PCT = 25.0
OBSERVABILITY_PARTIAL_PCT = 60.0
# Se la porzione cartografata e' concentrata da un lato (caso pedecollinare) la
# percentuale complessiva non lo comunica: si guarda anche per quadrante.
OBSERVABILITY_MIN_QUADRANT_PCT = 10.0

# --- Colture con copertura sistematicamente incompleta ------------------------
#
# Non e' solo l'assenza di cartografia in collina: dove la cartografia c'e', vite
# e olivo sono sottostimati. Vite 38.595 ha in iColt contro 53.236 ufficiali
# (73%); olivo 282 contro ~4.500 (6%), perche' l'olivicoltura emiliana e'
# collinare. Queste colture portano SEMPRE la nota, anche in pianura.
HARVEST_COVERAGE_NOTE = {
    "vite": (
        "La superficie a vigneto e' sottostimata da questo dato: iColt cartografa "
        "la pianura e ne rileva circa il 73% del totale regionale, con il deficit "
        "concentrato in collina."
    ),
    "olivo": (
        "La superficie a olivo e' fortemente sottostimata da questo dato: iColt "
        "cartografa la pianura e ne rileva circa il 6% del totale regionale, "
        "perche' l'olivicoltura emiliana e' collinare."
    ),
}

# --- Geometria ----------------------------------------------------------------

# UTM 32N: sistema metrico locale, usato per buffer e calcolo delle aree in
# Emilia-Romagna. I calcoli di superficie NON vanno fatti in gradi (EPSG:4326).
METRIC_EPSG = 32632

DEFAULT_RADIUS_M = 3000
MIN_RADIUS_M = 1000
MAX_RADIUS_M = 20000

# Rete di sicurezza sul numero di particelle servite alla mappa: a 10 km sono
# circa 3.500, quindi la soglia non scatta in uso normale.
MAX_PARCELS = 8000

# Tetto separato per l'endpoint geometrico: /composition regge 20 km perche'
# restituisce solo numeri, ma a 20 km le geometrie sono 806 kB compressi e 2,35 s
# di calcolo, fuori scala per una connessione in campagna.
MAX_GEOMETRY_RADIUS_M = 10000

# --- Mappatura colture tornatura -> classi iColt -------------------------------
#
# I codici sono quelli di HarvestType.code nel core di tornatura
# (vedi src/python/core/scripts/seed_harvest_types.py).
#
# Solo cinque colture hanno una classe iColt dedicata. Le altre non sono
# distinguibili nei dati satellitari e il servizio lo dichiara esplicitamente
# invece di restituire un numero che sembrerebbe preciso ma non lo e'.

HARVEST_TO_ICOLT = {
    "vite": "vigneti",
    "pero": "pero",
    "pesco": "pesco",
    "olivo": "olivo",
    "albicocco": "albicocco",
}

# Colture che nel dataset ricadono in una classe AGGREGATA (non separabile):
# mais e barbabietola sono entrambe dentro "colture estive", insieme a soia,
# sorgo, pomodoro da industria e altre.
HARVEST_AGGREGATED = {
    "mais": "colture estive",
    "barbabietola": "colture estive",
}

# Colture assenti dal dataset perche' non coltivate nell'area coperta.
HARVEST_NOT_IN_DATASET = {"agrumi"}

# Motivi per cui una coltura non e' mappabile (esposti nella risposta API).
# Classi iColt che raggruppano piu' colture: nel popup della mappa e nei testi non
# si puo' nominare una singola coltura, perche' il dato non la distingue. Il valore
# elenca cosa c'e' dentro, cosi' l'interfaccia lo puo' dire all'utente.
AGGREGATED_CLASSES = {
    "colture estive": "mais, soia, sorgo, girasole, pomodoro, bietola, orticole",
    "colture autunno-vernine": "frumento e altri cereali autunno-vernini, colza",
    "prati e medica": "erba medica e prati di graminacee",
    "frutteti misti": "frutteti con piu' specie, non distinguibili",
}

REASON_AGGREGATED = "aggregated_class"
REASON_NOT_IN_DATASET = "not_in_dataset"
REASON_UNKNOWN = "unknown_harvest_code"


# ==============================================================================
# AGREA - piani colturali grafici dichiarati
# ==============================================================================
#
# Seconda sorgente, di natura diversa da iColt: dichiarazione amministrativa
# invece di osservazione satellitare. Copre la collina (dove iColt e' cieca sopra
# i 200 m di quota o il 15% di pendenza), contiene bosco ed elementi
# caratteristici del paesaggio, e nomina le specie. In cambio esiste solo per le
# aziende che presentano il piano colturale.

AGREA_SOURCE = "AGREA piani colturali grafici"
AGREA_YEAR = 2026

# --- La classe e' la SPECIE, non un raggruppamento -----------------------------
#
# Nel dato preparato la colonna `cls` contiene il nome della SPECIE dichiarata,
# ricavato per sottrazione esatta: DESC_COLT e' la concatenazione di specie +
# destinazione + uso + varieta', e AGREA fornisce gli altri tre in campi propri,
# quindi togliendoli resta la specie. Nessuna regola a parole chiave, nessuna
# interpretazione. Verificato su tutti i 778 codici regionali: 366 specie
# distinte, zero rimozioni fallite; i 14 codici del mais collassano su uno.
# In un raggio di 3 km compaiono 45-73 specie, di cui 34-46 con almeno tre
# appezzamenti.

# --- Colture di tornatura -> specie AGREA --------------------------------------
#
# Tutte e otto hanno una riga propria: nessuna resta dentro un aggregato. Il
# valore e' un INSIEME perche' qualche coltura ha piu' di una specie dichiarata
# (il pesco comprende le nettarine) e perche' gli agrumi si dichiarano per specie.
HARVEST_TO_AGREA_SPECIES = {
    "vite": {"VITE"},
    "pero": {"PERO"},
    "pesco": {"PESCO", "PESCO NETTARINA"},
    "mais": {"GRANTURCO (MAIS)"},
    "barbabietola": {"BARBABIETOLA - RAPA ROSSA/BIETOLA DA COSTA"},
    "olivo": {"OLIVO"},
    "albicocco": {"ALBICOCCO"},
    "agrumi": {"AGRUMI", "ARANCIO", "LIMONE", "MANDARINO", "CLEMENTINE"},
}

# --- Nomi da mostrare ----------------------------------------------------------
#
# Solo presentazione: il nome dichiarato resta quello del dato. AGREA usa
# denominazioni burocratiche che in interfaccia sarebbero illeggibili, e queste
# sono le uniche riscritture, tutte 1:1 e senza accorpare nulla.
AGREA_DISPLAY_NAME = {
    "GRANTURCO (MAIS)": "Mais",
    "BARBABIETOLA - RAPA ROSSA/BIETOLA DA COSTA": "Barbabietola",
    "GRANO (FRUMENTO) TENERO": "Frumento tenero",
    "GRANO (FRUMENTO) DURO": "Frumento duro",
    "ACTINIDIA (KIWI)": "Kiwi",
    "LOTO (KAKI) (COMPRESO IL CACO MELA)": "Kaki",
    "RISONE": "Riso",
    "SUPERFICI AGRICOLE RITIRATE DALLA PRODUZIONE": "Ritirato dalla produzione",
    "SEMINATIVI": "Seminativo non specificato",
    "PESCO NETTARINA": "Pesco (nettarine)",
    "USO NON AGRICOLO - FABBRICATI": "Fabbricati e strade",
    "USO NON AGRICOLO - TARE": "Tare e incolti",
    "USO NON AGRICOLO - ALTRO": "Acque",
    "MARGINI (BORDI) DEI CAMPI": "Margini dei campi",
    "BOSCO": "Bosco",
}

# Famiglie per il colore sulla mappa. Il verde va al SEMI-NATURALE, che e' la
# variabile che la letteratura chiede: bosco e siepi contano piu' della
# distinzione fra prati e seminativi, che resta leggibile nella tabella.
FAMILY_SEMINATURAL = "seminaturale"

# Il layer geometrico AGREA si serve fino a 5 km, non 10: e' quattro volte piu'
# fitto di iColt e a 10 km il payload non e' piu' adatto a una connessione rurale.
AGREA_MAX_GEOMETRY_RADIUS_M = 5000

# Soglia di DISEGNO, non di calcolo. AGREA ha poligoni fino a 1,4 m2: disegnarli
# tutti costa 395 kB compressi a 5 km. Misurato: a 0,2 ha si disegna il 96,5%
# della superficie con 324 kB a 5 km e 123 kB a 3 km. Le PERCENTUALI restano
# calcolate su tutti gli appezzamenti, e l'interfaccia dichiara la differenza.
AGREA_MAP_MIN_HA = 0.2

# --- Precisione, da dichiarare a chi usa le geometrie -------------------------
# La semplificazione applicata in preparazione: differenza di forma 0,4% dell'area
# sul poligono mediano, fino al 7,8% nel caso peggiore, bordo spostato di 0,60 m
# in mediana e 1,62 m al massimo.
AGREA_SIMPLIFY_M = 1.0
# Accuratezza dichiarata dalla migliore trasformazione Monte Mario -> WGS 84
# disponibile in PROJ. Verificato che geopandas usi quella (le alternative
# divergono di 19 e 77 m) e che non ci sia disallineamento sistematico contro
# iColt (ottimo di correlazione a 3 m dallo zero, guadagno 0,10%: rumore).
AGREA_DATUM_ACCURACY_M = 4.0

# ==============================================================================
# Livello fine: i PEZZI, per il disegno di un campo nuovo
# ==============================================================================
#
# Due granularita' con due scopi diversi, misurate sui dati grezzi di Ferrara:
#
#   APPEZZAMENTO  frammenti dissolti per (azienda, ID_APPEZ). E' il campo
#                 agronomico dichiarato: mediana 1,18 ha, e nessuno dei 196.972
#                 appezzamenti contiene due colture. Alimenta "Il tuo paesaggio",
#                 dove serve un'indicazione di cosa c'e' intorno e non la
#                 precisione del bordo.
#   PEZZO         il frammento cosi' com'e' nel dato: appezzamento INTERSECATO la
#                 particella catastale. E' la granularita' minima esistente.
#                 Alimenta il disegno del campo, dove il bordo deve essere
#                 preciso e l'utente deve poter scegliere una porzione.
#
# Perche' non si scende sotto la soglia: il frammento mediano e' 0,04 ha (400 m2)
# e il 51,8% dei frammenti sta sotto 0,05 ha, valendo insieme l'1,27% della
# superficie. Sono le schegge dove una linea di PROPRIETA' taglia un campo di
# sbieco: bordi che sul terreno non si vedono. A 0,25 ha si tiene il 94,5% della
# superficie, i pezzi restano poligoni semplici nel 91,9% dei casi (contro il
# 71,6% degli appezzamenti interi) e il 41,2% degli appezzamenti offre una scelta
# vera, con mediana 2-3 pezzi.
AGREA_PIECE_MIN_HA = 0.25

# I pezzi NON sono semplificati, e non e' una dimenticanza: la semplificazione
# lavora un poligono per volta, quindi due pezzi confinanti si allontanerebbero
# di qualche decimetro sul bordo comune e l'unione uscirebbe con delle fessure.
# Nel dato grezzo i pezzi confinanti si toccano entro 1 cm nel 99,8% dei casi
# (distanza minima mediana 0,000 m), ed e' questo che rende pulita l'unione.
AGREA_PIECES_SIMPLIFY_M = 0.0

# Raggio massimo servibile del layer fine. Piu' basso di quello degli
# appezzamenti perche' il livello e' 1,54x i poligoni e 2,40x i vertici.
AGREA_PIECES_MAX_RADIUS_M = 3000

# Tetto sui VERTICI, non sui pezzi: e' il numero di vertici che determina il peso
# della risposta, e il rapporto e' misurato stabile fra 6,0 e 6,6 byte compressi
# per vertice in pianura come in collina. 30.000 vertici sono quindi circa 195 kB,
# un tetto uniforme dove il conteggio dei pezzi non lo sarebbe: a 3 km di raggio la
# pianura ferrarese ha 2.442 pezzi per 53.098 vertici, Brisighella 2.186 pezzi per
# 188.238, perche' i bordi di collina seguono il terreno.
# Si tengono i pezzi piu' GRANDI: a vista larga i piccoli non sono cliccabili
# comunque, e la soglia effettivamente applicata viene dichiarata nella risposta.
AGREA_PIECES_VERTEX_BUDGET = 30_000

# Decimali delle coordinate nella risposta (non nel file, che resta a precisione
# piena). 7 decimali sono 1,1 cm: due ordini di grandezza sotto i 4 m di
# accuratezza del datum, e sopra il lato piu' corto presente nel dato (7,9 cm),
# quindi nessun vertice collassa e i bordi condivisi restano condivisi — che e' la
# proprieta' su cui si regge l'unione dei pezzi. Misurato: dimezza il payload
# (336 -> 91 kB a 1,5 km) al costo di 22-91 ms di calcolo.
AGREA_PIECES_COORD_DECIMALS = 7
