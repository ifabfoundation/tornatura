# coding: utf-8

import os
from decouple import config
from pathlib import Path

_HERE = os.path.dirname(__file__)


class APIConfig(object):
    BASE_DIR = _HERE

    KEYCLOAK_CLIENT_ID = config('KEYCLOAK_CLIENT_ID', default='')
    KEYCLOAK_CLIENT_SECRET = config('KEYCLOAK_CLIENT_SECRET', default='')
    KEYCLOAK_REALM = config('KEYCLOAK_REALM', default='')
    KEYCLOAK_ENDPOINT = config('KEYCLOAK_ENDPOINT', default='')

    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')

    MONGO_DATABASE_HOST = config('MONGO_DATABASE_HOST', default='')
    MONGO_PASSWORD = config('MONGO_PASSWORD', default='')
    MONGO_USER = config('MONGO_USER', default='')

    MINIO_HOSTNAME = config('MINIO_HOSTNAME', default='')
    MINIO_ACCESS_KEY = config('MINIO_ACCESS_KEY', default='')
    MINIO_SECRET_KEY = config('MINIO_SECRET_KEY', default='')
    MINIO_SECURE = config('MINIO_SECURE', default=False, cast=bool)

    SMTP_EMAIL = config('SMTP_EMAIL', default='')
    SMTP_PASSWORD = config('SMTP_PASSWORD', default='')
    SMTP_HOST = config('SMTP_HOST', default='')
    SMTP_PORT = config('SMTP_PORT', default='')
    STAFF_EMAIL = config('STAFF_EMAIL', default='')
    FRONTEND_URL = config('FRONTEND_URL', default='')
