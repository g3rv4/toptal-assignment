from itsdangerous import URLSafeSerializer
from config import settings
from server import app
import sendgrid
import requests
import json
import logger


log = logger.getLogger(__name__)
urlserializer = URLSafeSerializer(app.config['SECRET_KEY'])


def send_email(to, subject, body, cc=None, bcc=None):
    cc = cc or []
    bcc = bcc or []
    if not isinstance(to, list):
        to = [to]
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
    message.set_from(settings.MAIL_FROM)
    message.set_text(body)

    message.add_filter('templates', 'enable', '1')
    message.add_filter('templates', 'template_id', template)

    status, msg = sg.send(message)
    log.debug('Sendgrid message sent, status %i, message: %s' % (status, msg))
