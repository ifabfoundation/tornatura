import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment, use } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Card, Col, Container, Row } from "react-bootstrap";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import { GradientLineChart } from "../../../components/GradientLineChart";
import {
  detectionTypesActions,
  detectionTypesSelectors,
} from "../../detection-types/state/detection-types-slice";
import { Detection } from "@tornatura/coreapis";
import { dateToString } from "../../../services/utils";

function getColor(min: number, max: number, value: number): string {
  console.log("getColor", { min, max, value });
  const colors = ["#42C318", "#FFB290", "#FF4D4D", "#A10505"];
  const range = max - min;
  const segment = range / colors.length;
  const index = Math.min(colors.length - 1, Math.floor((value - min) / segment));
  return colors[index];
}

function getDetectionStats(detection: Detection) {
  // calculate stats for each detection
  let detectionStats = {
    pointsCount: 0,
    pointsSum: 0,
    pointsMin: Infinity,
    pointsMax: -Infinity,
    pointsAvg: 0,
  };
  detection.detectionData.points.forEach((point) => {
    const v = point.data.rangeValue;
    const isValidPoint = v !== undefined && v !== null;
    if (isValidPoint) {
      detectionStats.pointsCount++;
      detectionStats.pointsSum += v;
      detectionStats.pointsMin = Math.min(detectionStats.pointsMin, v);
      detectionStats.pointsMax = Math.max(detectionStats.pointsMax, v);
    }
  });
  detectionStats.pointsAvg =
    detectionStats.pointsCount > 0 ? detectionStats.pointsSum / detectionStats.pointsCount : 0;
  return detectionStats;
}

function formatDate(value: number | string | undefined | null) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }
  return date.toLocaleDateString("it-IT");
}

export function FieldDetections() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { fieldId, companyId } = useParams();
  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionbyFieldId(state, fieldId ?? "default")
  );
  const detectionTypes = useAppSelector((state) =>
    detectionTypesSelectors.selectDetectionTypesByField(state, fieldId ?? "default")
  );
  console.log("detectionTypes", detectionTypes);

  console.log("detections: ", detections);

  const detectionTypeById = React.useMemo(() => {
    return new Map(detectionTypes.map((item) => [item.id, item]));
  }, [detectionTypes]);
  console.log("detectionTypeById", detectionTypeById);

  const groupedDetections = React.useMemo(() => {
    const groups = new Map<
      string,
      {
        typology: string;
        method: string;
        detectionTypeId?: string;
        items: typeof detections;
      }
    >();

    detections.forEach((item) => {
      const detectionType = detectionTypeById.get(item.detectionTypeId);
      const typology = detectionType?.typology ?? "Senza tipologia";
      const method = detectionType?.method ?? "Senza metodo";
      const key = `${typology}__${method}`;
      if (!groups.has(key)) {
        groups.set(key, {
          typology,
          method,
          detectionTypeId: detectionType?.id ?? item.detectionTypeId,
          items: [],
        });
      }
      groups.get(key)?.items.push(item);
    });

    return Array.from(groups.values()).sort((a, b) => {
      const typologyCompare = a.typology.localeCompare(b.typology);
      if (typologyCompare !== 0) {
        return typologyCompare;
      }
      return a.method.localeCompare(b.method);
    });
  }, [detections, detectionTypeById]);
  // -------------------------
  // -------------------------
  console.log("groupedDetections", groupedDetections);
  // -------------------------
  // -------------------------

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Tutti i rilevamenti", subtitle: "Subtitle" }));
  }, []);

  React.useEffect(() => {
    if (companyId && fieldId) {
      dispatch(detectionTypesActions.fetchDetectionTypesAction({ orgId: companyId, fieldId }));
    }
  }, [companyId, fieldId, dispatch]);

  return (
    <Fragment>
      <Container>
        <Row>
          <Col>
            <div className="cardlet">
              <div className="cardlet-header">RILEVAMENTI</div>
              <div className="cardlet-content">{detections.length}</div>
            </div>
          </Col>
          <Col>
            <a
              className="cardlet-button"
              onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`)}
            >
              <span className="d-md-none">+</span>
              <span className="d-none d-md-inline">+ Nuovo Rilevamento</span>
            </a>
          </Col>
        </Row>
        <Row className="mt-4">
          {groupedDetections.length === 0 && (
            <Col>
              <div className="text-muted">Nessun rilevamento disponibile.</div>
            </Col>
          )}
          {groupedDetections.map((group) => {
            const groupStats = {
              groupMin: Infinity,
              groupMax: -Infinity,
            };
            group.items.forEach((detection) => {
              const ds = getDetectionStats(detection);
              groupStats.groupMin = Math.min(groupStats.groupMin, ds.pointsMin);
              groupStats.groupMax = Math.max(groupStats.groupMax, ds.pointsMax);
              // console.log("ds", ds);
            });
            console.log("groupStats", groupStats);

            var graphData = group.items
              .map((detection, index) => {
                return {
                  x: detection.detectionTime,
                  // x: index,
                  y: getDetectionStats(detection).pointsAvg,
                  color: getColor(
                    groupStats.groupMin,
                    groupStats.groupMax,
                    getDetectionStats(detection).pointsAvg
                  ),
                };
              })
              .sort((a, b) => a.x - b.x);

            // -------------------------
            // -------------------------
            // -------------------------
            // -------------------------
            console.log("graphData", graphData);

            const lastDate = group.items
              .map((e) => e.detectionTime)
              .sort((a, b) => b - a)
              .reverse()[0];
            const lastDateString = dateToString(lastDate, false);

            return (
              <Col key={`${group.typology}-${group.method}`} xl={6}>
                <div className="detection-card">
                  <header>
                    <div className="label py-1">Rilevamenti di</div>
                    <div className="value">{`${group.typology}  ›  ${group.method}`}</div>
                  </header>

                  <div className="small-texts d-flex justify-content-between align-items-center mt-4 mb-2">
                    <div className="label">{`${group.items.length} RILEVAMENTI`}</div>
                    <div className="label">{`AGGIORNATO IL ${lastDateString}`}</div>
                  </div>

                  <GradientLineChart
                    height={100}
                    padding={{ top: 0, bottom: 0, left: 40, right: 40 }}
                    strokeWidth={20}
                    dotSize={14}
                    data={graphData}
                  />

                  <div className="mt-3 pt-1">
                    <button
                      className="trnt_btn accent wide"
                      data-type="round"
                      onClick={() =>
                        navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`, {
                          state: { typology: group.typology, method: group.method },
                        })
                      }
                    >
                      + Rilevamento {group.typology}
                    </button>
                  </div>

                  {/*  
                  {group.items
                    .slice()
                    .sort((a, b) => (b.detectionTime ?? 0) - (a.detectionTime ?? 0))
                    .map((item) => {
                      const ds = getDetectionStats(item);
                      return (
                        <div key={item.id} className="d-flex justify-content-between pt-1">
                          <div className="label">
                            Rilevamento del {formatDate(item.detectionTime)}
                          </div>{" "}
                          <div className="label tabular-nums">Avg: {ds.pointsAvg.toFixed(2)}</div>
                        </div>
                      );
                    })
                  }
                  */}
                </div>
              </Col>
            );
          })}
        </Row>
      </Container>
    </Fragment>
  );
}
