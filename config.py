settings = {
    'link-expiration-seconds': 5 * 60,  # used on the email links
    'database': {
        'name': 'toptaldemo',
        'params': {
            'host': '127.0.0.1',
            'user': 'root',
            'password': ''
        }
    },
    'celery': {
        'broker': ''
    },
    'sendgrid': {
        'api-key': '',
        'template-name': 'ToptalDemo',
        'mail-from': 'Gervasio Marchand\'s Toptal Demo <gmc@gmc.uy>'
    },
    'secret_key': ''
}
