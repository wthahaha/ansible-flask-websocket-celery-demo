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
