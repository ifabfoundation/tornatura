
from mongoengine import *
import datetime


class FileInfo(EmbeddedDocument):
    category = StringField(required=True)
    name = StringField(required=True)


class Point(EmbeddedDocument):
    lng = DecimalField(required=True, precision=14)
    lat = DecimalField(required=True, precision=14)


class Contacts(EmbeddedDocument):
    email = StringField(required=True)
    phone = StringField(required=True)

class Office(EmbeddedDocument):
    state = StringField(required=True)
    city = StringField(required=True)


class AgriFieldModel(Document):
    """The object AgriField stored in the Database"""
    name = StringField(required=True)
    description = StringField(required=True, max_length=100)
    harvest = StringField(required=True, default="barbabietola")
    area = DecimalField(required=True, default=150.0)
    map = ListField(EmbeddedDocumentField(Point), default=[])
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
    rapresentative = StringField(required=True, default="")
    rapresentativeContact = StringField(required=True, default="")
    office = EmbeddedDocumentField(Office, required=True, default=Office(
        state="",
        city=""
    ))
    legalForm = StringField(required=True, default="")
    logo = EmbeddedDocumentField(FileInfo, required=True)
    cover = EmbeddedDocumentField(FileInfo, required=True)
    description = StringField(required=True, default="")
    contacts = EmbeddedDocumentField(Contacts, required=True)
    deleted = BooleanField(default=False)
    creationTime = IntField()
    lastUpdateTime = IntField()

    meta = {
        'ordering': ['-creationTime']
    }

    def __str__(self):
        return str(self.orgId)


class DetectionModel(Document):
    """The object Detection stored in the Database"""
    agrifieldId = StringField(required=True)
    detectionTime = IntField(default=None)
    type = StringField(required=True)
    note = StringField(required=True)
    details = DictField(default={})
    position = EmbeddedDocumentField(Point, required=True)
    photos = ListField(EmbeddedDocumentField(FileInfo), default=[])
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
    