import datetime
from core.decorators import catch_api_exception
from core.models import FeedbackModel
from core.serializers import Feedback, FeedbackCreatePayload


class FeedbackServices:
    model = FeedbackModel
    serializer = Feedback
    
    def _serialize(self, obj, many=False):
        """Serialize object(s) to serializer instances
        
        Args:
            obj: Object or list of objects to serialize
            many: If True, treats obj as a list of objects
            
        Returns:
            Serializer instance or list of serializer instances
        """
        def _create_instance(item) -> Feedback:
            return self.serializer(
                id=str(item.id),
                category=item.category,
                feedback=item.feedback,
                author=item.author,
                creationTime=item.creationTime,
                lastUpdateTime=item.lastUpdateTime
            )
            
        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)
    
    @catch_api_exception
    def list(self):
        """List all feedbacks"""
        detections = self.model.objects(deleted=False)
        return self._serialize(detections, many=True)
    
    @catch_api_exception
    def create(self, payload: FeedbackCreatePayload):
        """Create feedback"""
        data = payload.model_dump()
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)

        data.update({
            "creationTime": current_time,
            "lastUpdateTime": current_time
        })

        #TODO; send email for notification
        feedback = self.model(**data).save()
        return self._serialize(feedback)
    

    