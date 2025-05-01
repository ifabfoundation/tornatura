files(name="realms", sources=["master-realm.json", "tornatura-realm.json"])

docker_image(
    name="docker",
    repository="darkform/tornatura.keycloak",
    image_tags=["22.0.3", "latest"],
    dependencies=[":realms"]
)
