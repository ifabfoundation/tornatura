import { useFormik } from "formik";
import React, { Fragment } from "react";
import * as Yup from "yup";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { unwrapResult } from "@reduxjs/toolkit";
import { Col, Container, Row, Image, Alert } from "react-bootstrap";
import { FileWithPath, useDropzone } from "react-dropzone";
import { getCoreApiConfiguration } from "../../../services/utils";
import { userActions, userSelectors } from "../state/user-slice";
import { AccountTypeEnum, UsersApi, UserUpdatePayload } from "@tornatura/coreapis";

const PhoneRegExp = /^\+?[0-9]{1,4}[\s\-]?[0-9]{6,14}$/;

export function UserProfile() {
  const dispatch = useAppDispatch();
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);
  const [files, setFiles] = React.useState<FileWithPath[]>([]);
  const [message, setMessage] = React.useState<string>();
  const [hasError, setHasError] = React.useState<boolean>(false);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Profilo Utente", subtitle: "Subtitle" }));
  }, []);

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
      phone: Yup.string()
        .matches(PhoneRegExp, "Telefono non valido")
        .required("Campo obbligatorio"),
    }),
    onSubmit: (values, { setSubmitting }) => {
      const payload: UserUpdatePayload = {
        lastName: values.lastName,
        phone: values.phone,
        firstName: values.firstName,
      };
      dispatch(userActions.updateUserAction(payload))
        .then(unwrapResult)
        .then((_) => {
          setMessage("Profilo aggiornato con successo");
          setHasError(false);
          setSubmitting(false);
        })
        .catch((error) => {
          console.error(error);
          setMessage("Errore durante l'aggiornamento del profilo");
          setHasError(true);
          setSubmitting(false);
        });
    },
  });

  React.useEffect(() => {
    formik.setValues({
      firstName: currentUser.firstName || "",
      lastName: currentUser.lastName || "",
      email: currentUser.email || "",
      piva: currentUser.piva || "",
      phone: currentUser.phone || "",
    });
  }, [currentUser]);

  const onDrop = React.useCallback((acceptedFiles: any) => {
    setFiles(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple: false });
  const filesPreview = files.length > 0 ? URL.createObjectURL(files[0]) : currentUser?.avatar;

  const handleAvatarUpdate = async () => {
    if (files.length === 0) {
      setMessage("Nessun file selezionato");
      setHasError(true);
      return;
    }

    try {
      const apiConfig = await getCoreApiConfiguration();
      const userApi = new UsersApi(apiConfig);
      console.log(userApi);

      await userApi.userAvatarUploadForm(files[0]);
      const user = await userApi.userInfo();
      dispatch(userActions.setCurrentUserAction(user.data));
      setMessage("Avatar aggiornato con successo");
      setHasError(false);
      setFiles([]);
    } catch (error) {
      console.error(error);
      setMessage("Errore durante l'aggiornamento dell'avatar");
      setHasError(true);
    }
  };

  return (
    <Fragment>
      {message && (
        <Alert variant={hasError ? "danger" : "success"} dismissible>
          {message}
        </Alert>
      )}

      <div className="form-section">
        <Container className="px-0">
          <Row>
            <Col>
              <h4 className="mb-4">
                <strong>Avatar</strong>
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
                  onClick={handleAvatarUpdate}
                >
                  Aggiorna
                </button>
              </div>
            </Col>
          </Row>
        </Container>
      </div>

      <div className="my-5"></div>

      <form onSubmit={formik.handleSubmit} autoComplete="off">
        <div className="form-section">
          <Container className="px-0">
            <Row>
              <Col className="mb-4">
                <h4>
                  <strong>Profilo</strong>
                </h4>
              </Col>
            </Row>
            <Row>
              <Col>
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
                      disabled={true}
                    />
                  </label>
                  {formik.touched.email && formik.errors.email ? (
                    <div className="error">{formik.errors.email}</div>
                  ) : null}
                </div>
                {currentUser.accountType === AccountTypeEnum.Agronomist && (
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
                <div className="buttons-wrapper mt-4">
                  <input type="submit" className="primary m-0" value="Modifica Profilo" />
                </div>
              </Col>
            </Row>
          </Container>
        </div>
      </form>

      <div className="my-5"></div>
    </Fragment>
  );
}
