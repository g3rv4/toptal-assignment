import models
import peewee
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--action", help="action to execute", required=True, choices=['create-database'])
args = parser.parse_known_args()[0]

if args.action == 'create-database':
    models.db.create_tables(peewee.Model.__subclasses__())
    models.Role(name='User', code='user').save()
    models.Role(name='User Manager', code='user-manager').save()
    models.Role(name='Admin', code='admin').save()
