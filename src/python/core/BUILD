python_sources(
    name="pysource",
    dependencies=[
        "3rdparty/python:reqs#phasetwo-sdk",
        "3rdparty/python:reqs#python-multipart",
    ],
)

# This target allows us to bundle our app into a PEX binary file via
#  `pants package`. We can also run it with `pants run`. See
#  https://www.pantsbuild.org/docs/python-package-goal and
#  https://www.pantsbuild.org/docs/python-run-goal.
pex_binary(
    name="app",
    entry_point="main.py",
    dependencies=[":pysource", ":statics"],
)

resources(
    name="statics",
    sources=["media/**", ".env", "templates/**"],
)
