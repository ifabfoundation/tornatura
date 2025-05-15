import { Button, Container, Row, Col } from "react-bootstrap";
import keycloakInstance from "../providers/keycloak";
import { Link } from "react-router-dom";
import TopHeader from "../components/TopHeader";

export function Welcome() {
  const handleLoginClick = async () => {
    await keycloakInstance.login({ redirectUri: window.location.origin });
  };

  return (
    <div id="app" className="main-app">
      <div className="ui-right">
        <TopHeader />
        <div className="content-area">
          <div className="content">
            <div className="spacer" style={{ marginTop: "25vh" }}></div>
            <Container className="welcome">
              <Row>
                <Col></Col>
                <Col md="auto" className="text-center">
                  <h1 className="mb-3">Benvenuto su Tornatura</h1>
                  <div className="bg-white p-4 rounded">
                    <div className="spacer d-none d-md-block" style={{ width: "320px" }}></div>

                    <p className="my-3">Hai un account?</p>
                    <Button className="accent wide" onClick={handleLoginClick}>
                      Login
                    </Button>
                    <div className="spacer my-5"></div>
                    <p className="my-3">Crea un nuovo account</p>
                    <Link className="button wide secondary" to="/signup">
                      Registrati
                    </Link>
                  </div>
                </Col>
                <Col></Col>
              </Row>
            </Container>
          </div>
        </div>
      </div>
    </div>
  );
}
