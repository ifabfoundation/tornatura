import { Detection } from "@tornatura/coreapis";
import { useNavigate } from "react-router-dom";
import { useAppSelector } from "../../../hooks";
import { detectionTypesSelectors } from "../state/detection-types-slice";
import { observationTypesSelectors } from "../../observation-types/state/observation-types-slice";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import { dateToString } from "../../../services/utils";
import { GradientLineChart } from "../../../components/GradientLineChart";

function getColor(min: number, max: number, value: number): string {
  // console.log("getColor", { min, max, value });
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

interface DetectionTypeCardProps {
  companyId: string;
  fieldId: string;
  typeId: string;
}

export function DetectionTypeCard({ companyId, fieldId, typeId }: DetectionTypeCardProps) {
  const navigate = useNavigate();

  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionByTypeId(state, typeId ?? "default"),
  );

  const detectionType = useAppSelector((state) =>
    detectionTypesSelectors.selectDetectionTypeById(state, typeId ?? "default"),
  );
  const observationType = useAppSelector((state) =>
    observationTypesSelectors.selectObservationTypeById(state, detectionType.observationTypeId),
  );

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

  const lastDate = detections
    .map((e) => e.detectionTime)
    .sort((a, b) => b - a)
    .reverse()[0];
  const lastDateString = dateToString(lastDate, false);

  return (
    <div className="detection-card">
      <header className="d-flex align-items-start justify-content-between">
        <div>
          <div className="label py-1">Rilevamenti di</div>
          <div className="value">{`${observationType.typology}  ›  ${observationType.method}`}</div>
        </div>
        <button
          className="trnt_btn slim-y outlined narrow-x"
          data-type="rounded"
          onClick={() =>
            navigate(`/companies/${companyId}/fields/${fieldId}/type/${detectionType.id}`, {
              // navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`, {
              state: { typeId: typeId },
            })
          }
        >
          Detail
        </button>
      </header>

      <div className="small-texts d-flex justify-content-between align-items-center mt-4 mb-2">
        <div className="label">{`${detections.length} RILEVAMENT${detections.length !== 1 ? "I" : "O"}`}</div>
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
              state: { typeId: typeId },
            })
          }
        >
          + Rilevamento {observationType.typology}
        </button>
      </div>
    </div>
  );
}
