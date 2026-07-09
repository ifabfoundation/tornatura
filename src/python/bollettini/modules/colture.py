"""
Modulo per query RAG su tutte le colture dei bollettini fitosanitari.

Estrae informazioni specifiche per ogni coltura usando:
- Filtraggio sezione-based (match esatto su section_title)
- Fallback keyword-based (solo se pochi risultati)
- Filtro anti-contaminazione (escludi sezioni altre colture)
- Generazione risposte con GPT-4o-mini

Supporta multi-regione (Emilia-Romagna, Campania).

Output: Report per ogni coltura in data/output_bollettini/{regione}/{coltura}/

Utilizzo:
    # Da scheduler (processa solo nuovi bollettini)
    processor = ColtureQueryProcessor()
    has_new, stats = processor.process_new_only()

    # Con filtro regione
    processor = ColtureQueryProcessor(regione="campania")
    has_new, stats = processor.process_new_only()

    # Da linea di comando
    python colture.py
"""

from pathlib import Path
from datetime import datetime
import json
import time
import shutil
import re
import markdown
from openai import OpenAI
from dotenv import load_dotenv
from bollettini import paths
from bollettini.modules.chunk_store import ChunkStore
import logging
from typing import List, Dict, Optional, Tuple

# ============= CONFIGURAZIONE =============
CHUNKSTORE_DB = paths.DATA_DIR / "chunks.db"
OUTPUT_DIR = paths.OUTPUT_DIR
CACHE_FILE = paths.DATA_DIR / "cache" / "colture_processed.json"
HISTORY_BASE_DIR = OUTPUT_DIR  # history lives under each regione/coltura dir

# Modello LLM
LLM_MODEL = "gpt-4o-mini"
# ==========================================


# ============= LOGGING (Lazy) =============
_logger = None

def get_logger():
    """Lazy logger initialization."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger(__name__)
        if not _logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            _logger.addHandler(handler)
            _logger.setLevel(logging.INFO)
    return _logger
# ==========================================


# ============= COLTURE DA CONFIG =============
from bollettini.modules.config import COLTURE, REGIONI, get_colture_per_regione, get_area_display_name
# ==========================================


# ============= SYSTEM PROMPT EMILIA-ROMAGNA (lean, struttura-first) =============
# Prompt dedicato all'ER (la Campania ha SYSTEM_PROMPT_CAMPANIA piu' sotto: i due contenuti sono
# opposti, l'unificazione e' stata testata e scartata perche' su Campania induceva fabbricazione).
# Filosofia: definire la STRUTTURA e pretendere FEDELTA' TOTALE, senza "spingere" il contenuto
# (niente elenchi di malattie/insetti, niente campi imposti). Si estrae TUTTO il crop-specifico
# senza perdere ne' inventare; le sezioni non legate alla coltura non si mettono. Il safety-net
# anti-perdita (lezione dei 391 fatti) e' la lista dei TIPI di dato da conservare "QUANDO
# presenti" — non un obbligo di emetterli.
SYSTEM_PROMPT = """Sei un redattore tecnico fitosanitario. Ricevi il testo di un bollettino
relativo a UNA coltura. Riorganizzalo nella struttura sotto, restando FEDELE: trasferisci TUTTE
le informazioni di QUELLA coltura cosi' come sono, senza perderne nessuna e senza aggiungerne.
Non riassumere; togli solo ripetizioni, intestazioni/pie' di pagina e frasi di collegamento.

PRINCIPIO — FEDELTA' TOTALE, NIENTE INVENZIONI:
- Riporta SOLO cio' che e' scritto nella fonte, ma riportalo TUTTO: se un dato non c'e', non
  scriverlo; se c'e', non perderlo.
- Conserva con precisione, QUANDO la fonte li riporta: date e scadenze; soglie di intervento
  (anche quantitative — ore di bagnatura, gradi-giorno, % — o diverse per varieta'); sostanze
  attive con i loro limiti (Max interventi, intervalli di sicurezza); i limiti CUMULATIVI per
  gruppo chimico o insieme di sostanze (es. "Tra gli SDHI Max 4", "Tra Ditianon e Captano Max
  16"); le sostanze candidate alla sostituzione (*); gli accorgimenti agronomici (es. taglio a
  una certa distanza dal sintomo, disinfezione attrezzi, fitotossicita'/distanziamenti); la
  salvaguardia delle api; le deroghe/usi eccezionali con le DATE e il loro significato esatto
  (distingui la data di CONCESSIONE da quella di SCADENZA/fine validita').
- NON imporre questi campi se la fonte non li contiene. Molte fonti (es. i bollettini Campania)
  danno consigli solo QUALITATIVI (es. "intervenire preventivamente con prodotti di copertura",
  senza numeri): riportali COSI' come sono. E' un ERRORE GRAVE aggiungere "Max interventi: N",
  "Intervallo di sicurezza: N giorni", soglie in % o qualsiasi altro numero quando la fonte NON
  lo riporta per quella voce: NON farlo MAI.
- Le TABELLE si COPIANO integralmente come tabelle markdown, riga per riga, senza aggiungerne,
  perderne o modificarne nessuna (es. tabelle rischio->prodotto, schemi di diserbo). UNICA
  ECCEZIONE: la tabella dei rilievi di monitoraggio in campo (colonne tipo Comune/Localita'/
  Varieta'/Stadio fenologico/Stato fitosanitario, tipica dei bollettini Campania) NON va
  riprodotta: viene inserita automaticamente.

STRUTTURA (usa questi titoli; OMETTI ogni sezione di cui la fonte non parla per questa coltura:
niente header vuoti, niente "nessuna indicazione"):

## Stato della coltura
Fase fenologica e situazione generale della coltura, se presenti.

## Avversita' e difesa
Una voce per ogni avversita' citata (malattia o insetto). Sotto ciascuna riporta FEDELMENTE cio'
che la fonte dice (stato, criteri agronomico/chimico/biologico, soglie, sostanze attive con i
loro limiti, accorgimenti), esattamente come scritto, senza inventarne e senza spostarli da
un'avversita' all'altra. Se la fonte raggruppa piu' agenti sotto un titolo, conservali TUTTI.
Suddividi in "### Malattie / Patogeni" (funghi, batteri, virus, fitoplasmi) e "### Insetti /
Acari / Fitofagi" (organismi animali).

## Difesa obbligatoria e scadenze
Solo se la fonte impone per QUESTA coltura misure di lotta OBBLIGATORIA / organismi da quarantena
(es. flavescenza dorata e il vettore scafoideo, colpo di fuoco, estirpi obbligatori). E' lotta
obbligatoria: riporta TUTTO il protocollo senza comprimere — organismo e riferimento normativo;
la SEQUENZA e il numero dei trattamenti con le DATE/finestre temporali esatte; le sostanze ammesse
coi relativi Max; le fasce di rispetto; le precondizioni; la salvaguardia delle api; gli estirpi.

## Pratiche agronomiche
Solo se la fonte da' indicazioni agronomiche per QUESTA coltura: successione/rotazione,
fertilizzazione, diserbo (lista COMPLETA delle sostanze erbicide come da documento, coi gruppi
chimico/HRAC se indicati), irrigazione/gestione del suolo, cautele operative.

## Vincoli e deroghe
Solo se citati per QUESTA coltura:
- limiti annuali e CUMULATIVI per gruppo chimico o sostanza: riportali TUTTI (es. "Tra gli SDHI
  Max 4", "Tra gli IBE Max 6", "Tra Ditianon e Captano Max 16", "Tra Fosetil Al e Fosfonato di K
  Max 10", tetti tipo "max 3 interventi insetticidi/anno"). Se la fonte li RIPETE piu' volte,
  raccoglili UNA sola volta ma senza ometterne NESSUNO;
- sostanze candidate alla sostituzione (*);
- deroghe/usi eccezionali con prodotto + sostanza attiva + DATE (concessione e scadenza, distinte).

## Note operative
2-4 azioni prioritarie della settimana, in bullet di una riga (richiami sintetici).

REGOLE
- Una sola coltura: ignora ogni riferimento ad ALTRE colture e le regole generali NON riferite a
  questa coltura.
- Fedelta' assoluta: nessuna invenzione e nessuna perdita. Niente placeholder ([N/A],
  [da verificare], [non specificato]): ometti la voce.
- Ogni avversita' compare UNA sola volta (Malattie OPPURE Insetti). Un organismo a lotta
  obbligatoria: stato in "Avversita' e difesa", protocollo in "Difesa obbligatoria e scadenze".
- Se la fonte non ha informazioni su questa coltura, scrivi un solo paragrafo: "Nessuna
  informazione specifica per questa coltura in questo bollettino." e ometti le sezioni."""

QUERY_TEMPLATE = """Coltura: {coltura_nome}
Bollettino del {data} - {province}

DOCUMENTI:
{context}

---
Estrai e riorganizza TUTTE le informazioni della coltura {coltura_nome} presenti nei documenti,
nel formato richiesto, senza perderne e senza inventarne."""
# ==========================================


# ============= VERIFICA / REVISIONE (rete anti-perdita e anti-allucinazione) =============
VERIFY_PROMPT = """Confronti la FONTE (estratto di un bollettino fitosanitario per una coltura)
con il REPORT generato. Il REPORT deve preservare TUTTI i fatti operativi della FONTE ed essere
FEDELE (niente di inventato).

IGNORA la tabella di monitoraggio (rilievi in campo): e' gestita separatamente e inserita
verbatim -- NON segnalare righe di monitoraggio mancanti, in piu' o alterate.

Individua i fatti IMPORTANTI presenti nella FONTE ma MANCANTI o ALTERATI nel REPORT:
- avversita' non riportate, o AGENTI persi quando la fonte ne raggruppa piu' d'uno sotto un titolo;
- date e scadenze; soglie (anche quantitative o per varieta'); sostanze attive con Max interventi
  e intervalli di sicurezza; limiti CUMULATIVI per gruppo chimico ("Tra gli SDHI Max 4", ecc.);
  accorgimenti agronomici e salvaguardia delle api;
- deroghe/usi eccezionali con le date e il loro significato (concessione vs scadenza);
- trattamenti/misure obbligatorie ed estirpi; righe di tabella NON-di-monitoraggio omesse.

Individua le AFFERMAZIONI del REPORT NON supportate dalla FONTE (allucinazioni), sempre da segnalare:
- valori numerici (soglie, "Max interventi: N", "Intervallo di sicurezza: N giorni") non presenti;
- sostanze, date o livelli di rischio non presenti; date di deroga col significato invertito;
- criteri/soglie/campionamenti attribuiti a un'avversita' diversa da quella della fonte.

Ignora le differenze di sola forma, prosa, ordine o sintesi non sostanziale.

Rispondi SOLO con JSON valido nella forma:
{"mancanti": ["fatto operativo mancante 1", "..."], "errati": ["affermazione errata 1", "..."]}
Se non manca nulla e non c'e' nulla di errato: {"mancanti": [], "errati": []}."""

REVISE_PROMPT = """Ti vengono dati: la FONTE, il REPORT attuale e una lista di CORREZIONI
(fatti MANCANTI da integrare e affermazioni ERRATE da rimuovere/correggere).
Restituisci il REPORT CORRETTO rispettando queste regole:
- mantieni la stessa struttura di sezioni e lo stesso stile del report attuale;
- AGGIUNGI i fatti mancanti nelle sezioni appropriate, fedeli alla FONTE;
- RIMUOVI o correggi le affermazioni errate;
- NON rimuovere nulla di corretto gia' presente; NON inventare nulla che non sia nella FONTE;
- le tabelle restano tabelle markdown complete.
Restituisci SOLO il report markdown corretto, senza commenti o preamboli."""
# =========================================================================================


# ============= PROMPT CAMPANIA (separato dall'ER per necessita') =============
# ER e Campania hanno contenuti OPPOSTI: ER quantitativo/regolatorio (soglie, Max interventi,
# limiti cumulativi, deroghe), Campania per lo piu' QUALITATIVO (consigli senza numeri). Un prompt
# unico NON funziona: l'enfasi ER su "preserva Max/intervalli/limiti" (necessaria al recall ER) e'
# proprio cio' che induce gpt-4o-mini a INVENTARE numeri/soglie e a riempire di placeholder le
# sezioni regolatorie sulla Campania (verificato: re-introduce il bug SA VITE). Quindi: prompt
# Campania dedicato, struttura-first, che VIETA l'invenzione di numeri. La tabella di monitoraggio
# resta iniettata dal codice (inject_monitoring).
SYSTEM_PROMPT_CAMPANIA = """Sei un redattore tecnico fitosanitario. Ricevi il testo di un
bollettino relativo a UNA coltura. Riorganizzalo nella struttura indicata sotto, restando
FEDELE: trasferisci le informazioni cosi' come sono, senza aggiungere e senza perdere nulla.
Non riassumere; togli solo ripetizioni, intestazioni/pie' di pagina e frasi di collegamento.

PRINCIPIO (il piu' importante): riporta SOLO cio' che e' scritto nella fonte. Non aggiungere
campi, numeri, soglie, sostanze, date, livelli di rischio o consigli che la fonte non contiene.
Se la fonte e' qualitativa, resta qualitativo. Se un dato non c'e', non scriverlo. Le TABELLE si
COPIANO integralmente come tabelle markdown, riga per riga, senza aggiungerne, perderne o
modificarne nessuna.

STRUTTURA (usa questi titoli; OMETTI ogni sezione di cui la fonte non parla: niente header
vuoti, niente "nessuna indicazione"):

## Stato della coltura
Riporta eventuali note testuali sulla fase fenologica o sulla situazione generale presenti nella
fonte. NON riprodurre qui la tabella dei rilievi di monitoraggio: viene inserita automaticamente
sotto un sotto-titolo "### Monitoraggio". Se non ci sono note testuali oltre alla tabella, scrivi
solo l'header della sezione.

## Avversita' e difesa
Una voce per ogni avversita' citata. Sotto ciascuna, riporta FEDELMENTE cio' che la fonte dice:
stato, criteri di difesa (agronomico/chimico/biologico), soglie, sostanze attive, campionamenti,
accorgimenti, limiti -- esattamente come scritti, senza inventarne e senza spostarli da
un'avversita' all'altra. Se la fonte raggruppa piu' agenti/avversita' sotto un titolo,
conservali TUTTI. Puoi suddividere in "### Malattie" e "### Insetti/Acari".

## Difesa obbligatoria
Solo se la fonte cita obblighi di legge, lotta obbligatoria o organismi da quarantena:
organismo, azione richiesta, riferimenti/scadenze citati.

## Altre indicazioni
Solo se presenti nella fonte: pratiche agronomiche generali, vincoli annuali/cumulativi,
deroghe/usi eccezionali con le loro date esatte. Riportale come sono.

## Note operative
2-4 azioni prioritarie della settimana, bullet di una riga (richiami sintetici).

REGOLE
- Una sola coltura: ignora ogni riferimento ad altre colture.
- Fedelta' assoluta: nessuna invenzione (vedi PRINCIPIO). Niente placeholder ([N/A],
  [da verificare], [non specificato]) e niente frasi tipo "non sono previsti / non specificato":
  se manca, OMETTI la voce o la sezione.
- Classifica: funghi/batteri/virus/fitoplasmi = malattie; organismi animali = insetti/acari.
- Se la fonte non ha informazioni sulla coltura, scrivi un solo paragrafo: "Nessuna informazione
  specifica per questa coltura in questo bollettino." """

QUERY_TEMPLATE_CAMPANIA = """Coltura: {coltura_nome}
Bollettino del {data}
Province: {province}

DOCUMENTI:
{context}

---
Estrai TUTTE le informazioni della coltura {coltura_nome} presenti nel bollettino (tabella di
monitoraggio + malattie e insetti con i relativi consigli di difesa agronomico/chimico/biologico),
riportandole FEDELMENTE nel formato richiesto. NON inventare numeri, soglie, intervalli di
sicurezza o max interventi non presenti nella fonte."""

VERIFY_PROMPT_CAMPANIA = """Confronti la FONTE (estratto di un bollettino fitosanitario della
Campania per una coltura) con il REPORT generato. Il REPORT deve preservare TUTTI i fatti della
FONTE ed essere FEDELE (niente di inventato).

IGNORA COMPLETAMENTE la tabella di monitoraggio (rilievi in campo): e' gestita separatamente e
inserita verbatim, quindi NON segnalare righe di monitoraggio mancanti, in piu' o alterate.

Individua i fatti IMPORTANTI presenti nella FONTE ma MANCANTI o ALTERATI nel REPORT:
- avversita' (malattie/insetti) non riportate, o AGENTI persi quando la fonte ne raggruppa piu'
  d'uno sotto un titolo (es. Xylella, Cytospora, Phytophthora spp.);
- criteri Agronomico/Chimico/Biologico, soglie, percentuali, metodi di campionamento, elenchi di
  sostanze attive, limiti ("al massimo N interventi") presenti nella fonte e non riportati;
- procedure obbligatorie / organismi da quarantena (Xylella, Flavescenza dorata) non riportati.

Individua le AFFERMAZIONI del REPORT NON supportate dalla FONTE (allucinazioni). Sono
particolarmente GRAVI e vanno SEMPRE segnalate:
- "Intervallo di sicurezza: N giorni", "Max interventi: N", "Soglia: ..." o qualunque valore
  numerico NON presente nella fonte;
- sostanze attive, date, livelli di rischio non presenti nella fonte;
- criteri/soglie/campionamenti attribuiti a un'avversita' diversa da quella della fonte.

Ignora le differenze di sola forma, ordine o prosa.

Rispondi SOLO con JSON valido nella forma:
{"mancanti": ["fatto mancante 1", "..."], "errati": ["affermazione inventata 1", "..."]}
Se non manca nulla e non c'e' nulla di errato: {"mancanti": [], "errati": []}."""
# ============================================================================


def parse_date_from_filename(filename: str) -> Optional[datetime]:
    """Estrae la data dal nome file nel formato DD-MM-YYYY."""
    match = re.search(r'(\d{2})-(\d{2})-(\d{4})\.md$', filename)
    if match:
        giorno, mese, anno = match.groups()
        return datetime(int(anno), int(mese), int(giorno))
    return None


def move_to_history(file_path: Path, province_slug: str, coltura_dir: Path, logger) -> bool:
    """
    Sposta un file report (MD e HTML) nella cartella history.

    Struttura: {coltura_dir}/history/{anno}/{provincia}/{DD-MM-YYYY.md}
    """
    if not file_path.exists():
        return False

    file_date = parse_date_from_filename(file_path.name)
    if not file_date:
        logger.warning(f"  Impossibile estrarre data da {file_path.name}, skip history")
        return False

    anno = str(file_date.year)

    history_path = coltura_dir / "history" / anno / province_slug
    history_path.mkdir(parents=True, exist_ok=True)

    # Nome file in history: solo la data (DD-MM-YYYY.md)
    date_str = file_path.name.split('_')[-1]  # "01-10-2025.md"
    dest_path = history_path / date_str

    shutil.move(str(file_path), str(dest_path))
    logger.info(f"  → History: {dest_path.relative_to(OUTPUT_DIR)}")

    # Sposta anche il file HTML se esiste
    html_path = file_path.with_suffix('.html')
    if html_path.exists():
        html_dest = dest_path.with_suffix('.html')
        shutil.move(str(html_path), str(html_dest))

    return True


def find_existing_report(province_slug: str, coltura_dir: Path) -> Optional[Path]:
    """Trova un report esistente per la provincia nella cartella coltura."""
    pattern = f"{province_slug}_*.md"
    existing = list(coltura_dir.glob(pattern))
    existing = [f for f in existing if "history" not in str(f)]
    if existing:
        return existing[0]
    return None


def convert_md_to_html(md_content: str, title: str) -> str:
    """Converte contenuto Markdown in HTML con stile CSS."""
    html_body = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code']
    )

    html_template = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #e67e22;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #e67e22;
            padding-left: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #e67e22;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        strong {{
            color: #2c3e50;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 30px 0;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin: 8px 0;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .footer {{
            font-size: 0.85em;
            color: #7f8c8d;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    return html_template


def normalize_province_slug(province: str) -> str:
    """Normalizza il nome della provincia per il nome file."""
    slug = province.lower().replace(' ', '_').replace(',', '_').replace('-', '_').replace('/', '_')
    slug = slug.replace('à', 'a').replace('è', 'e').replace('ì', 'i').replace('ò', 'o').replace('ù', 'u')
    while '__' in slug:
        slug = slug.replace('__', '_')
    return slug.strip('_')


def section_matches(section_title: str, sezioni: List[str]) -> bool:
    """
    Match esatto o prefix-match con word boundary.

    Esempi:
      "BARBABIETOLA DA ZUCCHERO" matcha sezione "BARBABIETOLA"
      "PESCO E NETTARINE" matcha sezione "PESCO"
      "PEROXIDE" NON matcha sezione "PERO"
    """
    # Strip annotazioni "(+N sezioni)" che il chunker aggiunge ai titoli mergiati
    st = re.sub(r'\s*\(\+\d+\s+sezion[ei]\)\s*', '', section_title).upper().strip()
    if not st:
        return False
    for s in sezioni:
        su = s.upper().strip()
        if st == su or st.startswith(su + " "):
            return True
    return False


def looks_like_coltura_heading(section_title: str) -> bool:
    """
    Euristica: titoli SHORT in MAIUSCOLO sono nomi di colture o sotto-colture.
    Usato per escludere sezioni di colture NON configurate (ALBICOCCO, NOCE,
    PATATA, ERBA MEDICA, etc.) dal fallback keyword.
    """
    st = re.sub(r'\s*\(\+\d+\s+sezion[ei]\)\s*', '', section_title).strip()
    if not st:
        return False
    # Tutto uppercase, max 5 parole, alfabetico
    if len(st.split()) <= 5 and st == st.upper() and any(c.isalpha() for c in st):
        return True
    return False


def is_other_coltura_section(section_title: str, current_coltura_id: str) -> bool:
    """
    Verifica se una sezione appartiene a un'ALTRA coltura.

    1. Match contro sezioni di colture configurate (escluse correnti)
    2. Euristica: titolo MAIUSCOLO short non appartenente alla coltura corrente
       → probabilmente un'altra coltura non configurata (ALBICOCCO, NOCE, ...)
    """
    current_sezioni = COLTURE.get(current_coltura_id, {}).get("sezioni", [])

    # 1. Sezione esplicita di altra coltura configurata
    for coltura_id, coltura_data in COLTURE.items():
        if coltura_id == current_coltura_id:
            continue
        if section_matches(section_title, coltura_data["sezioni"]):
            return True

    # 2. Euristica: titolo MAIUSCOLO breve che non matcha la coltura corrente
    if looks_like_coltura_heading(section_title) and not section_matches(section_title, current_sezioni):
        return True

    return False


# ============= FILTRO DEROGHE PER-VOCE (sezioni trasversali "a lista") =============
# Termini-coltura CURATI per il match delle voci-deroga (le 5 colture ER).
# Curati per evitare ambiguita': es. BARBABIETOLA usa solo 'barbabietola' e NON 'bietola',
# perche' 'bietola da foglia' (bietola da costa) e' un'ALTRA coltura. Per PESCO includiamo le
# varianti di genere/numero (nettarino/nettarina/nettarine) che la derivazione automatica
# perderebbe. Per colture non in mappa si ricade sulla derivazione automatica da config.
DEROGA_TERMS = {
    "VITE": {"vite", "vigneto"},
    "PERO": {"pero"},
    "PESCO": {"pesco", "pesche", "nettarine", "nettarina", "nettarino"},
    "MAIS": {"mais", "granoturco"},
    "BARBABIETOLA": {"barbabietola"},
}
_DEROGA_STOPWORDS = {"zucchero", "industria", "semi", "forzata", "semiforzata", "bietola"}


def coltura_match_terms(coltura_id: str) -> set:
    """
    Termini (nomi-coltura) per riconoscere quando una voce-deroga nomina questa coltura.
    Usa la mappa curata DEROGA_TERMS se presente; altrimenti deriva da `nome` + `sezioni`
    di config (nomi-coltura, NON keyword-malattia), escludendo token ambigui.
    """
    if coltura_id in DEROGA_TERMS:
        return set(DEROGA_TERMS[coltura_id])
    c = COLTURE.get(coltura_id, {})
    terms = set()
    for s in [c.get("nome", "")] + c.get("sezioni", []):
        s = re.sub(r"COLTURA[\s:]*", " ", s, flags=re.I)
        for tok in re.findall(r"[a-zàèéìòù]{4,}", s.lower()):
            if tok not in _DEROGA_STOPWORDS:
                terms.add(tok)
    return terms


def filter_deroghe_per_voce(content: str, coltura_id: str) -> str:
    """
    Spezza una sezione-lista (DEROGHE) in singole voci ('In data <gg> <mese> ... e' stata
    concessa ...') e tiene SOLO le voci che nominano la coltura (match per parola intera sui
    nomi-coltura). Deterministico: niente voci di altre colture (no mis-attribuzione), niente
    voci pertinenti perse (no top-k). Ritorna le voci tenute (o "" se nessuna).
    """
    terms = coltura_match_terms(coltura_id)
    if not terms:
        return ""
    pats = [re.compile(rf"\b{re.escape(t)}\b", re.I) for t in terms]
    # Split robusto: prima di ogni "In data <numero>" ovunque compaia (gestisce anche le voci
    # non a inizio riga o precedute da artefatti di pagina <!-- image --> / intestazioni).
    items = re.split(r"(?=\bIn\s+data\s+\d{1,2})", content)
    kept = [
        it.strip() for it in items
        if re.match(r"In\s+data\s+\d", it.strip()) and any(p.search(it) for p in pats)
    ]
    if not kept:
        return ""
    return ("## Deroghe e usi eccezionali pertinenti alla coltura\n\n" + "\n\n".join(kept))
# ===================================================================================


# ============= STRIP CODA ISTITUZIONALE CAMPANIA =============
# I bollettini Campania chiudono con sezioni BULLETIN-WIDE (non di coltura) che il chunker
# attribuisce all'ULTIMA coltura del documento, contaminandola: controlli/taratura attrezzature,
# AVVISI di sostanze in scadenza, tabella generale di Deroghe territoriali (cita molte colture),
# firma redazionale e data del prossimo bollettino. Vanno rimosse a monte: altrimenti rientrano
# anche via il pass di verifica (le vede come "fatti mancanti" e le re-inietta).
CAMPANIA_APPENDIX_MARKERS = [
    r"Controlli\s+delle\s+attrezzature",
    r"Piano\s+nazionale\s+sull[''’]uso\s+sostenibile",
    r"Saranno\s+in\s+scadenza",
    r"##\s*AVVISI\b",
    r"##\s*DEROGHE\b",
    r"Deroghe\s+territoriali",
    r"Il\s+presente\s+Bollettino\s+[eè]\s+stato\s+redatto",
    r"Il\s+prossimo\s+bollettino",
]
_CAMPANIA_APPENDIX_RE = re.compile("|".join(CAMPANIA_APPENDIX_MARKERS), re.I)


def strip_campania_appendix(content: str) -> str:
    """Taglia la coda istituzionale del bollettino Campania (vedi sopra), restituendo il
    contenuto fino al PRIMO marcatore della coda. I marcatori compaiono sempre DOPO il
    contenuto delle colture, quindi il taglio preserva l'informazione di coltura."""
    m = _CAMPANIA_APPENDIX_RE.search(content)
    return content[:m.start()].rstrip() if m else content
# =============================================================


# ============= TABELLA MONITORAGGIO DETERMINISTICA (Campania) =============
# La tabella di monitoraggio (rilievi in campo) e' dato STRUTTURATO: farla "ricopiare" all'LLM
# produce righe inventate/perse (osservato su SA OLIVO: 2 righe -> 3). Qui la estraiamo verbatim
# dal markdown della fonte e la iniettiamo nel report, bypassando l'LLM: e' l'estrazione piu'
# fedele possibile. Il monitoraggio in Campania precede sempre i "CONSIGLI DI DIFESA".
_TABLE_SEP_RE = re.compile(r"^\|?[\s|:\-]+\|?$")


def _normalize_md_table(block: List[str]) -> str:
    """Assicura il separatore markdown dopo l'header: alcune tabelle Campania ne sono prive e
    senza di esso il markdown non renderizza come tabella. Tutto il resto resta verbatim."""
    lines = [l for l in block if l.strip()]
    header = lines[0]
    rest = lines[1:]
    if rest and _TABLE_SEP_RE.match(rest[0].strip()):
        return "\n".join(lines)  # separatore gia' presente
    ncols = len(header.strip().strip("|").split("|"))
    sep = "|" + "|".join(" --- " for _ in range(ncols)) + "|"
    return "\n".join([header, sep] + rest)


def _table_data_rows(block: List[str]) -> int:
    """Conta le righe con contenuto reale in un blocco-tabella (header+separatore esclusi se
    'vuoti'): una riga conta se ha almeno una cella con caratteri alfanumerici."""
    n = 0
    for ln in block:
        s = ln.strip()
        if not s or _TABLE_SEP_RE.match(s):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if any(re.search(r"[A-Za-z0-9]", c) for c in cells):
            n += 1
    return n


def extract_campania_monitoring(source_text: str) -> Optional[str]:
    """Estrae VERBATIM la tabella di monitoraggio dalla fonte Campania.

    Strategia: guarda solo la parte PRIMA di 'CONSIGLI DI DIFESA' (dove sta il monitoraggio),
    raggruppa le righe-tabella contigue in blocchi, e restituisce il blocco con piu' righe-dati
    reali (header + >=1 riga). Le tabelle con sola intestazione (es. blocchi UTM vuoti) hanno
    0 righe-dati e vengono scartate. Ritorna None se non c'e' una tabella con dati reali.
    """
    m = re.search(r"CONSIGLI\s+DI\s+DIFESA", source_text, re.I)
    head = source_text[:m.start()] if m else source_text
    blocks, cur = [], []
    for ln in head.splitlines():
        if ln.lstrip().startswith("|"):
            cur.append(ln.rstrip())
        elif cur:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    if not blocks:
        return None
    best = max(blocks, key=lambda b: (_table_data_rows(b), len(b)))
    # serve almeno header + 1 riga-dati reale
    if _table_data_rows(best) < 2:
        return None
    return _normalize_md_table(best)


def inject_monitoring(report: str, monit_table: str) -> str:
    """Inserisce la tabella di monitoraggio (verbatim) come sotto-sezione '### Monitoraggio'
    dentro '## Stato della coltura'. Per robustezza rimuove dalla sezione Stato QUALSIASI
    riga-tabella e sotto-header '### Monitoraggio' eventualmente prodotti dall'LLM (che a volte
    duplica la tabella nonostante le istruzioni), poi appende la tabella deterministica. Se la
    sezione Stato manca, la crea in testa al report."""
    block = f"### Monitoraggio\n\n{monit_table}\n"
    m = re.search(r"(?im)^##\s+Stato della coltura[ \t]*$", report)
    if not m:
        return f"## Stato della coltura\n\n{block}\n{report.lstrip()}"
    start = m.end()
    nxt = re.search(r"(?m)^##\s+", report[start:])
    end = start + nxt.start() if nxt else len(report)
    sezione = report[start:end]
    # togli righe-tabella e sotto-header Monitoraggio dalla sola sezione Stato
    kept = [
        ln for ln in sezione.splitlines()
        if not ln.lstrip().startswith("|")
        and not re.match(r"(?i)^\s*###\s+Monitoraggio\s*$", ln)
    ]
    sezione_clean = "\n".join(kept).strip()
    new_section = (sezione_clean + "\n\n" if sezione_clean else "") + block
    return report[:start].rstrip() + "\n\n" + new_section + "\n" + report[end:].lstrip()
# ==========================================================================


class ColtureQueryProcessor:
    """
    Processore query RAG per tutte le colture.

    Genera report per ogni coltura trovata nel bollettino.
    Usa retrieval sezione-based con fallback keyword.
    Supporta filtro per regione.
    """

    def __init__(self, regione: str = None):
        """
        Args:
            regione: ID regione (es. "emilia_romagna", "campania").
                     Se None, processa tutte le regioni.
        """
        self.logger = get_logger()
        self.regione = regione

        # Filtra colture per regione
        if regione:
            self.colture = get_colture_per_regione(regione)
            if not self.colture:
                self.logger.warning(f"Nessuna coltura configurata per regione '{regione}'")
                self.colture = COLTURE
        else:
            self.colture = COLTURE

        # Cache separata per regione
        if regione:
            self._cache_file = paths.DATA_DIR / "cache" / f"colture_{regione}_processed.json"
        else:
            self._cache_file = CACHE_FILE
        self.cache = self._load_cache()

        # Lazy loading
        self._openai_client = None
        self._store = None

        # Pass di verifica/revisione anti-perdita e anti-allucinazione (vedi docs/redesign_er.md)
        self.verify = True

    # ============= CACHE MANAGEMENT =============

    def _load_cache(self) -> dict:
        """Carica cache dei bollettini già processati per ogni coltura."""
        if self._cache_file.exists():
            try:
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Errore caricamento cache: {e}")
        return {"processed": {}, "last_run": None}

    def _save_cache(self):
        """Salva cache su disco."""
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache["last_run"] = datetime.now().isoformat()
        with open(self._cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def _get_cache_key(self, doc_name: str, coltura_id: str) -> str:
        """Genera chiave cache per combinazione bollettino+coltura."""
        return f"{doc_name}::{coltura_id}"

    def _mark_processed(self, doc_name: str, coltura_id: str, output_file: str):
        """Segna una combinazione bollettino+coltura come processata."""
        cache_key = self._get_cache_key(doc_name, coltura_id)
        self.cache["processed"][cache_key] = {
            "processed_at": datetime.now().isoformat(),
            "output_file": output_file
        }
        # Non salvare qui, salva alla fine del batch

    def is_processed(self, doc_name: str, coltura_id: str) -> bool:
        """Verifica se una combinazione è già stata processata."""
        cache_key = self._get_cache_key(doc_name, coltura_id)
        return cache_key in self.cache.get("processed", {})

    def clear_cache(self):
        """Pulisce la cache (forza riprocessamento)."""
        self.cache = {"processed": {}, "last_run": None}
        self._save_cache()
        self.logger.info("Cache cleared")

    # ============= LAZY MODEL LOADING =============

    def _init_models(self):
        """Inizializza modelli solo quando necessario."""
        if self._openai_client is None:
            load_dotenv()

            self.logger.info("Initializing OpenAI client...")
            # timeout per chiamata + retry con backoff: evita hang indefiniti e
            # assorbe i rate-limit transitori senza bloccare la pipeline.
            self._openai_client = OpenAI(timeout=60.0, max_retries=4)

            self.logger.info(f"Apertura ChunkStore: {CHUNKSTORE_DB}")
            self._store = ChunkStore(CHUNKSTORE_DB)

    # ============= BOLLETTINI RETRIEVAL =============

    def get_available_bollettini(self) -> List[Dict]:
        """Recupera lista bollettini disponibili dal ChunkStore, con filtro regione."""
        self._init_models()

        all_docs = self._store.get_all(self.regione)

        bollettini_map = {}
        for meta in all_docs['metadatas']:
            doc_name = meta.get('doc_name', '')
            province = meta.get('province', '')
            numero = meta.get('numero_bollettino', None)
            data = meta.get('data', '')
            regione = meta.get('regione', 'emilia_romagna')

            if (doc_name
                and doc_name not in bollettini_map
                and province):
                # Per Campania: numero_bollettino puo' essere None
                # Per ER: deve avere numero
                if regione == 'campania' or (numero is not None and numero != ''):
                    bollettini_map[doc_name] = {
                        'doc_name': doc_name,
                        'province': province,
                        'numero_bollettino': numero,
                        'data': data,
                        'regione': regione,
                    }

        return list(bollettini_map.values())

    def get_latest_bollettini_by_province(self) -> List[Dict]:
        """Recupera solo l'ultimo bollettino per ogni provincia."""
        bollettini = self.get_available_bollettini()

        def _safe_numero(val):
            """Converte numero_bollettino in int, gestendo None e '' (Campania)."""
            if val is None or val == '':
                return 0
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        latest_by_province = {}
        for b in bollettini:
            province = b['province']
            sort_key = (b.get('data', ''), _safe_numero(b.get('numero_bollettino')))
            if province not in latest_by_province:
                latest_by_province[province] = b
            else:
                existing = latest_by_province[province]
                existing_key = (existing.get('data', ''), _safe_numero(existing.get('numero_bollettino')))
                if sort_key > existing_key:
                    latest_by_province[province] = b

        return list(latest_by_province.values())

    # ============= RETRIEVAL (SEZIONE + PARENT_COLTURA) =============

    def _retrieve_coltura_chunks(self, results: Dict, coltura_id: str) -> List[Dict]:
        """
        Recupera chunks che contengono informazioni sulla coltura specifica.

        Accetta i chunks del bollettino già pre-caricati (fetch ChromaDB unico
        per bollettino in process_bollettino, riusato per tutte le colture).

        Strategia unica (entrambe le regioni usano slice-by-coltura):
        - Match esatto su section_title (es. "VITE", "BARBABIETOLA DA ZUCCHERO")
        - OR match su parent_coltura == coltura_id (per chunks con titoli generici
          attribuiti via tracking del preprocess).
        Ogni chunk contiene gia' tutto il contenuto della coltura (Difesa, Diserbo,
        Tecniche, Vincoli, ecc.) grazie alla pipeline slice + merge consecutivi.
        """
        coltura = self.colture[coltura_id]
        sezioni = coltura["sezioni"]

        own_chunks = []       # blocchi propri della coltura (section/parent)
        cross_chunks = []     # sezioni trasversali applicabili (solo enrichment)
        seen_contents = set()  # Evita duplicati

        for doc, meta in zip(results['documents'], results['metadatas']):
            section_title = meta.get('section_title', '')
            parent = meta.get('parent_coltura', '')
            applies_to = meta.get('applies_to', '')

            # Campania: rimuovi la coda istituzionale che il chunker accoda all'ultima coltura
            # (controlli attrezzature, AVVISI, deroghe territoriali generali, firma redazionale).
            if meta.get('regione') == 'campania':
                doc = strip_campania_appendix(doc)

            # Trasversale "a lista" (DEROGHE): filtro per-voce deterministico.
            if applies_to == "PER_VOCE":
                filtered = filter_deroghe_per_voce(doc, coltura_id)
                if filtered.strip():
                    cross_chunks.append({
                        "content": filtered,
                        "metadata": meta,
                        "match_type": "trasversale",
                    })
                continue

            match_section = section_matches(section_title, sezioni)
            match_parent = parent == coltura_id
            # Trasversali: valgono per questa coltura (o per "ALL")
            match_cross = bool(applies_to) and (
                applies_to == "ALL"
                or coltura_id in [a.strip() for a in applies_to.split(',')]
            )

            content_key = doc[:200]
            if match_section or match_parent:
                if content_key not in seen_contents:
                    seen_contents.add(content_key)
                    own_chunks.append({
                        "content": doc,
                        "metadata": meta,
                        "match_type": "section" if match_section else "parent",
                    })
            elif match_cross:
                cross_chunks.append({
                    "content": doc,
                    "metadata": meta,
                    "match_type": "trasversale",
                })

        # Le sezioni trasversali ENRICHISCONO solo una coltura che ha gia' un blocco
        # proprio nel bollettino. Se la coltura non e' presente (nessun blocco proprio),
        # ritorna vuoto -> report statico "Nessuna informazione" (no resurrezione di
        # colture fuori stagione da solo contenuto generale).
        if not own_chunks:
            return []

        for c in cross_chunks:
            content_key = c["content"][:200]
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                own_chunks.append(c)

        return own_chunks

    # ============= LLM GENERATION =============

    def _generate_report(self, bollettino: Dict, coltura_id: str, chunks: List[Dict]) -> str:
        """Genera report per una coltura specifica."""
        coltura = self.colture[coltura_id]

        # Prepara contesto
        context = ""
        for chunk in chunks:
            meta = chunk['metadata']
            section = meta.get('section_title', 'Generale')
            match_type = chunk.get('match_type', 'unknown')
            if match_type == "trasversale":
                context += (
                    f"\n--- [{section}] (SEZIONE TRASVERSALE: vale per piu' colture; "
                    f"riporta SOLO cio' che riguarda {coltura['nome']}, ignorando le altre colture) ---\n"
                )
            else:
                context += f"\n--- [{section}] ---\n"
            context += chunk['content']
            context += "\n"

        numero = bollettino.get('numero_bollettino')
        numero_str = str(numero) if numero else "N/D"

        # Prompt PER-REGIONE: ER (quantitativo/regolatorio) e Campania (qualitativo) hanno
        # contenuti opposti -> un prompt unico induce fabbricazione di numeri sulla Campania
        # (verificato). Due prompt dedicati. La tabella di monitoraggio Campania resta iniettata
        # dal codice (sotto), fuori dal prompt.
        regione = bollettino.get('regione', 'emilia_romagna')
        is_campania = regione == 'campania'
        system_prompt = SYSTEM_PROMPT_CAMPANIA if is_campania else SYSTEM_PROMPT
        query_template = QUERY_TEMPLATE_CAMPANIA if is_campania else QUERY_TEMPLATE

        user_prompt = query_template.format(
            coltura_nome=coltura['nome'],
            numero=numero_str,
            data=bollettino['data'],
            province=bollettino['province'],
            context=context
        )

        content = self._chat(system_prompt, user_prompt)
        content = self._fix_table_spacing(content)

        # Pass di verifica/revisione: recupera fatti omessi e rimuove allucinazioni.
        content = self._verify_and_revise(coltura['nome'], context, content, is_campania)

        # Campania: la tabella di monitoraggio NON la scrive l'LLM (inventava righe). La estraggo
        # verbatim dalla fonte e la inietto qui, dopo la verifica -> sempre fedele.
        if is_campania:
            monit = extract_campania_monitoring(context)
            if monit:
                content = inject_monitoring(content, monit)
        return content

    # ============= LLM HELPERS =============

    def _chat(self, system: str, user: str, json_mode: bool = False) -> str:
        """Chiamata chat singola (temperature=0). json_mode forza output JSON."""
        kwargs = {
            "model": LLM_MODEL,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        return self._openai_client.chat.completions.create(**kwargs).choices[0].message.content

    @staticmethod
    def _fix_table_spacing(content: str) -> str:
        """Inserisce riga vuota tra header e tabella markdown attaccata (rendering)."""
        return re.sub(r'(^#{1,6}\s+.+)\n(\|)', r'\1\n\n\2', content, flags=re.M)

    def _verify_and_revise(self, coltura_nome: str, context: str, report: str,
                           is_campania: bool = False) -> str:
        """
        Rete di sicurezza: un pass indipendente confronta FONTE e REPORT, elenca i
        fatti operativi mancanti e le affermazioni non supportate, e (se ce ne sono)
        rigenera il report integrando/correggendo. 1 sola iterazione.
        Verify prompt per-regione (Campania: caccia anche i numeri inventati).
        """
        if not self.verify:
            return report
        verify_prompt = VERIFY_PROMPT_CAMPANIA if is_campania else VERIFY_PROMPT
        try:
            crit = self._chat(
                verify_prompt,
                f"FONTE:\n{context}\n\nREPORT:\n{report}",
                json_mode=True,
            )
            data = json.loads(crit)
            missing = [m for m in data.get("mancanti", []) if isinstance(m, str) and m.strip()]
            wrong = [w for w in data.get("errati", []) if isinstance(w, str) and w.strip()]
            if not missing and not wrong:
                return report

            corrections = ""
            if missing:
                corrections += "FATTI MANCANTI da integrare:\n" + "\n".join(f"- {m}" for m in missing)
            if wrong:
                corrections += "\n\nAFFERMAZIONI errate da rimuovere/correggere:\n" + "\n".join(f"- {w}" for w in wrong)

            revised = self._chat(
                REVISE_PROMPT,
                f"FONTE:\n{context}\n\nREPORT ATTUALE:\n{report}\n\nCORREZIONI:\n{corrections}",
            )
            revised = self._fix_table_spacing(revised)
            self.logger.info(f"    [verifica] {coltura_nome}: +{len(missing)} mancanti, -{len(wrong)} errati")
            return revised
        except Exception as e:
            self.logger.warning(f"    [verifica] saltata per {coltura_nome}: {e}")
            return report

    # ============= OUTPUT =============

    def _save_markdown(self, coltura_id: str, province: str, bollettino: Dict, report_content: str) -> Path:
        """Salva report markdown e HTML per una coltura, spostando il precedente in history."""
        regione = bollettino.get('regione', 'emilia_romagna')
        # Struttura: output_bollettini/{regione}/{coltura}/
        coltura_dir = OUTPUT_DIR / regione / coltura_id.lower()
        coltura_dir.mkdir(parents=True, exist_ok=True)

        province_slug = normalize_province_slug(province)
        data_bollettino = bollettino['data']
        # Converti da ISO (YYYY-MM-DD) a formato italiano (DD-MM-YYYY)
        data_ita = '-'.join(reversed(data_bollettino.split('-')))
        filename = f"{province_slug}_{data_ita}.md"
        md_path = coltura_dir / filename

        # Sposta report precedente in history (se esiste e diverso dal nuovo)
        existing = find_existing_report(province_slug, coltura_dir)
        if existing and existing != md_path:
            move_to_history(existing, province_slug, coltura_dir, self.logger)

        coltura = self.colture[coltura_id]

        # Nome visualizzazione: usa nome completo area se disponibile
        display_name = get_area_display_name(province) if province else province

        md_content = f"""# {coltura['nome']} - {display_name}

**Bollettino{' N.' + str(bollettino['numero_bollettino']) if bollettino.get('numero_bollettino') else ''}** | {data_ita}

---

{report_content}

---
*Report generato: {datetime.now().strftime('%d/%m/%Y %H:%M')}*
"""

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Genera HTML
        title = f"{coltura['nome']} - {display_name}"
        html_content = convert_md_to_html(md_content, title)
        html_path = md_path.with_suffix('.html')
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return md_path

    # ============= MAIN PROCESSING =============

    def process_bollettino_coltura(self, bollettino: Dict, coltura_id: str, bollettino_chunks: Dict) -> Optional[Path]:
        """
        Processa un singolo bollettino per una coltura specifica.

        Args:
            bollettino_chunks: Chunks del bollettino pre-caricati da ChromaDB
                (evita N query ripetute, una per coltura).

        Returns:
            Path del file markdown generato, o None se no chunks trovati
        """
        doc_name = bollettino['doc_name']
        province = bollettino['province']

        # Retrieval sezione-based + keyword fallback sui chunks già caricati
        chunks = self._retrieve_coltura_chunks(bollettino_chunks, coltura_id)
        coltura = self.colture[coltura_id]

        if not chunks:
            # Report statico senza chiamata LLM
            report_content = f"Nessuna informazione specifica per {coltura['nome']} in questo bollettino."
        else:
            # LLM Generation
            report_content = self._generate_report(bollettino, coltura_id, chunks)

        # Salva markdown + HTML (anche se contiene "nessuna informazione")
        md_path = self._save_markdown(coltura_id, province, bollettino, report_content)

        # Aggiorna cache
        self._mark_processed(doc_name, coltura_id, md_path.name)

        return md_path

    def process_bollettino(self, bollettino: Dict, force: bool = False) -> Tuple[int, int]:
        """
        Processa un bollettino per TUTTE le colture.

        Returns:
            (success_count, total_count)
        """
        doc_name = bollettino['doc_name']
        province = bollettino['province']

        self.logger.info(f"Processing: {province} (Bollettino {bollettino['numero_bollettino']})")

        # Fetch chunks del bollettino UNA VOLTA, riusati per tutte le colture
        bollettino_chunks = self._store.get_by_doc(doc_name)

        success = 0
        skipped = 0

        for coltura_id in self.colture:
            # Check cache
            if not force and self.is_processed(doc_name, coltura_id):
                skipped += 1
                continue

            try:
                result = self.process_bollettino_coltura(bollettino, coltura_id, bollettino_chunks)
                if result:
                    success += 1
                    self.logger.info(f"  {coltura_id}: {result.name}")
            except Exception as e:
                self.logger.error(f"  {coltura_id}: {e}")

        if skipped > 0:
            self.logger.info(f"  -> {skipped} colture gia in cache")

        return success, len(self.colture)

    def process_new_only(self) -> Tuple[bool, Dict]:
        """Processa solo bollettini nuovi (non completamente in cache)."""
        start_time = time.time()

        self.logger.info("=" * 60)
        self.logger.info("COLTURE - Report per tutte le colture")
        self.logger.info("=" * 60)

        self._init_models()

        bollettini = self.get_latest_bollettini_by_province()

        if not bollettini:
            self.logger.info("Nessun bollettino disponibile")
            return False, {
                'processed': 0,
                'total': 0,
                'reason': 'no_bollettini',
                'duration_seconds': time.time() - start_time
            }

        self.logger.info(f"Bollettini da processare: {len(bollettini)}")
        self.logger.info(f"Colture: {len(self.colture)}")

        total_success = 0
        total_processed = 0

        for bollettino in bollettini:
            success, total = self.process_bollettino(bollettino)
            total_success += success
            total_processed += total

        # Salva cache una volta alla fine
        self._save_cache()

        duration = time.time() - start_time

        self.logger.info("=" * 60)
        self.logger.info(f"Completato: {total_success} report generati in {duration:.1f}s")
        self.logger.info("=" * 60)

        return total_success > 0, {
            'processed': total_success,
            'total': total_processed,
            'bollettini': len(bollettini),
            'colture': len(COLTURE),
            'duration_seconds': duration
        }

    def process_all(self, force: bool = False) -> Tuple[bool, Dict]:
        """Processa tutti i bollettini (ultimo per provincia)."""
        start_time = time.time()

        if force:
            self.clear_cache()

        self.logger.info("=" * 60)
        self.logger.info("COLTURE - Report per tutte le colture (ALL)")
        self.logger.info("=" * 60)

        self._init_models()

        bollettini = self.get_latest_bollettini_by_province()

        if not bollettini:
            self.logger.info("Nessun bollettino disponibile")
            return False, {
                'processed': 0,
                'total': 0,
                'reason': 'no_bollettini',
                'duration_seconds': time.time() - start_time
            }

        self.logger.info(f"Bollettini: {len(bollettini)}")
        self.logger.info(f"Colture: {len(self.colture)}")

        total_success = 0
        total_processed = 0

        for bollettino in bollettini:
            success, total = self.process_bollettino(bollettino, force=force)
            total_success += success
            total_processed += total

        # Salva cache
        self._save_cache()

        duration = time.time() - start_time

        self.logger.info("=" * 60)
        self.logger.info(f"Completato: {total_success} report in {duration:.1f}s")
        self.logger.info("=" * 60)

        return total_success > 0, {
            'processed': total_success,
            'total': total_processed,
            'bollettini': len(bollettini),
            'colture': len(COLTURE),
            'duration_seconds': duration
        }


def main() -> int:
    """Entry point CLI."""
    processor = ColtureQueryProcessor()
    has_processed, stats = processor.process_new_only()
    return 0 if has_processed else 1


if __name__ == "__main__":
    exit(main())
