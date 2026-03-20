import TableCozy, { TableColumn, TableOptions } from "./TableCozy";
import { getColorDiseaseIndex, getDetectionStats } from "../helpers/detections";
import { Detection } from "@tornatura/coreapis";

interface DetectionsTableProps {
  detections: Detection[];
  observationType: string;
  handleHighlightDetection?: (row: { detection?: Detection }) => void;
  handleDeleteDetection?: (row: { detection?: Detection }) => void; // Maybe it can be handeled directly from inside here
}

function getCounterNames(detections: Detection[]) {
  if (detections.length > 0) {
    const firstDetection = detections[0];
    if (firstDetection.detectionData.points.length > 0) {
      const firstPoint = firstDetection.detectionData.points[0];
      if ((firstPoint.data?.counters?.length ?? 0) >= 2) {
        return firstPoint.data?.counters?.map((counter) => counter.counterName) ?? [];
      }
    }
  }
  return [];
}

export function DetectionsTable({
  detections,
  observationType,
  handleHighlightDetection,
  handleDeleteDetection,
}: DetectionsTableProps) {
  const tableOptions: TableOptions = {
    defaultSortCol: "date",
    defaultSortDir: "desc",
  };

  const tableColumnsBase: TableColumn[] = [
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
      align: "center",
    },
    {
      headerText: "Punti",
      id: "pointsNum",
      sortable: false,
      style: "normal",
      type: "text",
      align: "center",
    },
    {
      headerText: "Note",
      id: "notesNum",
      sortable: false,
      style: "normal",
      type: "text",
      align: "center",
    },
    {
      headerText: "Foto",
      id: "photosNum",
      sortable: false,
      style: "normal",
      type: "text",
      align: "center",
    },
  ];
  const tableColumnsRange: TableColumn[] = [
    {
      headerText: "% piante",
      id: "infectedPercent",
      sortable: true,
      style: "normal",
      type: "text",
      align: "center",
    },
    {
      headerText: "Intensità media",
      id: "statIntensityAvg",
      sortable: true,
      style: "normal",
      type: "text",
      align: "center",
    },
    {
      headerText: "Indice di malattia",
      id: "diseaseIndex",
      sortable: true,
      style: "normal",
      type: "text",
      align: "center",
    },
  ];
  const counterNames = getCounterNames(detections);
  const tableColumnsCounters: TableColumn[] = [
    {
      headerText: counterNames.length > 0 ? counterNames[0] : "Ninfe_",
      id: "counter1",
      sortable: true,
      style: "normal",
      type: "text",
      align: "center",
    },
    {
      headerText: counterNames.length > 1 ? counterNames[1] : "Adulti_",
      id: "counter2",
      sortable: true,
      style: "normal",
      type: "text",
      align: "center",
    },
    {
      headerText: "Somma",
      id: "counterSum",
      sortable: true,
      style: "normal",
      type: "text",
      align: "center",
    },
  ];
  const tableColumnsActions: TableColumn[] = [
    {
      headerText: "",
      id: "action2",
      type: "button",
      style: "outlined type-rounded slim-y",
      shrink: true,
      buttonText: "Evidenzia",
      onButtonClick: (data) => {
        if (handleHighlightDetection) {
          handleHighlightDetection(data);
          return;
        }
        console.log("handleHighlightDetection not set", data);
        alert("handleHighlightDetection not set");
      },
    },
    {
      headerText: "",
      id: "action1",
      type: "button",
      style: "normal",
      shrink: true,
      // buttonText: "E",
      buttonIcon: "bin",
      onButtonClick: (data) => {
        if (handleDeleteDetection) {
          handleDeleteDetection(data);
          return;
        }
        console.log("handleDeleteDetection not set", data);
        alert("handleDeleteDetection not set");
      },
    },
  ];

  const tableColumns: TableColumn[] = [
    ...tableColumnsBase,
    ...(observationType === "range" ? tableColumnsRange : tableColumnsCounters),
    ...tableColumnsActions,
  ];

  const sortedDetections = [...detections].sort((a, b) => a.detectionTime - b.detectionTime);

  const tableData = sortedDetections.map((detection) => {
    console.log("detection-------------:", detection);
    const dd = detection.detectionData;
    const ds = getDetectionStats(detection);
    const diseaseIndexColor = getColorDiseaseIndex(ds.diseaseIndex);
    return {
      detection,
      detectionTime:
        new Date(detection.detectionTime).toLocaleDateString("it-IT", {
          dateStyle: "short",
        }) +
        ", " +
        new Date(detection.detectionTime).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      bbch: dd.bbch ?? "-",
      pointsNum: dd.points.length ?? "-",
      infectedPercent: (
        <span className="d-inline-block text-right" style={{ width: "3em" }}>
          {ds.infectedPercentStr}
        </span>
      ),
      statIntensityAvg: (
        <span className="d-inline-block text-right" style={{ width: "3em" }}>
          {ds.intensityAvgStr}
        </span>
      ),
      photosNum: dd.photos && dd.photos.length > 0 ? dd.photos.length : "–",
      notesNum: dd.notes && dd.notes.length > 0 ? "Sì" : "–",
      diseaseIndex: (
        <span>
          <span className="d-inline-block text-right" style={{ width: "3em" }}>
            {ds.diseaseIndexStr}
          </span>
          <span
            className="dot mx-2"
            data-size="12"
            style={{ background: diseaseIndexColor }}
          ></span>
        </span>
      ),
      counter1:
        observationType == "counters"
          ? dd.points.reduce((acc: number, point: any) => {
              return acc + (point.data.counters[0].counterValue || 0);
            }, 0)
          : undefined,
      counter2:
        observationType == "counters"
          ? dd.points.reduce((acc: number, point: any) => {
              return acc + (point.data.counters[1].counterValue || 0);
            }, 0)
          : undefined,
      counterSum:
        observationType == "counters"
          ? dd.points.reduce((acc: number, point: any) => {
              return (
                acc +
                point.data.counters.reduce(
                  (sum: number, counter: any) => sum + (counter.counterValue || 0),
                  0,
                )
              );
            }, 0)
          : undefined,
    };
  });
  return <TableCozy columns={tableColumns} data={tableData} options={tableOptions} />;
}
