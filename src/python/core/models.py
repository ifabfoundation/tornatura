
from mongoengine import *
import datetime


class FileInfo(EmbeddedDocument):
    category = StringField(required=True)
    name = StringField(required=True)


class Point(EmbeddedDocument):
    lng = DecimalField(required=True, precision=14)
    lat = DecimalField(required=True, precision=14)


class ObservationCounter(EmbeddedDocument):
    counterName = StringField(required=True)
    counterValue = FloatField(required=True)


class ObservationData(EmbeddedDocument):
    rangeValue = FloatField(null=True)
    counters = ListField(EmbeddedDocumentField(ObservationCounter), default=[])


class ObservationPoint(EmbeddedDocument):
    position = EmbeddedDocumentField(Point, required=True)
    data = EmbeddedDocumentField(ObservationData, required=True)


class ObservationTreatment(EmbeddedDocument):
    treatment = BooleanField(default=False, required=True)
    treatmentDate = StringField(default="")
    treatmentProduct = StringField(default="")


class DetectionData(EmbeddedDocument):
    bbch = StringField(default="")
    notes = StringField(default="")
    treatment = EmbeddedDocumentField(ObservationTreatment, default=ObservationTreatment)
    photos = ListField(EmbeddedDocumentField(FileInfo), default=[])
    points = ListField(EmbeddedDocumentField(ObservationPoint), default=[])


class Contacts(EmbeddedDocument):
    email = StringField(required=True)
    phone = StringField(required=True)

class Office(EmbeddedDocument):
    state = StringField(required=True)
    city = StringField(required=True)


class AgriFieldModel(Document):
    """The object AgriField stored in the Database"""
    name = StringField(required=True)
    variety = StringField(required=True, default='')
    harvest = StringField(required=True, default='')
    area = DecimalField(required=True, default=1.0)
    plants = IntField(default=0)
    rotation = StringField(required=True, default="Si")
    year = StringField()
    irrigation = StringField(default='')
    grassing = StringField(default='')
    weaving = StringField(default='')
    map = ListField(EmbeddedDocumentField(Point), default=[])
    description = StringField(required=True, max_length=100)
    orgId = StringField(required=True)
    deleted = BooleanField(default=False)
    creationTime = IntField()
    lastUpdateTime = IntField()

    meta = {
        'ordering': ['-creationTime']
    }

    def __str__(self):
        return str(self.id)


class OrganizationModel(Document):
    """The object Organization stored in the Database"""
    orgId = StringField(required=True, unique=True)
    name = StringField(required=True)
    piva = StringField(required=True, default="")
    logo = EmbeddedDocumentField(FileInfo, required=True)
    cover = EmbeddedDocumentField(FileInfo, required=True)
    contacts = EmbeddedDocumentField(Contacts, required=True)
    deleted = BooleanField(default=False)
    creationTime = IntField()
    lastUpdateTime = IntField()

    meta = {
        'ordering': ['-creationTime']
    }

    def __str__(self):
        return str(self.orgId)


class ObservationType(Document):
    """The object Observation Type stored in the Database"""
    typology = StringField(required=True)
    method = StringField(required=True)
    category = StringField(required=True)
    locationAndScoreInstructions = StringField(required=True)
    observationHint = StringField(required=True, default="Valuta l'intensità del sintomo")
    observationType = StringField(required=True, choices=("range", "counters"))
    rangeMin = FloatField(null=True)
    rangeMax = FloatField(null=True)
    rangeLabels = ListField(StringField(), default=[])
    counters = ListField(StringField(), default=[])
    creationTime = IntField()

    meta = {
        'ordering': ['-creationTime']
    }

    def __str__(self):
        return str(self.id)


class DetectionType(Document):
    """The object Detection Type stored in the Database"""
    agrifieldId = StringField(required=True)
    observationTypeId = StringField(required=True)
    creationTime = IntField()
    meta = {
        'ordering': ['-creationTime']
    }

    def __str__(self):
        return str(self.id)


class DetectionModel(Document):
    """The object Detection stored in the Database"""
    agrifieldId = StringField(required=True)
    detectionTime = IntField(default=None)
    detectionTypeId = StringField(required=True)
    detectionData = EmbeddedDocumentField(DetectionData, required=True)
    deleted = BooleanField(default=False)
    creationTime = IntField()
    lastUpdateTime = IntField()

    meta = {
        'ordering': ['-creationTime']
    }

    def __str__(self):
        return str(self.id)


class FeedbackModel(Document):
    """The object Feedback stored in the Database"""
    category = StringField(required=True)
    feedback = StringField(required=True)
    author = StringField(required=True)
    deleted = BooleanField(default=False)
    creationTime = IntField()
    lastUpdateTime = IntField()

    meta = {
        'ordering': ['-creationTime']
    }

    def __str__(self):
        return str(self.id)

class InvitationModel(Document):
    """The object Invitation stored in the Database"""
    email = StringField(required=True)
    orgId = StringField()  # Optional - null when agronomist invites non-existent company owner
    inviterId = StringField(required=True)
    role = StringField(required=True)
    token = StringField(required=True, unique=True)
    status = StringField(default="pending")  # pending, accepted, declined, expired, revoked
    expiresAt = IntField(required=True)
    acceptedAt = IntField()
    deleted = BooleanField(default=False)
    creationTime = IntField(required=True)
    lastUpdateTime = IntField(required=True)

    meta = {
        'collection': 'invitations',
        'indexes': [
            'token',
            'email',
            'orgId',
            'status',
            {'fields': ['email', 'orgId', 'status']},
        ],
        'ordering': ['-creationTime']
    }

    def __str__(self):
        return str(self.id)     
