import copy
import datetime

from fastapi import HTTPException, status

from core.decorators import catch_api_exception
from core.models import BbchGroup, BbchScale, BbchStage
from core.serializers import (
    BbchScale as BbchScaleSerializer,
    BbchScaleCreatePayload,
    BbchScaleUpdatePayload,
)
from core.services.harvest_types_services import get_harvest_type_or_400


def _now_ms() -> int:
    return int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)


class BbchScaleServices:
    model = BbchScale

    def _groups_from_payload(self, groups):
        group_codes: set[str] = set()
        result = []
        for group in groups:
            group_code = group.code.strip()
            group_name = group.name.strip()
            if not group_code or not group_name or group_code in group_codes:
                raise HTTPException(status_code=400, detail="BBCH group codes and names must be unique and non-empty")
            group_codes.add(group_code)
            stage_codes: set[str] = set()
            for stage in group.stages:
                stage.code = stage.code.strip()
                stage.name = stage.name.strip()
                if not stage.code or not stage.name or stage.code in stage_codes:
                    raise HTTPException(status_code=400, detail=f"Invalid or duplicate BBCH stage in group {group_code}")
                stage_codes.add(stage.code)
            stages = [BbchStage(**stage.model_dump()) for stage in group.stages]
            data = group.model_dump(exclude={"stages"})
            data["code"] = group_code
            data["name"] = group_name
            result.append(BbchGroup(**data, stages=stages))
        return result

    def _resolve_groups(self, scale: BbchScale, visited: set[str] | None = None):
        visited = visited or set()
        if scale.harvestCode in visited:
            raise HTTPException(status_code=409, detail="Circular BBCH scale reference")
        visited.add(scale.harvestCode)
        if not scale.sourceHarvestCode:
            return scale.groups
        source = self.model.objects(harvestCode=scale.sourceHarvestCode).first()
        if not source:
            raise HTTPException(status_code=409, detail="Referenced BBCH scale does not exist")
        return self._resolve_groups(source, visited)

    def _serialize(self, scale: BbchScale, resolve: bool = True):
        groups = self._resolve_groups(scale) if resolve else scale.groups
        return BbchScaleSerializer(
            id=str(scale.id),
            harvestCode=scale.harvestCode,
            sourceHarvestCode=scale.sourceHarvestCode,
            groups=[
                {
                    "code": group.code,
                    "name": group.name,
                    "icon": group.icon,
                    "sortOrder": group.sortOrder,
                    "stages": [
                        {
                            "code": stage.code,
                            "name": stage.name,
                            "thumbnail": stage.thumbnail,
                            "icon": stage.icon,
                            "sortOrder": stage.sortOrder,
                        }
                        for stage in group.stages
                    ],
                }
                for group in groups
            ],
            creationTime=scale.creationTime,
            lastUpdateTime=scale.lastUpdateTime,
        )

    @catch_api_exception
    def list(self):
        return [self._serialize(scale) for scale in self.model.objects()]

    @catch_api_exception
    def get(self, harvest_code: str):
        scale = self.model.objects(harvestCode=harvest_code).first()
        if not scale:
            raise HTTPException(status_code=404, detail="BBCH scale not found")
        return self._serialize(scale)

    @catch_api_exception
    def create(self, payload: BbchScaleCreatePayload):
        harvest = get_harvest_type_or_400(payload.harvestCode)
        if self.model.objects(harvestCode=harvest.code).first():
            raise HTTPException(status_code=409, detail="BBCH scale already exists")
        source_code = payload.sourceHarvestCode
        if source_code:
            get_harvest_type_or_400(source_code)
            if source_code == harvest.code or not self.model.objects(harvestCode=source_code).first():
                raise HTTPException(status_code=400, detail="Invalid BBCH source scale")
        now = _now_ms()
        scale = self.model(
            harvestCode=harvest.code,
            sourceHarvestCode=source_code,
            groups=[] if source_code else self._groups_from_payload(payload.groups),
            creationTime=now,
            lastUpdateTime=now,
        ).save()
        return self._serialize(scale)

    @catch_api_exception
    def update(self, harvest_code: str, payload: BbchScaleUpdatePayload):
        scale = self.model.objects(harvestCode=harvest_code).first()
        if not scale:
            raise HTTPException(status_code=404, detail="BBCH scale not found")
        if payload.groups is not None:
            scale.groups = self._groups_from_payload(payload.groups)
            scale.sourceHarvestCode = None
        elif payload.sourceHarvestCode is not None:
            source_code = payload.sourceHarvestCode or None
            if source_code:
                get_harvest_type_or_400(source_code)
                if source_code == harvest_code or not self.model.objects(harvestCode=source_code).first():
                    raise HTTPException(status_code=400, detail="Invalid BBCH source scale")
            scale.sourceHarvestCode = source_code
            if source_code:
                scale.groups = []
        scale.lastUpdateTime = _now_ms()
        scale.save()
        return self._serialize(scale)

    @catch_api_exception
    def duplicate(self, source_harvest_code: str, target_harvest_code: str):
        source = self.model.objects(harvestCode=source_harvest_code).first()
        if not source:
            raise HTTPException(status_code=404, detail="Source BBCH scale not found")
        target_harvest = get_harvest_type_or_400(target_harvest_code)
        target = self.model.objects(harvestCode=target_harvest.code).first()
        now = _now_ms()
        groups = copy.deepcopy(self._resolve_groups(source))
        if target:
            if target.groups or not target.sourceHarvestCode:
                raise HTTPException(status_code=409, detail="Target BBCH scale is already independent")
            target.sourceHarvestCode = None
            target.groups = groups
            target.lastUpdateTime = now
            target.save()
        else:
            target = self.model(
                harvestCode=target_harvest.code,
                sourceHarvestCode=None,
                groups=groups,
                creationTime=now,
                lastUpdateTime=now,
            ).save()
        return self._serialize(target)

    @catch_api_exception
    def delete(self, harvest_code: str):
        scale = self.model.objects(harvestCode=harvest_code).first()
        if not scale:
            raise HTTPException(status_code=404, detail="BBCH scale not found")
        references = self.model.objects(sourceHarvestCode=harvest_code).count()
        if references:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "bbch_scale_in_use", "references": references},
            )
        scale.delete()
