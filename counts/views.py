import requests
from django.shortcuts import render
import os

api_key = os.environ['slack_api_key']

search_channels = ['city_hall', 'watercooler']


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


users = {x['name']: User(x) for x in send('users.list')['members']}


def get_message_counts():
    message_counts = []
    for user in users:
        if not users[user].deleted:
            messages_by_user = {}
            for channel in search_channels:
                messages_by_user[channel] = send(
                    'search.messages',
                    token=api_key,
                    query='from:' + user + ' in:' + channel,
                    count=1
                )['messages']['paging']['total']
            total = sum(messages_by_user.values())
            message_counts.append((users[user].real_name, messages_by_user, total))
    message_counts.sort(key=lambda x: x[2], reverse=True)
    return message_counts


def index(request):
    context = {
        'counts': get_message_counts()
    }
    return render(request, 'counts/counts.html', context=context)
