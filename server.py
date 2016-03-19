from flask import Flask, request, jsonify, url_for, send_from_directory, make_response
from flask.views import MethodViewType
from flask_restful import Resource, Api
from itsdangerous import BadData, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from config import settings
from dateutil.parser import parse as parse_date
import wrapt
import json
import types
import models
import utils
import tasks
import logger


log = logger.getLogger(__name__)
app = Flask(__name__)
api = Api(app)


class AppError(Exception):
    def __init__(self, message, status_code=None, *args, **kwargs):
        super(AppError, self).__init__()

        self.code = status_code or 400
        kwargs['error'] = message
        self.data = kwargs


class APIError(HTTPException):
    def __init__(self, message, status_code=None, description=None, response=None, **kwargs):
        super(APIError, self).__init__(description, response)

        self.code = status_code or 400
        kwargs['error'] = message
        self.data = kwargs


# decorator to allow certain methods to require logged in users. It can also enforce certain roles. If the function
# receives an account or a roles parameter, those get populated by the decorator as well
def verify_token_get_account(roles=None, accountid_free_roles=[], account_should_have_roles=[], kwargs={}):
    # check if the user is at least sending a bearer token
    if 'Authorization' not in request.headers or len(request.headers['Authorization']) < 8 or request.headers['Authorization'][:7] != 'Bearer ':
        raise APIError('Unauthorized', 401)

    token = request.headers['Authorization'][7:]
    try:
        token = utils.urlserializer.loads(token, settings['oauth-token-expiration-seconds'], salt='access-token')
    except BadData, e:
        log.error(e)
        raise APIError('Unauthorized', 401)

    if roles and not any(r for r in roles if r in token['roles']):
        raise APIError('Unauthorized', 401)

    account_id = (kwargs['account_id'] if 'account_id' in kwargs else 0) or token['id']
    if account_id != token['id'] and not any(r for r in accountid_free_roles if r in token['roles']):
        raise APIError('Unauthorized', 401)

    # this is the destination account, to allow certain actions only if the account the request
    # is affecting if that account has certain roles
    if account_should_have_roles:
        roles = map(lambda x: x.code, models.Role.select().join(models.AccountRole).where(models.AccountRole.account == models.get_active_account(id=account_id)))
        if not any(r for r in account_should_have_roles if r in roles):
            raise APIError("This action can't be performed on this account")

    return account_id, token


def require_auth(roles=None, accountid_free_roles=[], account_should_have_roles=[]):
    def decorator(funct_or_class):
        def decorate_function(funct):
            def decorated_function(*args, **kwargs):
                account_id, token = verify_token_get_account(roles, accountid_free_roles, account_should_have_roles, kwargs)

                try:
                    account = models.get_active_account(id=account_id)
                except models.Account.DoesNotExist:
                    raise APIError('Not Found', 404)

                if 'account_id' in funct.__code__.co_varnames:
                    kwargs['account_id'] = account_id

                if 'account' in funct.__code__.co_varnames:
                    kwargs['account'] = account

                if 'roles' in funct.__code__.co_varnames:
                    kwargs['roles'] = token['roles']

                if len(args) and isinstance(args[0], Resource):
                    args[0].logged_in_account_id = token['id']
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
                raise APIError('Invalid JSON received')
            return wrapped(*args, **kwargs)

        for action in (a for a in attrs if a in ('get', 'post', 'put', 'delete')):
            if action in ('post', 'put'):
                attrs[action] = add_json_parse(attrs[action])

            if 'pre_execute' in attrs:
                attrs[action] = add_pre_execute(attrs[action])

        return super(ResourceMeta, cls).__new__(cls, name, bases, attrs)


class DemoResource(Resource):
    __metaclass__ = ResourceMeta

    def return_paginated(self, query, endpoint, urlparams):
        try:
            page = int(request.args['page'])
        except:
            page = 1

        try:
            items_per_page = int(request.args['items-per-page'])
        except:
            items_per_page = 15

        items_per_page = items_per_page if items_per_page <= 100 else 100
        total_items = query.count()

        for k in request.args:
            urlparams[k] = request.args[k]

        next_url = previous_url = None
        if total_items > page * items_per_page:
            urlparams['page'] = page + 1
            next_url = url_for(endpoint, _external=True, **urlparams)

        if page > 1:
            urlparams['page'] = page - 1
            previous_url = url_for(endpoint, _external=True, **urlparams)

        query = query.offset((page - 1) * items_per_page).limit(items_per_page)

        return {
            'data': map(lambda x: x.serialize(), query),
            'pagination': {
                'total_items': total_items,
                'next': next_url,
                'previous': previous_url
            }
        }


class Accounts(DemoResource):
    @require_auth(roles=['user-manager', 'admin'])
    def get(self):
        accounts = models.Account.select().where(models.Account.deleted==False).order_by(models.Account.name)

        if 'name' in request.args:
            accounts = accounts.where(models.Account.name % ('%%%s%%' % request.args['name']))

        if 'email' in request.args:
            accounts = accounts.where(models.Account.email % ('%%%s%%' % request.args['email']))

        return self.return_paginated(accounts, 'accounts', {})

    def post(self):
        if any(f for f in ('email', 'password', 'name') if f not in self.data):
            raise APIError('Missing parameter(s)')
        if not utils.is_valid_email(self.data['email']):
            raise APIError('Invalid email address')
        if len(self.data['password']) < 8:
            raise APIError('Invalid password')
        if len(self.data['name']) < 3:
            raise APIError('Invalid name')

        try:
            models.get_active_account(email=self.data['email'])
            raise APIError('Email already registered')
        except models.Account.DoesNotExist:
            account = models.Account(name=self.data['name'], email=self.data['email'],
                                     password=generate_password_hash(self.data['password']))
            account.save()

            # make this account a user
            models.AccountRole(account=account, role=models.Role.get(code='user')).save()

            update_token = utils.urlserializer.dumps({'id': account.id, 'active': True}, salt='account-update')
            url = url_for('public', path='apply-account-changes', account_id=account.id, token=update_token,
                          _external=True)

            tasks.send_activation_email.delay(account.id, url, update_token)
            return created_response('account', account_id=account.id)


class Account(DemoResource):
    def update_account(self, account_id):
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
                tasks.send_account_update_email.delay(account_id, url, update_token, decoded_payload.get('email'))
            except BadData:
                raise APIError('Invalid token')
            raise APIError('Your token has expired. We have sent you a new link to your email')
        except BadData, e:
            log.error(e)
            raise APIError('Invalid token')

        if update_data['id'] != account_id:
            raise APIError('Invalid token')

        try:
            account = models.get_active_account(id=account_id)
        except models.Account.DoesNotExist:
            raise APIError('Account does not exist', 404)

        del update_data['id']
        for k in update_data:
            setattr(account, k, update_data[k])

        account.save()
        return '', 204

    def put(self, account_id):
        # if the account is being updated through the update_token, then we don't need to authenticate
        # the user (they may not even be able to log in)
        if 'update_token' in self.data:
            return self.update_account(account_id)

        # verify authorization
        if 'roles' in self.data:
            account_id, token = verify_token_get_account(['admin'], ['admin'], kwargs={'account_id': account_id})
        else:
            account_id, token = verify_token_get_account(['user', 'user-manager', 'admin'], ['user-manager', 'admin'], kwargs={'account_id': account_id})

        try:
            account = models.get_active_account(id=account_id)
        except models.Account.DoesNotExist:
            raise APIError('Account not found', 404)

        # perform updates
        if 'roles' in self.data:
            if not isinstance(self.data['roles'], list) or any(r for r in self.data['roles'] if not isinstance(r, basestring)):
                raise APIError('Invalid roles value')

            final_roles = models.Role.select().where(models.Role.code << self.data['roles'])
            if len(final_roles) != len(self.data['roles']):
                raise APIError('Invalid roles value')

            current_roles = models.Role.select().join(models.AccountRole).where(models.AccountRole.account == account)

            # handle deletions
            for role in [r for r in current_roles if r not in final_roles]:
                models.AccountRole.get(models.AccountRole.account == account, models.AccountRole.role == role).delete_instance()

            # handle additions
            for role in [r for r in final_roles if r not in current_roles]:
                models.AccountRole(account=account, role=role).save()

        if 'name' in self.data:
            if not isinstance(self.data['name'], basestring):
                raise APIError('Invalid name')

            account.name = self.data['name']

        if 'email' in self.data:
            if not utils.is_valid_email(self.data['email']):
                raise APIError('Invalid email')

            if models.get_active_account(email=self.data['email']):
                raise APIError('Email already used')

            update_token = utils.urlserializer.dumps({'id': account.id, 'email': self.data['email']}, salt='account-update')
            url = url_for('public', path='apply-account-changes', account_id=account.id, token=update_token,
                          _external=True)
            tasks.send_account_update_email.delay(account.id, url, update_token, email=self.data['email'])

        if 'password' in self.data:
            if len(self.data['password']) < 8:
                raise APIError('Invalid password')

            if 'current_password' not in self.data:
                raise APIError('Missing current_password')

            if not check_password_hash(account.password, self.data['current_password']):
                raise APIError('Invalid current_password')

            account.password = generate_password_hash(self.data['password'])

        account.save()
        return '', 204

    @require_auth(roles=['user', 'user-manager', 'admin'], accountid_free_roles=['admin', 'user-manager'])
    def get(self, account_id):
        return self.account.serialize()

    @require_auth(roles=['user-manager', 'admin'], accountid_free_roles=['admin', 'user-manager'])
    def delete(self, account_id):
        if self.logged_in_account_id == account_id:
            raise APIError("You can't delete your own account")

        self.account.deleted = True
        self.account.save()

        return '', 204


@require_auth(roles=['user', 'admin'], accountid_free_roles=['admin'], account_should_have_roles=['user'])
class Meals(DemoResource):
    def post(self, account_id):
        if any(f for f in ('date', 'time', 'description', 'calories') if f not in self.data):
            raise APIError('Missing Parameter(s)')

        if not utils.is_valid_date(self.data['date']):
            raise APIError('Invalid date')

        if not utils.is_valid_time(self.data['time']):
            raise APIError('Invalid time format')

        if not isinstance(self.data['calories'], int) or self.data['calories'] <= 0:
            raise APIError('Invalid calories value')

        meal_dt = parse_date('%s %s' % (self.data['date'], self.data['time']))

        meal = models.Meal(account=self.account, date=meal_dt.date(), time=self.data['time'],
                           description=self.data['description'], calories=self.data['calories'])
        meal.save()

        return created_response('meal', account_id=self.account.id, meal_id=meal.id)

    def get(self, account_id):
        meals = models.Meal.select().where(models.Meal.account == self.account).order_by(models.Meal.date.desc(), models.Meal.time.desc())

        if 'meal-date-from' in request.args:
            if not utils.is_valid_date(request.args['meal-date-from']):
                raise APIError('Invalid meal-date-from format')

            dt = parse_date(request.args['meal-date-from']).date()
            meals = meals.where(models.Meal.date >= dt)

        if 'meal-date-to' in request.args:
            if not utils.is_valid_date(request.args['meal-date-to']):
                raise APIError('Invalid meal-date-to format')

            dt = parse_date(request.args['meal-date-to']).date()
            meals = meals.where(models.Meal.date <= dt)

        if 'meal-time-from' in request.args:
            if not utils.is_valid_time(request.args['meal-time-from']):
                raise APIError('Invalid meal-time-from format')

            meals = meals.where(models.Meal.time >= request.args['meal-time-from'])

        if 'meal-time-to' in request.args:
            if not utils.is_valid_time(request.args['meal-time-to']):
                raise APIError('Invalid meal-time-to format')

            meals = meals.where(models.Meal.time <= request.args['meal-time-to'])

        return self.return_paginated(meals, 'meals', {'account_id': account_id})


@require_auth(roles=['user', 'admin'], accountid_free_roles=['admin'], account_should_have_roles=['user'])
class Meal(DemoResource):
    def pre_execute(self, *args, **kwargs):
        try:
            self.meal = models.Meal.get(models.Meal.id == kwargs['meal_id'], models.Meal.account == self.account)
        except models.Meal.DoesNotExist:
            raise APIError('Meal not found', 404)

    def get(self, account_id, meal_id):
        return self.meal.serialize()

    def delete(self, account_id, meal_id):
        self.meal.delete_instance()
        return '', 204

    def put(self, account_id, meal_id):
        if any(k for k in self.data if k not in ('id', 'account', 'date', 'time', 'description', 'calories')):
            raise APIError('Invalid parameters')

        # skipping id and account fields

        if 'date' in self.data:
            if not utils.is_valid_date(self.data['date']):
                raise APIError('Invalid date')

            self.meal.date = parse_date(self.data['date']).date()

        if 'time' in self.data:
            if not utils.is_valid_time(self.data['time']):
                raise APIError('Invalid time')

            self.meal.time = self.data['time']

        if 'description' in self.data:
            self.meal.description = self.data['description']

        if 'calories' in self.data:
            if not isinstance(self.data['calories'], int) or self.data['calories'] <= 0:
                raise APIError('Invalid calories value')

            self.meal.calories = self.data['calories']

        self.meal.save()
        return self.meal.serialize()


@app.errorhandler(AppError)
def handle_invalid_usage(error):
    response = jsonify(error.data)
    response.status_code = error.code
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
        raise AppError('invalid_request')

    if request.form['grant_type'] != 'password':
        # only implementing Resource Owner Password Credentials Grant from RFC 6749
        raise AppError('unsupported_grant_type')

    try:
        account = models.get_active_account(email=request.form['username'])
    except models.Account.DoesNotExist:
        raise AppError('invalid_grant')

    if not check_password_hash(account.password, request.form['password']):
        raise AppError('invalid_grant')

    if not account.active:
        update_token = utils.urlserializer.dumps({'id': account.id, 'active': True}, salt='account-update')
        url = url_for('public', path='apply-account-changes', account_id=account.id, token=update_token,
                      _external=True)
        tasks.send_activation_email.delay(account.id, url, update_token)
        raise AppError('invalid_grant', error_description='Your account is not active. An email has been sent '
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
