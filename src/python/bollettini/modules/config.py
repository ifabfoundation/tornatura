"""
Configurazione centralizzata multi-regione per RAG Colture.

Contiene:
- Dizionario regioni (aree, colture, URL)
- Dizionario colture completo (unione di tutte le regioni)
"""

# ============= REGIONI =============
REGIONI = {
    "emilia_romagna": {
        "nome": "Emilia-Romagna",
        "downloader_class": "EmiliaRomagnaDownloader",
        "aree": {
            "Bologna-Ferrara": "bologna-e-ferrara",
            "Forli-Cesena-Ravenna-Rimini": "forli-cesena-ravenna-rimini",
            "Modena-Reggio-Emilia": "modena-reggio-emilia",
            "Parma-Piacenza": "parma-piacenza",
        },
        "colture": ["VITE", "PERO", "PESCO", "MAIS", "BARBABIETOLA"],
    },
    "campania": {
        "nome": "Campania",
        "downloader_class": "CampaniaDownloader",
        "base_url": "https://agricoltura.regione.campania.it/difesa/bollettini",
        # Bollettini provinciali (sito ristrutturato 2026): 5 province
        # Pagina indice: bollettini_2026.html -> bollettini_2026/{slug}_2026.html
        # PDF: bollettini_2026/pdf/{slug}-DD-MM.pdf
        "aree": {
            "Avellino": "AV",
            "Benevento": "BN",
            "Caserta": "CE",
            "Napoli": "NA",
            "Salerno": "SA",
        },
        # 18 colture identificate dai PDF provinciali (sample analysis maggio 2026).
        # NETTARINE non e' separata: matchata da PESCO (sezioni includono "PESCO E NETTARINE").
        "colture": [
            "VITE", "OLIVO", "PESCO", "AGRUMI", "ACTINIDIA",
            "NOCCIOLO", "NOCE", "CIPOLLA", "POMODORO", "FRAGOLA",
            "CASTAGNO", "CILIEGIO", "MELO", "PERO", "PATATA",
            "SUSINO", "ALBICOCCO",
        ],
    },
}

# ============= COLTURE (unione di tutte le regioni) =============
#
# Nota sulle sezioni Campania:
# I PDF Campania hanno formati intestazione inconsistenti:
#   - "## COLTURA: PESCO"      (sele)
#   - "## COLTURA" + "## PESCO" su righe separate (vairano)
#   - "COLTURA: OLIVO" senza ## (sele)
#   - "COLTURA NOCCIOLO"       (sessa, senza colon)
#   - "PESCO" come testo sotto "## Stato fitosanitario" (sessa)
#   - "| COLTURA | VITE |" dentro tabelle (sessa)
#
# Il matching avviene su section_title (testo dell'header markdown).
# Le "sezioni" nel dizionario devono coprire tutte le varianti.
# Il fallback keyword cattura i casi residui.
#
COLTURE = {
    # === Emilia-Romagna ===
    "VITE": {
        "nome": "Vite",
        "sezioni": ["VITE", "Vite", "VITICOLTURA"],
        "keywords": [
            "vite", "vigneto", "uva", "vitigno",
            "escoriosi", "mal dell'esca", "peronospora della vite",
            "flavescenza dorata",
        ],
    },
    "PERO": {
        "nome": "Pero",
        "sezioni": [
            "PERO", "Pero",
            "COLTURA PERO", "COLTURA Pero", "COLTURA: PERO", "COLTURAPero",
        ],
        "keywords": [
            "pero", "pera", "pereto", "pomacee",
            "psilla del pero", "tentredine",
            "ticchiolatura del pero", "spilocaea pyri", "venturia pirina",
        ],
    },
    "PESCO": {
        "nome": "Pesco",
        "sezioni": [
            "PESCO", "Pesco", "PESCO E NETTARINE",
            "COLTURA: PESCO", "COLTURA:PESCO",
            "COLTURA PESCO", "COLTURA Pesco", "COLTURAPesco",
        ],
        "keywords": [
            "pesco", "pesca", "pescheto", "nettarina", "nettarine",
            "bolla del pesco", "taphrina deformans",
            "monilia", "fusicoccum amygdali",
            "cydia molesta", "anarsia lineatella", "capnode",
            "moniliosi dei fruttiferi",
        ],
    },
    "MAIS": {
        "nome": "Mais",
        "sezioni": ["MAIS", "Mais", "GRANOTURCO"],
        "keywords": ["mais", "granoturco", "granturco", "piralide"],
    },
    "BARBABIETOLA": {
        "nome": "Barbabietola",
        "sezioni": ["BARBABIETOLA", "Barbabietola", "BIETOLA"],
        "keywords": ["barbabietola", "bietola", "bieticoltura"],
    },
    # === Campania (confermati da PDF reali marzo 2026) ===
    "OLIVO": {
        "nome": "Olivo",
        "sezioni": [
            "OLIVO", "Olivo", "OLIVICOLTURA",
            "COLTURA: OLIVO", "COLTURA:OLIVO",
            "COLTURA OLIVO", "COLTURA Olivo", "COLTURAOlivo", "COLTURAOlivO",
        ],
        "keywords": [
            "olivo", "oliva", "oliveto", "olivicola",
            "rogna dell'olivo", "occhio di pavone", "spilocaea oleagina",
            "xylella fastidiosa", "lebbra", "cercosporiosi",
            "tignola dell'olivo", "prays oleae", "mosca dell'olivo",
            "bactrocera oleae",
        ],
    },
    "ACTINIDIA": {
        "nome": "Actinidia",
        "sezioni": [
            "ACTINIDIA", "Actinidia",
            "COLTURA:ACTINIDIA", "COLTURA: ACTINIDIA",
            "COLTURA ACTINIDIA", "COLTURAACTINIDIA",
        ],
        "keywords": [
            "actinidia", "kiwi",
            "cancro batterico", "pseudomonas syringae pv. actinidiae",
            "cocciniglia bianca",
            "metcalfa pruinosa", "psa",
        ],
    },
    "MELO": {
        "nome": "Melo",
        "sezioni": [
            "MELO", "Melo",
            "COLTURA MELO", "COLTURA: MELO",
            "COLTURA Melo", "COLTURAMelo",
        ],
        "keywords": [
            "melo", "mela", "meleto", "annurca",
            "ticchiolatura del melo", "venturia inequalis",
            "cancri e disseccamenti rameali",
            "podosphaera leucotricha", "oidium farinosum",
            "afide grigio", "fillominatori",
        ],
    },
    "CASTAGNO": {
        "nome": "Castagno",
        "sezioni": [
            "CASTAGNO", "Castagno",
            "COLTURA CASTAGNO", "COLTURA: CASTAGNO", "COLTURACASTAGNO",
        ],
        "keywords": [
            "castagno", "castagna", "castagneto",
            "cinipide galligeno", "dryocosmus kuriphilus",
            "mal dell'inchiostro", "cancro della corteccia",
            "cancro del castagno",
        ],
    },
    "CILIEGIO": {
        "nome": "Ciliegio",
        "sezioni": [
            "CILIEGIO", "Ciliegio",
            "COLTURA: CILIEGIO", "COLTURA CILIEGIO", "COLTURACILIEGIO",
        ],
        "keywords": [
            "ciliegio", "ciliegia",
            "aromia bungii", "monilia laxa",
            "moniliosi del ciliegio",
        ],
    },
    "SUSINO": {
        "nome": "Susino",
        "sezioni": [
            "SUSINO", "Susino",
            "COLTURA SUSINO", "COLTURA: SUSINO", "COLTURASUSINO",
        ],
        "keywords": [
            "susino", "susina", "prugna",
            "cancro batterico delle drupacee",
            "tentredine del susino",
        ],
    },
    "NOCCIOLO": {
        "nome": "Nocciolo",
        "sezioni": [
            "NOCCIOLO", "Nocciolo", "CORILICOLTURA",
            "COLTURA NOCCIOLO", "COLTURA: NOCCIOLO", "COLTURANOCCIOLO",
        ],
        "keywords": [
            "nocciolo", "nocciola", "corilicolo",
            "eriofide del nocciolo", "phytocoptella avellanae",
            "mal dello stacco", "cytospora corylicola",
            "tonda di giffoni", "san giovanni",
            "balanino", "curculio nucum",
        ],
    },
    "AGRUMI": {
        "nome": "Agrumi",
        "sezioni": [
            "AGRUMI", "Agrumi",
            "COLTURA: AGRUMI", "COLTURA AGRUMI", "COLTURAAGRUMI",
        ],
        "keywords": [
            "agrumi", "arancio", "limone", "mandarino",
            "tristeza", "ctv",
            "tignola della zagara", "prays citri",
            "gommosi del colletto", "marciume radicale",
        ],
    },
    "POMODORO": {
        "nome": "Pomodoro",
        "sezioni": [
            "POMODORO", "Pomodoro",
            "COLTURA: POMODORO", "COLTURA POMODORO", "COLTURAPOMODORO",
        ],
        "keywords": [
            "pomodoro", "solanacee",
            "tuta absoluta", "phytophthora infestans",
        ],
    },
    # Nuove colture identificate dai PDF provinciali Campania (maggio 2026)
    "NOCE": {
        "nome": "Noce",
        "sezioni": [
            "NOCE", "Noce",
            "COLTURA NOCE", "COLTURA: NOCE", "COLTURANOCE",
        ],
        "keywords": [
            "noce", "noceto",
            "batteriosi del noce", "macchie nere", "necrosi della corteccia",
            "antracnosi", "fersa",
            "xanthomonas arboricola juglandis",
        ],
    },
    "ALBICOCCO": {
        "nome": "Albicocco",
        "sezioni": [
            "ALBICOCCO", "Albicocco",
            "COLTURA ALBICOCCO", "COLTURA: ALBICOCCO", "COLTURAALBICOCCO",
        ],
        "keywords": [
            "albicocco", "albicocca", "albicoccheto",
            "monilia", "moniliosi delle drupacee",
            "batteriosi delle drupacee",
        ],
    },
    "CIPOLLA": {
        "nome": "Cipolla",
        "sezioni": [
            "CIPOLLA", "Cipolla",
            "COLTURA CIPOLLA", "COLTURA: CIPOLLA", "COLTURACIPOLLA",
        ],
        "keywords": [
            "cipolla", "cipolle",
            "peronospora della cipolla", "peronospora destructor",
            "tripidi della cipolla", "thrips tabaci",
        ],
    },
    "FRAGOLA": {
        "nome": "Fragola",
        "sezioni": [
            "FRAGOLA", "Fragola",
            "COLTURA FRAGOLA", "COLTURA: FRAGOLA", "COLTURAFRAGOLA",
        ],
        "keywords": [
            "fragola", "fragole", "fragoleto",
            "muffa grigia", "botrytis cinerea",
            "antracnosi della fragola", "colletotrichum",
            "oidio della fragola",
        ],
    },
    "PATATA": {
        "nome": "Patata",
        "sezioni": [
            "PATATA", "Patata",
            "COLTURA PATATA", "COLTURA: PATATA", "COLTURAPATATA",
        ],
        "keywords": [
            "patata", "patate", "tubero",
            "rizottoniosi della patata", "rhizoctonia solani",
            "peronospora della patata", "phytophthora infestans",
            "tignola della patata", "phthorimaea operculella",
            "tuta absoluta",
        ],
    },
}


def get_colture_per_regione(regione_id: str) -> dict:
    """Ritorna solo le colture configurate per una specifica regione."""
    regione = REGIONI.get(regione_id)
    if not regione:
        return {}
    return {k: v for k, v in COLTURE.items() if k in regione["colture"]}


def get_area_display_name(slug: str) -> str:
    """
    Converte uno slug area nel nome completo per la visualizzazione.

    Es: "sele" -> "Piana del Sele", "bologna-e-ferrara" -> "Bologna-Ferrara"
    """
    # Cerca in tutte le regioni
    for regione in REGIONI.values():
        for name, area_slug in regione["aree"].items():
            if area_slug == slug:
                return name
    # Fallback: capitalizza lo slug
    return slug.replace('_', ' ').replace('-', ' ').title()
