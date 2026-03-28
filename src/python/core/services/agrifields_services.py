

import datetime
from fastapi import HTTPException, status
from core.decorators import catch_api_exception
from core.models import AgriFieldModel, Point
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
                harvest=item.harvest,
                area=item.area,
                plants=item.plants,
                variety=item.variety,
                rotation=item.rotation,
                year=item.year,
                irrigation=item.irrigation,
                grassing=item.grassing,
                weaving=item.weaving,
                map=[{"lng": point.lng, "lat": point.lat} for point in item.map],
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
    def create(self, org_id: str, payload: AgriFieldMutationPayload, user_id: str):
        """Create agriField
        :rtype: AgriField
        """
        data = payload.model_dump(exclude_none=True)
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)

        data["map"] = [Point(lng=point.lng, lat=point.lat) for point in payload.map]
        data.update({
            "orgId": org_id,
            "createdBy": user_id,
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
    
    @catch_api_exception
    def delete(self, agrifield_id: str):
        """Soft delete agrifield
        
        Args:
            agrifield_id: ID of the agrifield to delete
            
        Returns:
            None
        """
        agrifield = self.model.objects(id=agrifield_id, deleted=False).first()
        if not agrifield:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agrifield not found"
            )
        
        agrifield.deleted = True
        agrifield.save()
        
        return None
    
    @catch_api_exception
    def update(self, agrifield_id: str, payload: AgriFieldMutationPayload):
        """Update agrifield
        
        Args:
            agrifield_id: ID of the agrifield to delete
            payload: Payload containing updated agrifield data
            
        Returns:
            AgriField: Updated agrifield data
        """
        agrifield = self.model.objects(id=agrifield_id, deleted=False).first()
        if not agrifield:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agrifield not found"
            )
        
        
        agrifield.name = payload.name
        agrifield.description = payload.description
        agrifield.harvest = payload.harvest
        agrifield.area = payload.area
        agrifield.plants = payload.plants
        agrifield.variety = payload.variety
        agrifield.rotation = payload.rotation
        agrifield.irrigation = payload.irrigation
        agrifield.grassing = payload.grassing
        agrifield.weaving = payload.weaving
        if payload.year is not None:
            agrifield.year = payload.year            
        agrifield.map = [Point(lng=point.lng, lat=point.lat) for point in payload.map]
        agrifield.lastUpdateTime = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)
        agrifield.save()

        return self._serialize(agrifield)
    
