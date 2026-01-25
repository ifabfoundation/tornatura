import React from "react";
import { Detection } from "@tornatura/coreapis";
import { useNavigate } from "react-router-dom";
import { useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import {
  observationTypesActions,
  observationTypesSelectors,
} from "../../observation-types/state/observation-types-slice";
import { detectionTypesActions, detectionTypesSelectors } from "../state/detection-types-slice";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import { Container, Row, Col } from "react-bootstrap";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { fieldsSelectors } from "../../fields/state/fields-slice";
import { FieldMap } from "../../../components/FieldMap";

import { GradientLineChart } from "../../../components/GradientLineChart";
import Icon from "../../../components/Icon";

interface HorizontalPhotoStackProps {
  photos: string[];
}

function HorizontalPhotoStack({ photos }: HorizontalPhotoStackProps) {
  const maxPhotosToShow = 5;
  return (
    <div className="d-flex flex-row">
      {photos.slice(0, maxPhotosToShow).map((photoUrl, index) => (
        <div
          key={index}
          className="me-2"
          style={{
            width: "80px",
            height: "80px",
            backgroundImage: `url(${photoUrl})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            borderRadius: "8px",
            boxShadow: "0 2px 6px rgba(0, 0, 0, 0.2)",
          }}
        ></div>
      ))}
      {photos.length > maxPhotosToShow && (
        <div
          className="d-flex align-items-center justify-content-center"
          style={{
            width: "80px",
            height: "80px",
            borderRadius: "8px",
            backgroundColor: "#f0f0f0",
            boxShadow: "0 2px 6px rgba(0, 0, 0, 0.2)",
            fontSize: "16px",
            color: "#555",
          }}
        >
          +{photos.length - maxPhotosToShow}
        </div>
      )}
    </div>
  );
}

function getDetectionStats(detection: Detection) {
  // calculate stats for each detection
  // FOR DATA OF TYPE "RANGE"
  let detectionStats = {
    pointsCount: 0,
    pointsSum: 0,
    pointsMin: Infinity,
    pointsMax: -Infinity,
    pointsAvg: 0,
    infectedPercent: 0,
    infectedPercentStr: "00%",
    intensityAvg: 0,
    intensityAvgStr: "00%",
    diseaseIndex: 0,
    diseaseIndexStr: "00%",
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

  // detection = {
  //   agrifieldId: "685a5d40f2de7db5c17f177c",
  //   creationTime: 1769275022455,
  //   detectionData: {
  //     bbch: "21",
  //     notes: "Lorem ipsum…",
  //     photos: ["https://placehold.co/600x400", "https://placehold.co/600x400"],
  //     points: [{
  //       data: {
  //         counters: [],
  //         rangeValue: 5,
  //       },
  //       position: {lng: 12.76965574474565, lat: 41.68182819504833}
  //     }],
  //   },
  //   detectionTime: 1769275000458,
  //   detectionTypeId: "6974fd8c388f508a98827411",
  //   id: "6974fe8e388f508a98827415",
  //   lastUpdateTime: 1769275022455,
  // }

  // calcolato qui sopra:
  // detectionStats.pointsCount
  // detectionStats.pointsSum
  // detectionStats.pointsMin
  // detectionStats.pointsMax
  // detectionStats.pointsAvg

  // pianteColpite
  const infectedCount = detection.detectionData.points.filter(
    (entry: any) => entry.data.rangeValue > 0,
  ).length;
  const infectedPercent = infectedCount / detection.detectionData.points.length;
  detectionStats.infectedPercent = infectedPercent;
  detectionStats.infectedPercentStr = `${(infectedPercent * 100).toFixed(1)}%`;

  const tonyHelpGettingRangeMaxFromObservationType = 5; // TO REPLACE WITH REAL VALUE

  // intensitaMedia
  const totalScores = detection.detectionData.points.reduce((acc: number, entry: any) => {
    const normalized = entry.data.rangeValue / tonyHelpGettingRangeMaxFromObservationType;
    return acc + normalized;
  }, 0);
  const avgScore = totalScores / detection.detectionData.points.length;
  const percent = avgScore;
  detectionStats.intensityAvg = percent;
  detectionStats.intensityAvgStr = `${(percent * 100).toFixed(1)}%`;

  detectionStats.diseaseIndex = detectionStats.infectedPercent * detectionStats.intensityAvg;
  detectionStats.diseaseIndexStr = `${(detectionStats.diseaseIndex * 100).toFixed(1)}%`;

  return detectionStats;
}

export function DetectionTypeDetail() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [tableIsOpen, setTableIsOpen] = React.useState<boolean>(false);
  const { companyId, fieldId, typeId } = useParams();

  const detectionType = useAppSelector((state) =>
    detectionTypesSelectors.selectDetectionTypeById(state, typeId ?? "default"),
  );

  const observationType = useAppSelector((state) =>
    observationTypesSelectors.selectObservationTypeById(
      state,
      detectionType?.observationTypeId ?? "default",
    ),
  );

  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionByTypeId(state, typeId ?? "default"),
  );
  console.log("detections", detections);

  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Focus Rilevamento", subtitle: "Subtitle" }));
  }, []);

  React.useEffect(() => {
    if (companyId && fieldId) {
      dispatch(detectionTypesActions.fetchDetectionTypesAction({ orgId: companyId, fieldId }));
    }
    dispatch(observationTypesActions.fetchObservationTypesAction({}));
  }, [companyId, fieldId]);

  const notes = [];
  detections.forEach((detection) => {
    // console.log("detection", detection);
    // @ts-ignore
    if (detection.detectionData.notes && detection.detectionData.notes != "") {
      // @ts-ignore
      notes.push(detection.detectionData.notes);
    }
  });
  const photos: string[] = [];
  detections.forEach((detection) => {
    // @ts-ignore
    if (detection.detectionData.photos && detection.detectionData.photos.length > 0) {
      // @ts-ignore
      detection.detectionData.photos.forEach((photo) => {
        photos.push(photo);
      });
    }
  });

  function handleDeleteClick(detection: Detection) {
    console.log("Delete clicked for", detection);
    // ... to be implemented
  }
  function handleHighlightDetection(detection: Detection) {
    console.log("Highlight clicked for", detection);
    // ... to be implemented
  }

  function DetectionsTable() {
    const tableOptions: TableOptions = {
      defaultSortCol: "date",
      defaultSortDir: "desc",
    };

    const tableColumns: TableColumn[] = [
      {
        headerText: "Data",
        id: "detectionTime",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "BBCH",
        id: "bbch",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "Osservazioni",
        id: "pointsNum",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "% piante",
        id: "infectedPercent",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "Intensità media",
        id: "statIntensityAvg",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "Fotografie",
        id: "photosNum",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "Indice di malattia",
        id: "diseaseIndex",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "Azioni",
        id: "actions",
        type: "button",
        style: "danger1",
        buttonText: "Elimina",
        onButtonClick: handleDeleteClick,
      },
      {
        headerText: "",
        id: "actions",
        type: "button",
        style: "secondary",
        buttonText: "Mostra",
        onButtonClick: handleHighlightDetection,
      },
    ];

    const tableData = detections.map((detection) => {
      const dd = detection.detectionData;

      const ds = getDetectionStats(detection);
      console.log("detection stats", ds);

      const diseaseIndexColor = getColor(0, 0.4, ds.diseaseIndex);

      return {
        detectionTime: new Date(detection.detectionTime).toLocaleDateString(),
        bbch: dd.bbch ?? "-",
        pointsNum: dd.points.length ?? "-",
        infectedPercent: ds.infectedPercentStr,
        statIntensityAvg: ds.intensityAvgStr,
        photosNum: dd.photos ? dd.photos.length : 0,
        diseaseIndex: (
          <span>
            <span
              className="dot me-2"
              data-size="12"
              style={{ background: diseaseIndexColor }}
            ></span>
            {ds.diseaseIndexStr}
          </span>
        ),
      };
    });
    return <TableCozy columns={tableColumns} data={tableData} options={tableOptions} />;
  }

  function getColor(min: number, max: number, value: number): string {
    // console.log("getColor", { min, max, value });
    const colors = ["#42C318", "#FFB290", "#FF4D4D", "#A10505"];
    const range = max - min;
    const segment = range / colors.length;
    const index = Math.min(colors.length - 1, Math.floor((value - min) / segment));
    return colors[index];
  }

  const groupStats = {
    groupMin: Infinity,
    groupMax: -Infinity,
  };

  detections.forEach((detection) => {
    const ds = getDetectionStats(detection);
    groupStats.groupMin = Math.min(groupStats.groupMin, ds.pointsMin);
    groupStats.groupMax = Math.max(groupStats.groupMax, ds.pointsMax);
    // console.log("ds", ds);
  });

  const graphData = detections
    .map((detection, index) => {
      return {
        // Linear time mapping
        // x: detection.detectionTime,
        // Sequential time mapping (better for debugging)
        x: index,

        y: getDetectionStats(detection).pointsAvg,
        color: getColor(
          groupStats.groupMin,
          groupStats.groupMax,
          getDetectionStats(detection).pointsAvg,
        ),
      };
    })
    .sort((a, b) => a.x - b.x);

  return (
    <div>
      <Container>
        <Row className="mt-4">
          <Col xl={12}>
            <section className="soft">
              <div className="d-flex align-items-start justify-content-between">
                <Container className="px-0">
                  <Row>
                    <Col md={6} xl={9}>
                      <div className="font-l-600">{`${observationType?.typology}  ›  ${observationType?.method}`}</div>
                    </Col>
                    <Col md={6} xl={3}>
                      <button
                        className="trnt_btn accent wide"
                        data-type="round"
                        onClick={() =>
                          navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`, {
                            state: { typeId: typeId },
                          })
                        }
                      >
                        + Rilevamento {observationType?.typology}
                      </button>
                    </Col>
                  </Row>
                </Container>
              </div>
              <div className="mt-4">
                <Container className="px-0">
                  <Row className="mt-4">
                    <Col md={3}>
                      <p className="font-s-label upper">Rilevamenti</p>
                      <div className="font-l-600">
                        {detections.length}
                        <button
                          className="trnt_btn slim-y narrow-x outlined font-s-600 text-transform-none px-2"
                          data-type="rounded"
                          onClick={() => setTableIsOpen(!tableIsOpen)}
                        >{` ${tableIsOpen ? "Nascondi" : "Vedi tutti"}`}</button>
                      </div>
                    </Col>
                    <Col md={3}>
                      <p className="font-s-label upper">Fotografie</p>
                      <div className="font-l-600">
                        {photos.length}
                        <HorizontalPhotoStack photos={photos} />
                      </div>
                    </Col>
                    <Col md={3}>
                      <p className="font-s-label upper">Note</p>
                      <div className="font-l-600">{notes.length}</div>
                    </Col>
                  </Row>
                  {tableIsOpen && <DetectionsTable />}
                </Container>
              </div>
            </section>
          </Col>
        </Row>
        <Row className="mt-4">
          <Col xl={12}>
            <section className="soft">
              <Row>
                <Col lg={6}>
                  <h4>Graph title</h4>
                  <p>Legend</p>

                  <GradientLineChart
                    height={100}
                    padding={{ top: 0, bottom: 0, left: 40, right: 40 }}
                    strokeWidth={20}
                    dotSize={14}
                    data={graphData}
                  />
                </Col>
                <Col lg={6}>
                  <h4>Map</h4>
                  {/* <FieldMap currentField={currentField} /> */}
                  <FieldMap />
                </Col>
              </Row>
            </section>
          </Col>
        </Row>
      </Container>
    </div>
  );
}
