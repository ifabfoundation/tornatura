import { Card, Col, Container, Row } from "react-bootstrap";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import React from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";


export function CompaniesList() {
  const dispatch = useAppDispatch();
  const companies = useAppSelector(companiesSelectors.selectAllCompanies);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({title: "Aziende", subtitle: "Subtitle"}));
  }, []); 

  return (
    <div>
      <h1>Lista Aziende</h1>
      <Container>
        <Row>
          {companies.map((company, index) => {
            return (
              <Col sm={3} key={index}>
                <Card>
                  <Card.Img variant="top" src={company.cover} />
                  <Card.Body>
                    <Card.Title>{company.name}</Card.Title>
                    <Card.Text>
                      {company.description}
                    </Card.Text>
                  </Card.Body>
                </Card>
              </Col>
            );
          })}
        </Row>
      </Container>
    </div>
  );
}