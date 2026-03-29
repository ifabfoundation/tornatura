python_sources(
    name="bollettini_sources",
    dependencies=[
        "3rdparty/python:bollettini#APScheduler",
        "3rdparty/python:bollettini#chromadb",
        "3rdparty/python:bollettini#docling",
        "3rdparty/python:bollettini#fastapi",
        "3rdparty/python:bollettini#geopandas",
        "3rdparty/python:bollettini#markdown",
        "3rdparty/python:bollettini#openai",
        "3rdparty/python:bollettini#python-dotenv",
        "3rdparty/python:bollettini#requests",
        "3rdparty/python:bollettini#sentence-transformers",
        "3rdparty/python:bollettini#shapely",
        "3rdparty/python:bollettini#uvicorn",
    ],
    resolve="bollettini"
)

resources(
    name="bollettini_resources",
    sources=[
        "data/**",
        "shapefiles/**",
        "modules/**",
        "MANIFEST.txt",
        "REPORT.md",
        ".env",
        "CLAUDE.md"
    ],
)

pex_binary(
    name="scheduler",
    entry_point="scheduler.py",
    execution_mode="venv",
    dependencies=[":bollettini_sources", ":bollettini_resources"],
    resolve="bollettini",
    layout="packed"
)

pex_binary(
    name="api",
    entry_point="api.py",
    execution_mode="venv",
    dependencies=[":bollettini_sources", ":bollettini_resources"],
    resolve="bollettini",
    layout="packed"
)
