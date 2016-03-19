from playhouse.shortcuts import model_to_dict
from flask import url_for
import datetime
import models


def serialize_meal(meal):
    res = model_to_dict(meal, recurse=False)
    res['id'] = url_for('meal', account_id=res['account'], meal_id=res['id'], _external=True)
    res['account'] = url_for('account', account_id=res['account'], _external=True)
    res['date'] = res['date'].strftime('%Y-%m-%d')
    res['time'] = res['time'].strftime('%H:%M:%S') if isinstance(res['time'], datetime.time) else res['time']
    return res


def serialize_account(account):
    res = model_to_dict(account, recurse=False)
    res['id'] = url_for('account', account_id=res['id'], _external=True)
    res['created_dt'] = res['created_dt'].strftime('%Y-%m-%d %H:%M:%S')
    res['roles'] = map(lambda x: x.code, models.Role.select().join(models.AccountRole).where(models.AccountRole.account == account))
    del res['password']
    return res
