python_sources(
    name="pysource",
    dependencies=[
        "3rdparty/python:reqs#phasetwo-sdk",
        "3rdparty/python:reqs#python-multipart",
        "3rdparty/python:reqs#Jinja2",
        "3rdparty/python:reqs#email-validator",
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

pex_binary(
    name="backfill-organization-roles",
    entry_point="scripts/backfill_organization_roles.py",
    dependencies=[":pysource", ":statics"],
)

pex_binary(
    name="cleanup-organization-fields",
    entry_point="scripts/cleanup_organization_fields.py",
    dependencies=[":pysource", ":statics"],
)

pex_binary(
    name="delete-user-and-orgs",
    entry_point="scripts/delete_user_and_orgs.py",
    dependencies=[":pysource", ":statics"],
)

pex_binary(
    name="generate-organization-stats",
    entry_point="scripts/generate_organization_stats.py",
    dependencies=[":pysource", ":statics"],
)

pex_binary(
    name="migrate-detection-photos",
    entry_point="scripts/migrate_detection_photos.py",
    dependencies=[":pysource", ":statics"],
)

pex_binary(
    name="migrate-detection-types",
    entry_point="scripts/migrate_detection_types.py",
    dependencies=[":pysource", ":statics"],
)

pex_binary(
    name="migrate-observation-type-supported-harvests",
    entry_point="scripts/migrate_observation_type_supported_harvests.py",
    dependencies=[":pysource", ":statics"],
)

pex_binary(
    name="seed-harvest-types",
    entry_point="scripts/seed_harvest_types.py",
    dependencies=[":pysource", ":statics"],
)

pex_binary(
    name="sync-deleted-organizations-from-keycloak",
    entry_point="scripts/sync_deleted_organizations_from_keycloak.py",
    dependencies=[":pysource", ":statics"],
)

pex_binary(
    name="update-observation-type-instruction-links",
    entry_point="scripts/update_observation_type_instruction_links.py",
    dependencies=[":pysource", ":statics"],
)

resources(
    name="statics",
    sources=["media/**", ".env", "templates/**"],
)
