#! /usr/bin/python

"""Sets up the celery environment, which is an asynchronous task manager."""

from celery import Celery
app = Celery('task_manager', broker='amqp://admin:pass@rabbit:5672',
             backend='rpc://', include=['task_manager.tasks'])
