import React from "react";
import { useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { fieldsSelectors } from "../state/fields-slice";
import { AgriField, Point } from "@tornatura/coreapis";
import * as turf from "@turf/turf";
import { BollettinoResponse, fetchFlavescenzaReport } from "../../../services/model-api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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

export function FieldModelFlavescenza() {
  const dispatch = useAppDispatch();
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );
  const [report, setReport] = React.useState<BollettinoResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const centroid = React.useMemo(() => getFieldCentroid(currentField), [currentField]);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Flavescenza dorata", subtitle: "Bollettini" }));
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
    fetchFlavescenzaReport(lat, lng)
      .then((data) => {
        setReport(data);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Errore di caricamento.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [centroid]);

  return (
    <div className="container my-5">
      {error && <div className="alert alert-danger">{error}</div>}
      {loading && <div>Caricamento report...</div>}
      {!loading && !error && (
        <div className="card">
          <div className="card-header">Report Flavescenza Dorata</div>
          <div className="card-body">
            <div className="mb-2">
              <strong>Provincia:</strong> {report?.province ?? "-"}
            </div>
            <div className="mb-2">
              <strong>Data report:</strong> {report?.report_date ?? "-"}
            </div>
            <div className="mb-2">
              <strong>Ultimo aggiornamento:</strong> {report?.last_modified ?? "-"}
            </div>
            <div className="mb-3">
              <strong>File:</strong> {report?.filename ?? "-"}
            </div>
            <div className="model-markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {report?.content ?? "Nessun contenuto."}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
