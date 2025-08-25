import { useFormik } from "formik";
import React from "react";
import * as Yup from "yup";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { useAppDispatch } from "../../../hooks";
import { OrganizationCreatePayload } from "@tornatura/coreapis";
import { companiesActions } from "../state/companies-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import { useNavigate } from "react-router-dom";
import { MenuItemEntry } from "../../../components/Sidebar";
import { SidebarActions } from "../../sidebar/state/sidebar-slice";

export function CompanyForm() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Nuova Azienda", subtitle: "Subtitle" }));
  }, []);

  React.useEffect(() => {
    let menuEntries: MenuItemEntry[] = [];
    let menuBottomEntries: MenuItemEntry[] = [];

    menuEntries = [
      {
        id: "companies",
        icon: "ifab_grid",
        text: "Aziende gestite",
        path: "/companies",
      },
    ];

    menuBottomEntries = [
      {
        id: "feedback",
        icon: "ifab_baloon",
        text: "Invia Feedback",
        path: "/new-feedback",
      },
    ];
    
    dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
    dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
    
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
      email: Yup.string().required("Campo obbligatorio"),
      phone: Yup.string().required("Campo obbligatorio"),
      // legalForm: Yup.string().required("Campo obbligatorio"),
      // rappresentative: Yup.string().required("Campo obbligatorio"),
      // rappresentativeContact: Yup.string().required("Campo obbligatorio"),
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
        <input type="submit" className="primary" value="Aggiungi" />
      </div>
    </form>
  );
}
