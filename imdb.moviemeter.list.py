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

from lib import trakt

try:
    import config
except ImportError:
    print(('Please see config.py.example, update the '
           'values and rename it to config.py'))
    sys.exit(1)

IMDB_URL = 'https://www.imdb.com/chart/moviemeter/'

def get_moviemeter_ids():
    response = requests.get(IMDB_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    moviemeter_movies = []
    for link in soup.find_all('div', {'data-recordmetrics': 'true'}):
        moviemeter_movies.append(link.get('data-tconst'))
    return moviemeter_movies

def get_trakt_ids(list_id):
    req = trakt.get_oauth_request('users/me/lists/{0}/items'.format(list_id))
    trakt_movies = set()
    for movie in req:
        imdb = movie["movie"]["ids"]["imdb"]
        trakt_movies.add(imdb)
    return trakt_movies

def main():
    list_id = trakt.get_list_id(config.TRAKT_LIST_MOVIEMETER_NAME)
    list_api_url = 'users/me/lists/{0}/items'.format(list_id)

    # update list description
    trakt.put_oauth_request('users/me/lists/{0}'.format(list_id), data={
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
        #print('Will delete {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}}) 
    list_api_url_rm = 'users/me/lists/{0}/items/remove'.format(list_id)
    pprint(trakt.post_oauth_request(list_api_url_rm, data={'movies': post_data}).json())

    # add missing list to trakt from pirated list   
    post_data = []

    for imdb in moviemeter_list:
        print('Will add {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}})
    pprint(trakt.post_oauth_request(list_api_url, data={'movies': post_data}).json())

if __name__ == '__main__':
    main()
