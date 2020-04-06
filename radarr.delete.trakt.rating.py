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

def get_rating_imdb_ids(rating):
    movies = set()
    i = 1
    while i <= rating:
        list_api_url = 'users/me/ratings/movies/{0}'.format(i)
        req = trakt.get_oauth_request(list_api_url)
        for movie in req:
            imdb = movie["movie"]["ids"]["imdb"]
            movies.add(imdb)
        i += 1
    return movies

def main():

    radarr_url = config.RADARR_URL
    radarr_key = config.RADARR_SESSION
    trakt_bad_rating = config.TRAKT_BAD_RATING

    # delete movies from radarr rated 1 in trakt
    trakt_bad_movies = get_rating_imdb_ids(trakt_bad_rating)

    radarrSession = requests.Session()
    radarrSession.trust_env = False
    radarrMovies = radarrSession.get('{0}/api/movie?apikey={1}'.format(radarr_url, radarr_key))

    if radarrMovies.status_code != 200:
      print('Radarr server error - response {}'.format(radarrMovies.status_code))
      sys.exit(0)

    for movie in radarrMovies.json():
        if movie['imdbId'] in trakt_bad_movies:
          print('Will delete {0}...'.format(movie['imdbId']))
          radarrMovies = radarrSession.delete('{0}/api/movie/{2}?apikey={1}&deleteFiles=true&addExclusion=true'.format(radarr_url, radarr_key, movie['id']))



if __name__ == '__main__':
    main()
