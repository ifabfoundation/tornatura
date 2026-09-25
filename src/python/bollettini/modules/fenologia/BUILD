# pypdfium2 (usato da testo.py) NON e' fra i requisiti diretti del resolve "bollettini": arriva
# con docling, che nel lockfile lo fissa a 4.30.0. Dichiararlo richiederebbe di rigenerare il
# lockfile, e il 25/09/2026 la rigenerazione avrebbe cambiato 58 pacchetti (torch, docling-core,
# opencv 4 -> 5): troppo per una lettura di testo. Per questo la dipendenza passa da docling, qui
# esplicita; `verifica.py` (lanciabile anche nel container) fallisce se pypdfium2 sparisce dal pex.
python_sources(
    dependencies=["3rdparty/python:bollettini#docling"],
)
