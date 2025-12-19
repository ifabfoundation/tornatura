import { useFormik } from "formik";
import React, { Fragment } from "react";
import * as Yup from "yup";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { FilesApi, OrganizationUpdatePayload } from "@tornatura/coreapis";
import { companiesActions, companiesSelectors } from "../state/companies-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import { useParams } from "react-router-dom";
import { Col, Container, Row, Image, Alert } from "react-bootstrap";
import { FileWithPath, useDropzone } from "react-dropzone";
import { getCoreApiConfiguration } from "../../../services/utils";

const PhoneRegExp = /^\+?[0-9]{1,4}[\s\-]?[0-9]{6,14}$/;

export function CompanySettings() {
  const dispatch = useAppDispatch();
  const { companyId } = useParams();
  const currentCompany = useAppSelector((state) =>
    companiesSelectors.selectCompanybyId(state, companyId ?? "default")
  );
  const [files, setFiles] = React.useState<FileWithPath[]>([]);
  const [message, setMessage] = React.useState<string>();
  const [hasError, setHasError] = React.useState<boolean>(false);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Impostazioni Azienda", subtitle: "Subtitle" }));
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
      email: Yup.string().email("Email non valida").required("Campo obbligatorio"),
      phone: Yup.string()
        .matches(PhoneRegExp, "Telefono non valido")
        .required("Campo obbligatorio"),
    }),
    onSubmit: (values, { setSubmitting }) => {
      const organization: OrganizationUpdatePayload = {
        contacts: {
          email: values.email,
          phone: values.phone,
        },
      };
      dispatch(
        companiesActions.updateCompanyAction({ orgId: companyId ?? "default", body: organization })
      )
        .then(unwrapResult)
        .then((_) => {
          setMessage("Anagrafica aggiornata con successo");
          setHasError(false);
          setSubmitting(false);
        })
        .catch((_) => {
          setMessage("Errore durante l'aggiornamento dell'anagrafica");
          setHasError(true);
          setSubmitting(false);
        });
    },
  });

  React.useEffect(() => {
    if (currentCompany) {
      formik.setValues({
        name: currentCompany.name ?? "",
        piva: currentCompany.piva ?? "",
        state: currentCompany.office?.state ?? "",
        city: currentCompany.office?.city ?? "",
        legalForm: currentCompany.legalForm ?? "",
        rappresentative: currentCompany.rapresentative ?? "",
        rappresentativeContact: currentCompany.rapresentativeContact ?? "",
        email: currentCompany.contacts?.email ?? "",
        phone: currentCompany.contacts?.phone ?? "",
      });
    }
  }, [currentCompany]);

  const onDrop = React.useCallback((acceptedFiles: any) => {
    setFiles(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple: false });
  const filesPreview = files.length > 0 ? URL.createObjectURL(files[0]) : currentCompany?.logo;

  const uploadFiles = async (files: FileWithPath[]) => {
    const apiConfig = await getCoreApiConfiguration();
    const filesApi = new FilesApi(apiConfig);

    if (files.length === 0 || companyId === undefined) {
      return [];
    }

    try {
      const results = await filesApi.uploadFilesForm(files, companyId, "data").then((response) => {
        return response.data;
      });
      return results;
    } catch (error) {
      console.error("Error uploading files:", error);
      return [];
    }
  };

  const handleLogoUpdate = async () => {
    if (files.length === 0) {
      setMessage("Nessun file selezionato");
      setHasError(true);
      return;
    }

    try {
      const uploadedFiles = await uploadFiles(files);
      if (uploadedFiles.length > 0) {
        setMessage("Logo aziendale aggiornato con successo");
        setHasError(false);
        setFiles([]);
        // Refresh company data to get the new logo URL
        if (companyId) {
          dispatch(companiesActions.getCompanyAction(companyId));
        }
      } else {
        setMessage("Errore durante l'upload del logo aziendale");
        setHasError(true);
      }
    } catch (error) {
      setMessage("Errore durante l'upload del logo aziendale");
      setHasError(true);
    }
  };

  return (
    <Fragment>
      <div className="form-section">
        <Container className="px-0">
          {message && (
            <Alert variant={hasError ? "danger" : "success"} dismissible>
              {message}
            </Alert>
          )}
          <Row>
            <Col>
              <h4 className="mb-4">
                <strong>Anagrafica</strong>
              </h4>
            </Col>
          </Row>
          <Row>
            <Col>
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
                      disabled={true}
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
                      disabled={true}
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
                <div className="buttons-wrapper mt-4">
                  <input type="submit" className="primary m-0" value="Salva Modifiche" />
                </div>
              </form>
            </Col>
          </Row>
        </Container>
      </div>

      <div className="my-5"></div>

      <div className="form-section">
        <Container className="px-0">
          <Row>
            <Col className="mb-4">
              <h4 className="mb-4">
                <strong>Logo dell'azienda</strong>
              </h4>
              <div className="input-row">
                <Image src={filesPreview} roundedCircle width="80px" height="80px" />
                <div className="mt-3" {...getRootProps()}>
                  <input {...getInputProps()} accept=".png, .jpeg, .jpg" />
                  {isDragActive ? (
                    <p>Trascina i file qui...</p>
                  ) : (
                    <p>Trascina e rilascia alcuni file qui, oppure fai clic per selezionarli</p>
                  )}
                </div>
              </div>

              <div className="buttons-wrapper mt-4">
                <button
                  className="trnt_btn primary m-0"
                  value="Aggiorna"
                  onClick={handleLogoUpdate}
                >
                  Aggiorna
                </button>
              </div>
            </Col>
          </Row>
        </Container>
      </div>

      <div className="my-5"></div>
    </Fragment>
  );
}
