# 使用celery
from celery import Celery

# 创建一个Celery 实例

celery = Celery('celery_tasks.tasks', broker='redis://localhost:6379')


def send_mail_register(request):
    pass
