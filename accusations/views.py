import re
from datetime import datetime

import requests
from django.shortcuts import render

api_key = 'xoxp-34556136643-34610936081-37277544212-a20f181123'


class User:
    def __init__(self, kwargs):
        self.__dict__.update(kwargs)


def send(method, **params):
    params['token'] = api_key
    r = requests.post(
        'https://slack.com/api/' + method,
        params=params
    )
    if not r.json()['ok']:
        raise Exception(r.json()['error'])
    return r.json()


users = {x['id']: User(x) for x in send('users.list')['members']}


def get_accusation_list():
    accusations = []
    messages = send(
        'search.messages',
        query='in:accusations after:yesterday',
        sort_dir='asc'
    )['messages']['matches']
    for message in messages:
        print(message['text'])
        if re.match(r'a(ccuse|bsolve): <@\w+>', message['text'].lower()) and len(message['text'].split()) == 2:
            if (message['is_bot'] if 'is_bot' in message else 'false') == 'false':
                accusations.append(
                    [
                        message['user'],
                        message['text'].split(':')[0].lower(),
                        message['text'].split('@')[1][:-1],
                        datetime.fromtimestamp(float(message['ts'])).isoformat().split('T')[1].split('.')[0]
                    ]
                )
    return [
        [
            users[a[0]].real_name,
            a[1],
            users[a[2]].real_name,
            a[3]
        ] for a in accusations
        ]


def get_accusation_totals():
    accusation_totals = {}
    accusations = get_accusation_list()
    for accusation in accusations:
        name, action, target, time = accusation
        if action == 'accuse':
            for l in accusation_totals:
                if name in accusation_totals[l]:
                    accusation_totals[l].remove(name)
            if target in accusation_totals:
                accusation_totals[target].append(name)
            else:
                accusation_totals[target] = [name]
        elif action == 'absolve':
            if target in accusation_totals:
                accusation_totals[target].remove(name)
    t = {}
    for a in accusation_totals:
        if not len(accusation_totals[a]) == 0:
            t[a] = accusation_totals[a]
    accusation_totals = t
    return [[a, len(accusation_totals[a]), ', '.join(accusation_totals[a])] for a in accusation_totals]


def index(request):
    context = {
        'accusation_list': reversed(get_accusation_list()),
        'accusation_totals': get_accusation_totals()
    }
    return render(request, 'accusations/accusations.html', context=context)
