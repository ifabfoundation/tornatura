"""Estrae la "Fase fenologica" per coltura dai bollettini di produzione integrata dell'Emilia-Romagna.

Deterministico, senza modelli linguistici: ogni riga di uscita porta file e numero di riga
e si puo' ricontrollare aprendo il sorgente. In produzione il testo arriva da `testo.py`
(pypdfium2, gia' senza revisioni di Word e con i trattini a fine riga); le regole sono quelle
dell'esperimento `esperimenti/cimice_landscape/fenologia/estrai_fasi.py`, verificate il
25/09/2026 su 165 bollettini ER 2026: 5.142 righe identiche alla tabella controllata a mano.
Il ramo "docling" (markdown) resta per compatibilita' con l'esperimento.

REGOLE (tutte esplicite; i casi fuori regola finiscono in uno stato da rivedere, mai
accettati in silenzio)

R1 Una fase e' una riga che INIZIA con "Fase fenologica" (dopo `#`, `*`, commenti
   immagine), oppure una riga "COLTURA Fase fenologica: ..." con COLTURA nota. Le
   menzioni dentro frasi o tabelle ("prestare attenzione alla fase fenologica") no.
R2 Un'intestazione di coltura e' una riga il cui testo (tolti `#`, `*`, commenti
   immagine, due punti finali) e' in MAIUSCOLO ed e' nell'elenco `COLTURE`, esatto o
   togliendo una parentesi finale ("MELONE (coltura semiforzata)"). Vale sia come
   titolo markdown sia come riga semplice: in molti bollettini "VITE", "PESCO",
   "CILIEGIO" sono righe semplici. Un maiuscolo non in elenco non e' mai associato a
   una coltura per somiglianza.
R3 La coltura di una fase e' l'ultima intestazione di coltura vista, PURCHE' non abbia
   gia' ricevuto una fase: una sezione ha una sola riga di fase. Una seconda fase
   sotto la stessa intestazione (segno di un'intestazione persa) -> stato
   `seconda_fase_stessa_intestazione`. Un'intestazione di sezione nota (`AZZERA`,
   es. "COLTURE ERBACEE", "DIFESA") azzera la coltura corrente.
R4 Il testo della fase e' quello sulla stessa riga; se e' vuoto, o termina con una
   parola sospesa ("da", "a", "ad", "e", "verde:" ...), si aggiunge la riga seguente
   (una sola) purche' sia corta, non sia un'intestazione, un commento o un'etichetta
   ("Batteriosi:"). Nel testo Poppler una riga che prosegue in minuscolo senza due
   punti e' la continuazione dello stesso paragrafo.
R5 Una fase e' `ok` solo se contiene un vocabolo fenologico (`VOCABOLARIO`); altrimenti
   `dubbia`. Se al posto della fase c'e' un'intestazione, un commento/immagine,
   un'etichetta di malattia o un paragrafo, la fase e' `assente`.
R6 Coerenza coltura-vocabolario: termini esclusivi di un gruppo (es. "grappoli" solo
   per la vite, "trilobata" per la soia, "pennacchio" per il mais) usati per un'altra
   coltura -> stato `incoerente`. E' il controllo contro l'errore piu' pericoloso,
   la fase giusta attribuita alla coltura sbagliata.
R7 Data, numero e area dal nome del file; un nome non riconosciuto e' un errore.
R8-R9 (pulizia finale, in `testo.pulisci_fase`) titoli di sottosezione ed etichette incollati.
"""

from __future__ import annotations

import datetime as dt
import re

MESI = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}

AREE = {
    "modena": ("Modena", ["MO"]),
    "reggio emilia": ("Reggio Emilia", ["RE"]),
    "bologna e ferrara": ("Bologna e Ferrara", ["BO", "FE"]),
    "forli-cesena, ravenna, rimini": (
        "Forli-Cesena, Ravenna, Rimini",
        ["FC", "RA", "RN"],
    ),
    "forli-cesena, ravenna e rimini": (
        "Forli-Cesena, Ravenna, Rimini",
        ["FC", "RA", "RN"],
    ),
    "parma": ("Parma", ["PR"]),
    "piacenza": ("Piacenza", ["PC"]),
}

# Intestazione (maiuscolo) -> coltura. Le sottospecie con fenologia diversa restano
# distinte (susino europeo e cino-giapponese, pomodoro da industria e da mensa): se e
# come fonderle e' una scelta a valle, dichiarata, non dell'estrattore.
COLTURE = {
    "PERO": "PERO",
    "MELO": "MELO",
    "PESCO": "PESCO",
    "PESCO E NETTARINE": "PESCO",
    "PESCHE E NETTARINE": "PESCO",
    "PESCO E NETTARINO": "PESCO",
    "NETTARINE": "PESCO",
    "ALBICOCCO": "ALBICOCCO",
    "CILIEGIO": "CILIEGIO",
    "SUSINO": "SUSINO",
    "SUSINO EUROPEO": "SUSINO_EUROPEO",
    "SUSINO EUPEREO": "SUSINO_EUROPEO",
    "SUSINO CINO-GIAPPONESE": "SUSINO_CINO_GIAPPONESE",
    "SUSINO CINO GIAPPONESE": "SUSINO_CINO_GIAPPONESE",
    "SUSINO CINO-GIAPPONESE ED EUROPEO": "SUSINO",
    "ACTINIDIA": "ACTINIDIA",
    "KIWI": "ACTINIDIA",
    "KAKI": "KAKI",
    "NOCE": "NOCE",
    "NOCCIOLO": "NOCCIOLO",
    "OLIVO": "OLIVO",
    "VITE": "VITE",
    "CASTAGNO": "CASTAGNO",
    "MAIS": "MAIS",
    "SOIA": "SOIA",
    "SORGO": "SORGO",
    "GIRASOLE": "GIRASOLE",
    "COLZA": "COLZA",
    "FRUMENTO": "FRUMENTO",
    "FRUMENTO TENERO": "FRUMENTO",
    "FRUMENTO DURO": "FRUMENTO",
    "FRUMENTO TENERO E DURO": "FRUMENTO",
    "FRUMENTO DURO E TENERO": "FRUMENTO",
    "FRUMENTO E ORZO": "FRUMENTO",
    "CEREALI AUTUNNO-VERNINI": "FRUMENTO",
    "CEREALI AUTUNNO VERNINI": "FRUMENTO",
    "CEREALI AUTUNNO VERNINI (FRUMENTO E ORZO)": "FRUMENTO",
    "CEREALI AUTUNNO-VERNINI (FRUMENTO E ORZO)": "FRUMENTO",
    "ORZO": "ORZO",
    "RISO": "RISO",
    "ERBA MEDICA": "ERBA_MEDICA",
    "MEDICA": "ERBA_MEDICA",
    "BARBABIETOLA DA ZUCCHERO": "BARBABIETOLA",
    "BARBABIETOLA": "BARBABIETOLA",
    "BIETOLA DA ZUCCHERO": "BARBABIETOLA",
    "POMODORO DA INDUSTRIA": "POMODORO_INDUSTRIA",
    "POMODORO": "POMODORO",
    "POMODORO DA MENSA": "POMODORO_MENSA",
    "PATATA": "PATATA",
    "CIPOLLA": "CIPOLLA",
    "CIPOLLA PRIMAVERILE": "CIPOLLA",
    "AGLIO": "AGLIO",
    "PISELLO": "PISELLO",
    "PISELLO PROTEICO": "PISELLO",
    "FAGIOLINO": "FAGIOLINO",
    "FAGIOLO": "FAGIOLO",
    "MELONE": "MELONE",
    "ANGURIA": "ANGURIA",
    "COCOMERO": "ANGURIA",
    "ZUCCHINO": "ZUCCHINO",
    "ZUCCA": "ZUCCA",
    "PEPERONE": "PEPERONE",
    "MELANZANA": "MELANZANA",
    "LATTUGA": "LATTUGA",
    "SPINACIO": "SPINACIO",
    "CAVOLI": "CAVOLI",
    "CAVOLO": "CAVOLI",
    "CAVOLI A TESTA (CAPPUCCI)": "CAVOLI",
    "CAVOLI A INFIORESCENZA": "CAVOLI",
    "FRAGOLA": "FRAGOLA",
    "ASPARAGO": "ASPARAGO",
    "CARCIOFO": "CARCIOFO",
    "FINOCCHIO": "FINOCCHIO",
    "SEDANO": "SEDANO",
    "CAROTA": "CAROTA",
    "RADICCHIO": "RADICCHIO",
    "BASILICO": "BASILICO",
    "PREZZEMOLO": "PREZZEMOLO",
    "CETRIOLO": "CETRIOLO",
    "PORRO": "PORRO",
    "CANAPA": "CANAPA",
    "PIOPPO": "PIOPPO",
    "FAVINO": "FAVINO",
    "CECE": "CECE",
    "LENTICCHIA": "LENTICCHIA",
}
# Intestazioni di sezione che chiudono la sezione della coltura precedente.
AZZERA = {
    "COLTURE ARBOREE",
    "COLTURE ERBACEE",
    "COLTURE ORTICOLE",
    "DIFESA",
    "DIFESA ARBOREE",
    "DIFESA ERBACEE",
    "DIFESA ORTICOLE",
    "DISERBO ARBOREE",
    "DISERBO ERBACEE",
    "PARTE SPECIFICA",
    "TECNICHE AGRONOMICHE",
    "INFORMAZIONI GENERALI",
    "INFORMAZIONI GENERALI E NORMATIVE",
    "INDICAZIONI LEGISLATIVE",
    "INFORMAZIONI METEO",
    "IRRIGAZIONE",
    "FERTILIZZAZIONE",
    "DIFESA E CONTROLLO DELLE INFESTANTI",
    "TRATTAMENTI IN FIORITURA",
    "DATI DI FALDA",
    "AMBITO APPLICATIVO",
    "PATENTINI FITOSANITARI",
    "COLTURE",
    "ARBOREE",
    "ERBACEE",
    "ORTICOLE",
    "INFORMAZIONI RIGUARDANTI LA CIMICE ASIATICA (HALYOMORPHA HALYS)",
}

VOCABOLARIO = [
    "gemm",
    "germogl",
    "fiorit",
    "bottone",
    "bottoni",
    "mazzett",
    "allegag",
    "frutt",
    "maturaz",
    "raccolt",
    "invaiat",
    "semina",
    "emergen",
    "cotiledon",
    "fogli",
    "levata",
    "spigat",
    "accestim",
    "trapiant",
    "baccell",
    "pennacch",
    "sete",
    "bulb",
    "fittone",
    "chiusura",
    "palco",
    "indurim",
    "nocciol",
    "scamiciat",
    "ripresa",
    "riposo",
    "caduta",
    "mignol",
    "drup",
    "ceros",
    "latte",
    "lattea",
    "vegetat",
    "dormien",
    "punte verdi",
    "punta verde",
    "orecchiette",
    "rigonfiam",
    "rosetta",
    "grappol",
    "acin",
    "fine ciclo",
    "senescen",
    "ingrossam",
    "accrescim",
    "sviluppo",
    "infiorescenz",
    "formazione",
    "riempim",
    "trilobat",
    "interfila",
    "capolin",
    "tuber",
    "stolon",
    "fiore",
    "piantine",
    "cima",
    "fusto",
    "ricacc",
    "abbozz",
    "turion",
    "zampe",
    "sfalci",
    "dimora",
    "botticella",
    "cotonos",
    "seme",
    "spiga",
    "nodo",
    "internod",
    "pannocchia",
    "granella",
    "cariossid",
    "rottura",
    "racimol",
    "allungament",
    "sepal",
]
# Termini esclusivi di un gruppo di colture (R6). Se compaiono in un'altra coltura la
# riga e' `incoerente`. Solo termini che in italiano agronomico non hanno altri usi.
ESCLUSIVI = {
    # verificati sul testo il 25/09/2026: "levata" e "spigatura" si usano anche per mais e
    # colza, "capolini" per la colza, "foglie trilobate" per la medica, "gemma cotonosa"
    # per l'actinidia, "mignolatura" per la vite. Restano esclusivi solo i termini che nel
    # corpus non hanno altri usi.
    "grappol": {"VITE"},
    "acin": {"VITE"},
    "racimol": {"VITE"},
    "cotonos": {"VITE", "ACTINIDIA", "KAKI"},
    "trilobat": {"SOIA", "FAGIOLO", "FAGIOLINO", "ERBA_MEDICA"},
    "pennacch": {"MAIS", "SORGO"},
    "cariossid": {"MAIS", "SORGO", "FRUMENTO", "ORZO", "RISO"},
    "botticella": {"FRUMENTO", "ORZO", "RISO"},
    "fittone": {"BARBABIETOLA", "CAROTA"},
    "turion": {"ASPARAGO"},
    "mazzett": {"PERO", "MELO"},
    "scamiciat": {
        "PESCO",
        "ALBICOCCO",
        "SUSINO",
        "SUSINO_EUROPEO",
        "SUSINO_CINO_GIAPPONESE",
        "CILIEGIO",
    },
    "drup": {"OLIVO"},
    "palco": {
        "POMODORO",
        "POMODORO_INDUSTRIA",
        "POMODORO_MENSA",
        "PATATA",
        "MELONE",
        "ANGURIA",
        "PEPERONE",
        "MELANZANA",
        "ZUCCHINO",
        "ZUCCA",
        "CETRIOLO",
    },
}
SOSPESO = re.compile(
    r"(?:^|\s)(?:da|dal|dalla|dallo|dai|dalle|a|ad|al|alla|allo|ai|alle|e|ed|di|del|"
    r"della|verso|fino|in|con|-|–|/)\s*$|:\s*$",
    re.I,
)
ETICHETTA = re.compile(
    r"^[A-ZÀ-Ü][\w'’àèéìòù ]{1,40}\s*:\s*$"
)  # "Batteriosi:", "Monilia :"

RE_FILE = re.compile(
    r"^Bollettino\s+(?:n\.?\s*)?(?P<num>\d+)\s*(?P<bis>BIS)?\s+del(?:l['’]?)?\s*(?P<g>\d{1,2})°?\s+"
    r"(?P<m>[A-Za-zò]+)\s+(?P<a>\d{4})\s+(?:di\s+)?(?P<area>.+?)\.(?:md|txt|pdf)$",
    re.I,
)
RE_IMG = re.compile(r"<!--.*?-->")
# "Fase" con la F maiuscola (o tutto maiuscolo): una riga che comincia con "fase
# fenologica" minuscola e' la continuazione di una frase ("... nella\nfase fenologica piu'
# avanzata"), non l'etichetta della fase.
RE_FASE = re.compile(
    r"^(?:Fase|FASE)\s+(?:fenologic|FENOLOGIC)\w*\s*(?:#+\s*)?(?::|–|-)?\s*(?P<testo>.*)$"
)
RE_COLTURA_FASE = re.compile(
    r"^(?P<coltura>[A-ZÀ-Ü][A-ZÀ-Ü'’ \-/,().]{1,60}?)\s+(?:#+\s*)?"
    r"(?:Fase|FASE)\s+(?:fenologic|FENOLOGIC)\w*\s*(?:#+\s*)?(?::|–|-)?\s*(?P<testo>.*)$"
)


def normalizza(s: str) -> str:
    return re.sub(r"[    \t]+", " ", s).rstrip()


def nucleo(riga: str) -> str:
    """Il testo della riga senza commenti immagine, `#`, `*` e spazi di contorno."""
    t = RE_IMG.sub(" ", riga)
    t = re.sub(r"^[#*\s]+", "", t)
    t = re.sub(r"[#*\s]+$", "", t)
    return re.sub(r"\s+", " ", t).strip()


def e_maiuscolo(t: str) -> bool:
    fuori = re.sub(r"\(.*?\)", "", t)  # la parentesi puo' essere minuscola
    lettere = re.sub(r"[^A-Za-zÀ-ü]", "", fuori)
    return len(lettere) >= 3 and lettere.upper() == lettere


def coltura_da_intestazione(t: str, anche_minuscolo: bool = False):
    """(chiave, testo) se `t` e' un'intestazione di coltura (R2), altrimenti (None, testo).

    Con `anche_minuscolo` accetta "Frumento" o "Soia": vale solo quando il chiamante ha
    verificato che la riga e' seguita da una riga "Fase fenologica" (R2 debole).
    """
    t = t.strip(" :.")
    if not t or (not anche_minuscolo and not e_maiuscolo(t)):
        return None, t
    su = re.sub(r"\s+", " ", t.upper())
    if su in COLTURE:
        return COLTURE[su], t
    base = re.sub(r"\s*\(.*?\)\s*$", "", su).strip()
    return COLTURE.get(base), t


def pulisci(t: str) -> str:
    t = RE_IMG.sub(" ", t)
    t = re.sub(r"^[:\-–#*\s]+", "", t)
    t = re.sub(r"[#*\s]+$", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip(" .;")


def ha_vocabolario(t: str) -> bool:
    tl = t.lower()
    return any(v in tl for v in VOCABOLARIO)


def incoerenze(coltura: str, testo: str):
    tl = testo.lower()
    return sorted(
        k for k, ammesse in ESCLUSIVI.items() if k in tl and coltura not in ammesse
    )


def meta_file(nome: str):
    m = RE_FILE.match(nome)
    if not m:
        return None
    mese = MESI.get(m.group("m").lower())
    if not mese:
        return None
    area_raw = m.group("area").strip()
    tipo = "bollettino"
    area = area_raw
    if re.search(r"aggiornamento|irrigazion", area_raw, re.I):
        tipo = "aggiornamento_irrigazione"
        area = re.split(r"\s*[–\-]\s*Aggiornamento", area_raw, flags=re.I)[0].strip()
    chiave = re.sub(r"\s+", " ", area.lower()).replace("ì", "i").strip()
    if chiave not in AREE:
        return None
    nome_area, prov = AREE[chiave]
    return {
        "numero": int(m.group("num")),
        "bis": bool(m.group("bis")),
        "data": dt.date(int(m.group("a")), mese, int(m.group("g"))),
        "area": nome_area,
        "province": prov,
        "tipo": tipo,
    }


def testo_fase(righe, i, stessa, poppler):
    """(fase, riga_testo, stato, note) secondo R4 e R5."""
    t = pulisci(stessa or "")
    riga_testo = i + 1
    serve_seguito = (not t) or bool(SOSPESO.search(t))
    j = i + 1
    if poppler:
        # nel testo Poppler i paragrafi vanno a capo: una riga che prosegue in minuscolo,
        # corta e senza due punti e' la continuazione della stessa frase
        if t and j < len(righe) and righe[j].strip() and not serve_seguito:
            nx = nucleo(righe[j])
            if nx and nx[0].islower() and ":" not in nx and len(nx) <= 60:
                t = f"{t} {pulisci(nx)}"
                riga_testo = j + 1
    if serve_seguito:
        while j < len(righe) and not righe[j].strip():
            j += 1
        if j >= len(righe):
            return t, riga_testo, ("dubbia" if t else "assente"), "fine del file"
        grezza = righe[j].strip()
        nx = nucleo(grezza)
        m_art = re.match(r"^#+\s*:\s*(?P<x>.+)$", grezza)  # "## : testo" (artefatto)
        if m_art:
            nx = pulisci(m_art.group("x"))
        elif grezza.startswith("<!--") and not nx:
            return (
                t,
                riga_testo,
                ("dubbia" if t else "assente"),
                "segue immagine: fase persa nella conversione",
            )
        elif (
            grezza.startswith("#")
            and not e_maiuscolo(nx)
            and not coltura_da_intestazione(nx, True)[0]
            and nx.upper() not in AZZERA
            and ha_vocabolario(nx)
            and len(nx) <= 80
            and not t
        ):
            # Docling a volte converte la riga della fase in un titolo: "## accrescimento frutti"
            t = pulisci(nx)
            return (
                t,
                j + 1,
                "ok",
                "testo della fase in un titolo markdown (artefatto di conversione)",
            )
        elif (
            grezza.startswith("#")
            or coltura_da_intestazione(nx)[0]
            or nucleo(grezza).upper() in AZZERA
        ):
            return (
                t,
                riga_testo,
                ("dubbia" if t else "assente"),
                f"segue intestazione: {nx[:50]}",
            )
        if ETICHETTA.match(nx):
            return (
                t,
                riga_testo,
                ("dubbia" if t else "assente"),
                f"segue un'etichetta: {nx[:40]}",
            )
        if len(nx) > 110:
            return (
                t,
                riga_testo,
                ("dubbia" if t else "assente"),
                f"segue paragrafo: {nx[:50]}",
            )
        t = f"{t} {pulisci(nx)}".strip()
        riga_testo = j + 1
    if not t:
        return "", riga_testo, "assente", "testo vuoto"
    if len(t) > 160:
        return t[:160], riga_testo, "dubbia", "testo troppo lungo: paragrafo?"
    if SOSPESO.search(t):
        return t, riga_testo, "dubbia", "testo ancora sospeso dopo la continuazione"
    if not ha_vocabolario(t):
        return t, riga_testo, "dubbia", "nessun vocabolo fenologico"
    return t, riga_testo, "ok", ""


def estrai(nome: str, testo: str, fonte: str = "poppler"):
    """Righe di fase di un bollettino. `nome` e' il nome del file (R7), `testo` il suo testo con
    le pagine separate da \f e le righe vuote fra i paragrafi."""
    meta = meta_file(nome)
    if meta is None:
        return [{"fonte": fonte, "file": nome, "stato": "file_non_riconosciuto"}], 0, []
    poppler = fonte == "poppler"
    righe = [normalizza(l) for l in testo.split("\n")]
    out, maiuscole_ignote = [], []
    corrente = None  # dict(chiave, testo, riga, usata)
    n_strutturali = 0

    def emetti(riga_n, fase, riga_testo, stato, note):
        col = corrente["chiave"] if corrente else ""
        if stato == "ok" and col:
            inc = incoerenze(col, fase)
            if inc:
                stato, note = (
                    "incoerente",
                    f"termini di altre colture: {', '.join(inc)}",
                )
        out.append(
            {
                "fonte": fonte,
                "file": nome,
                "riga": riga_n,
                "riga_testo": riga_testo,
                "numero": meta["numero"],
                "bis": "BIS" if meta["bis"] else "",
                "data": meta["data"].isoformat(),
                "area": meta["area"],
                "province": "|".join(meta["province"]),
                "tipo_doc": meta["tipo"],
                "coltura": col,
                "intestazione": corrente["testo"] if corrente else "",
                "riga_intestazione": corrente["riga"] if corrente else "",
                "fase": fase,
                "stato": stato,
                "note": note,
            }
        )

    for i, riga in enumerate(righe):
        if not riga.strip():
            continue
        nu = nucleo(riga)
        if not nu:
            continue
        # (a) "COLTURA Fase fenologica: ..." sulla stessa riga
        mcf = RE_COLTURA_FASE.match(nu)
        if mcf:
            chiave, testo = coltura_da_intestazione(mcf.group("coltura"))
            if chiave:
                n_strutturali += 1
                corrente = {
                    "chiave": chiave,
                    "testo": testo,
                    "riga": i + 1,
                    "usata": True,
                }
                emetti(i + 1, *testo_fase(righe, i, mcf.group("testo"), poppler))
                continue
        # (b) riga che inizia con "Fase fenologica"
        mf = RE_FASE.match(nu)
        if mf:
            n_strutturali += 1
            fase, rt, stato, note = testo_fase(righe, i, mf.group("testo"), poppler)
            if corrente is None:
                stato, note = "senza_coltura", "nessuna intestazione di coltura prima"
                emetti(i + 1, fase, rt, stato, note)
            elif corrente["usata"]:
                emetti(
                    i + 1,
                    fase,
                    rt,
                    "seconda_fase_stessa_intestazione",
                    f"l'intestazione {corrente['testo']} (riga {corrente['riga']}) ha gia' una fase",
                )
            else:
                corrente["usata"] = True
                emetti(i + 1, fase, rt, stato, note)
            continue
        # (c) intestazioni (markdown o riga semplice)
        breve = len(nu) <= 70
        if breve:
            chiave, testo = coltura_da_intestazione(nu)
            if not chiave and not e_maiuscolo(nu):
                # R2 debole: "## Frumento" o "Soia" valgono solo se entro tre righe non vuote
                # arriva una riga "Fase fenologica"
                ch2, t2 = coltura_da_intestazione(nu, anche_minuscolo=True)
                if ch2 and prossima_e_fase(righe, i):
                    chiave, testo = ch2, t2
            if chiave:
                corrente = {
                    "chiave": chiave,
                    "testo": testo,
                    "riga": i + 1,
                    "usata": False,
                }
                continue
            su = re.sub(r"\s+", " ", nu.strip(" :.").upper())
            if su in AZZERA and e_maiuscolo(nu):
                corrente = None
                continue
            if riga.lstrip().startswith("#") and e_maiuscolo(nu):
                maiuscole_ignote.append((nome, i + 1, nu))
    return out, n_strutturali, maiuscole_ignote


def prossima_e_fase(righe, i, quante=3):
    visti = 0
    for j in range(i + 1, len(righe)):
        nu = nucleo(righe[j])
        if not nu:
            continue
        if RE_FASE.match(nu):
            return True
        visti += 1
        if visti >= quante:
            return False
    return False
