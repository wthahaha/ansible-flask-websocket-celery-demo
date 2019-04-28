#!/usr/bin/env python
import os
from app import celery, app_create

app = app_create(os.getenv('FLASK_CONFIG') or 'default')
app.app_context().push()