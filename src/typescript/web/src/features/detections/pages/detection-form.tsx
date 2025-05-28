import React, { Fragment } from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import { DetectionMutationPayload } from "@tornatura/coreapis";
import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import { detectionsActions } from "../state/detections-slice";

interface DetectionProps {
  formData: DetectionMutationPayload;
  action: string;
  onBackClick?: () => Promise<void>;
  onNextClick: (data: any) => Promise<void>;
}

function DetectionFormStep3({ formData, action, onBackClick, onNextClick }: DetectionProps) {
  const formik = useFormik({
    initialValues: {
      detectionTime: 0,
      note: "",
      insect: "",
    },
    onSubmit: (values, { setSubmitting, resetForm }) => {
      onNextClick(values);
      resetForm({});
      setSubmitting(false);
    },
  });

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <h4>Dati del rilevamento: Insetti</h4>
      <div className="input-row">
        <label>
          Nome dell'insetto
          <input
            id="insect"
            name="insect"
            type="text"
            placeholder="Nome insetto"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.insect}
          />
        </label>
        {formik.touched.insect && formik.errors.insect ? (
          <div className="error">{formik.errors.insect}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Noa aggiuntiva
          <textarea
            id="note"
            name="note"
            placeholder=""
            rows={15}
            cols={50}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.note}
          ></textarea>
        </label>
        {formik.touched.note && formik.errors.note ? (
          <div className="error">{formik.errors.note}</div>
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

function DetectionFormStep1({ formData, action, onBackClick, onNextClick }: DetectionProps) {
  const formik = useFormik({
    initialValues: {
      latitude: formData.position.lat || 0,
      longitude: formData.position.lng || 0,
    },
    validationSchema: Yup.object({
      latitude: Yup.number().required("posizione richiesta"),
      longitude: Yup.number().required("posizione richiesta"),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      onNextClick(values);
      resetForm({});
      setSubmitting(false);
    },
  });

  React.useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        formik.setValues({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      });
    }
  }, []);

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <h4>La tua posizione</h4>
      <div className="input-row">
        <label>
          Latitudine
          <input
            id="latitude"
            name="latitude"
            type="number"
            placeholder="Latitudine"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.latitude}
          />
        </label>
        {formik.touched.latitude && formik.errors.latitude ? (
          <div className="error">{formik.errors.latitude}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Longitudine
          <input
            id="longitude"
            name="longitude"
            type="number"
            placeholder="longitudine"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.longitude}
          />
        </label>
        {formik.touched.longitude && formik.errors.longitude ? (
          <div className="error">{formik.errors.longitude}</div>
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

function DetectionFormStep2({ action, onNextClick }: DetectionProps) {
  const formik = useFormik({
    initialValues: {
      type: "Malattia",
    },
    onSubmit: (values, { setSubmitting, resetForm }) => {
      onNextClick(values);
      resetForm({});
      setSubmitting(false);
    },
  });

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <h4>Cosa vuoi segnalare?</h4>
      <div className="input-row">
        <label>
          Tipologia
          <select
            id="type"
            name="type"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.type}
          >
            <option value="Malattie">Malattie</option>
            <option value="Insetti">Insetti</option>
            <option value="Parassiti">Parassiti</option>
            <option value="Altro">Altro</option>
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

export function DetectionForm() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { companyId, fieldId } = useParams();
  const [step, setStep] = React.useState(1);
  const [action, setAction] = React.useState("Avanti");
  const [formData, setFormData] = React.useState<DetectionMutationPayload>({
    detectionTime: new Date().getTime(),
    type: "",
    note: "",
    position: {
      lat: 0,
      lng: 0,
    },
    details: {},
    photos: [],
  });

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Nuovo Rilevamento", subtitle: "Subtitle" }));
  }, []);

  const createDetectionAction = async (payload: DetectionMutationPayload) => {
    if (companyId && fieldId) {
      dispatch(
        detectionsActions.addNewDetectionAction({
          orgId: companyId,
          fieldId: fieldId,
          body: payload,
        })
      )
        .then(unwrapResult)
        .then((_) => {
          navigate(`/companies/${companyId}/fields/${fieldId}`, { replace: true });
        })
        .catch((reason) => {
          console.error("Error creating detection with reason: ", reason);
        });
    }
  };

  const handleNextClick = async (data: any) => {
    if (step === 1) {
      const payload = {
        ...formData,
        type: data.type,
      };
      setFormData(payload);
      setAction("Avanti");
      setStep(step + 1);
    } else if (step === 2) {
      const payload = {
        ...formData,
        position: {
          lat: data.latitude,
          lng: data.longitude,
        },
      };
      setFormData(payload);
      setAction("Salva rilevamento");
      setStep(step + 1);
    } else if (step === 3) {
      const payload = {
        ...formData,
        details: {
          desease: data.desease,
          parasite: data.parasite,
          insect: data.insect,
        },
        note: data.note,
      };
      setFormData(payload);
      createDetectionAction(payload);
    }
  };

  const handleBackClick = async () => {
    if (step > 1) {
      setStep(step - 1);
      setAction("Avanti");
    }
  };

  return (
    <Fragment>
      <ol className="stepper" data-steps={3}>
        <li
          data-step-num="1"
          data-done={step > 1 ? "true" : "false"}
          data-current={step == 1 ? "true" : "false"}
        >
          <span>Posizione</span>
        </li>
        <li
          data-step-num="2"
          data-done={step > 2 ? "true" : "false"}
          data-current={step == 2 ? "true" : "false"}
        >
          <span>Categoria</span>
        </li>
        <li
          data-step-num="3"
          data-done={step > 3 ? "true" : "false"}
          data-current={step == 3 ? "true" : "false"}
        >
          <span>Dati</span>
        </li>
      </ol>
      <div className="form-wrapper">
        <div>
          {step === 1 && (
            <DetectionFormStep1 formData={formData} action={action} onNextClick={handleNextClick} />
          )}
          {step === 2 && (
            <DetectionFormStep2
              formData={formData}
              action={action}
              onBackClick={handleBackClick}
              onNextClick={handleNextClick}
            />
          )}
          {step === 3 && (
            <DetectionFormStep3
              formData={formData}
              action={action}
              onBackClick={handleBackClick}
              onNextClick={handleNextClick}
            />
          )}
        </div>
      </div>
    </Fragment>
  );
}
