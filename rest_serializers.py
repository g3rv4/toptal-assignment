from playhouse.shortcuts import model_to_dict
from flask import url_for


def serialize_meal(meal):
    res = model_to_dict(meal, recurse=False)
    res['id'] = url_for('meal', account_id=res['account'], meal_id=res['id'], _external=True)
    res['account'] = url_for('account', account_id=res['account'], _external=True)
    res['date'] = res['date'].strftime('%Y-%m-%d')
    res['time'] = res['time'].strftime('%H:%M:%S')
    return res


def serialize_meals(meals):
    return map(serialize_meal, meals)
