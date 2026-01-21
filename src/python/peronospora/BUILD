python_sources(
    name="peronospora_sources",
    dependencies=[
        "3rdparty/python:reqs#fastapi",
        "3rdparty/python:reqs#uvicorn",
        "3rdparty/python:reqs#cfgrib",
        "3rdparty/python:reqs#eccodes",
        "3rdparty/python:reqs#boto3",
        "3rdparty/python:reqs#apscheduler",
        "3rdparty/python:reqs#folium",
    ],
)

resources(
    name="peronospora_resources",
    sources=[
        "data/**",
        "model/**",
        "predictions/**",
        "risk_levels.json",
        "MANIFEST.txt",
    ],
)

pex_binary(
    name="scheduler",
    entry_point="scheduler.py",
    dependencies=[":peronospora_sources", ":peronospora_resources"],
)

pex_binary(
    name="api",
    entry_point="api.py",
    dependencies=[":peronospora_sources", ":peronospora_resources"],
)
