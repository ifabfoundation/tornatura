python_sources(
    name="pysource",
    dependencies=[
        "3rdparty/python:landscape#fastapi",
        "3rdparty/python:landscape#geopandas",
        "3rdparty/python:landscape#pandas",
        "3rdparty/python:landscape#pyarrow",
        "3rdparty/python:landscape#shapely",
        "3rdparty/python:landscape#uvicorn",
    ],
    resolve="landscape"
)

resources(
    name="landscape_resources",
    sources=[
        "data/**",
        "MANIFEST.txt",
        "CLAUDE.md",
    ],
)

# Due binari, come bollettini e peronospora. Non c'e' uno SCHEDULER perche' i
# dataset sono annuali: l'updater si invoca a mano o come passo di avvio del
# container, ed e' idempotente.
pex_binary(
    name="updater",
    entry_point="updater.py",
    execution_mode="venv",
    dependencies=[":pysource", ":landscape_resources"],
    resolve="landscape",
    layout="packed",
)

pex_binary(
    name="api",
    entry_point="api.py",
    execution_mode="venv",
    dependencies=[":pysource", ":landscape_resources"],
    resolve="landscape",
    layout="packed"
)
