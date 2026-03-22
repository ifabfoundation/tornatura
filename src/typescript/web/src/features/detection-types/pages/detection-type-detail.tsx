import React from "react";
import { Detection, DetectionPhoto } from "@tornatura/coreapis";
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

import Icon from "../../../components/Icon";
import LineChartVisx from "../../../components/LineChartVisx";
import {
  getColorDiseaseIndex,
  getDetectionStats,
  getGraphLegend,
  getGraphName,
  shouldUseGradients,
} from "../../../helpers/detections";
import { ModalConfirm } from "../../../components/ModalConfirm";
import { DetectionsTable } from "../../../components/DetectionsTable";
import { useIsMobile } from "../../../helpers/common";

interface HorizontalPhotoStackProps {
  photos: DetectionPhoto[];
}

function HorizontalPhotoStack({ photos }: HorizontalPhotoStackProps) {
  const maxPhotosToShow = 4;
  return (
    <div className="horizontal-photo-stack">
      {photos.slice(0, maxPhotosToShow).map((photo, index) => (
        <div key={index} className="photo" style={{ backgroundImage: `url(${photo.url})` }}></div>
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
      className="trnt_btn narrow-x slim-y outlined ps-1 type-rounded"
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
  const [notesDetailIsOpen, setNotesDetailIsOpen] = React.useState<boolean>(false);
  const [photosDetailIsOpen, setPhotosDetailIsOpen] = React.useState<boolean>(false);
  const [mediaDetailIsOpen, setMediaDetailIsOpen] = React.useState<boolean>(false);

  const [selectedDetectionId, setSelectedDetectionId] = React.useState<string | null>(null);
  const [modalOpen, setModalOpen] = React.useState(false);
  const [modal, setModal] = React.useState<any>({});
  const { companyId, fieldId, typeId } = useParams();
  const isMobile = useIsMobile();
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
      const sortedDetections = [...detections].sort((a, b) => a.detectionTime - b.detectionTime);
      setSelectedDetectionId(sortedDetections[sortedDetections.length - 1].id);
    }
  }, [detections]);

  // React.useEffect(() => {
  //   console.log("selectedDetectionId changed:", selectedDetectionId);
  //   const selectedDetection = detections.find((d) => d.id === selectedDetectionId);
  //   console.log(`Observations: ${selectedDetection?.detectionData.points.length ?? 0}`);
  // }, [selectedDetectionId]);

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

  const notes: {
    detection: Detection;
    detectionTime: number;
    text: string;
  }[] = [];
  sortedDetections.forEach((detection) => {
    // @ts-ignore
    if (detection.detectionData.notes && detection.detectionData.notes != "") {
      // @ts-ignore
      notes.push({
        detection,
        text: detection.detectionData.notes,
        detectionTime: detection.detectionTime,
      });
    }
  });
  const photos: {
    detection: Detection;
    detectionTime: number;
    photo: DetectionPhoto;
  }[] = [];
  sortedDetections.forEach((detection) => {
    if (detection.detectionData.photos && detection.detectionData.photos.length > 0) {
      detection.detectionData.photos.forEach((photo) => {
        photos.push({
          detection,
          detectionTime: detection.detectionTime,
          photo,
        });
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

  /*const handleHighlightDetection = (row: { detection?: Detection }) => {
    const detection = row?.detection;
    if (!detection) {
      return;
    }
    setSelectedDetectionId(detection.id);
    scrollToGraphAndMap();
  }*/

  function handleGraphPointClick(d: any) {
    console.log("Graph point Datum", d);
    setSelectedDetectionId(d?.detection.id);
  }

  function scrollToGraphAndMap() {
    console.log("scrollToGraphAndMap");
    const graphAndMapSection = document.getElementById("graph-map-section");
    if (graphAndMapSection) {
      graphAndMapSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  const groupStats = {
    groupMin: Infinity,
    groupMax: -Infinity,
  };

  sortedDetections.forEach((detection) => {
    const ds = getDetectionStats(detection);
    groupStats.groupMin = Math.min(groupStats.groupMin, ds.pointsMin);
    groupStats.groupMax = Math.max(groupStats.groupMax, ds.pointsMax);
    // console.log("ds", ds);
  });

  /*const graphData = sortedDetections
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
    .sort((a, b) => a.x - b.x);*/

  const graphDataVisx = sortedDetections.map((detection) => {
    const ds = getDetectionStats(detection);
    return {
      id: detection.id,
      // Linear time mapping
      x: new Date(detection.detectionTime),
      // Sequential time mapping (better for debugging)
      // x: new Date(mapValues(index, 0, a.length, a[0].detectionTime, a[a.length - 1].detectionTime)),
      y: ds.type === "counters" ? ds.counterSumsTotal : ds.diseaseIndex,
      // color: getColor(groupStats.groupMin, groupStats.groupMax, ds.pointsAvg),
      color:
        observationType?.observationType === "range"
          ? getColorDiseaseIndex(ds.diseaseIndex)
          : "white",
      detection: detection,
      displayValue: ds.displayValue,
      displayLabel: ds.displayLabel,
    };
  });
  // .sort((a, b) => b.x.getTime() - a.x.getTime());

  const modelPaths = {
    Peronospora: `/companies/${companyId}/fields/${fieldId}/models/peronospora`,
    Flavescenza: `/companies/${companyId}/fields/${fieldId}/models/flavescenza-dorata`,
    Cimice: `/companies/${companyId}/fields/${fieldId}/models/cimice-asiatica`,
    // Lisso: `/companies/${companyId}/fields/${fieldId}/models/lisso`,
    // Scafoideo: `/companies/${companyId}/fields/${fieldId}/models/scafoideo`,
    // Diabrotica: `/companies/${companyId}/fields/${fieldId}/models/diabrotica`,
  };
  // @ts-ignore
  let modelPath;
  type Typology = keyof typeof modelPaths;
  // "Peronospora" | "Cimice" | "Flavescenza"
  if (observationType && observationType.typology in modelPaths) {
    modelPath = modelPaths[observationType.typology as Typology];
  }

  // to be used for csv download
  const flatDetectionsData: Record<string, unknown>[] = [];
  sortedDetections.forEach((detection) => {
    const dd = detection.detectionData;
    const ds = getDetectionStats(detection);
    console.log("ds-------------:", ds);
    dd.points.forEach((point, index) => {
      if (observationType?.observationType === "range") {
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
      } else if (observationType?.observationType === "counters") {
        // @ts-ignore
        const counter1Name = point?.data?.counters[0]?.counterName ?? "_1";
        // @ts-ignore
        const counter2Name = point?.data?.counters[1]?.counterName ?? "_2";
        // @ts-ignore
        const counter1Value = point?.data?.counters[0]?.counterValue;
        // @ts-ignore
        const counter2Value = point?.data?.counters[1]?.counterValue;
        const entry = {
          detectionId: detection.id,
          detectionTime: new Date(detection.detectionTime).toISOString(),
          bbch: dd.bbch ?? "",
          observationNum: `#${index + 1}`,
          [`counter${counter1Name}`]: counter1Value,
          [`counter${counter2Name}`]: counter2Value,
          counterSum:
            counter1Value !== undefined && counter2Value !== undefined
              ? counter1Value + counter2Value
              : "",
        };
        console.log("entry", entry);
        flatDetectionsData.push(entry);
      }
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
  
  // @ts-ignore
  function handleToggleTable() {
    const newIsOpen = !tableIsOpen;
    if (newIsOpen === true && notesDetailIsOpen) {
      setNotesDetailIsOpen(false);
      setPhotosDetailIsOpen(false);
    }
    setTableIsOpen(newIsOpen);
  }
  function handleToggleMedia() {
    const newIsOpen = !mediaDetailIsOpen;
    setMediaDetailIsOpen(newIsOpen);
  }
  function handleTogglePhotos() {
    const newIsOpen = !photosDetailIsOpen;
    if (newIsOpen === true && tableIsOpen) {
      setTableIsOpen(false);
      setNotesDetailIsOpen(false);
    }
    setPhotosDetailIsOpen(newIsOpen);
  }
  // @ts-ignore
  function handleToggleNotes() {
    const newIsOpen = !notesDetailIsOpen;
    if (newIsOpen === true && tableIsOpen) {
      setTableIsOpen(false);
      setPhotosDetailIsOpen(false);
    }
    setNotesDetailIsOpen(newIsOpen);
  }

  function handleSwitchDate(direction: "next" | "prev") {
    const currentIndex = graphDataVisx.findIndex((d) => d.id === selectedDetectionId);
    if (currentIndex !== -1) {
      const nextIndex =
        direction === "prev"
          ? (currentIndex + 1) % graphDataVisx.length
          : (currentIndex - 1 + graphDataVisx.length) % graphDataVisx.length;
      setSelectedDetectionId(graphDataVisx[nextIndex].id);
      // scrollToGraphAndMap();
    }
  }

  const ButtonDashboard = (
    <button
      className="trnt_btn primary type-rounded"
      onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}`)}
    >
      {"← Dashboard"}
    </button>
  );

  const ButtonNewDetection = (
    <button
      className="trnt_btn accent type-rounded"
      data-type="rounded"
      onClick={() =>
        navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`, {
          state: { typeId: typeId },
        })
      }
    >
      <span className="font-m-600">+ Rilevamento {observationType?.typology}</span>
    </button>
  );

  const graphTitle = getGraphName(observationType?.typology ?? "");
  const graphLegend = getGraphLegend(observationType?.typology ?? "");
  const graphHeight = isMobile ? 150 : 200;

  const selectedDetection = detections.find((d) => d.id === selectedDetectionId);
  const selectedDate = selectedDetection
    ? new Date(selectedDetection.detectionTime).toLocaleDateString("es-ES", {
        day: "2-digit",
        month: "2-digit",
        year: "2-digit",
      })
    : "";

  console.log("observationType", observationType);

  function MediaItems() {
    const itemsWithDate = [{} as { date: Date; item: JSX.Element }];

    notes.forEach((note, index) => {
      const item = (
        <section className="soft nested-1 mt-2 p-3 pt-0">
          <div className="mb-1 pt-2 d-flex align-items-baseline justify-content-between">
            <strong>
              <span
                className="d-inline-block position-relative"
                style={{ margin: "-8px -5px -8px -8px", top: "10px" }}
              >
                <Icon iconName="asterisk" color="black" />
              </span>
              {`Rilevamento ${new Date(note.detectionTime).toLocaleDateString([], {
                day: "2-digit",
                month: "2-digit",
                year: "2-digit",
              })}`}
            </strong>

            <button
              className="trnt_btn slim-y narrow-x outlined font-s-600 text-transform-none px-2 type-rounded"
              data-type="rounded"
              style={{ top: "-3px", position: "relative" }}
              onClick={() => {
                setSelectedDetectionId(note.detection.id);
                scrollToGraphAndMap();
              }}
            >
              Evidenzia
            </button>
          </div>
          <div key={index}>
            <p className="ps-3 pe-md-5">{note.text}</p>
          </div>
        </section>
      );
      itemsWithDate.push({ date: new Date(note.detectionTime), item });
    });

    photos.forEach((photo, index) => {
      const item = (
        <section className="soft nested-1 mt-2 p-3 pt-0">
          <div className="mb-1 pt-2 d-flex align-items-baseline justify-content-between">
            <strong>
              <span
                className="d-inline-block position-relative"
                style={{ margin: "-8px -5px -8px -8px", top: "10px" }}
              >
                <Icon iconName="asterisk" color="black" />
              </span>
              {`Rilevamento ${new Date(photo.detectionTime).toLocaleDateString([], {
                day: "2-digit",
                month: "2-digit",
                year: "2-digit",
              })}`}
            </strong>

            <button
              className="trnt_btn slim-y narrow-x outlined font-s-600 text-transform-none px-2 type-rounded"
              data-type="rounded"
              style={{ top: "-3px", position: "relative" }}
              onClick={() => {
                setSelectedDetectionId(photo.detection.id);
                scrollToGraphAndMap();
              }}
            >
              Evidenzia
            </button>
          </div>
          <div key={index} className="text-center">
            <img
              className="d-inline-block rounded"
              src={photo.photo.url}
              style={{ maxWidth: "300px", maxHeight: "300px" }}
            />
          </div>
        </section>
      );
      itemsWithDate.push({ date: new Date(photo.detectionTime), item });
    });

    // @ts-ignore
    return <div>{itemsWithDate.sort((a, b) => a.date - b.date).map(({ item }) => item)}</div>;
  }

  return (
    <div>
      <Container fluid>
        {modalOpen && <modal.component {...modal.componentProps} />}
        <Row>
          <Col xs={6}>{ButtonDashboard}</Col>
          <Col xs={6} className="text-end">
            {ButtonNewDetection}
          </Col>
          <Col xs={6} className="text-end">
            <div className="space-05"></div>
          </Col>
        </Row>
        <Row>
          <Col xl={12}>
            <section className="soft">
              <div className="d-flex align-items-start justify-content-between">
                <Container fluid className="px-0">
                  <Row>
                    <Col sm={6}>
                      <div className="font-s-label mb-1">Rilevamenti di</div>
                      <div className="font-l-600">{`${observationType?.typology}  ›  ${observationType?.method}`}</div>
                      {/* <div className="debug">{observationType?.typology}</div> */}
                    </Col>
                    <Col sm={6} className="text-sm-end">
                      <div className="d-flex align-items-center justify-content-sm-end">
                        <div className="ms-sm-3 mt-4 mt-sm-0">
                          <p className="font-s-label upper mb-1">
                            {/* {`${photos.length ? photos.length + " " : ""}Fotografi${photos.length === 1 ? "a" : "e"}`} */}
                            Foto e note
                            {/* {`${photos.length ? photos.length + " " : ""}Foto e ${notes.length ? notes.length + " " : ""}Note`} */}
                          </p>
                          <div className="font-l-600">
                            <span onClick={handleTogglePhotos}>
                              {photos.length + notes.length > 0 && (
                                <>
                                  <HorizontalPhotoStack photos={photos.map((item) => item.photo)} />
                                  <button
                                    className="trnt_btn slim-y narrow-x outlined font-s-600 text-transform-none px-2 type-rounded me-0"
                                    data-type="rounded"
                                    style={{ top: "-8px", position: "relative" }}
                                    onClick={handleToggleMedia}
                                  >{`  ${mediaDetailIsOpen ? "Nascondi" : "Espandi"}  `}</button>
                                </>
                              )}
                            </span>
                            {photos.length + notes.length === 0 && (
                              <div className="font-l-600">Nessuna</div>
                            )}
                          </div>
                        </div>
                        {/* <div className="d-none d-lg-block">{ButtonNewDetection}</div> */}
                      </div>
                    </Col>
                  </Row>
                  {mediaDetailIsOpen && (
                    <Row>
                      <Col xl={12} className="mt-5">
                        <MediaItems />
                      </Col>
                    </Row>
                  )}
                </Container>
              </div>
            </section>
          </Col>
        </Row>

        <Row className="mt-4" id="graph-map-section">
          <Col xl={12}>
            <section className="soft">
              <Row>
                <Col lg={{ span: 6, order: 2 }}>
                  <FieldMaplet
                    detectionId={selectedDetectionId}
                    interactions={{
                      dragPan: false,
                      scrollZoom: false,
                    }}
                  />
                </Col>
                <Col
                  lg={{ span: 6, order: 1 }}
                  className="d-flex flex-column align-items-start justify-content-start"
                >
                  {/* Line graph */}
                  <div ref={containerRef} className="w-100 order-md-3">
                    <LineChartVisx
                      width={containerWidth}
                      height={graphHeight}
                      data={graphDataVisx}
                      onSelectPoint={handleGraphPointClick}
                      gradients={shouldUseGradients(observationType?.typology)}
                      ticksFormatterName={observationType?.observationType as "counters" | "range"}
                      selectedId={selectedDetectionId ?? undefined}
                    />
                  </div>

                  {/* Title & legend */}
                  <div className="order-md-1 d-xl-flex align-items-start justify-content-between w-100">
                    {/* Date switcher */}
                    <div className="date-switcher order-lg-2 my-3 mt-lg-0 my-xl-0 ms-xl-3">
                      <button
                        className="trnt_btn slim-y narrow-x outlined font-s-600 text-transform-none px-2 type-round"
                        style={{ top: "-3px", position: "relative" }}
                        onClick={() => handleSwitchDate("prev")}
                      >
                        &larr;
                      </button>
                      <span className="date">{`${selectedDate}`}</span>
                      <button
                        className="trnt_btn slim-y narrow-x outlined font-s-600 text-transform-none px-2 type-round"
                        style={{ top: "-3px", position: "relative" }}
                        onClick={() => handleSwitchDate("next")}
                      >
                        &rarr;
                      </button>
                    </div>
                    {/* Title & Legend */}
                    <div className="order-lg-1" style={{ flexGrow: 1 }}>
                      <h4>
                        <strong>{graphTitle}</strong>
                      </h4>
                      {graphLegend && (
                        <div className="graph-legend my-3 p-2 pb-2 rounded bg-white d-inline-flex">
                          <img src={graphLegend} alt="Legenda grafico" />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Spacer */}
                  <div className="flex-grow-1 bg-white order-md-2"></div>
                </Col>
              </Row>
            </section>
          </Col>
        </Row>

        <Row className="mt-4">
          <Col xl={12}>
            <section className="soft pb-3">
              <div className="">
                <Container fluid className="px-0">
                  <Row>
                    <Col xl={12} className="mt-0">
                      <DetectionsTable
                        detections={sortedDetections}
                        observationType={observationType?.observationType ?? ""}
                        handleHighlightDetection={(row) => {
                          setSelectedDetectionId(row.detection?.id ?? null);
                          scrollToGraphAndMap();
                        }}
                        handleDeleteDetection={handleDeleteClick}
                      />
                    </Col>
                    <Col xl={12} className="mt-3 d-flex align-items-center justify-content-end">
                      <div className="font-s-600 me-2">Esporta dati</div>
                      <DownloadDataButton
                        data={sortedDetections}
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
                </Container>
              </div>
            </section>
          </Col>
        </Row>
        <Row className="mt-4 d-md-none">
          <Col xs={6}>{ButtonDashboard}</Col>
          <Col xs={6} className="text-end">
            {ButtonNewDetection}
          </Col>
        </Row>

        {/* {modelPath && (
          <Row>
            <Col xl={12} className="text-center mt-4">
              <button
                className="trnt_btn primary type-rounded"
                data-type="rounded"
                onClick={() => navigate(modelPath)}
              >
                Modello previsionale &rarr;
              </button>
            </Col>
            <Col xl={12} className="spacer my-4"></Col>
          </Row>
        )} */}
        <Row>
          <Col xl={12} className="spacer my-4"></Col>
        </Row>
      </Container>
    </div>
  );
}
