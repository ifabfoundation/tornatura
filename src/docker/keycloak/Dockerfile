FROM quay.io/phasetwo/phasetwo-keycloak:21.1.2.1688664025

RUN mkdir -p /opt/keycloak/data/import
COPY src/docker/keycloak/master-realm.json /opt/keycloak/data/import/
COPY src/docker/keycloak/tornatura-realm.json /opt/keycloak/data/import/

