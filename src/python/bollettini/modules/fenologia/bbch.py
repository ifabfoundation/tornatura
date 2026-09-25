"""Traduce ogni dicitura di fase dei bollettini in un intervallo di codici BBCH, per coltura.

Fonte dei codici: Meier U. (ed.) 2001, *Growth stages of mono- and dicotyledonous plants.
BBCH Monograph*, 2nd ed., Federal Biological Research Centre for Agriculture and Forestry
(BBA). Sezioni usate (testo in `esperimenti/cimice_landscape/fenologia/fonti/bbch/`): scala generale (Hack et al. 1992), pomacee e
drupacee (Meier et al. 1994), vite (Lorenz et al. 1994), olivo (Sanz-Cortes et al. 2002 nella
monografia), soia (Munger et al. 1997), mais (Lancashire et al. 1991), solanacee da frutto
(Feller et al. 1995), girasole. Actinidia, kaki e noce non hanno una scala propria nella
monografia: si usa la scala generale, che ha gli stessi stadi principali.

METODO, dichiarato: nella dicitura si cercano le parole chiave della tabella del gruppo della
coltura, dalla piu' lunga alla piu' corta, senza sovrapposizioni; l'intervallo della
dicitura e' [minimo dei minimi, massimo dei massimi] delle parole trovate. "da X a Y",
"X – Y" e "X; Y (cv gialle)" producono cosi' l'intervallo che copre entrambe. Le parole
che nella monografia non hanno un codice esplicito (es. "indurimento nocciolo" nelle
drupacee, "chiusura interfila" nella soia) portano la nota del perche' di quel codice.

Il dizionario e' generico: dice in che stadio e' la coltura, non se quello stadio conta per un
organismo. Le finestre di suscettibilita' stanno con l'organismo, nel servizio landscape
(`data/pests/<codice>/meta.json`).

Verifica (25/09/2026): 630 diciture delle colture ospiti della cimice tradotte alla cieca da due
lettori sulla monografia e, dove non concordavano, da tre arbitri; tabella di controllo in
`attese/dizionario_fasi_2026.csv`, verifica con `python -m bollettini.modules.fenologia.verifica`.
"""

from __future__ import annotations

import re

# ----------------------------------------------------------------------------------------
# Parole chiave -> (bbch_min, bbch_max, riferimento). Le tabelle sono per gruppo di colture.
# ----------------------------------------------------------------------------------------

# Arboree da frutto: pomacee (pero, melo) e drupacee (pesco, albicocco, susino, ciliegio),
# piu' actinidia, kaki e noce sulla scala generale. Le fasi a gemma usano la serie delle
# gemme a fiore (5x) come i bollettini ("mazzetti", "bottoni").
ARBOREE = [
    ("gemma ferma", 0, 0, "00 Dormancy"),
    ("gemme ferme", 0, 0, "00 Dormancy"),
    ("riposo vegetativo", 0, 0, "00 Dormancy"),
    ("inizio rigonfiamento", 1, 1, "01 Beginning of bud swelling"),
    ("fine rigonfiamento", 3, 3, "03 End of bud swelling"),
    ("rigonfiamento", 1, 3, "01-03 bud swelling"),
    ("gemma gonfia", 1, 3, "01-03 bud swelling"),
    ("gemme gonfie", 1, 3, "01-03 bud swelling"),
    ("ingrossamento gemm", 1, 3, "01-03 bud swelling"),
    ("gemma ingrossata", 1, 3, "01-03 bud swelling"),
    (
        "gemma cotonosa",
        3,
        5,
        "fra 03 End of bud swelling e 07 bud break (stadio lanoso; non codificato nella scala generale)",
    ),
    ("inizio rottura gemm", 7, 7, "07 Beginning of bud break"),
    ("inizio apertura gemm", 7, 7, "07 Beginning of bud break"),
    ("rottura gemm", 7, 9, "07-09 bud break, green leaf tips"),
    ("apertura gemm", 7, 9, "07-09 bud break, green leaf tips"),
    ("punte verdi", 7, 9, "07-09 green leaf tips (pomacee 07/09, drupacee 09)"),
    ("punta verde", 7, 9, "07-09 green leaf tips"),
    ("inizio germogliamento", 7, 7, "07 Beginning of bud break (scala generale)"),
    ("germogliamento", 7, 9, "07-09 bud break (scala generale)"),
    (
        "orecchiette di topo",
        54,
        54,
        "54 Mouse-ear stage (pomacee; equivale a 10 della serie fogliare)",
    ),
    ("5 – 7 cm", 31, 33, "31-33 shoots (germogli di 5-7 cm)"),
    ("comparsa dei mazzetti fiorali", 55, 55, "55 Flower buds visible (still closed)"),
    ("comparsa mazzetti", 55, 55, "55 Flower buds visible (still closed)"),
    ("mazzetti affioranti", 55, 55, "55 Flower buds visible (still closed)"),
    ("mazzetti fiorali", 55, 55, "55 Flower buds visible (still closed)"),
    ("mazzetti divaricati", 56, 56, "56 Green bud stage: single flowers separating"),
    ("bottone verde", 56, 56, "56 Flower pedicel elongating; sepals closed (drupacee)"),
    ("bottoni verdi", 56, 56, "56 Flower pedicel elongating; sepals closed (drupacee)"),
    ("inizio bottone rosso", 57, 57, "57 Sepals open: petal tips visible"),
    (
        "bottone rosa",
        57,
        57,
        "57 Pink bud stage (pomacee) / sepals open, petal tips visible (drupacee)",
    ),
    ("bottoni rosa", 57, 57, "57 Pink bud stage"),
    ("bottone rosso", 57, 57, "57 Sepals open: petal tips visible (albicocco)"),
    (
        "bottone bianco",
        57,
        59,
        "57-59 petal tips visible to hollow ball (ciliegio, susino, actinidia)",
    ),
    ("bottoni bianchi", 57, 59, "57-59 petal tips visible to hollow ball"),
    (
        "comparsa bottoni fiorali",
        51,
        55,
        "51-55 inflorescence buds swelling to flower buds visible (scala generale)",
    ),
    ("bottoni fiorali", 55, 59, "55-59 flower buds visible to hollow ball"),
    ("bottone fiorale", 55, 59, "55-59 flower buds visible to hollow ball"),
    (
        "comparsa abbozzi fiorali",
        51,
        55,
        "51-55 inflorescence buds swelling (scala generale)",
    ),
    (
        "presenza abbozzi fiorali",
        51,
        55,
        "51-55 inflorescence buds swelling (scala generale)",
    ),
    ("abbozzi fiorali", 51, 55, "51-55 inflorescence buds swelling (scala generale)"),
    (
        "emissione degli amenti",
        51,
        59,
        "51-59 inflorescence emergence (amenti del noce, scala generale)",
    ),
    (
        "emissione amenti",
        51,
        59,
        "51-59 inflorescence emergence (amenti del noce, scala generale)",
    ),
    (
        "inizio caduta petali",
        65,
        67,
        "65 Full flowering, first petals falling - 67 flowers fading",
    ),
    ("completa caduta petali", 69, 69, "69 End of flowering: all petals fallen"),
    (
        "caduta petali",
        67,
        69,
        "67 Flowers fading: majority of petals fallen - 69 all petals fallen",
    ),
    ("inizio fioritura", 60, 61, "60 First flowers open - 61 Beginning of flowering"),
    (
        "inizia fioritura",
        60,
        61,
        "60-61 (refuso del bollettino per 'inizio fioritura')",
    ),
    ("piena fioritura", 65, 65, "65 Full flowering"),
    ("fine fioritura", 67, 69, "67-69 flowers fading to end of flowering"),
    ("fioritura", 60, 69, "60-69 Flowering"),
    (
        "inizio allegagione",
        69,
        71,
        "69 End of flowering - 71 fruit fall after flowering",
    ),
    ("fine allegagione", 71, 72, "71-72"),
    (
        "allegagione",
        71,
        71,
        "71 Fruit size up to 10 mm / ovary growing; fruit fall after flowering",
    ),
    (
        "inizio scamiciatura",
        72,
        72,
        "72 Green ovary surrounded by dying sepal crown (drupacee)",
    ),
    (
        "scamiciatura",
        72,
        73,
        "72 Green ovary surrounded by dying sepal crown - 73 second fruit fall (drupacee)",
    ),
    (
        "frutto noce",
        72,
        74,
        "72 Fruit size up to 20 mm - 74 fruit diameter up to 40 mm (pomacee)",
    ),
    (
        "inizio indurimento nocciolo",
        73,
        75,
        "73-75 (drupacee: l'indurimento del nocciolo non ha un codice; avviene a meta' dello stadio 7)",
    ),
    (
        "indurimento nocciolo",
        75,
        77,
        "75-77 fruit about half to 70% final size (drupacee: nessun codice esplicito per l'indurimento)",
    ),
    (
        "indurimento guscio",
        75,
        79,
        "75-79 (noce: nessun codice esplicito; meta'-fine accrescimento del frutto)",
    ),
    ("inizio ingrossamento frutt", 71, 72, "71-72 inizio dello stadio 7"),
    ("inizio accrescimento frutt", 71, 72, "71-72 inizio dello stadio 7"),
    ("inizio sviluppo frutt", 71, 72, "71-72 inizio dello stadio 7"),
    ("ingrossamento frutt", 71, 79, "71-79 Development of fruit"),
    ("accrescimento frutt", 71, 79, "71-79 Development of fruit"),
    ("sviluppo frutt", 71, 79, "71-79 Development of fruit"),
    ("inizio invaiatura", 81, 81, "81 Beginning of fruit colouring (ciliegio)"),
    (
        "invaiatura",
        81,
        85,
        "81 Beginning of fruit colouring - 85 colouring advanced (ciliegio)",
    ),
    ("inizio maturazione", 81, 81, "81 Beginning of ripening / fruit colouring"),
    (
        "maturazione gheriglio",
        81,
        87,
        "81-87 ripening (noce: maturazione del gheriglio)",
    ),
    ("maturazione", 81, 89, "81-89 Ripening of fruit"),
    ("termine raccolta", 89, 89, "89 Fruit ripe for consumption (raccolta conclusa)"),
    ("raccolta", 87, 89, "87 Fruit ripe for picking - 89"),
    ("post – raccolta", 91, 93, "91 Shoot growth completed; foliage still green - 93"),
    ("post raccolta", 91, 93, "91-93"),
    (
        "accrescimento",
        71,
        79,
        "71-79 (dicitura abbreviata 'accrescimento' = accrescimento dei frutti)",
    ),
    (
        "ingrossamento",
        71,
        79,
        "71-79 (dicitura abbreviata 'ingrossamento' = ingrossamento dei frutti)",
    ),
]

OLIVO = [
    ("riposo vegetativo", 0, 0, "00 Foliar buds closed (dormancy)"),
    (
        "inizio ripresa vegetativa",
        1,
        3,
        "01-03 foliar buds start to swell and lengthen",
    ),
    ("ripresa vegetativa", 1, 9, "01-09 bud development"),
    ("accrescimento germogli", 31, 37, "31-37 shoots reach 10-70% of final size"),
    (
        "inizio mignolatura",
        50,
        52,
        "50-52 inflorescence buds closed to opening (mignole)",
    ),
    ("mignolatura", 50, 57, "50-57 inflorescence development (mignole)"),
    ("inizi fioritura", 60, 61, "60-61 (refuso del bollettino per 'inizio fioritura')"),
    ("inizio fioritura", 60, 61, "60 First flowers open - 61 Beginning of flowering"),
    (
        "fine fioritura",
        68,
        69,
        "68 Majority of petals fallen - 69 End of flowering, fruit set",
    ),
    ("fioritura", 60, 69, "60-69 Flowering"),
    (
        "allegagione",
        69,
        69,
        "69 End of flowering, fruit set (verificato il 25/09/2026: prima era 69-71)",
    ),
    ("inizio accrescimento frutt", 71, 71, "71 Fruit size about 10% of final size"),
    (
        "inizio indurimento nocciolo",
        75,
        75,
        "75 Fruit about 50%; stone starts to lignificate",
    ),
    ("indurimento nocciolo", 75, 75, "75 Fruit about 50%; stone starts to lignificate"),
    ("accrescimento drupe", 71, 79, "71-79 fruit development"),
    ("accrescimento frutt", 71, 79, "71-79 fruit development"),
    ("invaiatura", 81, 85, "81 Beginning of fruit colouring - 85"),
    ("maturazione", 80, 89, "80-89 fruit maturity"),
    ("raccolta", 89, 89, "89 Harvest maturity"),
]

VITE = [
    ("gemma ferma", 0, 0, "00 Dormancy"),
    ("riposo vegetativo", 0, 0, "00 Dormancy"),
    ("inizio rigonfiamento", 1, 1, "01 Beginning of bud swelling"),
    ("rigonfiamento", 1, 3, "01-03 bud swelling"),
    ("gemma cotonosa", 5, 5, "05 Wool stage"),
    (
        "pianto",
        0,
        1,
        "00-01 (pianto: fuoriuscita di linfa prima del rigonfiamento; nessun codice esplicito)",
    ),
    ("inizio apertura gemm", 7, 7, "07 Beginning of bud burst"),
    ("apertura gemm", 7, 8, "07-08 bud burst"),
    ("rottura gemm", 7, 8, "07-08 bud burst"),
    ("inizio germogliamento", 7, 7, "07 Beginning of bud burst"),
    ("germogliamento", 7, 8, "07-08 bud burst"),
    ("punte verdi", 7, 8, "07-08 green shoot tips"),
    ("prima foglia", 11, 11, "11 First leaf unfolded"),
    ("foglie distese", 11, 19, "11-19 leaves unfolded"),
    ("foglia distesa", 11, 11, "11 First leaf unfolded"),
    ("prime foglie", 11, 12, "11-12 first leaves unfolded"),
    ("prime foglie distese", 11, 12, "11-12 first leaves unfolded"),
    ("sviluppo foglie", 11, 19, "11-19 leaves unfolded"),
    ("prima comparsa grappolini", 53, 53, "53 Inflorescences clearly visible"),
    ("comparsa grappolini", 53, 53, "53 Inflorescences clearly visible"),
    ("grappolini visibili", 53, 53, "53 Inflorescences clearly visible"),
    ("grappoli visibili", 53, 53, "53 Inflorescences clearly visible"),
    (
        "grappolini separati",
        55,
        55,
        "55 Inflorescences swelling, flowers closely pressed together",
    ),
    (
        "grappoli separati",
        55,
        55,
        "55 Inflorescences swelling, flowers closely pressed together",
    ),
    ("racimoli separati", 55, 55, "55 Inflorescences swelling (racimoli)"),
    ("grappolini", 53, 55, "53-55 inflorescences visible/swelling"),
    (
        "grappoli in distensione",
        55,
        55,
        "55 Inflorescences swelling, flowers closely pressed together",
    ),
    ("distensione grappoli", 55, 55, "55 Inflorescences swelling"),
    (
        "bottoni fiorali separati",
        57,
        57,
        "57 Inflorescences fully developed; flowers separating",
    ),
    ("bottoni separati", 57, 57, "57 flowers separating"),
    ("bottoni fiorali", 57, 57, "57 flowers separating"),
    ("pre – fioritura", 57, 60, "57-60"),
    ("prefioritura", 57, 60, "57-60"),
    (
        "inizio fioritura",
        60,
        61,
        "60 First flowerhoods detached - 61 Beginning of flowering",
    ),
    ("piena fioritura", 65, 65, "65 Full flowering"),
    ("fine fioritura", 68, 69, "68-69 end of flowering"),
    ("fioritura", 60, 69, "60-69 Flowering"),
    ("allegagione", 71, 71, "71 Fruit set"),
    ("mignolatura", 73, 73, "73 Berries groat-sized (acino 'grano di pepe')"),
    ("grano di pepe", 73, 73, "73 Berries groat-sized"),
    ("acino pisello", 75, 75, "75 Berries pea-sized"),
    ("pre – chiusura", 77, 77, "77 Berries beginning to touch"),
    ("pre – chiusura grappolo", 77, 77, "77 Berries beginning to touch"),
    ("pre chiusura grappolo", 77, 77, "77 Berries beginning to touch"),
    ("prechiusura", 77, 77, "77 Berries beginning to touch"),
    ("inizio chiusura grappolo", 77, 77, "77 Berries beginning to touch"),
    (
        "chiusura grappolo",
        77,
        79,
        "77 Berries beginning to touch - 79 majority touching",
    ),
    ("accrescimento acini", 73, 77, "73-77 berry growth"),
    ("ingrossamento acini", 73, 77, "73-77 berry growth"),
    (
        "sviluppo acini",
        73,
        75,
        "73 Berries groat-sized - 75 pea-sized: fra allegagione (71) e pre-chiusura (77) nella progressione dei bollettini; deciso il 25/09/2026 da tre arbitri",
    ),
    (
        "sviluppo degli acini",
        73,
        75,
        "73-75: fra allegagione (71) e pre-chiusura (77) nella progressione dei bollettini; deciso il 25/09/2026 da tre arbitri",
    ),
    ("acino dimensione pisello", 75, 75, "75 Berries pea-sized"),
    ("inizio invaiatura", 81, 81, "81 Beginning of ripening"),
    ("invaiatura", 81, 83, "81 Beginning of ripening - 83 berries developing colour"),
    ("inizio maturazione", 85, 85, "85 Softening of berries"),
    ("maturazione", 85, 89, "85 Softening of berries - 89 ripe for harvest"),
    ("vendemmia", 89, 89, "89 Berries ripe for harvest"),
    ("raccolta", 89, 89, "89 Berries ripe for harvest"),
    ("post – raccolta", 91, 91, "91 After harvest"),
    ("post raccolta", 91, 91, "91 After harvest"),
    ("post vendemmia", 91, 91, "91 After harvest"),
    ("caduta foglie", 93, 97, "93-97 leaf fall"),
]

ERBACEE_COMUNI = [
    ("pre – semina", 0, 0, "00 Dry seed (coltura non ancora seminata)"),
    ("presemina", 0, 0, "00 Dry seed (coltura non ancora seminata)"),
    ("pre semina", 0, 0, "00 Dry seed (coltura non ancora seminata)"),
    ("pre – esemina", 0, 0, "00 (refuso del bollettino per 'pre-semina')"),
    ("semina", 0, 0, "00 Dry seed / sowing"),
    ("pre – emergenza", 0, 8, "00-08 germination before emergence"),
    ("pre emergenza", 0, 8, "00-08 germination before emergence"),
    ("preemergenza", 0, 8, "00-08 germination before emergence"),
    ("emergenza", 9, 9, "09 Emergence"),
    ("cotiledoni", 10, 10, "10 Cotyledons completely unfolded"),
    ("sviluppo vegetativo", 10, 49, "10-49 vegetative development"),
]

SOIA = ERBACEE_COMUNI + [
    (
        "prime foglie vere",
        11,
        11,
        "11 First pair of true leaves unfolded (unifoliolate)",
    ),
    ("prima foglia vera", 11, 11, "11 First pair of true leaves unfolded"),
    (
        "prima foglia trifogliata",
        12,
        12,
        "12 Trifoliolate leaf on the 2nd node unfolded",
    ),
    (
        "seconda foglia trifogliata",
        13,
        13,
        "13 Trifoliolate leaf on the 3rd node unfolded",
    ),
    ("prime foglie", 11, 12, "11-12"),
    (
        "chiusura interfila",
        21,
        59,
        "non codificato BBCH: chiusura della fila, fra sviluppo vegetativo (2x) e bottoni fiorali (5x)",
    ),
    ("inizio fioritura", 60, 61, "60 First flowers opened - 61 Beginning of flowering"),
    ("fioritura", 60, 69, "60-69 Flowering"),
    (
        "formazione baccelli",
        69,
        75,
        "69 End of flowering: first pods visible - 75 about 50% of pods at final length",
    ),
    (
        "ingrossamento semi",
        75,
        79,
        "75-79 pods reaching final length, seeds filling (R5-R6)",
    ),
    (
        "riempimento semi",
        75,
        79,
        "75-79 pods reaching final length, seeds filling (R5-R6)",
    ),
    ("maturazione", 80, 89, "80-89 pods ripe, beans dry and hard"),
    ("raccolta", 89, 99, "89 Full maturity - 99 harvested product"),
]

MAIS = ERBACEE_COMUNI + [
    ("levata", 30, 39, "30-39 Stem elongation"),
    ("spigatura", 51, 59, "51-59 Tassel emergence (dicitura 'spigatura')"),
    ("emissione pennacchio", 51, 59, "51-59 Tassel emergence"),
    (
        "comparsa sete",
        63,
        65,
        "63-65 (sete: la scala del mais codifica la fioritura maschile; l'emissione delle sete coincide con 63-65)",
    ),
    ("senescenza sete", 67, 69, "67-69 End of flowering: stigmata completely dry"),
    ("fioritura", 61, 69, "61-69 Flowering"),
    ("maturazione lattea", 73, 75, "73 Early milk - 75 kernels milky"),
    ("maturazione cerosa", 83, 85, "83 Early dough - 85 Dough stage"),
    ("cerosa", 83, 85, "83-85 dough stage (in 'maturazione lattea – cerosa')"),
    ("maturazione fisiologica", 87, 87, "87 Physiological maturity"),
    ("raccolta", 89, 99, "89 Fully ripe - 99 harvested product"),
    ("trebbiatura", 89, 99, "89-99"),
]

SOLANACEE = ERBACEE_COMUNI + [
    (
        "pre – trapianto",
        0,
        13,
        "00-13 piantine in vivaio (coltura non ancora in campo)",
    ),
    ("pre trapianto", 0, 13, "00-13 piantine in vivaio (coltura non ancora in campo)"),
    ("termine trapianti", 13, 19, "13-19 leaves on main shoot (fine dei trapianti)"),
    ("termine trapianto", 13, 19, "13-19 leaves on main shoot (fine dei trapianti)"),
    ("trapianto", 13, 15, "13-15 young plants set out"),
    ("sviluppo fogliare", 10, 19, "10-19 leaves on main shoot"),
    ("fioritura 1° palco", 61, 61, "61 First inflorescence: first flower open"),
    ("fioritura primo palco", 61, 61, "61 First inflorescence: first flower open"),
    ("inizio fioritura", 60, 61, "60-61"),
    ("fioritura", 61, 69, "61-69 flowering"),
    (
        "allegagione 4° palco",
        74,
        74,
        "74 4th fruit cluster: first fruit has reached typical size",
    ),
    (
        "allegagione",
        71,
        71,
        "71 First fruit cluster: first fruit has reached typical size",
    ),
    (
        "invaiatura primo palco",
        81,
        81,
        "81 10% of fruits show typical fully ripe colour",
    ),
    ("invaiatura", 81, 83, "81-83 fruits colouring"),
    ("accrescimento frutt", 71, 79, "71-79 fruit development"),
    ("ingrossamento frutt", 71, 79, "71-79 fruit development"),
    (
        "accrescimento",
        71,
        79,
        "71-79 (dicitura abbreviata 'accrescimento' = dei frutti)",
    ),
    ("inizio maturazione", 81, 81, "81"),
    ("maturazione", 81, 89, "81-89 ripening"),
    ("raccolta", 89, 99, "89 Fully ripe - 99"),
]

GIRASOLE = ERBACEE_COMUNI + [
    ("levata", 30, 39, "30-39 Stem elongation"),
    ("allungamento", 30, 39, "30-39 Stem elongation"),
    ("prime foglie", 10, 12, "10-12 cotyledons to first pair of leaves"),
    ("bottone fiorale", 51, 59, "51-59 Inflorescence emergence"),
    ("comparsa capolino", 51, 53, "51-53 Inflorescence just visible"),
    ("capolino", 51, 59, "51-59 Inflorescence emergence"),
    ("inizio fioritura", 61, 61, "61 Beginning of flowering"),
    ("fioritura", 61, 69, "61-69 Flowering"),
    ("riempimento acheni", 71, 79, "71-79 seeds developing"),
    ("formazione semi", 71, 79, "71-79 seeds developing"),
    ("maturazione", 80, 89, "80-89 ripening"),
    ("raccolta", 89, 99, "89-99"),
]

FAGIOLO = ERBACEE_COMUNI + [
    ("inizio fioritura", 60, 61, "60 First flowers open - 61"),
    ("fioritura", 60, 69, "60-69 Flowering"),
    ("formazione baccelli", 69, 75, "69 End of flowering: first pods visible - 75"),
    ("ingrossamento baccelli", 71, 79, "71-79 pods reaching typical length"),
    ("maturazione", 81, 89, "81-89 pods ripe"),
    ("raccolta", 79, 89, "79 pods: beans visible (fagiolino raccolto verde) - 89"),
]


def _con(base, sostituzioni):
    """La tabella `base` con alcune parole chiave ridefinite o aggiunte (per gruppo di colture)."""
    nuove = {k: (k, lo, hi, rif) for k, lo, hi, rif in sostituzioni}
    return [nuove.pop(k, (k, lo, hi, rif)) for k, lo, hi, rif in base] + list(
        nuove.values()
    )


# Pomacee e drupacee: nei bollettini "rigonfiamento", "rottura gemme", "punte verdi" descrivono le
# gemme a fiore, che nella monografia hanno la serie 5x (verificato il 25/09/2026 con due letture
# alla cieca: 51 Inflorescence buds swelling, 52 End of bud swelling (solo pomacee), 53 Bud burst).
# Le frasi "gemma a legno" del pesco restano sulla serie delle gemme a foglia (drupacee: 01, 03, 09).
_GEMME_A_LEGNO = [
    (
        "rottura gemma a legno",
        3,
        9,
        "03 End of leaf bud swelling: scales separated - 09 Green leaf tips visible (gemme a legno)",
    ),
    ("rottura gemme a legno", 3, 9, "03-09 (gemme a legno)"),
    (
        "inizio rottura gemma a legno",
        3,
        3,
        "03 End of leaf bud swelling: scales separated, light green bud sections visible",
    ),
    ("inizio rottura gemme a legno", 3, 3, "03 (gemme a legno)"),
    (
        "gemma gonfia a inizio rottura gemme a legno",
        1,
        3,
        "01 Beginning of bud swelling (leaf buds) - 03 (gemme a legno)",
    ),
    ("gemma gonfia ad inizio rottura gemme a legno", 1, 3, "01-03 (gemme a legno)"),
]
# Ciliegio (Parma, Piacenza): "da bottone rosa ad apertura gemme" viene fra "rigonfiamento gemme" e
# "da bottone verde a inizio fioritura": l'apertura e' quella delle gemme (53), non dei fiori.
# Deciso il 25/09/2026 da tre arbitri e dalla progressione delle settimane.
POMACEE = _con(
    ARBOREE,
    [
        ("inizio rigonfiamento", 51, 51, "51 Inflorescence buds swelling"),
        ("fine rigonfiamento", 52, 52, "52 End of bud swelling"),
        ("rigonfiamento", 51, 52, "51-52 inflorescence bud swelling"),
        ("gemma gonfia", 51, 52, "51-52 inflorescence bud swelling"),
        ("gemme gonfie", 51, 52, "51-52 inflorescence bud swelling"),
        ("ingrossamento gemm", 51, 52, "51-52 inflorescence bud swelling"),
        ("gemma ingrossata", 51, 52, "51-52 inflorescence bud swelling"),
        (
            "inizio rottura gemm",
            53,
            53,
            "53 Bud burst: green leaf tips enclosing flowers visible",
        ),
        ("inizio apertura gemm", 53, 53, "53 Bud burst"),
        (
            "rottura gemm",
            53,
            53,
            "53 Bud burst: green leaf tips enclosing flowers visible",
        ),
        ("apertura gemm", 53, 53, "53 Bud burst"),
        (
            "punte verdi",
            53,
            53,
            "53 Bud burst: green leaf tips enclosing flowers visible",
        ),
        ("punta verde", 53, 53, "53 Bud burst"),
    ],
)
DRUPACEE = _con(
    ARBOREE,
    [
        ("inizio rigonfiamento", 51, 51, "51 Inflorescence buds swelling"),
        ("fine rigonfiamento", 51, 51, "51 (le drupacee non hanno il 52)"),
        ("rigonfiamento", 51, 51, "51 Inflorescence buds swelling"),
        ("gemma gonfia", 51, 51, "51 Inflorescence buds swelling"),
        ("gemme gonfie", 51, 51, "51 Inflorescence buds swelling"),
        ("ingrossamento gemm", 51, 51, "51 Inflorescence buds swelling"),
        ("gemma ingrossata", 51, 51, "51 Inflorescence buds swelling"),
        (
            "inizio rottura gemm",
            53,
            53,
            "53 Bud burst: scales separated, light green bud sections visible",
        ),
        ("inizio apertura gemm", 53, 53, "53 Bud burst"),
        ("rottura gemm", 53, 53, "53 Bud burst"),
        ("apertura gemm", 53, 53, "53 Bud burst"),
        ("punte verdi", 53, 53, "53 Bud burst"),
        ("punta verde", 53, 53, "53 Bud burst"),
    ]
    + _GEMME_A_LEGNO,
)
# Scala generale (actinidia, kaki, noce): "69 End of flowering: fruit set visible"
GENERALE = _con(
    ARBOREE,
    [
        (
            "allegagione",
            69,
            69,
            "69 End of flowering: fruit set visible (scala generale)",
        ),
        (
            "inizio allegagione",
            69,
            69,
            "69 End of flowering: fruit set visible (scala generale)",
        ),
    ],
)

GRUPPO = {
    "PERO": POMACEE,
    "MELO": POMACEE,
    "PESCO": DRUPACEE,
    "ALBICOCCO": DRUPACEE,
    "CILIEGIO": DRUPACEE,
    "SUSINO": DRUPACEE,
    "SUSINO_EUROPEO": DRUPACEE,
    "SUSINO_CINO_GIAPPONESE": DRUPACEE,
    "ACTINIDIA": GENERALE,
    "KAKI": GENERALE,
    "NOCE": GENERALE,
    "OLIVO": OLIVO,
    "VITE": VITE,
    "SOIA": SOIA,
    "MAIS": MAIS,
    "POMODORO_INDUSTRIA": SOLANACEE,
    "POMODORO": SOLANACEE,
    "POMODORO_MENSA": SOLANACEE,
    "PEPERONE": SOLANACEE,
    "MELANZANA": SOLANACEE,
    "GIRASOLE": GIRASOLE,
    "FAGIOLO": FAGIOLO,
    "FAGIOLINO": FAGIOLO,
}


def normalizza(t: str) -> str:
    t = t.lower().replace("’", "'")
    t = re.sub(r"\s*[-–]\s*", " – ", t)
    t = re.sub(r"(\d)\s*°", r"\1°", t)
    return re.sub(r"\s+", " ", t).strip(" .;:")


RE_FOGLIE = re.compile(
    r"(?<![°\d])(\d{1,2})(?:\s*(?:–|/|a)\s*(\d{1,2}))?\s*°?\s*(foglie|foglia)(\s+trilobat\w*|\s+trifogliat\w*|\s+vere)?"
)
RE_ORD_TRILOBATA = re.compile(r"(\d{1,2})\s*°\s*foglia\s+(?:trilobat|trifogliat)\w*")


def foglie(coltura: str, t: str):
    """'2 – 4 foglie', '6/10 foglie', '3 – 5 foglie trilobate', '6° foglia trilobata'."""
    trovati = []
    for m in RE_ORD_TRILOBATA.finditer(t):
        n = int(m.group(1))
        trovati.append(
            (
                11 + n,
                11 + n,
                f"{11 + n} trifoliolate on node {n + 1} (soia: {n}a foglia trilobata)",
                m.span(),
            )
        )
    for m in RE_FOGLIE.finditer(t):
        if any(a <= m.start() < b for *_, (a, b) in trovati):
            continue
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        trilobate = bool(
            m.group(4) and ("trilob" in m.group(4) or "trifogl" in m.group(4))
        )
        if coltura == "SOIA" and trilobate:
            lo, hi = 11 + a, 11 + b  # n-esima trifogliata = BBCH 11+n
            rif = f"{lo}-{hi} trifoliolate leaves ({a}-{b} foglie trilobate)"
        else:
            lo, hi = 10 + a, min(
                19, 10 + b
            )  # n foglie distese = BBCH 1n (19 = 9 o piu')
            rif = f"{lo}-{hi} leaves unfolded ({a}-{b} foglie)"
        trovati.append((lo, min(hi, 19 if coltura != "SOIA" else 29), rif, m.span()))
    return trovati


ORDINALI = {
    "primo": 1,
    "secondo": 2,
    "terzo": 3,
    "quarto": 4,
    "quinto": 5,
    "sesto": 6,
    "ultimo": 9,
}
RE_PALCO = re.compile(
    r"(fioritura|allegagione|invaiatura)\s+(?:del\s+)?((?:\d{1,2}°?\s*(?:–\s*\d{1,2}°?\s*)?)|primo|secondo|terzo|quarto|quinto|sesto|ultimo)\s*pa(?:l)?co"
)


def palchi(coltura: str, t: str):
    """Solanacee: 'allegagione 3° palco' = 73 (3rd fruit cluster), 'fioritura 2° palco' = 62,
    'allegagione 1° – 4° palco' = 71-74; 'ultimo' = 9 o piu' (x9). L'invaiatura non e' per palco
    nella scala (81-89 = % di frutti colorati): resta 81-83."""
    if coltura not in (
        "POMODORO",
        "POMODORO_INDUSTRIA",
        "POMODORO_MENSA",
        "PEPERONE",
        "MELANZANA",
    ):
        return []
    out = []
    for m in RE_PALCO.finditer(t):
        fase, n = m.group(1), m.group(2).strip()
        nums = [int(x) for x in re.findall(r"\d{1,2}", n)] or [ORDINALI[n]]
        a, b = min(nums), max(nums)
        if fase == "fioritura":
            out.append(
                (
                    60 + a,
                    60 + b,
                    f"{60 + a}-{60 + b} inflorescence {a}-{b}: first flower open",
                    m.span(),
                )
            )
        elif fase == "allegagione":
            out.append(
                (
                    70 + a,
                    70 + b,
                    f"{70 + a}-{70 + b} fruit cluster {a}-{b}: first fruit typical size",
                    m.span(),
                )
            )
        else:
            out.append(
                (81, 83, "81-83 fruits colouring (invaiatura di un palco)", m.span())
            )
    return out


def traduci(coltura: str, fase: str):
    """(bbch_min, bbch_max, riferimenti, residuo) per la dicitura; None se nessuna parola nota."""
    tabella = GRUPPO.get(coltura)
    if tabella is None:
        return None
    t = normalizza(fase)
    occupato = [False] * len(t)
    trovati = []
    for lo, hi, rif, (a, b) in palchi(coltura, t) + foglie(coltura, t):
        trovati.append((lo, hi, rif, t[a:b]))
        for k in range(a, b):
            occupato[k] = True
    for chiave, lo, hi, rif in sorted(tabella, key=lambda x: -len(x[0])):
        k = normalizza(chiave)
        for m in re.finditer(re.escape(k), t):
            a, b = m.span()
            if any(occupato[a:b]):
                continue
            trovati.append((lo, hi, rif, k))
            for i in range(a, b):
                occupato[i] = True
    residuo = "".join(" " if occupato[i] else ch for i, ch in enumerate(t))
    # parole di contorno: desinenze rimaste ("frutt|i"), oggetti gia' impliciti nella parola chiave
    # ("rigonfiamento | gemme", "mazzetti | fiorali", "rottura gemma | a legno") e qualificatori di
    # cultivar. Tutto il resto resta nel residuo e va guardato.
    residuo = re.sub(
        r"\b(da|a|ad|al|alla|e|di|del|della|dei|delle|in|cv|cv\.|varieta'|varietà|le|precoci|"
        r"precocissime|medio|tardive|verdi|gialle|verde|giallo|impianti|produzione|nuovi|vecchi|"
        r"i|o|gemme|gemma|fiorali|fiorale|legno|comparsa|inizio|fine|frutti|frutto)\b",
        " ",
        residuo,
    )
    residuo = re.sub(r"[\s–;:,.()/°]+", " ", residuo).strip()
    if not trovati:
        return None
    return (
        min(x[0] for x in trovati),
        max(x[1] for x in trovati),
        " | ".join(f"{x[3]} -> {x[2]}" for x in trovati),
        residuo,
    )
