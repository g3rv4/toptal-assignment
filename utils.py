from itsdangerous import URLSafeTimedSerializer
from config import settings
from server import app
import sendgrid
import requests
import json
import logger


log = logger.getLogger(__name__)
urlserializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


def send_email(account, subject, body, cc=None, bcc=None):
    cc = cc or []
    bcc = bcc or []
    to = [account.email]
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
