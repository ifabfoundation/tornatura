import React from "react";
import { useFormik } from "formik";
import * as Yup from 'yup';
import { AccountTypeEnum, Configuration, UserCreatePayload, UsersApi } from "@tornatura/coreapis";
import { useNavigate } from "react-router-dom";

interface SignupProps {
  action: string;
  onBackClick?: () => Promise<void>;
  onNextClick: (data: any) => Promise<void>;
}

function SignupStep3({action, onBackClick, onNextClick}: SignupProps) {
  const formik = useFormik({
    initialValues: {
      name: '',
      description: '',
      email: '',
      phone: ''
    },
    validationSchema: Yup.object({
      name: Yup.string().required('nome richiesto'),
      description: Yup.string().required('descrizione richiesta'),
      email: Yup.string().email('Email non valida').required('Email richiesta'),
      phone: Yup.string().required('Telefono richiesto'),
    }),
    onSubmit: (values, {setSubmitting, resetForm}) => {
      onNextClick(values);
      resetForm({});
      setSubmitting(false);
    },
  });
  
  return (
    <form  onSubmit={formik.handleSubmit} autoComplete="off">
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
          <div className="error">{formik.errors.name}</div>) : null}
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
          <div className="error">{formik.errors.email}</div>) : null}
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
          <div className="error">{formik.errors.phone}</div>) : null}
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
          >
          </textarea>
        </label>
        {formik.touched.description && formik.errors.description ? (
          <div className="error">{formik.errors.description}</div>) : null}
      </div>
      <hr />
      <div className="buttons-wrapper">
        <button className="secondary" onClick={onBackClick}>Indietro</button>
        <input type="submit" className="primary" value={action} />
      </div>
    </form>
  );
}

function SignupStep2({action, onBackClick, onNextClick}: SignupProps) {
  const formik = useFormik({
    initialValues: {
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      privacy: false,
    },
    validationSchema: Yup.object({
      firstName: Yup.string().required('nome richiesto'),
      lastName: Yup.string().required('cognome richiesto'),
      email: Yup.string().email('Email non valida').required('Email richiesta'),
      phone: Yup.string().required('Telefono richiesto'),
      privacy: Yup.boolean().oneOf([true], 'Devi accettare la privacy policy'),
    }),
    onSubmit: (values, {setSubmitting, resetForm}) => {
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
          <div className="error">{formik.errors.firstName}</div>) : null}
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
          <div className="error">{formik.errors.lastName}</div>) : null}
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
          <div className="error">{formik.errors.email}</div>) : null}
      </div>
      <div className="input-row">
        <label>
          Phone
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
          <div className="error">{formik.errors.phone}</div>) : null}
      </div>
      <div className="input-row">
        <label>
          Consenso sulla privacy <a href="informativa_privacy.pdf">Informativa sulla privacy</a>
          <input
            id="privacy"
            name="privacy"
            type="checkbox"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            checked={formik.values.privacy}
          />
        </label>
        {formik.touched.privacy && formik.errors.privacy ? (
          <div className="error">{formik.errors.privacy}</div>) : null}
      </div>
      <hr />
      <div className="buttons-wrapper">
        <button className="secondary" onClick={onBackClick}>Indietro</button>
        <input type="submit" className="primary" value={action} />
      </div>
    </form>
  );
}

function SignupStep1({action, onNextClick}: SignupProps) {
  const formik = useFormik({
    initialValues: {
      accountType: 'Agronomist',
    },
    onSubmit: (values, {setSubmitting, resetForm}) => {
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
            <option  value='Agronomist'>Sono agronomo</option>
            <option  value='Standard'>Sono Imprenditore agricolo</option>
          </select>
        </label>
      </div>
      <hr />
      <div className="buttons-wrapper">
        <input type="submit" className="primary" value={action}/>
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
    "firstName": "",
    "lastName": "",
    "email": "",
    "accountType": AccountTypeEnum.Agronomist,
    "phone": ""
  });

  const createAccountAction = async (payload: UserCreatePayload) => {
    const apiConfig = new Configuration({basePath: `${COREAPIS_BASE_PATH}`})
    const usersApi = new UsersApi(apiConfig);
    const response = await usersApi.registerUser(payload);
    if (response.status === 201) {
      navigate("/welcome", { replace: true });
    } else {
      console.error("Error creating account", response);
    }
  }
  
  const handleNextClick = async (data: any) => {
    if (step === 1) {
      setFormData({
        ...data,
        accountType: data.accountType
      });
      if (data.accountType === AccountTypeEnum.Agronomist) {
        setAction("Crea");
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
        phone: data.phone
      }
      if (data.accountType === AccountTypeEnum.Standard) {
        setFormData(payload);
        setAction("Crea");
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
            phone: data.phone
          }
        }
      }
      createAccountAction(payload);
    }
  }

  const handleBackClick = async () => {
    if (step > 1) {
      setStep(step - 1);
    }
  }

  return (
    <div id="app" className="main-app">
      <div className="ui-right">
        <div className="content-area">
          <div className="content">
            <div style={{margin: "150px"}}>
              {step === 1 && <SignupStep1 action={action} onNextClick={handleNextClick} />}
              {step === 2 && <SignupStep2 action={action} onBackClick={handleBackClick} onNextClick={handleNextClick} />}
              {step === 3 && <SignupStep3 action={action} onBackClick={handleBackClick} onNextClick={handleNextClick} />}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}