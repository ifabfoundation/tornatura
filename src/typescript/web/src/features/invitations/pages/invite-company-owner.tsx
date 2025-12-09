import React from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import { useNavigate } from "react-router-dom";
import { Alert, Container } from "react-bootstrap";
import { unwrapResult } from "@reduxjs/toolkit";
import { useAppDispatch } from "../../../hooks";
import { invitationsActions } from "../state/invitations-slice";
import { InvitationCreatePayload } from "@tornatura/coreapis";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";

// Email validation regex
const EmailRegExp = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function InviteCompanyOwner() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [message, setMessage] = React.useState<string>();
  const [hasError, setHasError] = React.useState<boolean>(false);

  const formik = useFormik({
    initialValues: {
      email: "",
    },
    validationSchema: Yup.object({
      email: Yup.string()
        .matches(EmailRegExp, "Email non valida")
        .required("Campo obbligatorio"),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      const payload: InvitationCreatePayload = {
        email: values.email,
        role: "company-owner-access",
        // Omit orgId entirely for agronomist inviting non-existent company owner
      };

      dispatch(invitationsActions.sendInvitationAction(payload))
        .then(unwrapResult)
        .then((_) => {
          setMessage(`Invito inviato con successo a ${values.email}`);
          setHasError(false);
          resetForm({});
          setSubmitting(false);
          // Navigate back after 2 seconds
          setTimeout(() => {
            navigate("/");
          }, 2000);
        })
        .catch((error) => {
          setMessage(
            error?.detail || "Errore durante l'invio dell'invito"
          );
          setHasError(true);
          setSubmitting(false);
        });
    },
  });

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Invita azienda", subtitle: "Subtitle" }));
  }, []);

  const handleCancel = () => {
    navigate("/companies");
  };

  return (
    <Container>
      <section>
        <header>
          <h1>Invita proprietario azienda</h1>
          <p>
            Invita un proprietario di azienda a creare il suo profilo e la sua organizzazione.
            Dopo aver creato la sua organizzazione, verrai automaticamente aggiunto come agronomo.
          </p>
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

        <form onSubmit={formik.handleSubmit} autoComplete="off">
          <div className="input-row">
            <label>
              Email del proprietario azienda
              <input
                id="email"
                name="email"
                type="email"
                placeholder="email@esempio.com"
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                value={formik.values.email}
              />
            </label>
            {formik.touched.email && formik.errors.email ? (
              <div className="error">{formik.errors.email}</div>
            ) : null}
            <small style={{ color: "#6c757d", marginTop: "0.5rem", display: "block" }}>
              Il destinatario riceverà un'email con le istruzioni per creare il suo profilo
              e la sua organizzazione. Una volta completata la registrazione, verrai aggiunto
              alla sua organizzazione come agronomo.
            </small>
          </div>

          <hr />

          <div className="buttons-wrapper">
            <button
              type="button"
              className="trnt_btn secondary"
              onClick={handleCancel}
              disabled={formik.isSubmitting}
            >
              Annulla
            </button>
            <button
              type="submit"
              className="trnt_btn primary"
              disabled={formik.isSubmitting}
            >
              {formik.isSubmitting ? "Invio in corso..." : "Invia invito"}
            </button>
          </div>
        </form>
      </section>
    </Container>
  );
}
