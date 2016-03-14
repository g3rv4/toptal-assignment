from models import *
import peewee
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--action", help="action to execute", required=True, choices=['create-database'])
args = parser.parse_known_args()[0]

if args.action == 'create-database':
    db.create_tables(peewee.Model.__subclasses__())
