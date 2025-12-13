import React, { Fragment, useEffect, useState } from "react";
import { Col, Container, Row } from "react-bootstrap";
// import { useFormik } from "formik";
// import * as Yup from "yup";
import { DetectionMutationPayload, FilesApi } from "@tornatura/coreapis";
import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import { detectionsActions } from "../state/detections-slice";
import { FileWithPath /* , useDropzone */ } from "react-dropzone";
import { getCoreApiConfiguration } from "../../../services/utils";
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
import doneIcon from "../../../assets/images/icon-large-done.svg";

interface DetectionProps {
  formData: DetectionMutationPayload;
  action: string;
  onBackClick?: () => Promise<void>;
  onNextClick: (data: any) => Promise<void>;
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
  onMarkerChange: (p: Point) => Promise<void>;
}

function DetectionFormMapPosition({ onMarkerChange }: DetectionFormMapProps) {
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default")
  );
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  const [mapLoaded, setMapLoaded] = React.useState(false);
  const [inputValue, setInputValue] = React.useState("");
  const markerRef = React.useRef<Marker | null>(null);

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
            "fill-color": "#c4c920",
            "fill-opacity": 0.7,
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

        mapRef.current!.addLayer({
          id: "current-location-circle",
          type: "circle",
          source: "current-location",
          paint: {
            "circle-radius": 12,
            "circle-color": "#007AFF", // iOS blue
            "circle-opacity": 0.6,
          },
        });

        // Animate pulsing radius
        let radius = 10;
        let growing = true;

        function animate() {
          radius = growing ? radius + 0.3 : radius - 0.3;
          if (radius > 20) growing = false;
          if (radius < 10) growing = true;

          mapRef.current!.setPaintProperty("current-location-circle", "circle-radius", radius);

          requestAnimationFrame(animate);
        }
        animate();
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
            markerRef.current = new mapboxgl.Marker()
              .setLngLat([point.lng, point.lat])
              .addTo(mapRef.current!);
          }

          onMarkerChange(point);
        });

        setMapLoaded(true);
      });

      // ----------------------------------
      // Watch position continuously
      const watchId = navigator.geolocation.watchPosition(
        (pos) => {
          const lng = pos.coords.longitude;
          const lat = pos.coords.latitude;

          // Update source data
          const source = mapRef.current!.getSource("current-location") as mapboxgl.GeoJSONSource;
          if (source) {
            source.setData({
              type: "Feature",
              geometry: {
                type: "Point",
                coordinates: [lng, lat],
              },
              properties: {}, // 👈 required by type definition
            });
          }

          // Optionally recenter map
          // mapRef.current!.setCenter([lng, lat]);
        },
        (err) => console.error("Geolocation error:", err),
        { enableHighAccuracy: true }
      );
      // ----------------------------------

      return () => {
        mapRef.current.remove();
      };
    }
  }, [mapContainerRef, currentField]);

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
      },
      other_fungi: {
        name: "Altro fungo",
      },
    },
  },
  bacteria: {
    icon: "bacteria",
    name: "Batterio",
    items: {
      flavescenza: {
        name: "Flavescenza",
      },
      other_bacteria: {
        name: "Altro batterio",
      },
    },
  },
  insect: {
    icon: "bug",
    name: "Insetto",
    items: {
      scafoideo: {
        name: "Scafoideo",
      },
      cimice: {
        name: "Cimice",
        // icon: "baloon",
      },
      diabrotica: {
        name: "Diabrotica",
      },
      other_insect: {
        name: "Altro insetto",
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

  const [geolocation, setGeolocation] = React.useState<GeolocationPosition>();
  const [hasGeolocation, setHasGeolocation] = React.useState<boolean>(false);
  const [markerPosition, setMarkerPosition] = React.useState<Point>();

  React.useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        setGeolocation(position);
        setHasGeolocation(true);
        console.log("Geolocation position:", position);
      });
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
        console.log("Using current position: ", geolocation);
        if (geolocation === undefined || !geolocation.hasOwnProperty("coords")) {
          console.log("Geolocation coords not found");
          return;
        } else {
          const point = turf.point([geolocation.coords.longitude, geolocation.coords.latitude]);
          const geolocationValid = turf.booleanContains(polygon, point);
          console.log("Geolocation valid?", geolocationValid);

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

    const data = {
      latitude: source === "current" ? geolocation?.coords.latitude : markerPosition?.lat,
      longitude: source === "current" ? geolocation?.coords.longitude : markerPosition?.lng,
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
      <DetectionFormMapPosition onMarkerChange={handleMarkerChange} />
      <hr />
      <div className="buttons-wrapper">
        <button className="trnt_btn primary" onClick={handleNextClick}>
          {action}
        </button>
      </div>
    </Fragment>
  );
}

function DetectionStepTipologia({ onNextClick }: DetectionProps) {
  const handleOnSelectClick = (value: string) => {
    onNextClick({
      type: value,
    });
  };

  return (
    <Fragment>
      <AccordionTipologia onSelect={handleOnSelectClick} />
    </Fragment>
  );
}

function DetectionStepMetodo({ formData, onNextClick }: DetectionProps) {
  const handleOnSelectClick = (value: string) => {
    onNextClick({
      method: value,
    });
  };

  return (
    <div className="narrow-container my-5">
      <h3 className="mb-4 text-center">{methods[formData.type].title}</h3>
      {methods[formData.type].items.map((itemKey: string, itemIndex: number) => (
        <CozyButton
          key={itemIndex}
          content={itemKey}
          onClick={() => handleOnSelectClick(itemKey)}
          arrow={true}
        />
      ))}
    </div>
  );
}

type ScoreEntry = {
  timeStamp: number;
  score: number;
  scoreNorm: number;
};

function DetectionUI({ formData, onBackClick, onNextClick }: DetectionProps) {
  const listRef = React.useRef<HTMLDivElement>(null);

  const [scores, setScores] = useState<ScoreEntry[]>([]);

  const handleFinishClick = () => {
    console.log("Clicked FINE:", scores);
    if (scores.length === 0) {
      alert("Devi registrare almeno un'osservazione prima di terminare.");
      return;
    }
    onNextClick({
      scores: scores,
    });
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
    for (let i = 0; i < multiplier; i++) {
      const scoreEntry = {
        timeStamp: new Date().getTime(),
        score: score,
        scoreNorm: score / 5,
      };
      setScores((prev) => [...prev, scoreEntry]);
    }
    console.log(
      `Scores (${scores.length})`,
      scores
        .slice(-5)
        .map((entry) => entry.score)
        .join(", ")
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
        <a onClick={() => onBackClick()}>&larr;</a>
        <a
          className="finish-btn"
          onClick={() => {
            handleFinishClick();
          }}
        >
          <span>FINE</span>
        </a>
      </div>

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
  const { companyId, fieldId } = useParams();
  const [step, setStep] = React.useState(1);
  const [action, setAction] = React.useState("Avanti");
  const [formData, setFormData] = React.useState<DetectionMutationPayload | any>({
    detectionTime: new Date().getTime(),
    type: "",
    method: "",
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
        method: data.method,
      };
      setFormData(payload);
      setStep(step + 1);
      setAction("Avanti");
    } else if (step === 3) {
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
    } else if (step === 4) {
      const payload = {
        ...formData,
        scores: {
          scores: data.scores,
        },
      };
      setFormData(payload);
      setAction("Avanti");
      setStep(step + 1);
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
      {step <= 3 && (
        <div className="stepper-wrapper">
          <button
            className="stepper-back-button"
            onClick={() => {
              if (step > 1) setStep(step - 1);
              else navigate(-1);
            }}
          >
            &larr;
          </button>
          <ol className="stepper" data-steps={3}>
            <li
              data-step-num="1"
              data-done={step > 1 ? "true" : "false"}
              data-current={step == 1 ? "true" : "false"}
              onClick={() => {
                if (step > 1) setStep(1);
              }}
            >
              <span>Tipologia</span>
            </li>
            <li
              data-step-num="2"
              data-done={step > 2 ? "true" : "false"}
              data-current={step == 2 ? "true" : "false"}
              onClick={() => {
                if (step > 2) setStep(2);
              }}
            >
              <span>Metodo</span>
            </li>
            <li
              data-step-num="3"
              data-done={step > 3 ? "true" : "false"}
              data-current={step == 3 ? "true" : "false"}
              onClick={() => {
                if (step > 3) setStep(3);
              }}
            >
              <span>Posizione</span>
            </li>
          </ol>
        </div>
      )}
      <div>
        {step === 1 && (
          <DetectionStepTipologia
            formData={formData}
            action={action}
            onNextClick={handleNextClick}
          />
        )}
        {step === 2 && (
          <DetectionStepMetodo
            formData={formData}
            action={action}
            onBackClick={handleBackClick}
            onNextClick={handleNextClick}
          />
        )}
        {step === 3 && (
          <DetectionStepPosizione
            formData={formData}
            action={action}
            onBackClick={handleBackClick}
            onNextClick={handleNextClick}
          />
        )}
        {step === 4 && (
          <DetectionUI
            formData={formData}
            action={action}
            onBackClick={handleBackClick}
            onNextClick={handleNextClick}
          />
        )}
        {step === 5 && (
          <SaveDone
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
