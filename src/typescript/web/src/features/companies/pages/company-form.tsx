import { useFormik } from "formik";
import React from "react";
import * as Yup from 'yup';
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
    dispatch(headerbarActions.setTitle({title: "Nuova Azienda", subtitle: "Subtitle"}));
  }, []); 

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
      const organization: OrganizationCreatePayload = {
        name: values.name,
        description: values.description,
        contacts: {
          email: values.email,
          phone: values.phone
        }
      }
      dispatch(companiesActions.addNewCompanyAction(organization))
      .then(unwrapResult)
      .then(_ => {
        resetForm({});
        setSubmitting(false);
        navigate("/companies");
      })
      .catch(_ => {
        setSubmitting(false);
      });
    },
  });
  
  return (
    <form  onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="input-row">
        <label>
          Denominazione
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
        <input type="submit" className="primary" value="Aggiungi" />
      </div>
    </form>
  );
}
