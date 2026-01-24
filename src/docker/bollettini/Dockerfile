FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BOLLETTINI_RUNTIME_DIR=/data/bollettini 

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libeccodes0 \
    libeccodes-dev \
    libspatialindex-dev \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get install -y --no-install-recommends \
    libxcb1 libx11-6 libxext6 libxrender1 libxrandr2 libxi6 libxfixes3 \
    libxcursor1 libxcomposite1 libxdamage1 libxkbcommon0 libxkbcommon-x11-0 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

CMD ["python", "/bin/bollettini-scheduler.pex"]

COPY src.python.bollettini/scheduler.pex /bin/bollettini-scheduler.pex

COPY src.python.bollettini/api.pex /bin/bollettini-api.pex

VOLUME ["/data/bollettini"]
