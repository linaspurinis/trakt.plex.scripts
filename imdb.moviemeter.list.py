#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function

import json
import os
import re
import sys
import time
from pprint import pprint
from datetime import datetime

import requests

import urllib.request
from bs4 import BeautifulSoup

try:
    import config
except ImportError:
    print(('Please see config.py.example, update the '
           'values and rename it to config.py'))
    sys.exit(1)

HERE = os.path.abspath(os.path.dirname(__file__))
CACHEFILE = os.path.join(HERE, '.local.db')
APIURL = 'https://api.trakt.tv'
IMDB_URL = 'https://www.imdb.com/chart/moviemeter/'


localdb = {}
if os.path.exists(CACHEFILE):
    with open(CACHEFILE, 'r') as fp:
        localdb = json.load(fp)


def db_set(key, value):
    localdb[key] = value
    with open(CACHEFILE, 'w') as fp:
        json.dump(localdb, fp, indent=2, sort_keys=True)


def get_oauth_headers():
    headers = {
        'Content-type': 'application/json',
        'trakt-api-key': config.CLIENT_ID,
        'trakt-api-version': '2',
    }

    access_token_expires = float(localdb.get('access_token_expires', 0))
    access_token = localdb.get('access_token')
    refresh_token = localdb.get('refresh_token')

    if access_token_expires > time.time() and access_token:
        headers['Authorization'] = 'Bearer %s' % access_token

    else:
        print('Acquiring access_token, refresh_token={0}...'.format(
            refresh_token
        ))
        if refresh_token:
            req = requests.post(
                '{0}/oauth/token'.format(APIURL),
                headers=headers,
                json={
                    'refresh_token': refresh_token,
                    'client_id': config.CLIENT_ID,
                    'client_secret': config.CLIENT_SECRET,
                    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
                    'grant_type': 'refresh_token',
                })
            res = req.json()
            db_set('access_token', res['access_token'])
            db_set('refresh_token', res['refresh_token'])
            db_set('access_token_expires', time.time() + res['expires_in'] - (14 * 24 * 3600))
            print('New access_token acquired!')
        else:
            print('No refresh_token, manual action needed...')
            req = requests.post(
                '{0}/oauth/device/code'.format(APIURL),
                json={
                    'client_id': config.CLIENT_ID,
                }
            )
            assert req.ok, (req, req.content)

            data = req.json()
            start_time = time.time()

            print('Go to {verification_url} and enter code {user_code}'.format(
                verification_url=data['verification_url'],
                user_code=data['user_code'],
            ))

            interval = data['interval']

            while 1:
                if start_time + data['expires_in'] < time.time():
                    print('Too late, you need to start from beginning :(')
                    sys.exit(1)

                time.sleep(interval)
                req = requests.post(
                    '{0}/oauth/device/token'.format(APIURL),
                    json={
                        'client_id': config.CLIENT_ID,
                        'client_secret': config.CLIENT_SECRET,
                        'code': data['device_code'],
                    }
                )

                if req.status_code == 200:
                    res = req.json()
                    print('New tokens acquired!')
                    db_set('access_token', res['access_token'])
                    db_set('refresh_token', res['refresh_token'])
                    db_set('access_token_expires', time.time() + res['expires_in'] - (14 * 24 * 3600))
                    break
                elif req.status_code == 400:
                    print('Pending - waiting for the user to authorize your app')
                elif req.status_code == 404:
                    print('Not Found - invalid device_code')
                    return
                elif req.status_code == 409:
                    print('Already Used - user already approved this code')
                    return
                elif req.status_code == 410:
                    print('Expired - the tokens have expired, restart the process')
                    return
                elif req.status_code == 418:
                    print('Denied - user explicitly denied this code')
                    return
                elif req.status_code == 429:
                    print('Slow Down - your app is polling too quickly')
                    time.sleep(interval)
        headers['Authorization'] = 'Bearer %s' % res['access_token']
    return headers


def get_oauth_request(path, *args, **kwargs):
    headers = get_oauth_headers()
    if 'headers' in kwargs:
        headers.update(kwargs.pop('headers'))
    req = requests.get(
        '{0}/{1}'.format(APIURL, path), headers=headers, **kwargs
    )
    assert req.ok, (req, req.content)
    return req.json()


def post_oauth_request(path, data, *args, **kwargs):
    req = requests.post(
        '{0}/{1}'.format(APIURL, path),
        json=data, headers=get_oauth_headers(), **kwargs
    )
    assert req.ok, (req, req.content)
    return req

def put_oauth_request(path, data, *args, **kwargs):
    req = requests.put(
        '{0}/{1}'.format(APIURL, path),
        json=data, headers=get_oauth_headers(), **kwargs
    )
    assert req.ok, (req, req.content)
    return req

def get_list_id(name):
    key = 'list-id:{0}'.format(name)
    if key in localdb:
        return localdb[key]
    req = get_oauth_request('users/me/lists')
    existing_lists = [x['name'] for x in req]
    if name not in existing_lists:
        post_oauth_request('users/me/lists', data={
            'name': name,
        })
        time.sleep(0.5)
        req = get_oauth_request('users/me/lists')
    res = [x for x in req if x['name'] == name]
    if not res:
        raise Exception('Could not find the list "{0}" :('.format(name))
    list_id = res[0]['ids']['trakt']
    db_set(key, list_id)   
    return list_id


def get_moviemeter_ids():
    response = requests.get(IMDB_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    moviemeter_movies = []
    for link in soup.find_all('div', {'data-recordmetrics': 'true'}):
        moviemeter_movies.append(link.get('data-tconst'))
    return moviemeter_movies


def get_trakt_ids(list_id):
    req = get_oauth_request('users/me/lists/{0}/items'.format(list_id))
    trakt_movies = set()
    for movie in req:
        imdb = movie["movie"]["ids"]["imdb"]
        trakt_movies.add(imdb)
    return trakt_movies

def main():
    list_id = get_list_id(config.TRAKT_LIST_MOVIEMETER_NAME)
    list_api_url = 'users/me/lists/{0}/items'.format(list_id)

    # update list description
    put_oauth_request('users/me/lists/{0}'.format(list_id), data={
        'description': \
        'IMDb Most Popular Movies top 100' +
        '\r\n\r\n' + 'URL: https://www.imdb.com/chart/moviemeter/' +
        '\r\n' + 'Source code: https://github.com/linaspurinis/trakt.lists/' +
        '\r\n\r\nUpdated at ' + datetime.today().strftime('%Y-%m-%d')
    })
    time.sleep(0.5) 

    print('List URL - https://trakt.tv/users/me/lists/{0}'.format(list_id))
    print('')
    
    # delete movies trakt list   
    trakt_list = get_trakt_ids(list_id)
    moviemeter_list = get_moviemeter_ids()
    post_data = []

    for imdb in trakt_list:
        print('Will delete {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}}) 
    list_api_url_rm = 'users/me/lists/{0}/items/remove'.format(list_id)
    pprint(post_oauth_request(list_api_url_rm, data={'movies': post_data}).json())

    # add missing list to trakt from pirated list   
    post_data = []

    for imdb in moviemeter_list:
        print('Will add {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}})
    pprint(post_oauth_request(list_api_url, data={'movies': post_data}).json())


if __name__ == '__main__':
    main()
