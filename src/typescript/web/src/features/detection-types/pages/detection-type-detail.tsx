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
    <div className="horizontal-photo-stack">
      {photos.slice(0, maxPhotosToShow).map((photoUrl, index) => (
        <div key={index} className="photo" style={{ backgroundImage: `url(${photoUrl})` }}></div>
      ))}
      {photos.length > maxPhotosToShow && (
        <div className="more-photos">+{photos.length - maxPhotosToShow}</div>
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

  const modelPaths = {
    Peronospora: `/companies/${companyId}/fields/${fieldId}/models/peronospora`,
    Cimice: `/companies/${companyId}/fields/${fieldId}/models/cimice-asiatica`,
    Flavescenza: `/companies/${companyId}/fields/${fieldId}/models/flavescenza-dorata`,
  };
  let modelPath = null;
  type Typology = keyof typeof modelPaths;
  // "Peronospora" | "Cimice" | "Flavescenza"
  if (observationType && observationType.typology in modelPaths) {
    modelPath = modelPaths[observationType.typology as Typology];
  }

  return (
    <div>
      <Container>
        <Row className="">
          <Col xl={12}>
            <section className="soft">
              <div className="d-flex align-items-start justify-content-between">
                <Container className="px-0">
                  <Row>
                    <Col md={6} xl={9}>
                      <div className="font-l-600">{`${observationType?.typology}  ›  ${observationType?.method}`}</div>
                    </Col>
                    <Col md={6} xl={3} className="text-end">
                      <button
                        className="trnt_btn accent"
                        data-type="rounded"
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
                    <Col className="d-flex align-items-start justify-content-start gap-5">
                      <div style={{ minWidth: "140px" }}>
                        <p className="font-s-label upper mb-2">{detections.length} Rilevamenti</p>
                        <div className="font-l-600">
                          {/* <span className="me-1">{detections.length}</span> */}
                          <button
                            className="trnt_btn slim-y narrow-x outlined font-s-600 text-transform-none px-2"
                            style={{ top: "-3px", position: "relative" }}
                            data-type="rounded"
                            onClick={() => setTableIsOpen(!tableIsOpen)}
                          >{`  ${tableIsOpen ? "Nascondi" : "Mostra lista"}  `}</button>
                        </div>
                      </div>
                      <div style={{ minWidth: "140px" }}>
                        <p className="font-s-label upper mb-2">{photos.length} Fotografie</p>
                        <div className="font-l-600">
                          {/* {photos.length} */}
                          <HorizontalPhotoStack photos={photos} />
                        </div>
                      </div>
                      <div style={{ minWidth: "140px" }}>
                        <p className="font-s-label upper mb-2">Note</p>
                        <div className="font-l-600">{notes.length}</div>
                      </div>
                    </Col>
                  </Row>

                  {tableIsOpen && (
                    <Row>
                      <Col className="mt-5">
                        <DetectionsTable />
                      </Col>
                    </Row>
                  )}
                </Container>
              </div>
            </section>
          </Col>
        </Row>
        <Row className="mt-4">
          <Col xl={12}>
            <section className="soft">
              <Row>
                <Col lg={6} className="d-flex flex-column align-items-start justify-content-start">
                  <div>
                    <h4>Graph title</h4>
                    <p>Legend</p>
                  </div>

                  <div className="flex-grow-1 bg-white"></div>

                  <GradientLineChart
                    height={100}
                    padding={{ top: 0, bottom: 0, left: 40, right: 40 }}
                    strokeWidth={20}
                    dotSize={14}
                    data={graphData}
                  />
                </Col>
                <Col lg={6}>
                  {/* <h4>Map</h4> */}
                  {/* <FieldMap currentField={currentField} /> */}
                  <FieldMap />
                </Col>
              </Row>
            </section>
          </Col>
        </Row>
        {modelPath && (
          <Row>
            <Col xl={12} className="text-center mt-4">
              <button
                className="trnt_btn primary"
                data-type="rounded"
                onClick={() => navigate(modelPath)}
              >
                Modello previsionale &rarr;
              </button>
            </Col>
            <Col xl={12} className="spacer my-5"></Col>
          </Row>
        )}
      </Container>
    </div>
  );
}
