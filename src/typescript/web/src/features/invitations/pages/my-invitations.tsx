import React, { Fragment } from "react";
import { useNavigate } from "react-router-dom";
import { Alert, Container, Col, Row } from "react-bootstrap";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { invitationsActions, invitationsSelectors } from "../state/invitations-slice";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";

// Helper to format timestamps
const formatDate = (timestamp: number) => {
  return new Date(timestamp).toLocaleDateString("it-IT", {
    // year: "numeric",
    // month: "long",
    // day: "numeric",
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
  });
};

// Helper to translate role
const translateRole = (role: string) => {
  switch (role) {
    case "company-owner-access":
      return "Proprietario azienda";
    case "company-manager-access":
      return "Manager azienda";
    case "company-standard-access":
      return "Collaboratore";
    case "agronomist-access":
      return "Agronomo";
    default:
      return role;
  }
};

export function MyInvitations() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const invitations = useAppSelector(invitationsSelectors.selectMyInvitations);
  const status = useAppSelector(invitationsSelectors.selectInvitationsStatus);
  const error = useAppSelector(invitationsSelectors.selectInvitationsError);

  // Load user's invitations on mount
  React.useEffect(() => {
    dispatch(invitationsActions.fetchMyInvitationsAction());
  }, [dispatch]);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Inviti ricevuti", subtitle: "Subtitle" }));
  }, []);

  const handleViewInvitation = (token: string) => {
    navigate(`/invitations/accept?token=${token}`);
  };

  if (status === "pending") {
    return (
      <Container>
        <div className="loading">Caricamento inviti...</div>
      </Container>
    );
  }

  return (
    <Container>
      <section>
        <header className="my-4">
          <p className="">Lista degli inviti che hai ricevuto</p>
        </header>

        {error && (
          <Alert variant="danger" dismissible>
            {error}
          </Alert>
        )}

        {invitations.length === 0 ? (
          <div className="empty-state" style={{ textAlign: "center", padding: "3rem" }}>
            <h3>Nessun invito in attesa</h3>
            <p>Non hai inviti pendenti al momento</p>
          </div>
        ) : (
          <Row>
            {/* {Array(3)
              .fill(invitations)
              .flat()
              .map((invitation) => ( */}
            {invitations.map((invitation) => (
              <Col md={6} xl={4} key={invitation.id} className="mb-4">
                <div className="form-section p-4">
                  <div>
                    <div>
                      <p className="font-s-label mb-1">Invito da</p>
                      <p className="font-m-600 mb-3">
                        {`${invitation.orgId ? invitation.organization?.name : invitation.email} (${
                          invitation.orgId ? "Organizzazione" : "Agronomo"
                        })`}
                      </p>

                      <hr />

                      <p className="font-s-label mb-1">Invito al ruolo di</p>
                      <p className="font-m-600 mb-3">{translateRole(invitation.role)}</p>

                      {invitation.orgId && invitation.organization && (
                        <Fragment>
                          <p className="font-s-label mb-1">Organizzazione</p>
                          <p className="font-m-600 mb-3">{invitation.organization.name}</p>
                        </Fragment>
                      )}

                      <hr />

                      <div className="row">
                        <div className="col">
                          <p className="font-s-label mb-1">Ricezione</p>
                          <p className="font-m-600 mb-3">{formatDate(invitation.creationTime)}</p>
                        </div>

                        <div className="col">
                          <p className="font-s-label mb-1">Scadenza</p>
                          <p className="font-m-600 mb-3">{formatDate(invitation.expiresAt)}</p>
                        </div>
                      </div>
                    </div>
                    <div className="buttons-wrapper">
                      <button
                        className="trnt_btn primary m-0"
                        onClick={() => handleViewInvitation(invitation.token)}
                        style={{ width: "100%" }}
                      >
                        Vedi l'invito
                      </button>
                    </div>
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        )}
      </section>
    </Container>
  );
}
