import React, { Fragment } from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import { DetectionMutationPayload, FilesApi } from "@tornatura/coreapis";
import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import { detectionsActions } from "../state/detections-slice";
import { FileWithPath, useDropzone } from "react-dropzone";
import { getCoreApiConfiguration } from "../../../services/utils";

interface DetectionProps {
  formData: DetectionMutationPayload;
  action: string;
  onBackClick?: () => Promise<void>;
  onNextClick: (data: any) => Promise<void>;
}

function DetectionFormMalattia({ action, onBackClick, onNextClick }: DetectionProps) {
  const [files, setFiles] = React.useState<FileWithPath[]>([]);

  const formik = useFormik({
    initialValues: {
      detectionTime: "",
      note: "",
      desease: "",
      infectedPlants: 0,
      uprootedPlants: 0,
    },
    validationSchema: Yup.object({
      detectionTime: Yup.string().required("Specifica la data del rilevamento"),
      desease: Yup.string().required("Specifica il nome della malattia"),
      infectedPlants: Yup.number()
        .min(0, "La percentuale di piante contagiate deve essere possitiva")
        .max(100),
      uprootedPlants: Yup.number().required("Specifica il numero di piante estirpate"),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      const data = {
        detectionTime: new Date(values.detectionTime).getTime(),
        note: values.note,
        details: {
          desease: values.desease,
          infectedPlants: values.infectedPlants,
          uprootedPlants: values.uprootedPlants,
        },
        files: files,
      };
      onNextClick(data);
      resetForm({});
      setSubmitting(false);
    },
  });

  const onDrop = React.useCallback((acceptedFiles: any) => {
    setFiles(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple: false });

  const filesPreview = files.map((file: FileWithPath) => (
    <li key={file.name}>
      <span className="mr-2">{file.name}</span>
    </li>
  ));

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <h4>Dati del rilevamento: Malattia</h4>
      <div className="input-row">
        <label>
          Data del rilevamento
          <input
            id="detectionTime"
            name="detectionTime"
            type="datetime-local"
            placeholder="Data rilevamento"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.detectionTime}
          />
        </label>
        {formik.touched.detectionTime && formik.errors.detectionTime ? (
          <div className="error">{formik.errors.detectionTime}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Nome della malattia
          <input
            id="desease"
            name="desease"
            type="text"
            placeholder="Nome malattia"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.desease}
          />
        </label>
        {formik.touched.desease && formik.errors.desease ? (
          <div className="error">{formik.errors.desease}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Percentuale Piante Contagiate
          <input
            id="infectedPlants"
            name="infectedPlants"
            type="text"
            placeholder="Percentuale Piante Contagiate"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.infectedPlants}
          />
        </label>
        {formik.touched.infectedPlants && formik.errors.infectedPlants ? (
          <div className="error">{formik.errors.infectedPlants}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Numero di Piante Estirpate
          <input
            id="uprootedPlants"
            name="uprootedPlants"
            type="text"
            placeholder="Nome Piante Estirpate"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.uprootedPlants}
          />
        </label>
        {formik.touched.uprootedPlants && formik.errors.uprootedPlants ? (
          <div className="error">{formik.errors.uprootedPlants}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Nota aggiuntiva
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
      <div className="input-row">
        <div {...getRootProps()}>
          <input {...getInputProps()} accept=".png, .jpeg, .jpg" />
          {isDragActive ? (
            <p>Trascina i file qui...</p>
          ) : (
            <p>Trascina e rilascia alcuni file qui, oppure fai clic per selezionarli</p>
          )}
        </div>
        --------------------------------------------------------------------------
        <div>
          <ul>{filesPreview}</ul>
        </div>
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

function DetectionFormParassita({ action, onBackClick, onNextClick }: DetectionProps) {
  const [files, setFiles] = React.useState<FileWithPath[]>([]);

  const formik = useFormik({
    initialValues: {
      detectionTime: "",
      note: "",
      parasite: "",
      infectedPlants: 0,
      uprootedPlants: 0,
    },
    validationSchema: Yup.object({
      detectionTime: Yup.string().required("Specifica la data del rilevamento"),
      parasite: Yup.string().required("Specifica il nome del parassita"),
      infectedPlants: Yup.number()
        .min(0, "La percentuale di piante contagiate deve essere possitiva")
        .max(100),
      uprootedPlants: Yup.number().required("Specifica il numero di piante estirpate"),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      const data = {
        detectionTime: new Date(values.detectionTime).getTime(),
        note: values.note,
        details: {
          parasite: values.parasite,
          infectedPlants: values.infectedPlants,
          uprootedPlants: values.uprootedPlants,
        },
        files: files,
      };
      onNextClick(data);
      resetForm({});
      setSubmitting(false);
    },
  });

  const onDrop = React.useCallback((acceptedFiles: any) => {
    setFiles(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple: false });

  const filesPreview = files.map((file: FileWithPath) => (
    <li key={file.name}>
      <span className="mr-2">{file.name}</span>
    </li>
  ));

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <h4>Dati del rilevamento: Parassita</h4>
      <div className="input-row">
        <label>
          Data del rilevamento
          <input
            id="detectionTime"
            name="detectionTime"
            type="datetime-local"
            placeholder="Data rilevamento"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.detectionTime}
          />
        </label>
        {formik.touched.detectionTime && formik.errors.detectionTime ? (
          <div className="error">{formik.errors.detectionTime}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Nome del parassita
          <input
            id="parasite"
            name="parasite"
            type="text"
            placeholder="Nome malattia"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.parasite}
          />
        </label>
        {formik.touched.parasite && formik.errors.parasite ? (
          <div className="error">{formik.errors.parasite}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Percentuale Piante Contagiate
          <input
            id="infectedPlants"
            name="infectedPlants"
            type="text"
            placeholder="Percentuale Piante Contagiate"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.infectedPlants}
          />
        </label>
        {formik.touched.infectedPlants && formik.errors.infectedPlants ? (
          <div className="error">{formik.errors.infectedPlants}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Numero di Piante Estirpate
          <input
            id="uprootedPlants"
            name="uprootedPlants"
            type="text"
            placeholder="Nome Piante Estirpate"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.uprootedPlants}
          />
        </label>
        {formik.touched.uprootedPlants && formik.errors.uprootedPlants ? (
          <div className="error">{formik.errors.uprootedPlants}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Nota aggiuntiva
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
      <div className="input-row">
        <div {...getRootProps()}>
          <input {...getInputProps()} accept=".png, .jpeg, .jpg" />
          {isDragActive ? (
            <p>Trascina i file qui...</p>
          ) : (
            <p>Trascina e rilascia alcuni file qui, oppure fai clic per selezionarli</p>
          )}
        </div>
        --------------------------------------------------------------------------
        <div>
          <ul>{filesPreview}</ul>
        </div>
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

function DetectionFormInsetto({ action, onBackClick, onNextClick }: DetectionProps) {
  const [files, setFiles] = React.useState<FileWithPath[]>([]);

  const formik = useFormik({
    initialValues: {
      detectionTime: "",
      note: "",
      insect: "",
      trapsNumber: 0,
    },
    validationSchema: Yup.object({
      detectionTime: Yup.string().required("Specifica la data del rilevamento"),
      insect: Yup.string().required("Specifica il nome dell'insetto"),
      trapsNumber: Yup.number(),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      const data = {
        detectionTime: new Date(values.detectionTime).getTime(),
        note: values.note,
        details: {
          insect: values.insect,
          trapsNumber: values.trapsNumber,
        },
        files: files,
      };
      onNextClick(data);
      resetForm({});
      setSubmitting(false);
    },
  });

  const onDrop = React.useCallback((acceptedFiles: any) => {
    setFiles(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple: false });

  const filesPreview = files.map((file: FileWithPath) => (
    <li key={file.name}>
      <span className="mr-2">{file.name}</span>
    </li>
  ));

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <h4>Dati del rilevamento: Insetti</h4>
      <div className="input-row">
        <label>
          Data del rilevamento
          <input
            id="detectionTime"
            name="detectionTime"
            type="datetime-local"
            placeholder="Data rilevamento"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.detectionTime}
          />
        </label>
        {formik.touched.detectionTime && formik.errors.detectionTime ? (
          <div className="error">{formik.errors.detectionTime}</div>
        ) : null}
      </div>
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
          Numero di trappole
          <input
            id="trapsNumber"
            name="trapsNumber"
            type="text"
            placeholder="Numero di trappole"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.trapsNumber}
          />
        </label>
        {formik.touched.trapsNumber && formik.errors.trapsNumber ? (
          <div className="error">{formik.errors.trapsNumber}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Nota aggiuntiva
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
      <div className="input-row">
        <div {...getRootProps()}>
          <input {...getInputProps()} accept=".png, .jpeg, .jpg" />
          {isDragActive ? (
            <p>Trascina i file qui...</p>
          ) : (
            <p>Trascina e rilascia alcuni file qui, oppure fai clic per selezionarli</p>
          )}
        </div>
        --------------------------------------------------------------------------
        <div>
          <ul>{filesPreview}</ul>
        </div>
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

function DetectionFormAltro({ action, onBackClick, onNextClick }: DetectionProps) {
  const [files, setFiles] = React.useState<FileWithPath[]>([]);

  const formik = useFormik({
    initialValues: {
      detectionTime: "",
      note: "",
    },
    validationSchema: Yup.object({
      detectionTime: Yup.string().required("Specifica la data del rilevamento"),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      const data = {
        detectionTime: new Date(values.detectionTime).getTime(),
        note: values.note,
        details: {},
        files: files,
      };
      onNextClick(data);
      resetForm({});
      setSubmitting(false);
    },
  });

  const onDrop = React.useCallback((acceptedFiles: any) => {
    setFiles(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple: false });
  const filesPreview = files.map((file: FileWithPath) => (
    <li key={file.name}>
      <span className="mr-2">{file.name}</span>
    </li>
  ));

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <h4>Dati del rilevamento: Insetti</h4>
      <div className="input-row">
        <label>
          Data del rilevamento
          <input
            id="detectionTime"
            name="detectionTime"
            type="datetime-local"
            placeholder="Data rilevamento"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.detectionTime}
          />
        </label>
        {formik.touched.detectionTime && formik.errors.detectionTime ? (
          <div className="error">{formik.errors.detectionTime}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Nota
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
      <div className="input-row">
        <div {...getRootProps()}>
          <input {...getInputProps()} accept=".png, .jpeg, .jpg" />
          {isDragActive ? (
            <p>Trascina i file qui...</p>
          ) : (
            <p>Trascina e rilascia alcuni file qui, oppure fai clic per selezionarli</p>
          )}
        </div>
        --------------------------------------------------------------------------
        <div>
          <ul>{filesPreview}</ul>
        </div>
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

function DetectionFormStep1({ formData, action, onNextClick }: DetectionProps) {
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
    formik.setValues({
      latitude: formData.position.lat || 0,
      longitude: formData.position.lng || 0,
    });
  }, [formData]);

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
        <input type="submit" className="primary" value={action} />
      </div>
    </form>
  );
}

function DetectionFormStep2({ formData, action, onBackClick, onNextClick }: DetectionProps) {
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

  React.useEffect(() => {
    formik.setValues({
      type: formData.type || "Malattia",
    });
  }, [formData]);

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
            <option value="Malattia">Malattia</option>
            <option value="Insetto">Insetto</option>
            <option value="Parassita">Parassita</option>
            <option value="Altro">Altro</option>
          </select>
        </label>
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

  const handleNextClick = async (data: any) => {
    if (step === 2) {
      const payload = {
        ...formData,
        type: data.type,
      };
      setFormData(payload);
      setAction("Salva rilevamento");
      setStep(step + 1);
    } else if (step === 1) {
      const payload = {
        ...formData,
        position: {
          lat: data.latitude,
          lng: data.longitude,
        },
      };
      setFormData(payload);
      setAction("Avanti");
      setStep(step + 1);
    } else if (step === 3) {
      const payload = {
        ...formData,
        detectionTime: data.detectionTime,
        details: data.details || {},
        photos: await uploadFiles(data.files || []),
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
        {step === 3 && formData.type === "Malattia" && (
          <DetectionFormMalattia
            formData={formData}
            action={action}
            onBackClick={handleBackClick}
            onNextClick={handleNextClick}
          />
        )}
        {step === 3 && formData.type === "Parassita" && (
          <DetectionFormParassita
            formData={formData}
            action={action}
            onBackClick={handleBackClick}
            onNextClick={handleNextClick}
          />
        )}
        {step === 3 && formData.type === "Insetto" && (
          <DetectionFormInsetto
            formData={formData}
            action={action}
            onBackClick={handleBackClick}
            onNextClick={handleNextClick}
          />
        )}
        {step === 3 && formData.type === "Altro" && (
          <DetectionFormAltro
            formData={formData}
            action={action}
            onBackClick={handleBackClick}
            onNextClick={handleNextClick}
          />
        )}
      </div>
    </Fragment>
  );
}
