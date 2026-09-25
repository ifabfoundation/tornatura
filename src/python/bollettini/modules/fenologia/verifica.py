"""Verifica di non-regressione della fenologia contro le tabelle controllate a mano nel 2026.

    python -m bollettini.modules.fenologia.verifica                 # solo il dizionario (630 diciture)
    python -m bollettini.modules.fenologia.verifica <cartella PDF>  # + l'estrazione (5.142 righe)

Le due tabelle in `attese/` vengono dall'esperimento `esperimenti/cimice_landscape/fenologia/`:
  - `dizionario_fasi_2026.csv`: dicitura -> intervallo BBCH per le colture ospiti della cimice,
    verificato da due traduzioni alla cieca sulla monografia BBCH e, nei casi discordi, da tre
    arbitri;
  - `fasi_verificate_2026.csv`: le righe di fase dei 165 bollettini ER 2026 (tre letture
    testuali, lettura geometrica di ogni riga, due letture visive alla cieca delle pagine corrette).
Una modifica alle regole o al dizionario che cambia anche una sola riga fa uscire con codice 1.
Il confronto del testo ignora maiuscole, spazi e spazi intorno a trattini e barre.
"""

from __future__ import annotations

import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from bollettini.modules.fenologia import bbch, testo

ATTESE = Path(__file__).resolve().parent / "attese"
LEGATURE = {
    "ﬀ": "ff",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "’": "'",
    "‘": "'",
    "–": "-",
    "—": "-",
}


def norm(t: str) -> str:
    for a, b in LEGATURE.items():
        t = t.replace(a, b)
    t = unicodedata.normalize("NFC", t).lower()
    t = re.sub(r"\s*-\s*", "-", t)
    t = re.sub(r"\s*/\s*", "/", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip(" .;:,")


def verifica_dizionario() -> int:
    diversi = []
    righe = list(
        csv.DictReader(open(ATTESE / "dizionario_fasi_2026.csv", encoding="utf-8"))
    )
    for r in righe:
        t = bbch.traduci(r["coltura"], r["dicitura"])
        atteso = (int(r["bbch_min"]), int(r["bbch_max"]))
        if t is None or (t[0], t[1]) != atteso:
            diversi.append(
                (r["coltura"], r["dicitura"], atteso, (t[0], t[1]) if t else None)
            )
    print(
        f"dizionario: {len(righe) - len(diversi)}/{len(righe)} diciture con l'intervallo atteso"
    )
    for d in diversi[:30]:
        print("  diversa:", d)
    return len(diversi)


def verifica_estrazione(cartella: Path) -> int:
    attese = defaultdict(Counter)
    for r in csv.DictReader(
        open(ATTESE / "fasi_verificate_2026.csv", encoding="utf-8")
    ):
        attese[r["bollettino"]][(r["coltura"], norm(r["fase"]))] += 1
    trovate = defaultdict(Counter)
    for pdf in sorted(cartella.glob("*.pdf")):
        if pdf.stem not in attese:
            continue  # bollettini dopo la verifica: non c'e' una riga attesa con cui confrontarli
        for r in testo.fasi_pdf(pdf):
            trovate[pdf.stem][(r["coltura"], norm(r["fase"]))] += 1
    mancanti = sorted(set(attese) - set(trovate))
    manca = in_piu = 0
    esempi = []
    for b in sorted(attese):
        if b in mancanti:
            continue
        for k, v in (attese[b] - trovate[b]).items():
            manca += v
            esempi.append(("manca", b, k))
        for k, v in (trovate[b] - attese[b]).items():
            in_piu += v
            esempi.append(("in piu'", b, k))
    tot = sum(sum(c.values()) for b, c in attese.items() if b not in mancanti)
    print(
        f"estrazione: {len(attese) - len(mancanti)} bollettini confrontati, {tot - manca}/{tot} righe attese "
        f"trovate, {in_piu} in piu' | PDF assenti nella cartella: {len(mancanti)}"
    )
    for e in esempi[:30]:
        print("  ", e)
    return manca + in_piu


def main() -> int:
    errori = verifica_dizionario()
    if len(sys.argv) > 1:
        errori += verifica_estrazione(Path(sys.argv[1]))
    print("ESITO:", "tutto uguale" if errori == 0 else f"{errori} differenze")
    return 0 if errori == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
