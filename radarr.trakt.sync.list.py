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

from lib import trakt
try:
    import config
except ImportError:
    print(('Please see config.py.example, update the '
           'values and rename it to config.py'))
    sys.exit(1)

def get_trakt_collection(list_id):
    req = trakt.get_oauth_request('users/me/lists/{0}/items'.format(list_id))
    trakt_movies = set()
    for movie in req:
        imdb = movie["movie"]["ids"]["imdb"]
        trakt_movies.add(imdb)
    return trakt_movies

def get_radarr_collection():
    radarr_movies = set()
    radarr_movies_all = set()
    radarr_url = config.RADARR_URL
    radarr_key = config.RADARR_SESSION
    radarrSession = requests.Session()
    radarrSession.trust_env = False
    radarrMovies = radarrSession.get('{0}/api/movie?apikey={1}'.format(radarr_url, radarr_key))
    if radarrMovies.status_code != 200:
      print('Radarr server error - response {}'.format(radarrMovies.status_code))
      sys.exit(0)
    for movie in radarrMovies.json():
        radarr_movies_all.add(movie['imdbId'])
        if movie['downloaded']:
            radarr_movies.add(movie['imdbId'])
    return radarr_movies, radarr_movies_all

def main():
    list_id = trakt.get_list_id('My Collection')
    # update list description
    trakt.put_oauth_request('users/me/lists/{0}'.format(list_id), data={
        'description': 'Updated at ' + datetime.today().strftime('%Y-%m-%d')
    })
    time.sleep(0.5) 

    list_id_rw = trakt.get_list_id('Radarr Watchlist')
    # update list description
    trakt.put_oauth_request('users/me/lists/{0}'.format(list_id_rw), data={
        'description': 'Updated at ' + datetime.today().strftime('%Y-%m-%d')
    })
    time.sleep(0.5) 

    radarr_collection, radarr_collection_rw = get_radarr_collection()
    trakt_collection = get_trakt_collection(list_id)
    trakt_collection_rw = get_trakt_collection(list_id_rw)
    
    post_data_add = []
    post_data_remove = []

    for imdb in radarr_collection:
        if imdb in trakt_collection:
            continue
        print('Movie in Radarr but not in Trakt. Will add {0}...'.format(imdb))
        post_data_add.append({'ids': {'imdb': '{0}'.format(imdb)}})    
    pprint(trakt.post_oauth_request('users/me/lists/{0}/items'.format(list_id), data={'movies': post_data_add}).json())


    for imdb in trakt_collection:
        if imdb in radarr_collection:
            continue
        print('Movie in Trakt but not in Radarr. Will delete {0}...'.format(imdb))
        post_data_remove.append({'ids': {'imdb': '{0}'.format(imdb)}})
    pprint(trakt.post_oauth_request('users/me/lists/{0}/items/remove'.format(list_id), data={'movies': post_data_remove}).json())

    post_data_add = []
    post_data_remove = []

    for imdb in radarr_collection_rw:
        if imdb in trakt_collection_rw:
            continue
        print('Movie in Radarr but not in Trakt. Will add {0}...'.format(imdb))
        post_data_add.append({'ids': {'imdb': '{0}'.format(imdb)}})    
    pprint(trakt.post_oauth_request('users/me/lists/{0}/items'.format(list_id_rw), data={'movies': post_data_add}).json())


    for imdb in trakt_collection_rw:
        if imdb in radarr_collection_rw:
            continue
        print('Movie in Trakt but not in Radarr. Will delete {0}...'.format(imdb))
        post_data_remove.append({'ids': {'imdb': '{0}'.format(imdb)}})
    pprint(trakt.post_oauth_request('users/me/lists/{0}/items/remove'.format(list_id_rw), data={'movies': post_data_remove}).json())

if __name__ == '__main__':
    main()
