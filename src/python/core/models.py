
from mongoengine import *
import datetime


class FileInfo(EmbeddedDocument):
    category = StringField(required=True)
    name = StringField(required=True)


class Point(EmbeddedDocument):
    lng = DecimalField(required=True)
    lat = DecimalField(required=True)


class Contacts(EmbeddedDocument):
    email = StringField(required=True)
    phone = StringField(required=True)


class AgriFieldModel(Document):
    """The object AgriField stored in the Database"""
    name = StringField(required=True)
    description = StringField(required=True, max_length=100)
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
    description = StringField(required=True, max_length=100)
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


class DetectionModel(Document):
    """The object Detection stored in the Database"""
    agrifieldId = StringField(required=True)
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
    