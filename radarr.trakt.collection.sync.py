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

def get_trakt_collection():
    req = trakt.get_oauth_request('sync/collection/movies')
    trakt_movies = set()
    for movie in req:
        imdb = movie["movie"]["ids"]["imdb"]
        trakt_movies.add(imdb)
    return trakt_movies

def get_radarr_collection():
    radarr_movies = set()
    radarr_url = config.RADARR_URL
    radarr_key = config.RADARR_SESSION
    radarrSession = requests.Session()
    radarrSession.trust_env = False
    radarrMovies = radarrSession.get('{0}/api/movie?apikey={1}'.format(radarr_url, radarr_key))
    if radarrMovies.status_code != 200:
      print('Radarr server error - response {}'.format(radarrMovies.status_code))
      sys.exit(0)
    for movie in radarrMovies.json():
        if movie['downloaded']:
            radarr_movies.add(movie['imdbId'])
    return radarr_movies

def main():

    radarr_collection = get_radarr_collection()
    trakt_collection = get_trakt_collection()
    
    post_data_add = []
    post_data_remove = []

    for imdb in radarr_collection:
        if imdb in trakt_collection:
            continue
        print('Movie in Radarr but not in Trakt. Will add {0}...'.format(imdb))
        post_data_add.append({'ids': {'imdb': '{0}'.format(imdb)}})    
    pprint(trakt.post_oauth_request('sync/collection', data={'movies': post_data_add}).json())

    for imdb in trakt_collection:
        if imdb in radarr_collection:
            continue
        print('Movie in Trakt but not in Radarr. Will delete {0}...'.format(imdb))
        post_data_remove.append({'ids': {'imdb': '{0}'.format(imdb)}})
    pprint(trakt.post_oauth_request('sync/collection/remove', data={'movies': post_data_remove}).json())


if __name__ == '__main__':
    main()
