import { Card, Col, Container, Row } from "react-bootstrap";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import React from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { useNavigate } from "react-router-dom";

export function CompaniesList() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const companies = useAppSelector(companiesSelectors.selectAllCompanies);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Aziende gestite", subtitle: "Subtitle" }));
  }, []);

  const handleCompanyClick = (companyId: string) => {
    navigate(`/companies/${companyId}/fields`);
  };

  return (
    <Container>
      <Row>
        {companies.map((company, index) => {
          return (
            <Col md={6} xl={4} key={index} style={{ display: "flex", alignItems: "stretch" }}>
              <Card className="with-hover-effect" onClick={() => handleCompanyClick(company.orgId)}>
                <Card.Header>
                  {/* <Image src={company.cover} roundedCircle width="30px" className="me-3" /> */}
                  <div className="round-thumb" style={{ backgroundImage: company.logo }}></div>
                  <span style={{ marginLeft: 10 }}>{company.name}</span>
                </Card.Header>
                <Card.Img
                  variant="top"
                  src={company.cover}
                />
                {<div className="llist-group">
                  <div className="llist-group-item">{company.office.city}</div>
                  <div className="llist-group-item">{company.office.state}</div>
                </div>}
              </Card>
            </Col>
          );
        })}
        <Col md={6} xl={4}>
          <Card
            className="add-item with-hover-effect"
            data-text="Invita un'azienda"
            onClick={() => navigate("/companies/new-company")}
          ></Card>
        </Col>
      </Row>
    </Container>
  );
}
