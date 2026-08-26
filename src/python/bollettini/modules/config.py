"""
Configurazione centralizzata multi-regione per RAG Colture.

Contiene:
- Caricamento della API key OpenAI da UNA sola fonte, fuori dal repo (load_openai_key)
- Dizionario regioni (aree, colture, URL)
- Dizionario colture completo (unione di tutte le regioni)
"""
import os
import re
from pathlib import Path

# ============= CREDENZIALI =============
# La API key NON vive nel progetto. Un solo punto di lettura per tutta la pipeline, cosi' la
# chiave sta in un posto e non si moltiplica in copie: e' esattamente il modo in cui la stessa
# chiave era finita in una decina di .env, dentro archivi di trasferimento e su OneDrive.
#
# Precedenza (la prima che risponde vince):
#   1. OPENAI_API_KEY gia' presente nell'ambiente  -> container, CI, systemd, `export` a mano.
#   2. il file indicato da OPENAI_KEY_FILE          -> override esplicito.
#   3. ~/.config/openai/key.env  (o $XDG_CONFIG_HOME/openai/key.env)  -> posizione canonica.
#   4. %APPDATA%\openai\key.env                    -> equivalente su Windows.
#   5. ~/.config/rag_colture/env                    -> alternativa per-progetto, sempre in home.
# Se nessuna risponde, si solleva un errore con le istruzioni: MAI un fallback dentro il repo.
_XDG = os.getenv("XDG_CONFIG_HOME")
_APPDATA = os.getenv("APPDATA")

def openai_key_candidates() -> list:
    """I file (fuori dal repo) in cui si cerca la chiave, in ordine di precedenza."""
    cand = []
    esplicito = os.getenv("OPENAI_KEY_FILE")
    if esplicito:
        cand.append(Path(esplicito).expanduser())
    cand.append(Path(_XDG).expanduser() / "openai" / "key.env" if _XDG
                else Path.home() / ".config" / "openai" / "key.env")
    if _APPDATA:
        cand.append(Path(_APPDATA) / "openai" / "key.env")
    cand.append(Path.home() / ".config" / "rag_colture" / "env")
    return cand


def load_openai_key(verbose: bool = False) -> str:
    """Popola os.environ['OPENAI_API_KEY'] leggendola dalla prima fonte disponibile.

    Ritorna una descrizione MASCHERATA della provenienza, adatta al log
    (es. "sk-proj-...Rb4A da ~/.config/openai/key.env"). Non ritorna mai la chiave.
    Solleva RuntimeError se non la trova, spiegando dove metterla.
    """
    from dotenv import load_dotenv  # import locale: config.py resta importabile senza dotenv

    origine = None
    if os.getenv("OPENAI_API_KEY"):
        origine = "variabile d'ambiente"
    else:
        for f in openai_key_candidates():
            if f.is_file():
                # override=False: l'ambiente ha sempre l'ultima parola (regola 1)
                load_dotenv(f, override=False)
                if os.getenv("OPENAI_API_KEY"):
                    origine = f"{f}"
                    _controlla_permessi(f)
                    break

    if not origine:
        percorsi = "\n  ".join(str(f) for f in openai_key_candidates())
        raise RuntimeError(
            "OPENAI_API_KEY non trovata. La chiave NON va messa nel progetto: creala in uno "
            f"di questi percorsi (permessi 600), con dentro `OPENAI_API_KEY=sk-...`:\n  {percorsi}\n"
            "Oppure esportala nell'ambiente, oppure indica il file con OPENAI_KEY_FILE."
        )

    _avvisa_se_chiave_nel_repo()
    k = os.environ["OPENAI_API_KEY"]
    descrizione = f"{k[:8]}...{k[-4:]} da {origine}"
    if verbose:
        print(f"Chiave OpenAI: {descrizione}")
    return descrizione


def _controlla_permessi(f: Path):
    """Avvisa se il file della chiave e' leggibile da altri utenti (solo POSIX)."""
    if os.name == "nt":
        return
    modo = f.stat().st_mode & 0o077
    if modo:
        print(f"ATTENZIONE: {f} e' leggibile da altri utenti. Correggi con: chmod 600 {f}")


def _avvisa_se_chiave_nel_repo():
    """Rete di sicurezza: segnala se una chiave ricompare in un .env dentro il repo."""
    for nome in (".env", ".env.local"):
        f = Path(__file__).resolve().parent.parent / nome
        try:
            testo = f.read_text(encoding="utf-8", errors="ignore") if f.is_file() else ""
            if re.search(r"sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{36}|github_pat_|AKIA[0-9A-Z]{16}", testo):
                print(f"ATTENZIONE: {f} contiene una credenziale. Le chiavi non vanno nel "
                      f"progetto (rischio di copie e di finire in archivi/cloud): spostala in "
                      f"~/.config/openai/key.env e cancella questo file.")
        except OSError:
            pass
# ==========================================


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
        "colture": ["VITE", "PERO", "PESCO", "MELO", "MAIS", "BARBABIETOLA"],
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
    # Nota: MELO (piu' sotto) e' usata da ENTRAMBE le regioni: negli ER l'header e' sempre
    # "MELO" secco, in Campania compaiono anche le varianti "COLTURA: MELO" ecc.
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
            # avversita' tipiche dei bollettini Emilia-Romagna
            "colpo di fuoco batterico", "erwinia amylovora",
            "glomerella", "colletotrichum",
            "afide lanigero", "eriosoma lanigerum",
            "carpocapsa", "cemiostoma", "litocollete", "eulia",
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
