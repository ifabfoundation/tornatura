import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import { useParams } from "react-router-dom";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Card, Col, Container, ListGroup, Row } from "react-bootstrap";
import { fieldsSelectors } from "../../fields/state/fields-slice";
import { AgriField } from "@tornatura/coreapis";


export function CompanyFields() {
  const dispatch = useAppDispatch();
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
            <Col md={6} xl={4} key={index}>
              <Card>
                <Card.Header>{field.name}</Card.Header>
                <Card.Img variant="top"/>
                <Card.Body>
                </Card.Body>
                <ListGroup variant="flush">
                  <ListGroup.Item>22 rilevamenti</ListGroup.Item>
                  <ListGroup.Item>Barbabietola</ListGroup.Item>
                </ListGroup>
              </Card>
            </Col>
          );
        })}
      </Row>
    </Container>
  );
}