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

from lib import movieinfo
from lib import trakt

try:
    import config
except ImportError:
    print(('Please see config.py.example, update the '
           'values and rename it to config.py'))
    sys.exit(1)
    
def get_trakt_ids(list_id):
    req = trakt.get_oauth_request('users/me/lists/{0}/items'.format(list_id))
    trakt_movies = []
    for movie in req:
        imdb = movie["movie"]["ids"]["imdb"]
        trakt_movies.append(imdb)
    return trakt_movies

def get_anticipated_ids():
    list_api_url_1 = 'movies/anticipated/?limit=100'
    req = trakt.get_oauth_request(list_api_url_1)
    trakt_movies = []
    for movie in req:
        imdb = movie["movie"]["ids"]["imdb"]
        trakt_movies.append(imdb)
    return trakt_movies

def main():
    list_id = trakt.get_list_id(config.TRAKT_LIST_NAME_ANTICIPATED)
    list_api_url = 'users/me/lists/{0}/items'.format(list_id)
        
    # update list description
    trakt.put_oauth_request('users/me/lists/{0}'.format(list_id), data={
        'description': 'Updated at ' + datetime.today().strftime('%Y-%m-%d') + 
        '\r\nThe most anticipated movies based on the number of lists a movie appears on.'+
        '\r\nSource: https://trakt.tv/movies/anticipated?limit=100'
    })
    time.sleep(0.5) 

    print('List URL - https://trakt.tv/users/me/lists/{0}'.format(list_id))
    print('')
    
    # delete movies from trakt list no longer in anticipated list   
    post_data = []
    trakt_anticipated_list = get_anticipated_ids()
    trakt_list = get_trakt_ids(list_id)

    for imdb in trakt_list:
        #print('Will delete {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}}) 
    list_api_url_rm = 'users/me/lists/{0}/items/remove'.format(list_id)
    pprint(trakt.post_oauth_request(list_api_url_rm, data={'movies': post_data}).json())

    # add missing list to trakt from top watched list    
    post_data = []
    for imdb in trakt_anticipated_list:    
        print('Will add {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}})
    pprint(trakt.post_oauth_request(list_api_url, data={'movies': post_data}).json())

if __name__ == '__main__':
    main()
