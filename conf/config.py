# encoding: utf-8

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    REDIS_URL = "redis://218.241.108.243:6379/0"
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']

    INVENTORY_PATH = "/home/wt/project/ansible-flask-websocket-celery-demo/app/ansibles/ansible.host"

    @staticmethod
    def init_app(app):
        pass


class ProductionConfig(Config):
    pass


config = {
    'default': ProductionConfig,
    'production': ProductionConfig,
}
