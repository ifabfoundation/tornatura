import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import { useFormik } from "formik";
import * as Yup from "yup";
import { AccountTypeEnum, Configuration, UserCreatePayload, UsersApi } from "@tornatura/coreapis";
import { useNavigate } from "react-router-dom";

interface SignupProps {
  action: string;
  onBackClick?: () => Promise<void>;
  onNextClick: (data: any) => Promise<void>;
}

function SignupStep3({ action, onBackClick, onNextClick }: SignupProps) {
  const formik = useFormik({
    initialValues: {
      name: "",
      description: "",
      email: "",
      phone: "",
    },
    validationSchema: Yup.object({
      name: Yup.string().required("Campo necessario"),
      description: Yup.string().required("Campo necessario"),
      email: Yup.string().email("Email non valida").required("Campo necessario"),
      phone: Yup.string().required("Campo necessario"),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      onNextClick(values);
      resetForm({});
      setSubmitting(false);
    },
  });

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="input-row">
        <label>
          Denominazione Aziendale
          <input
            id="name"
            name="name"
            type="text"
            placeholder="Agricolus s.r.l"
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
          Email di Contatto
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
      <div className="input-row">
        <label>
          Descrizione
          <textarea
            id="description"
            name="description"
            placeholder=""
            rows={15}
            cols={50}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.description}
          ></textarea>
        </label>
        {formik.touched.description && formik.errors.description ? (
          <div className="error">{formik.errors.description}</div>
        ) : null}
      </div>
      <hr />
      <div className="buttons-wrapper">
        <button className="secondary" onClick={onBackClick}>
          Indietro
        </button>
        <input type="submit" className="primary" value={action} />
      </div>
    </form>
  );
}

function SignupStep2({ action, onBackClick, onNextClick }: SignupProps) {
  const formik = useFormik({
    initialValues: {
      firstName: "",
      lastName: "",
      email: "",
      phone: "",
      privacy: false,
      privacy2: false,
    },
    validationSchema: Yup.object({
      firstName: Yup.string().required("Campo necessario"),
      lastName: Yup.string().required("Campo necessario"),
      email: Yup.string().email("Email non valida").required("Campo necessario"),
      phone: Yup.string().required("Campo necessario"),
      privacy: Yup.boolean().oneOf([true], "È necessaria l'accettazione"),
      privacy2: Yup.boolean().oneOf([true], "È necessaria l'accettazione"),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      onNextClick(values);
      resetForm({});
      setSubmitting(false);
    },
  });
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
        <button className="secondary" onClick={onBackClick}>
          Indietro
        </button>
        <input type="submit" className="primary" value={action} />
      </div>
    </form>
  );
}

function SignupStep1({ action, onNextClick }: SignupProps) {
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
        <input type="submit" className="primary" value={action} />
      </div>
    </form>
  );
}

const COREAPIS_BASE_PATH = process.env.REACT_APP_COREAPIS_SERVER_URL;

export function Signup() {
  const navigate = useNavigate();
  const [step, setStep] = React.useState(1);
  const [action, setAction] = React.useState("Avanti");
  const [formData, setFormData] = React.useState<UserCreatePayload>({
    firstName: "",
    lastName: "",
    email: "",
    accountType: AccountTypeEnum.Agronomist,
    phone: "",
  });

  const createAccountAction = async (payload: UserCreatePayload) => {
    const apiConfig = new Configuration({ basePath: `${COREAPIS_BASE_PATH}` });
    const usersApi = new UsersApi(apiConfig);
    const response = await usersApi.registerUser(payload);
    if (response.status === 201) {
      navigate("/welcome", { replace: true });
    } else {
      console.error("Error creating account", response);
    }
  };

  const handleNextClick = async (data: any) => {
    if (step === 1) {
      setFormData({
        ...data,
        accountType: data.accountType,
      });
      if (data.accountType === AccountTypeEnum.Agronomist) {
        setAction("Iscriviti");
      } else {
        setAction("Avanti");
      }
      setStep(step + 1);
    } else if (step === 2) {
      const payload = {
        ...formData,
        firstName: data.firstName,
        lastName: data.lastName,
        email: data.email,
        phone: data.phone,
      };
      if (data.accountType === AccountTypeEnum.Standard) {
        setFormData(payload);
        setAction("Iscriviti");
        setStep(step + 1);
      } else {
        createAccountAction(payload);
      }
    } else if (step === 3) {
      const payload = {
        ...formData,
        organization: {
          name: data.name,
          description: data.description,
          contacts: {
            email: data.email,
            phone: data.phone,
          },
        },
      };
      createAccountAction(payload);
    }
  };

  const handleBackClick = async () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  return (
    <div id="app" className="main-app">
      <div className="ui-right">
        <div className="content-area">
          <div className="content">
            {/* <Container>
              <Row>
                <Col></Col>
                <Col md={auto}> */}
            <div style={{ margin: "150px" }}>
              {step === 1 && <SignupStep1 action={action} onNextClick={handleNextClick} />}
              {step === 2 && (
                <SignupStep2
                  action={action}
                  onBackClick={handleBackClick}
                  onNextClick={handleNextClick}
                />
              )}
              {step === 3 && (
                <SignupStep3
                  action={action}
                  onBackClick={handleBackClick}
                  onNextClick={handleNextClick}
                />
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
