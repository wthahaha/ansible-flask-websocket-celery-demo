# flask-websocket-celery-demo

## 感谢 miguelgrinberg、jwhelland

## 本项目根据 miguelgrinberg 和 jwhelland 的项目修改而来

# Using Celery with Flask

This repository contains the example code for my blog article [Using Celery with Flask](http://blog.miguelgrinberg.com/post/using-celery-with-flask).

The application provides two examples of background tasks using Celery:

- Example 1 sends emails asynchronously.
- Example 2 launches one or more asynchronous jobs and shows progress updates in the web page.

Here is a screenshot of this application:

<center><img src="http://blog.miguelgrinberg.com/static/images/flask-celery.png"></center>

## 本项目快速启动（Linux or Mac）

1. Clone 本项目.
2. 创建 virtualenv(python3.6.7) 并且安装 requirements.
3. 安装并启动 redis (如果是在 Linux or Mac 上, 执行 `run-redis.sh` 来安装并启动 redis).
4. 在项目根目录下创建.env 文件，用于存储环境变量
   示例:
   ```
   REDIS_URL=redis://127.0.0.1:6379/0
   ```
5. 启动 Celery worker: `celery worker -A celery_worker.celery --loglevel=info`.
6. 启动 app: `venv/bin/python app.py`.
7. 浏览器访问 `http://localhost:5000/`
8. 演示：
   <center><img src="https://github.com/cncert/ansible-flask-websocket-celery-demo/blob/master/templates/1556374302219.gif"></center>
