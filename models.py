from peewee import *
from config import settings
import datetime

db = MySQLDatabase(settings['database']['name'], **settings['database']['params'])


class Account(Model):
    name = CharField()
    email = CharField(unique=True)
    password = CharField()
    active = BooleanField(default=False)
    created_dt = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
