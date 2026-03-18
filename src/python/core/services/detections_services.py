import datetime
from fastapi import HTTPException, status
from core.decorators import catch_api_exception
from core.models import (
    DetectionData,
    DetectionModel,
    DetectionType as DetectionTypeModel,
    FileInfo,
    ObservationCounter,
    ObservationData,
    ObservationPoint,
    ObservationTreatment,
    Point,
    detectionPhoto,
)
from core.serializers import Detection, DetectionMutationPayload
from core.services.agrifields_services import AgriFieldServices
from core.services.files_services import FileServices


class DetectionServices:
    model = DetectionModel
    serializer = Detection
    
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
                detectionTime=item.detectionTime if item.detectionTime else item.creationTime,
                detectionTypeId=item.detectionTypeId,
                detectionData={
                    "bbch": item.detectionData.bbch,
                    "notes": item.detectionData.notes,
                    "treatment": {
                        "treatment": treatment.treatment,
                        "treatmentDate": treatment.treatmentDate,
                        "treatmentProduct": treatment.treatmentProduct,
                    },
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
    def create(self, agrifield_id: str, payload: DetectionMutationPayload):
        """Create detection
        
        Args:
            agrifield_id: ID of the agricultural field
            payload: Detection creation data
            
        Returns:
            Serialized created detection
        """
        data = payload.model_dump()
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)

        detection_type = DetectionTypeModel.objects(id=data["detectionTypeId"]).first()
        if detection_type is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection type not found"
            )
        if detection_type.agrifieldId != agrifield_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Detection type does not belong to this agrifield"
            )

        detection_data = data["detectionData"]
        treatment_data = detection_data.get("treatment", {})
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

        detection = self.model(
            agrifieldId=agrifield_id,
            detectionTime=data["detectionTime"],
            detectionTypeId=data["detectionTypeId"],
            detectionData=DetectionData(
                bbch=detection_data.get("bbch", ""),
                notes=detection_data.get("notes", ""),
                treatment=ObservationTreatment(**treatment_data),
                photos=photos,
                points=points,
            ),
            creationTime=current_time,
            lastUpdateTime=current_time,
        ).save()
        return self._serialize(detection)
    
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
    
