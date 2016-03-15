from celery import Celery
from config import settings
import models
import utils

app = Celery('tasks', broker=settings['celery']['broker'])
app.conf.CELERY_ACCEPT_CONTENT = ['json']
app.conf.CELERY_TASK_SERIALIZER = 'json'


@app.task
def send_activation_email(account_id, url):
    account = models.Account.get(id=account_id)
    utils.send_email(account, 'Activate your account', 'Visit <a href="%s">this link</a> to activate your account' % url)

@app.task
def send_account_update_email(account_id, url):
    account = models.Account.get(id=account_id)
    utils.send_email(account, 'Update your account', 'Visit <a href="%s">this link</a> to apply the pending changes to your account' % url)
