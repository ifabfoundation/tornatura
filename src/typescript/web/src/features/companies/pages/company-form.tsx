import { useFormik } from "formik";
import React from "react";
import * as Yup from "yup";
import { Alert, Col, Container, Row } from "react-bootstrap";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { useAppDispatch } from "../../../hooks";
import { OrganizationCreatePayload } from "@tornatura/coreapis";
import { companiesActions } from "../state/companies-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import { useNavigate } from "react-router-dom";
import keycloakInstance from "../../../providers/keycloak";
import { getUserInfo } from "../../users/utils";
import { userActions } from "../../users/state/user-slice";
import SignupImpactQuestionnaireStep, {
  SignupImpactQuestionnaireFormData,
} from "../../auth/components/signup-impact-questionnaire-step";
import Stepper from "../../../components/Stepper";

const PhoneRegExp =
  /^((\\+[1-9]{1,4}[ \\-]*)|(\\([0-9]{2,3}\\)[ \\-]*)|([0-9]{2,4})[ \\-]*)*?[0-9]{3,4}?[ \\-]*[0-9]{3,4}?$/;
const PivaRegExp = /^\d{11}$/;
const COREAPIS_BASE_PATH = process.env.REACT_APP_COREAPIS_SERVER_URL;
const OBJECT_STORAGE_ENDPOINT = process.env.REACT_APP_OBJECT_STORAGE_ENDPOINT;

const initialQuestionnaireValues: SignupImpactQuestionnaireFormData = {
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
};

type CompanyPayloadDraft = Omit<OrganizationCreatePayload, "questionnaire"> & {
  questionnaire?: never;
};

interface CompanyStepProps {
  initialCompany?: CompanyPayloadDraft;
  action: string;
  onBackClick: () => void;
  onNextClick: (company: CompanyPayloadDraft) => void;
}

interface CompanyConsentsStepProps {
  company?: CompanyPayloadDraft;
  action: string;
  onBackClick: () => Promise<void>;
  onNextClick: () => Promise<void>;
}

function CompanyStep({ initialCompany, action, onBackClick, onNextClick }: CompanyStepProps) {
  const formik = useFormik({
    initialValues: {
      name: initialCompany?.name || "",
      piva: initialCompany?.piva || "",
      email: initialCompany?.contacts.email || "",
      phone: initialCompany?.contacts.phone || "",
    },
    enableReinitialize: true,
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
    onSubmit: async (values, { setSubmitting }) => {
      const organization: CompanyPayloadDraft = {
        name: values.name,
        piva: values.piva,
        contacts: {
          email: values.email,
          phone: values.phone,
        },
      };
      onNextClick(organization);
      setSubmitting(false);
    },
  });

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="form-section">
        <Container className="px-0">
          <Row>
            <Col className="mb-4">
              <h4>
                <strong>Registra azienda</strong>
              </h4>
              <p>Inserisci i dati dell'azienda da gestire in Tornatura.</p>
            </Col>
          </Row>

          <Row>
            <Col>
              <div className="input-row">
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

              <div className="input-row">
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

              <div className="input-row">
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

              <div className="input-row">
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
            </Col>
          </Row>
        </Container>
      </div>

      <div className="buttons-wrapper mt-4 text-center">
        <button
          type="button"
          className="trnt_btn secondary"
          onClick={onBackClick}
          disabled={formik.isSubmitting}
        >
          Annulla
        </button>
        <button type="submit" className="trnt_btn primary" disabled={formik.isSubmitting}>
          {formik.isSubmitting ? "Caricamento..." : action}
        </button>
      </div>
    </form>
  );
}

function CompanyConsentsStep({
  company,
  action,
  onBackClick,
  onNextClick,
}: CompanyConsentsStepProps) {
  const [isProjectFormLoading, setIsProjectFormLoading] = React.useState(false);

  const formik = useFormik({
    initialValues: {
      privacy: false,
      privacy4: false,
    },
    validationSchema: Yup.object({
      privacy: Yup.boolean().oneOf([true], "È necessaria l'accettazione"),
      privacy4: Yup.boolean().oneOf([true], "È necessaria l'accettazione"),
    }),
    onSubmit: async (_values, { setSubmitting }) => {
      setSubmitting(true);
      await onNextClick();
      setSubmitting(false);
    },
  });

  const handleOpenProjectFormPdf = async (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    if (isProjectFormLoading) {
      return;
    }

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
            PIVA: company?.piva || "",
            RAGIONE_SOCIALE: company?.name || "",
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
                  Ho letto e accetto i &nbsp;
                  <a
                    href={`${OBJECT_STORAGE_ENDPOINT}/public/media/termini-di-servizio.pdf`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Termini di servizio
                  </a>
                  &nbsp; e la &nbsp;
                  <a
                    href={`${OBJECT_STORAGE_ENDPOINT}/public/media/informativa-privacy.pdf`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Privacy policy
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
                  id="company-privacy4"
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
                    {isProjectFormLoading
                      ? "caricamento modulo..."
                      : "modulo informativa PMI partecipanti"}
                  </a>
                </span>
              </label>
              {formik.touched.privacy4 && formik.errors.privacy4 ? (
                <div className="error">{formik.errors.privacy4}</div>
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
          {formik.isSubmitting ? "Caricamento..." : action}
        </button>
      </div>
    </form>
  );
}

export function CompanyForm() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [message, setMessage] = React.useState<string>();
  const [step, setStep] = React.useState<"company" | "consents" | "questionnaire">("company");
  const [companyPayload, setCompanyPayload] = React.useState<CompanyPayloadDraft>();
  const [questionnaireValues, setQuestionnaireValues] =
    React.useState<SignupImpactQuestionnaireFormData>(initialQuestionnaireValues);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Nuova azienda", subtitle: "Aziende gestite" }));
  }, []);

  const stepperSteps = [
    { label: "Dati Aziendali", step: "company" },
    { label: "Consensi", step: "consents" },
    { label: "Questionario", step: "questionnaire" },
  ] as const;
  const currentStepIndex = Math.max(
    stepperSteps.findIndex((stepItem) => stepItem.step === step),
    0,
  );

  const goToPreviousStep = () => {
    if (step === "company") {
      navigate("/m/companies");
      return;
    }

    if (step === "consents") {
      setStep("company");
      return;
    }

    setStep("consents");
  };

  const createOrganization = async (questionnaire: SignupImpactQuestionnaireFormData) => {
    if (!companyPayload) {
      setStep("company");
      setMessage("Completa prima i dati aziendali.");
      return;
    }

    setMessage(undefined);
    setQuestionnaireValues(questionnaire);

    try {
      const payloadWithQuestionnaire = {
        ...companyPayload,
        questionnaire,
      } as OrganizationCreatePayload & { questionnaire: SignupImpactQuestionnaireFormData };
      const createdOrganization = await dispatch(
        companiesActions.addNewCompanyAction(payloadWithQuestionnaire),
      ).then(unwrapResult);
      await keycloakInstance.updateToken(-1);
      const profile = await getUserInfo();
      if (profile) {
        await dispatch(userActions.setCurrentUserAction(profile));
      }
      navigate(`/m/companies/${createdOrganization.orgId}/fields`);
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.detail;
      setMessage(
        detail === "Organization with the same name already exists"
          ? "Un'azienda con lo stesso nome esiste già sulla piattaforma."
          : "Non è stato possibile creare l'azienda. Riprova più tardi.",
      );
    }
  };

  return (
    <Container className="px-0">
      <Stepper
        items={stepperSteps.map((stepItem) => stepItem.label)}
        currentStep={currentStepIndex}
        handleStepClick={(stepIndex) => {
          setStep(stepperSteps[stepIndex].step);
        }}
        handleBackClick={goToPreviousStep}
        handleExitClick={() => navigate("/m/companies")}
      />

      {message && (
        <Row>
          <Col className="mb-4">
            <Alert variant="danger" dismissible onClose={() => setMessage(undefined)}>
              {message}
            </Alert>
          </Col>
        </Row>
      )}

      <div className="form-wrapper">
        {step === "company" && (
          <CompanyStep
            initialCompany={companyPayload}
            action="Avanti"
            onBackClick={() => navigate("/m/companies")}
            onNextClick={(organization) => {
              setMessage(undefined);
              setCompanyPayload(organization);
              setStep("consents");
            }}
          />
        )}

        {step === "consents" && (
          <CompanyConsentsStep
            company={companyPayload}
            action="Avanti"
            onBackClick={async () => setStep("company")}
            onNextClick={async () => setStep("questionnaire")}
          />
        )}

        {step === "questionnaire" && (
          <SignupImpactQuestionnaireStep
            action="Registra azienda"
            initialValues={questionnaireValues}
            onBackClick={async () => setStep("consents")}
            onNextClick={createOrganization}
          />
        )}
      </div>
    </Container>
  );
}
