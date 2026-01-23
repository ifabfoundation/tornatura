import { UsersApi } from "@tornatura/coreapis";
import { getCoreApiConfiguration } from "../../services/utils";

export async function getUserInfo() {
  const apiConfig = await getCoreApiConfiguration();
  const usersApi = new UsersApi(apiConfig);
  const userInfo = usersApi.userInfo().then((response) => {
    return response.data;
  });
  return userInfo;
}

import { useEffect, useState } from "react";

export function useMediaQuery(query: string): boolean {
  const getMatch = (q: string): boolean => {
    if (typeof window === "undefined") return false;
    return window.matchMedia(q).matches;
  };
  const [matches, setMatches] = useState<boolean>(() => getMatch(query));
  useEffect(() => {
    const media = window.matchMedia(query);
    const listener = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };
    setMatches(media.matches);
    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, [query]);
  return matches;
}
