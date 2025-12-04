import React from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import mapboxgl from "mapbox-gl";
import { SearchBox } from "@mapbox/search-js-react";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import { AgriFieldMutationPayload, Point } from "@tornatura/coreapis";
import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { fieldsActions } from "../../fields/state/fields-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import * as turf from "@turf/turf";
import { Col, Row } from "react-bootstrap";

interface FieldProps {
  formData: AgriFieldMutationPayload;
  action: string;
  onBackClick?: () => Promise<void>;
  onNextClick: (data: any) => Promise<void>;
}


const calcArea = (points: Point[]) => {
  const coords: number[][] = [];
  points.forEach((p) => coords.push([p.lng, p.lat]));
  var polygon = turf.polygon([coords]);
  var areaSqm = turf.area(polygon);
  var areaHe = areaSqm / 10000; // Convert to hectares
  return parseFloat(areaHe.toFixed(2));
};

function FieldFormStep2({ formData, action, onNextClick, onBackClick }: FieldProps) {
  const formik = useFormik({
    initialValues: {
      name: "",
      description: "",
      harvest: "",
      area: 0.0,
      areafrom: "mappa",
      plants: 0,
    },
    validationSchema: Yup.object({
      name: Yup.string().required("Campo necessario"),
      harvest: Yup.string().required("Campo necessario"),
      area: Yup.number().typeError("Il valore inserito non è positivo").min(0, "Il valore deve essere positivo").required("Campo necessario"),
    }),
    onSubmit: (values, { setSubmitting }) => {
      if (values.areafrom === "mappa") {
        values.area = calcArea(formData.map);
      }
      onNextClick(values);
      setSubmitting(false);
    },
  });

  React.useEffect(() => {
    formik.setValues({
      name: formData.name,
      description: formData.description,
      harvest: formData.harvest,
      area: formData.area,
      areafrom: "mappa",
      plants: formData.plants || 0,
    });
  }, [formData]);



  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="input-row">
        <label>
          Nome
          <input
            id="name"
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
      <div className="input-row">
        <label>
          Coltura
          <input
            id="harvest"
            name="harvest"
            type="text"
            placeholder="Coltura del campo"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.harvest}
          />
        </label>
        {formik.touched.harvest && formik.errors.harvest ? (
          <div className="error">{formik.errors.harvest}</div>
        ) : null}
      </div>
      <div className="input-row">
        Dimensione del campo 
        <Row>
          <Col>
            <input type="radio" name="areafrom" value="mappa" onChange={formik.handleChange} checked={formik.values.areafrom === "mappa"}/>
            Calcola dalla mappa
          </Col>
          <Col>
            <input type="radio" name="areafrom" value="manuale" onChange={formik.handleChange} checked={formik.values.areafrom === "manuale"}/>
            manuale
          </Col>
          <Col>
            <label>
              Dimensione in ettari
              <input
                id="area"
                name="area"
                /*type="number"
                step={0.01}*/
                min={0}
                placeholder="Area del campo in ettari"
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                value={formik.values.areafrom === "manuale" ? formik.values.area : calcArea(formData.map)}
              />
            </label>
          </Col>
        </Row>
        {formik.touched.area && formik.errors.area ? (
          <div className="error">{formik.errors.area}</div>
        ) : null}
      </div>
      <div className="input-row">
        <label>
          Numero di piante
          <input
            id="plants"
            name="plants"
            type="number"
            min={0}
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
      <div className="input-row">
        <label>
          Descrizione
          <textarea
            id="description"
            name="description"
            placeholder="Descrizione del campo"
            rows={15}
            cols={50}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.description}
          ></textarea>
        </label>
        {formik.touched.description && formik.errors.description ? (
          <div className="error">{formik.errors.description}</div>
        ) : null}
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

const FieldFormStep1 = ({ action, onNextClick }: FieldProps) => {
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  const [mapLoaded, setMapLoaded] = React.useState(false);
  const [inputValue, setInputValue] = React.useState("");
  const [map, setMap] = React.useState<Point[]>([]);
  const [currentPosition, setCurrentPosition] = React.useState<Point>();

  const calcArea = (points: Point[]) => {
    const coords: number[][] = [];
    points.forEach((p) => coords.push([p.lng, p.lat]));
    console.log("coords", coords);
    var polygon = turf.polygon([coords]);
    var areaSqm = turf.area(polygon);
    var areaHe = areaSqm / 10000; // Convert to hectares
    console.log("points", points);
    console.log("area in sqm", areaSqm);
    console.log("area in hectares", areaHe);
  };

  React.useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        setCurrentPosition({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
      });
    }
  }, []);

  React.useEffect(() => {
    if (mapContainerRef.current) {
      mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_API_TOKEN;

      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/satellite-streets-v12",
        center: currentPosition
          ? [currentPosition.lng, currentPosition.lat]
          : [12.5736108, 41.29246],
        zoom: 9,
      });

      const draw = new MapboxDraw({
        displayControlsDefault: false,
        controls: {
          polygon: true,
          trash: true,
        },
        defaultMode: "draw_polygon",
      });

      mapRef.current.on("load", () => {
        setMapLoaded(true);
      });

      mapRef.current.addControl(draw);
      mapRef.current.on("draw.create", updateArea);
      mapRef.current.on("draw.delete", updateArea);
      mapRef.current.on("draw.update", updateArea);

      function updateArea() {
        const data = draw.getAll();
        const points: Point[] = [];
        if (data.features.length > 0) {
          // @ts-ignore
          data.features[0].geometry.coordinates[0].forEach((point: number[]) => {
            points.push({
              lng: point[0],
              lat: point[1],
            });
          });
          calcArea(points);
          setMap(points);
        } else {
          setMap(points);
        }
      }

      return () => {
        if (mapRef.current) {
          mapRef.current.remove();
        }
      };
    }
  }, [mapContainerRef, currentPosition]);

  return (
    <>
      <h4>Disegna la mappa del campo</h4>
      <hr />
      {mapLoaded && (
        <div className="mapbox-searchbox-wrapper">
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
      <div ref={mapContainerRef} id="map" style={{ height: "500px" }}></div>
      <hr />
      <div className="buttons-wrapper mt-5">
        <button
          className="trnt_btn primary"
          onClick={() => {
            onNextClick(map);
          }}
          disabled={map.length === 0}
        >
          {action}
        </button>
      </div>
    </>
  );
};

export function CompanyFieldForm() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { companyId } = useParams();
  const currentCompany = useAppSelector((state) =>
    companiesSelectors.selectCompanybyId(state, companyId ?? "default")
  );
  const [step, setStep] = React.useState(1);
  const [action, setAction] = React.useState("Avanti");
  const [formData, setFormData] = React.useState<AgriFieldMutationPayload>({
    name: "",
    description: "",
    area: 0,
    harvest: "",
    plants: 0,
    map: [],
  });

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Nuovo campo", subtitle: "Subtitle" }));
  }, []);

  const createFieldAction = async (payload: AgriFieldMutationPayload) => {
    if (currentCompany) {
      dispatch(fieldsActions.addNewFieldAction({ orgId: currentCompany.orgId, body: payload }))
        .then(unwrapResult)
        .then((_) => {
          navigate(`/companies/${companyId}/fields`, { replace: true });
        })
        .catch((reason) => {
          console.error("Error creating field with reason: ", reason);
        });
    }
  };

  const handleNextClick = async (data: any) => {
    if (step === 2) {
      const payload = {
        ...formData,
        name: data.name,
        description: data.description,
        area: data.area,
        harvest: data.harvest,
        plants: data.plants,
      };
      setFormData(payload);
      createFieldAction(payload);
    } else if (step === 1) {
      const payload = {
        ...formData,
        map: data,
      };
      setFormData(payload);
      setAction("Aggiungi campo");
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
    <div className="form-wrapper">
      {step === 1 && (
        <FieldFormStep1 formData={formData} action={action} onNextClick={handleNextClick} />
      )}
      {step === 2 && (
        <FieldFormStep2
          formData={formData}
          action={action}
          onBackClick={handleBackClick}
          onNextClick={handleNextClick}
        />
      )}
    </div>
  );
}
