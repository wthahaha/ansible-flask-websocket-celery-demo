# encoding: utf-8

import os
from dotenv import load_dotenv
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    REDIS_URL = os.getenv("REDIS_URL")
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERY_ACCEPT_CONTENT = ['json', 'pickle', 'msgpack', 'yaml']
    CELERY_WORKER_CONCURRENCY = 10
    ES_HOST=os.getenv("ES_HOST")
    ES_PORT=os.getenv("ES_PORT")
    ES_INDEX=os.getenv("ES_INDEX")
    ES_KEY_PREFIX=os.getenv("ES_KEY_PREFIX")
    UPDATE_CMDB_URL=os.getenv("UPDATE_CMDB_URL")
    UPDATE_CMDB_EMAIL=os.getenv("UPDATE_CMDB_EMAIL")
    UPDATE_CMDB_PASS=os.getenv("UPDATE_CMDB_PASS")
    UPDATE_CMDB_TOKEN_API=os.getenv("UPDATE_CMDB_TOKEN_API")
    UPDATE_CMDB_OS_API=os.getenv("UPDATE_CMDB_OS_API")
    CMDB_MODEL_API=os.getenv("CMDB_MODEL_API")
    INVENTORY_PATH = os.getenv("INVENTORY_PATH")

    @staticmethod
    def init_app(app):
        pass


class ProductionConfig(Config):
    pass


config = {
    'default': ProductionConfig,
    'production': ProductionConfig,
}
