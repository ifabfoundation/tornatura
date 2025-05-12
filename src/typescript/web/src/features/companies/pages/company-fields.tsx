import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import { useNavigate, useParams } from "react-router-dom";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Card, Col, Container, ListGroup, Row } from "react-bootstrap";
import { fieldsSelectors } from "../../fields/state/fields-slice";
import { AgriField, Point } from "@tornatura/coreapis";


function getFieldMapGeoJson(field: AgriField) {
  let data: number[][] = [];
  field.map.forEach((point: Point) => {
    data.push([point.lng, point.lat]);
  });
  return {
    "type": "Feature",
    "properties": {
      "fill": "%23c4c920"
    },
    "geometry": {
      "coordinates": [
        data
      ],
      "type": "Polygon"
    }
  }
}


export function CompanyFields() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { companyId } = useParams();
  const currentCompany = useAppSelector(state => companiesSelectors.selectCompanybyId(state, companyId ?? "default"));
  const fields = useAppSelector(state => fieldsSelectors.selectFieldsByOrgId(state, currentCompany.orgId));

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({title: "Campi", subtitle: ""}));
  }, []);

  React.useEffect(() => {
  }, [currentCompany]);
  
  return (
    <Container>
      <Row>
        {fields.map((field: AgriField, index: number) => {
          return (
            <Col md={6} xl={4} key={index} className="mb-5">
              <Card onClick={() => navigate(`/companies/${companyId}/fields/${field.id}`)}>
                <Card.Header>{field.name}</Card.Header>
                <Card.Img variant="top" src={`https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/geojson(${JSON.stringify(getFieldMapGeoJson(field))})/auto/640x480?access_token=${process.env.REACT_APP_MAPBOX_API_TOKEN}`}/>
                <ListGroup variant="flush">
                  <ListGroup.Item>{field.harvest}</ListGroup.Item>
                  <ListGroup.Item>{field.area} he</ListGroup.Item>
                  <ListGroup.Item>{22} rilevamenti</ListGroup.Item>
                </ListGroup>
              </Card>
            </Col>
          );
        })}
        <Col md={6} xl={4}>
          <Card onClick={() => navigate(`/companies/${companyId}/fields/new-field`)}>
            <Card.Img variant="top"/>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}