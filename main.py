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
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[userId] = {'name': None, 'game': False}
        return
    if sessionStorage[userId]['name'] is None:
        name = getName(req)
        if name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[userId]['name'] = name
            sessionStorage[userId]['guessed'] = []
            res['response']['text'] = f'Приятно познакомиться, {name.title()}. Я - Алиса. Отгадаешь город по фото?'
            res['response']['buttons'] = [{'title': 'Да', 'hide': True},
                                          {'title': 'Нет', 'hide': True}]
    else:
        if not sessionStorage[userId]['game']:
            if 'да' in req['request']['nlu']['tokens']:
                if len(sessionStorage[userId]['guessed']) == len(cities.keys()):
                    res['response']['text'] = 'Ты отгадал все города!'
                    res['end_session'] = True
                else:
                    sessionStorage[userId]['game'] = True
                    sessionStorage[userId]['attempt'] = 1
                    playGame(res, req)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['end_session'] = True
            else:
                res['response']['text'] = 'Не поняла ответа! Так да или нет?'
                res['response']['buttons'] = [{'title': 'Да', 'hide': True},
                                              {'title': 'Нет', 'hide': True}]
        else:
            playGame(res, req)


def playGame(res, req):
    userId = req['session']['user_id']
    attempt = sessionStorage[userId]['attempt']
    res['response']['buttons'] = [{'title': 'Помощь', 'hide': True}]
    if 'помощь' in req['request']['nlu']['tokens']:
        res['response']['text'] = 'Вам нужно узнать город, какой загадала Алиса. Свои варианты отправляйте ей ;)'
        return
    if attempt == 1:
        city = random.choice(list(cities))
        while city in sessionStorage[userId]['guessed']:
            city = random.choice(list(cities))
        sessionStorage[userId]['city'] = city
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = 'Тогда сыграем!'
    else:
        city = sessionStorage[userId]['city']
        if getCity(req) == city:
            res['response']['text'] = 'Правильно! Сыграем ещё?'
            res['response']['buttons'] = [{'title': 'Да', 'hide': True},
                                          {'title': 'Нет', 'hide': True},
                                          {'title': 'Покажи город на карте', 'hide': True, 'url': 'https://yandex.ru/maps/?mode=search&text=' + city}]
            sessionStorage[userId]['guessed'].append(city)
            sessionStorage[userId]['game'] = False
            return
        else:
            if attempt == 3:
                res['response']['text'] = f'Вы пытались. Это {city.title()}. Сыграем ещё?'
                res['response']['buttons'] = [{'title': 'Да', 'hide': True},
                                              {'title': 'Нет', 'hide': True}]
                sessionStorage[userId]['game'] = False
                sessionStorage[userId]['guessed'].append(city)
                return
            else:
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Неправильно. Вот тебе дополнительное фото'
                res['response']['card']['image_id'] = cities[city][attempt - 1]
                res['response']['text'] = 'А вот и не угадал!'
    sessionStorage[userId]['attempt'] += 1


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
