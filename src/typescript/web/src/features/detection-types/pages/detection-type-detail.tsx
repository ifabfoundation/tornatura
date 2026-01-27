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
import { detectionsActions, detectionsSelectors } from "../../detections/state/detections-slice";
import { Container, Row, Col } from "react-bootstrap";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { FieldMaplet } from "../../../components/FieldMaplet";
import { GradientLineChart } from "../../../components/GradientLineChart";
import Icon from "../../../components/Icon";
import LineChartVisx from "../../../components/LineChartVisx";
import { getColorDiseaseIndex, getDetectionStats } from "../../../helpers/detections";
import { ModalConfirm } from "../../../components/ModalConfirm";
import { mapValues } from "../../../helpers/common";

// import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { DetectionsTable } from "../../../components/DetectionsTable";

interface HorizontalPhotoStackProps {
  photos: string[];
}

function HorizontalPhotoStack({ photos }: HorizontalPhotoStackProps) {
  const maxPhotosToShow = 4;
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

type ExportFormat = "json" | "csv";

type DownloadDataButtonProps = {
  data: unknown[] | Record<string, unknown>; // CSV requires arrays or array of objects
  format: ExportFormat;
  filename?: string;
};

export function DownloadDataButton({
  data,
  format,
  filename = `data.${format}`,
}: DownloadDataButtonProps) {
  const convertToCsv = (rows: Record<string, unknown>[]) => {
    if (rows.length === 0) return "";

    const headers = Object.keys(rows[0]);
    const csvRows = [
      headers.join(","), // header row
      ...rows.map((row) => headers.map((h) => JSON.stringify(row[h] ?? "")).join(",")),
    ];

    return csvRows.join("\n");
  };

  const handleDownload = () => {
    let fileContent = "";
    let mime = "";

    if (format === "json") {
      fileContent = JSON.stringify(data, null, 2);
      mime = "application/json";
    } else {
      // CSV
      if (!Array.isArray(data)) {
        console.error("CSV export requires an array of objects");
        return;
      }
      fileContent = convertToCsv(data as Record<string, unknown>[]);
      mime = "text/csv";
    }

    const blob = new Blob([fileContent], { type: mime });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();

    URL.revokeObjectURL(url);
  };

  return (
    <button
      className="trnt_btn narrow-x slim-y outlined ps-1"
      data-type="rounded"
      onClick={handleDownload}
    >
      <Icon iconName={"download"} color={"black"} />
      {format.toUpperCase()}
    </button>
  );
}

export function DetectionTypeDetail() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [tableIsOpen, setTableIsOpen] = React.useState<boolean>(false);
  const [selectedDetectionId, setSelectedDetectionId] = React.useState<string | null>(null);
  const [modalOpen, setModalOpen] = React.useState(false);
  const [modal, setModal] = React.useState<any>({});
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
  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Focus Rilevamento", subtitle: "Subtitle" }));
  }, []);

  React.useEffect(() => {
    if (detections.length > 0) {
      const sortedDetections = [...detections].sort((a, b) => b.detectionTime - a.detectionTime);
      setSelectedDetectionId(sortedDetections[0].id);
    }
  }, [detections]);

  React.useEffect(() => {
    console.log("selectedDetectionId changed:", selectedDetectionId);
    const selectedDetection = detections.find((d) => d.id === selectedDetectionId);
    console.log(`Observations: ${selectedDetection?.detectionData.points.length ?? 0}`);
  }, [selectedDetectionId]);

  React.useEffect(() => {
    if (companyId && fieldId) {
      dispatch(detectionTypesActions.fetchDetectionTypesAction({ orgId: companyId, fieldId }));
    }
    dispatch(observationTypesActions.fetchObservationTypesAction({}));
  }, [companyId, fieldId]);

  // Responsive width
  const [containerWidth, setContainerWidth] = React.useState<number>(0);
  const containerRef = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    function updateWidth() {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth);
      } else {
        setContainerWidth(0);
      }
    }
    updateWidth();
    window.addEventListener("resize", updateWidth);
    return () => {
      window.removeEventListener("resize", updateWidth);
    };
  }, []);

  const sortedDetections = [...detections].sort((a, b) => b.detectionTime - a.detectionTime);

  const notes = [];
  sortedDetections.forEach((detection) => {
    // @ts-ignore
    if (detection.detectionData.notes && detection.detectionData.notes != "") {
      // @ts-ignore
      notes.push(detection.detectionData.notes);
    }
  });
  const photos: string[] = [];
  sortedDetections.forEach((detection) => {
    // @ts-ignore
    if (detection.detectionData.photos && detection.detectionData.photos.length > 0) {
      // @ts-ignore
      detection.detectionData.photos.forEach((photo) => {
        photos.push(photo);
      });
    }
  });

  function handleDeleteClick(row: { detection?: Detection }) {
    const detection = row?.detection;
    if (!detection || !companyId || !fieldId) {
      return;
    }
    const detectionDate = new Date(detection.detectionTime).toLocaleDateString();
    setModal({
      component: ModalConfirm,
      componentProps: {
        title: "Eliminazione rilevamento",
        content: `Sei sicuro di voler eliminare il rilevamento del ${detectionDate}? Questa azione non può essere annullata.`,
        action: "Elimina",
        actionBtnClass: "danger",
        handleCancel: () => setModalOpen(false),
        handleConfirm: async () => {
          await dispatch(
            detectionsActions.deleteDetectionAction({
              orgId: companyId,
              fieldId,
              detectionId: detection.id,
            }),
          );
          setModalOpen(false);
          if (selectedDetectionId === detection.id) {
            const remaining = detections.filter((item) => item.id !== detection.id);
            setSelectedDetectionId(remaining.length > 0 ? remaining[0].id : null);
          }
        },
      },
    });
    setModalOpen(true);
  }
  function handleHighlightDetection(row: { detection?: Detection }) {
    const detection = row?.detection;
    if (!detection) {
      return;
    }
    setSelectedDetectionId(detection.id);
  }

  function handleGraphPointClick(d: any) {
    console.log("Graph point Datum", d);
    setSelectedDetectionId(d?.detection.id);
  }

  // function DetectionsTable() {
  //   const tableOptions: TableOptions = {
  //     defaultSortCol: "date",
  //     defaultSortDir: "desc",
  //   };

  //   const tableColumns: TableColumn[] = [
  //     {
  //       headerText: "Data",
  //       id: "detectionTime",
  //       sortable: true,
  //       style: "normal",
  //       type: "text",
  //     },
  //     {
  //       headerText: "BBCH",
  //       id: "bbch",
  //       sortable: true,
  //       style: "normal",
  //       type: "text",
  //     },
  //     {
  //       headerText: "Osservazioni",
  //       id: "pointsNum",
  //       sortable: true,
  //       style: "normal",
  //       type: "text",
  //     },
  //     {
  //       headerText: "% piante",
  //       id: "infectedPercent",
  //       sortable: true,
  //       style: "normal",
  //       type: "text",
  //     },
  //     {
  //       headerText: "Intensità media",
  //       id: "statIntensityAvg",
  //       sortable: true,
  //       style: "normal",
  //       type: "text",
  //     },
  //     {
  //       headerText: "Fotografie",
  //       id: "photosNum",
  //       sortable: true,
  //       style: "normal",
  //       type: "text",
  //     },
  //     {
  //       headerText: "Indice di malattia",
  //       id: "diseaseIndex",
  //       sortable: true,
  //       style: "normal",
  //       type: "text",
  //     },
  //     {
  //       headerText: "Azioni",
  //       id: "action1",
  //       type: "button",
  //       style: "danger1",
  //       buttonText: "Elimina",
  //       onButtonClick: handleDeleteClick,
  //     },
  //     {
  //       headerText: "",
  //       id: "action2",
  //       type: "button",
  //       style: "secondary",
  //       buttonText: "Mostra",
  //       onButtonClick: handleHighlightDetection,
  //     },
  //   ];

  //   const sortedDetections = [...detections].sort((a, b) => a.detectionTime - b.detectionTime);

  //   const tableData = sortedDetections.map((detection) => {
  //     const dd = detection.detectionData;
  //     const ds = getDetectionStats(detection);
  //     const diseaseIndexColor = getColorDiseaseIndex(ds.diseaseIndex);
  //     return {
  //       detection,
  //       detectionTime:
  //         new Date(detection.detectionTime).toLocaleDateString() +
  //         ", " +
  //         new Date(detection.detectionTime).toLocaleTimeString([], {
  //           hour: "2-digit",
  //           minute: "2-digit",
  //         }),
  //       bbch: dd.bbch ?? "-",
  //       pointsNum: dd.points.length ?? "-",
  //       infectedPercent: ds.infectedPercentStr,
  //       statIntensityAvg: ds.intensityAvgStr,
  //       photosNum: dd.photos && dd.photos.length > 0 ? dd.photos.length : "–",
  //       diseaseIndex: (
  //         <span>
  //           <span
  //             className="dot me-2"
  //             data-size="12"
  //             style={{ background: diseaseIndexColor }}
  //           ></span>
  //           {ds.diseaseIndexStr}
  //         </span>
  //       ),
  //     };
  //   });
  //   return <TableCozy columns={tableColumns} data={tableData} options={tableOptions} />;
  // }

  // function getColor(min: number, max: number, value: number): string {
  //   // console.log("getColor", { min, max, value });
  //   const colors = ["#42C318", "#FFB290", "#FF4D4D", "#A10505"];
  //   const range = max - min;
  //   const segment = range / colors.length;
  //   const index = Math.min(colors.length - 1, Math.floor((value - min) / segment));
  //   return colors[index];
  // }

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
      const ds = getDetectionStats(detection);
      return {
        // x: detection.detectionTime, // Linear time mapping
        x: index, // Sequential time mapping (better for debugging)
        y: ds.pointsAvg,
        // color: getRangePointColor(groupStats.groupMin, groupStats.groupMax, ds.pointsAvg),
        color: getColorDiseaseIndex(ds.diseaseIndex),
        detection: detection,
      };
    })
    .sort((a, b) => a.x - b.x);

  const graphDataVisx = sortedDetections.map((detection, index, a) => {
    const ds = getDetectionStats(detection);
    return {
      id: detection.id,
      // Linear time mapping
      // x: new Date(detection.detectionTime),
      // Sequential time mapping (better for debugging)
      x: new Date(mapValues(index, a.length, 0, a[0].detectionTime, a[a.length - 1].detectionTime)),
      y: ds.type === "counters" ? ds.counterSumsTotal : ds.pointsAvg,
      // color: getColor(groupStats.groupMin, groupStats.groupMax, ds.pointsAvg),
      color: getColorDiseaseIndex(ds.diseaseIndex),
      detection: detection,
      displayValue: ds.displayValue,
      displayLabel: ds.displayLabel,
    };
  });
  // .sort((a, b) => b.x.getTime() - a.x.getTime());

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

  // to be used for csv download
  const flatDetectionsData: Record<string, unknown>[] = [];
  detections.forEach((detection) => {
    const dd = detection.detectionData;
    const ds = getDetectionStats(detection);
    dd.points.forEach((point, index) => {
      const dotValue = point.data.rangeValue;
      const entry = {
        detectionId: detection.id,
        detectionTime: new Date(detection.detectionTime).toISOString(),
        bbch: dd.bbch ?? "",
        observationNum: `#${index + 1}`,
        dotValue: dotValue !== undefined && dotValue !== null ? dotValue : "",
        diseaseIndex: ds.diseaseIndex,
      };
      flatDetectionsData.push(entry);
    });
  });

  // debug CSV data view
  if (false) {
    return (
      <div>
        <h2>Debug CSV data</h2>
        <table className="raw-data-preview">
          {/* output a table showing the flat data with keys => headers */}
          {flatDetectionsData.length > 0 &&
            flatDetectionsData.slice(0, 1).map((row, rowIndex) => (
              <tr key={rowIndex}>
                {Object.entries(row).map(([key]) => (
                  <th key={key}>{key}</th>
                ))}
              </tr>
            ))}
          {flatDetectionsData.length > 0 &&
            flatDetectionsData.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {Object.entries(row).map(([key, value]) => (
                  <td key={key}>{String(value)}</td>
                ))}
              </tr>
            ))}
        </table>
      </div>
    );
  }

  const buttonNewDetection = (
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
  );

  return (
    <div>
      <Container>
        {modalOpen && <modal.component {...modal.componentProps} />}
        <Row className="">
          <Col xl={12}>
            <section className="soft">
              <div className="d-flex align-items-start justify-content-between">
                <Container className="px-0">
                  <Row>
                    <Col md={6}>
                      <div className="font-l-600">{`${observationType?.typology}  ›  ${observationType?.method}`}</div>
                    </Col>
                    <Col md={6} className="text-md-end d-none d-md-block">
                      {buttonNewDetection}
                    </Col>
                  </Row>
                </Container>
              </div>
              <div className="mt-4">
                <Container className="px-0">
                  <Row className="mt-4">
                    <Col xs={"auto"} md={{ order: 1 }} className="me-4">
                      <p className="font-s-label upper mb-2">Rilevamenti</p>
                      <div className="font-l-600">
                        <span className="me-1">{detections.length}</span>
                        <button
                          className="trnt_btn slim-y narrow-x outlined font-s-600 text-transform-none px-2"
                          style={{ top: "-3px", position: "relative" }}
                          data-type="rounded"
                          onClick={() => setTableIsOpen(!tableIsOpen)}
                        >{`  ${tableIsOpen ? "Nascondi" : "Espandi"}  `}</button>
                      </div>
                    </Col>

                    <Col xs={"auto"} md={{ order: 3 }} className="me-4">
                      <p className="font-s-label upper mb-2">Note</p>
                      <div className="font-l-600">
                        <span className="me-1">{notes.length > 0 ? notes.length : "Nessuna"}</span>
                        {notes.length > 0 && (
                          <button
                            disabled
                            className="trnt_btn slim-y narrow-x outlined font-s-600 text-transform-none px-2"
                            style={{ top: "-3px", position: "relative" }}
                            data-type="rounded"
                            onClick={() => setTableIsOpen(!tableIsOpen)}
                          >{`  ${tableIsOpen ? "Nascondi" : "Espandi"}  `}</button>
                        )}
                      </div>
                    </Col>

                    <Col xs={12} md={{ span: "auto", order: 2 }} className="me-4 mt-3 mt-md-0">
                      <p className="font-s-label upper mb-2">{`${photos.length ? photos.length + " " : ""}Fotografi${photos.length === 1 ? "a" : "e"}`}</p>
                      <div className="font-l-600">
                        {photos.length > 0 && <HorizontalPhotoStack photos={photos} />}
                        {photos.length === 0 && <div className="font-l-600">Nessuna</div>}
                      </div>
                    </Col>
                  </Row>

                  {tableIsOpen && (
                    <Row>
                      <Col xl={12} className="mt-5">
                        <DetectionsTable
                          detections={sortedDetections}
                          handleHighlightDetection={(row) =>
                            setSelectedDetectionId(row.detection?.id ?? null)
                          }
                          handleDeleteDetection={handleDeleteClick}
                        />
                      </Col>
                      <Col xl={12} className="my-2">
                        <DownloadDataButton
                          data={detections}
                          format={"json"}
                          filename={`campo ${fieldId}`}
                        />
                        <DownloadDataButton
                          data={flatDetectionsData}
                          format={"csv"}
                          filename={`campo ${fieldId}`}
                        />
                      </Col>
                    </Row>
                  )}
                  <Row>
                    <Col xl={12} className="mt-4 d-md-none">
                      {buttonNewDetection}
                    </Col>
                  </Row>
                </Container>
              </div>
            </section>
          </Col>
        </Row>
        <Row className="mt-4">
          <Col xl={12}>
            <section className="soft">
              <Row>
                <Col lg={{ span: 6, order: 2 }}>
                  {selectedDetectionId && (
                    <FieldMaplet
                      detectionId={selectedDetectionId}
                      interactions={{
                        dragPan: false,
                        scrollZoom: false,
                      }}
                    />
                  )}
                </Col>
                <Col
                  lg={{ span: 6, order: 1 }}
                  className="d-flex flex-column align-items-start justify-content-start"
                >
                  <div>
                    <h4>Graph title</h4>
                    <p>Legend</p>
                  </div>

                  <div className="flex-grow-1 bg-white"></div>
                  <div ref={containerRef}>
                    <GradientLineChart
                      height={100}
                      padding={{ top: 0, bottom: 0, left: 40, right: 40 }}
                      strokeWidth={20}
                      dotSize={14}
                      data={graphData}
                    />
                    <LineChartVisx
                      width={containerWidth}
                      height={200}
                      data={graphDataVisx}
                      onSelectPoint={handleGraphPointClick}
                      selectedId={selectedDetectionId ?? undefined}
                    />
                  </div>
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
