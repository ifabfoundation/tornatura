# coding: utf-8

import os
from decouple import config
from pathlib import Path

_HERE = os.path.dirname(__file__)


class APIConfig(object):
    BASE_DIR = Path(_HERE).parent

    KEYCLOAK_CLIENT_ID = config('KEYCLOAK_CLIENT_ID', default='')
    KEYCLOAK_CLIENT_SECRET = config('KEYCLOAK_CLIENT_SECRET', default='')
    KEYCLOAK_REALM = config('KEYCLOAK_REALM', default='')
    KEYCLOAK_ENDPOINT = config('KEYCLOAK_ENDPOINT', default='')

    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')

    MONGO_DATABASE_HOST = config('MONGO_DATABASE_HOST', default='')
    MONGO_PASSWORD = config('MONGO_PASSWORD', default='')
    MONGO_USER = config('MONGO_USER', default='')
