from flask import Flask, request, jsonify
import logging
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

words = {
    'dog': '1652229/ff4e6df69e751cb0864b',
    'cat': '1533899/f09554cf9d3af83a1102',
    'mouse': '1656841/907892ddd9fb00d8a6b5',
    'horse': '1533899/d499cae814922c70bdf8',
    'cow': '1533899/45a6a6335d3b73765ad6'
}

first_letter = {
    'dog': 'd',
    'cat': 'c',
    'mouse': 'm',
    'horse': 'h',
    'cow': 'c'
}

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return jsonify(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False
        }
        return
    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            sessionStorage[user_id]['guessed_words'] = []
            res['response']['text'] = ('Приятно познакомиться, ' +
                                       f'{first_name.title()}.' +
                                       ' Я - Алиса. Напишешь английское ' +
                                       'слово по фото?')
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]
    else:
        if not sessionStorage[user_id]['game_started']:
            if 'да' in req['request']['nlu']['tokens']:
                if len(sessionStorage[user_id]['guessed_words']) == 5:
                    res['response']['text'] = 'Ты отгадал все слова'
                    res['response']['end_session'] = True
                else:
                    sessionStorage[user_id]['game_started'] = True
                    sessionStorage[user_id]['attempt'] = 1
                    play_game(res, req)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['response']['end_session'] = True
            else:
                res['response']['text'] = 'Не поняла ответа! Так да или нет?'
                res['response']['buttons'] = [
                    {
                     'title': 'Да',
                     'hide': True
                    },
                    {
                     'title': 'Нет',
                     'hide': True
                    }
                ]
        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if attempt == 1:
        word = random.choice(list(words))
        while word in sessionStorage[user_id]['guessed_words']:
            word = random.choice(list(words))
        sessionStorage[user_id]['word'] = word
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Отгадай слово по-английски?'
        res['response']['card']['image_id'] = words[word]
        res['response']['text'] = 'Тогда сыграем!'
    else:
        word = sessionStorage[user_id]['word']
        if get_word(req, word):
            res['response']['text'] = 'Правильно! Сыграем еще?'
            sessionStorage[user_id]['guessed_words'].append(word)
            sessionStorage[user_id]['game_started'] = False
            res['response']['buttons'] = [
                    {
                     'title': 'Да',
                     'hide': True
                    },
                    {
                     'title': 'Нет',
                     'hide': True
                    }
                ]
            return
        else:
            if attempt == 3:
                res['response']['text'] = (f'Вы пытались. Это {word.title()}.'
                                           + 'Сыграем еще?')
                res['response']['buttons'] = [
                    {
                     'title': 'Да',
                     'hide': True
                    },
                    {
                     'title': 'Нет',
                     'hide': True
                    }
                ]
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_words'].append(word)
            else:
                res['response']['text'] = ('А вот и не угадал! Слово ' +
                                           'начинается на букву ' +
                                           f'{first_letter[word]}')
    sessionStorage[user_id]['attempt'] += 1


def get_word(req, word):
    return (word in req['request']['nlu']['tokens'])


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
