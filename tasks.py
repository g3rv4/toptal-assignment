from celery import Celery
from config import settings
import models

app = Celery('tasks', broker=settings['celery']['broker'])
app.conf.CELERY_ACCEPT_CONTENT = ['json']


@app.task
def send_activation_email(id):
    account = models.Account.get(id=id)
