# flask-websocket-celery-demo
## 感谢miguelgrinberg、jwhelland
## 本项目根据miguelgrinberg和jwhelland的项目修改而来

Using Celery with Flask
=======================

This repository contains the example code for my blog article [Using Celery with Flask](http://blog.miguelgrinberg.com/post/using-celery-with-flask).

The application provides two examples of background tasks using Celery:

- Example 1 sends emails asynchronously.
- Example 2 launches one or more asynchronous jobs and shows progress updates in the web page.

Here is a screenshot of this application:

<center><img src="http://blog.miguelgrinberg.com/static/images/flask-celery.png"></center>

本项目快速启动（Linux or Mac）
-----------

1. Clone 本项目.
2. 创建 virtualenv(python3.6.7) 并且安装 requirements.
3. 安装并启动redis (如果是在 Linux or Mac上, 执行 `run-redis.sh` 来安装并启动redis).
4. 启动Celery worker: `venv/bin/celery worker -A app.celery --loglevel=info`.
5. 启动app: `venv/bin/python app.py`.
6. 浏览器访问 `http://localhost:5000/` 


