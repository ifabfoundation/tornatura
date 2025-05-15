import { useState, createContext, useEffect, PropsWithChildren } from "react";
import keycloakInstance from "./keycloak";

const initialState = {
  initialized: false,
  authenticated: false,
};

const authStore = createContext(initialState);

const AuthProvider = (props: PropsWithChildren) => {
  const { children } = props;
  const [initialized, setInitialized] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    if (!keycloakInstance.didInitialize) {
      keycloakInstance
        .init({ onLoad: "check-sso", checkLoginIframe: false })
        .then((authenticated) => {
          setAuthenticated(authenticated);
          setInitialized(true);
        })
        .catch((reason) => {
          console.log(reason);
          setInitialized(false);
        });
    }
    keycloakInstance.onAuthSuccess = () => {
      console.log("Authenticated");
      setAuthenticated(true);
    }
  }, []);

  useEffect(() => {
    if (authenticated && initialized) {
      keycloakInstance.onTokenExpired = () => {
        console.log("Token expired");
        keycloakInstance.updateToken(3).then((status) => {
          if (!status) {
            setAuthenticated(false);
            keycloakInstance.logout();
          }
        });
      };
    }
  }, [initialized, authenticated]);

  return (
    <authStore.Provider
      value={{
        initialized,
        authenticated,
      }}
    >
      {children}
    </authStore.Provider>
  );
};

export { authStore, AuthProvider };