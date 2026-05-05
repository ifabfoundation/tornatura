from mongoengine import *
from core.config import APIConfig

connect(host=APIConfig.MONGO_DATABASE_HOST, 
        db=APIConfig.MONGO_DATABASE_NAME,
        port=27017, 
        username=APIConfig.MONGO_USER, 
        password=APIConfig.MONGO_PASSWORD)
