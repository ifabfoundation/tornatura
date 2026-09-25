"""Archivio delle fasi fenologiche dei bollettini ER (SQLite sul volume) e interrogazione per data.

`aggiorna()` legge i PDF gia' scaricati dalla pipeline (solo la cartella del downloader ER, senza
sottocartelle: la chiave dell'archivio e' il nome del file), estrae le righe di fase (testo.fasi_pdf),
le traduce in BBCH (bbch.traduci) e le salva in `DATA_DIR/fenologia.sqlite`. E' idempotente:
un PDF gia' letto e non cambiato (stessa dimensione e data di modifica) non si rilegge.

`fasi_al(area, giorno)` risponde alla domanda "in che fase e' ogni coltura in questa zona a
questa data?" con regole dichiarate:
  - vale l'ultimo bollettino **principale** (non BIS, non aggiornamenti irrigui) con data <= giorno;
  - se una coltura manca in quel bollettino si usa la sua ultima fase nella stessa zona, purche'
    abbia al massimo `VALIDITA_GIORNI` giorni (14: i bollettini sono settimanali);
  - se nello stesso bollettino le sezioni (tecniche agronomiche, difesa) danno diciture diverse,
    l'intervallo BBCH e' l'unione e si riportano tutte le diciture;
  - si usano solo i bollettini dello stesso anno del giorno richiesto (le regole sono verificate
    sul 2026); per le colture senza fase negli ultimi 14 giorni si riporta comunque l'ultima fase
    dell'anno con `stale: true`, perche' chi la usa possa distinguere "non ancora scritta" da
    "coltura gia' conclusa e tolta dal bollettino".
"""

from __future__ import annotations

import datetime as dt
import logging
import sqlite3
from pathlib import Path
from typing import Optional

from bollettini import paths
from bollettini.modules.fenologia import bbch, regole, testo

logger = logging.getLogger("bollettini.fenologia")

DB = paths.DATA_DIR / "fenologia.sqlite"
PDF_DIR = paths.DATA_DIR / "input_bollettini" / "emilia_romagna" / "bollettini"
VALIDITA_GIORNI = 14
# versione delle regole: se cambia, tutti i PDF si rileggono
VERSIONE_REGOLE = "2026-09-25"

# provincia (come nel nome normalizzato dello shapefile) -> area dei bollettini
AREA_DA_PROVINCIA = {
    "bologna": "Bologna e Ferrara",
    "ferrara": "Bologna e Ferrara",
    "forli_cesena": "Forli-Cesena, Ravenna, Rimini",
    "ravenna": "Forli-Cesena, Ravenna, Rimini",
    "rimini": "Forli-Cesena, Ravenna, Rimini",
    "modena": "Modena",
    "reggio_nell_emilia": "Reggio Emilia",
    "reggio_emilia": "Reggio Emilia",
    "parma": "Parma",
    "piacenza": "Piacenza",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS documenti (
    file TEXT PRIMARY KEY, dimensione INTEGER, mtime REAL, versione TEXT,
    letto_il TEXT, data TEXT, area TEXT, tipo_doc TEXT, bis INTEGER, n_fasi INTEGER, esito TEXT
);
CREATE TABLE IF NOT EXISTS fasi (
    file TEXT, riga INTEGER, data TEXT, area TEXT, province TEXT, tipo_doc TEXT, bis INTEGER,
    numero INTEGER, coltura TEXT, intestazione TEXT, fase TEXT,
    bbch_min INTEGER, bbch_max INTEGER, riferimenti TEXT
);
CREATE INDEX IF NOT EXISTS fasi_area_data ON fasi (area, data);
"""


def _connetti(db: Path = DB, scrittura: bool = False) -> sqlite3.Connection:
    if scrittura:
        db.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(db)
        con.executescript(SCHEMA)
        return con
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True)


def aggiorna(pdf_dir: Path = PDF_DIR, db: Path = DB, forza: bool = False) -> dict:
    """Legge i PDF nuovi o cambiati. Ritorna i conteggi (letti, gia' presenti, errori, fasi)."""
    stat = {
        "letti": 0,
        "gia_presenti": 0,
        "non_riconosciuti": 0,
        "errori": 0,
        "fasi": 0,
    }
    if not pdf_dir.exists():
        logger.warning("fenologia: cartella dei PDF assente: %s", pdf_dir)
        return stat
    con = _connetti(db, scrittura=True)
    try:
        noti = {
            r[0]: r[1:]
            for r in con.execute(
                "SELECT file, dimensione, mtime, versione FROM documenti"
            )
        }
        for pdf in sorted(pdf_dir.glob("*.pdf")):  # piatta: la chiave e' il nome
            st = pdf.stat()
            if not forza and noti.get(pdf.name) == (
                st.st_size,
                st.st_mtime,
                VERSIONE_REGOLE,
            ):
                stat["gia_presenti"] += 1
                continue
            meta = regole.meta_file(pdf.name)
            con.execute("DELETE FROM fasi WHERE file = ?", (pdf.name,))
            if meta is None:
                stat["non_riconosciuti"] += 1
                esito, righe = "nome_non_riconosciuto", []
            else:
                try:
                    righe = testo.fasi_pdf(pdf)
                    esito = "ok"
                except Exception as e:  # un PDF rotto non ferma gli altri
                    logger.error("fenologia: errore su %s: %s", pdf.name, e)
                    stat["errori"] += 1
                    esito, righe = f"errore: {e}"[:200], []
            for r in righe:
                t = bbch.traduci(r["coltura"], r["fase"])
                con.execute(
                    "INSERT INTO fasi VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        pdf.name,
                        r["riga"],
                        r["data"],
                        r["area"],
                        r["province"],
                        r["tipo_doc"],
                        1 if r["bis"] else 0,
                        r["numero"],
                        r["coltura"],
                        r["intestazione"],
                        r["fase"],
                        t[0] if t else None,
                        t[1] if t else None,
                        t[2] if t else None,
                    ),
                )
            con.execute(
                "INSERT OR REPLACE INTO documenti VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    pdf.name,
                    st.st_size,
                    st.st_mtime,
                    # dopo un errore la versione non combacia: al giro seguente si riprova (un
                    # errore puo' essere passeggero, es. memoria esaurita nel container)
                    VERSIONE_REGOLE
                    if not esito.startswith("errore")
                    else "da_riprovare",
                    dt.datetime.now().isoformat(timespec="seconds"),
                    meta["data"].isoformat() if meta else None,
                    meta["area"] if meta else None,
                    meta["tipo"] if meta else None,
                    (1 if meta["bis"] else 0) if meta else None,
                    len(righe),
                    esito,
                ),
            )
            con.commit()
            stat["letti"] += 1
            stat["fasi"] += len(righe)
    finally:
        con.close()
    logger.info("fenologia: %s", stat)
    return stat


def area_da_provincia(provincia_normalizzata: str) -> Optional[str]:
    return AREA_DA_PROVINCIA.get(provincia_normalizzata)


def fasi_al(
    area: str, giorno: dt.date, colture: Optional[list[str]] = None, db: Path = DB
) -> dict:
    """Fase di ogni coltura nella zona al giorno dato (regole in testa al modulo)."""
    if not db.exists():
        return {
            "available": False,
            "reason": "archivio fenologico non ancora costruito",
        }
    con = _connetti(db)
    try:
        ultimo = con.execute(
            "SELECT file, data FROM documenti WHERE area = ? AND tipo_doc = 'bollettino' AND bis = 0 "
            "AND esito = 'ok' AND data <= ? AND data >= ? ORDER BY data DESC LIMIT 1",
            (
                area,
                giorno.isoformat(),
                dt.date(giorno.year, 1, 1).isoformat(),
            ),  # stessa regola dell'anno
        ).fetchone()
        dal = dt.date(giorno.year, 1, 1).isoformat()  # solo l'anno del giorno richiesto
        q = (
            "SELECT coltura, data, file, fase, bbch_min, bbch_max FROM fasi WHERE area = ? AND tipo_doc = "
            "'bollettino' AND bis = 0 AND data <= ? AND data >= ? AND coltura != ''"
        )
        par: list = [area, giorno.isoformat(), dal]
        if colture:
            q += f" AND coltura IN ({','.join('?' * len(colture))})"
            par += list(colture)
        righe = con.execute(q + " ORDER BY data", par).fetchall()
    finally:
        con.close()
    per: dict = {}
    for col, data, file, fase, lo, hi in righe:
        per.setdefault(col, {}).setdefault(data, []).append((file, fase, lo, hi))
    colt = {}
    for col, per_data in per.items():
        data = max(per_data)  # l'ultima data disponibile
        voci = per_data[data]
        tradotte = [v for v in voci if v[2] is not None]
        diciture = list(dict.fromkeys(v[1] for v in voci))  # in ordine, senza doppioni
        eta = (giorno - dt.date.fromisoformat(data)).days
        colt[col] = {
            "bulletin_date": data,
            "age_days": eta,
            "stale": eta > VALIDITA_GIORNI,
            "file": voci[0][0],
            "phases": diciture,
            "bbch_min": min(v[2] for v in tradotte) if tradotte else None,
            "bbch_max": max(v[3] for v in tradotte) if tradotte else None,
        }
    return {
        "available": True,
        "area": area,
        "date": giorno.isoformat(),
        "validity_days": VALIDITA_GIORNI,
        "last_bulletin": {"file": ultimo[0], "date": ultimo[1]} if ultimo else None,
        "crops": colt,
    }


if __name__ == "__main__":  # python -m bollettini.modules.fenologia.archivio [--forza]
    import sys

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
    )
    print(aggiorna(forza="--forza" in sys.argv))
