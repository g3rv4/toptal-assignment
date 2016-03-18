from flask import Flask, request, jsonify, url_for, send_from_directory, make_response, abort
from flask.views import MethodViewType
from flask_restful import Resource, Api
from itsdangerous import BadData, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash
from validate_email import validate_email
from config import settings
from dateutil.parser import parse as parse_date
import wrapt
import json
import types
import models
import utils
import tasks
import logger
import rest_serializers


log = logger.getLogger(__name__)
app = Flask(__name__)
api = Api(app)


# decorator to allow certain methods to require logged in users. It can also enforce certain roles. If the function
# receives an account or a roles parameter, those get populated by the decorator as well
def require_auth(roles=None, accountid_free_roles=[]):
    def decorator(funct_or_class):
        def decorate_function(funct):
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

                account_id = (kwargs['account_id'] if 'account_id' in kwargs else 0) or token['id']
                if account_id != token['id'] and not any(r for r in accountid_free_roles if r in token['roles']):
                    abort(401, 'Unauthorized')

                try:
                    account = models.Account.get(id=account_id)
                except models.Account.DoesNotExist:
                    abort(404, 'Not Found')

                if 'account_id' in funct.__code__.co_varnames:
                    kwargs['account_id'] = token['id']

                if 'account' in funct.__code__.co_varnames:
                    kwargs['account'] = account

                if 'roles' in funct.__code__.co_varnames:
                    kwargs['roles'] = token['roles']

                if len(args) and isinstance(args[0], Resource):
                    args[0].account = account
                    args[0].roles = token['roles']

                return funct(*args, **kwargs)

            decorated_function.triggering_pre_execute = True
            return decorated_function

        if isinstance(funct_or_class, types.FunctionType):
            return decorate_function(funct_or_class)
        else:
            for action in (a for a in ('get', 'post', 'put', 'delete') if hasattr(funct_or_class, a)):
                setattr(funct_or_class, action, decorate_function(getattr(funct_or_class, action)))
            return funct_or_class
    return decorator


def created_response(url_name, **kwargs):
    resp = make_response('', 201)
    resp.headers['Location'] = url_for(url_name, _external=True, **kwargs)
    return resp


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


class ResourceMeta(MethodViewType):
    def __new__(cls, name, bases, attrs):
        @wrapt.decorator
        def add_pre_execute(wrapped, instance, args, kwargs):
            attrs['pre_execute'](instance, *args, **kwargs)
            return wrapped(*args, **kwargs)

        @wrapt.decorator
        def add_json_parse(wrapped, instance, args, kwargs):
            try:
                instance.data = json.loads(request.data)
            except:
                raise InvalidAPIUsage('Invalid JSON received')
            return wrapped(*args, **kwargs)

        for action in (a for a in attrs if a in ('get', 'post', 'put', 'delete')):
            if action in ('post', 'put'):
                attrs[action] = add_json_parse(attrs[action])

            if 'pre_execute' in attrs:
                attrs[action] = add_pre_execute(attrs[action])

        return super(ResourceMeta, cls).__new__(cls, name, bases, attrs)


class Accounts(Resource):
    __metaclass__ = ResourceMeta

    def post(self):
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
            return created_response('account', account_id=account.id)


class Account(Resource):
    __metaclass__ = ResourceMeta

    def put(self, account_id):
        try:
            update_data = utils.urlserializer.loads(self.data['update_token'], salt='account-update', max_age=settings['link-expiration-seconds'])
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


@require_auth(roles=['user', 'admin'], accountid_free_roles=['admin'])
class Meals(Resource):
    __metaclass__ = ResourceMeta

    def post(self, account_id):
        if any(f for f in ('date', 'time', 'description', 'calories') if f not in self.data):
            abort(400, 'Missing Parameter(s)')

        if not utils.is_valid_date(self.data['date']):
            abort(400, 'Invalid date')

        if not utils.is_valid_time(self.data['time']):
            abort(400, 'Invalid time format')

        if not isinstance(self.data['calories'], int) or self.data['calories'] <= 0:
            abort(400, 'Invalid calories value')

        meal_dt = parse_date('%s %s' % (self.data['date'], self.data['time']))

        meal = models.Meal(account=self.account, date=meal_dt.date(), time=self.data['time'],
                           description=self.data['description'], calories=self.data['calories'])
        meal.save()

        return created_response('meal', account_id=self.account.id, meal_id=meal.id)

    def get(self, account_id):
        meals = models.Meal.select().where(models.Meal.account == self.account)

        if 'meal-date-from' in request.args:
            meals = meals.where(models.Meal.meal_date)

        return rest_serializers.serialize_meals(meals)


@require_auth(roles=['user', 'admin'], accountid_free_roles=['admin'])
class Meal(Resource):
    __metaclass__ = ResourceMeta

    def __init__(self):
        self.meal = None
        super(Meal, self).__init__()

    def pre_execute(self, *args, **kwargs):
        try:
            self.meal = models.Meal.get(models.Meal.id == kwargs['meal_id'], models.Meal.account == self.account)
        except models.Meal.DoesNotExist:
            abort(404, 'Meal not found')

    def get(self, account_id, meal_id):
        return jsonify(rest_serializers.serialize_meal(self.meal))

    def delete(self, account_id, meal_id):
        self.meal.delete_instance()
        return '', 204

    def put(self, account_id, meal_id):
        if any(k for k in self.data if k not in ('id', 'account', 'date', 'time', 'description', 'calories')):
            raise InvalidAPIUsage('Invalid parameters')

        # skipping id and account fields

        if 'date' in self.data:
            if not utils.is_valid_date(self.data['date']):
                raise InvalidAPIUsage('Invalid date')

            self.meal.date = parse_date(self.data['date']).date()

        if 'time' in self.data:
            if not utils.is_valid_time(self.data['time']):
                raise InvalidAPIUsage('Invalid time')

            self.meal.time = self.data['time']

        if 'description' in self.data:
            self.meal.description = self.data['description']

        if 'calories' in self.data:
            if not isinstance(self.data['calories'], int) or self.data['calories'] <= 0:
                abort(400, 'Invalid calories value')

            self.meal.calories = self.data['calories']

        self.meal.save()
        return jsonify(rest_serializers.serialize_meal(self.meal))


@app.errorhandler(InvalidAPIUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

api.add_resource(Accounts, '/api/accounts', endpoint='accounts')
api.add_resource(Account, '/api/accounts/<int:account_id>', endpoint='account')
api.add_resource(Meals, '/api/accounts/<int:account_id>/meals', endpoint='meals')
api.add_resource(Meal, '/api/accounts/<int:account_id>/meals/<int:meal_id>', endpoint='meal')


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
