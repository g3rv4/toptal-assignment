from peewee import *
from config import settings
import datetime
import rest_serializers

db = MySQLDatabase(settings['database']['name'], **settings['database']['params'])


class DemoModel(Model):
    def serialize(self):
        if hasattr(rest_serializers, 'serialize_%s' % self._meta.db_table):
            return getattr(rest_serializers, 'serialize_%s' % self._meta.db_table)(self)
        raise Exception('Serializer not set for %s' % self._meta.db_table)


class Account(DemoModel):
    name = CharField()
    email = CharField()
    password = CharField()
    active = BooleanField(default=False)
    deleted = BooleanField(default=False)
    created_dt = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        indexes = (
            (('email', 'deleted'), False),
        )


class Role(DemoModel):
    name = CharField()
    code = CharField(unique=True)

    class Meta:
        database = db


class AccountRole(DemoModel):
    account = ForeignKeyField(Account)
    role = ForeignKeyField(Role)

    class Meta:
        database = db


class Meal(DemoModel):
    account = ForeignKeyField(Account)
    date = DateField(index=True)
    time = TimeField(index=True)
    description = CharField()
    calories = IntegerField()

    class Meta:
        database = db


def get_active_account(*args, **kwargs):
    return Account.get(deleted=False, *args, **kwargs)
