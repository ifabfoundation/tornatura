import datetime
from fastapi import HTTPException, status

from core.decorators import catch_api_exception
from core.models import ObservationType
from core.serializers import ObservationType as ObservationTypeSerializer
from core.serializers import ObservationTypeCreatePayload, ObservationTypeUpdatePayload


class ObservationTypeServices:
    model = ObservationType
    serializer = ObservationTypeSerializer

    def _serialize(self, obj, many=False):
        """Serialize object(s) to serializer instances."""
        def _create_instance(item: ObservationType) -> ObservationTypeSerializer:
            return self.serializer(
                id=str(item.id),
                typology=item.typology,
                method=item.method,
                category=item.category,
                locationAndScoreInstructions=item.locationAndScoreInstructions,
                bchInstructions=item.bchInstructions,
                observationType=item.observationType,
                rangeMin=item.rangeMin,
                rangeMax=item.rangeMax,
                counters=item.counters,
                creationTime=item.creationTime,
            )

        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)

    @catch_api_exception
    def list(self):
        """List observation types."""
        types = self.model.objects()
        return self._serialize(types, many=True)

    @catch_api_exception
    def get(self, observation_type_id: str):
        """Get observation type by ID."""
        observation_type = self.model.objects(id=observation_type_id).first()
        if not observation_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Observation type not found"
            )
        return self._serialize(observation_type)

    @catch_api_exception
    def create(self, payload: ObservationTypeCreatePayload):
        """Create observation type."""
        data = payload.model_dump()
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)
        data.update({
            "creationTime": current_time,
        })
        observation_type = self.model(**data).save()
        return self._serialize(observation_type)

    @catch_api_exception
    def update(self, observation_type_id: str, payload: ObservationTypeUpdatePayload):
        """Update observation type."""
        observation_type = self.model.objects(id=observation_type_id).first()
        if not observation_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Observation type not found"
            )

        if payload.typology is not None:
            observation_type.typology = payload.typology
        if payload.method is not None:
            observation_type.method = payload.method
        if payload.category is not None:
            observation_type.category = payload.category
        if payload.locationAndScoreInstructions is not None:
            observation_type.locationAndScoreInstructions = payload.locationAndScoreInstructions
        if payload.bchInstructions is not None:
            observation_type.bchInstructions = payload.bchInstructions
        if payload.observationType is not None:
            observation_type.observationType = payload.observationType
        if payload.rangeMin is not None:
            observation_type.rangeMin = payload.rangeMin
        if payload.rangeMax is not None:
            observation_type.rangeMax = payload.rangeMax
        if payload.counters is not None:
            observation_type.counters = payload.counters

        observation_type.save()
        return self._serialize(observation_type)

    @catch_api_exception
    def delete(self, observation_type_id: str):
        """Delete observation type."""
        observation_type = self.model.objects(id=observation_type_id).first()
        if not observation_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Observation type not found"
            )
        observation_type.delete()
        return None
