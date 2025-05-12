import { Card, Col, Container, Row, Image } from "react-bootstrap";
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
            <Col md={6} xl={4} key={index} style={{ display: "flex", alignItems: "stretch" }} className="mb-5">
              <Card onClick={() => handleCompanyClick(company.orgId)}>
                <Card.Header>
                  <Image src={company.cover} roundedCircle width="30px" className="me-3" />
                  <span>{company.name}</span>
                </Card.Header>
                <Card.Img variant="top" src={company.cover}/>
                <Card.Body>
                </Card.Body>
              </Card>
            </Col>
          );
        })}
        <Col md={6} xl={4}>
          <Card onClick={() => navigate("/companies/new-company")}>
            <Card.Img variant="top" height="250"/>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}