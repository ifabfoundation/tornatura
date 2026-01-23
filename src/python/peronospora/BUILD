python_sources(
    name="peronospora_sources",
    dependencies=[
        "3rdparty/python:peronospora#fastapi",
        "3rdparty/python:peronospora#uvicorn",
        "3rdparty/python:peronospora#pandas",
        "3rdparty/python:peronospora#xgboost",
        "3rdparty/python:peronospora#xarray",
        "3rdparty/python:peronospora#cfgrib",
        "3rdparty/python:peronospora#eccodes",
        "3rdparty/python:peronospora#boto3",
        "3rdparty/python:peronospora#apscheduler",
        "3rdparty/python:peronospora#folium",
        "3rdparty/python:peronospora#geopandas",
    ],
    resolve="peronospora"
)

resources(
    name="peronospora_resources",
    sources=[
        "data/**",
        "model/**",
        "predictions/**",
        "weather/**",
        "risk_levels.json",
        "MANIFEST.txt",
    ],
)

pex_binary(
    name="scheduler",
    entry_point="scheduler.py",
    execution_mode="venv",
    dependencies=[":peronospora_sources", ":peronospora_resources"],
    resolve="peronospora"
)

pex_binary(
    name="api",
    entry_point="api.py",
    execution_mode="venv",
    dependencies=[":peronospora_sources", ":peronospora_resources"],
    resolve="peronospora"
)
