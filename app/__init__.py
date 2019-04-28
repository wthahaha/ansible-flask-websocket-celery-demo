# encoding: utf-8


from flask import Flask
from conf.config import config
from flask_restful import Api
from flask_cors import CORS
from flask_redis import FlaskRedis
from flask_socketio import SocketIO

api = Api()
socketio = SocketIO()
redis = FlaskRedis()


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
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    redis.init_app(app)

    from app.apis.view import AnsibleTaskView, EventView
    from app.apis import api_blueprint
    from app.main import main_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint)

    api.add_resource(AnsibleTaskView, "/api/ansible_task/",
                     endpoint="ansible_task")
    api.add_resource(EventView, "/api/event/",
                     endpoint="event")

    api.init_app(app)
    socketio.init_app(app)
    CORS(app)
    return app
