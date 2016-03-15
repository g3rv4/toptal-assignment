from flask import Flask, request, jsonify, url_for, send_from_directory, make_response, abort
from flask_restful import Resource, Api
from itsdangerous import BadData, SignatureExpired
from werkzeug.security import generate_password_hash
from validate_email import validate_email
from config import settings
import json
import models
import utils
import tasks
import logger


log = logger.getLogger(__name__)
app = Flask(__name__)
api = Api(app)


class InvalidAPIUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class DemoResource(Resource):
    def __init__(self):
        self.data = None

    def load_data(self):
        try:
            self.data = json.loads(request.data)
        except:
            raise InvalidAPIUsage('Invalid JSON received')


class Accounts(DemoResource):
    def post(self):
        self.load_data()

        if any(f for f in ('email', 'password', 'name') if f not in self.data):
            raise InvalidAPIUsage('Missing parameter(s)')
        if not validate_email(self.data['email']):
            raise InvalidAPIUsage('Invalid email address')
        if len(self.data['password']) < 8:
            raise InvalidAPIUsage('Invalid password')
        if len(self.data['name']) < 3:
            raise InvalidAPIUsage('Invalid name')

        try:
            models.Account.get(email=self.data['email'])
            raise InvalidAPIUsage('Email already registered')
        except models.Account.DoesNotExist:
            account = models.Account(name=self.data['name'], email=self.data['email'],
                                     password=generate_password_hash(self.data['password']))
            account.save()

            update_token = utils.urlserializer.dumps({'id': account.id, 'active': True}, salt='account-update')
            url = url_for('public', path='apply-account-changes', account_id=account.id, token=update_token,
                          _external=True)

            tasks.send_activation_email.delay(account.id, url)
            resp = make_response('', 201)
            resp.headers['Location'] = url_for('account', account_id=account.id)
            return resp


class Account(DemoResource):
    def put(self, account_id):
        data = json.loads(request.data)
        try:
            update_data = utils.urlserializer.loads(data['update_token'], salt='account-update', max_age=settings['link-expiration-seconds'])
        except SignatureExpired, e:
            encoded_payload = e.payload
            try:
                # generate it again and send it
                decoded_payload = utils.urlserializer.load_payload(encoded_payload)

                update_token = utils.urlserializer.dumps(decoded_payload, salt='account-update')
                url = url_for('public', path='apply-account-changes', account_id=account_id, token=update_token,
                              _external=True)
                tasks.send_account_update_email.delay(account_id, url)
            except BadData:
                abort(400, 'Invalid token')
            abort(400, 'Your token has expired. We have sent you a new link to your email')
        except BadData, e:
            log.error(e)
            abort(400, 'Invalid token')

        if update_data['id'] != account_id:
            abort(400, 'Invalid token')

        try:
            account = models.Account.get(id=account_id)
        except models.Account.DoesNotExist:
            abort(404, 'Account does not exist')

        del update_data['id']
        for k in update_data:
            setattr(account, k, update_data[k])

        account.save()
        return '', 204


@app.errorhandler(InvalidAPIUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

api.add_resource(Accounts, '/api/accounts', endpoint='accounts')
api.add_resource(Account, '/api/accounts/<int:account_id>', endpoint='account')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def public(path):
    return send_from_directory('static', 'index.html')


def _force_https():
    if request.headers.get('X-Forwarded-Proto', 'http') == 'https':
        from flask import _request_ctx_stack
        if _request_ctx_stack is not None:
            reqctx = _request_ctx_stack.top
            reqctx.url_adapter.url_scheme = 'https'

app.before_request(_force_https)
app.secret_key = settings['secret_key']
if __name__ == "__main__":
    app.run(debug=True)
