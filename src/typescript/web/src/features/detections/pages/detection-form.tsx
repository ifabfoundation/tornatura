import React, { Fragment } from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import { DetectionMutationPayload, FilesApi } from "@tornatura/coreapis";
import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import { detectionsActions } from "../state/detections-slice";
import { FileWithPath, useDropzone } from "react-dropzone";
import { getCoreApiConfiguration } from "../../../services/utils";
import { fieldsSelectors } from "../../fields/state/fields-slice";
import { SearchBox } from "@mapbox/search-js-react";
import mapboxgl, { LngLatLike, Marker } from "mapbox-gl";
import { Point } from "@tornatura/coreapis";
import * as turf from "@turf/turf";
import { ModalConfirm } from "../../../components/ModalConfirm";
import { Accordion, AccordionItem } from "../../../components/Accordion";
import CozyButton from "../../../components/CozyButton";
import Icon from "../../../components/Icon";

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
      <h4 className="mt-4 mb-4">Dati del rilevamento: Malattia</h4>
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
        <div
          {...getRootProps()}
          style={{ backgroundColor: "white", height: "60px", textAlign: "center", margin: "auto" }}
        >
          <input {...getInputProps()} accept=".png, .jpeg, .jpg" />
          {isDragActive ? (
            <p className="mt-4">Trascina i file qui...</p>
          ) : (
            <p className="mt-4">
              Trascina e rilascia alcuni file qui, oppure fai clic per selezionarli
            </p>
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
      <h4 className="mt-4 mb-4">Dati del rilevamento: Parassita</h4>
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
      <h4 className="mt-4 mb-4">Dati del rilevamento: Insetti</h4>
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
      <h4 className="mt-4 mb-4">Dati del rilevamento: Insetti</h4>
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

  React.useEffect(() => {
    if (mapContainerRef.current && currentField) {
      mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_API_TOKEN;

      let data: number[][] = [];
      currentField.map.forEach((point: Point) => {
        data.push([point.lng, point.lat]);
      });
      if (data.length <= 2) {
        console.log("••• not enough points to draw the field shape", data);
        return;
      }

      let centroid: LngLatLike = [12.5736108, 41.29246];
      let fieldShapeBbox: any;
      if (data.length > 2) {
        const polygon = turf.polygon([data]);
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
                coordinates: [data],
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

        mapRef.current.on("click", function (e: any) {
          const { lng, lat } = e.lngLat;
          if (markerRef.current) {
            markerRef.current.setLngLat([lng, lat]);
          } else {
            markerRef.current = new mapboxgl.Marker().setLngLat([lng, lat]).addTo(mapRef.current!);
          }
          const point: Point = {
            lat: lat,
            lng: lng,
          };
          onMarkerChange(point);
        });

        setMapLoaded(true);
      });

      return () => {
        mapRef.current.remove();
      };
    }
  }, [mapContainerRef, currentField]);

  return (
    <div>
      {mapLoaded && (
        <div className="mapbox-searchbox-wrapper field-map-mapbox-searchbox-wrapper">
          {/*@ts-ignore*/}
          <SearchBox
            options={{
              language: "it",
              country: "IT",
            }}
            accessToken={process.env.REACT_APP_MAPBOX_API_TOKEN ?? ""}
            map={mapRef.current}
            mapboxgl={mapboxgl}
            value={inputValue}
            onChange={(d) => {
              setInputValue(d);
            }}
            marker
          />
        </div>
      )}
      <div ref={mapContainerRef} id="map" className="map-detection-form"></div>
    </div>
  );
}

const categorie: any = {
  fungi: {
    name: "Fungo e peronospora",
    items: {
      peronospora: {
        name: "Peronospora",
      },
      oter_fungi: {
        name: null,
      },
    },
  },
  bacteria: {
    name: "Batterio",
    items: {
      flavescenza: {
        name: "Flavescenza",
      },
      oter_bacteria: {
        name: null,
      },
    },
  },
  insect: {
    name: "Insetto",
    items: {
      scafoideo: {
        name: "Scafoideo",
      },
      cimice: {
        name: "Cimice",
      },
      diabrotica: {
        name: "Diabrotica",
      },
      oter_insect: {
        name: null,
      },
    },
  },
};

const methods: any = {
  peronospora: ["Foglia", "Frutto", "Tutta la pianta"],
  oter_fungi: ["Foglia", "Frutto", "Tutta la pianta"],
  flavescenza: ["Foglia", "Frutto", "Tutta la pianta"],
  oter_bacteria: ["Foglia", "Frutto", "Tutta la pianta"],
  cimice: ["Trappola", "Campo (Frappage – Visivo)"],
  scafoideo: ["Foglie basali/polloni", "Chioma"],
  diabrotica: [],
  oter_insect: ["Trappola", "Altro"],
}


function AccordionTest() {
  let items: AccordionItem[] = [];
  items = [
    {
      id: "one",
      title: "Fungo e peronospora",
      content: (
        <Fragment>
          <CozyButton iconName={"spots"} text={"Peronospora"} onClick={() => {}} />
          <CozyButton iconName={"spots"} text={"Altro fungo"} onClick={() => {}} />
        </Fragment>
      ),
      icon: "spots",
    },
    {
      id: "two",
      title: "Batterio",
      content: (
        <Fragment>
          <CozyButton iconName={"bacteria"} text={"Nome della malattia"} onClick={() => {}} />
          <CozyButton iconName={"bacteria"} text={"Altro batterio"} onClick={() => {}} />
        </Fragment>
      ),
      icon: "bacteria",
    },
    {
      id: "three",
      title: "Insetto",
      content: (
        <Fragment>
          <CozyButton iconName={"bug"} text={"Scafoideo"} onClick={() => {}} />
          <CozyButton iconName={"bug"} text={"Cimice"} onClick={() => {}} />
          <CozyButton iconName={"bug"} text={"Diabrotica"} onClick={() => {}} />
          <CozyButton iconName={"bug"} text={"Altro insetto"} onClick={() => {}} />
        </Fragment>
      ),
      icon: "bug",
    },
  ];
  return (
    <div style={{ margin: "auto", maxWidth: "600px", marginTop: "80px", marginBottom: "80px" }}>
      <Accordion items={items} />
    </div>
  );
}

interface AccordionTipologiaProps {
  onSelect: (selection: string) => void
}

function AccordionTipologia({onSelect}: AccordionTipologiaProps) {
  let items: AccordionItem[] = [];
  items = Object.keys(categorie).map((key: string, index: number) => {
    return {
      id: index.toString(),
      title: categorie[key].name,
      content: (
        <Fragment>
          {Object.keys(categorie[key].items).map((itemKey: string, itemIndex) => (
            <CozyButton key={itemIndex} iconName={"bug"} text={categorie[key].items[itemKey].name || "Altro"} onClick={() => onSelect(itemKey)} />
          ))}
        </Fragment>
      ),
      icon: "spots",
    }
  })
  return (
    <div style={{ margin: "auto", maxWidth: "600px", marginTop: "80px", marginBottom: "80px" }}>
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
      });
    }
  }, []);

  const handleSourceChange = (value: string) => {
    setSource(value);
  };

  const handleMarkerChange = async (point: Point) => {
    setMarkerPosition(point);
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
      <h4 className="mt-4">La tua posizione</h4>
      <div className="input-row">
        <label>
          <select name="source" onChange={(e) => handleSourceChange(e.target.value)} value={source}>
            <option value="current">Usa posizione corrente</option>
            <option value="map">Seleziona un punto sulla mappa</option>
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
      type: value
    })
  }

  return (
    <Fragment>
      <AccordionTipologia onSelect={handleOnSelectClick}/>
    </Fragment>
  );
}

function DetectionStepMetodo({ formData, onNextClick }: DetectionProps) {
  const handleOnSelectClick = (value: string) => {
    onNextClick({
      method: value
    })
  }

  return (
    <Fragment>
      {methods[formData.type].map((itemKey: string, itemIndex: number) => (
        <CozyButton key={itemIndex} iconName={"bug"} text={itemKey} onClick={() => handleOnSelectClick(itemKey)} />
      ))}
    </Fragment>
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
    } else if (step === 2) {
      const payload = {
        ...formData,
        method: data.method
      };
      setFormData(payload);
      setStep(step + 1);
      setAction("Avanti");
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
          <span>Tipologia</span>
        </li>
        <li
          data-step-num="2"
          data-done={step > 2 ? "true" : "false"}
          data-current={step == 2 ? "true" : "false"}
        >
          <span>Metodo</span>
        </li>
        <li
          data-step-num="3"
          data-done={step > 3 ? "true" : "false"}
          data-current={step == 3 ? "true" : "false"}
        >
          <span>Posizione</span>
        </li>
      </ol>
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
      </div>
    </Fragment>
  );
}
