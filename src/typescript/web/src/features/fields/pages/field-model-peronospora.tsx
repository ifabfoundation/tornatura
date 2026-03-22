import React, { Fragment } from "react";
import { useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { fieldsSelectors } from "../state/fields-slice";
import { AgriField, Point } from "@tornatura/coreapis";
import * as turf from "@turf/turf";
import {
  fetchPeronosporaCurrent,
  fetchPeronosporaForecast,
  PeronosporaResponse,
} from "../../../services/model-api";
import { capitalize } from "../../../services/utils";
import { Container, Row, Col } from "react-bootstrap";
import { getFieldMapGeoJson } from "../../companies/pages/company-fields";

type ActiveDataType = "current" | "forecast";

function getFieldCentroid(field?: AgriField): { lat: number; lng: number } | null {
  if (!field?.map?.length) {
    return null;
  }
  const points: Point[] = field.map;
  if (points.length < 3) {
    return { lat: points[0].lat, lng: points[0].lng };
  }
  const coords = points.map((p) => [p.lng, p.lat]);
  const polygon = turf.polygon([coords]);
  const centroid = turf.centroid(polygon);
  return {
    lng: centroid.geometry.coordinates[0],
    lat: centroid.geometry.coordinates[1],
  };
}

export function FieldModelPeronospora() {
  const dispatch = useAppDispatch();
  const { fieldId } = useParams();
  const iframeRef = React.useRef<HTMLIFrameElement>(null);
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );
  const [current, setCurrent] = React.useState<PeronosporaResponse | null>(null);
  const [forecast, setForecast] = React.useState<PeronosporaResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [activeDataType, setActiveDataType] = React.useState<ActiveDataType>("current");

  const centroid = React.useMemo(() => getFieldCentroid(currentField), [currentField]);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Peronospora", subtitle: "Modello previsivo" }));
  }, []);

  React.useEffect(() => {
    if (!centroid) {
      setError("Posizione del campo non disponibile.");
      return;
    }

    const lat = Number(centroid.lat.toFixed(6));
    const lng = Number(centroid.lng.toFixed(6));

    setLoading(true);
    setError(null);
    Promise.all([fetchPeronosporaCurrent(lat, lng), fetchPeronosporaForecast(lat, lng)])
      .then(([currentData, forecastData]) => {
        setCurrent(currentData);
        setForecast(forecastData);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Errore di caricamento.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [centroid]);

  const syncIframeLeadButton = React.useCallback((nextType: ActiveDataType) => {
    const iframe = iframeRef.current;
    if (!iframe) {
      return;
    }

    iframe.contentWindow?.postMessage(
      {
        type: "peronospora:setLead",
        lead: nextType === "current" ? 0 : 1,
      },
      "*",
    );
  }, []);

  const handleDataTypeChange = React.useCallback(
    (nextType: ActiveDataType) => {
      setActiveDataType(nextType);
      syncIframeLeadButton(nextType);
    },
    [syncIframeLeadButton],
  );

  const getRiskColor = (riskLevel?: number): string => {
    switch (riskLevel) {
      case 0:
        return "9FDC71"; // Green
      case 1:
        return "FFFF00"; // Yellow
      case 2:
        return "FFA500"; // Orange
      case 3:
        return "FF0000"; // Red
      case 4:
          return "FF0000"; // Red
      default:
        return "CCCCCC"; // Grey for unknown
    }
  };

  const renderDetail = (payload?: PeronosporaResponse | null) => {
    if (!payload?.detail) {
      return <div className="text-muted">Nessun dettaglio disponibile.</div>;
    }
    const entries = Object.entries<any>(payload.detail).filter(
      ([, value]) => value !== null && value !== undefined && value !== "",
    );
    if (!entries.length) {
      return <div className="text-muted">Nessun dettaglio disponibile.</div>;
    }
    return (
      <table className="model-table my-0">
        <tbody>
          {entries.map(([key, value]) => (
            <tr key={key}>
              <th style={{ width: "40%" }}>
                <div className="font-s">{key}</div>
              </th>
              <td>
                <div className="font-s">{key === 'risk_meta' ? String(value.descrizione) : String(value)}</div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  let title = "Peronospora";

  let data = activeDataType === "current" ? current : forecast;

  const geoJson = getFieldMapGeoJson(currentField);
  const riskLevel = typeof data?.detail?.risk_level === "number" ? data.detail.risk_level : 0;
  const riskColor = getRiskColor(riskLevel);
  geoJson.properties = {
    fill: `%23${riskColor}`,
    "fill-opacity": 0.8,
    stroke: `%23${riskColor}`,
    "stroke-width": 3,
    "stroke-opacity": 1,
  };

  if (error) {
    return <div className="container my-5">{error}</div>
  } else if (current === null || forecast === null) {
    return <div className="container my-5">Caricamento dati...</div>;
  }

  const processDate = (dateStr?: string) => {
    if (!dateStr) return "-";
    // const input = "2025-10-01";
    // const input = "2026-01-26T07:24:30.177695";
    const date = new Date(dateStr);
    if (date) {
      return date.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "2-digit",
        year: "2-digit",
      });
    }
    return dateStr ?? "-";
  };
  const processProvincePeronospora = (provinceStr?: string) => {
    if (!provinceStr) {
      return "-";
    }

    return provinceStr
      .split("_")
      .filter(Boolean)
      .map((part) => capitalize(part))
      .join(" ");
  };

  console.log("Peronospora ---> ", data);
  return (
    <Container fluid className="mb-5">
      <Row>
        <Col>
          {error && <div className="alert alert-danger">{error}</div>}
          {loading && <div>Caricamento report...</div>}
          {!loading && !error && (
            <Fragment>
              <h1 className="my-3 mb-4">{title}</h1>
              <section className="soft bg-white">
                <Row>
                  <Col xl={12} className="mb-4 d-md-none">
                    <div style={{ backgroundColor: "#" + riskColor }} className="p-3 rounded">
                      <small>{`⬤  `}</small>
                      <span className="font-m-600 upper">
                        {String(data?.detail?.risk_label ?? "-")}
                      </span>
                    </div>
                  </Col>

                  <Col md={6} xl={4} xxl={3}>
                    <div className="position-relative me-md-4 mb-2 mb-md-0">
                      <img
                        src={`https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/static/geojson(${JSON.stringify(
                          geoJson,
                        )})/auto/1024x1024?padding=160&access_token=${process.env.REACT_APP_MAPBOX_API_TOKEN}`}
                        alt="Field Map"
                        className="img-fluid rounded ratio-1-1 d-block"
                      />
                      {/* <button
                        className="trnt_btn slim-y narrow-x secondary type-rounded position-absolute top-0 end-0 m-3 bg-white"
                        onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}/map`)}
                      >
                        <Icon iconName={"fullscreen"} color={"black"} />
                      </button> */}
                    </div>
                  </Col>
                  <Col>
                    <Row>
                      <Col xl={12} className="mb-4 d-none d-md-block">
                        <div style={{ backgroundColor: "#" + riskColor }} className="p-3 rounded">
                          <small>{`⬤  `}</small>
                          <span className="font-m-600 upper">
                            {String(data?.detail?.risk_label ?? "-")}
                          </span>
                        </div>
                      </Col>

                      <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2">
                        <div className="iiinfo-label font-s-label mb-1 color-grey">Provincia</div>
                        <div className="iiinfo-value font-l-600">
                          {processProvincePeronospora(data?.province)}
                        </div>
                      </Col>

                      <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2">
                        <div className="iiinfo-label font-s-label mb-1 color-grey">
                          Punteggio rischio
                        </div>
                        <div className="iiinfo-value font-l-600" style={{ whiteSpace: "nowrap" }}>
                          <small
                            style={{ color: "#" + riskColor }}
                            className="small"
                          >{`⬤  `}</small>
                          {`${data?.detail?.risk_score ?? "-"} / 5.0`}
                        </div>
                      </Col>

                      <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2">
                        <div className="iiinfo-label font-s-label mb-1 color-grey">
                          Data del report
                        </div>
                        <div className="iiinfo-value font-l-600">
                          {processDate(data?.forecast_date)}
                        </div>
                      </Col>

                      <Col xl={12} className="iiinfo-col d-flex align-items-center mt-3 mb-2">
                        <button
                          className={`trnt_btn outlined type-rounded m-0 me-2 ${activeDataType === "current" ? "" : "opacity-02"}`}
                          onClick={() => handleDataTypeChange("current")}
                        >
                          {/* Dati Correnti */}
                          <span className="font-s-600">
                            {current.target_week?.start ?? "-"} → {current.target_week?.end ?? "-"}
                          </span>
                        </button>
                        <button
                          className={`trnt_btn outlined type-rounded m-0 ${activeDataType === "forecast" ? "" : "opacity-02"}`}
                          onClick={() => handleDataTypeChange("forecast")}
                        >
                          {/* Previsioni */}
                          <span className="font-s-600">
                            {forecast.target_week?.start ?? "-"} →{" "}
                            {forecast.target_week?.end ?? "-"}
                          </span>
                        </button>
                      </Col>
                    </Row>
                  </Col>
                </Row>
              </section>

              <section className="soft bg-white">
                <iframe
                  ref={iframeRef}
                  src={`${process.env.REACT_APP_MODELAPIS_SERVER_URL}/v1/peronospora/risk/map`}
                  style={{
                    width: "100%",
                    height: "650px",
                    border: "none",
                    display: "block",
                  }}
                  scrolling="no"
                  onLoad={() => syncIframeLeadButton(activeDataType)}
                />
              </section>

              <section className="soft bg-white">
                <Row>
                  <Col>{renderDetail(data)}</Col>
                </Row>
              </section>
            </Fragment>
          )}
        </Col>
      </Row>
    </Container>
  );

  return (
    <div className="container my-5">
      {/* <div>
        <button
          className={`trnt_btn outlined slim-y type-rounded me-2 ${activeDataType === "current" ? "" : "opacity-05"}`}
          onClick={() => setActiveDataType("current")}
        >
          {/* Dati Correnti * /}
          {current.target_week?.start ?? "-"} → {current.target_week?.end ?? "-"}
        </button>
        <button
          className={`trnt_btn outlined slim-y type-rounded ${activeDataType === "forecast" ? "" : "opacity-05"}`}
          onClick={() => setActiveDataType("forecast")}
        >
          {/* Previsioni * /}
          {forecast.target_week?.start ?? "-"} → {forecast.target_week?.end ?? "-"}
        </button>
      </div> 
      */}
      {error && <div className="alert alert-danger">{error}</div>}
      {loading && <div>Caricamento dati...</div>}
      {!loading && !error && (
        <div className="row">
          <div className="col-12 col-lg-6 mb-4">
            <div className="card">
              <div className="card-header">Rischio attuale</div>
              <div className="card-body">
                <div className="mb-2">
                  <strong>Provincia:</strong> {data?.province ?? "-"}
                </div>
                <div className="mb-2">
                  <strong>Data base:</strong> {data?.forecast_date ?? "-"}
                </div>
                {data?.target_week && (
                  <div className="mb-3">
                    <strong>Settimana target:</strong> {data?.target_week?.start ?? "-"} →{" "}
                    {data?.target_week?.end ?? "-"}
                  </div>
                )}
                {renderDetail(data)}
              </div>
            </div>
          </div>
        </div>
      )}
      <iframe
        src={`${process.env.REACT_APP_MODELAPIS_SERVER_URL}/v1/peronospora/risk/map`}
        style={{
          width: "100%",
          height: "650px",
          border: "none",
          display: "block",
        }}
        scrolling="no"
      />
    </div>
  );
}

/* 
Anatomy of peronospora model data object
--------------------------------------------------------------------------------
detail: {
  NUTS_3: "bologna"
  bbch_code: 0
  forecast_base: "2026-01-27"
  lead_weeks: 1
  lw: 87
  plant_susceptibility: 0
  prec: 20.1
  rh: 90
  risk_label: "Nessun rischio rilevato"
  risk_level: 1
  risk_score: 1.47
  target_period_end: "2026-02-08"
  target_period_start: "2026-02-02"
  temp: 4.5
}, 
forecast_date: "2026-01-27"
location: {
  lat: 44.500127
  lng: 11.34239
}
province: "bologna"
target_week: {
  start: "2026-02-02"
  end: "2026-02-08" 
}
--------------------------------------------------------------------------------
*/
