# encoding: utf-8

import os
from flask_script import Manager
from app import app_create
from flask_migrate import Migrate, MigrateCommand
from app import socketio


# 设置启动方式，可选：development、testing、production
app = app_create(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)


manager.add_command('db', MigrateCommand)
manager.add_command('run', socketio.run(
    app=app, host='0.0.0.0', port=5000,debug=True))  # 新加入的内容，重写manager的run命令


if __name__ == '__main__':
    manager.run()
