from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from werkzeug.security import generate_password_hash
from validate_email import validate_email
from config import settings
import json
import models
import tasks


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

    def post(self):
        try:
            self.data = json.loads(request.data)
        except:
            raise InvalidAPIUsage('Invalid JSON received')


class Registrations(DemoResource):
    def post(self):
        super(Registrations, self).post()

        if 'email' not in self.data or 'password' not in self.data:
            raise InvalidAPIUsage('Missing parameter(s)')
        if not validate_email(self.data['email']):
            raise InvalidAPIUsage('Invalid email address')
        if len(self.data['password']) < 8:
            raise InvalidAPIUsage('Invalid password')

        try:
            models.Account.get(email=self.data['email'])
            raise InvalidAPIUsage('Email already registered')
        except models.Account.DoesNotExist:
            account = models.Account(email=self.data['email'], password=generate_password_hash(self.data['password']))
            account.save()
            tasks.send_activation_email.delay(account.id)
            return '', 204


@app.errorhandler(InvalidAPIUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

api.add_resource(Registrations, '/api/registrations')

app.secret_key = settings['secret_key']
if __name__ == "__main__":
    app.run(debug=True)
