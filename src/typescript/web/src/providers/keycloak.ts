import Keycloak from "keycloak-js";

const AUTH_SERVER_URL = process.env.REACT_APP_AUTH_SERVER_URL ?? ""
const AUTH_REALM_NAME = process.env.REACT_APP_AUTH_REALM_NAME ?? ""
const APP_AUTH_CLIENT_ID = process.env.REACT_APP_AUTH_CLIENT_ID ?? ""

const keycloakInstance = new Keycloak({
  url: AUTH_SERVER_URL,
  realm: AUTH_REALM_NAME,
  clientId: APP_AUTH_CLIENT_ID,
});

export default keycloakInstance;
