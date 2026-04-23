FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PERONOSPORA_RUNTIME_DIR=/data/peronospora \
    AWS_DEFAULT_REGION=eu-west-1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libeccodes0 \
    libeccodes-dev \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/bin/peronospora-scheduler.pex", "--run-now"]

COPY src.python.peronospora/scheduler.pex /bin/peronospora-scheduler.pex

COPY src.python.peronospora/api.pex /bin/peronospora-api.pex

VOLUME ["/data/peronospora"]