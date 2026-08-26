FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANDSCAPE_RUNTIME_DIR=/data/landscape

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY src.python.landscape/api.pex /bin/landscape-api.pex

# I dati AGREA (387 MB) NON stanno nell'immagine: si scaricano dalla fonte nel
# volume, come peronospora fa con i GRIB di ECMWF. L'updater e' idempotente, si
# puo' invocare a ogni avvio, e se non gira mai il servizio funziona sul solo
# iColt che viaggia dentro il pex.
#   docker exec <container> python /bin/landscape-updater.pex --run-now
COPY src.python.landscape/updater.pex /bin/landscape-updater.pex

# Il processo principale e' l'API. Non c'e' uno scheduler come in bollettini e
# peronospora perche' i dataset sono annuali: l'updater sopra si invoca a parte.
CMD ["python", "/bin/landscape-api.pex"]

VOLUME ["/data/landscape"]
