import { Button } from "react-bootstrap";
import keycloakInstance from "../providers/keycloak";
import { Link } from "react-router-dom";



export function Welcome() {

  const handleLoginClick = async () => {
    await keycloakInstance.login({redirectUri: window.location.origin});
  };

  return (
    <div id="app" className="main-app">
      <div className="ui-right">
        <div className="content-area">
          <div className="content">
            <h1>Benvenuto su Tornatura</h1>
            <h2>Hai un account?</h2>
            <Button onClick={handleLoginClick}>Login</Button>
            <h2>Non hai un account registrarti</h2>
            <Link to="/signup">Registrarti</Link>
          </div>
        </div>
      </div>
    </div>
  );
}