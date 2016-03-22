settings = {
    'link-expiration-seconds': 5 * 60,  # used on the email links
    'oauth-token-expiration-seconds': 3600,  # how long will the oauth tokens be good for? after this time, the user needs to login again
    'default_calories_goal': 2500,
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
