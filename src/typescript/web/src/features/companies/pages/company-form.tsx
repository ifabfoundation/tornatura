import { useFormik } from "formik";
import React from "react";
import * as Yup from "yup";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { useAppDispatch } from "../../../hooks";
import { OrganizationCreatePayload } from "@tornatura/coreapis";
import { companiesActions } from "../state/companies-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import { useNavigate } from "react-router-dom";

export function CompanyForm() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Nuova Azienda", subtitle: "Subtitle" }));
  }, []);

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
      piva: Yup.string().required("Campo obbligatorio"),
      state: Yup.string().required("Campo obbligatorio"),
      city: Yup.string().required("Campo obbligatorio"),
      legalForm: Yup.string().required("Campo obbligatorio"),
      rappresentative: Yup.string().required("Campo obbligatorio"),
      rappresentativeContact: Yup.string().required("Campo obbligatorio"),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      const organization: OrganizationCreatePayload = {
        name: values.name,
        piva: values.piva,
        legalForm: values.legalForm,
        office: {
          state: values.state,
          city: values.city
        },
        rapresentative: values.rappresentative,
        rapresentativeContact: values.rappresentativeContact,
        contacts: {
          email: values.email,
          phone: values.phone,
        },
      };
      dispatch(companiesActions.addNewCompanyAction(organization))
        .then(unwrapResult)
        .then((_) => {
          resetForm({});
          setSubmitting(false);
          navigate("/companies");
        })
        .catch((_) => {
          setSubmitting(false);
        });
    },
  });

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="input-row">
        <label>
          Ragione Sociale
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
          Regione Sede legale
          <input
            id="state"
            name="state"
            type="text"
            placeholder="Regione Sede legale"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.state}
          />
        </label>
        {formik.touched.state && formik.errors.state ? (
          <div className="error">{formik.errors.state}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Comune sede legale
          <input
            id="city"
            name="city"
            type="text"
            placeholder="Comune sede legale"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.city}
          />
        </label>
        {formik.touched.city && formik.errors.city ? (
          <div className="error">{formik.errors.city}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Forma giuridica
          <input
            id="legalForm"
            name="legalForm"
            type="text"
            placeholder="Forma giuridica"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.legalForm}
          />
        </label>
        {formik.touched.legalForm && formik.errors.legalForm ? (
          <div className="error">{formik.errors.legalForm}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Legale rappresentante
          <input
            id="rappresentative"
            name="rappresentative"
            type="text"
            placeholder="Rappresentante Legale"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.rappresentative}
          />
        </label>
        {formik.touched.rappresentative && formik.errors.rappresentative ? (
          <div className="error">{formik.errors.rappresentative}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Contatto Legale rappresentante
          <input
            id="rappresentativeContact"
            name="rappresentativeContact"
            type="text"
            placeholder="Contatto Rappresentante"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.rappresentativeContact}
          />
        </label>
        {formik.touched.rappresentativeContact && formik.errors.rappresentativeContact ? (
          <div className="error">{formik.errors.rappresentativeContact}</div>
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
      <hr />
      <div className="buttons-wrapper">
        <input type="submit" className="primary" value="Aggiungi" />
      </div>
    </form>
  );
}
