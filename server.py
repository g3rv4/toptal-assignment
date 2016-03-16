from flask import Flask, request, jsonify, url_for, send_from_directory, make_response, abort
from flask_restful import Resource, Api
from itsdangerous import BadData, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash
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


# decorator to allow certain methods to require logged in users. It can also enforce certain roles. If the function
# receives an account or a roles parameter, those get populated by the decorator as well
def require_auth(roles=None, accountid_free_roles=[]):
    def decorator(funct):
        def decorated_function(*args, **kwargs):
            # check if the user is at least sending a bearer token
            if 'Authorization' not in request.headers or len(request.headers['Authorization']) < 8 or request.headers['Authorization'][:7] != 'Bearer ':
                abort(401, 'Unauthorized')

            token = request.headers['Authorization'][7:]
            try:
                token = utils.urlserializer.loads(token, settings['oauth-token-expiration-seconds'], salt='access-token')
            except BadData, e:
                log.error(e)
                abort(401, 'Unauthorized')

            if roles and not any(r for r in roles if r in token['roles']):
                abort(401, 'Unauthorized')

            if 'account_id' in kwargs:
                # if the value is 0, the user meant the owner of the token
                kwargs['account_id'] = kwargs['account_id'] or token['id']

                # if the function is receiving an account_id that's not the token's owner, then we require the user
                # to have one of the accountid_free_roles
                if kwargs['account_id'] != token['id'] and not any(r for r in accountid_free_roles if r in token['roles']):
                    abort(401, 'Unauthorized')

            try:
                account = models.Account.get(id=kwargs['account_id'] if 'account_id' in kwargs else token['id'])
            except models.Account.DoesNotExist:
                abort(404, 'Not Found')

            if 'kwargs' in funct.__code__.co_varnames or 'account' in funct.__code__.co_varnames:
                kwargs['account'] = account

            if 'kwargs' in funct.__code__.co_varnames or 'roles' in funct.__code__.co_varnames:
                kwargs['roles'] = token['roles']

            return funct(*args, **kwargs)

        return decorated_function
    return decorator


class InvalidAPIUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, **kwargs):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = kwargs

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
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

            # make this account a user
            models.AccountRole(account=account, role=models.Role.get(code='user')).save()

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


class Meals(DemoResource):
    @require_auth(roles=['user', 'admin'], accountid_free_roles=['admin'])
    def post(self, account_id, account):
        return '', 201


@app.errorhandler(InvalidAPIUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

api.add_resource(Accounts, '/api/accounts', endpoint='accounts')
api.add_resource(Account, '/api/accounts/<int:account_id>', endpoint='account')
api.add_resource(Meals, '/api/accounts/<int:account_id>/meals', endpoint='meals')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def public(path):
    return send_from_directory('static', 'index.html')


@app.route('/api/oauth', methods=['POST'])
def login():
    if any(f for f in ('grant_type', 'username', 'password') if f not in request.form) or \
            any(k for k in request.form if k not in ('grant_type', 'username', 'password')):
        raise InvalidAPIUsage('invalid_request')

    if request.form['grant_type'] != 'password':
        # only implementing Resource Owner Password Credentials Grant from RFC 6749
        raise InvalidAPIUsage('unsupported_grant_type')

    try:
        account = models.Account.get(email=request.form['username'])
    except models.Account.DoesNotExist:
        raise InvalidAPIUsage('invalid_grant')

    if not check_password_hash(account.password, request.form['password']):
        raise InvalidAPIUsage('invalid_grant')

    if not account.active:
        update_token = utils.urlserializer.dumps({'id': account.id, 'active': True}, salt='account-update')
        url = url_for('public', path='apply-account-changes', account_id=account.id, token=update_token,
                      _external=True)
        tasks.send_activation_email.delay(account.id, url)
        raise InvalidAPIUsage('invalid_grant', error_description='Your account is not active. An email has been sent '
                                                                 'to you with instructions to activate your account.')

    roles = map(lambda x: x.code, models.Role.select().join(models.AccountRole).where(models.AccountRole.account == account))

    # not generating refresh tokens as it's making it all the way to the user's browser. If an attacker got their
    # hands on a refresh token, they could do anything without a time restriction
    return jsonify({
        'access_token': utils.urlserializer.dumps({'id': account.id, 'roles': roles}, salt='access-token'),
        'token_type': 'bearer',
        'expires_in': settings['oauth-token-expiration-seconds'],
        'scope': ' '.join(roles)
    })


def _force_https():
    if request.headers.get('X-Forwarded-Proto', 'http') == 'https':
        from flask import _request_ctx_stack
        if _request_ctx_stack is not None:
            reqctx = _request_ctx_stack.top
            reqctx.url_adapter.url_scheme = 'https'

app.before_request(_force_https)
app.secret_key = settings['secret_key']
if __name__ == "__main__":
    app.run()
