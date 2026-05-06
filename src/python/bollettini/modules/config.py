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
        "aree": {
            "Avellino": "AV",
            "Benevento": "BN",
            "Caserta": "CE",
            "Napoli": "NA",
            "Salerno": "SA"
        },
        # Colture confermate da analisi PDF reali (marzo 2026)
        # AGRUMI e POMODORO non presenti nei bollettini invernali, probabilmente estivi
        "colture": [
            "VITE", "OLIVO", "PESCO", "NOCCIOLO",
            "ACTINIDIA", "MELO", "CASTAGNO", "CILIEGIO", "SUSINO",
            "AGRUMI", "POMODORO",
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
        "sezioni": ["PERO", "Pero"],
        "keywords": ["pero", "pera", "pereto", "pomacee"],
    },
    "PESCO": {
        "nome": "Pesco",
        "sezioni": [
            "PESCO", "Pesco", "PESCO E NETTARINE",
            "COLTURA: PESCO", "COLTURA:PESCO",
        ],
        "keywords": [
            "pesco", "pesca", "pescheto", "nettarina", "nettarine",
            "bolla del pesco", "taphrina deformans",
            "monilia", "fusicoccum amygdali",
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
        ],
        "keywords": [
            "olivo", "oliva", "oliveto", "olivicola",
            "rogna dell'olivo", "occhio di pavone", "spilocaea oleagina",
            "xylella fastidiosa", "lebbra", "cercosporiosi",
        ],
    },
    "ACTINIDIA": {
        "nome": "Actinidia",
        "sezioni": [
            "ACTINIDIA", "Actinidia",
            "COLTURA:ACTINIDIA", "COLTURA: ACTINIDIA",
        ],
        "keywords": [
            "actinidia", "kiwi",
            "cancro batterico", "pseudomonas syringae pv. actinidiae",
            "cocciniglia bianca",
        ],
    },
    "MELO": {
        "nome": "Melo",
        "sezioni": [
            "MELO", "Melo",
            "COLTURA MELO", "COLTURA: MELO",
        ],
        "keywords": [
            "melo", "mela", "meleto", "annurca",
            "ticchiolatura del melo", "venturia inequalis",
            "cancri e disseccamenti rameali",
        ],
    },
    "CASTAGNO": {
        "nome": "Castagno",
        "sezioni": [
            "CASTAGNO", "Castagno",
            "COLTURA CASTAGNO", "COLTURA: CASTAGNO",
        ],
        "keywords": [
            "castagno", "castagna", "castagneto",
            "cinipide galligeno", "dryocosmus kuriphilus",
            "mal dell'inchiostro", "cancro della corteccia",
        ],
    },
    "CILIEGIO": {
        "nome": "Ciliegio",
        "sezioni": [
            "CILIEGIO", "Ciliegio",
            "COLTURA: CILIEGIO", "COLTURA CILIEGIO",
        ],
        "keywords": [
            "ciliegio", "ciliegia",
            "aromia bungii",
        ],
    },
    "SUSINO": {
        "nome": "Susino",
        "sezioni": [
            "SUSINO", "Susino",
            "COLTURA SUSINO", "COLTURA: SUSINO",
        ],
        "keywords": [
            "susino", "susina", "prugna",
            "cancro batterico delle drupacee",
        ],
    },
    "NOCCIOLO": {
        "nome": "Nocciolo",
        "sezioni": [
            "NOCCIOLO", "Nocciolo", "CORILICOLTURA",
            "COLTURA NOCCIOLO", "COLTURA: NOCCIOLO",
        ],
        "keywords": [
            "nocciolo", "nocciola", "corilicolo",
            "eriofide del nocciolo", "phytocoptella avellanae",
            "mal dello stacco", "cytospora corylicola",
            "tonda di giffoni", "san giovanni",
        ],
    },
    # Campania estive (da verificare nei bollettini primavera/estate)
    "AGRUMI": {
        "nome": "Agrumi",
        "sezioni": [
            "AGRUMI", "Agrumi",
            "COLTURA: AGRUMI", "COLTURA AGRUMI",
        ],
        "keywords": ["agrumi", "arancio", "limone", "mandarino"],
    },
    "POMODORO": {
        "nome": "Pomodoro",
        "sezioni": [
            "POMODORO", "Pomodoro",
            "COLTURA: POMODORO", "COLTURA POMODORO",
        ],
        "keywords": ["pomodoro", "solanacee"],
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
