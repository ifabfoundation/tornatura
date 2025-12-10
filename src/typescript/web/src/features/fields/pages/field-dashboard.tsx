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
      {/* TABLE TEST */}
      <div className="container">
        <div className="row">
          <div className="col-xl-9">
            <div className="details-grid">
              <div className="details-table">
                <div className="row">
                  <div className="label">Coltura</div>
                  <div className="value">Vite</div>
                </div>
                <div className="row">
                  <div className="label">Cultivar</div>
                  <div className="value">Garganega</div>
                </div>
                <div className="row">
                  <div className="label">Anno di impianto</div>
                  <div className="value">2011</div>
                </div>
                <div className="row">
                  <div className="label">Tessitura</div>
                  <div className="value">Argilla</div>
                </div>
              </div>

              <div className="details-table">
                <div className="row">
                  <div className="label">Num. rilevamenti</div>
                  <div className="value">9</div>
                </div>
                <div className="row">
                  <div className="label">Dimensione</div>
                  <div className="value">2,44 he</div>
                </div>
                <div className="row">
                  <div className="label">Num. piante</div>
                  <div className="value">11.500</div>
                </div>
                <div className="row">
                  <div className="label">Inerbimento</div>
                  <div className="value">Misto/spoglio</div>
                </div>
              </div>
            </div>
          </div>
          <div className="col-xl-3">
            <div className="mt-5 mt-xl-0"></div>
            <a
              className="cardlet-button"
              onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`)}
            >
              + Nuovo Rilevamento
            </a>
          </div>
        </div>
      </div>

      {/* 
      <Container>
        <Row>
          <Col md={6} xl={3}>
            <div className="cardlet">
              <div className="cardlet-header">Tipologia</div>
              <div className="cardlet-content">{currentField?.harvest ?? ""}</div>
            </div>
          </Col>
          <Col xs={6} xl={3}>
            <div className="cardlet">
              <div className="cardlet-header">
                Dimensione<span className="only-dsk"> del campo</span>
              </div>
              <div className="cardlet-content">{currentField?.area ?? ""} he</div>
            </div>
          </Col>
          <Col xs={6} xl={3}>
            <div className="cardlet">
              <div className="cardlet-header">Rilevamenti</div>
              <div className="cardlet-content">{detections.length}</div>
            </div>
          </Col>
          <Col md={6} xl={3}>
            <a
              className="cardlet-button"
              onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`)}
            >
              + Nuovo Rilevamento
            </a>
          </Col>
        </Row>
      </Container>
       */}

      <Container>
        <Row className="mt-4">
          <Col xl={6}>
            <Card>
              <div className="cardlet-header">
                <span className="title">Mappa del campo</span>
                <button
                  className="trnt_btn slim-y narrow-x primary"
                  onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}/map`)}
                >
                  Espandi&nbsp;<span className="d-none d-sm-inline"> la mappa</span>
                </button>
              </div>
              <Card.Img
                variant="top"
                src={`https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/static/geojson(${JSON.stringify(
                  getFieldMapGeoJson(currentField)
                )})/auto/1024x768?access_token=${process.env.REACT_APP_MAPBOX_API_TOKEN}`}
              />
            </Card>
          </Col>
          <Col xl={6}>
            <Card>
              <div className="cardlet-header">
                <span className="title">Rilevamenti</span>
                <button
                  className="trnt_btn slim-y narrow-x primary"
                  onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}/detections`)}
                >
                  <span className="d-sm-none">Espandi</span>
                  <span className="d-none d-sm-inline">Tutti i rilevamenti</span>
                </button>
              </div>
              <Card.Body className="mt-0">
                <Table responsive>
                  <tbody>
                    {detections.map((d: Detection, index) => {
                      const c = new Date(d.detectionTime);
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
                          <td>{c.toLocaleString("it-IT")}</td>
                          <td>{d.type}</td>
                          <td>{summary}</td>
                        </tr>
                      );
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
