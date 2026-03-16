FROM python:3.12

RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT [ "/bin/app.pex" ]

COPY src.python.core/app.pex /bin
