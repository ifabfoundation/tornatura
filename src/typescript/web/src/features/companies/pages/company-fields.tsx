import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import { useNavigate, useParams } from "react-router-dom";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Card, Col, Container, Row } from "react-bootstrap";
import { fieldsSelectors } from "../../fields/state/fields-slice";
import { AgriField, Point } from "@tornatura/coreapis";
import Icon from "../../../components/Icon";
import _ from "lodash";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import keycloakInstance from "../../../providers/keycloak";

export function getFieldMapGeoJson(field: AgriField) {
  let data: number[][] = [];
  field.map.forEach((point: Point) => {
    data.push([point.lng, point.lat]);
  });
  return {
    type: "Feature",
    properties: {
      fill: "%23F0FF4A",
      "fill-opacity": 0.2,
      stroke: "%23EAFF00",
      "stroke-width": 2,
      "stroke-opacity": 1,
    },
    geometry: {
      coordinates: [data],
      type: "Polygon",
    },
  };
}

export function CompanyFields() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { companyId } = useParams();
  const currentCompany = useAppSelector((state) =>
    companiesSelectors.selectCompanybyId(state, companyId ?? "default"),
  );
  const fields = useAppSelector((state) =>
    fieldsSelectors.selectFieldsByOrgId(state, currentCompany.orgId),
  );
  // sort by name
  fields
    .sort((a, b) => {
      const nameA = a.name.toUpperCase(); // ignore upper and lowercase
      const nameB = b.name.toUpperCase(); // ignore upper and lowercase
      return nameA < nameB ? -1 : nameA > nameB ? 1 : 0;
    })
    .forEach((f) => {
      console.log("--- F --", f.name);
    });

  const detections = useAppSelector(detectionsSelectors.selectDetections);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Campi dell'azienda", subtitle: "" }));
  }, []);

  React.useEffect(() => {}, [currentCompany]);

  function capitalize(s: string) {
    if (s.length === 0) return s;
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  const canCreateField = () => {
    if (keycloakInstance.tokenParsed && companyId) {
      return keycloakInstance.tokenParsed.organizations[companyId]["roles"].includes("manage-agrifields") 
      || keycloakInstance.tokenParsed.organizations[companyId]["roles"].includes("manage-detections")
    }
  }

  return (
    <Container fluid>
      <Row>
        {fields.map((field: AgriField, index: number) => {
          const numberOdDetections = detections.filter((d) => d.agrifieldId === field.id).length;
          return (
            <Col xs={6} md={4} xxl={3} key={index}>
              <Card
                className="with-hover-effect"
                onClick={() => navigate(`/companies/${companyId}/fields/${field.id}`)}
              >
                <Card.Header>{field.name}</Card.Header>
                <Card.Img
                  variant="top"
                  src={`https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/geojson(${JSON.stringify(
                    getFieldMapGeoJson(field),
                  )})/auto/640x480?padding=60&access_token=${process.env.REACT_APP_MAPBOX_API_TOKEN}`} ///padding=50
                />
                <div className="llist-group">
                  <div className="llist-group-item">
                    <span className="d-flex align-items-center dot-overflow-txt">
                      <Icon iconName={"wheat"} color={"black"} />
                      <span className="upper">{capitalize(field.harvest)}</span>
                      <span className="upper d-none d-sm-inline">{"  •  " + field.variety}</span>
                    </span>
                    {/* <span className="d-flex align-items-center">
                      <Icon iconName={"size"} color={"black"} /> {field.area} he
                    </span> */}
                  </div>
                  <div className="llist-group-item">
                    <span className="d-flex align-items-center">
                      <Icon iconName={"asterisk"} color={"black"} />
                      <span className="upper">{`${numberOdDetections} rilevament${numberOdDetections === 1 ? "o" : "i"}`}</span>
                    </span>
                  </div>
                </div>
              </Card>
            </Col>
          );
        })}
        {canCreateField() && <Col xs={6} md={4} xxl={3}>
          <Card
            className="add-item with-hover-effect"
            data-text="Aggiungi un campo"
            onClick={() => navigate(`/companies/${companyId}/new-field`)}
          ></Card>
        </Col>}
      </Row>
    </Container>
  );
}
