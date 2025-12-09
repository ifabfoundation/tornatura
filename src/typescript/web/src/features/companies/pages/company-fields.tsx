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

export function getFieldMapGeoJson(field: AgriField) {
  let data: number[][] = [];
  field.map.forEach((point: Point) => {
    data.push([point.lng, point.lat]);
  });
  return {
    type: "Feature",
    properties: {
      fill: "%23c4c920",
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
    companiesSelectors.selectCompanybyId(state, companyId ?? "default")
  );
  const fields = useAppSelector((state) =>
    fieldsSelectors.selectFieldsByOrgId(state, currentCompany.orgId)
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
    dispatch(headerbarActions.setTitle({ title: "Campi", subtitle: "" }));
  }, []);

  React.useEffect(() => {}, [currentCompany]);

  return (
    <Container>
      <Row>
        {fields.map((field: AgriField, index: number) => {
          const numberOdDetections = detections.filter((d) => d.agrifieldId === field.id).length;
          return (
            <Col md={6} xl={4} key={index}>
              <Card
                className="with-hover-effect"
                onClick={() => navigate(`/companies/${companyId}/fields/${field.id}`)}
              >
                <Card.Header>{field.name}</Card.Header>
                <Card.Img
                  variant="top"
                  src={`https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/geojson(${JSON.stringify(
                    getFieldMapGeoJson(field)
                  )})/auto/640x480?access_token=${process.env.REACT_APP_MAPBOX_API_TOKEN}`}
                />
                <div className="llist-group">
                  <div className="llist-group-item">
                    <span className="d-flex align-items-center">
                      <Icon iconName={"wheat"} color={"black"} /> {field.harvest}
                    </span>
                    <span className="d-flex align-items-center">
                      <Icon iconName={"size"} color={"black"} /> {field.area} he
                    </span>
                  </div>
                  <div className="llist-group-item">
                    <span className="d-flex align-items-center">
                      <Icon iconName={"asterisk"} color={"black"} /> {numberOdDetections}{" "}
                      rilevamenti
                    </span>
                  </div>
                </div>
              </Card>
            </Col>
          );
        })}
        <Col md={6} xl={4}>
          <Card
            className="add-item with-hover-effect"
            data-text="Aggiungi un campo"
            onClick={() => navigate(`/companies/${companyId}/new-field`)}
          ></Card>
        </Col>
      </Row>
    </Container>
  );
}
