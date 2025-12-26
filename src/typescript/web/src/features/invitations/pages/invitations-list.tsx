import React, { Fragment } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Alert, Container } from "react-bootstrap";
import { unwrapResult } from "@reduxjs/toolkit";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { invitationsActions, invitationsSelectors } from "../state/invitations-slice";
import { Invitation } from "@tornatura/coreapis";
import { ModalConfirm } from "../../../components/ModalConfirm";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";

// Helper to format timestamps
const formatDate = (timestamp: number) => {
  return new Date(timestamp).toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
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

  // -----------------------------------------------------------
  const tableOptions: TableOptions = {
    defaultSortCol: "sentDate",
    defaultSortDir: "desc",
  };

  const tableColumns: TableColumn[] = [
    {
      headerText: "Email",
      id: "email",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Ruolo",
      id: "role",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Stato",
      id: "status",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Data invio",
      id: "sentDate",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Scadenza",
      id: "expirationDate",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Azioni",
      id: "button_resend",
      buttonText: "Reinvia",
      type: "button",
      style: "secondary",
      onButtonClick: handleResend,
    },
    {
      headerText: "",
      id: "button_cancel",
      buttonText: "Revoca",
      type: "button",
      style: "danger1",
      onButtonClick: handleCancelClick,
    },
  ];

  const tableData = invitations.map((invitation) => ({
    email: invitation.email,
    role: translateRole(invitation.role),
    status: translateStatus(invitation.status),
    sentDate: formatDate(invitation.creationTime),
    expirationDate: formatDate(invitation.expiresAt),
    // action1:
    // action2:
  }));
  // -----------------------------------------------------------

  if (status === "pending") {
    return (
      <Container>
        <div className="loading">Caricamento inviti...</div>
      </Container>
    );
  }

  return (
    <Container>
      <section className="my-5">
        <div className="text-center">
          <h3 className="mb-4">Lista degli inviti fatti dall'azienda</h3>
          <p>Qui puoi vedere gli inviti che hai creato e che sono in attesa di una risposta.</p>
          <div className="my-4"></div>
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
              {/* <p>Nessun invito trovato</p> */}
              <button className="trnt_btn primary" onClick={handleSendInvitation}>
                Crea un invito
              </button>
            </div>
          ) : (
            <Fragment>
              <TableCozy columns={tableColumns} data={tableData} options={tableOptions} />
              <section className="my-3">
                <button className="trnt_btn primary m-0" onClick={handleSendInvitation}>
                  + Nuovo invito
                </button>
              </section>
            </Fragment>
          )}
        </div>
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
