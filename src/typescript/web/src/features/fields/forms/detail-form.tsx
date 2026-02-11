import React, { Fragment } from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import { AgriField, AgriFieldMutationPayload, Point } from "@tornatura/coreapis";
import { useNavigate } from "react-router-dom";
import { useAppDispatch } from "../../../hooks";
import { fieldsActions } from "../../fields/state/fields-slice";
import * as turf from "@turf/turf";
import { ModalConfirm } from "../../../components/ModalConfirm";

const calcArea = (points: Point[]) => {
  const coords: number[][] = [];
  points.forEach((p) => coords.push([p.lng, p.lat]));
  var polygon = turf.polygon([coords]);
  var areaSqm = turf.area(polygon);
  var areaHe = areaSqm / 10000; // Convert to hectares
  return parseFloat(areaHe.toFixed(2));
};

interface FieldDetailProps {
  field: AgriField;
}

export function FieldDetailForm({ field }: FieldDetailProps) {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const [modalOpen, setModalOpen] = React.useState(false);
  const [modal, setModal] = React.useState<any>({});

  const formik = useFormik({
    initialValues: {
      name: "",
      description: "",
      harvest: "",
      area: 0.0,
      areafrom: "map",
      plants: 0,
      variety: "",
      irrigation: "",
      weaving: "",
      rotation: "",
      grassing: "",
      year: "",
    },
    validationSchema: Yup.object({
      name: Yup.string().required("Campo necessario"),
      harvest: Yup.string().required("Campo necessario"),
      area: Yup.number()
        .typeError("Il valore inserito non è positivo")
        .min(0, "Il valore deve essere positivo")
        .required("Campo necessario"),
      variety: Yup.string().required("Campo necessario"),
      irrigation: Yup.string().required("Campo necessario"),
      weaving: Yup.string().required("Campo necessario"),
      rotation: Yup.string().required("Campo necessario"),
      grassing: Yup.string().required("Campo necessario"),
    }),
    onSubmit: (values, { setSubmitting, setErrors }) => {
      console.log("submit clicked!!!")
      if (values.areafrom === "map") {
        values.area = calcArea(field.map);
      }
      if (values.rotation === "no" && !values.year) {
        setErrors({ year: "Specificare l'anno di impianto" });
        setSubmitting(false);
        return;
      } else if (values.rotation === "si") {
        values.year = "";
      }
      const payload: AgriFieldMutationPayload = {
        name: values.name,
        description: values.description,
        harvest: values.harvest,
        area: values.area,
        map: field.map,
        plants: values.plants,
        variety: values.variety,
        irrigation: values.irrigation,
        weaving: values.weaving,
        rotation: values.rotation,
        grassing: values.grassing,
        year: values.year,
      };

      dispatch(
        fieldsActions.updateFieldAction({ orgId: field.orgId, fieldId: field.id, body: payload })
      );
      setSubmitting(false);
      navigate(`/companies/${field.orgId}/fields/${field.id}`);
    },
  });

  React.useEffect(() => {
    formik.setValues({
      name: field.name,
      description: field.description,
      harvest: field.harvest,
      area: field.area,
      areafrom: "map",
      plants: field.plants || 0,
      variety: field.variety,
      irrigation: field.irrigation,
      weaving: field.weaving,
      rotation: field.rotation,
      grassing: field.grassing,
      year: field.year || "",
    });
  }, [field]);

  const form_options_coltura = {
    vite: "Vite",
    pero: "Pero",
    pesco: "Pesco",
    mais: "Mais",
    barbabietola: "Barbabietola",
  };
  const form_options_rotazione = {
    si: "Sì",
    no: "No",
  };
  const form_options_dimensione = {
    map: "Calcolo automatico dalla mappa",
    manual: "Manuale",
  };
  const form_options_irrigazione = {
    scorrimento: "A scorrimento",
    pioggia: "A pioggia",
    goccia: "A goccia",
  };
  const form_options_inerbimento = {
    misto_spoglio: "Misto / Spoglio",
    brassicaceae: "Brassicaceae",
    graminaceae: "Graminaceae",
    fabaceae: "Fabaceae",
  };
  const form_options_tessitura = {
    misto: "Misto",
    argilla: "Argilla",
    sabbia: "Sabbia",
    limo: "Limo",
  };

  const handleFieldDelete = async () => {
    setModal({
      component: ModalConfirm,
      componentProps: {
        title: "Eliminazione campo",
        content:
          "Sei sicuro di voler eliminare questo campo? Questa azione non può essere annullata.",
        action: "Elimina",
        handleCancel: () => setModalOpen(false),
        handleConfirm: () => {
          dispatch(fieldsActions.deleteFieldAction({ orgId: field.orgId, fieldId: field.id }));
          setModalOpen(false);
          navigate(`/companies/${field.orgId}`, { replace: true });
        },
      },
    });
    setModalOpen(true);
  };

  return (
    <Fragment>
      <form onSubmit={formik.handleSubmit} autoComplete="off">
        <div className="form-section">
          <div className="container px-0">
            <div className="row">
              <div className="col mb-4">
                <h4>
                  <strong>Dettagli del Campo</strong>
                </h4>
              </div>
            </div>
            {modalOpen && <modal.component {...modal.componentProps} />}
            <div className="row input-row">
              <div className="col">
                <label>
                  Nome
                  <input
                    id="FIELD_1"
                    name="name"
                    type="text"
                    placeholder="Nome del campo"
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
              <div className="col-md-6 input-row-margin-fix">
                <label>
                  Coltura
                  <select
                    id="FIELD_2"
                    name="harvest"
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    value={formik.values.harvest}
                  >
                    <option value="" disabled>
                      Scegli la coltura
                    </option>
                    {Object.entries(form_options_coltura).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                {formik.touched.harvest && formik.errors.harvest ? (
                <div className="error">{formik.errors.harvest}</div>
              ) : null}
              </div>
              <div className="col-md-6 input-row-margin-fix">
                <label>
                  Varietà/Cultivar
                  <input
                    id="FIELD_3"
                    name="variety"
                    type="text"
                    placeholder="Indica la varietà o cultivar"
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    value={formik.values.variety}
                  />
                </label>
                {formik.touched.variety && formik.errors.variety ? (
                <div className="error">{formik.errors.variety}</div>
              ) : null}
              </div>
            </div>
            <div className="row input-row">
              <div className="col-md-6 input-row-margin-fix">
                <label>
                  Rotazione
                  <select
                    id="FIELD_4"
                    name="rotation"
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    value={formik.values.rotation}
                  >
                    <option value="" disabled>
                      Scegli...
                    </option>
                    {Object.entries(form_options_rotazione).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                {formik.touched.rotation && formik.errors.rotation ? (
                <div className="error">{formik.errors.rotation}</div>
              ) : null}
              </div>
              <div className="col-md-6 input-row-margin-fix">
                <label>
                  Anno di impianto
                  <input
                    id="FIELD_5"
                    name="year"
                    type="text"
                    // placeholder="[SOLO SE ROTAZIONE = NO]"
                    placeholder="Anno"
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    disabled={formik.values.rotation === "si"}
                    value={formik.values.rotation === "no" ? formik.values.year : ""}
                  />
                </label>
                {formik.touched.year && formik.errors.year ? (
                <div className="error">{formik.errors.year}</div>
              ) : null}
              </div>
            </div>
            <div className="row input-row">
              <div className="col-md-6 input-row-margin-fix">
                <label>
                  Dimensione del campo
                  <select
                    id="FIELD_6"
                    name="areafrom"
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    value={formik.values.areafrom}
                  >
                    <option value="" disabled>
                      Scegli il metodo di inserimento
                    </option>
                    {Object.entries(form_options_dimensione).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                {formik.touched.areafrom && formik.errors.areafrom ? (
                <div className="error">{formik.errors.areafrom}</div>
              ) : null}
              </div>
              <div className="col-md-6 input-row-margin-fix">
                <label>
                  Dimensione in ettari
                  <input
                    id="FIELD_7"
                    name="area"
                    type="text"
                    min={0}
                    // placeholder="[NON MODIFICABILE SE CALCOLO AUTOMATICO]"
                    placeholder="He"
                    disabled={formik.values.areafrom === "map"}
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    value={
                      formik.values.areafrom === "manual" ? formik.values.area : calcArea(field.map)
                    }
                  />
                </label>
                {formik.touched.area && formik.errors.area ? (
                <div className="error">{formik.errors.area}</div>
              ) : null}
              </div>
            </div>
            <div className="row input-row">
              <div className="col-md-6 input-row-margin-fix">
                <label>
                  Numero di piante
                  <input
                    id="FIELD_8"
                    name="plants"
                    type="text"
                    placeholder="Numero di piante"
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    value={formik.values.plants}
                  />
                </label>
                {formik.touched.plants && formik.errors.plants ? (
                  <div className="error">{formik.errors.plants}</div>
                ) : null}
              </div>
              <div className="col-md-6 input-row-margin-fix">
                <label>
                  Irrigazione
                  <select
                    id="FIELD_9"
                    name="irrigation"
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    value={formik.values.irrigation}
                  >
                    <option value="" disabled>
                      Scegli il tipo di irrigazione
                    </option>
                    {Object.entries(form_options_irrigazione).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                {formik.touched.irrigation && formik.errors.irrigation ? (
                <div className="error">{formik.errors.irrigation}</div>
              ) : null}
              </div>
            </div>
            <div className="row input-row">
              <div className="col-md-6 input-row-margin-fix">
                <label>
                  Inerbimento
                  <select
                    id="FIELD_10"
                    name="grassing"
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    value={formik.values.grassing}
                  >
                    <option value="" disabled>
                      Scegli il tipo di inerbimento
                    </option>
                    {Object.entries(form_options_inerbimento).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                {formik.touched.grassing && formik.errors.grassing ? (
                  <div className="error">{formik.errors.grassing}</div>
                ) : null}
              </div>
              <div className="col-md-6 input-row-margin-fix">
                <label>
                  Tessitura
                  <select
                    id="FIELD_11"
                    name="weaving"
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    value={formik.values.weaving}
                  >
                    <option value="" disabled>
                      Scegli la tessitura del suolo
                    </option>
                    {Object.entries(form_options_tessitura).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                {formik.touched.weaving && formik.errors.weaving ? (
                <div className="error">{formik.errors.weaving}</div>
              ) : null}
              </div>
            </div>
            <div className="row input-row">
              <div className="col">
                <label>
                  Descrizione
                  <textarea
                    id="FIELD_12"
                    name="description"
                    rows={15}
                    cols={50}
                    placeholder="Descrizione del campo"
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    value={formik.values.description}
                  />
                </label>
                {formik.touched.description && formik.errors.description ? (
                  <div className="error">{formik.errors.description}</div>
                ) : null}
              </div>
            </div>
            {/* <hr /> */}
          </div>
        </div>
        <div className="buttons-wrapper mt-4 text-center">
          <input type="submit" className="primary" value="Salva modifiche"/>
          <button className="trnt_btn info danger1" onClick={handleFieldDelete}>
            Elimina campo
          </button>
        </div>
      </form>
      <div className="spacer my-5"></div>
    </Fragment>
  );
}
