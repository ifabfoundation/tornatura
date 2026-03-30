import React, { Fragment } from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import { useNavigate, useParams } from "react-router-dom";
import { Alert, Container, Row, Col } from "react-bootstrap";
import { unwrapResult } from "@reduxjs/toolkit";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { invitationsActions } from "../state/invitations-slice";
import { AccountTypeEnum, InvitationCreatePayload } from "@tornatura/coreapis";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { userSelectors } from "../../users/state/user-slice";

// Email validation regex
const EmailRegExp = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Role options
const ROLE_OPTIONS = [
  {
    value: "company-owner-access",
    label: "Proprietario azienda",
    description: "Accesso completo all'organizzazione",
  },
  {
    value: "company-standard-access",
    label: "Collaboratore",
    description: "Visualizzazione e modifica limitata",
  },
  {
    value: "agronomist-access",
    label: "Agronomo",
    description: "Accesso per agronomo consulente",
  },
];

const AGRONOMIST_ROLE_OPTIONS = [
  {
    value: "company-standard-access",
    label: "Collaboratore",
    description: "Visualizzazione e modifica limitata",
  },
  {
    value: "agronomist-access",
    label: "Agronomo",
    description: "Accesso per agronomo consulente",
  },
];

export function SendInvitation() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);
  const { companyId } = useParams<{ companyId: string }>();
  const [message, setMessage] = React.useState<string>();
  const [hasError, setHasError] = React.useState<boolean>(false);

  const formik = useFormik({
    initialValues: {
      email: "",
      role: "",
    },
    validationSchema: Yup.object({
      email: Yup.string().matches(EmailRegExp, "Email non valida").required("Campo obbligatorio"),
      role: Yup.string()
        .oneOf(
          ROLE_OPTIONS.map((r) => r.value),
          "Seleziona un ruolo valido"
        )
        .required("Campo obbligatorio"),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      if (!companyId) {
        setMessage("ID organizzazione mancante");
        setHasError(true);
        setSubmitting(false);
        return;
      }

      const payload: InvitationCreatePayload = {
        email: values.email,
        role: values.role,
        orgId: companyId,
      };

      dispatch(invitationsActions.sendInvitationAction(payload))
        .then(unwrapResult)
        .then((_) => {
          setMessage(`Invito inviato con successo a ${values.email}`);
          setHasError(false);
          resetForm({});
          setSubmitting(false);
          // Navigate back to invitations list after 2 seconds
          setTimeout(() => {
            navigate(`/companies/${companyId}/invitations`);
          }, 2000);
        })
        .catch((error) => {
          setMessage(error?.detail || "Errore durante l'invio dell'invito");
          setHasError(true);
          setSubmitting(false);
        });
    },
  });

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Invita", subtitle: "Subtitle" }));
  }, []);

  const handleCancel = () => {
    navigate(`/companies/${companyId}/invitations`);
  };

  const roles =
    currentUser.accountType === AccountTypeEnum.Agronomist ? AGRONOMIST_ROLE_OPTIONS : ROLE_OPTIONS;

  return (
    <Fragment>
      {message && (
        <Container className="px-0">
          <Row>
            <Col className="mb-4">
              <Alert
                variant={hasError ? "danger" : "success"}
                dismissible
                onClose={() => setMessage(undefined)}
              >
                {message}
              </Alert>
            </Col>
          </Row>
        </Container>
      )}

      <form onSubmit={formik.handleSubmit} autoComplete="off">
        <div className="form-section">
          <Container className="px-0">
            <Row>
              <Col className="mb-4">
                <h4>
                  <strong>Invia invito</strong>
                </h4>
                <p>Invita un nuovo membro a far parte dell'organizzazione</p>
              </Col>
            </Row>

            <Row>
              <Col className="mb-4">
                <div className="input-row">
                  <label>
                    Email del destinatario
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
                </div>

                <div className="input-row">
                  <label>
                    Ruolo
                    <select
                      id="role"
                      name="role"
                      onChange={formik.handleChange}
                      onBlur={formik.handleBlur}
                      value={formik.values.role}
                    >
                      <option value="">Seleziona un ruolo</option>
                      {roles.map((role) => (
                        <option key={role.value} value={role.value}>
                          {role.label} - {role.description}
                        </option>
                      ))}
                    </select>
                  </label>
                  {formik.touched.role && formik.errors.role ? (
                    <div className="error">{formik.errors.role}</div>
                  ) : null}
                </div>
              </Col>
            </Row>
          </Container>
        </div>
        <div className="buttons-wrapper mt-4 text-center">
          <button
            type="button"
            className="trnt_btn secondary"
            onClick={handleCancel}
            disabled={formik.isSubmitting}
          >
            Annulla
          </button>
          <button type="submit" className="trnt_btn primary" disabled={formik.isSubmitting}>
            {formik.isSubmitting ? "Invio in corso..." : "Invia invito"}
          </button>
        </div>
      </form>
    </Fragment>
  );
}
