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
import movieinfo
import trakt

try:
    import config
except ImportError:
    print(('Please see config.py.example, update the '
           'values and rename it to config.py'))
    sys.exit(1)

movieinfo.OMDB_APIKEY = config.OMDB_APIKEY

def get_radarr_collection():
    radarr_movies = []
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
            if movie['imdbId']:
              radarr_movies.append(movie['imdbId'])
    return radarr_movies

def get_trakt_ids(list_id):
    req = trakt.get_oauth_request('users/me/lists/{0}/items'.format(list_id))
    trakt_movies = []
    for movie in req:
        imdb = movie["movie"]["ids"]["imdb"]
        trakt_movies.append(imdb)
    return trakt_movies

def main():

    list_id = trakt.get_list_id("My Worst Movies")
    list_api_url = 'users/me/lists/{0}/items'.format(list_id)
    bad_ids = []

    radarr_collection = get_radarr_collection()
    i = 0

    for imdb in radarr_collection:
      movieinfo.movie_get_info(imdb) 
      if not movieinfo.local_ratings[imdb].get('imdbRating'):
        continue
      # Set 0 if not exists
      if movieinfo.local_ratings[imdb].get('metaRating'):
        metaRating = movieinfo.local_ratings[imdb]['metaRating']
      else:
        metaRating = 0
      if movieinfo.local_ratings[imdb].get('rottRating'):
        rottRating = movieinfo.local_ratings[imdb]['rottRating']
      else:
        rottRating = 0
      if (movieinfo.local_ratings[imdb]['imdbRating'] < 6 and metaRating < 50 and rottRating < 50):
          print("==================  bad movie found... {}  =================".format(imdb))
          bad_ids.append(imdb)

    print("continuing...")
    # delete movies from trakt list no longer in bad list
    trakt_list = get_trakt_ids(list_id)
    post_data = []
    
    for imdb in trakt_list:
      if imdb in bad_ids:
        continue
      #print('Will delete {0}...'.format(imdb))
      post_data.append({'ids': {'imdb': '{0}'.format(imdb)}})
    list_api_url_rm = 'users/me/lists/{0}/items/remove'.format(list_id)
    pprint(trakt.post_oauth_request(list_api_url_rm, data={'movies': post_data}).json())

    # add missing list to trakt from pirated list
    post_data = []

    for imdb in bad_ids:
        if imdb in trakt_list:
            continue
        print('Will add {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}})

    if not post_data:
        print('Nothing to add...')

    print('Result:')
    pprint(trakt.post_oauth_request(list_api_url, data={'movies': post_data}).json())

    movieinfo.save_local_db()

if __name__ == '__main__':
    main()
