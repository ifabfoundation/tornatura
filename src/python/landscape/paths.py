import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = Path(os.getenv("LANDSCAPE_RUNTIME_DIR", str(PACKAGE_DIR)))

# --- dati STATICI: versionati nel package, finiscono nel PEX come resources ---
DATA_DIR = PACKAGE_DIR / "data"
ICOLT_PARQUET = DATA_DIR / "icolt2026_er.parquet"

# --- dati RUNTIME: nel volume (/data/landscape in Docker) ---
LOG_DIR = RUNTIME_DIR / "logs"

# I dati AGREA vivono sul VOLUME, non dentro l'immagine: sono centinaia di MB per
# annata contro i 34 di iColt, e con execution_mode="venv" il pex li
# materializzerebbe in due copie extra dentro PEX_ROOT, fuori dal volume
# dichiarato e riestratte a ogni ricreazione del container.
# Se i file mancano il servizio continua a funzionare sul solo iColt.
AGREA_DIR = RUNTIME_DIR / "agrea"
AGREA_COLTURE_PARQUET = AGREA_DIR / "agrea2026_colture_er.parquet"
AGREA_ELEMENTI_PARQUET = AGREA_DIR / "agrea2026_elementi_er.parquet"
# Livello fine per il disegno del campo: i frammenti catastali, non dissolti e
# non semplificati. Se manca, il disegno resta quello a mano e nessuna pagina
# si rompe: il suggerimento e' un aiuto, non un prerequisito.
AGREA_PARCELLE_PARQUET = AGREA_DIR / "agrea2026_parcelle_er.parquet"
# Gli elementi del paesaggio con la loro FORMA (il file sopra li tiene come centroide): servono
# solo all'updater, per ritagliare le altre fonti del semi-naturale fuori dalle siepi e dai fossi
# gia' dichiarati. Il servizio non li legge mai a richiesta.
AGREA_ELEMENTI_FORME_PARQUET = AGREA_DIR / "agrea2026_elementi_forme_er.parquet"

# Zone semi-naturali dalle fonti regionali ed europee, gia' ritagliate fuori da AGREA
# dall'updater (modules/seminaturale_prepare.py). Se mancano, il semi-naturale e' il solo AGREA.
SEMINATURALE_DIR = RUNTIME_DIR / "seminaturale"
SEMINATURALE_STRATI_PARQUET = SEMINATURALE_DIR / "strati_er.parquet"  # EPSG:32632
SEMINATURALE_SWF_TIF = SEMINATURALE_DIR / "swf_residuo_er.tif"  # EPSG:3035, 5 m
# Gli stessi strati per la sola MAPPA: uniti per categoria e fonte a celle di 5 km e
# semplificati, perche' serviti cosi' come sono pesavano 513 kB in piu' a 3 km in collina.
SEMINATURALE_MAPPA_PARQUET = SEMINATURALE_DIR / "mappa_er.parquet"  # EPSG:32632
SEMINATURALE_MANIFEST = SEMINATURALE_DIR / "manifest.json"

# Solo le directory runtime vengono create: quelle statiche vivono dentro il PEX.
for _path in (LOG_DIR, AGREA_DIR, SEMINATURALE_DIR):
    _path.mkdir(parents=True, exist_ok=True)
