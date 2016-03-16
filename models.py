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


class Role(Model):
    name = CharField()
    code = CharField(unique=True)

    class Meta:
        database = db


class AccountRole(Model):
    account = ForeignKeyField(Account)
    role = ForeignKeyField(Role)

    class Meta:
        database = db


class Meal(Model):
    account = ForeignKeyField(Account)
    meal_date = DateField(index=True)
    meal_time = TimeField(index=True)
    description = CharField()
    calories = IntegerField()

    class Meta:
        database = db
