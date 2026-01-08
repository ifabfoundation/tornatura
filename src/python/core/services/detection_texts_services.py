import datetime
from fastapi import HTTPException, status

from core.decorators import catch_api_exception
from core.models import DetectionText
from core.serializers import DetectionText as DetectionTextSerializer
from core.serializers import DetectionTextCreatePayload, DetectionTextUpdatePayload


class DetectionTextServices:
    model = DetectionText
    serializer = DetectionTextSerializer

    def _serialize(self, obj, many=False):
        """Serialize object(s) to serializer instances."""
        def _create_instance(item: DetectionText) -> DetectionTextSerializer:
            return self.serializer(
                id=str(item.id),
                typology=item.typology,
                method=item.method,
                locationAndScoreInstructions=item.locationAndScoreInstructions,
                bbchInstructions=item.bbchInstructions,
                creationTime=item.creationTime,
            )

        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)

    @catch_api_exception
    def list(self):
        """List detection texts."""
        texts = self.model.objects()
        return self._serialize(texts, many=True)

    @catch_api_exception
    def get(self, detection_text_id: str):
        """Get detection text by ID."""
        detection_text = self.model.objects(id=detection_text_id).first()
        if not detection_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection text not found"
            )
        return self._serialize(detection_text)

    @catch_api_exception
    def create(self, payload: DetectionTextCreatePayload):
        """Create detection text."""
        data = payload.model_dump()
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)
        data.update({
            "creationTime": current_time,
        })
        detection_text = self.model(**data).save()
        return self._serialize(detection_text)

    @catch_api_exception
    def update(self, detection_text_id: str, payload: DetectionTextUpdatePayload):
        """Update detection text."""
        detection_text = self.model.objects(id=detection_text_id).first()
        if not detection_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection text not found"
            )

        if payload.typology is not None:
            detection_text.typology = payload.typology
        if payload.method is not None:
            detection_text.method = payload.method
        if payload.locationAndScoreInstructions is not None:
            detection_text.locationAndScoreInstructions = payload.locationAndScoreInstructions
        if payload.bbchInstructions is not None:
            detection_text.bbchInstructions = payload.bbchInstructions

        detection_text.save()
        return self._serialize(detection_text)

    @catch_api_exception
    def delete(self, detection_text_id: str):
        """Delete detection text."""
        detection_text = self.model.objects(id=detection_text_id).first()
        if not detection_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection text not found"
            )
        detection_text.delete()
        return None
