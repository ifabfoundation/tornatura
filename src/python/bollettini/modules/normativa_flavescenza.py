"""
Normativa Flavescenza Dorata - Dati strutturati.

Determinazione Regionale N.9016 del 14/05/2025
"Prescrizioni fitosanitarie per la lotta contro la Flavescenza Dorata
della vite nella Regione Emilia-Romagna. Anno 2025"

Questo file viene aggiornato annualmente (tipicamente a maggio).
Per aggiornare: sostituire NORMATIVA_CORRENTE con i nuovi dati.

Utilizzo:
    from normativa_flavescenza import get_normativa_per_provincia, get_obblighi_generali
"""

from typing import Dict, List, Optional


# ============= NORMATIVA 2025 =============
NORMATIVA_2025 = {
    "anno": 2025,
    "determinazione": "N.9016 del 14/05/2025",
    "riferimento": "Ordinanza SFC n.4 del 22/06/2023",
    "documenti_tecnici": [
        "Nota Settore Fitosanitario prot. 516119 del 26/05/2025 (Lotta obbligatoria scafoideo)",
        "Scheda tecnica 'Interventi insetticidi obbligatori 2025' v.01 del 29/05/2025"
    ],

    # Obblighi generali (validi per TUTTE le province)
    "obblighi_generali": {
        "trattamenti_vigneti": "Almeno 2 trattamenti nel periodo primaverile-estivo con prodotti fitosanitari autorizzati contro Scaphoideus titanus o cicaline in genere",
        "trattamenti_vivai": "Almeno 3 trattamenti per campi piante madri (marze e portinnesti) e barbatellai, nei periodi indicati dal Settore Fitosanitario",
        "estirpo_zona_infestata": "Obbligo di estirpo immediato di ogni pianta con sintomi sospetti, anche in assenza di analisi di conferma",
        "estirpo_zona_cuscinetto": "Obbligo di estirpo immediato di ogni pianta con sintomi sospetti (dopo conferma analisi di laboratorio)",
        "capitozzatura": "Ammessa come alternativa temporanea: taglio dell'intera porzione aerea (chioma) + eliminazione ricacci. Estirpo completo del ceppo entro 31 marzo",
        "piante_madri": "Obbligo estirpo immediato piante sintomatiche + divieto prelievo materiale di moltiplicazione senza autorizzazione del Settore Fitosanitario",
        "sanzioni_min": 1000,
        "sanzioni_max": 6000,
        "sanzioni_riferimento": "D.Lgs. 02/02/2021 n.19, art. 55 comma 15"
    },

    # ===========================================
    # SCADENZE TRATTAMENTI (valide per TUTTA la regione)
    # ===========================================
    "scadenze_trattamenti": {
        "inizio_lotta": "5 giugno 2025",
        "condizioni_preliminari": "Non prima della completa sfioritura della vite e dopo sfalcio erbe spontanee fiorite sottostanti",
        "integrata": {
            "primo_trattamento": "entro 20 giugno 2025",
            "secondo_trattamento": "entro 31 luglio 2025",
            "periodo_consigliato_primo": "5-15 giugno 2025",
            "intervallo_secondo": "20-30 giorni dal primo"
        },
        "biologica": {
            "primo_trattamento": "entro 20 giugno 2025",
            "secondo_trattamento": "entro 15 luglio 2025",
            "periodo_consigliato_primo": "5-12 giugno 2025 (consigliato anticipare)",
            "intervallo_secondo": "circa 1 settimana dal primo",
            "nota_terzo": "Se presenza significativa scafoideo, consigliato 3° trattamento con intervallo 1 settimana"
        },
        "vivai_barbatellai": {
            "terzo_trattamento": "entro 31 agosto 2025"
        }
    },

    # ===========================================
    # INSETTICIDI AMMESSI (validi per TUTTA la regione)
    # ===========================================
    "insetticidi_ammessi": {
        "difesa_integrata": [
            {"sostanza": "Acetamiprid", "limitazioni": "max 1 intervento/anno", "bio": False},
            {"sostanza": "Sulfoxaflor", "limitazioni": "uso emergenza (Closer) dal 01/05 al 28/08/2025", "bio": False},
            {"sostanza": "Flupyradifurone", "limitazioni": "max 1 intervento/anno", "bio": False},
            {"sostanza": "Tau-fluvalinate", "limitazioni": "max 2 interventi/anno, piretroide", "bio": False},
            {"sostanza": "Deltametrina", "limitazioni": "max 2 interventi/anno, piretroide", "bio": False},
            {"sostanza": "Etofenprox", "limitazioni": "max 1 tra Etofenprox/Lambdacialotrina/Esfenvalerate, piretroide", "bio": False},
            {"sostanza": "Lambdacialotrina", "limitazioni": "max 1 tra Etofenprox/Lambdacialotrina/Esfenvalerate, piretroide", "bio": False},
            {"sostanza": "Esfenvalerate", "limitazioni": "max 1 tra Etofenprox/Lambdacialotrina/Esfenvalerate, piretroide", "bio": False},
            {"sostanza": "Piretrine pure", "limitazioni": "piretroide", "bio": True},
            {"sostanza": "Azadiractina", "limitazioni": None, "bio": True},
            {"sostanza": "Beauveria bassiana", "limitazioni": None, "bio": True},
            {"sostanza": "Olio essenziale di arancio dolce", "limitazioni": None, "bio": True},
            {"sostanza": "Sali potassici degli acidi grassi", "limitazioni": None, "bio": True},
            {"sostanza": "Silicato di alluminio (caolino)", "limitazioni": "SURROUND uso emergenza dal 17/04 al 14/08/2025", "bio": True}
        ],
        "nota_piretroidi": "Max 4 interventi/anno complessivi con piretrine e piretroidi",
        "nota_closer": "2 trattamenti a meta dose con Closer = 1 trattamento a dose piena"
    },

    # ===========================================
    # STRATEGIE DI DIFESA RACCOMANDATE (valide per TUTTA la regione)
    # Fonte: DTU n.29 Comitato Fitosanitario Nazionale 13/12/2022
    # ===========================================
    "strategie_difesa": {
        "integrata": {
            "primo_trattamento": ["Acetamiprid", "Flupyradifurone", "Sulfoxaflor"],
            "secondo_trattamento": ["Tau-fluvalinate", "Deltametrina", "Etofenprox", "Lambdacialotrina", "Esfenvalerate"],
            "nota": "Se si usano prodotti bio, seguire strategia biologica"
        },
        "biologica": {
            "primo_trattamento": ["Azadiractina", "Beauveria bassiana", "Olio arancio", "Piretrine", "Sali potassici", "Caolino"],
            "secondo_trattamento": ["Piretrine pure (OBBLIGATORIO)"],
            "nota": "Almeno 1 dei 2 trattamenti obbligatori DEVE essere con piretrine"
        }
    },

    # ===========================================
    # ACCORGIMENTI OPERATIVI (validi per TUTTA la regione)
    # ===========================================
    "accorgimenti_operativi": [
        "Cimare e sfoltire vegetazione 2-3 giorni prima del trattamento (permette risalita forme giovanili)",
        "Spollonatura 3 giorni prima del trattamento",
        "Verificare taratura e funzionamento attrezzatura",
        "Volume minimo acqua: 400 lt/ha",
        "Bagnare accuratamente tutta la vegetazione, comprese parti interne, polloni e ricacci",
        "Correggere pH soluzione (deve essere < 7)",
        "Evitare miscele con altri prodotti se possibile",
        "Prodotti fotolabili (es. piretro): trattare nelle ore serali o notturne",
        "Usare cartine idrosensibili per verificare qualita distribuzione"
    ],

    # ===========================================
    # TUTELA API (L.R. 2/2019)
    # ===========================================
    "tutela_api": {
        "riferimento": "L.R. 4 marzo 2019 n. 2 - Norme tutela apicoltura",
        "divieto_fioritura": "Vietato trattare con insetticidi/acaricidi durante fioritura (dalla schiusura petali alla caduta)",
        "divieto_fioriture_spontanee": "Vietato trattare in presenza di fioriture spontanee sottostanti, salvo preventivo sfalcio/trinciatura con asportazione",
        "consiglio": "Effettuare trattamenti nelle ore serali quando attivita pronubi e' limitata o assente"
    },

    # Zone delimitate per provincia
    "province": {
        "Piacenza": {
            "zona_infestata": [
                "Agazzano", "Alseno", "Alta val Tidone", "Besenzone", "Bobbio",
                "Borgonovo Val Tidone", "Cadeo", "Calendasco", "Caorso",
                "Carpaneto Piacentino", "Castel San Giovanni", "Castell'Arquato",
                "Castelvetro Piacentino", "Cortemaggiore", "Fiorenzuola d'Arda",
                "Gazzola", "Gossolengo", "Gragnano Trebbiense", "Monticelli D'Ongina",
                "Piacenza", "Pianello Val Tidone", "Piozzano", "Podenzano",
                "Ponte Dell'Olio", "Pontenure", "Rivergaro", "Rottofreno",
                "San Giorgio Piacentino", "San Pietro in Cerro", "Sarmato",
                "Travo", "Vigolzone", "Villanova Sull'Arda", "Ziano Piacentino"
            ],
            "zona_cuscinetto": [
                "Bettola", "Cerignale", "Coli", "Corte Brugnatella",
                "Gropparello", "Lugagnano Val D'Arda", "Vernasca", "Zerba"
            ],
            "note": "Zona cuscinetto perimetrale 500m per i comuni indicati"
        },

        "Parma": {
            "zona_infestata": [
                "Busseto", "Collecchio", "Colorno", "Fidenza", "Fontanellato",
                "Fontevivo", "Montechiarugolo", "Noceto", "Polesine Zibello",
                "Roccabianca", "Salsomaggiore Terme", "San Secondo Parmense",
                "Sissa Trecasali", "Soragna", "Sorbolo", "Mezzani", "Torrile"
            ],
            "zona_cuscinetto": [
                "Felino", "Fornovo Di Taro", "Langhirano", "Medesano", "Parma",
                "Pellegrino Parmense", "Sala Baganza", "Traversetolo", "Varano De'Melegari"
            ],
            "note": "Zona cuscinetto perimetrale 500m per i comuni indicati"
        },

        "Reggio Emilia": {
            "zona_infestata": [
                "Albinea", "Bagnolo in Piano", "Bibbiano", "Boretto", "Brescello",
                "Cadelbosco Di Sopra", "Campagnola Emilia", "Campegine", "Casalgrande",
                "Castellarano", "Castelnovo Di Sotto", "Cavriago", "Correggio",
                "Fabbrico", "Gattatico", "Gualtieri", "Guastalla", "Luzzara",
                "Montecchio Emilia", "Novellara", "Poviglio", "Quattro Castella",
                "Reggio nell'Emilia", "Reggiolo", "Rio Saliceto", "Rolo", "Rubiera",
                "San Martino In Rio", "San Polo D'Enza", "Sant'Ilario D'Enza", "Scandiano"
            ],
            "zona_cuscinetto": [
                "Baiso", "Canossa", "Vezzano Sul Crostolo", "Viano"
            ],
            "note": "Zona cuscinetto perimetrale 500m per i comuni indicati"
        },

        "Modena": {
            "zona_infestata": [
                "Bastiglia", "Bomporto", "Campogalliano", "Camposanto", "Carpi",
                "Castelfranco Emilia", "Castelnuovo Rangone", "Castelvetro Di Modena",
                "Cavezzo", "Concordia sulla Secchia", "Finale Emilia", "Fiorano Modenese",
                "Formigine", "Guiglia", "Maranello", "Medolla", "Mirandola", "Modena",
                "Nonantola", "Novi di Modena", "Ravarino", "San Cesario Sul Panaro",
                "San Felice Sul Panaro", "San Possidonio", "San Prospero", "Sassuolo",
                "Savignano Sul Panaro", "Soliera", "Spilamberto", "Vignola"
            ],
            "zona_cuscinetto": [
                "Marano Sul Panaro", "Prignano sulla Secchia", "Serramazzoni"
            ],
            "zona_cuscinetto_speciale": [
                "Pavullo nel Frignano", "Zocca"
            ],
            "note": "Zona cuscinetto perimetrale 500m. Pavullo e Zocca: cuscinetto 500m dal confine con Guiglia"
        },

        "Bologna": {
            "zona_infestata": [
                "Anzola Dell'Emilia", "Argelato", "Baricella", "Bentivoglio", "Bologna",
                "Borgo Tossignano", "Budrio", "Calderara Di Reno", "Casalecchio Di Reno",
                "Castel Guelfo Di Bologna", "Castel Maggiore", "Castello D'Argile",
                "Castenaso", "Crevalcore", "Dozza", "Galliera", "Granarolo dell'Emilia",
                "Imola", "Malalbergo", "Medicina", "Minerbio", "Molinella",
                "Monte San Pietro", "Mordano", "Pieve Di Cento", "Sala Bolognese",
                "San Giorgio Di Piano", "San Giovanni In Persiceto", "San Lazzaro Di Savena",
                "San Pietro in Casale", "Sant'Agata Bolognese", "Sasso Marconi", "Zola Predosa"
            ],
            "zona_cuscinetto": [
                "Casalfiumanese", "Castel San Pietro Terme", "Fontanelice", "Marzabotto",
                "Monzuno", "Ozzano dell'Emilia", "Pianoro", "Valsamoggia"
            ],
            "note": "Zona cuscinetto perimetrale 500m per i comuni indicati"
        },

        "Ferrara": {
            "zona_infestata": ["INTERA PROVINCIA"],
            "zona_cuscinetto": [],
            "note": "Tutta la provincia e' zona infestata"
        },

        "Ravenna": {
            "zona_infestata": [
                "Alfonsine", "Bagnacavallo", "Bagnara Di Romagna", "Castel Bolognese",
                "Cervia", "Conselice", "Cotignola", "Faenza", "Fusignano", "Lugo",
                "Massa Lombarda", "Ravenna", "Riolo Terme", "Russi",
                "Sant'Agata Sul Santerno", "Solarolo"
            ],
            "zona_cuscinetto": [
                "Brisighella", "Casola Valsenio"
            ],
            "note": "Zona cuscinetto perimetrale 500m per i comuni indicati"
        },

        "Forli-Cesena": {
            "zona_infestata": [
                "Bertinoro", "Castrocaro Terme e Terra Del Sole", "Dovadola",
                "Forli'", "Forlimpopoli", "Montiano"
            ],
            "zona_cuscinetto": [
                "Borghi", "Cesena", "Cesenatico", "Longiano", "Meldola",
                "Modigliana", "Predappio", "Rocca San Casciano", "Roncofreddo", "Tredozio"
            ],
            "note": "Zona cuscinetto perimetrale 500m per i comuni indicati"
        },

        "Rimini": {
            "zona_infestata": ["Poggio Torriana (solo focolaio Case Marcosanti)"],
            "zona_cuscinetto": ["Poggio Torriana (parziale)", "Santarcangelo di Romagna (parziale)"],
            "note": "Focolaio puntuale con zona cuscinetto 500m"
        }
    }
}

# Puntatore alla normativa corrente (da aggiornare annualmente)
NORMATIVA_CORRENTE = NORMATIVA_2025


# ============= FUNZIONI DI ACCESSO =============

def get_obblighi_generali() -> Dict:
    """Restituisce gli obblighi generali validi per tutte le province."""
    return NORMATIVA_CORRENTE["obblighi_generali"]


def get_info_normativa() -> Dict:
    """Restituisce le info base della normativa (anno, determinazione, riferimento)."""
    return {
        "anno": NORMATIVA_CORRENTE["anno"],
        "determinazione": NORMATIVA_CORRENTE["determinazione"],
        "riferimento": NORMATIVA_CORRENTE["riferimento"]
    }


def get_province_disponibili() -> List[str]:
    """Restituisce la lista delle province disponibili."""
    return list(NORMATIVA_CORRENTE["province"].keys())


def normalizza_nome_provincia(provincia: str) -> Optional[str]:
    """
    Normalizza il nome della provincia per il matching.

    Gestisce varianti come:
    - "Bologna" / "BOLOGNA" / "bologna"
    - "Reggio Emilia" / "Reggio-Emilia" / "RE"
    - "Forli-Cesena" / "Forlì-Cesena" / "FC"
    """
    provincia_lower = provincia.lower().strip()

    # Mapping varianti -> nome standard
    mapping = {
        # Piacenza
        "piacenza": "Piacenza", "pc": "Piacenza",
        # Parma
        "parma": "Parma", "pr": "Parma",
        # Reggio Emilia
        "reggio emilia": "Reggio Emilia", "reggio-emilia": "Reggio Emilia",
        "reggio nell'emilia": "Reggio Emilia", "re": "Reggio Emilia",
        # Modena
        "modena": "Modena", "mo": "Modena",
        # Bologna
        "bologna": "Bologna", "bo": "Bologna",
        # Ferrara
        "ferrara": "Ferrara", "fe": "Ferrara",
        # Ravenna
        "ravenna": "Ravenna", "ra": "Ravenna",
        # Forli-Cesena
        "forli-cesena": "Forli-Cesena", "forlì-cesena": "Forli-Cesena",
        "forli cesena": "Forli-Cesena", "forlì cesena": "Forli-Cesena",
        "fc": "Forli-Cesena",
        # Rimini
        "rimini": "Rimini", "rn": "Rimini"
    }

    return mapping.get(provincia_lower)


def get_zone_provincia(provincia: str) -> Optional[Dict]:
    """
    Restituisce le zone delimitate per una specifica provincia.

    Args:
        provincia: Nome provincia (case-insensitive, accetta varianti)

    Returns:
        Dict con zona_infestata, zona_cuscinetto, note oppure None se non trovata
    """
    nome_standard = normalizza_nome_provincia(provincia)
    if nome_standard and nome_standard in NORMATIVA_CORRENTE["province"]:
        return NORMATIVA_CORRENTE["province"][nome_standard]
    return None


def get_normativa_per_provincia(provincia: str) -> Optional[Dict]:
    """
    Restituisce TUTTE le informazioni normative filtrate per provincia.

    Combina:
    - Info base normativa (anno, determinazione)
    - Obblighi generali (validi per tutti)
    - Zone specifiche della provincia

    Args:
        provincia: Nome provincia (case-insensitive, accetta varianti)

    Returns:
        Dict completo oppure None se provincia non trovata
    """
    nome_standard = normalizza_nome_provincia(provincia)
    if not nome_standard:
        return None

    zone = get_zone_provincia(provincia)
    if not zone:
        return None

    return {
        "anno": NORMATIVA_CORRENTE["anno"],
        "determinazione": NORMATIVA_CORRENTE["determinazione"],
        "riferimento": NORMATIVA_CORRENTE["riferimento"],
        "obblighi_generali": NORMATIVA_CORRENTE["obblighi_generali"],
        "zone_provincia": zone,
        "provincia": nome_standard
    }


def _formatta_zona_singola(provincia: str) -> Optional[str]:
    """Formatta le zone per una singola provincia."""
    zone = get_zone_provincia(provincia)
    if not zone:
        return None

    nome_standard = normalizza_nome_provincia(provincia)

    # Formatta zone infestata
    if zone["zona_infestata"] == ["INTERA PROVINCIA"]:
        zona_infestata_str = "INTERA PROVINCIA"
    else:
        zona_infestata_str = ", ".join(zone["zona_infestata"])

    # Formatta zona cuscinetto
    if zone["zona_cuscinetto"]:
        zona_cuscinetto_str = ", ".join(zone["zona_cuscinetto"])
    else:
        zona_cuscinetto_str = "Nessuna (tutta zona infestata)"

    # Zona cuscinetto speciale (solo Modena)
    zona_speciale_str = ""
    if "zona_cuscinetto_speciale" in zone:
        zona_speciale_str = f"\n- Zona cuscinetto speciale: {', '.join(zone['zona_cuscinetto_speciale'])}"

    return f"""ZONE DELIMITATE ({nome_standard}):
- Zona infestata: {zona_infestata_str}
- Zona cuscinetto: {zona_cuscinetto_str}{zona_speciale_str}
- Note: {zone.get('note', 'Nessuna')}"""


def _formatta_scadenze() -> str:
    """Formatta le scadenze trattamenti."""
    scad = NORMATIVA_CORRENTE["scadenze_trattamenti"]
    return f"""SCADENZE TRATTAMENTI OBBLIGATORI:
- Inizio lotta obbligatoria: {scad['inizio_lotta']}
- Condizioni preliminari: {scad['condizioni_preliminari']}

Difesa INTEGRATA:
- 1° trattamento: {scad['integrata']['primo_trattamento']} (consigliato: {scad['integrata']['periodo_consigliato_primo']})
- 2° trattamento: {scad['integrata']['secondo_trattamento']} ({scad['integrata']['intervallo_secondo']})

Difesa BIOLOGICA:
- 1° trattamento: {scad['biologica']['primo_trattamento']} (consigliato: {scad['biologica']['periodo_consigliato_primo']})
- 2° trattamento: {scad['biologica']['secondo_trattamento']} ({scad['biologica']['intervallo_secondo']})
- Nota: {scad['biologica']['nota_terzo']}

Vivai/Barbatellai: 3° trattamento {scad['vivai_barbatellai']['terzo_trattamento']}"""


def _formatta_insetticidi() -> str:
    """Formatta gli insetticidi ammessi."""
    ins = NORMATIVA_CORRENTE["insetticidi_ammessi"]

    lines = ["INSETTICIDI AMMESSI:"]

    # Difesa integrata
    lines.append("\nDifesa INTEGRATA:")
    for prod in ins["difesa_integrata"]:
        if not prod["bio"]:
            limit = f" ({prod['limitazioni']})" if prod['limitazioni'] else ""
            lines.append(f"- {prod['sostanza']}{limit}")

    # Difesa biologica
    lines.append("\nDifesa BIOLOGICA:")
    for prod in ins["difesa_integrata"]:
        if prod["bio"]:
            limit = f" ({prod['limitazioni']})" if prod['limitazioni'] else ""
            lines.append(f"- {prod['sostanza']}{limit}")

    # Note
    lines.append(f"\nNOTA piretroidi: {ins['nota_piretroidi']}")
    lines.append(f"NOTA Closer: {ins['nota_closer']}")

    return "\n".join(lines)


def _formatta_strategie() -> str:
    """Formatta le strategie di difesa raccomandate."""
    strat = NORMATIVA_CORRENTE["strategie_difesa"]

    lines = ["STRATEGIE DIFESA RACCOMANDATE (DTU n.29 CFN 13/12/2022):"]

    lines.append("\nDifesa INTEGRATA:")
    lines.append(f"- 1° trattamento: {', '.join(strat['integrata']['primo_trattamento'])}")
    lines.append(f"- 2° trattamento: {', '.join(strat['integrata']['secondo_trattamento'])}")
    lines.append(f"- Nota: {strat['integrata']['nota']}")

    lines.append("\nDifesa BIOLOGICA:")
    lines.append(f"- 1° trattamento: {', '.join(strat['biologica']['primo_trattamento'])}")
    lines.append(f"- 2° trattamento: {', '.join(strat['biologica']['secondo_trattamento'])}")
    lines.append(f"- IMPORTANTE: {strat['biologica']['nota']}")

    return "\n".join(lines)


def _formatta_accorgimenti() -> str:
    """Formatta gli accorgimenti operativi."""
    acc = NORMATIVA_CORRENTE["accorgimenti_operativi"]

    lines = ["ACCORGIMENTI OPERATIVI:"]
    for item in acc:
        lines.append(f"- {item}")

    return "\n".join(lines)


def _formatta_tutela_api() -> str:
    """Formatta le norme tutela api."""
    api = NORMATIVA_CORRENTE["tutela_api"]

    return f"""TUTELA API ({api['riferimento']}):
- {api['divieto_fioritura']}
- {api['divieto_fioriture_spontanee']}
- Consiglio: {api['consiglio']}"""


def formatta_normativa_per_llm(province_str: str) -> Optional[str]:
    """
    Formatta le informazioni normative come testo per il context LLM.

    Gestisce sia singole province che province multiple (es. "Bologna,Ferrara").

    Args:
        province_str: Nome provincia o province separate da virgola

    Returns:
        Stringa formattata per il prompt LLM oppure None
    """
    # Gestisce province multiple (es. "Bologna,Ferrara")
    province_list = [p.strip() for p in province_str.split(',')]

    # Obblighi generali (sempre gli stessi)
    obblighi = get_obblighi_generali()
    info = get_info_normativa()

    # Raccogli zone per ogni provincia
    zone_sections = []
    province_valide = []

    for provincia in province_list:
        zona_text = _formatta_zona_singola(provincia)
        if zona_text:
            zone_sections.append(zona_text)
            province_valide.append(normalizza_nome_provincia(provincia))

    if not zone_sections:
        return None

    province_header = ", ".join(province_valide)
    zone_text = "\n\n".join(zone_sections)

    # Formatta tutte le sezioni
    scadenze_text = _formatta_scadenze()
    insetticidi_text = _formatta_insetticidi()
    strategie_text = _formatta_strategie()
    accorgimenti_text = _formatta_accorgimenti()
    tutela_api_text = _formatta_tutela_api()

    return f"""=== NORMATIVA REGIONALE (Determinazione {info['determinazione']}) ===
Documenti tecnici: {', '.join(NORMATIVA_CORRENTE.get('documenti_tecnici', []))}

PROVINCE: {province_header}

OBBLIGHI GENERALI:
- Trattamenti vigneti: {obblighi['trattamenti_vigneti']}
- Trattamenti vivai/barbatellai: {obblighi['trattamenti_vivai']}
- Estirpo zona infestata: {obblighi['estirpo_zona_infestata']}
- Estirpo zona cuscinetto: {obblighi['estirpo_zona_cuscinetto']}
- Capitozzatura: {obblighi['capitozzatura']}
- Piante madri: {obblighi['piante_madri']}
- Sanzioni: da {obblighi['sanzioni_min']:,} a {obblighi['sanzioni_max']:,} euro ({obblighi['sanzioni_riferimento']})

{scadenze_text}

{insetticidi_text}

{strategie_text}

{accorgimenti_text}

{tutela_api_text}

{zone_text}
"""


# ============= TEST =============

if __name__ == "__main__":
    # Test
    print("Province disponibili:", get_province_disponibili())
    print()

    # Test normalizzazione
    for test in ["Bologna", "BOLOGNA", "bo", "Reggio Emilia", "RE", "Forlì-Cesena"]:
        print(f"  '{test}' -> {normalizza_nome_provincia(test)}")
    print()

    # Test output formattato (singola provincia)
    print("=== TEST SINGOLA PROVINCIA ===")
    print(formatta_normativa_per_llm("Modena"))

    # Test output formattato (province multiple)
    print("\n=== TEST PROVINCE MULTIPLE ===")
    print(formatta_normativa_per_llm("Bologna,Ferrara"))
