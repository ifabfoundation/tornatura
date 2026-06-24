import { Card, Col, Container, Row } from "react-bootstrap";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import React from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { useNavigate } from "react-router-dom";
import Icon from "../../../components/Icon";
import { userSelectors } from "../../users/state/user-slice";
import { AccountTypeEnum } from "@tornatura/coreapis";

export function CompaniesList() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const companies = useAppSelector(companiesSelectors.selectAllCompanies);
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Aziende gestite", subtitle: "Subtitle" }));
  }, []);

  const handleCompanyClick = (companyId: string) => {
    navigate(`/m/companies/${companyId}/fields`);
  };

  return (
    <Container fluid>
      <Row>
        {companies.map((company, index) => {
          return (
            <Col
              xs={6}
              md={4}
              xxl={3}
              key={index}
              style={{ display: "flex", alignItems: "stretch" }}
            >
              <Card className="with-hover-effect" onClick={() => handleCompanyClick(company.orgId)}>
                <Card.Header>
                  <Icon iconName={"barn"} color={"black"} />
                  {/* {company.logo ? (
                    <img src={company.logo} width="30px" height="30px" />
                  ) : (
                    <div className="round-thumb" style={{ backgroundImage: company.logo }}></div>
                  )} */}
                  <span style={{ marginLeft: 10 }}>{company.name}</span>
                </Card.Header>
                <Card.Img variant="top" src={company.cover} />
                {
                  <div className="llist-group">
                    <div className="llist-group-item">{company.contacts.email}</div>
                    <div className="llist-group-item">{company.contacts.phone}</div>
                  </div>
                }
              </Card>
            </Col>
          );
        })}
        {currentUser.accountType === AccountTypeEnum.Agronomist && (
          <Col xs={6} md={4} xxl={3}>
            <Card
              className="add-item with-hover-effect"
              data-text="Registra azienda"
              onClick={() => navigate("/m/companies/new")}
            ></Card>
          </Col>
        )}
      </Row>
    </Container>
  );
}
