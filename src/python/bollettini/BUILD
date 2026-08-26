python_sources(
    name="pysource",
    dependencies=[
        "3rdparty/python:bollettini#APScheduler",
        "3rdparty/python:bollettini#beautifulsoup4",
        "3rdparty/python:bollettini#docling",
        "3rdparty/python:bollettini#fastapi",
        "3rdparty/python:bollettini#geopandas",
        "3rdparty/python:bollettini#markdown",
        "3rdparty/python:bollettini#openai",
        "3rdparty/python:bollettini#python-dotenv",
        "3rdparty/python:bollettini#requests",
        "3rdparty/python:bollettini#shapely",
        "3rdparty/python:bollettini#uvicorn",
    ],
    resolve="bollettini"
)

resources(
    name="bollettini_resources",
    sources=[
        "shapefiles/**",
        "modules/**",
        "MANIFEST.txt",
        "REPORT.md",
        # NIENTE ".env" qui: queste risorse entrano nel pex, e il pex viene
        # copiato dentro l'immagine Docker, che e' PUBBLICA su Docker Hub. Un
        # .env presente in locale al momento della build finirebbe leggibile da
        # chiunque con un `docker pull`. E' successo: la chiave OpenAI e un token
        # GitHub sono stati esposti per sette mesi, in sette tag pubblicati.
        # I segreti si passano ai container dall'esterno (env_file nel compose).
        "CLAUDE.md"
    ],
)

pex_binary(
    name="scheduler",
    entry_point="scheduler.py",
    execution_mode="venv",
    dependencies=[":pysource", ":bollettini_resources"],
    resolve="bollettini",
    layout="packed"
)

pex_binary(
    name="api",
    entry_point="api.py",
    execution_mode="venv",
    dependencies=[":pysource", ":bollettini_resources"],
    resolve="bollettini",
    layout="packed"
)
