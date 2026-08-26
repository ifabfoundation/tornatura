import datetime
import uuid
from fastapi import HTTPException, status
from bson.errors import InvalidId
from mongoengine.errors import ValidationError as MongoValidationError
from core.decorators import catch_api_exception
from core.models import (
    DetectionData,
    DetectionModel,
    DetectionType as DetectionTypeModel,
    FileInfo,
    ObservationCounter,
    ObservationData,
    ObservationPoint,
    ObservationTreatmentEntry,
    ObservationTreatment,
    Point,
    detectionPhoto,
)
from core.serializers import (
    Detection,
    DetectionMutationPayload,
    DetectionTimeUpdatePayload,
    MultiDetectionMutationPayload,
)
from core.services.agrifields_services import AgriFieldServices
from core.services.files_services import FileServices


# Tolleranza sul futuro per detectionTime. Gli orologi dei telefoni usati in campo sono
# spesso sfasati e un rilevamento vero non deve mai essere rifiutato per qualche minuto:
# rifiutiamo solo cio' che non puo' essere uno scarto d'orologio.
FUTURE_TOLERANCE_MS = 24 * 60 * 60 * 1000


class DetectionServices:
    model = DetectionModel
    serializer = Detection

    def _normalize_treatment_data(self, treatment_data: dict | None) -> dict:
        treatment_data = treatment_data or {}
        treatment_flag = bool(treatment_data.get("treatment", False))
        raw_entries = treatment_data.get("treatments") or []
        normalized_entries = []

        for entry in raw_entries:
            treatment_date = (entry.get("treatmentDate", "") or "").strip()
            treatment_product = (entry.get("treatmentProduct", "") or "").strip()
            if treatment_date == "" and treatment_product == "":
                continue
            normalized_entries.append(
                {
                    "treatmentDate": treatment_date,
                    "treatmentProduct": treatment_product,
                }
            )

        if not normalized_entries:
            legacy_date = (treatment_data.get("treatmentDate", "") or "").strip()
            legacy_product = (treatment_data.get("treatmentProduct", "") or "").strip()
            if legacy_date != "" or legacy_product != "":
                normalized_entries.append(
                    {
                        "treatmentDate": legacy_date,
                        "treatmentProduct": legacy_product,
                    }
                )

        if treatment_flag and not normalized_entries:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one treatment entry is required when treatment is true",
            )

        for entry in normalized_entries:
            if entry["treatmentDate"] == "":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each treatment entry must include a treatmentDate",
                )
            if entry["treatmentProduct"] == "":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each treatment entry must include a treatmentProduct",
                )

        latest_entry = normalized_entries[-1] if normalized_entries else None
        return {
            "treatment": treatment_flag,
            "treatments": normalized_entries if treatment_flag else [],
            "treatmentDate": latest_entry["treatmentDate"] if latest_entry and treatment_flag else "",
            "treatmentProduct": latest_entry["treatmentProduct"] if latest_entry and treatment_flag else "",
        }
    
    def _serialize(self, obj, many=False):
        """Serialize object(s) to serializer instances
        
        Args:
            obj: Object or list of objects to serialize
            many: If True, treats obj as a list of objects
            
        Returns:
            Serializer instance or list of serializer instances
        """
        file_services = FileServices()
        agrifield_services = AgriFieldServices()
       
        def _create_instance(item) -> Detection:
            agrifield = agrifield_services.get(item.agrifieldId)
            treatment = item.detectionData.treatment or ObservationTreatment()
            serialized_treatment = self._normalize_treatment_data(
                {
                    "treatment": treatment.treatment,
                    "treatments": [
                        {
                            "treatmentDate": entry.treatmentDate,
                            "treatmentProduct": entry.treatmentProduct,
                        }
                        for entry in getattr(treatment, "treatments", [])
                    ],
                    "treatmentDate": treatment.treatmentDate,
                    "treatmentProduct": treatment.treatmentProduct,
                }
            )
            points = []
            for point in item.detectionData.points:
                points.append(
                    {
                        "position": {
                            "lng": point.position.lng,
                            "lat": point.position.lat,
                        },
                        "data": {
                            "rangeValue": point.data.rangeValue,
                            "counters": [
                                {
                                    "counterName": counter.counterName,
                                    "counterValue": counter.counterValue,
                                }
                                for counter in point.data.counters
                            ],
                        }
                    }
                )

            return self.serializer(
                id=str(item.id),
                agrifieldId=item.agrifieldId,
                sessionId=getattr(item, "sessionId", None),
                detectionTime=item.detectionTime if item.detectionTime else item.creationTime,
                detectionTypeId=item.detectionTypeId,
                detectionData={
                    "bbch": item.detectionData.bbch,
                    "notes": item.detectionData.notes,
                    "treatment": serialized_treatment,
                    "photos": [
                        {
                            "caption": photo.caption,
                            "url": file_services.get_file_url(
                                agrifield.orgId,
                                photo.photo.category,
                                photo.photo.name,
                            ),
                            "position": {
                                "lng": photo.position.lng,
                                "lat": photo.position.lat,
                            } if photo.position else None,
                        }
                        for photo in item.detectionData.photos
                    ],
                    "points": points,
                },
                creationTime=item.creationTime,
                lastUpdateTime=item.lastUpdateTime,
            )
            
        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)

    def _build_detection_data(self, detection_data: dict) -> DetectionData:
        treatment_data = self._normalize_treatment_data(detection_data.get("treatment", {}))
        points = []
        for point in detection_data.get("points", []):
            observation = point.get("data", {})
            counters = [
                ObservationCounter(**counter)
                for counter in observation.get("counters", [])
            ]
            observation_doc = ObservationData(
                rangeValue=observation.get("rangeValue"),
                counters=counters,
            )
            points.append(
                ObservationPoint(
                    position=Point(**point.get("position")),
                    data=observation_doc,
                )
            )

        photos = []
        for photo in detection_data.get("photos", []):
            position = photo.get("position")
            photos.append(
                detectionPhoto(
                    caption=photo.get("caption", ""),
                    photo=FileInfo(**photo.get("photo")),
                    position=Point(**position) if position else None,
                )
            )

        return DetectionData(
            bbch=detection_data.get("bbch", ""),
            notes=detection_data.get("notes", ""),
            treatment=ObservationTreatment(
                treatment=treatment_data["treatment"],
                treatments=[
                    ObservationTreatmentEntry(**entry)
                    for entry in treatment_data["treatments"]
                ],
                treatmentDate=treatment_data["treatmentDate"],
                treatmentProduct=treatment_data["treatmentProduct"],
            ),
            photos=photos,
            points=points,
        )

    def _validate_detection_type(self, agrifield_id: str, detection_type_id: str):
        detection_type = DetectionTypeModel.objects(id=detection_type_id).first()
        if detection_type is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Detection type not found: {detection_type_id}"
            )
        if detection_type.agrifieldId != agrifield_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Detection type does not belong to this agrifield"
            )
        return detection_type
    
    @catch_api_exception
    def list(self, agrifield_id: str, detection_type_id: str | None = None):
        """List detections for an agricultural field
        
        Args:
            agrifield_id: ID of the agricultural field
            detection_type_id: Optional detection type ID filter
            
        Returns:
            serialized detections
        """
        query = {"agrifieldId": agrifield_id, "deleted": False}
        if detection_type_id:
            query["detectionTypeId"] = detection_type_id
        detections = self.model.objects(**query)
        return self._serialize(detections, many=True)
    
    @catch_api_exception
    def create(self, agrifield_id: str, payload: DetectionMutationPayload, user_id: str):
        """Create detection
        
        Args:
            agrifield_id: ID of the agricultural field
            payload: Detection creation data
            
        Returns:
            Serialized created detection
        """
        data = payload.model_dump()
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)
        self._validate_detection_type(agrifield_id, data["detectionTypeId"])

        detection = self.model(
            agrifieldId=agrifield_id,
            detectionTime=data["detectionTime"],
            detectionTypeId=data["detectionTypeId"],
            detectionData=self._build_detection_data(data["detectionData"]),
            createdBy=user_id,
            creationTime=current_time,
            lastUpdateTime=current_time,
        ).save()
        return self._serialize(detection)

    @catch_api_exception
    def create_bulk(self, agrifield_id: str, payload: MultiDetectionMutationPayload, user_id: str):
        data = payload.model_dump()
        entries = data["entries"]
        if not entries:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one detection entry is required"
            )

        detection_type_ids = [entry["detectionTypeId"] for entry in entries]
        if len(set(detection_type_ids)) != len(detection_type_ids):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate detection types are not allowed in the same session"
            )

        for detection_type_id in detection_type_ids:
            self._validate_detection_type(agrifield_id, detection_type_id)

        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)
        session_id = uuid.uuid4().hex
        created_detections = []

        for entry in entries:
            detection_data = {
                "bbch": data["bbch"],
                "notes": entry["notes"],
                "treatment": data.get("treatment", {}),
                "photos": entry["photos"],
                "points": entry["points"],
            }
            detection = self.model(
                agrifieldId=agrifield_id,
                sessionId=session_id,
                detectionTime=data["detectionTime"],
                detectionTypeId=entry["detectionTypeId"],
                detectionData=self._build_detection_data(detection_data),
                createdBy=user_id,
                creationTime=current_time,
                lastUpdateTime=current_time,
            ).save()
            created_detections.append(detection)

        return {
            "sessionId": session_id,
            "detections": self._serialize(created_detections, many=True),
        }
    
    @catch_api_exception
    def get(self, detection_id: str):
        """Get detection by ID
        
        Args:
            detection_id: ID of the detcetion
            
        Returns:
            Serialized detection
        """
        detection = self.model.objects(id=detection_id, deleted=False).first()
        if not detection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection not found"
            )
        return self._serialize(detection)
    
    @catch_api_exception
    def update_time(
        self, agrifield_id: str, detection_id: str, payload: DetectionTimeUpdatePayload
    ):
        """Correct when a detection was made.

        `creationTime` is deliberately left untouched: it stays the record of when the
        detection entered the system, so the original information is never lost.

        When the detection belongs to a multi-detection session, every member moves
        together. `create_bulk` writes a single detectionTime for the whole session, so
        moving one member alone would produce a state the app cannot create.

        Args:
            agrifield_id: ID of the agricultural field the detection must belong to
            detection_id: ID of the detection to correct
            payload: the new detectionTime, in milliseconds

        Returns:
            dict with the session ID (if any) and the serialized updated detections
        """
        try:
            detection = self.model.objects(id=detection_id, deleted=False).first()
        except (InvalidId, MongoValidationError):
            # Un id malformato non puo' corrispondere a nulla: la risposta onesta e' 404.
            # Senza questo, mongoengine solleva e handle_api_exceptions restituisce 500.
            detection = None
        if not detection or detection.agrifieldId != agrifield_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection not found"
            )

        new_time = payload.detectionTime
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)
        if new_time <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid detection time"
            )
        if new_time > current_time + FUTURE_TOLERANCE_MS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Detection time cannot be in the future"
            )

        session_id = detection.sessionId or None
        if session_id:
            # Filtriamo anche per agrifieldId: una sessione nasce sempre su un solo campo
            # (create_bulk ne riceve uno), e cosi' non possiamo toccare dati di altri campi.
            targets = list(
                self.model.objects(
                    sessionId=session_id, agrifieldId=agrifield_id, deleted=False
                )
            )
        else:
            targets = [detection]

        for target in targets:
            target.detectionTime = new_time
            target.lastUpdateTime = current_time
            target.save()

        return {
            "sessionId": session_id,
            "detections": self._serialize(targets, many=True),
        }

    @catch_api_exception
    def delete(self, detection_id: str):
        """Soft delete detection
        
        Args:
            detection_id: ID of the detection
            
        Returns:
            None
        """
        detection = self.model.objects(id=detection_id, deleted=False).first()
        if not detection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection not found"
            )
        
        detection.deleted = True
        detection.save()
        
        return None
        
    def __repr__(self):
        return f"DetectionServices(model={self.model.__name__})"
    
