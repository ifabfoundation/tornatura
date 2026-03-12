import React from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import {
  AccountTypeEnum,
  Configuration,
  InvitationPublic,
  InvitationValidateResponse,
  UserCreatePayload,
  UsersApi,
} from "@tornatura/coreapis";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, Col, Container, Row } from "react-bootstrap";
import keycloakInstance from "../providers/keycloak";
import TopHeader from "../components/TopHeader";
import { invitationsActions } from "../features/invitations/state/invitations-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import { useAppDispatch } from "../hooks";
import Stepper from "../components/Stepper";
import SignupImpactQuestionnaireStep, {
  SignupImpactQuestionnaireFormData,
} from "../features/auth/components/signup-impact-questionnaire-step";

const PhoneRegExp =
  /^((\\+[1-9]{1,4}[ \\-]*)|(\\([0-9]{2,3}\\)[ \\-]*)|([0-9]{2,4})[ \\-]*)*?[0-9]{3,4}?[ \\-]*[0-9]{3,4}?$/;
const PivaRegExp = /^\d{11}$/;

function readSignupStep(state: unknown): number | undefined {
  if (!state || typeof state !== "object") {
    return undefined;
  }

  const rawStep = (state as { signupStep?: unknown }).signupStep;
  if (typeof rawStep !== "number" || !Number.isInteger(rawStep) || rawStep < 1) {
    return undefined;
  }

  return rawStep;
}

interface SignupProps {
  formData: UserCreatePayload;
  action: string;
  isCompanyOwnerInStandardFlow?: boolean;
  onBackClick?: () => Promise<void>;
  onNextClick: (data: any) => Promise<void>;
}

function SignupStep4({ formData, action, isCompanyOwnerInStandardFlow, onBackClick, onNextClick }: SignupProps) {
  const [isProjectFormLoading, setIsProjectFormLoading] = React.useState(false);

  const formik = useFormik({
    initialValues: {
      privacy: false,
      privacy2: false,
      privacy3: false,
      privacy4: false,
    },
    validationSchema: Yup.object({
      privacy: Yup.boolean().oneOf([true], "È necessaria l'accettazione"),
      privacy2: Yup.boolean().oneOf([true], "È necessaria l'accettazione"),
      privacy3: Yup.boolean().oneOf([true], "È necessaria l'accettazione"),
      privacy4: Yup.boolean().test(
        "privacy4-required",
        "È necessaria l'accettazione",
        (value) => !isCompanyOwnerInStandardFlow || value === true
      ),
    }),
    onSubmit: async (values, { setSubmitting }) => {
      setSubmitting(true);
      await onNextClick(values);
      setSubmitting(false);
    },
  });

  const handleOpenProjectFormPdf = async (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    if (isProjectFormLoading) {
      return;
    }

    const companyName = formData.organization?.name || `${formData.firstName} ${formData.lastName}`.trim();
    const companyVat = formData.organization?.piva || formData.piva || "";
    const today = new Date().toLocaleDateString("it-IT");

    setIsProjectFormLoading(true);
    try {
      const response = await fetch(`${COREAPIS_BASE_PATH}/v1/forms/form-01/informativa-pmi/pdf`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          data: {
            DATA: today,
            PIVA: companyVat,
            RAGIONE_SOCIALE: companyName
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Impossibile caricare il documento");
      }

      const pdfBlob = await response.blob();
      const blobUrl = window.URL.createObjectURL(pdfBlob);
      window.open(blobUrl, "_blank", "noopener,noreferrer");
      window.setTimeout(() => window.URL.revokeObjectURL(blobUrl), 60000);
    } catch (error) {
      console.error(error);
      window.alert("Errore nel caricamento del modulo. Riprova più tardi.");
    } finally {
      setIsProjectFormLoading(false);
    }
  };

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="form-section">
        <div className="container px-0">
          <div className="row input-row">
            <div className="col">
              <label className="d-flex align-items-start">
                <input
                  id="privacy"
                  name="privacy"
                  type="checkbox"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  checked={formik.values.privacy}
                  className="d-inline"
                />
                <span className="my-2">
                  Ho preso visione della&nbsp;
                  <a
                    href="https://tornatura.it/f/24-04-2025-informativa-privacy-app-tornatura.pdf"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    privacy policy
                  </a>
                </span>
              </label>
              {formik.touched.privacy && formik.errors.privacy ? (
                <div className="error">{formik.errors.privacy}</div>
              ) : null}
            </div>
          </div>
          <div className="row input-row">
            <div className="col">
              <label className="d-flex align-items-start">
                <input
                  id="privacy2"
                  name="privacy2"
                  type="checkbox"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  checked={formik.values.privacy2}
                  className="d-inline"
                />
                <span className="my-2">
                  {
                    "Le informazioni e i dati conferiti nell’ambito del progetto Tornatura, tramite l’utilizzo dell'applicazione, devono essere veritieri, accurati e nella piena disponibilità di chi li fornisce. Tali dati saranno utilizzati per contribuire al progetto e saranno comunicati anche per scopi rendicontativi all’ente finanziatore. Pertanto, il dichiarante si assume la piena responsabilità di ogni informazione inserita sull'applicazione"
                  }
                </span>
              </label>
              {formik.touched.privacy2 && formik.errors.privacy2 ? (
                <div className="error">{formik.errors.privacy2}</div>
              ) : null}
            </div>
          </div>
          {isCompanyOwnerInStandardFlow && (
            <div className="row input-row">
              <div className="col">
                <label className="d-flex align-items-start">
                  <input
                    id="privacy4"
                    name="privacy4"
                    type="checkbox"
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    checked={formik.values.privacy4}
                    className="d-inline"
                  />
                  <span className="my-2">
                    Ho preso visione del&nbsp;
                    <a href="#" onClick={handleOpenProjectFormPdf}>
                      {isProjectFormLoading ? "caricamento modulo..." : "modulo informativa PMI partecipanti"}
                    </a>
                  </span>
                </label>
                {formik.touched.privacy4 && formik.errors.privacy4 ? (
                  <div className="error">{formik.errors.privacy4}</div>
                ) : null}
              </div>
            </div>
          )}
          <div className="row input-row">
            <div className="col">
              <label className="d-flex align-items-start">
                <input
                  id="privacy3"
                  name="privacy3"
                  type="checkbox"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  checked={formik.values.privacy3}
                  className="d-inline"
                />
                <span className="my-2">
                  Ho preso visione della&nbsp;
                  <a
                    href="https://tornatura.it/f/policy-newsletter-tornatura.pdf"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    privacy policy newsletter
                  </a>
                </span>
              </label>
              {formik.touched.privacy3 && formik.errors.privacy3 ? (
                <div className="error">{formik.errors.privacy3}</div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
      <div className="buttons-wrapper mt-4 text-center">
        <button className="trnt_btn secondary" type="button" onClick={onBackClick}>
          Indietro
        </button>
        <button type="submit" className="trnt_btn primary" disabled={formik.isSubmitting}>
          {formik.isSubmitting ? "caricamento..." : action}
        </button>
      </div>
    </form>
  );
}

function SignupStep3({ formData, action, onBackClick, onNextClick }: SignupProps) {
  const formik = useFormik({
    initialValues: {
      name: "",
      piva: "",
      email: "",
      phone: "",
    },
    validationSchema: Yup.object({
      name: Yup.string().required("Campo obbligatorio"),
      piva: Yup.string()
        .matches(PivaRegExp, "Partita IVA non valida")
        .required("Campo obbligatorio"),
      email: Yup.string().email("Email non valida").required("Campo obbligatorio"),
      phone: Yup.string()
        .matches(PhoneRegExp, "Telefono non valido")
        .required("Campo obbligatorio"),
    }),
    onSubmit: async (values, { setSubmitting, resetForm }) => {
      await onNextClick(values);
      resetForm({});
      setSubmitting(false);
    },
  });

  React.useEffect(() => {
    formik.setValues({
      name: formData.organization?.name || "",
      piva: formData.organization?.piva || "",
      email: formData.organization?.contacts.email || "",
      phone: formData.organization?.contacts.phone || "",
    });
  }, [formData]);

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="form-section">
        <div className="container px-0">
          <div className="row input-row">
            <div className="col">
              <label>
                Nominazione Impresa
                <input
                  id="name"
                  name="name"
                  type="text"
                  placeholder="Ragione Sociale"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.name}
                />
              </label>
              {formik.touched.name && formik.errors.name ? (
                <div className="error">{formik.errors.name}</div>
              ) : null}
            </div>
          </div>
          <div className="row input-row">
            <div className="col input-row-margin-fix">
              <label>
                Partita Iva
                <input
                  id="piva"
                  name="piva"
                  type="text"
                  placeholder="P.IVA"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.piva}
                />
              </label>
              {formik.touched.piva && formik.errors.piva ? (
                <div className="error">{formik.errors.piva}</div>
              ) : null}
            </div>
          </div>
          <div className="row input-row">
            <div className="col input-row-margin-fix">
              <label>
                Email Aziendale
                <input
                  id="email"
                  name="email"
                  type="text"
                  placeholder="Email"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.email}
                />
              </label>
              {formik.touched.email && formik.errors.email ? (
                <div className="error">{formik.errors.email}</div>
              ) : null}
            </div>
          </div>
          <div className="row input-row">
            <div className="col">
              <label>
                Telefono Aziendale
                <input
                  id="phone"
                  name="phone"
                  type="text"
                  placeholder="Telefono"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.phone}
                />
              </label>
              {formik.touched.phone && formik.errors.phone ? (
                <div className="error">{formik.errors.phone}</div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
      <div className="buttons-wrapper mt-4 text-center">
        <button className="trnt_btn secondary" onClick={onBackClick}>
          Indietro
        </button>
        <button type="submit" className="trnt_btn primary" disabled={formik.isSubmitting}>
          {formik.isSubmitting ? "caricamento..." : action}
        </button>
      </div>
    </form>
  );
}

function SignupStep2({ formData, action, onBackClick, onNextClick }: SignupProps) {
  const formik = useFormik({
    initialValues: {
      firstName: "",
      lastName: "",
      email: "",
      piva: "",
      phone: "",
    },
    validationSchema: Yup.object({
      firstName: Yup.string().required("Campo obbligatorio"),
      lastName: Yup.string().required("Campo obbligatorio"),
      email: Yup.string().email("Email non valida").required("Campo obbligatorio"),
      phone: Yup.string()
        .matches(PhoneRegExp, "Telefono non valido")
        .required("Campo obbligatorio"),
      piva: Yup.string().matches(PivaRegExp, "Partita IVA non valida"),
    }),
    onSubmit: async (values, { setSubmitting, setErrors }) => {
      if (!values.piva && formData.accountType === AccountTypeEnum.Agronomist) {
        setErrors({ piva: "Campo obbligatorio" });
      } else {
        await onNextClick(values);
      }
      setSubmitting(false);
    },
  });

  React.useEffect(() => {
    formik.setValues({
      firstName: formData.firstName || "",
      lastName: formData.lastName || "",
      email: formData.email || "",
      piva: formData.piva || "",
      phone: formData.phone || "",
    });
  }, [formData]);

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="form-section">
        <div className="container px-0">
          <div className="row input-row">
            <div className="col input-row-margin-fix">
              <label>
                Nome
                <input
                  id="name"
                  name="firstName"
                  type="text"
                  placeholder="Nome"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.firstName}
                />
              </label>
              {formik.touched.firstName && formik.errors.firstName ? (
                <div className="error">{formik.errors.firstName}</div>
              ) : null}
            </div>
          </div>
          <div className="row input-row">
            <div className="col input-row-margin-fix">
              <label>
                Cognome
                <input
                  id="lastname"
                  name="lastName"
                  type="text"
                  placeholder="Cognome"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.lastName}
                />
              </label>
              {formik.touched.lastName && formik.errors.lastName ? (
                <div className="error">{formik.errors.lastName}</div>
              ) : null}
            </div>
          </div>
          <div className="row input-row">
            <div className="col input-row-margin-fix">
              <label>
                Email di Accesso
                <input
                  id="email"
                  name="email"
                  type="text"
                  placeholder="Email"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.email}
                />
              </label>
              {formik.touched.email && formik.errors.email ? (
                <div className="error">{formik.errors.email}</div>
              ) : null}
            </div>
          </div>
          {formData.accountType === AccountTypeEnum.Agronomist && (<div className="row input-row">
            <div className="col input-row-margin-fix">
              <label>
                Partita Iva
                <input
                  id="piva"
                  name="piva"
                  type="text"
                  placeholder="P.IVA"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.piva}
                />
              </label>
              {formik.touched.piva && formik.errors.piva ? (
                <div className="error">{formik.errors.piva}</div>
              ) : null}
            </div>
          </div>)}
          <div className="row input-row">
            <div className="col">
              <label>
                Telefono
                <input
                  id="phone"
                  name="phone"
                  type="text"
                  placeholder="Telefono"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.phone}
                />
              </label>
              {formik.touched.phone && formik.errors.phone ? (
                <div className="error">{formik.errors.phone}</div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
      <div className="buttons-wrapper mt-4 text-center">
        <button className="trnt_btn secondary" type="button" onClick={onBackClick}>
          Indietro
        </button>
        <button type="submit" className="trnt_btn primary" disabled={formik.isSubmitting}>
          {formik.isSubmitting ? "caricamento..." : action}
        </button>
      </div>
    </form>
  );
}

function SignupStep1({ formData, action, onBackClick, onNextClick }: SignupProps) {
  const formik = useFormik({
    initialValues: {
      accountType: "Agronomist",
    },
    onSubmit: async (values, { setSubmitting, resetForm }) => {
      await onNextClick(values);
      resetForm({});
      setSubmitting(false);
    },
  });

  React.useEffect(() => {
    formik.setValues({
      accountType: formData.accountType || "Agronomist",
    });
  }, [formData]);

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="form-section">
        <div className="container px-0">
          <div className="row input-row">
            <div className="col">
              <label>
                Chi sei?
                <select
                  id="typeId"
                  name="accountType"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.accountType}
                >
                  <option value="Agronomist">Sono un agronomo</option>
                  <option value="Standard">Sono un imprenditore agricolo</option>
                </select>
              </label>
            </div>
          </div>
        </div>
      </div>
      <div className="buttons-wrapper mt-4 text-center">
        <button className="trnt_btn secondary" type="button" onClick={onBackClick}>
          Indietro
        </button>
        <button type="submit" className="trnt_btn primary" disabled={formik.isSubmitting}>
          {formik.isSubmitting ? "caricamento..." : action}
        </button>
      </div>
    </form>
  );
}

const COREAPIS_BASE_PATH = process.env.REACT_APP_COREAPIS_SERVER_URL;

export function Signup() {
  const dispatch = useAppDispatch();
  const location = useLocation();
  const navigate = useNavigate();
  const [step, setStep] = React.useState(readSignupStep(location.state) || 1);
  const [flow, setFlow] = React.useState<string>("Standard");
  const [invitation, setInvitation] = React.useState<InvitationPublic>();
  const [invitationToken, setInvitationToken] = React.useState<string>();
  const [impactQuestionnaireData, setImpactQuestionnaireData] =
    React.useState<SignupImpactQuestionnaireFormData>({
      employeeCount: "",
      revenueRange: "",
      damageIncidencePercent: "",
      defenseActions: [],
      annualSpendAgrochemicals: "",
      annualSpendAgronomists: "",
      annualSpendOperators: "",
      annualSpendPreventiveTools: "",
      annualSpendOther: "",
      annualSpendNone: false,
      satisfactionEffectiveness: "",
      satisfactionCostBenefit: "",
      productionProblemOutcome: "",
      monitoredKpiCount: "",
      kpiUpdateFrequency: "",
      objectivesTimeHorizon: "",
      objectivesDifficulty: "",
      productionBonusBasis: "",
      workerPromotionCriteria: "",
      lowProductivityWorkerReassignmentTiming: "",
    });
  const [formData, setFormData] = React.useState<UserCreatePayload>({
    firstName: "",
    lastName: "",
    email: "",
    piva: "",
    accountType: AccountTypeEnum.Agronomist,
    phone: "",
  });


  const goToStep = React.useCallback((nextStep: number, replace = false) => {
    setStep(nextStep);
    navigate(`${location.pathname}${location.search}${location.hash}`, {
      replace,
      state: {
        ...((location.state && typeof location.state === "object" ? location.state : {}) as Record<string, unknown>),
        signupStep: nextStep,
      },
    });
  }, [location.hash, location.pathname, location.search, location.state, navigate]);

  const handleBackClick = async () => {
    navigate(-1);
  };

  React.useEffect(() => {
    const historyStep = readSignupStep(location.state);
    if (!historyStep) {
      goToStep(step, true);
    }
  }, [goToStep, location.state, step]);

  React.useEffect(() => {
    const historyStep = readSignupStep(location.state);
    if (historyStep && historyStep !== step) {
      setStep(historyStep);
    }
  }, [location.state, step]);

  React.useEffect(() => {
    const session = sessionStorage.getItem("pending_invitation_token");
    let token = undefined;
    if (session) {
      const invitation_token = JSON.parse(session);
      if (invitation_token.has_pending_invitation) {
        token = invitation_token.pending_invitation_token;
        console.log(token, invitation_token);
        setInvitationToken(token);
        dispatch(invitationsActions.validateInvitationTokenAction(token))
          .then(unwrapResult)
          .then((response: InvitationValidateResponse) => {
            if (response.valid) {
              setInvitation(response.invitation);
              if (response.invitation) {
                setFormData((v) => {
                  let r = v;
                  if (response.invitation?.email) {
                    r = { ...v, email: response.invitation?.email };
                  }
                  if (response.invitation?.role === "agronomist-access") {
                    r = { ...r, accountType: AccountTypeEnum.Agronomist };
                  } else {
                    r = { ...r, accountType: AccountTypeEnum.Standard };
                  }
                  return r;
                });
              }
            } else {
              sessionStorage.removeItem("pending_invitation_token");
            }
          });
      }
    }
  }, []);

  React.useEffect(() => {
    if (invitation) {
      if (
        invitation.role === "company-standard-access" ||
        invitation.role === "company-manager-access"
      ) {
        setFlow("Simple");
      }
    }
  }, [invitation]);

  const isCompanyOwnerInStandardFlow =
    flow === "Standard" && formData.accountType === AccountTypeEnum.Standard;
  const standardStepperSteps = isCompanyOwnerInStandardFlow
    ? [
        { label: "Profilo", step: 1 },
        { label: "Dati Personali", step: 2 },
        { label: "Dati Aziendali", step: 3 },
        { label: "Consensi", step: 4 },
        { label: "Questionario", step: 5 },
        { label: "Esito", step: 6 },
      ]
    : [
        { label: "Profilo", step: 1 },
        { label: "Dati Personali", step: 2 },
        { label: "Consensi", step: 4 },
        { label: "Esito", step: 5 },
      ];
  const simpleFlowStepperSteps = [
    { label: "Dati Personali", step: 1 },
    { label: "Consensi", step: 2 },
    { label: "Esito", step: 3 },
  ];
  const standardQuestionnaireStep = standardStepperSteps.find(
    (stepItem) => stepItem.label === "Questionario"
  )?.step;
  
  const standardSuccessStep = standardStepperSteps[standardStepperSteps.length - 1].step;
  const simpleFlowSuccessStep = simpleFlowStepperSteps[simpleFlowStepperSteps.length - 1].step;
  const currentStandardStepIndex = Math.max(
    standardStepperSteps.findIndex((stepItem) => stepItem.step === step),
    0
  );
  const currentSimpleFlowStepIndex = Math.max(
    simpleFlowStepperSteps.findIndex((stepItem) => stepItem.step === step),
    0
  );
  const getNextMappedStep = (
    stepperSteps: Array<{ label: string; step: number }>,
    currentStep: number
  ) => {
    const currentStepIndex = stepperSteps.findIndex((stepItem) => stepItem.step === currentStep);
    if (currentStepIndex < 0 || currentStepIndex >= stepperSteps.length - 1) {
      return undefined;
    }
    return stepperSteps[currentStepIndex + 1].step;
  };

  const createAccountAction = async (payload: UserCreatePayload) => {
    const apiConfig = new Configuration({ basePath: `${COREAPIS_BASE_PATH}` });
    const usersApi = new UsersApi(apiConfig);
    const response = await usersApi.registerUser(payload);

    if (response.status === 201) {
      if (flow === "Standard") {
        goToStep(standardSuccessStep);
      } else {
        goToStep(simpleFlowSuccessStep);
      }
    } else {
      console.error("Error creating account", response);
    }
  };

  const handleNextClick = async (data: any) => {
    if (flow === "Standard") {
      if (step === 1) {
        setFormData({
          ...formData,
          accountType: data.accountType,
        });
        const nextStep = getNextMappedStep(standardStepperSteps, step);
        if (nextStep !== undefined) {
          goToStep(nextStep);
        }
      } else if (step === 2) {
        const payload = {
          ...formData,
          firstName: data.firstName,
          lastName: data.lastName,
          email: data.email,
          piva: data.piva,
          phone: data.phone,
        };
        setFormData(payload);
        const nextStep = getNextMappedStep(standardStepperSteps, step);
        if (nextStep !== undefined) {
          goToStep(nextStep);
        }
      } else if (step === 3) {
        const payload = {
          ...formData,
          organization: {
            name: data.name,
            piva: data.piva,
            contacts: {
              email: data.email,
              phone: data.phone,
            },
          },
        };
        setFormData(payload);
        const nextStep = getNextMappedStep(standardStepperSteps, step);
        if (nextStep !== undefined) {
          goToStep(nextStep);
        }
      } else if (step === 4) {
        if (standardQuestionnaireStep !== undefined) {
          goToStep(standardQuestionnaireStep);
        } else {
          await createAccountAction(formData);
        }
      } else if (step === standardQuestionnaireStep) {
        setImpactQuestionnaireData(data);
        await createAccountAction({
          ...formData,
          questionnaire: data,
        } as any);
      }
    } else {
      if (step === 1) {
        const payload = {
          ...formData,
          accountType: AccountTypeEnum.Standard,
          firstName: data.firstName,
          lastName: data.lastName,
          email: data.email,
          piva: data.piva,
          phone: data.phone,
        };
        setFormData(payload);
        const nextStep = getNextMappedStep(simpleFlowStepperSteps, step);
        if (nextStep !== undefined) {
          goToStep(nextStep);
        }
      } else if (step === 2) {
        await createAccountAction(formData);
      }
    }
  };

  const handleLoginClick = async () => {
    // If there's an invitation token, redirect to accept page after login
    if (invitationToken) {
      const redirectUri = `${window.location.origin}/invitations/accept?token=${invitationToken}`;
      await keycloakInstance.login({ redirectUri: redirectUri });
    } else {
      await keycloakInstance.login({ redirectUri: window.location.origin });
    }
  };

  if (flow === "Standard") {
    return (
      <div id="app" className="main-app">
        <div className="ui-right">
          <TopHeader />
          <div className="content-area">
            <div className="content">
              <Stepper
                items={standardStepperSteps.map((stepItem) => stepItem.label)}
                currentStep={currentStandardStepIndex}
                handleStepClick={(stepIndex) => {
                  goToStep(standardStepperSteps[stepIndex].step);
                }}
              />
              <div className="form-wrapper">
                {step === 1 && (
                  <SignupStep1
                    formData={formData}
                    action="Avanti"
                    onNextClick={handleNextClick}
                    onBackClick={handleBackClick}
                  />
                )}
                {step === 2 && (
                  <SignupStep2
                    formData={formData}
                    action="Avanti"
                    onBackClick={handleBackClick}
                    onNextClick={handleNextClick}
                  />
                )}
                {step === 3 && (
                  <SignupStep3
                    formData={formData}
                    action="Avanti"
                    onBackClick={handleBackClick}
                    onNextClick={handleNextClick}
                  />
                )}
                {step === 4 && (
                  <SignupStep4
                    formData={formData}
                    action={standardQuestionnaireStep !== undefined ? "Avanti" : "Iscriviti"}
                    onBackClick={handleBackClick}
                    onNextClick={handleNextClick}
                    isCompanyOwnerInStandardFlow={isCompanyOwnerInStandardFlow}
                  />
                )}
                {step === standardQuestionnaireStep && (
                  <SignupImpactQuestionnaireStep
                    initialValues={impactQuestionnaireData}
                    action="Iscriviti"
                    onBackClick={handleBackClick}
                    onNextClick={handleNextClick}
                  />
                )}
                {step === standardSuccessStep && (
                  <Container>
                    <Row>
                      <Col></Col>
                      <Col md="auto" className="text-center">
                        <h1 className="mb-3">Registrazione</h1>
                        <div className="bg-white p-4 rounded">
                          <div
                            className="spacer d-none d-md-block"
                            style={{ width: "320px" }}
                          ></div>
                          <p className="my-3">
                            Registrazione Avvenuta con successo. Riceverai una email di conferma
                            dell'avvenuta registrazione
                          </p>
                          <Button className="trnt_btn accent wide" onClick={handleLoginClick}>
                            Vai al Login
                          </Button>
                        </div>
                      </Col>
                      <Col></Col>
                    </Row>
                  </Container>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  } else {
    return (
      <div id="app" className="main-app">
        <div className="ui-right">
          <TopHeader />
          <div className="content-area">
            <div className="content">
              <Stepper
                items={simpleFlowStepperSteps.map((stepItem) => stepItem.label)}
                currentStep={currentSimpleFlowStepIndex}
                handleStepClick={(stepIndex) => {
                  goToStep(simpleFlowStepperSteps[stepIndex].step);
                }}
              />

              <div className="form-wrapper">
                {step === 1 && (
                  <SignupStep2
                    formData={formData}
                    action="Avanti"
                    onBackClick={handleBackClick}
                    onNextClick={handleNextClick}
                  />
                )}
                {step === 2 && (
                  <SignupStep4
                    formData={formData}
                    action="Iscriviti"
                    onBackClick={handleBackClick}
                    onNextClick={handleNextClick}
                    isCompanyOwnerInStandardFlow={isCompanyOwnerInStandardFlow}
                  />
                )}
                {step === 3 && (
                  <Container>
                    <Row>
                      <Col></Col>
                      <Col md="auto" className="text-center">
                        <h1 className="mb-3">Registrazione</h1>
                        <div className="bg-white p-4 rounded">
                          <div
                            className="spacer d-none d-md-block"
                            style={{ width: "320px" }}
                          ></div>
                          <p className="my-3">
                            Registrazione Avvenuta con successo. Riceverai una email di conferma
                            dell'avvenuta registrazione
                          </p>
                          <Button className="trnt_btn accent wide" onClick={handleLoginClick}>
                            Vai al Login
                          </Button>
                        </div>
                      </Col>
                      <Col></Col>
                    </Row>
                  </Container>
                )}
              </div>
              {/*                 </Col>
                  <Col></Col>
                </Row>
              </Container> */}
            </div>
          </div>
        </div>
      </div>
    );
  }
}
