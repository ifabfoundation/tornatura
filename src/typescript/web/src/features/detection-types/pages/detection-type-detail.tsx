import { useParams, useSearchParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { observationTypesSelectors } from "../../observation-types/state/observation-types-slice";
import { detectionTypesSelectors } from "../state/detection-types-slice";
import { detectionsSelectors } from "../../detections/state/detections-slice";



export function DetectionTypeDetail() {
  const dispatch = useAppDispatch();
  const [searchParams] = useSearchParams();
  const { companyId, fieldId, typeId} = useParams();

  const detectionType = useAppSelector((state) =>
    detectionTypesSelectors.selectDetectionTypeById(state, typeId ?? "default"),
  );

  const observationType = useAppSelector((state) =>
    observationTypesSelectors.selectObservationTypeById(state, detectionType.observationTypeId),
  );

  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionByTypeId(state, typeId ?? "default"),
  );

  return (
    <div>
      <p>pagina per {observationType.typology} / {observationType.method} con numero {detections.length } detections</p>
    </div>
  )
}

