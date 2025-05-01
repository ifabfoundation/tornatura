import { UsersApi } from "@tornatura/coreapis"
import { getCoreApiConfiguration } from "../../services/utils";


export async function getUserInfo() {
  const apiConfig = await getCoreApiConfiguration();
  const usersApi = new UsersApi(apiConfig);
  const userInfo = usersApi.userInfo().then((response) => {
    return response.data;
  });
  return userInfo;
}