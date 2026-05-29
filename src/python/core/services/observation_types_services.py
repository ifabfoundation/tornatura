import datetime
from fastapi import HTTPException, status

from core.decorators import catch_api_exception
from core.models import ObservationType
from core.services.harvest_types_services import (
    get_harvest_type_or_400,
    validate_supported_harvest_codes,
)
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
                observationHint=item.observationHint,
                observationType=item.observationType,
                rangeMin=item.rangeMin,
                rangeMax=item.rangeMax,
                rangeLabels=item.rangeLabels,
                counters=item.counters,
                supportedHarvestCodes=item.supportedHarvestCodes,
                creationTime=item.creationTime,
            )

        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)

    @catch_api_exception
    def list(self, harvest: str | None = None):
        """List observation types."""
        query = {}
        if harvest is not None:
            harvest_type = get_harvest_type_or_400(harvest)
            query["supportedHarvestCodes"] = harvest_type.code
        types = self.model.objects(**query)
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
        data["supportedHarvestCodes"] = validate_supported_harvest_codes(
            data.get("supportedHarvestCodes", [])
        )
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
        if payload.observationHint is not None:
            observation_type.observationHint = payload.observationHint
        if payload.observationType is not None:
            observation_type.observationType = payload.observationType
        if payload.rangeMin is not None:
            observation_type.rangeMin = payload.rangeMin
        if payload.rangeMax is not None:
            observation_type.rangeMax = payload.rangeMax
        if payload.rangeLabels is not None:
            observation_type.rangeLabels = payload.rangeLabels
        if payload.counters is not None:
            observation_type.counters = payload.counters
        if payload.supportedHarvestCodes is not None:
            observation_type.supportedHarvestCodes = validate_supported_harvest_codes(
                payload.supportedHarvestCodes
            )

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
