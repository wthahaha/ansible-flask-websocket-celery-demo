# encoding: utf-8

import uuid
import os
import random
import json
from collections import Counter
from flask import request, abort, jsonify, g, url_for, current_app, session
from flask_restful import Resource, reqparse
from flask_socketio import (
    emit,
    disconnect
)
from app.ansibles.ansible_task import INVENTORY
from app.ansibles.ansible_core import Runner
from app import redis, socketio, api
from tasks.task import long_task
from app import redis


class LoginView(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('username', type=str, location=[
                                   'json', 'args', 'headers'])
        self.reqparse.add_argument('password', type=str, location=[
                                   'json', 'args', 'headers'])
        self.args = self.reqparse.parse_args()
        super(LoginView, self).__init__()

    def get(self):
        print("clients")
        return jsonify({'clients': "unlogin"})

    def post(self):
        print(self.args)
        return jsonify({"user": "admin", "token": "dsdsdufsffjfjudss789h", "code": 200})


class UserInfoView(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', type=str, location=[
                                   'json', 'args', 'headers'])
        self.args = self.reqparse.parse_args()
        super(UserInfoView, self).__init__()

    def get(self):
        print(self.args)
        # if token == user["token"]:
        #     name = "admin"
        return jsonify({"token": "dsdsdufsffjfjudss789h", "code": 200, "name": "admin"})

    def post(self):
        print(self.args)
        return jsonify({"token": "dsdsdufsffjfjudss789h", "code": 200})


class LogoutView(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('method', type=str, location=[
                                   'json', 'args', 'headers'])
        self.args = self.reqparse.parse_args()
        super(LogoutView, self).__init__()

    def post(self):
        print(self.args)
        return jsonify({"method": "logout", "code": 200})
