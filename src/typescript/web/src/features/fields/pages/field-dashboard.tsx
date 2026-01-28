import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Card, Col, Container, Row } from "react-bootstrap";
import { fieldsSelectors } from "../state/fields-slice";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import { getFieldMapGeoJson } from "../../companies/pages/company-fields";
import _ from "lodash";
import { GradientLineChart } from "../../../components/GradientLineChart";
import {
  detectionTypesActions,
  detectionTypesSelectors,
} from "../../detection-types/state/detection-types-slice";
import { observationTypesActions } from "../../observation-types/state/observation-types-slice";
import { DetectionTypeCard } from "../../detection-types/components/detection-type-card";
import Icon from "../../../components/Icon";

// --- Field infos
// currentField?.area
// currentField?.grassing
// currentField?.harvest
// currentField?.plants
// currentField?.rotation
// currentField?.variety
// currentField?.weaving
// currentField?.year

function valOrEmpty(value: any, fallback: string = "–") {
  if (value === null || value === undefined || (typeof value === "string" && value.trim() === "")) {
    return fallback;
  }
  return value;
}

function toTitleCase(str: string): string {
  return str.replace(
    /\w\S*/g,
    (text) => text.charAt(0).toUpperCase() + text.substring(1).toLowerCase(),
  );
}

export function FieldDashboard() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { companyId, fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );
  console.log(">>> Current Field:", currentField);
  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionbyFieldId(state, fieldId ?? "default"),
  );

  const detectionTypes = useAppSelector((state) =>
    detectionTypesSelectors.selectDetectionTypesByField(state, fieldId ?? "default"),
  );

  React.useEffect(() => {
    dispatch(
      headerbarActions.setTitle({ title: "Dashboard " + currentField?.name, subtitle: "Subtitle" }),
    );
  }, []);

  React.useEffect(() => {
    if (companyId && fieldId) {
      dispatch(detectionTypesActions.fetchDetectionTypesAction({ orgId: companyId, fieldId }));
    }
    dispatch(observationTypesActions.fetchObservationTypesAction({}));
  }, [companyId, fieldId]);

  return (
    <Fragment>
      {/* TABLE TEST 2 */}
      <Container fluid>
        <Row>
          <Col xs={12}>
            <section className="soft bg-white">
              <Row>
                <Col md={6} xl={4} xxl={3}>
                  <div className="position-relative me-md-4 mb-2 mb-md-0">
                    <img
                      src={`https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/static/geojson(${JSON.stringify(
                        getFieldMapGeoJson(currentField),
                      )})/auto/1024x1024?padding=160&access_token=${process.env.REACT_APP_MAPBOX_API_TOKEN}`}
                      alt="Field Map"
                      className="img-fluid rounded ratio-1-1 d-block"
                    />
                    <button
                      className="trnt_btn slim-y narrow-x secondary type-rounded position-absolute top-0 end-0 m-3 bg-white"
                      onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}/map`)}
                    >
                      <Icon iconName={"fullscreen"} color={"black"} />
                    </button>
                  </div>
                </Col>
                <Col>
                  <Row>
                    <Col xl={12} className="mb-5">
                      <div className="font-l-600">{currentField?.name}</div>
                    </Col>

                    <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2">
                      <div className="iiinfo-label font-s-label">Coltura</div>
                      <div className="iiinfo-value font-l-600">
                        {valOrEmpty(toTitleCase(currentField?.harvest))}
                      </div>
                    </Col>
                    <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2">
                      <div className="iiinfo-label font-s-label">Cultivar</div>
                      <div className="iiinfo-value font-l-600">
                        {valOrEmpty(currentField?.variety)}
                      </div>
                    </Col>
                    <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2">
                      <div className="iiinfo-label font-s-label">Dimensione</div>
                      <div className="iiinfo-value font-l-600">
                        {valOrEmpty(currentField?.area)}
                      </div>
                    </Col>
                    <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2">
                      <div className="iiinfo-label font-s-label">Num. piante</div>
                      <div className="iiinfo-value font-l-600">
                        {valOrEmpty(currentField?.plants)}
                      </div>
                    </Col>
                    <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2">
                      <div className="iiinfo-label font-s-label">Num. rilevamenti</div>
                      <div className="iiinfo-value font-l-600">{valOrEmpty(detections.length)}</div>
                    </Col>
                    <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2">
                      <div className="iiinfo-label font-s-label">Anno di impianto</div>
                      <div className="iiinfo-value font-l-600">
                        {valOrEmpty(currentField?.year)}
                      </div>
                    </Col>
                    <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2 d-none d-md-block">
                      <div className="iiinfo-label font-s-label">Rotazione</div>
                      <div className="iiinfo-value font-l-600">
                        {valOrEmpty(toTitleCase(currentField?.rotation))}
                      </div>
                    </Col>
                    <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2 d-none d-md-block">
                      <div className="iiinfo-label font-s-label">Tessitura</div>
                      <div className="iiinfo-value font-l-600">
                        {valOrEmpty(toTitleCase(currentField?.weaving))}
                      </div>
                    </Col>
                  </Row>
                </Col>
              </Row>
            </section>
          </Col>
        </Row>
      </Container>

      <Container fluid>
        {companyId && fieldId && (
          <Row className="mt-4">
            {detectionTypes.map((value, index) => (
              <Col key={index} xl={12}>
                <DetectionTypeCard companyId={companyId} fieldId={fieldId} typeId={value.id} />
              </Col>
            ))}
          </Row>
        )}

        <Row className="mb-5">
          <Col className="text-center mb-5">
            <a
              // className="cardlet-button"
              className="button dashed fat-y type-rounded px-4"
              data-type="rounded"
              onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`)}
            >
              {"⊕  Nuovo tipo di rilevamento"}
            </a>
          </Col>
        </Row>

        {/*  
        <Row className="mt-5">
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
                  getFieldMapGeoJson(currentField),
                )})/auto/1024x768?padding=80&access_token=${process.env.REACT_APP_MAPBOX_API_TOKEN}`}
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
                <div className="p-3">
                  <GradientLineChart
                    height={400}
                    padding={80}
                    strokeWidth={20}
                    dotSize={14}
                    data={[
                      { x: 0, y: 10, color: "#42C318" },
                      { x: 2, y: 40, color: "#FFB290" },
                      { x: 5, y: 25, color: "#42C318" },
                      { x: 8, y: 60, color: "#FF4D4D" },
                      { x: 9, y: 70, color: "#A10505" },
                    ]}
                  />
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
        */}
      </Container>
    </Fragment>
  );
}
