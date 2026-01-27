/*** WWWWWW IIIIII PPPPPP ***/
/*** WWWWWW IIIIII PPPPPP ***/
/*** WWWWWW IIIIII PPPPPP ***/

import React from "react";
import { useAppSelector } from "../hooks";
import { fieldsSelectors } from "../features/fields/state/fields-slice";
// import { detectionsSelectors } from "../detections/state/detections-slice";
import { useParams } from "react-router-dom";
import TableCozy, { TableColumn, TableOptions } from "./TableCozy";
import { getColorDiseaseIndex, getDetectionStats } from "../helpers/detections";
import { Detection } from "@tornatura/coreapis";

interface DetectionsTableProps {
  detections: Detection[];
  handleHighlightDetection?: (row: { detection?: Detection }) => void;
  handleDeleteDetection?: (row: { detection?: Detection }) => void; // Maybe it can be handeled directly from inside here
}

export function DetectionsTable({
  detections,
  handleHighlightDetection,
  handleDeleteDetection,
}: DetectionsTableProps) {
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );

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
      headerText: "Note",
      id: "notesNum",
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
      id: "action1",
      type: "button",
      style: "danger1",
      buttonText: "Elimina",
      onButtonClick: (data) => {
        if (handleDeleteDetection) {
          handleDeleteDetection(data);
          return;
        }
        console.log("handleDeleteDetection not set", data);
        alert("handleDeleteDetection not set");
      },
    },
    {
      headerText: "",
      id: "action2",
      type: "button",
      style: "secondary",
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
  ];

  const sortedDetections = [...detections].sort((a, b) => a.detectionTime - b.detectionTime);

  const tableData = sortedDetections.map((detection) => {
    const dd = detection.detectionData;
    const ds = getDetectionStats(detection);
    const diseaseIndexColor = getColorDiseaseIndex(ds.diseaseIndex);
    return {
      detection,
      detectionTime:
        new Date(detection.detectionTime).toLocaleDateString() +
        ", " +
        new Date(detection.detectionTime).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      bbch: dd.bbch ?? "-",
      pointsNum: dd.points.length ?? "-",
      infectedPercent: ds.infectedPercentStr,
      statIntensityAvg: ds.intensityAvgStr,
      photosNum: dd.photos && dd.photos.length > 0 ? dd.photos.length : "–",
      notesNum: dd.notes && dd.notes.length > 0 ? "Sì" : "–",
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
