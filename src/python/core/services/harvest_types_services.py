import datetime
import re
from typing import Optional

from fastapi import HTTPException, status

from core.decorators import catch_api_exception
from core.models import AgriFieldModel, HarvestType, ObservationType
from core.serializers import (
    HarvestType as HarvestTypeSerializer,
    HarvestTypeCreatePayload,
    HarvestTypeUpdatePayload,
)


HARVEST_CODE_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")

def normalize_harvest_code(value: str) -> str:
    normalized = (value or "").strip().lower()
    return normalized


def validate_harvest_code_format(value: str) -> str:
    normalized = normalize_harvest_code(value)
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_harvest_code",
                "message": "Harvest code is required",
            },
        )
    if not HARVEST_CODE_PATTERN.match(normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_harvest_code",
                "message": "Harvest code must be lowercase and use underscores only",
                "harvest": normalized,
            },
        )
    return normalized


def deduplicate_harvest_codes(values: list[str]) -> list[str]:
    deduplicated: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = validate_harvest_code_format(value)
        if normalized not in seen:
            seen.add(normalized)
            deduplicated.append(normalized)
    return deduplicated


def get_harvest_type_or_400(harvest_code: str) -> HarvestType:
    exact_match = HarvestType.objects(code=harvest_code).first()
    if exact_match:
        return exact_match

    normalized = validate_harvest_code_format(harvest_code)
    harvest_type = HarvestType.objects(code=normalized).first()
    if not harvest_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "unknown_harvest_code",
                "message": "Harvest code is not supported by the registry",
                "harvest": normalized,
            },
        )
    return harvest_type


def validate_supported_harvest_codes(values: list[str]) -> list[str]:
    normalized_codes = deduplicate_harvest_codes(values)
    if not normalized_codes:
        return []

    existing_codes = {
        harvest_type.code
        for harvest_type in HarvestType.objects(code__in=normalized_codes)
    }
    missing_codes = [code for code in normalized_codes if code not in existing_codes]
    if missing_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "unknown_supported_harvest_codes",
                "message": "Every supported harvest code must exist in the harvest registry",
                "missingHarvestCodes": missing_codes,
            },
        )
    return normalized_codes


class HarvestTypeServices:
    model = HarvestType
    serializer = HarvestTypeSerializer

    def _serialize(self, obj, many: bool = False):
        def _create_instance(item: HarvestType) -> HarvestTypeSerializer:
            return self.serializer(
                id=str(item.id),
                code=item.code,
                label=item.label,
                active=item.active,
                sortOrder=item.sortOrder,
                creationTime=item.creationTime,
                lastUpdateTime=item.lastUpdateTime,
            )

        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)

    @catch_api_exception
    def list(self, active: Optional[bool] = None, include_inactive: bool = False):
        query = {}
        if active is not None:
            query["active"] = active
        elif not include_inactive:
            query["active"] = True
        harvest_types = self.model.objects(**query)
        return self._serialize(harvest_types, many=True)

    @catch_api_exception
    def get(self, harvest_type_id: str):
        harvest_type = self.model.objects(id=harvest_type_id).first()
        if not harvest_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Harvest type not found",
            )
        return self._serialize(harvest_type)

    @catch_api_exception
    def create(self, payload: HarvestTypeCreatePayload):
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)
        code = validate_harvest_code_format(payload.code)
        if self.model.objects(code=code).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Harvest type code already exists",
            )
        harvest_type = self.model(
            code=code,
            label=payload.label.strip(),
            active=payload.active,
            sortOrder=payload.sortOrder,
            creationTime=current_time,
            lastUpdateTime=current_time,
        ).save()
        return self._serialize(harvest_type)

    @catch_api_exception
    def update(self, harvest_type_id: str, payload: HarvestTypeUpdatePayload):
        harvest_type = self.model.objects(id=harvest_type_id).first()
        if not harvest_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Harvest type not found",
            )

        if payload.code is not None:
            updated_code = validate_harvest_code_format(payload.code)
            if updated_code != harvest_type.code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "harvest_code_immutable",
                        "message": "Harvest code is stable and cannot be changed",
                    },
                )
        if payload.label is not None:
            harvest_type.label = payload.label.strip()
        if payload.active is not None:
            harvest_type.active = payload.active
        if payload.sortOrder is not None:
            harvest_type.sortOrder = payload.sortOrder

        harvest_type.lastUpdateTime = int(
            datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000
        )
        harvest_type.save()
        return self._serialize(harvest_type)

    @catch_api_exception
    def delete(self, harvest_type_id: str):
        harvest_type = self.model.objects(id=harvest_type_id).first()
        if not harvest_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Harvest type not found",
            )

        agrifield_references = AgriFieldModel.objects(harvest=harvest_type.code, deleted=False).count()
        observation_type_references = ObservationType.objects(
            supportedHarvestCodes=harvest_type.code
        ).count()
        if agrifield_references or observation_type_references:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "harvest_type_in_use",
                    "message": "Harvest type cannot be deleted because it is in use",
                    "references": {
                        "agrifields": agrifield_references,
                        "observationTypes": observation_type_references,
                    },
                },
            )

        harvest_type.delete()
        return None
