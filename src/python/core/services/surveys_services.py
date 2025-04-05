import datetime
from fastapi import HTTPException, status
from core.decorators import catch_api_exception
from core.models import SurveysModel
from core.serializers import Survey, SurveyMutationPayload
from core.services.agrifields_services import AgriFieldServices
from core.services.files_services import FileServices


class SurveyServices:
    model = SurveysModel
    serializer = Survey
    
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
       
        def _create_instance(item) -> Survey:
            agrifield = agrifield_services.get(item.agrifieldId)
            return self.serializer(
                id=str(item.id),
                agrifieldId=item.agrifieldId,
                name=item.name,
                type=item.type, 
                position={
                    "lng": item.position.lng,
                    "lat": item.position.lat
                },
                photos=[file_services.get_file_url(agrifield.orgId, photo.category, photo.name) for photo in item.photos],
                note=item.note,
                creationTime=item.creationTime,
                lastUpdateTime=item.lastUpdateTime
            )
            
        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)
    
    @catch_api_exception
    def list(self, agrifield_id: str):
        """List surveys for an agricultural field
        
        Args:
            agrifield_id: ID of the agricultural field
            
        Returns:
            serialized surveys
        """
        surveys = self.model.objects(agrifieldId=agrifield_id, deleted=False)
        return self._serialize(surveys, many=True)
    
    @catch_api_exception
    def create(self, agrifield_id: str, payload: SurveyMutationPayload):
        """Create survey
        
        Args:
            agrifield_id: ID of the agricultural field
            payload: Survey creation data
            
        Returns:
            Serialized created survey
        """
        data = payload.model_dump()
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)

        data.update({
            "agrifieldId": agrifield_id,
            "creationTime": current_time,
            "lastUpdateTime": current_time
        })

        survey = self.model(**data).save()
        return self._serialize(survey)
    
    @catch_api_exception
    def get(self, survey_id: str):
        """Get survey by ID
        
        Args:
            survey_id: ID of the survey
            
        Returns:
            Serialized survey
        """
        survey = self.model.objects(id=survey_id, deleted=False).first()
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        return self._serialize(survey)
    
    @catch_api_exception
    def update(self, survey_id: str, payload: SurveyMutationPayload):
        """Update survey
        
        Args:
            survey_id: ID of the survey
            payload: Survey update data
            
        Returns:
            Serialized updated survey
        """
        survey = self.model.objects(id=survey_id, deleted=False).first()
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        
        data = payload.model_dump()
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)
        
        survey.name = data["name"]
        survey.note = data["note"]
        survey.location = data["location"]
        survey.photos = data["photos"]
        survey.lastUpdateTime = current_time
        survey.save()
        
        return self._serialize(survey)
    
    @catch_api_exception
    def delete(self, survey_id: str):
        """Soft delete survey
        
        Args:
            survey_id: ID of the survey
            
        Returns:
            None
        """
        survey = self.model.objects(id=survey_id, deleted=False).first()
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        
        survey.deleted = True
        survey.save()
        
        return None
        
    def __repr__(self):
        return f"SurveyServices(model={self.model.__name__})"