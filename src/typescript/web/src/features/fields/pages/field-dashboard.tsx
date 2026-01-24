import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Card, Col, Container, Row} from "react-bootstrap";
import { fieldsSelectors } from "../state/fields-slice";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import { getFieldMapGeoJson } from "../../companies/pages/company-fields";
import _ from "lodash";
import { GradientLineChart } from "../../../components/GradientLineChart";
import { detectionTypesActions, detectionTypesSelectors } from "../../detection-types/state/detection-types-slice";
import { observationTypesActions } from "../../observation-types/state/observation-types-slice";
import { DetectionTypeCard } from "../../detection-types/components/detection-type-card";

function valOrEmpty(value: any, fallback: string = "–") {
  if (value === null || value === undefined || (typeof value === "string" && value.trim() === "")) {
    return fallback;
  }
  return value;
}

function toTitleCase(str: string): string {
  return str.replace(
    /\w\S*/g,
    (text) => text.charAt(0).toUpperCase() + text.substring(1).toLowerCase()
  );
}

export function FieldDashboard() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { companyId, fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default")
  );
  console.log(">>> Current Field:", currentField);
  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionbyFieldId(state, fieldId ?? "default")
  );

  const detectionTypes = useAppSelector((state) =>
    detectionTypesSelectors.selectDetectionTypesByField(state, fieldId ?? "default"),
  );

  React.useEffect(() => {
    dispatch(
      headerbarActions.setTitle({ title: "Dashboard " + currentField?.name, subtitle: "Subtitle" })
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
      <div className="container">
        <div className="row">
          <div className="col-xl-9">
            <div className="row">
              <div className="iiinfo-col mt-2 mb-2 col-6 col-sm-4 col-md-3">
                <div className="iiinfo-label font-s-label">Coltura</div>
                <div className="iiinfo-value font-l-600">
                  {valOrEmpty(toTitleCase(currentField?.harvest))}
                </div>
              </div>
              <div className="iiinfo-col mt-2 mb-2 col-6 col-sm-4 col-md-3">
                <div className="iiinfo-label font-s-label">Cultivar</div>
                <div className="iiinfo-value font-l-600">{valOrEmpty(currentField?.variety)}</div>
              </div>
              <div className="iiinfo-col mt-2 mb-2 col-6 col-sm-4 col-md-3">
                <div className="iiinfo-label font-s-label">Dimensione</div>
                <div className="iiinfo-value font-l-600">{valOrEmpty(currentField?.area)}</div>
              </div>
              <div className="iiinfo-col mt-2 mb-2 col-6 col-sm-4 col-md-3">
                <div className="iiinfo-label font-s-label">Num. piante</div>
                <div className="iiinfo-value font-l-600">{valOrEmpty(currentField?.plants)}</div>
              </div>
              <div className="iiinfo-col mt-2 mb-2 col-6 col-sm-4 col-md-3">
                <div className="iiinfo-label font-s-label">Num. rilevamenti</div>
                <div className="iiinfo-value font-l-600">{valOrEmpty(detections.length)}</div>
              </div>
              <div className="iiinfo-col mt-2 mb-2 col-6 col-sm-4 col-md-3">
                <div className="iiinfo-label font-s-label">Anno di impianto</div>
                <div className="iiinfo-value font-l-600">{valOrEmpty(currentField?.year)}</div>
              </div>
              <div className="iiinfo-col mt-2 mb-2 col-6 col-sm-4 col-md-3 d-none d-md-block">
                <div className="iiinfo-label font-s-label">Rotazione</div>
                <div className="iiinfo-value font-l-600">
                  {valOrEmpty(toTitleCase(currentField?.rotation))}
                </div>
              </div>
              <div className="iiinfo-col mt-2 mb-2 col-6 col-sm-4 col-md-3 d-none d-md-block">
                <div className="iiinfo-label font-s-label">Tessitura</div>
                <div className="iiinfo-value font-l-600">
                  {valOrEmpty(toTitleCase(currentField?.weaving))}
                </div>
              </div>
              {/*  
              <div className="col-3">
                <div className="font-s-label">Inerbimento</div>
                <div className="font-l-600">{valOrEmpty(toTitleCase(currentField?.grassing))}</div>
              </div>
              */}
            </div>

            {/*  
            <div className="rt-responsive-table">
              <div className="rt-row">
                <div className="rt-label">Coltura</div>
                <div className="rt-value">{valOrEmpty(toTitleCase(currentField?.harvest))}</div>
              </div>
              <div className="rt-row">
                <div className="rt-label">Cultivar</div>
                <div className="rt-value">{valOrEmpty(currentField?.variety)}</div>
              </div>
              <div className="rt-row">
                <div className="rt-label">Dimensione</div>
                <div className="rt-value">{valOrEmpty(currentField?.area)}</div>
              </div>
              <div className="rt-row">
                <div className="rt-label">Num. piante</div>
                <div className="rt-value">{valOrEmpty(currentField?.plants)}</div>
              </div>

              <div className="rt-row">
                <div className="rt-label">Num. rilevamenti</div>
                <div className="rt-value">{valOrEmpty(detections.length)}</div>
              </div>
              <div className="rt-row">
                <div className="rt-label">Rotazione</div>
                <div className="rt-value">{valOrEmpty(toTitleCase(currentField?.rotation))}</div>
              </div>
              <div className="rt-row">
                <div className="rt-label">Anno di impianto</div>
                <div className="rt-value">{valOrEmpty(currentField?.year)}</div>
              </div>
              <div className="rt-row">
                <div className="rt-label">Tessitura</div>
                <div className="rt-value">{valOrEmpty(toTitleCase(currentField?.weaving))}</div>
              </div>
              <div className="rt-row">
                <div className="rt-label">Inerbimento</div>
                <div className="rt-value">{valOrEmpty(toTitleCase(currentField?.grassing))}</div>
              </div>
            </div>
              */}
          </div>
          <div className="col-xl-3 ps-xl-5">
            <div className="mt-5 mt-xl-0"></div>
            <a
              // className="cardlet-button"
              className="button accent fat-y wide"
              data-type="rounded"
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
        {companyId && fieldId && <Row className="mt-4">
          {detectionTypes.map((value, index) => 
            <Col key={index} xl={6}>
              <DetectionTypeCard 
                companyId={companyId}
                fieldId={fieldId}
                typeId={value.id}
              />
            </Col>
          )}
        </Row>}
      </Container>
    </Fragment>
  );
}
