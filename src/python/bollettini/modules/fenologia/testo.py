"""Testo di un bollettino PDF, gia' senza revisioni di Word, e righe di fase estratte.

Si usa pypdfium2, che il servizio ha gia' (arriva con Docling): nessuna dipendenza nuova, nessun
programma esterno. Rispetto a Poppler e Docling, che l'esperimento ha usato per primi:

  - i caratteri **barrati** (revisioni di Word rimaste nel PDF: il testo cancellato resta
    stampato accanto al nuovo) si tolgono. Regola: linea sottile (< 1,5 pt) dello stesso colore
    del carattere, nella fascia 30-75% dell'altezza della riga, che copre il centro del
    carattere. Uno spazio non si toglie. Il bollettino 6 del 18/03/2026 di Bologna e Ferrara ne
    aveva 23 righe di fase;
  - la parola spezzata a fine riga: pdfium la segna con \x02 (o \ufffe) e unisce le due righe;
    si rimette il trattino e si va a capo, come nel PDF (Poppler e Docling lo cancellano:
    "pre-semina-" + "semina" diventava "pre-seminasemina");
  - le righe vuote fra paragrafi, che le regole usano per le intestazioni di coltura, si
    ricostruiscono dallo spazio verticale fra le righe (SALTO_PARAGRAFO).

Verifica (25/09/2026, esperimento `esperimenti/cimice_landscape/fenologia/estrai_pdfium.py`):
sui 165 bollettini ER 2026 le righe prodotte coincidono con le 5.142 della tabella controllata
a mano (tre letture testuali, lettura geometrica di ogni riga, due letture visive alla cieca).
"""

from __future__ import annotations

import ctypes
import re
from pathlib import Path

import pypdfium2 as pdfium  # pants: no-infer-dep (arriva con docling, vedi BUILD)
import pypdfium2.raw as pr  # pants: no-infer-dep
from bollettini.modules.fenologia import regole


def _colore_carattere(tp, i):
    r, g, b, a = (ctypes.c_uint() for _ in range(4))
    ok = pr.FPDFText_GetFillColor(tp.raw, i, r, g, b, a)
    return (r.value, g.value, b.value) if ok else None


def _linee_sottili(pagina):
    """Rettangoli e tratti orizzontali sottili con il loro colore: (x0, x1, y_centro, colore)."""
    out = []
    for obj in pagina.get_objects(filter=[pr.FPDF_PAGEOBJ_PATH], max_depth=5):
        x0, y0, x1, y1 = obj.get_pos()
        if (y1 - y0) >= 1.5 or (x1 - x0) <= 1:
            continue
        for fn in (pr.FPDFPageObj_GetFillColor, pr.FPDFPageObj_GetStrokeColor):
            r, g, b, a = (ctypes.c_uint() for _ in range(4))
            if fn(obj.raw, r, g, b, a) and a.value > 0:
                out.append((x0, x1, (y0 + y1) / 2, (r.value, g.value, b.value)))
    return out


# Spazio fra due righe, in altezze di carattere, oltre cui c'e' una riga vuota. Misurato sui
# bollettini: righe dello stesso paragrafo ~0,3; riga che va a capo o etichetta sotto
# l'intestazione 0,6-0,7; paragrafi diversi sempre oltre 1,0.
SALTO_PARAGRAFO = 0.9


def testo_pagina(pagina) -> str:
    """Testo della pagina senza caratteri barrati, con le righe vuote fra i paragrafi.

    Le righe vuote servono alle regole di estrai_fasi (le intestazioni di coltura stanno fra righe
    vuote, come nel testo di Poppler): pdfium non le da', si ricostruiscono dallo spazio verticale.
    """
    tp = pagina.get_textpage()
    n = tp.count_chars()
    linee = _linee_sottili(pagina)
    righe, cur, box = [], [], []  # box: (basso, alto) dei caratteri visibili della riga
    for i in range(n):
        c = tp.get_text_range(i, 1)
        if c in ("\x02", "\ufffe"):
            # parola spezzata col trattino a fine riga: pdfium unisce la riga seguente a questa.
            # Si rimette il trattino e si va a capo, come nel PDF (e come fa Poppler -raw)
            cur.append("-")
            righe.append(
                (
                    "".join(cur),
                    (min(x[0] for x in box), max(x[1] for x in box)) if box else None,
                )
            )
            cur, box = [], []
            continue
        if c in ("\r", "\n"):
            if c == "\n" or (i + 1 < n and tp.get_text_range(i + 1, 1) != "\n"):
                righe.append(
                    (
                        "".join(cur),
                        (min(x[0] for x in box), max(x[1] for x in box))
                        if box
                        else None,
                    )
                )
                cur, box = [], []
            continue
        if c and not c.isspace():
            l, b, r, t = tp.get_charbox(i)
            h = t - b
            if linee:
                # per la barratura conta l'altezza della riga (box "loose": da discendente ad
                # ascendente del font), non quella del disegno: un trattino e' alto 0,7 pt
                lL, bL, rL, tL = tp.get_charbox(i, loose=True)
                hL = tL - bL
                cx = (l + r) / 2
                col = _colore_carattere(tp, i) if hL > 0 else None
                # in PDF l'asse y sale; la sottolineatura sta sotto il 20%, la barratura a meta'
                if col is not None and any(
                    x0 - 0.5 <= cx <= x1 + 0.5
                    and bL + 0.30 * hL <= ym <= bL + 0.75 * hL
                    and all(abs(p - q) <= 20 for p, q in zip(lc, col))
                    for x0, x1, ym, lc in linee
                ):
                    continue  # carattere barrato: testo cancellato con le revisioni
            if h > 0:
                box.append((b, t))
        cur.append(c)
    if cur:
        righe.append(
            (
                "".join(cur),
                (min(x[0] for x in box), max(x[1] for x in box)) if box else None,
            )
        )
    out, prec = [], None
    for testo, bb in righe:
        if bb and prec:
            h = max(bb[1] - bb[0], prec[1] - prec[0])
            if prec[0] - bb[1] > SALTO_PARAGRAFO * h:
                out.append("")
        out.append(testo.rstrip())
        if bb:
            prec = bb
    return "\n".join(out)


# R8: titoli di sottosezione che a volte restano attaccati in fondo alla riga della fase
TITOLI_CODA = re.compile(
    r"\s+(tecniche agronomiche|difesa|diserbo|irrigazione|fertilizzazione|concimazione)\s*$",
    re.I,
)
# R8: un'etichetta "Parola:" incollata senza spazio dopo una minuscola ("grappoliniPeronospora: su")
ETICHETTA_INCOLLATA = re.compile(r"(?<=[a-zà-ù])(?=[A-Z][a-zà-ù]+\s*:)")
# R9: qualificatore fra parentesi con i due punti in testa ("(primaverile): da pre-emergenza ...")
QUALIFICATORE_TESTA = re.compile(r"^\([^)]{1,30}\)\s*:\s*")


def pulisci_fase(t: str) -> str:
    t = ETICHETTA_INCOLLATA.split(t, maxsplit=1)[0]
    t = TITOLI_CODA.sub("", t)
    t = QUALIFICATORE_TESTA.sub("", t)
    return t.strip(" .;")


def testo_pdf(pdf: Path) -> str:
    """Testo di tutto il PDF: pagine separate da "\n\f" come nel testo di Poppler."""
    doc = pdfium.PdfDocument(str(pdf))
    try:
        return "\n\f".join(testo_pagina(doc[i]) for i in range(len(doc)))
    finally:
        doc.close()


def fasi_pdf(pdf: Path) -> list[dict]:
    """Le righe di fase accettate (stato "ok") di un bollettino, con il testo gia' pulito (R8-R9).

    Le righe in altri stati (dubbia, assente, seconda fase sotto la stessa intestazione...) non
    entrano: nella verifica del 2026 nessuna di queste era una fase vera mancante.
    """
    righe, _n, _ignote = regole.estrai(pdf.name, testo_pdf(pdf))
    out = []
    for r in righe:
        if r.get("stato") == "ok":
            r["fase"] = pulisci_fase(r["fase"])
            out.append(r)
    return out
