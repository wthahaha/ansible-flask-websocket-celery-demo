# encoding: utf-8


from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flask_redis import FlaskRedis
from flask_socketio import SocketIO
from celery import Celery
import elasticsearch
from conf.config import config, Config

api = Api()
socketio = SocketIO()
redis = FlaskRedis(decode_responses=True)
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)


# api = Api(app, decorators=[csrf_protect.exempt])
# api.add_resource(FTRecordsAPI,
#                  '/api/v1.0/ftrecords/<string:ios_sync_timestamp>',
#                  endpoint="api.ftrecord")
# You'll need to specify a value for the ios_sync_timestamp part of your URL:

# flask.url_for('api.ftrecord', ios_sync_timestamp='some value')
# or you could use Api.url_for(), which takes a resource:

# api.url_for(FTRecordsAPI, ios_sync_timestamp='some value')

def app_create(config_name):
    # config_name: development, testing, production
    app = Flask(__name__, static_folder="../static",
                template_folder="../templates")
    app.config.from_object(config[config_name])
    app.clients = {}
    config[config_name].init_app(app)
    redis.init_app(app)

    from app.apis.view import AnsibleTaskView, EventView, ClientView, ClientIpListView
    from app.apis.service_view import LoginView, UserInfoView, LogoutView
    from app.apis.cmdb_view import UpdateCmdb
    from app.apis import api_blueprint
    from app.main import main_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint)

    api.add_resource(AnsibleTaskView, "/api/ansible_task/",
                     endpoint="ansible_task", strict_slashes=False)
    api.add_resource(EventView, "/api/events/",
                     endpoint="events", strict_slashes=False)
    api.add_resource(ClientView, "/api/client/",
                     endpoint="client", strict_slashes=False)
    api.add_resource(ClientIpListView, "/api/iplist/",
                     endpoint="iplist", strict_slashes=False)
    api.add_resource(LoginView, "/api/user/login",
                     endpoint="login", strict_slashes=False)
    api.add_resource(UserInfoView, "/api/user/info",
                     endpoint="info", strict_slashes=False)
    api.add_resource(LogoutView, "/api/user/logout",
                     endpoint="logout", strict_slashes=False)
    api.add_resource(UpdateCmdb, "/api/update_cmdb",
                     endpoint="update_cmdb", strict_slashes=False)

    api.init_app(app)
    socketio.init_app(app)
    CORS(app, supports_credentials=True)
    celery.conf.update(app.config)
    return app
