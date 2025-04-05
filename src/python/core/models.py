
from mongoengine import *
import datetime


class Location(EmbeddedDocument):
    long = DecimalField(required=True)
    lat = DecimalField(required=True)


class AgriFieldModel(Document):
    """The object AgriField stored in the Database"""
    name = StringField(required=True)
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
    orgId = StringField(required=True)
    name = StringField(required=True)
    description = StringField(required=True, max_length=100)
    logo = StringField(required=True)
    cover = StringField(required=True)
    deleted = BooleanField(default=False)
    creationTime = IntField()
    lastUpdateTime = IntField()

    meta = {
        'ordering': ['-creationTime']
    }

    def __str__(self):
        return str(self.orgId)


class SurveysModel(Document):
    """The object Survey stored in the Database"""
    name = StringField(required=True)
    note = StringField(required=True)
    agrifieldId = StringField(required=True)
    location = EmbeddedDocumentField(Location, required=True)
    photos = ListField(StringField())
    deleted = BooleanField(default=False)
    creationTime = IntField()
    lastUpdateTime = IntField()

    meta = {
        'ordering': ['-creationTime']
    }

    def __str__(self):
        return str(self.id)
    