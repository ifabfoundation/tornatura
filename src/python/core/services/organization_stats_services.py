import calendar
from datetime import datetime, timezone

from core.models import AgriFieldModel, DetectionModel, OrganizationModel


def subtract_months(reference: datetime, months: int) -> datetime:
    month_index = reference.month - months
    year = reference.year + (month_index - 1) // 12
    month = (month_index - 1) % 12 + 1
    day = min(reference.day, calendar.monthrange(year, month)[1])
    return reference.replace(year=year, month=month, day=day)


def normalize_harvest(harvest: str | None) -> str | None:
    if harvest is None:
        return None
    harvest = harvest.strip()
    return harvest or None


class OrganizationStatsServices:
    def build_detection_counts(self, agrifield_ids: list[str], window_start_ms: int) -> dict[str, int]:
        if not agrifield_ids:
            return {}

        collection = DetectionModel._get_collection()
        pipeline = [
            {
                "$match": {
                    "deleted": False,
                    "agrifieldId": {"$in": agrifield_ids},
                    "$expr": {
                        "$gte": [
                            {"$ifNull": ["$detectionTime", "$creationTime"]},
                            window_start_ms,
                        ]
                    },
                }
            },
            {
                "$group": {
                    "_id": "$agrifieldId",
                    "count": {"$sum": 1},
                }
            },
        ]

        return {item["_id"]: item["count"] for item in collection.aggregate(pipeline)}

    def get_organization_stats(self, org_id: str, months: int = 3) -> dict:
        organization = OrganizationModel.objects(orgId=org_id, deleted=False).first()
        if organization is None:
            raise ValueError(f"Organization not found or deleted: {org_id}")

        now = datetime.now(timezone.utc)
        window_start = subtract_months(now, months)
        window_start_ms = int(window_start.timestamp() * 1000)
        window_end_ms = int(now.timestamp() * 1000)

        agrifields = list(
            AgriFieldModel.objects(orgId=org_id, deleted=False).order_by("name", "creationTime")
        )
        agrifield_ids = [str(agrifield.id) for agrifield in agrifields]
        detection_counts = self.build_detection_counts(agrifield_ids, window_start_ms)

        distinct_harvests = sorted(
            {
                harvest
                for harvest in (normalize_harvest(agrifield.harvest) for agrifield in agrifields)
                if harvest is not None
            }
        )

        return {
            "organization": {
                "orgId": organization.orgId,
                "name": organization.name,
            },
            "window": {
                "months": months,
                "start": window_start.isoformat(),
                "end": now.isoformat(),
                "startTimestampMs": window_start_ms,
                "endTimestampMs": window_end_ms,
            },
            "agrifieldCount": len(agrifields),
            "distinctHarvestCount": len(distinct_harvests),
            "distinctHarvests": distinct_harvests,
            "agrifields": [
                {
                    "id": str(agrifield.id),
                    "name": agrifield.name,
                    "harvest": normalize_harvest(agrifield.harvest),
                    "creationTime": agrifield.creationTime,
                    "detectionCount": detection_counts.get(str(agrifield.id), 0),
                }
                for agrifield in agrifields
            ],
        }

    def list_organization_stats(self, months: int = 3) -> list[dict]:
        organizations = OrganizationModel.objects(deleted=False).order_by("name", "creationTime")
        return [
            self.get_organization_stats(org_id=organization.orgId, months=months)
            for organization in organizations
        ]
