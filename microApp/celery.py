import os
from celery import Celery
from celery.schedules import crontab 

 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'microApp.settings')
app = Celery('microApp')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'scheduled_task': { 
        'task': 'superadmin.tasks.user_subscription', 
        'schedule': crontab(minute=10, hour=0),
        # 'args': (5,10)
    }
}  

app.autodiscover_tasks()
     
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
