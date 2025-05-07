import { Card, Col, Container, Row } from "react-bootstrap";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import React from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { useNavigate } from "react-router-dom";


export function CompaniesList() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate()
  const companies = useAppSelector(companiesSelectors.selectAllCompanies);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({title: "Aziende gestite", subtitle: "Subtitle"}));
  }, []); 

  const handleCompanyClick = (companyId: string) => {
    navigate(`/companies/${companyId}/fields`);
  }

  return (
    <Container>
      <Row>
        {companies.map((company, index) => {
          return (
            <Col md={6} xl={4} key={index} style={{ display: "flex", alignItems: "stretch" }}>
              <Card onClick={() => handleCompanyClick(company.orgId)}>
                <Card.Header>{company.name}</Card.Header>
                <Card.Img variant="top" src={company.cover} />
                <Card.Body>
                  <Card.Text>{company.description}</Card.Text>
                </Card.Body>
              </Card>
            </Col>
          );
        })}
        <Col md={6} xl={4} style={{ display: "flex", alignItems: "stretch" }}>
          <Card onClick={() => navigate("/companies/new-company")}>
            <Card.Body>
              + Nuova azienda
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}