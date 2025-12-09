import React, { Fragment } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Alert, Container } from "react-bootstrap";
import { unwrapResult } from "@reduxjs/toolkit";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { invitationsActions, invitationsSelectors } from "../state/invitations-slice";
import { Invitation } from "@tornatura/coreapis";
import { ModalConfirm } from "../../../components/ModalConfirm";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";

// Helper to format timestamps
const formatDate = (timestamp: number) => {
  return new Date(timestamp).toLocaleDateString("it-IT", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
};

// Helper to get status badge class
const getStatusClass = (status: string) => {
  switch (status) {
    case "pending":
      return "badge-warning";
    case "accepted":
      return "badge-success";
    case "declined":
      return "badge-danger";
    case "expired":
      return "badge-secondary";
    case "revoked":
      return "badge-dark";
    default:
      return "badge-secondary";
  }
};

// Helper to translate status
const translateStatus = (status: string) => {
  switch (status) {
    case "pending":
      return "In attesa";
    case "accepted":
      return "Accettato";
    case "declined":
      return "Rifiutato";
    case "expired":
      return "Scaduto";
    case "revoked":
      return "Revocato";
    default:
      return status;
  }
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

export function InvitationsList() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { companyId } = useParams<{ companyId: string }>();

  const invitations = useAppSelector(invitationsSelectors.selectAllInvitations);
  const status = useAppSelector(invitationsSelectors.selectInvitationsStatus);
  const error = useAppSelector(invitationsSelectors.selectInvitationsError);

  const [message, setMessage] = React.useState<string>();
  const [hasError, setHasError] = React.useState<boolean>(false);
  const [showCancelModal, setShowCancelModal] = React.useState<boolean>(false);
  const [selectedInvitation, setSelectedInvitation] = React.useState<Invitation | null>(null);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Gestione Inviti", subtitle: "Subtitle" }));
  }, []);

  // Load invitations on mount
  React.useEffect(() => {
    if (companyId) {
      dispatch(
        invitationsActions.fetchOrganizationInvitationsAction({
          orgId: companyId,
        })
      );
    }
  }, [dispatch, companyId]);

  const handleSendInvitation = () => {
    navigate(`/companies/${companyId}/send-invitation`);
  };

  const handleCancelClick = (invitation: Invitation) => {
    setSelectedInvitation(invitation);
    setShowCancelModal(true);
  };

  const handleCancelConfirm = () => {
    if (selectedInvitation) {
      dispatch(invitationsActions.cancelInvitationAction(selectedInvitation.id))
        .then(unwrapResult)
        .then((_) => {
          setMessage("Invito revocato con successo");
          setHasError(false);
          setShowCancelModal(false);
          setSelectedInvitation(null);
        })
        .catch((error) => {
          setMessage(error?.detail || "Errore durante la revoca dell'invito");
          setHasError(true);
          setShowCancelModal(false);
        });
    }
  };

  const handleResend = (invitation: Invitation) => {
    dispatch(invitationsActions.resendInvitationAction(invitation.id))
      .then(unwrapResult)
      .then((_) => {
        setMessage(`Invito rinviato con successo a ${invitation.email}`);
        setHasError(false);
      })
      .catch((error) => {
        setMessage(error?.detail || "Errore durante il reinvio dell'invito");
        setHasError(true);
      });
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
          <h1>Gestione inviti</h1>
          <button className="trnt_btn primary" onClick={handleSendInvitation}>
            + Invia nuovo invito
          </button>
        </header>

        {message && (
          <Alert
            variant={hasError ? "danger" : "success"}
            dismissible
            onClose={() => setMessage(undefined)}
          >
            {message}
          </Alert>
        )}

        {error && (
          <Alert variant="danger" dismissible>
            {error}
          </Alert>
        )}

        {invitations.length === 0 ? (
          <div className="empty-state">
            <p>Nessun invito trovato</p>
            <button className="trnt_btn primary" onClick={handleSendInvitation}>
              Invia il primo invito
            </button>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table table-hover">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Ruolo</th>
                  <th>Stato</th>
                  <th>Data invio</th>
                  <th>Scadenza</th>
                  <th>Azioni</th>
                </tr>
              </thead>
              <tbody>
                {invitations.map((invitation) => (
                  <tr key={invitation.id}>
                    <td>{invitation.email}</td>
                    <td>{translateRole(invitation.role)}</td>
                    <td>
                      <span className={`badge ${getStatusClass(invitation.status)}`}>
                        {translateStatus(invitation.status)}
                      </span>
                    </td>
                    <td>{formatDate(invitation.creationTime)}</td>
                    <td>{formatDate(invitation.expiresAt)}</td>
                    <td>
                      {invitation.status === "pending" && (
                        <Fragment>
                          <button
                            className="trnt_btn trnt_btn-sm secondary"
                            onClick={() => handleResend(invitation)}
                            style={{ marginRight: "0.5rem" }}
                          >
                            Reinvia
                          </button>
                          <button
                            className="trnt_btn trnt_btn-sm danger"
                            onClick={() => handleCancelClick(invitation)}
                          >
                            Revoca
                          </button>
                        </Fragment>
                      )}
                      {invitation.status === "accepted" && (
                        <span className="text-muted">
                          {invitation.acceptedAt && `Accettato il ${formatDate(invitation.acceptedAt)}`}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {showCancelModal && selectedInvitation && (
        <ModalConfirm
          handleCancel={() => setShowCancelModal(false)}
          title="Conferma revoca invito"
          content={
            <p>
              Sei sicuro di voler revocare l'invito per <strong>{selectedInvitation.email}</strong>?
              <br />
              L'utente non potrà più accettare questo invito.
            </p>
          }
          action="Revoca invito"
          handleConfirm={handleCancelConfirm}
        />
      )}
    </Container>
  );
}
