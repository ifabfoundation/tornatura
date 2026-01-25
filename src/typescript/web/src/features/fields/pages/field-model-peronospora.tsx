import React from "react";
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
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );
  const [current, setCurrent] = React.useState<PeronosporaResponse | null>(null);
  const [forecast, setForecast] = React.useState<PeronosporaResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

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

  const renderDetail = (payload?: PeronosporaResponse | null) => {
    if (!payload?.detail) {
      return <div className="text-muted">Nessun dettaglio disponibile.</div>;
    }
    const entries = Object.entries(payload.detail).filter(
      ([, value]) => value !== null && value !== undefined && value !== "",
    );
    if (!entries.length) {
      return <div className="text-muted">Nessun dettaglio disponibile.</div>;
    }
    return (
      <div className="table-responsive">
        <table className="table table-sm">
          <tbody>
            {entries.map(([key, value]) => (
              <tr key={key}>
                <th style={{ width: "40%" }}>{key}</th>
                <td>{String(value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="container my-5">
      {error && <div className="alert alert-danger">{error}</div>}
      {loading && <div>Caricamento dati...</div>}
      {!loading && !error && (
        <div className="row">
          <div className="col-12 col-lg-6 mb-4">
            <div className="card">
              <div className="card-header">Rischio attuale</div>
              <div className="card-body">
                <div className="mb-2">
                  <strong>Provincia:</strong> {current?.province ?? "-"}
                </div>
                <div className="mb-2">
                  <strong>Data base:</strong> {current?.forecast_date ?? "-"}
                </div>
                {current?.target_week && (
                  <div className="mb-3">
                    <strong>Settimana target:</strong>{" "}
                    {current.target_week.start ?? "-"} → {current.target_week.end ?? "-"}
                  </div>
                )}
                {renderDetail(current)}
              </div>
            </div>
          </div>
          <div className="col-12 col-lg-6 mb-4">
            <div className="card">
              <div className="card-header">Previsione</div>
              <div className="card-body">
                <div className="mb-2">
                  <strong>Provincia:</strong> {forecast?.province ?? "-"}
                </div>
                <div className="mb-2">
                  <strong>Data base:</strong> {forecast?.forecast_date ?? "-"}
                </div>
                {forecast?.target_week && (
                  <div className="mb-3">
                    <strong>Settimana target:</strong>{" "}
                    {forecast.target_week.start ?? "-"} → {forecast.target_week.end ?? "-"}
                  </div>
                )}
                {renderDetail(forecast)}
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
