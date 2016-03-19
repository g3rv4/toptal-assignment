from itsdangerous import URLSafeTimedSerializer
from dateutil.parser import parse as parse_date
from validate_email import validate_email
from config import settings
from server import app
import sendgrid
import requests
import json
import logger
import re


log = logger.getLogger(__name__)
urlserializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


def send_email(account, subject, body, cc=None, bcc=None, to=None):
    cc = cc or []
    bcc = bcc or []
    to = [to] if to else [account.email]
    if not isinstance(cc, list):
        cc = [cc]
    if not isinstance(bcc, list):
        bcc = [bcc]

    sg = sendgrid.SendGridClient(settings['sendgrid']['api-key'])

    response = requests.get('https://api.sendgrid.com/v3/templates', headers={
        'Authorization': 'Bearer %s' % settings['sendgrid']['api-key'],
        'Content-Type': 'application/json'
    })
    response = json.loads(response.content)
    templates = {t['name']: t['id'] for t in response['templates']}
    template = templates[settings['sendgrid']['template-name']]

    message = sendgrid.Mail()
    for address in to:
        message.add_to(address)
    for address in cc:
        message.add_cc(address)
    for address in bcc:
        message.add_bcc(address)

    message.set_subject(subject)
    message.set_from(settings['sendgrid']['mail-from'])
    message.set_html(body)

    message.add_filter('templates', 'enable', '1')
    message.add_filter('templates', 'template_id', template)
    message.add_substitution('--name--', account.name)

    status, msg = sg.send(message)
    log.debug('Sendgrid message sent to %s, status %i, message: %s' % (to, status, msg))


def is_valid_date(date):
    if re.match('[0-9]{4}-[0-9]{2}-[0-9]{2}$', date):
        try:
            parse_date(date)
            return True
        except:
            pass
    return False


def is_valid_time(time):
    if re.match('[0-9]{2}:[0-9]{2}:[0-9]{2}$', time):
        try:
            parse_date('2015-01-01 %s' % time)
            return True
        except:
            pass
    return False


def is_valid_email(email):
    return validate_email(email) and re.match(r'.*@.+\.[a-z]+$', email)
