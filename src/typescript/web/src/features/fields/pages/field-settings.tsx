import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import mapboxgl, { LngLatLike } from "mapbox-gl";
import { SearchBox } from "@mapbox/search-js-react";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Col, Container, Row } from "react-bootstrap";
import { fieldsActions, fieldsSelectors } from "../state/fields-slice";
import _ from "lodash";
import { AgriField, AgriFieldMutationPayload, Point } from "@tornatura/coreapis";
import * as turf from "@turf/turf";
import { ModalConfirm } from "../../../components/ModalConfirm";


interface FieldFormProps {
  formData: AgriField;
}

function FieldFormStep1({ formData }: FieldFormProps) {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  
  const [modalOpen, setModalOpen] = React.useState(false);
  const [modal, setModal] = React.useState<any>({});

  const formik = useFormik({
    initialValues: {
      name: "",
      description: "",
      harvest: "",
      area: 0,
    },
    validationSchema: Yup.object({
      name: Yup.string().required("Campo necessario"),
      harvest: Yup.string().required("Campo necessario"),
      area: Yup.number().required("Campo necessario"),
    }),
    onSubmit: (values, { setSubmitting }) => {
      const payload: AgriFieldMutationPayload = {
        name: values.name,
        description: values.description,
        harvest: values.harvest,
        area: values.area,
        map: formData.map,
      };
      dispatch(fieldsActions.updateFieldAction({ orgId: formData.orgId, fieldId: formData.id, body: payload }));
      setSubmitting(false);
    },
  });

  React.useEffect(() => {
    formik.setValues({
      name: formData.name,
      description: formData.description,
      harvest: formData.harvest,
      area: formData.area,
    });
  }, [formData]);

  const handleFieldDelete = async () => {
    setModal({
      component: ModalConfirm,
      componentProps: {
        title: "Eliminazione campo",
        content: "Sei sicuro di voler eliminare questo campo? Questa azione non può essere annullata.",
        action: "Elimina",
        handleCancel: () => setModalOpen(false),
        handleConfirm: () => {
          dispatch(fieldsActions.deleteFieldAction({ orgId: formData.orgId, fieldId: formData.id}));
          setModalOpen(false);
          navigate(`/companies/${formData.orgId}`, { replace: true });
        },
      },
    });
    setModalOpen(true);
  }


  return (
    <Fragment>
      {modalOpen && <modal.component {...modal.componentProps} />}
      <form onSubmit={formik.handleSubmit} autoComplete="off" className="mt-5">
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
          <label>
            Area in ettari
            <input
              id="area"
              name="area"
              type="number"
              min={1}
              placeholder="Area del campo in ettari"
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              value={formik.values.area}
            />
          </label>
          {formik.touched.area && formik.errors.area ? (
            <div className="error">{formik.errors.area}</div>
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
          <input type="submit" className="primary" value="Salva modifiche" />
          <button className="trnt_btn info" onClick={handleFieldDelete}>Elimina campo</button>
        </div>
      </form>
    </Fragment>
  );
}

const FieldFormStep2 = ({ formData }: FieldFormProps) => {
  const dispatch = useAppDispatch();
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default")
  );
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  const [mapLoaded, setMapLoaded] = React.useState(false);
  const [inputValue, setInputValue] = React.useState("");
  const [map, setMap] = React.useState<Point[]>([]);


  React.useEffect(() => {
    if (mapContainerRef.current && currentField) {
      mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_API_TOKEN;

      let data: number[][] = [];
      currentField.map.forEach((point: Point) => {
        data.push([point.lng, point.lat]);
      });

      let centroid: LngLatLike = [12.5736108, 41.29246];
      if (data.length > 2) {
        const polygon = turf.polygon([data]);
        const result = turf.centroid(polygon);
        centroid = [result.geometry.coordinates[0], result.geometry.coordinates[1]];
      }

      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/satellite-streets-v12",
        center: centroid,
        zoom: 14,
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
        const source = mapRef.current.getSource("maine");
        if (!source) {
          mapRef.current.addSource("maine", {
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
          id: "maine",
          type: "fill",
          source: "maine",
          layout: {},
          paint: {
            "fill-color": "#c4c920",
            "fill-opacity": 0.7,
          },
        });
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
          setMap(points);
        } else {
          setMap(points);
        }
        console.log("Updated map points: ", points);
      }

      return () => {
        mapRef.current.remove();
      };
    }
  }, [mapContainerRef, currentField]);
  

  const handleSaveMap = async () => {
    if (map && map.length !== 0) {
      console.log("Map data to save: ", map);
      const payload: AgriFieldMutationPayload = {
        name: formData.name,
        description: formData.description,
        harvest: formData.harvest,
        area: formData.area,
        map: map,
      };
      await dispatch(fieldsActions.updateFieldAction({ orgId: formData.orgId, fieldId: formData.id, body: payload }));
    }
  }


  return (
    <>
      {mapLoaded && (
        <div className="mapbox-searchbox-wrapper mt-5">
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
      <div className="buttons-wrapper">
        <button className="trnt_btn primary" onClick={handleSaveMap}>Salva modifiche</button>
      </div>
    </>
  );
};


export function FieldSettings() {
  const dispatch = useAppDispatch();
  // const navigate = useNavigate();
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default")
  );

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Impostazioni", subtitle: "Subtitle" }));
  }, []);

  return (
    <Fragment>
      <Container>
        <Row className="mt-2">
          <Col xl={6}>
            <h4>Dettaglio del campo</h4>
            <hr />
            <FieldFormStep1 formData={currentField} />
          </Col>
          <Col xl={6}>
            <h4>Mappa del campo</h4>
            <hr />
            <FieldFormStep2 formData={currentField} />
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
}
