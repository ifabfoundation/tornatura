import { Card, Col, Container, Row } from "react-bootstrap";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import React from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { useNavigate } from "react-router-dom";
import { MenuItemEntry } from "../../../components/Sidebar";
import { SidebarActions } from "../../sidebar/state/sidebar-slice";
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

  React.useEffect(() => {
    let menuEntries: MenuItemEntry[] = [];
    let menuBottomEntries: MenuItemEntry[] = [];

    menuEntries = [
      {
        id: "companies",
        icon: "grid",
        text: "Aziende gestite",
        path: "/companies",
      },
    ];

    menuBottomEntries = [
      {
        id: "feedback",
        icon: "baloon",
        text: "Invia Feedback",
        path: "/new-feedback",
      },
      // {
      //   id: "my-invitations",
      //   icon: "grid",
      //   text: "I miei inviti",
      //   path: "/invitations/me",
      // },
      {
        id: "user",
        icon: "users",
        text: "Profilo Utente",
        path: "/profile",
      },
    ];

    dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
    dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
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
                  {company.logo ? (
                    <img src={company.logo} width="30px" height="30px" />
                  ) : (
                    <div className="round-thumb" style={{ backgroundImage: company.logo }}></div>
                  )}
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
          <Col md={6} xl={4}>
            <Card
              className="add-item with-hover-effect"
              data-text="Invita un'azienda"
              onClick={() => navigate("/invitations/invite-company-owner")}
            ></Card>
          </Col>
        )}
      </Row>
    </Container>
  );
}
