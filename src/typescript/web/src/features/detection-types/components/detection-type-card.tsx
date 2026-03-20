import React from "react";
import { useNavigate } from "react-router-dom";
import { useAppSelector } from "../../../hooks";
import { detectionTypesSelectors } from "../state/detection-types-slice";
import { observationTypesSelectors } from "../../observation-types/state/observation-types-slice";
import { detectionsSelectors } from "../../detections/state/detections-slice";

import { getColorDiseaseIndex, getDetectionStats } from "../../../helpers/detections";
import LineChartVisx from "../../../components/LineChartVisx";
import { mapValues } from "../../../helpers/common";
import Icon from "../../../components/Icon";

export function getColor(min: number, max: number, value: number): string {
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
  const sortedDetections = [...detections].sort((a, b) => b.detectionTime - a.detectionTime);

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
  sortedDetections.forEach((detection) => {
    const ds = getDetectionStats(detection);
    groupStats.groupMin = Math.min(groupStats.groupMin, ds.pointsMin);
    groupStats.groupMax = Math.max(groupStats.groupMax, ds.pointsMax);
  });

  const graphDataVisx = sortedDetections.map((detection, index, a) => {
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
        observationType.observationType === "range"
          ? getColorDiseaseIndex(ds.diseaseIndex)
          : "white",
      detection: detection,
      displayValue: ds.displayValue,
      displayLabel: ds.displayLabel,
    };
  });
  // .sort((a, b) => a.x.getTime() - b.x.getTime());

  /*const lastDate = sortedDetections
    .map((e) => e.detectionTime)
    .sort((a, b) => b - a)
    .reverse()[0];*/
  // const lastDateString = dateToString(lastDate, false);

  type NewDetectionButtonProps = {
    className?: string;
  };
  function NewDetectionButton({ className }: NewDetectionButtonProps) {
    return (
      <button
        className={"trnt_btn accent type-rounded" + (className ? " " + className : "")}
        onClick={() =>
          navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`, {
            state: { typeId: typeId },
          })
        }
      >
        <span className="font-m-600">+&nbsp;Rilevamento {observationType.typology}</span>
      </button>
    );
  }
  type OpenDetailButtonProps = {
    className?: string;
  };
  function OpenDetailButton({ className }: OpenDetailButtonProps) {
    return (
      <button
        className={"trnt_btn primary ps-lg-4 type-rounded" + (className ? " " + className : "")}
        onClick={() =>
          navigate(`/companies/${companyId}/fields/${fieldId}/type/${detectionType.id}`, {
            state: { typeId: typeId },
          })
        }
      >
        {"Espandi"}
        <span className="ms-1 mt-1 me-0">
          <Icon iconName={"fullscreen"} color={"white"} />
        </span>
      </button>
    );
  }
  return (
    <div className="detection-card">
      <header className="d-flex align-items-start justify-content-between flex-wrap">
        <div>
          {/* <div className="label py-1">Rilevamenti di</div> */}
          <a
            className="font-l-600 color-black no-u pointer d-inline-block me-4 mb-2"
            onClick={() =>
              navigate(`/companies/${companyId}/fields/${fieldId}/type/${detectionType.id}`, {
                // navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`, {
                state: { typeId: typeId },
              })
            }
          >{`${observationType.typology}  ›  ${observationType.method}`}</a>
          {/* <br />
          <button
            className="trnt_btn slim-y primary narrow-x px-3 mt-2 type-rounded"
            style={{ marginLeft: "-5px" }}
            // data-type="rounded"
            onClick={() =>
              navigate(`/companies/${companyId}/fields/${fieldId}/type/${detectionType.id}`, {
                // navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`, {
                state: { typeId: typeId },
              })
            }
          >
            {"Dettaglio →"}
          </button> */}
        </div>
        <div className="d-none d-md-block" style={{ marginLeft: "-7px" }}>
          <OpenDetailButton />
          <NewDetectionButton />
        </div>
      </header>

      <div className="spacer py-2"></div>

      {/*  
      <div className="small-texts d-flex justify-content-between align-items-center mt-4 mb-2">
        <div className="label">{`${detections.length} RILEVAMENT${detections.length !== 1 ? "I" : "O"}`}</div>
        <div className="label">{`AGGIORNATO IL ${lastDateString}`}</div>
      </div>
        */}

      <div ref={containerRef} className="bg-grey_1 rounded-visible">
        <div className="p-3 font-s-600">
          {detections.length == 1 && "1 rilevamento"}
          {detections.length > 1 && `${detections.length} rilevamenti`}

          {/* <div className="label">{`${detections.length} RILEVAMENT${detections.length !== 1 ? "I" : "O"}`}</div> */}
        </div>
        <LineChartVisx
          width={containerWidth}
          height={200}
          data={graphDataVisx}
          onSelectPoint={undefined}
          gradients={observationType?.typology === "Peronospora"}
          selectedId={undefined}
        />
      </div>

      <div className="d-md-none mt-3 pt-1 d-flex align-items-center justify-content-stretch">
        <OpenDetailButton className="w-50 px-0" />
        <NewDetectionButton className="w-50" />
      </div>
    </div>
  );
}
