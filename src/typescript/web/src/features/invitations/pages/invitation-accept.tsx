import React from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Alert, Container } from "react-bootstrap";
import { unwrapResult } from "@reduxjs/toolkit";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { invitationsActions, invitationsSelectors } from "../state/invitations-slice";
import { userSelectors } from "../../users/state/user-slice";
import keycloakInstance from "../../../providers/keycloak";
import TopHeader from "../../../components/TopHeader";
import { authStore } from "../../../providers/auth-providers";

// Helper to format timestamps
const formatDate = (timestamp: number) => {
  return new Date(timestamp).toLocaleDateString("it-IT", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// Helper to translate role
const translateRole = (role: string) => {
  switch (role) {
    case "company-owner-access":
      return "Imprenditore agricolo";
    case "company-manager-access":
      return "Manager";
    case "company-standard-access":
      return "Collaboratore";
    case "agronomist-access":
      return "Agronomo";
    default:
      return role;
  }
};

export function InvitationAccept() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const { authenticated } = React.useContext(authStore);

  const validationStatus = useAppSelector(invitationsSelectors.selectValidationStatus);
  const validatedInvitation = useAppSelector(invitationsSelectors.selectValidatedInvitation);
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);

  const [message, setMessage] = React.useState<string>();
  const [hasError, setHasError] = React.useState<boolean>(false);
  const [isProcessing, setIsProcessing] = React.useState<boolean>(false);
  const [isConfirmationStep, setIsConfirmationStep] = React.useState(false);

  React.useEffect(() => {
    if (token) {
      dispatch(invitationsActions.validateInvitationTokenAction(token));
    } else {
      setMessage("Token invito mancante");
      setHasError(true);
    }
  }, [token]);

  React.useEffect(() => {
    return () => {
      dispatch(invitationsActions.clearValidation());
    };
  }, []);

  const handleLoginClick = async () => {
    const session = {
      has_pending_invitation: true,
      pending_invitation_token: token,
    };
    sessionStorage.setItem("pending_invitation_token", JSON.stringify(session));
    await keycloakInstance.login({ redirectUri: window.location.href });
  };

  const handleSignUpClick = async () => {
    const session = {
      has_pending_invitation: true,
      pending_invitation_token: token,
    };
    sessionStorage.setItem("pending_invitation_token", JSON.stringify(session));
    navigate("/signup");
  };

  const handleAccept = async () => {
    if (!token) {
      setMessage("Token invito mancante");
      setHasError(true);
      return;
    }

    setIsProcessing(true);
    setIsConfirmationStep(true);

    // Check if this is a company owner invitation and user needs to select org
    const isCompanyOwnerInvitation =
      validatedInvitation?.invitation?.role === "company-owner-access";
    const userOrganizations = currentUser?.organizations || [];

    // Prepare payload
    const orgId =
      isCompanyOwnerInvitation && userOrganizations.length > 0
        ? userOrganizations[0].id
        : validatedInvitation?.invitation?.organization?.orgId;

    dispatch(
      invitationsActions.acceptInvitationAction({
        token,
        orgId,
      }),
    )
      .then(unwrapResult)
      .then((response) => {
        setMessage(response.message || "Invito accettato con successo!");
        setHasError(false);
        setIsProcessing(false);
        // Redirect to home after 2 seconds
        // const redirectUri = `${window.location.origin}/companies`;
        setTimeout(() => {
          sessionStorage.removeItem("pending_invitation_token");
          keycloakInstance.login({ redirectUri: window.location.origin });
        }, 2000);
      })
      .catch((error) => {
        setMessage(error?.detail || "Errore durante l'accettazione dell'invito");
        setHasError(true);
        setIsProcessing(false);
      });
  };

  const handleDecline = async () => {
    if (!token) {
      setMessage("Token invito mancante");
      setHasError(true);
      return;
    }

    setIsProcessing(true);
    setIsConfirmationStep(true);

    dispatch(invitationsActions.declineInvitationAction(token))
      .then(unwrapResult)
      .then((_) => {
        setMessage("Invito rifiutato");
        setHasError(false);
        setIsProcessing(false);
        // Redirect to home after 2 seconds
        setTimeout(() => {
          sessionStorage.removeItem("pending_invitation_token");
          navigate("/");
        }, 2000);
      })
      .catch((error) => {
        setMessage(error?.detail || "Errore durante il rifiuto dell'invito");
        setHasError(true);
        setIsProcessing(false);
      });
  };

  if (validationStatus === "pending") {
    return (
      <Container>
        <div className="loading" style={{ textAlign: "center", marginTop: "2rem" }}>
          Verifica invito in corso...
        </div>
      </Container>
    );
  }

  if (!validatedInvitation?.valid && !isConfirmationStep) {
    return (
      <div id="app" className="main-app">
        <div className="ui-right">
          <TopHeader />
          <div className="content-area">
            <div className="content">
              <Container>
                <section style={{ textAlign: "center", marginTop: "2rem" }}>
                  <Alert variant="danger">
                    <h4>Invito non valido</h4>
                    <p>{validatedInvitation?.error || "Questo invito non è valido o è scaduto"}</p>
                  </Alert>
                  <button className="trnt_btn primary" onClick={() => navigate("/")}>
                    Torna alla home
                  </button>
                </section>
              </Container>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const invitation = validatedInvitation?.invitation;

  return (
    <div id="app" className="main-app">
      <div className="ui-right">
        <TopHeader />
        <div className="content-area">
          <div className="content">
            <div className="narrow-container">
              <section className="soft bg-white mt-5">
                <h2 className="mb-4">
                  Invito a {invitation?.organization?.name || "un'organizzazione"}
                </h2>

                {message && (
                  <Alert
                    variant={hasError ? "danger" : "success"}
                    dismissible
                    onClose={() => setMessage(undefined)}
                  >
                    {message}
                  </Alert>
                )}

                <div style={{ marginBottom: "1.5rem" }}>
                  <p>
                    <strong>
                      {invitation?.inviter?.firstName} {invitation?.inviter?.lastName}
                    </strong>{" "}
                    ti ha invitato{" "}
                    {invitation?.organization?.name ? (
                      <span>
                        a far parte dell'organizzazione{" "}
                        <strong>{invitation.organization.name}</strong>
                      </span>
                    ) : (
                      <span>creare un account su Tornatura</span>
                    )}{" "}
                    come <strong>{translateRole(invitation?.role || "")}</strong>.
                  </p>

                  {invitation?.organization && (
                    <div
                      className=""
                      style={{
                        marginTop: "1rem",
                        padding: "1.5rem",
                        backgroundColor: "#f0f0f0",
                        borderRadius: "4px",
                      }}
                    >
                      <h5 className="mb-2">Dettagli organizzazione</h5>
                      <p>
                        <strong>Nome:</strong> {invitation.organization.name}
                      </p>
                      {invitation.organization.contacts && (
                        <>
                          <p>
                            <strong>Email:</strong> {invitation.organization.contacts.email}
                          </p>
                          <p>
                            <strong>Telefono:</strong> {invitation.organization.contacts.phone}
                          </p>
                        </>
                      )}
                    </div>
                  )}
                  <p style={{ marginTop: "1.5rem", fontSize: "0.875rem", color: "#6c757d" }}>
                    Questo invito scade il {formatDate(invitation?.expiresAt || 0)}
                  </p>
                  {!authenticated && (
                    <p>
                      Per poter accettare l’invito devi creare un account o se ne hai gia uno
                      autenticarti.
                    </p>
                  )}
                </div>
                <hr />
                {!authenticated ? (
                  <div className="buttons-wrapper" style={{ justifyContent: "space-between" }}>
                    <button className="trnt_btn primary" onClick={handleLoginClick}>
                      Login
                    </button>
                    <button className="trnt_btn primary" onClick={handleSignUpClick}>
                      Registrati
                    </button>
                  </div>
                ) : (
                  <div className="buttons-wrapper" style={{ justifyContent: "space-between" }}>
                    <button
                      className="trnt_btn secondary"
                      onClick={handleDecline}
                      disabled={isProcessing}
                    >
                      Rifiuta
                    </button>
                    <button
                      className="trnt_btn primary"
                      onClick={handleAccept}
                      disabled={isProcessing}
                    >
                      {isProcessing ? "Elaborazione..." : "Accetta invito"}
                    </button>
                  </div>
                )}
              </section>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
