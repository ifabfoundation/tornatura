

import datetime
from fastapi import HTTPException, status
from core.decorators import catch_api_exception
from core.models import AgriFieldModel
from core.serializers import AgriField, AgriFieldMutationPayload



class AgriFieldServices:
    model = AgriFieldModel
    serializer = AgriField

    def _serialize(self, obj, many=False):
        """Serialize object(s) to serializer instances
        
        Args:
            obj: Object or list of objects to serialize
            many: If True, treats obj as a list of objects
            
        Returns:
            Serializer instance or list of serializer instances
        """
        def _create_instance(item):
            return self.serializer(
                id=str(item.id),
                name=item.name,
                description=item.description,
                orgId=item.orgId,
                creationTime=item.creationTime,
                lastUpdateTime=item.lastUpdateTime
            )
            
        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)
    
    @catch_api_exception
    def list(self, org_id: str):
        """List agriField
        :rtype: List[AgriField]
        """
        agrifields = self.model.objects(deleted=False, orgId=org_id)
        return self._serialize(agrifields, many=True)
    

    @catch_api_exception
    def create(self, org_id: str, payload: AgriFieldMutationPayload):
        """Create agriField
        :rtype: AgriField
        """
        data = payload.model_dump()
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)

        data.update({
            "orgId": org_id,
            "creationTime": current_time,
            "lastUpdateTime": current_time
        })

        agrifield = self.model(**data).save()
        return self._serialize(agrifield)
    
    @catch_api_exception
    def get(self, agrifield_id: str):
        """get agriField
        :rtype: AgriField
        """
        agrifield = self.model.objects(deleted=False, id=agrifield_id).first()
        if agrifield is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AgriField not found"
            )
        return self._serialize(agrifield)