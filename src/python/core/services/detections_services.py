import datetime
from fastapi import HTTPException, status
from core.decorators import catch_api_exception
from core.models import DetectionModel
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
            return self.serializer(
                id=str(item.id),
                agrifieldId=item.agrifieldId,
                type=item.type, 
                position={
                    "lng": item.position.lng,
                    "lat": item.position.lat
                },
                photos=[file_services.get_file_url(agrifield.orgId, photo.category, photo.name) for photo in item.photos],
                note=item.note,
                details=item.details,
                creationTime=item.creationTime,
                lastUpdateTime=item.lastUpdateTime
            )
            
        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)
    
    @catch_api_exception
    def list(self, agrifield_id: str):
        """List detections for an agricultural field
        
        Args:
            agrifield_id: ID of the agricultural field
            
        Returns:
            serialized detections
        """
        detections = self.model.objects(agrifieldId=agrifield_id, deleted=False)
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

        data.update({
            "agrifieldId": agrifield_id,
            "creationTime": current_time,
            "lastUpdateTime": current_time
        })

        detection = self.model(**data).save()
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
    def update(self, detection_id: str, payload: DetectionMutationPayload):
        """Update detection
        
        Args:
            detection_id: ID of the detection
            payload: Detection update data
            
        Returns:
            Serialized updated detection
        """
        detection = self.model.objects(id=detection_id, deleted=False).first()
        if not detection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection not found"
            )
        
        data = payload.model_dump()
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)
        
        detection.type = data["type"]
        detection.note = data["note"]
        detection.position = data["position"]
        detection.photos = data["photos"]
        detection.details = data["details"]
        detection.lastUpdateTime = current_time
        detection.save()
        
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
    