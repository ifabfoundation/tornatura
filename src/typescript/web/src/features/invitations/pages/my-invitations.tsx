import React from "react";
import { useNavigate } from "react-router-dom";
import { Alert, Container, Card, Col, Row } from "react-bootstrap";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { invitationsActions, invitationsSelectors } from "../state/invitations-slice";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";

// Helper to format timestamps
const formatDate = (timestamp: number) => {
  return new Date(timestamp).toLocaleDateString("it-IT", {
    year: "numeric",
    month: "long",
    day: "numeric",
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

  const invitations = useAppSelector(invitationsSelectors.selectAllInvitations);
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
        <header>
          <h1>Inviti ricevuti</h1>
          <p>Visualizza e gestisci gli inviti che hai ricevuto</p>
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
            {invitations.map((invitation) => (
              <Col md={6} xl={4} key={invitation.id}>
                <Card className="with-hover-effect" style={{ marginBottom: "1.5rem" }}>
                  <Card.Header>
                    <strong>
                      {invitation.orgId ? "Invito da organizzazione" : "Invito da agronomo"}
                    </strong>
                  </Card.Header>
                  <Card.Body>
                    <div style={{ marginBottom: "1rem" }}>
                      <p>
                        <strong>Da:</strong> {invitation.inviterId}
                      </p>
                      <p>
                        <strong>Ruolo:</strong> {translateRole(invitation.role)}
                      </p>
                      {invitation.orgId && (
                        <p>
                          <strong>Organizzazione:</strong> {invitation.orgId}
                        </p>
                      )}
                      <p style={{ fontSize: "0.875rem", color: "#6c757d" }}>
                        <strong>Ricevuto:</strong> {formatDate(invitation.creationTime)}
                      </p>
                      <p style={{ fontSize: "0.875rem", color: "#6c757d" }}>
                        <strong>Scade:</strong> {formatDate(invitation.expiresAt)}
                      </p>
                    </div>
                    <button
                      className="trnt_btn primary"
                      onClick={() => handleViewInvitation(invitation.token)}
                      style={{ width: "100%" }}
                    >
                      Visualizza invito
                    </button>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </section>
    </Container>
  );
}
