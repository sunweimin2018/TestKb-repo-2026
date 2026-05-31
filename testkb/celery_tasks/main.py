from celery import Celery
import os

# 告诉celery 如果需要使用Django的配置文件,应该去那里加载
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testkb.settings.dev")
os.environ.setdefault('FORKED_BY_MULTIPROCESSING','1')  # 主要加上这一段话
# 1.创建celery实例对象
celery_app = Celery('testkb')

# 2.加载配置文件
celery_app.config_from_object('celery_tasks.config')

# 3.自动注册异步任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])

