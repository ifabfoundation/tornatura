import React from "react";
import { useNavigate } from "react-router-dom";
import { useAppSelector } from "../../../hooks";
import { detectionTypesSelectors } from "../state/detection-types-slice";
import { observationTypesSelectors } from "../../observation-types/state/observation-types-slice";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import { dateToString } from "../../../services/utils";
import { GradientLineChart } from "../../../components/GradientLineChart";
import { getDetectionStats } from "../../../helpers/detections";
import LineChartVisx from "../../../components/LineChartVisx";
import { mapValues } from "../../../helpers/common";

function getColor(min: number, max: number, value: number): string {
  const colors = ["#42C318", "#FFB290", "#FF4D4D", "#A10505"];
  const range = max - min;
  const segment = range / colors.length;
  const index = Math.min(colors.length - 1, Math.floor((value - min) / segment));
  return colors[index];
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

  // --- Calculate group stats

  const groupStats = {
    groupMin: Infinity,
    groupMax: -Infinity,
  };
  detections.forEach((detection) => {
    const ds = getDetectionStats(detection);
    groupStats.groupMin = Math.min(groupStats.groupMin, ds.pointsMin);
    groupStats.groupMax = Math.max(groupStats.groupMax, ds.pointsMax);
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
  const graphDataVisx = detections
    .map((detection, index, a) => {
      const ds = getDetectionStats(detection);
      return {
        id: detection.id,
        // Linear time mapping
        // x: new Date(detection.detectionTime),
        // Sequential time mapping (better for debugging)
        x: new Date(
          mapValues(index, a.length, 0, a[0].detectionTime, a[a.length - 1].detectionTime),
        ),
        y: ds.pointsAvg,
        color: getColor(groupStats.groupMin, groupStats.groupMax, ds.pointsAvg),
        detection: detection,
        displayValue: ds.displayValue,
        displayLabel: ds.displayLabel,
      };
    })
    .sort((a, b) => a.x.getTime() - b.x.getTime());

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
          className="trnt_btn slim-y primary outlined narrow-x px-3 type-rounded"
          data-type="rounded"
          onClick={() =>
            navigate(`/companies/${companyId}/fields/${fieldId}/type/${detectionType.id}`, {
              // navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`, {
              state: { typeId: typeId },
            })
          }
        >
          Espandi
          {/* <Icon iconName={"enlarge"} color={"black"} /> */}
        </button>
      </header>

      <div className="small-texts d-flex justify-content-between align-items-center mt-4 mb-2">
        <div className="label">{`${detections.length} RILEVAMENT${detections.length !== 1 ? "I" : "O"}`}</div>
        <div className="label">{`AGGIORNATO IL ${lastDateString}`}</div>
      </div>

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
          height={100}
          data={graphDataVisx}
          onSelectPoint={undefined}
          selectedId={undefined}
        />
      </div>

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
