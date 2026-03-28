import keycloakInstance from "../providers/keycloak";
import { Configuration } from "@tornatura/coreapis";

const COREAPIS_BASE_PATH = process.env.REACT_APP_COREAPIS_SERVER_URL;

export async function getCoreApiConfiguration() {
  await keycloakInstance.updateToken(7200);
  return new Configuration({
    basePath: `${COREAPIS_BASE_PATH}`,
    baseOptions: { headers: { Authorization: `Bearer ${keycloakInstance.token}` } },
  });
}

export function capitalize(str: string) {
  return str.charAt(0).toUpperCase() + str.toLowerCase().slice(1);
}

export function dateToString(date: any, showTime: boolean = true) {
  const d = new Date(date);
  const offset = d.getTimezoneOffset() * 60 * 1000;
  const adjustedDate = new Date(d.getTime() - offset);

  if (showTime) {
    return adjustedDate.toLocaleString();
  } else {
    return adjustedDate.toLocaleDateString();
  }
}
