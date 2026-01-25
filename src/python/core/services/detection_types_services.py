import datetime
from fastapi import HTTPException, status

from core.decorators import catch_api_exception
from core.models import DetectionType, ObservationType
from core.serializers import DetectionType as DetectionTypeSerializer
from core.serializers import DetectionTypeCreatePayload, DetectionTypeUpdatePayload


class DetectionTypeServices:
    model = DetectionType
    serializer = DetectionTypeSerializer

    def _serialize(self, obj, many=False):
        """Serialize object(s) to serializer instances."""
        def _create_instance(item: DetectionType) -> DetectionTypeSerializer:
            return self.serializer(
                id=str(item.id),
                agrifieldId=item.agrifieldId,
                observationTypeId=item.observationTypeId,
                creationTime=item.creationTime,
            )

        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)

    @catch_api_exception
    def list(self, agrifield_id: str):
        """List detection types for an agrifield."""
        types = self.model.objects(agrifieldId=agrifield_id)
        return self._serialize(types, many=True)

    @catch_api_exception
    def get(self, detection_type_id: str):
        """Get detection type by ID."""
        detection_type = self.model.objects(id=detection_type_id).first()
        if not detection_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection type not found"
            )
        return self._serialize(detection_type)

    @catch_api_exception
    def create(self, agrifield_id: str, payload: DetectionTypeCreatePayload):
        """Create detection type."""
        data = payload.model_dump()
        observation_type = ObservationType.objects(id=data["observationTypeId"]).first()
        if not observation_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Observation type not found"
            )
        existing_type = self.model.objects(
            agrifieldId=agrifield_id,
            observationTypeId=data["observationTypeId"],
        ).first()
        if existing_type:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Detection type already exists for this agrifield and observation type"
            )
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)
        data.update({
            "agrifieldId": agrifield_id,
            "creationTime": current_time,
        })
        detection_type = self.model(**data).save()
        return self._serialize(detection_type)

    @catch_api_exception
    def update(self, detection_type_id: str, payload: DetectionTypeUpdatePayload):
        """Update detection type."""
        detection_type = self.model.objects(id=detection_type_id).first()
        if not detection_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection type not found"
            )

        if payload.observationTypeId is not None:
            observation_type = ObservationType.objects(id=payload.observationTypeId).first()
            if not observation_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Observation type not found"
                )
            existing_type = self.model.objects(
                agrifieldId=detection_type.agrifieldId,
                observationTypeId=payload.observationTypeId,
                id__ne=detection_type_id,
            ).first()
            if existing_type:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Detection type already exists for this agrifield and observation type"
                )
            detection_type.observationTypeId = payload.observationTypeId
        detection_type.save()
        return self._serialize(detection_type)

    @catch_api_exception
    def delete(self, detection_type_id: str):
        """Delete detection type."""
        detection_type = self.model.objects(id=detection_type_id).first()
        if not detection_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection type not found"
            )
        detection_type.delete()
        return None
