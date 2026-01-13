import React, { Fragment, useEffect, useState } from "react";
import { Col, Container, Row } from "react-bootstrap";
// import { useFormik } from "formik";
// import * as Yup from "yup";
import { DetectionMutationPayload, ObservationType, DetectionText } from "@tornatura/coreapis";
import { useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import { detectionsActions } from "../state/detections-slice";
import { fieldsSelectors } from "../../fields/state/fields-slice";
// import { SearchBox } from "@mapbox/search-js-react";
import mapboxgl, { LngLatLike, Marker } from "mapbox-gl";
import { Point } from "@tornatura/coreapis";
import * as turf from "@turf/turf";
import { ModalConfirm } from "../../../components/ModalConfirm";
import { Accordion, AccordionItem } from "../../../components/Accordion";
import CozyButton from "../../../components/CozyButton";
import Icon from "../../../components/Icon";
// import { timeStamp } from "console";
import { detectionTypesActions, detectionTypesSelectors } from "../../detection-types/state/detection-types-slice";
import { observationTypesActions, observationTypesSelectors } from "../../observation-types/state/observation-types-slice";
import { detectionTextsActions, detectionTextsSelectors } from "../../detection-texts/state/detection-texts-slice";
import { gpsStore } from "../../../providers/gps-providers";

const markerOptions = { color: "#EAFF00" };

interface DetectionProps {
  formData: DetectionMutationPayload;
  action?: string;
  onBackClick?: () => Promise<void>;
  onNextClick: (data: any) => Promise<void>;
}

function CameraCapture({
  open,
  onClose,
  onCapture,
}: {
  open: boolean;
  onClose: () => void;
  onCapture: (file: File) => void;
}) {
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const streamRef = React.useRef<MediaStream | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!open) {
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Camera non disponibile.");
      return;
    }
    let active = true;
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false })
      .then((stream) => {
        if (!active) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => null);
        }
      })
      .catch(() => {
        setError("Impossibile accedere alla camera.");
      });

    return () => {
      active = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, [open]);

  const handleCapture = () => {
    const video = videoRef.current;
    if (!video) {
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return;
    }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          return;
        }
        const file = new File([blob], `photo-${Date.now()}.jpg`, { type: "image/jpeg" });
        onCapture(file);
        onClose();
      },
      "image/jpeg",
      0.9
    );
  };

  if (!open) {
    return null;
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0, 0, 0, 0.75)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 2000,
      }}
    >
      <div
        style={{
          width: "min(92vw, 560px)",
          background: "#fff",
          borderRadius: "12px",
          padding: "12px",
        }}
      >
        {error ? (
          <div className="text-center">
            <p className="mb-3">{error}</p>
            <button className="trnt_btn primary" onClick={onClose}>
              Chiudi
            </button>
          </div>
        ) : (
          <Fragment>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              style={{ width: "100%", borderRadius: "8px" }}
            />
            <div className="buttons-wrapper mt-3 text-center">
              <button className="trnt_btn secondary" onClick={onClose}>
                Annulla
              </button>
              <button className="trnt_btn primary ms-2" onClick={handleCapture}>
                Scatta
              </button>
            </div>
          </Fragment>
        )}
      </div>
    </div>
  );
}

function isPointInsideField(pointLon: number, pointLat: number, areaPoints: number[][]) {
  if (areaPoints.length > 2) {
    const polygon = turf.polygon([areaPoints]);
    const point = turf.point([pointLon, pointLat]);
    const isContained = turf.booleanContains(polygon, point);
    return isContained;
  }
  return false;
}

// function DetectionFormMalattia({ action, onBackClick, onNextClick }: DetectionProps) {
//   const [files, setFiles] = React.useState<FileWithPath[]>([]);

//   const formik = useFormik({
//     initialValues: {
//       detectionTime: "",
//       note: "",
//       desease: "",
//       infectedPlants: 0,
//       uprootedPlants: 0,
//     },
//     validationSchema: Yup.object({
//       detectionTime: Yup.string().required("Specifica la data del rilevamento"),
//       desease: Yup.string().required("Specifica il nome della malattia"),
//       infectedPlants: Yup.number()
//         .min(0, "La percentuale di piante contagiate deve essere possitiva")
//         .max(100),
//       uprootedPlants: Yup.number().required("Specifica il numero di piante estirpate"),
//     }),
//     onSubmit: (values, { setSubmitting, resetForm }) => {
//       const data = {
//         detectionTime: new Date(values.detectionTime).getTime(),
//         note: values.note,
//         details: {
//           desease: values.desease,
//           infectedPlants: values.infectedPlants,
//           uprootedPlants: values.uprootedPlants,
//         },
//         files: files,
//       };
//       onNextClick(data);
//       resetForm({});
//       setSubmitting(false);
//     },
//   });

//   const onDrop = React.useCallback((acceptedFiles: any) => {
//     setFiles(acceptedFiles);
//   }, []);

//   const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple: false });

//   const filesPreview = files.map((file: FileWithPath) => (
//     <li key={file.name}>
//       <span className="mr-2">{file.name}</span>
//     </li>
//   ));

//   return (
//     <form onSubmit={formik.handleSubmit} autoComplete="off">
//       <h4 className="mt-4 mb-4">Dati del rilevamento: Malattia</h4>
//       <div className="input-row">
//         <label>
//           Data del rilevamento
//           <input
//             id="detectionTime"
//             name="detectionTime"
//             type="datetime-local"
//             placeholder="Data rilevamento"
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.detectionTime}
//           />
//         </label>
//         {formik.touched.detectionTime && formik.errors.detectionTime ? (
//           <div className="error">{formik.errors.detectionTime}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <label>
//           Nome della malattia
//           <input
//             id="desease"
//             name="desease"
//             type="text"
//             placeholder="Nome malattia"
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.desease}
//           />
//         </label>
//         {formik.touched.desease && formik.errors.desease ? (
//           <div className="error">{formik.errors.desease}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <label>
//           Percentuale Piante Contagiate
//           <input
//             id="infectedPlants"
//             name="infectedPlants"
//             type="text"
//             placeholder="Percentuale Piante Contagiate"
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.infectedPlants}
//           />
//         </label>
//         {formik.touched.infectedPlants && formik.errors.infectedPlants ? (
//           <div className="error">{formik.errors.infectedPlants}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <label>
//           Numero di Piante Estirpate
//           <input
//             id="uprootedPlants"
//             name="uprootedPlants"
//             type="text"
//             placeholder="Nome Piante Estirpate"
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.uprootedPlants}
//           />
//         </label>
//         {formik.touched.uprootedPlants && formik.errors.uprootedPlants ? (
//           <div className="error">{formik.errors.uprootedPlants}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <label>
//           Nota aggiuntiva
//           <textarea
//             id="note"
//             name="note"
//             placeholder=""
//             rows={15}
//             cols={50}
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.note}
//           ></textarea>
//         </label>
//         {formik.touched.note && formik.errors.note ? (
//           <div className="error">{formik.errors.note}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <div
//           {...getRootProps()}
//           style={{ backgroundColor: "white", height: "60px", textAlign: "center", margin: "auto" }}
//         >
//           <input {...getInputProps()} accept=".png, .jpeg, .jpg" />
//           {isDragActive ? (
//             <p className="mt-4">Trascina i file qui...</p>
//           ) : (
//             <p className="mt-4">
//               Trascina e rilascia alcuni file qui, oppure fai clic per selezionarli
//             </p>
//           )}
//         </div>
//         --------------------------------------------------------------------------
//         <div>
//           <ul>{filesPreview}</ul>
//         </div>
//       </div>
//       <hr />
//       <div className="buttons-wrapper">
//         <button className="trnt_btn secondary" onClick={onBackClick}>
//           Indietro
//         </button>
//         <input type="submit" className="primary" value={action} />
//       </div>
//     </form>
//   );
// }

// function DetectionFormParassita({ action, onBackClick, onNextClick }: DetectionProps) {
//   const [files, setFiles] = React.useState<FileWithPath[]>([]);

//   const formik = useFormik({
//     initialValues: {
//       detectionTime: "",
//       note: "",
//       parasite: "",
//       infectedPlants: 0,
//       uprootedPlants: 0,
//     },
//     validationSchema: Yup.object({
//       detectionTime: Yup.string().required("Specifica la data del rilevamento"),
//       parasite: Yup.string().required("Specifica il nome del parassita"),
//       infectedPlants: Yup.number()
//         .min(0, "La percentuale di piante contagiate deve essere possitiva")
//         .max(100),
//       uprootedPlants: Yup.number().required("Specifica il numero di piante estirpate"),
//     }),
//     onSubmit: (values, { setSubmitting, resetForm }) => {
//       const data = {
//         detectionTime: new Date(values.detectionTime).getTime(),
//         note: values.note,
//         details: {
//           parasite: values.parasite,
//           infectedPlants: values.infectedPlants,
//           uprootedPlants: values.uprootedPlants,
//         },
//         files: files,
//       };
//       onNextClick(data);
//       resetForm({});
//       setSubmitting(false);
//     },
//   });

//   const onDrop = React.useCallback((acceptedFiles: any) => {
//     setFiles(acceptedFiles);
//   }, []);

//   const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple: false });

//   const filesPreview = files.map((file: FileWithPath) => (
//     <li key={file.name}>
//       <span className="mr-2">{file.name}</span>
//     </li>
//   ));

//   return (
//     <form onSubmit={formik.handleSubmit} autoComplete="off">
//       <h4 className="mt-4 mb-4">Dati del rilevamento: Parassita</h4>
//       <div className="input-row">
//         <label>
//           Data del rilevamento
//           <input
//             id="detectionTime"
//             name="detectionTime"
//             type="datetime-local"
//             placeholder="Data rilevamento"
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.detectionTime}
//           />
//         </label>
//         {formik.touched.detectionTime && formik.errors.detectionTime ? (
//           <div className="error">{formik.errors.detectionTime}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <label>
//           Nome del parassita
//           <input
//             id="parasite"
//             name="parasite"
//             type="text"
//             placeholder="Nome malattia"
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.parasite}
//           />
//         </label>
//         {formik.touched.parasite && formik.errors.parasite ? (
//           <div className="error">{formik.errors.parasite}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <label>
//           Percentuale Piante Contagiate
//           <input
//             id="infectedPlants"
//             name="infectedPlants"
//             type="text"
//             placeholder="Percentuale Piante Contagiate"
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.infectedPlants}
//           />
//         </label>
//         {formik.touched.infectedPlants && formik.errors.infectedPlants ? (
//           <div className="error">{formik.errors.infectedPlants}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <label>
//           Numero di Piante Estirpate
//           <input
//             id="uprootedPlants"
//             name="uprootedPlants"
//             type="text"
//             placeholder="Nome Piante Estirpate"
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.uprootedPlants}
//           />
//         </label>
//         {formik.touched.uprootedPlants && formik.errors.uprootedPlants ? (
//           <div className="error">{formik.errors.uprootedPlants}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <label>
//           Nota aggiuntiva
//           <textarea
//             id="note"
//             name="note"
//             placeholder=""
//             rows={15}
//             cols={50}
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.note}
//           ></textarea>
//         </label>
//         {formik.touched.note && formik.errors.note ? (
//           <div className="error">{formik.errors.note}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <div {...getRootProps()}>
//           <input {...getInputProps()} accept=".png, .jpeg, .jpg" />
//           {isDragActive ? (
//             <p>Trascina i file qui...</p>
//           ) : (
//             <p>Trascina e rilascia alcuni file qui, oppure fai clic per selezionarli</p>
//           )}
//         </div>
//         --------------------------------------------------------------------------
//         <div>
//           <ul>{filesPreview}</ul>
//         </div>
//       </div>
//       <hr />
//       <div className="buttons-wrapper">
//         <button className="trnt_btn secondary" onClick={onBackClick}>
//           Indietro
//         </button>
//         <input type="submit" className="primary" value={action} />
//       </div>
//     </form>
//   );
// }

// function DetectionFormInsetto({ action, onBackClick, onNextClick }: DetectionProps) {
//   const [files, setFiles] = React.useState<FileWithPath[]>([]);

//   const formik = useFormik({
//     initialValues: {
//       detectionTime: "",
//       note: "",
//       insect: "",
//       trapsNumber: 0,
//     },
//     validationSchema: Yup.object({
//       detectionTime: Yup.string().required("Specifica la data del rilevamento"),
//       insect: Yup.string().required("Specifica il nome dell'insetto"),
//       trapsNumber: Yup.number(),
//     }),
//     onSubmit: (values, { setSubmitting, resetForm }) => {
//       const data = {
//         detectionTime: new Date(values.detectionTime).getTime(),
//         note: values.note,
//         details: {
//           insect: values.insect,
//           trapsNumber: values.trapsNumber,
//         },
//         files: files,
//       };
//       onNextClick(data);
//       resetForm({});
//       setSubmitting(false);
//     },
//   });

//   const onDrop = React.useCallback((acceptedFiles: any) => {
//     setFiles(acceptedFiles);
//   }, []);

//   const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple: false });

//   const filesPreview = files.map((file: FileWithPath) => (
//     <li key={file.name}>
//       <span className="mr-2">{file.name}</span>
//     </li>
//   ));

//   return (
//     <form onSubmit={formik.handleSubmit} autoComplete="off">
//       <h4 className="mt-4 mb-4">Dati del rilevamento: Insetti</h4>
//       <div className="input-row">
//         <label>
//           Data del rilevamento
//           <input
//             id="detectionTime"
//             name="detectionTime"
//             type="datetime-local"
//             placeholder="Data rilevamento"
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.detectionTime}
//           />
//         </label>
//         {formik.touched.detectionTime && formik.errors.detectionTime ? (
//           <div className="error">{formik.errors.detectionTime}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <label>
//           Nome dell'insetto
//           <input
//             id="insect"
//             name="insect"
//             type="text"
//             placeholder="Nome insetto"
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.insect}
//           />
//         </label>
//         {formik.touched.insect && formik.errors.insect ? (
//           <div className="error">{formik.errors.insect}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <label>
//           Numero di trappole
//           <input
//             id="trapsNumber"
//             name="trapsNumber"
//             type="text"
//             placeholder="Numero di trappole"
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.trapsNumber}
//           />
//         </label>
//         {formik.touched.trapsNumber && formik.errors.trapsNumber ? (
//           <div className="error">{formik.errors.trapsNumber}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <label>
//           Nota aggiuntiva
//           <textarea
//             id="note"
//             name="note"
//             placeholder=""
//             rows={15}
//             cols={50}
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.note}
//           ></textarea>
//         </label>
//         {formik.touched.note && formik.errors.note ? (
//           <div className="error">{formik.errors.note}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <div {...getRootProps()}>
//           <input {...getInputProps()} accept=".png, .jpeg, .jpg" />
//           {isDragActive ? (
//             <p>Trascina i file qui...</p>
//           ) : (
//             <p>Trascina e rilascia alcuni file qui, oppure fai clic per selezionarli</p>
//           )}
//         </div>
//         --------------------------------------------------------------------------
//         <div>
//           <ul>{filesPreview}</ul>
//         </div>
//       </div>
//       <hr />
//       <div className="buttons-wrapper">
//         <button className="trnt_btn secondary" onClick={onBackClick}>
//           Indietro
//         </button>
//         <input type="submit" className="primary" value={action} />
//       </div>
//     </form>
//   );
// }

// function DetectionFormAltro({ action, onBackClick, onNextClick }: DetectionProps) {
//   const [files, setFiles] = React.useState<FileWithPath[]>([]);

//   const formik = useFormik({
//     initialValues: {
//       detectionTime: "",
//       note: "",
//     },
//     validationSchema: Yup.object({
//       detectionTime: Yup.string().required("Specifica la data del rilevamento"),
//     }),
//     onSubmit: (values, { setSubmitting, resetForm }) => {
//       const data = {
//         detectionTime: new Date(values.detectionTime).getTime(),
//         note: values.note,
//         details: {},
//         files: files,
//       };
//       onNextClick(data);
//       resetForm({});
//       setSubmitting(false);
//     },
//   });

//   const onDrop = React.useCallback((acceptedFiles: any) => {
//     setFiles(acceptedFiles);
//   }, []);

//   const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple: false });
//   const filesPreview = files.map((file: FileWithPath) => (
//     <li key={file.name}>
//       <span className="mr-2">{file.name}</span>
//     </li>
//   ));

//   return (
//     <form onSubmit={formik.handleSubmit} autoComplete="off">
//       <h4 className="mt-4 mb-4">Dati del rilevamento: Insetti</h4>
//       <div className="input-row">
//         <label>
//           Data del rilevamento
//           <input
//             id="detectionTime"
//             name="detectionTime"
//             type="datetime-local"
//             placeholder="Data rilevamento"
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.detectionTime}
//           />
//         </label>
//         {formik.touched.detectionTime && formik.errors.detectionTime ? (
//           <div className="error">{formik.errors.detectionTime}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <label>
//           Nota
//           <textarea
//             id="note"
//             name="note"
//             placeholder=""
//             rows={15}
//             cols={50}
//             onChange={formik.handleChange}
//             onBlur={formik.handleBlur}
//             value={formik.values.note}
//           ></textarea>
//         </label>
//         {formik.touched.note && formik.errors.note ? (
//           <div className="error">{formik.errors.note}</div>
//         ) : null}
//       </div>
//       <div className="input-row">
//         <div {...getRootProps()}>
//           <input {...getInputProps()} accept=".png, .jpeg, .jpg" />
//           {isDragActive ? (
//             <p>Trascina i file qui...</p>
//           ) : (
//             <p>Trascina e rilascia alcuni file qui, oppure fai clic per selezionarli</p>
//           )}
//         </div>
//         --------------------------------------------------------------------------
//         <div>
//           <ul>{filesPreview}</ul>
//         </div>
//       </div>
//       <hr />
//       <div className="buttons-wrapper">
//         <button className="trnt_btn secondary" onClick={onBackClick}>
//           Indietro
//         </button>
//         <input type="submit" className="primary" value={action} />
//       </div>
//     </form>
//   );
// }

interface DetectionFormMapProps {
  sourceType: string;
  onMarkerChange: (p: Point) => Promise<void>;
}

function DetectionFormMapPosition({ sourceType, onMarkerChange }: DetectionFormMapProps) {
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default")
  );
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  const [mapLoaded, setMapLoaded] = React.useState(false);
  const markerRef = React.useRef<Marker | null>(null);
  const currentPosition = React.useContext(gpsStore);

  // React.useEffect(() => {
  //   if (map.current) return; // initialize only once

  //   map.current = new mapboxgl.Map({
  //     container: mapContainer.current!,
  //     style: "mapbox://styles/mapbox/streets-v11",
  //     center: [0, 0],
  //     zoom: 14,
  //   });

  //   // Add source + layer for current location
  //   map.current.on("load", () => {
  //     map.current!.addSource("current-location", {
  //       type: "geojson",
  //       data: {
  //         type: "Feature",
  //         geometry: { type: "Point", coordinates: [0, 0] },
  //       },
  //     });

  //     map.current!.addLayer({
  //       id: "current-location-circle",
  //       type: "circle",
  //       source: "current-location",
  //       paint: {
  //         "circle-radius": 12,
  //         "circle-color": "#007AFF", // iOS blue
  //         "circle-opacity": 0.6,
  //       },
  //     });

  //     // Animate pulsing radius
  //     let radius = 10;
  //     let growing = true;

  //     function animate() {
  //       radius = growing ? radius + 0.3 : radius - 0.3;
  //       if (radius > 20) growing = false;
  //       if (radius < 10) growing = true;

  //       map.current!.setPaintProperty(
  //         "current-location-circle",
  //         "circle-radius",
  //         radius
  //       );

  //       requestAnimationFrame(animate);
  //     }
  //     animate();
  //   });

  //   // Watch position continuously
  //   const watchId = navigator.geolocation.watchPosition(
  //     (pos) => {
  //       const lng = pos.coords.longitude;
  //       const lat = pos.coords.latitude;

  //       // Update source data
  //       const source = map.current!.getSource("current-location") as mapboxgl.GeoJSONSource;
  //       if (source) {
  //         source.setData({
  //           type: "Feature",
  //           geometry: { type: "Point", coordinates: [lng, lat] },
  //         });
  //       }

  //       // Optionally recenter map
  //       map.current!.setCenter([lng, lat]);
  //     },
  //     (err) => console.error("Geolocation error:", err),
  //     { enableHighAccuracy: true }
  //   );

  //   return () => navigator.geolocation.clearWatch(watchId);
  // }, []);

  React.useEffect(() => {
    // -------------------------------
    // also set marker position if the
    if (sourceType === "current" && currentPosition) {
      // console.log(">>>>>>>>>>>>>>>>> sourceType updated", sourceType);
      // console.log(">>>>>>>>>>>>>>>>> currentPosition updated", currentPosition);
      if (markerRef.current) {
        markerRef.current.setLngLat([currentPosition.lng, currentPosition.lat]);
      } else {
        // markerRef.current = new mapboxgl.Marker(markerOptions)
        //   .setLngLat([currentPosition.lng, currentPosition.lat])
        //   .addTo(mapRef.current!);
      }
    }
    // -------------------------------
  }, [sourceType]);

  React.useEffect(() => {
    if (mapContainerRef.current && currentField) {
      mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_API_TOKEN;

      let areaPoints: number[][] = [];
      currentField.map.forEach((point: Point) => {
        areaPoints.push([point.lng, point.lat]);
      });
      if (areaPoints.length <= 2) {
        console.log("••• not enough points to draw the field shape", areaPoints);
        return;
      }

      let centroid: LngLatLike = [12.5736108, 41.29246];
      let fieldShapeBbox: any;
      if (areaPoints.length > 2) {
        const polygon = turf.polygon([areaPoints]);
        const result = turf.centroid(polygon);
        centroid = [result.geometry.coordinates[0], result.geometry.coordinates[1]];
        fieldShapeBbox = turf.bbox(polygon);
        console.log("••• bbox", fieldShapeBbox);
      }

      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/satellite-streets-v12",
        center: centroid,
        zoom: 14,
      });

      mapRef.current.on("load", () => {
        console.log("map loaded", mapRef);

        const source = mapRef.current.getSource("fieldShape");
        if (!source) {
          mapRef.current.addSource("fieldShape", {
            type: "geojson",
            data: {
              type: "Feature",
              geometry: {
                type: "Polygon",
                coordinates: [areaPoints],
              },
            },
          });
        }

        mapRef.current.addLayer({
          id: "fieldShape",
          type: "fill",
          source: "fieldShape",
          layout: {},
          paint: {
            "fill-color": "#fff",
            "fill-opacity": 0.5,
          },
        });
        mapRef.current.addLayer({
          id: "fieldShapeLine",
          type: "line",
          source: "fieldShape",
          layout: {},
          paint: {
            "line-color": "#fff",
            "line-width": 2,
            "line-opacity": 1.0, // outline opacity
          },
        });

        mapRef.current.fitBounds(fieldShapeBbox, {
          padding: { top: 10, bottom: 10, left: 10, right: 10 },
        });

        // --------------------------------------------------
        // Add source + layer for current location
        mapRef.current!.addSource("current-location", {
          type: "geojson",
          data: {
            type: "Feature",
            geometry: { type: "Point", coordinates: [0, 0] },
          },
        });

        // Static dot
        mapRef.current!.addLayer({
          id: "current-location-dot",
          type: "circle",
          source: "current-location",
          paint: {
            "circle-radius": 5,
            "circle-color": "#007AFF",
            "circle-opacity": 1,
          },
        });

        // Pulse layer
        mapRef.current!.addLayer({
          id: "current-location-pulse",
          type: "circle",
          source: "current-location",
          paint: {
            "circle-radius": 5,
            "circle-color": "#007AFF",
            "circle-opacity": 0,
            "circle-radius-transition": { duration: 0, delay: 0 },
            "circle-opacity-transition": { duration: 0, delay: 0 },
          },
        });

        function animatePulse(startTime: number) {
          const t = (performance.now() - startTime) / 1000;
          const cycle = 2; // seconds per pulse
          const minRadius = 5;
          const maxRadius = 40;
          const maxOpacity = 0.8;

          // Instead of one pulse, compute multiple overlapping pulses
          const pulses = 3; // number of simultaneous ripples
          const radii: number[] = [];
          const opacities: number[] = [];

          for (let i = 0; i < pulses; i++) {
            const offset = i * (cycle / pulses);
            const progress = ((t - offset) % cycle) / cycle;

            const radius = minRadius + progress * (maxRadius - minRadius);
            const opacity = maxOpacity * (1 - progress);

            radii.push(radius);
            opacities.push(opacity);
          }

          // Use the largest radius and highest opacity for the layer
          // (or dynamically create multiple layers if you want all visible)
          const radius = radii[0];
          const opacity = opacities[0];

          if (mapRef.current) {
            mapRef.current.setPaintProperty("current-location-pulse", "circle-radius", radius);
            mapRef.current.setPaintProperty("current-location-pulse", "circle-opacity", opacity);
          }

          requestAnimationFrame(() => animatePulse(startTime));
        }

        animatePulse(performance.now());
        // --------------------------------------------------

        mapRef.current.on("click", function (e: any) {
          const { lng, lat } = e.lngLat;

          // Check if inside field shape
          let point: Point = {
            lat: lat,
            lng: lng,
          };
          console.log(">>> clicked point", point);

          const isIt = isPointInsideField(lng, lat, areaPoints);
          console.log(">>> isPointInsideField? " + isIt);
          if (!isIt) {
            turf.polygon([areaPoints]);
            const polygon = turf.polygon([areaPoints]);
            const p = turf.point([lng, lat]);

            const boundary = turf.polygonToLine(polygon);
            const nearest = turf.nearestPointOnLine(boundary, p);

            point = {
              lat: nearest.geometry.coordinates[1],
              lng: nearest.geometry.coordinates[0],
            };
            // alert("Attenzione: il punto selezionato non è all'interno del campo!");
            console.log(">>> nearest point on field boundary", nearest);
          }

          if (markerRef.current) {
            markerRef.current.setLngLat([point.lng, point.lat]);
          } else {
            markerRef.current = new mapboxgl.Marker(markerOptions)
              .setLngLat([point.lng, point.lat])
              .addTo(mapRef.current!);
          }

          onMarkerChange(point);
        });

        setMapLoaded(true);
      });

      return () => {
        mapRef.current.remove();
      };
    }
  }, [mapContainerRef, currentField]);

  React.useEffect(() => {
    // Update source data
    const source = mapRef.current!.getSource("current-location") as mapboxgl.GeoJSONSource;
    if (source) {
      source.setData({
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [currentPosition.lng, currentPosition.lat],
        },
        properties: {}, // 👈 required by type definition
      });

      // -------------------------------
      // also set marker position if the
      if (markerRef.current) {
        markerRef.current.setLngLat([currentPosition.lng, currentPosition.lat]);
      } else {
        markerRef.current = new mapboxgl.Marker(markerOptions)
          .setLngLat([currentPosition.lng, currentPosition.lat])
          .addTo(mapRef.current!);
      }
      // -------------------------------
    }

    // Optionally recenter map
    // mapRef.current!.setCenter([lng, lat]);
    // ----------------------------------
  }, [mapLoaded, currentPosition]);

  return (
    <div>
      <div ref={mapContainerRef} id="map" className="map-detection-form"></div>
    </div>
  );
}

const categorie: any = {
  fungi: {
    icon: "spots",
    name: "Fungo e peronospora",
    items: {
      peronospora: {
        name: "Peronospora",
        icon: false,
      },
      other_fungi: {
        name: "Altro fungo",
        icon: false,
      },
    },
  },
  bacteria: {
    icon: "bacteria",
    name: "Batterio",
    items: {
      flavescenza: {
        name: "Flavescenza",
        icon: false,
      },
      other_bacteria: {
        name: "Altro batterio",
        icon: false,
      },
    },
  },
  insect: {
    icon: "bug",
    name: "Insetto",
    items: {
      scafoideo: {
        name: "Scafoideo",
        icon: false,
      },
      cimice: {
        name: "Cimice",
        // icon: "baloon",
        icon: false,
      },
      diabrotica: {
        name: "Diabrotica",
        icon: false,
      },
      other_insect: {
        name: "Altro insetto",
        icon: false,
      },
    },
  },
};

const methods: any = {
  peronospora: {
    title: (
      <span>
        Rilevamento di <strong>peronospora</strong> su…
      </span>
    ),
    items: ["Foglia", "Frutto", "Tutta la pianta"],
  },
  other_fungi: {
    title: (
      <span>
        Rilevamento di <strong>altro fungo</strong> su…
      </span>
    ),
    items: ["Foglia", "Frutto", "Tutta la pianta"],
  },
  flavescenza: {
    title: (
      <span>
        Rilevamento di <strong>flavescenza</strong> su…
      </span>
    ),
    items: ["Foglia", "Frutto", "Tutta la pianta"],
  },
  other_bacteria: {
    title: (
      <span>
        Rilevamento di <strong>altro batterio</strong> su…
      </span>
    ),
    items: ["Foglia", "Frutto", "Tutta la pianta"],
  },
  cimice: {
    title: (
      <span>
        Scegli un metodo di rilevamento della <strong>cimice</strong>
      </span>
    ),
    items: ["Trappola", "Campo (Frappage – Visivo)"],
  },
  scafoideo: {
    title: (
      <span>
        Scegli un focus di rilevamento dello <strong>scafoideo</strong>
      </span>
    ),
    items: ["Foglie basali/polloni", "Chioma"],
  },
  diabrotica: {
    title: (
      <span>
        Scegli un metodo di rilevamento della <strong>diabrotica</strong>
      </span>
    ),
    items: [],
  },
  other_insect: {
    title: (
      <span>
        Scegli un metodo di rilevamento di <strong>altro insetto</strong>
      </span>
    ),
    items: ["Trappola", "Altro"],
  },
};

interface AccordionTipologiaProps {
  onSelect: (selection: string) => void;
}

function AccordionTipologia({ onSelect }: AccordionTipologiaProps) {
  let items: AccordionItem[] = [];
  items = Object.keys(categorie).map((key: string, index: number) => {
    let iconNameAccItem = categorie[key].icon ?? null;
    return {
      id: index.toString(),
      title: categorie[key].name,
      content: (
        <Fragment>
          {Object.keys(categorie[key].items).map((itemKey: string, itemIndex) => {
            let iconNameBtn = categorie[key].icon ?? null;
            if (categorie[key].items[itemKey].icon) {
              iconNameBtn = categorie[key].items[itemKey].icon;
            }
            if (categorie[key].items[itemKey].icon === false) {
              iconNameBtn = null;
            }
            return (
              <CozyButton
                key={itemIndex}
                iconName={iconNameBtn}
                content={categorie[key].items[itemKey].name || "Altro"}
                onClick={() => onSelect(itemKey)}
                arrow={true}
              />
            );
          })}
        </Fragment>
      ),
      icon: iconNameAccItem,
    };
  });
  return (
    <div className="narrow-container my-5">
      <h3 className="mb-4 text-center">Seleziona la tipologia di rilevamento</h3>
      <Accordion items={items} />
    </div>
  );
}

function DetectionStepPosizione({ action, onNextClick }: DetectionProps) {
  const [source, setSource] = React.useState<string>("current");
  const [modalOpen, setModalOpen] = React.useState(false);
  const [modal, setModal] = React.useState<any>({});
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default")
  );

  const currentPosition = React.useContext(gpsStore);
  const [hasGeolocation, setHasGeolocation] = React.useState<boolean>(false);
  const [markerPosition, setMarkerPosition] = React.useState<Point>();

  React.useEffect(() => {
    if (navigator.geolocation) {
      setHasGeolocation(true);
    }
  }, []);

  const handleSourceChange = (value: string) => {
    setSource(value);
  };

  const handleMarkerChange = async (point: Point) => {
    setMarkerPosition(point);
    setSource("map");
  };

  const handleNextClick = async () => {
    if (source === "current" && !hasGeolocation) {
      setModal({
        component: ModalConfirm,
        componentProps: {
          title: "Rilevamento",
          content:
            "Non è possibile utilizzare la posizione corrente perché il browser non supporta la geolocalizzazione.",
          action: "Ok",
          handleCancel: () => setModalOpen(false),
          handleConfirm: () => {
            setModalOpen(false);
          },
        },
      });
      setModalOpen(true);
      return;
    }

    if (source === "map" && !markerPosition) {
      setModal({
        component: ModalConfirm,
        componentProps: {
          title: "Rilevamento",
          content: "Devi selezionare un punto sulla mappa.",
          action: "Ok",
          handleCancel: () => setModalOpen(false),
          handleConfirm: () => {
            setModalOpen(false);
          },
        },
      });
      setModalOpen(true);
      return;
    }

    if (source === "current" && hasGeolocation) {
      let data: number[][] = [];
      currentField.map.forEach((point: Point) => {
        data.push([point.lng, point.lat]);
      });
      if (data.length > 2) {
        const polygon = turf.polygon([data]);
        if (!hasGeolocation) {
          console.log("No Geolocation data");
          return;
        } else {
          const point = turf.point([currentPosition.lng, currentPosition.lat]);
          const geolocationValid = turf.booleanContains(polygon, point);
          console.log("Geolocation valid?", geolocationValid);
          if (!geolocationValid) {
            setModal({
              component: ModalConfirm,
              componentProps: {
                title: "Rilevamento",
                content:
                  "La tua posizione corrente risulta fuori dall'area del campo. Scegli un altro punto cliccando sulla mappa.",
                action: "Ok",
                handleCancel: () => setModalOpen(false),
                handleConfirm: () => {
                  setSource("map");
                  setModalOpen(false);
                },
              },
            });
            setModalOpen(true);
            return;
          }
        }
      }
    }

    const data = {
      latitude: source === "current" ? currentPosition.lat : markerPosition?.lat,
      longitude: source === "current" ? currentPosition.lng : markerPosition?.lng,
    };

    onNextClick(data);
  };

  return (
    <Fragment>
      {modalOpen && <modal.component {...modal.componentProps} />}
      {/* <h4 className="mt-4">La tua posizione</h4> */}
      <div className="input-row">
        <label>
          <select name="source" onChange={(e) => handleSourceChange(e.target.value)} value={source}>
            <option value="current">Usa posizione corrente</option>
            <option value="map">Seleziona un punto sulla mappa</option>
            <option value="map">Rilevamento per l'intero campo</option>
          </select>
        </label>
      </div>
      <DetectionFormMapPosition sourceType={source} onMarkerChange={handleMarkerChange} />
      {/* <hr /> */}
      <div className="buttons-wrapper mt-4 text-center">
        <button className="trnt_btn primary" onClick={handleNextClick}>
          {action}
        </button>
      </div>
    </Fragment>
  );
}

function DetectionStepTipologia({
  typologies,
  onNextClick,
}: DetectionProps & { typologies: string[] }) {
  return (
    <div className="narrow-container my-5">
      <h3 className="mb-4 text-center">Seleziona la tipologia di rilevamento</h3>
      {typologies.length === 0 && <div>Nessuna tipologia disponibile.</div>}
      {typologies.map((item, index) => (
        <CozyButton
          key={index}
          content={item}
          onClick={() => onNextClick({ typology: item })}
          arrow={true}
        />
      ))}
    </div>
  );
}

function DetectionStepMetodo({
  typology,
  methods,
  onNextClick,
}: DetectionProps & { typology: string; methods: string[] }) {
  return (
    <div className="narrow-container my-5">
      <h3 className="mb-4 text-center">Seleziona il metodo di osservazione</h3>
      {typology && <p className="text-center">Tipologia: {typology}</p>}
      {methods.length === 0 && <div>Nessun metodo disponibile.</div>}
      {methods.map((item, index) => (
        <CozyButton
          key={index}
          content={item}
          onClick={() => onNextClick({ method: item })}
          arrow={true}
        />
      ))}
    </div>
  );
}

function DetectionStepGuide({
  detectionText,
  onNextClick,
}: DetectionProps & { detectionText?: DetectionText }) {
  return (
    <div className="narrow-container my-5 text-center">
      <h3 className="mb-4">Guida all'osservazione</h3>
      {detectionText ? (
        <Fragment>
          <div className="mb-3">
            <strong>Istruzioni posizione e punteggio</strong>
            <p>{detectionText.locationAndScoreInstructions}</p>
          </div>
          <div className="mb-4">
            <strong>Istruzioni BBCH</strong>
            <p>{detectionText.bbchInstructions}</p>
          </div>
        </Fragment>
      ) : (
        <div>Nessuna guida disponibile per questa tipologia e metodo.</div>
      )}
      <div className="buttons-wrapper mt-4 text-center">
        <button className="trnt_btn primary" onClick={() => onNextClick({})}>
          Avanti
        </button>
      </div>
    </div>
  );
}

function DetectionStepBbch({
  formData,
  onNextClick,
}: DetectionProps) {
  const [bbch, setBbch] = React.useState(formData?.detectionData?.bbch ?? "");
  const [notes, setNotes] = React.useState(formData?.detectionData?.notes ?? "");

  React.useEffect(() => {
    setBbch(formData?.detectionData?.bbch ?? "");
    setNotes(formData?.detectionData?.notes ?? "");
  }, [formData]);

  return (
    <div className="narrow-container my-5">
      <h3 className="mb-4 text-center">Seleziona BBCH</h3>
      <div className="input-row">
        <label>
          BBCH
          <input
            id="bbch"
            name="bbch"
            type="text"
            placeholder="BBCH"
            onChange={(event) => setBbch(event.target.value)}
            value={bbch}
          />
        </label>
      </div>
      <div className="input-row">
        <label>
          Note
          <textarea
            id="notes"
            name="notes"
            placeholder=""
            rows={6}
            onChange={(event) => setNotes(event.target.value)}
            value={notes}
          ></textarea>
        </label>
      </div>
      <div className="buttons-wrapper mt-4 text-center">
        <button className="trnt_btn primary" onClick={() => onNextClick({ bbch, notes })}>
          Avanti
        </button>
      </div>
    </div>
  );
}

function DetectionStepObservationPoints({
  formData,
  observationType,
  onNextClick,
  onBackClick,
}: DetectionProps & { observationType?: ObservationType }) {
  if (observationType?.observationType === "range") {
    return (
      <DetectionUI formData={formData} onBackClick={onBackClick} onNextClick={onNextClick} />
    );
  }
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default")
  );
  const currentPosition = React.useContext(gpsStore);
  const [source, setSource] = React.useState<string>("current");
  const [markerPosition, setMarkerPosition] = React.useState<Point>();
  const [rangeValue, setRangeValue] = React.useState<string>("");
  const [counterValues, setCounterValues] = React.useState<Record<string, string>>({});
  const [points, setPoints] = React.useState(formData?.detectionData?.points ?? []);
  const [photos, setPhotos] = React.useState<File[]>(
    (formData?.detectionData?.photos as File[]) ?? []
  );
  const [cameraOpen, setCameraOpen] = React.useState(false);
  const [modalOpen, setModalOpen] = React.useState(false);
  const [modal, setModal] = React.useState<any>({});

  React.useEffect(() => {
    setPoints(formData?.detectionData?.points ?? []);
  }, [formData]);

  React.useEffect(() => {
    if (!observationType) {
      return;
    }
    if (observationType.observationType === "counters") {
      const defaults: Record<string, string> = {};
      observationType.counters.forEach((counter) => {
        defaults[counter] = "";
      });
      setCounterValues(defaults);
    }
  }, [observationType]);

  const handleMarkerChange = async (point: Point) => {
    setMarkerPosition(point);
    setSource("map");
  };

  const buildPointData = () => {
    if (!observationType) {
      return null;
    }
    if (observationType.observationType === "range") {
      if (rangeValue === "") {
        return null;
      }
      return {
        rangeValue: Number(rangeValue),
        counters: [],
      };
    }
    const counters = observationType.counters.map((counter) => {
      return {
        counterName: counter,
        counterValue: Number(counterValues[counter] || 0),
      };
    });
    return {
      rangeValue: null,
      counters,
    };
  };

  const validatePoint = () => {
    if (!currentField) {
      return "Campo non trovato.";
    }
    if (source === "current" && !currentPosition) {
      return "Posizione corrente non disponibile.";
    }
    if (source === "map" && !markerPosition) {
      return "Devi selezionare un punto sulla mappa.";
    }
    const point = source === "current" ? currentPosition : markerPosition;
    if (!point) {
      return "Posizione non valida.";
    }
    const areaPoints: number[][] = currentField.map.map((pt: Point) => [pt.lng, pt.lat]);
    if (areaPoints.length > 2 && !isPointInsideField(point.lng, point.lat, areaPoints)) {
      return "Il punto selezionato è fuori dall'area del campo.";
    }
    if (!buildPointData()) {
      return "Inserisci i dati dell'osservazione.";
    }
    return null;
  };

  const handleAddPoint = () => {
    const error = validatePoint();
    if (error) {
      setModal({
        component: ModalConfirm,
        componentProps: {
          title: "Rilevamento",
          content: error,
          action: "Ok",
          handleCancel: () => setModalOpen(false),
          handleConfirm: () => setModalOpen(false),
        },
      });
      setModalOpen(true);
      return;
    }
    const point = source === "current" ? currentPosition : markerPosition;
    const data = buildPointData();
    if (!point || !data) {
      return;
    }
    setPoints((prev) => [
      ...prev,
      {
        position: {
          lng: point.lng,
          lat: point.lat,
        },
        data,
      },
    ]);
    setMarkerPosition(undefined);
    setRangeValue("");
    if (observationType?.observationType === "counters") {
      const defaults: Record<string, string> = {};
      observationType.counters.forEach((counter) => {
        defaults[counter] = "";
      });
      setCounterValues(defaults);
    }
  };

  const handleSave = () => {
    if (points.length === 0) {
      setModal({
        component: ModalConfirm,
        componentProps: {
          title: "Rilevamento",
          content: "Devi aggiungere almeno un punto di osservazione.",
          action: "Ok",
          handleCancel: () => setModalOpen(false),
          handleConfirm: () => setModalOpen(false),
        },
      });
      setModalOpen(true);
      return;
    }
    onNextClick({ points, photos });
  };

  if (!observationType) {
    return (
      <div className="narrow-container my-5 text-center">
        <h3 className="mb-4">Osservazioni</h3>
        <p>Nessun tipo di osservazione disponibile per questa tipologia e metodo.</p>
      </div>
    );
  }

  return (
    <Fragment>
      {modalOpen && <modal.component {...modal.componentProps} />}
      <CameraCapture
        open={cameraOpen}
        onClose={() => setCameraOpen(false)}
        onCapture={(file) => setPhotos((prev) => [...prev, file])}
      />
      <div className="narrow-container my-5">
        <h3 className="mb-4 text-center">Aggiungi punti di osservazione</h3>
        <div className="input-row">
          <label>
            <select name="source" onChange={(e) => setSource(e.target.value)} value={source}>
              <option value="current">Usa posizione corrente</option>
              <option value="map">Seleziona un punto sulla mappa</option>
            </select>
          </label>
        </div>
        <DetectionFormMapPosition sourceType={source} onMarkerChange={handleMarkerChange} />
        <div className="my-4"></div>
        {observationType.observationType === "range" && (
          <div className="input-row">
            <label>
              Valore
              <input
                type="number"
                placeholder="Valore"
                value={rangeValue}
                onChange={(event) => setRangeValue(event.target.value)}
              />
            </label>
          </div>
        )}
        {observationType.observationType === "counters" &&
          observationType.counters.map((counter) => (
            <div className="input-row" key={counter}>
              <label>
                {counter}
                <input
                  type="number"
                  placeholder="Valore"
                  value={counterValues[counter] ?? ""}
                  onChange={(event) =>
                    setCounterValues((prev) => ({ ...prev, [counter]: event.target.value }))
                  }
                />
              </label>
            </div>
          ))}
        <div className="buttons-wrapper mt-4 text-center">
          <button className="trnt_btn secondary" onClick={handleAddPoint}>
            + Aggiungi punto
          </button>
        </div>
        {points.length > 0 && (
          <div className="mt-4">
            <h5 className="mb-3">Punti aggiunti</h5>
            {points.map((point: any, index: number) => (
              <div key={index} className="mb-2 d-flex align-items-center">
                <span className="mr-3">
                  #{index + 1} — {point.position.lat.toFixed(5)}, {point.position.lng.toFixed(5)}
                </span>
                <button
                  className="trnt_btn danger1 m-0"
                  onClick={() =>
                    setPoints((prev: any[]) => prev.filter((_, idx) => idx !== index))
                  }
                >
                  Rimuovi
                </button>
              </div>
            ))}
          </div>
        )}
        <div className="buttons-wrapper mt-4 text-center">
          <button
            className="trnt_btn secondary"
            onClick={() => setCameraOpen(true)}
          >
            + Foto
          </button>
          <button className="trnt_btn primary" onClick={handleSave}>
            Salva rilevamento
          </button>
        </div>
      </div>
    </Fragment>
  );
}

type ScoreEntry = {
  timeStamp: number;
  score: number;
  scoreNorm: number;
  location?: Point;
};

function DetectionUI({ formData, onBackClick, onNextClick }: DetectionProps) {
  const listRef = React.useRef<HTMLDivElement>(null);

  const currentPosition = React.useContext(gpsStore);

  const [scores, setScores] = useState<ScoreEntry[]>([]);
  const [photos, setPhotos] = useState<File[]>(
    (formData?.detectionData?.photos as File[]) ?? []
  );
  const [cameraOpen, setCameraOpen] = useState(false);

  const handleFinishClick = () => {
    console.log("Clicked FINE:", scores);
    if (scores.length === 0) {
      alert("Devi registrare almeno un'osservazione prima di terminare.");
      return;
    }
    const points = scores.map((entry) => {
      return {
        position: {
          lng: entry.location?.lng ?? currentPosition.lng,
          lat: entry.location?.lat ?? currentPosition.lat,
        },
        data: {
          rangeValue: entry.score,
          counters: [],
        },
      };
    });
    const hasInvalidLocation = points.some(
      (point) => point.position.lat === 0 && point.position.lng === 0
    );
    if (hasInvalidLocation) {
      alert("Posizione corrente non disponibile.");
      return;
    }
    onNextClick({ points, photos });
  };

  // Scroll to bottom whenever scores changes
  // useEffect(() => {
  //   endRef.current?.scrollIntoView({ behavior: "smooth" });
  // }, [scores]);

  useEffect(() => {
    const el = listRef.current;
    if (el) {
      el.scrollTo({
        top: el.scrollHeight, // scroll to the end
        behavior: "smooth", // animate the scroll
      });
    }
  }, [scores]); // run whenever scores updates

  const handleScoreClick = (score: number, multiplier: number) => {
    if (currentPosition.lat === 0 && currentPosition.lng === 0) {
      alert("Posizione corrente non disponibile.");
      return;
    }
    for (let i = 0; i < multiplier; i++) {
      const scoreEntry = {
        timeStamp: new Date().getTime(),
        score: score,
        scoreNorm: score / 5,
        location: currentPosition,
      };
      setScores((prev) => [...prev, scoreEntry]);
    }
    console.log(
      `Scores (${scores.length})`,
      scores
      // scores
      //   .slice(-5)
      //   .map((entry) => entry.score)
      //   .join(", ")
    );
  };
  function ScoreBtnRow({ score, label }: { score: number; label: string }) {
    return (
      <div className="d-flex" style={{ gap: "4px", marginBottom: "4px" }}>
        <div style={{ width: "90%" }}>
          <CozyButton
            btnSize="small"
            content={btnCnt(score, label)}
            onClick={() => handleScoreClick(score, 1)}
          />
        </div>
        <div style={{ width: "63px" }}>
          <CozyButton btnSize="small" content={"×5"} onClick={() => handleScoreClick(score, 5)} />
        </div>
      </div>
    );
  }

  const scoreDots = (dotsNum = 5, score = 0) => {
    const dots = Array.from({ length: dotsNum }, (_, i) => {
      const circleType = i < score ? "circlefull" : "circleempty";
      return <Icon key={i} iconName={circleType} color="black" />;
    });
    return <span className="score-dots">{dots}</span>;
  };

  const btnCnt = (score: number, label: string) => {
    return (
      <div className="d-inline-flex align-items-center mt-1">
        {scoreDots(5, score)}
        <div>{label}</div>
      </div>
    );
  };

  const getStat = (scores: ScoreEntry[], stat: string) => {
    if (scores.length === 0) return "-";
    if (stat === "pianteColpite") {
      // count entries with score > 0
      const infectedCount = scores.filter((entry) => entry.score > 0).length;
      const percent = ((infectedCount / scores.length) * 100).toFixed(1);
      return `${percent}%`;
    } else if (stat === "intensitaMedia") {
      const totalScores = scores.reduce((acc, entry) => acc + entry.scoreNorm, 0);
      const avgScore = totalScores / scores.length;
      const percent = (avgScore * 100).toFixed(1);
      return `${percent}%`;
    }
    return "-";
  };

  return (
    <Fragment>
      <div className="hacky-header-cover">
        <a
          onClick={() => {
            onBackClick?.();
          }}
        >
          &larr;
        </a>
        <a
          onClick={() => {
            setCameraOpen(true);
          }}
        >
          <span>FOTO</span>
        </a>
        <a
          className="finish-btn"
          onClick={() => {
            handleFinishClick();
          }}
        >
          <span>FINE</span>
        </a>
      </div>
      <CameraCapture
        open={cameraOpen}
        onClose={() => setCameraOpen(false)}
        onCapture={(file) => setPhotos((prev) => [...prev, file])}
      />

      <div className="narrow-container">
        <div className="detection-ui">
          <div className="detection-scores">
            <Container className="h-100 p-0">
              <Row className="h-100">
                <Col className="h-100">
                  <div className="scores-list-wrapper">
                    <div className="scores-list" ref={listRef}>
                      <header className="font-s-label">Ultime osservazioni</header>
                      {scores.length === 0 && <div>Nessuna osservazione ancora registrata</div>}
                      {scores.map((entry, index) => (
                        <div key={index} className="score-entry">
                          <span className="txt new-score-entry">
                            <span>#{index + 1}</span> — <span>{entry.score}</span>
                          </span>
                        </div>
                      ))}
                      {/* <div ref={endRef} /> invisible anchor */}
                    </div>
                  </div>
                </Col>
                <Col className="h-100">
                  <header className="font-s-label">Piante colpite</header>
                  <div className="font-xl mt-1 mb-3">{getStat(scores, "pianteColpite")}</div>
                  <header className="font-s-label">Intensità media</header>
                  <div className="font-xl mt-1 mb-3">{getStat(scores, "intensitaMedia")}</div>
                </Col>
              </Row>
            </Container>
          </div>
          <div className="detection-inputs">
            <div className="mt-2 mb-3">
              <div className="font-s-label">Osservazione #{scores.length + 1}</div>
              <div className="font-l mt-1">Valuta l'intensità del problema</div>
            </div>
            <ScoreBtnRow score={0} label="Assente" />
            <ScoreBtnRow score={1} label="Basso" />
            <ScoreBtnRow score={2} label="Limitato" />
            <ScoreBtnRow score={3} label="Cospicuo" />
            <ScoreBtnRow score={4} label="Alto" />
            <ScoreBtnRow score={5} label="Molto Alto" />
          </div>
        </div>
      </div>
    </Fragment>
  );
}

function SaveDone() {
  const navigate = useNavigate();
  const { companyId, fieldId } = useParams();
  return (
    <div className="narrow-container my-5 text-center px-4">
      <div className="my-5 py-4"></div>
      <img src={doneIcon} />
      <div className="my-4"></div>
      <h3 className="mb-4">Rilevamento salvato con successo!</h3>
      <p className="mb-4 color-grey">{"(storage to be implemented)"}</p>
      <button
        className="trnt_btn"
        onClick={() => {
          navigate(`/companies/${companyId}/fields/${fieldId}`, { replace: true });
        }}
      >
        Chiudi
      </button>
    </div>
  );
}

export function DetectionForm() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { companyId, fieldId } = useParams();
  const preselectedState = location.state as { typology?: string; method?: string } | null;
  const preselectedTypology = (preselectedState?.typology ?? searchParams.get("typology") ?? "").trim();
  const preselectedMethod = (preselectedState?.method ?? searchParams.get("method") ?? "").trim();
  const hasPreselection = preselectedTypology !== "" && preselectedMethod !== "";
  const [stepIndex, setStepIndex] = React.useState(0);
  const [formData, setFormData] = React.useState<DetectionMutationPayload>({
    detectionTime: new Date().getTime(),
    detectionTypeId: "",
    detectionData: {
      bbch: "",
      notes: "",
      photos: [],
      points: [],
    },
  });
  const [selectedTypology, setSelectedTypology] = React.useState(() =>
    hasPreselection ? preselectedTypology : ""
  );
  const [selectedMethod, setSelectedMethod] = React.useState(() =>
    hasPreselection ? preselectedMethod : ""
  );
  const [useShortFlow, setUseShortFlow] = React.useState(false);

  const detectionTypes = useAppSelector((state) =>
    detectionTypesSelectors.selectDetectionTypesByField(state, fieldId ?? "default")
  );
  const detectionTexts = useAppSelector((state) =>
    detectionTextsSelectors.selectDetectionTexts(state)
  );
  const observationTypes = useAppSelector((state) =>
    observationTypesSelectors.selectObservationTypes(state)
  );

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Nuovo Rilevamento", subtitle: "Subtitle" }));
  }, []);

  React.useEffect(() => {
    if (companyId && fieldId) {
      dispatch(detectionTypesActions.fetchDetectionTypesAction({ orgId: companyId, fieldId }));
    }
    dispatch(detectionTextsActions.fetchDetectionTextsAction({}));
    dispatch(observationTypesActions.fetchObservationTypesAction({}));
  }, [companyId, fieldId, dispatch]);

  React.useEffect(() => {
    if (hasPreselection) {
      const matchingType = detectionTypes.find(
        (item) => item.typology === preselectedTypology && item.method === preselectedMethod
      );
      if (matchingType) {
        setFormData((prev) => ({
          ...prev,
          detectionTypeId: matchingType.id,
        }));
        setUseShortFlow(true);
      } else {
        setUseShortFlow(false);
      }
      return;
    } else {
      setUseShortFlow(false);
    }
  }, [detectionTypes, hasPreselection, preselectedMethod, preselectedTypology]);

  const steps = useShortFlow
    ? ["bbch", "points"]
    : hasPreselection
      ? ["bbch", "points"]
      : ["typology", "method", "guide", "bbch", "points"];

  const currentStepKey = steps[stepIndex];

  const typologyOptions = React.useMemo(() => {
    const values = detectionTexts.length
      ? detectionTexts.map((item) => item.typology)
      : observationTypes.map((item) => item.typology);
    return Array.from(new Set(values));
  }, [detectionTexts, observationTypes]);

  const methodOptions = React.useMemo(() => {
    const texts = detectionTexts.filter((item) => item.typology === selectedTypology);
    const values = texts.length
      ? texts.map((item) => item.method)
      : observationTypes
          .filter((item) => item.typology === selectedTypology)
          .map((item) => item.method);
    return Array.from(new Set(values));
  }, [detectionTexts, observationTypes, selectedTypology]);

  const detectionText = useAppSelector((state) =>
    detectionTextsSelectors.selectDetectionTextsByTypologyAndMethod(
      state,
      selectedTypology,
      selectedMethod
    )
  )[0];

  const observationType = useAppSelector((state) =>
    observationTypesSelectors.selectObservationTypesByTypologyAndMethod(
      state,
      selectedTypology,
      selectedMethod
    )
  )[0];

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
    if (currentStepKey === "typology") {
      setSelectedTypology(data.typology);
      setSelectedMethod("");
      setStepIndex(stepIndex + 1);
      return;
    }
    if (currentStepKey === "method") {
      setSelectedMethod(data.method);
      setStepIndex(stepIndex + 1);
      return;
    }
    if (currentStepKey === "guide") {
      setStepIndex(stepIndex + 1);
      return;
    }
    if (currentStepKey === "bbch") {
      setFormData((prev) => ({
        ...prev,
        detectionData: {
          ...prev.detectionData,
          bbch: data.bbch ?? "",
          notes: data.notes ?? "",
        },
      }));
      setStepIndex(stepIndex + 1);
      return;
    }
    if (currentStepKey === "points") {
      let detectionTypeId = formData.detectionTypeId;
      if (!detectionTypeId && companyId && fieldId) {
        try {
          const created = await dispatch(
            detectionTypesActions.addDetectionTypeAction({
              orgId: companyId,
              fieldId,
              body: {
                typology: selectedTypology,
                method: selectedMethod,
              },
            })
          ).then(unwrapResult);
          detectionTypeId = created.id;
          setFormData((prev) => ({
            ...prev,
            detectionTypeId: created.id,
          }));
        } catch (error) {
          console.error("Error creating detection type:", error);
          return;
        }
      }

      if (!detectionTypeId) {
        console.error("Missing detection type id for detection creation.");
        return;
      }

      const payload: DetectionMutationPayload = {
        ...formData,
        detectionTypeId: detectionTypeId,
        detectionData: {
          ...formData.detectionData,
          points: data.points ?? [],
          photos: data.photos ?? formData.detectionData.photos ?? [],
        },
      };
      await createDetectionAction(payload);
    }
  };

  const handleBackClick = async () => {
    if (stepIndex > 0) {
      setStepIndex(stepIndex - 1);
    }
  };

  return (
    <Fragment>
      <div>
        {currentStepKey === "typology" && (
          <DetectionStepTipologia
            typologies={typologyOptions}
            formData={formData}
            onNextClick={handleNextClick}
          />
        )}
        {currentStepKey === "method" && (
          <DetectionStepMetodo
            typology={selectedTypology}
            methods={methodOptions}
            onBackClick={handleBackClick}
            onNextClick={handleNextClick}
          />
        )}
        {currentStepKey === "guide" && (
          <DetectionStepGuide
            formData={formData}
            onBackClick={handleBackClick}
            detectionText={detectionText}
            onNextClick={handleNextClick}
          />
        )}
        {currentStepKey === "bbch" && (
          <DetectionStepBbch
            formData={formData}
            onBackClick={handleBackClick}
            onNextClick={handleNextClick}
          />
        )}
        {currentStepKey === "points" && (
          <DetectionStepObservationPoints
            formData={formData}
            onBackClick={handleBackClick}
            observationType={observationType}
            onNextClick={handleNextClick}
          />
        )}
      </div>
    </Fragment>
  );
}
