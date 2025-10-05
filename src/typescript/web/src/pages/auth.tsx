import React from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import { AccountTypeEnum, Configuration, UserCreatePayload, UsersApi } from "@tornatura/coreapis";
import { useNavigate } from "react-router-dom";
import { Button, Col, Container, Row } from "react-bootstrap";
import keycloakInstance from "../providers/keycloak";
import TopHeader from "../components/TopHeader";


const PhoneRegExp = /^((\\+[1-9]{1,4}[ \\-]*)|(\\([0-9]{2,3}\\)[ \\-]*)|([0-9]{2,4})[ \\-]*)*?[0-9]{3,4}?[ \\-]*[0-9]{3,4}?$/
const PivaRegExp = /^[1-7]\d{6}\d{3,4}[0-9]$/

interface SignupProps {
  formData: UserCreatePayload;
  action: string;
  onBackClick?: () => Promise<void>;
  onNextClick: (data: any) => Promise<void>;
}

function SignupStep4({ formData, action, onBackClick, onNextClick }: SignupProps) {
  const formik = useFormik({
    initialValues: {
      privacy: false,
      privacy2: false,
    },
    validationSchema: Yup.object({
      privacy: Yup.boolean().oneOf([true], "È necessaria l'accettazione"),
      privacy2: Yup.boolean().oneOf([true], "È necessaria l'accettazione"),
    }),
    onSubmit: (values, { setSubmitting, setErrors }) => {
      onNextClick(values);
      setSubmitting(false);
    },
  });

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="input-row">
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
            Ho preso visione della&nbsp; <a href="informativa_privacy.pdf">privacy policy</a>
          </span>
        </label>
        {formik.touched.privacy && formik.errors.privacy ? (
          <div className="error">{formik.errors.privacy}</div>
        ) : null}
      </div>
      <div className="input-row">
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
      <hr />
      <div className="buttons-wrapper">
        <button className="trnt_btn secondary" type="button" onClick={onBackClick}>
          Indietro
        </button>
        <input type="submit" className="primary" value={action} />
      </div>
    </form>
  );
}

function SignupStep3({ formData, action, onBackClick, onNextClick }: SignupProps) {
  const formik = useFormik({
    initialValues: {
      name: "",
      piva: "",
      state: "",
      city: "",
      legalForm: "",
      rappresentative: "",
      rappresentativeContact: "",
      email: "",
      phone: "",
    },
    validationSchema: Yup.object({
      name: Yup.string().required("Campo obbligatorio"),
      piva: Yup.string().matches(PivaRegExp, "Partita IVA non valida").required("Campo obbligatorio"),
      email: Yup.string().email("Email non valida").required("Campo obbligatorio"),
      phone: Yup.string().matches(PhoneRegExp, "Telefono non valido").required("Campo obbligatorio"),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      onNextClick(values)
        .then((_) => {
          resetForm({});
        })
        .catch((_) => {
          setSubmitting(false);
        })
        .finally(() => {
          setSubmitting(false);
        });
    },
  });

  React.useEffect(() => { 
    formik.setValues({
      name: formData.organization?.name || "",
      piva: formData.organization?.piva || "",
      state: "",
      city: "",
      legalForm: "",
      rappresentative: "",
      rappresentativeContact: "",
      email: formData.organization?.contacts.email || "",
      phone: formData.organization?.contacts.phone || "",
    });
  }, [formData]);

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
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
          Email
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
      <hr />
      <div className="buttons-wrapper">
        <button className="trnt_btn secondary" onClick={onBackClick}>
          Indietro
        </button>
        <input type="submit" className="primary" value={action} />
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
      phone: ""
    },
    validationSchema: Yup.object({
      firstName: Yup.string().required("Campo obbligatorio"),
      lastName: Yup.string().required("Campo obbligatorio"),
      email: Yup.string().email("Email non valida").required("Campo obbligatorio"),
      phone: Yup.string().matches(PhoneRegExp, "Telefono non valido").required("Campo obbligatorio"),
      piva: Yup.string().matches(PivaRegExp, "Partita IVA non valida")
    }),
    onSubmit: (values, { setSubmitting, setErrors }) => {
      if (!values.piva && formData.accountType === AccountTypeEnum.Agronomist) {
        setErrors({ piva: "Campo obbligatorio" });
      } else {
        onNextClick(values);
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
      phone: formData.phone || ""
    });
  }, [formData]);

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="input-row">
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
      <div className="input-row">
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
      <div className="input-row">
        <label>
          Email
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
      {formData.accountType === AccountTypeEnum.Agronomist && (
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
      )}
      <div className="input-row">
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
      <hr />
      <div className="buttons-wrapper">
        <button className="trnt_btn secondary" type="button" onClick={onBackClick}>
          Indietro
        </button>
        <input type="submit" className="primary" value={action} />
      </div>
    </form>
  );
}

function SignupStep1({ formData, action, onBackClick, onNextClick }: SignupProps) {
  const formik = useFormik({
    initialValues: {
      accountType: "Agronomist",
    },
    onSubmit: (values, { setSubmitting, resetForm }) => {
      onNextClick(values);
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
      <div className="input-row">
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
      <hr />
      <div className="buttons-wrapper">
        <button className="trnt_btn secondary" type="button" onClick={onBackClick}>
          Indietro
        </button>
        <input type="submit" className="primary" value={action} />
      </div>
    </form>
  );
}

const COREAPIS_BASE_PATH = process.env.REACT_APP_COREAPIS_SERVER_URL;

export function Signup() {
  const navigate = useNavigate();
  const [step, setStep] = React.useState(1);
  const [formData, setFormData] = React.useState<UserCreatePayload>({
    firstName: "",
    lastName: "",
    email: "",
    piva: "",
    accountType: AccountTypeEnum.Agronomist,
    phone: "",
  });

  const createAccountAction = async (payload: UserCreatePayload) => {
    const apiConfig = new Configuration({ basePath: `${COREAPIS_BASE_PATH}` });
    const usersApi = new UsersApi(apiConfig);
    const response = await usersApi.registerUser(payload);
    
    if (response.status === 201) {
      setStep(5);
    } else {
      console.error("Error creating account", response);
    }
  };

  const handleNextClick = async (data: any) => {
    if (step === 1) {
      setFormData({
        ...formData,
        accountType: data.accountType,
      });
      setStep(step + 1);
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
      if (formData.accountType === AccountTypeEnum.Standard) {
        setStep(step + 1);
      } else {
        setStep(step + 2);
      }
    } else if (step === 3) {
      const payload = {
        ...formData,
        organization: {
          name: data.name,
          piva: data.piva,
          legalForm: "",
          office: {
            state: data.state,
            city: data.city,
          },
          rapresentative: data.rappresentative,
          rapresentativeContact: data.rappresentativeContact,
          contacts: {
            email: data.email,
            phone: data.phone,
          },
        },
      };
      setFormData(payload);
      setStep(step + 1);
    } else if (step === 4) {
      await createAccountAction(formData);
    }
  };

  const handleBackClick = async () => {
    if (step > 1) {
      if (step === 4 && formData.accountType === AccountTypeEnum.Agronomist) {
        setStep(step - 2);
      } else {
        setStep(step - 1);
      }
    } else {
      navigate(-1);
    }
  };

  const handleLoginClick = async () => {
    await keycloakInstance.login({ redirectUri: window.location.origin });
  };

  return (
    <div id="app" className="main-app">
      <div className="ui-right">
        <TopHeader />
        <div className="content-area">
          <div className="content">
            {/* <Container>
              <Row>
                <Col></Col>
                <Col md={auto}> */}
            <ol className="stepper" data-steps={5}>
              <li
                data-step-num="1"
                data-done={step > 1 ? "true" : "false"}
                data-current={step == 1 ? "true" : "false"}
              >
                <span>Profilo</span>
              </li>
              <li
                data-step-num="2"
                data-done={step > 2 ? "true" : "false"}
                data-current={step == 2 ? "true" : "false"}
              >
                <span>Dati Personali</span>
              </li>
              <li
                data-step-num="3"
                data-done={step > 3 ? "true" : "false"}
                data-current={step == 3 ? "true" : "false"}
              >
                <span>Dati Aziendali</span>
              </li>
              <li
                data-step-num="4"
                data-done={step > 4 ? "true" : "false"}
                data-current={step == 4 ? "true" : "false"}
              >
                <span>Consensi</span>
              </li>
              <li
                data-step-num="5"
                data-done={step > 5 ? "true" : "false"}
                data-current={step == 5 ? "true" : "false"}
              >
                <span>Esito</span>
              </li>
            </ol>
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
                  action="Iscriviti"
                  onBackClick={handleBackClick}
                  onNextClick={handleNextClick}
                />
              )}
              {step === 5 && (
                <Container>
                  <Row>
                    <Col></Col>
                    <Col md="auto" className="text-center">
                      <h1 className="mb-3">Registrazione</h1>
                      <div className="bg-white p-4 rounded">
                        <div className="spacer d-none d-md-block" style={{ width: "320px" }}></div>
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
