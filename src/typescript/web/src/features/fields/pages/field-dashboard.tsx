import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Card, Col, Container, Row, Table } from "react-bootstrap";
import { fieldsSelectors } from "../state/fields-slice";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import { getFieldMapGeoJson } from "../../companies/pages/company-fields";
import _ from "lodash";
import { Detection } from "@tornatura/coreapis";

export function FieldDashboard() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { companyId, fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default")
  );
  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionbyFieldId(state, fieldId ?? "default")
  );
  

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Dashboard", subtitle: "Subtitle" }));
  }, []);

  return (
    <Fragment>
      <Container>
        <Row>
          <Col md={6} xl={3}>
            <div className="cardlet">
              <header>Tipologia</header>
              <div className="cardlet-content">{currentField?.harvest ?? ""}</div>
            </div>
          </Col>
          <Col md={6} xl={3}>
            <div className="cardlet">
              <header>Dimensione del campo</header>
              <div className="cardlet-content">{currentField?.area ?? ""} he</div>
            </div>
          </Col>
          <Col md={6} xl={3}>
            <div className="cardlet">
              <header>Rilevamenti</header>
              <div className="cardlet-content">{detections.length}</div>
            </div>
          </Col>
          <Col md={6} xl={3}>
            <a className="cardlet-button" onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`)}>
              + Nuovo Rilevamento
            </a>
          </Col>
        </Row>
        <Row className="mt-4">
          <Col md={1} xl={6}>
            <Card onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}/map`)}>
              <Card.Header>Mappa del campo</Card.Header>
              <Card.Img variant="top" src={`https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/geojson(${JSON.stringify(getFieldMapGeoJson(currentField))})/auto/640x480?access_token=${process.env.REACT_APP_MAPBOX_API_TOKEN}`}/>
            </Card>
          </Col>
          <Col md={1} xl={6}>
            <Card>
              <Card.Header>Rilevamenti</Card.Header>
              <Card.Body>
                <Table responsive>
                  <tbody>
                    {detections.map((d: Detection, index) => {
                      const c = new Date(d.creationTime);
                      let summary = "";
                      if (d.details.desease) {
                        summary = d.details.desease;
                      } else if (d.details.insect) {
                        summary = d.details.insect;
                      } else if (d.details.parasite) {
                        summary = d.details.parasite;
                      }
                      return (
                        <tr key={index}>
                          <td>{c.toLocaleString('it-IT')}</td>
                          <td>{d.type}</td>
                          <td>{summary}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </Table>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
}
