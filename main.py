from flask import Flask, request
import logging
import json
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {'москва': ['1030494/d9ef8c16772da410d978', '1521359/2407f60e6ed44c34e4fe'],
          'нью-йорк': ['965417/01a11c292efc8d3c59df', '1030494/a604aa188b2a4e660e62'],
          'париж': ['1540737/16bd53b968e9d445a0e0', '1652229/20c9895502d1feac35bc'],
          'сидней': ['1540737/07a7b5a61dbc8d53dc3c', '1656841/c718f6671b27649d4422']}

sessionStorage = {}


@app.route('/', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {'session': request.json['session'],
                'version': request.json['version'],
                'response': {'end_session': False}}
    handleDialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return json.dumps(response)


def handleDialog(res, req):
    userId = req['session']['user_id']
    res['response']['buttons'].append({'title': 'Помощь', 'hide': False})
    if 'помощь' in req['request']['nlu']['tokens']:
        res['response']['text'] = 'Это игра "Угадай город". Вам нужно познакомиться с Алисой и отправлять ей названия городов.'
        return
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[userId] = {'name': None}
        return
    if sessionStorage[userId]['name'] is None:
        name = getName(req)
        if name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[userId]['name'] = name
            res['response']['text'] = f'Приятно познакомиться, {name.title()}. Я - Алиса. Какой город хочешь увидеть?'
            res['response']['buttons'] = [{'title': city.title(), 'hide': True} for city in cities]
    else:
        city = getCity(req)
        if city in cities:
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'Я знаю этот город!'
            res['response']['card']['image_id'] = random.choice(cities[city])
            res['response']['text'] = 'Я угадал!'
        else:
            res['response']['text'] = 'Первый раз слышу об этом городе. Попробуй ещё разок!'


def getName(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


def getCity(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


if __name__ == '__main__':
    app.run()
