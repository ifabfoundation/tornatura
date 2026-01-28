import React, { Fragment } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { fieldsSelectors } from "../state/fields-slice";
import { AgriField, Point } from "@tornatura/coreapis";
import * as turf from "@turf/turf";
import { BollettinoResponse, fetchCimiceReport } from "../../../services/model-api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Container, Row, Col } from "react-bootstrap";
import { getFieldMapGeoJson } from "../../companies/pages/company-fields";
import Icon from "../../../components/Icon";

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

export function FieldModelCimice() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { companyId, fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );
  const [report, setReport] = React.useState<BollettinoResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const centroid = React.useMemo(() => getFieldCentroid(currentField), [currentField]);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Cimice asiatica", subtitle: "Bollettini" }));
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
    fetchCimiceReport(lat, lng)
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

  const title = "Report Cimice Asiatica";

  const geoJson = getFieldMapGeoJson(currentField);
  geoJson.properties = {
    fill: "%23FFFFFF",
    "fill-opacity": 0.4,
    stroke: "%23FFFFFF",
    "stroke-width": 3,
    "stroke-opacity": 1,
  };

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
  const processProvince = (provinceStr?: string) => {
    if (provinceStr === "bologna_ferrara") {
      return "Bologna e Ferrara";
    }
    return provinceStr ?? "-";
  };
  return (
    <Container fluid className="mb-5">
      <Row>
        <Col>
          {error && <div className="alert alert-danger">{error}</div>}
          {loading && <div>Caricamento report...</div>}
          {!loading && !error && (
            <Fragment>
              <section className="soft bg-white">
                <Row>
                  <Col md={6} xl={4} xxl={3}>
                    <div className="position-relative me-md-4 mb-2 mb-md-0">
                      <img
                        src={`https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/static/geojson(${JSON.stringify(
                          geoJson,
                        )})/auto/1024x1024?padding=160&access_token=${process.env.REACT_APP_MAPBOX_API_TOKEN}`}
                        alt="Field Map"
                        className="img-fluid rounded ratio-1-1"
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
                      <Col xl={12} className="mb-5">
                        <h1 className="">{title}</h1>
                      </Col>

                      <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2">
                        <div className="iiinfo-label font-s-label">Provincia</div>
                        <div className="iiinfo-value font-l-600">
                          {processProvince(report?.province)}
                        </div>
                      </Col>

                      <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2">
                        <div className="iiinfo-label font-s-label">Data del report</div>
                        <div className="iiinfo-value font-l-600">
                          {processDate(report?.report_date)}
                        </div>
                      </Col>

                      <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2">
                        <div className="iiinfo-label font-s-label">Aggiornato il</div>
                        <div className="iiinfo-value font-l-600">
                          {processDate(report?.last_modified)}
                        </div>
                      </Col>

                      <Col className="col-6 col-lg-4 col-xl-3 iiinfo-col mt-2 mb-2 opacity-05">
                        <div className="iiinfo-label font-s-label">File</div>
                        <div className="iiinfo-value font-s-600">{report?.filename ?? "-"}</div>
                      </Col>
                    </Row>
                  </Col>
                </Row>
              </section>

              <section className="soft bg-white">
                <div id="model-markdown">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {report?.content ?? "Nessun contenuto."}
                  </ReactMarkdown>
                </div>
              </section>
            </Fragment>
          )}
        </Col>
      </Row>
    </Container>
  );
}
