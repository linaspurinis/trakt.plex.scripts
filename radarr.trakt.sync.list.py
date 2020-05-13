#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function
from collections import OrderedDict
import json
import os
import re
import sys
import time
from pprint import pprint
from datetime import datetime
import requests

from lib import movieinfo
from lib import trakt

try:
    import config
except ImportError:
    print(('Please see config.py.example, update the '
           'values and rename it to config.py'))
    sys.exit(1)

movieinfo.OMDB_APIKEY = config.OMDB_APIKEY
movieinfo.TRAKT_RATINGS = config.TRAKT_RATINGS

def get_trakt_collection(list_id):
    req = trakt.get_oauth_request('users/me/lists/{0}/items'.format(list_id))
    trakt_movies = set()
    for movie in req:
        imdb = movie["movie"]["ids"]["imdb"]
        trakt_movies.add(imdb)
    return trakt_movies

def get_radarr_collection():
    radarr_movies = {}
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
            #radarr_movies.add(movie['imdbId'])
            if movie['imdbId']:
              imdb = movie['imdbId']
              folderName = movie['folderName']
              movieinfo.movie_get_info(imdb)
              tRatings = 0
              if movieinfo.local_ratings[imdb].get('imdbRating'):
                  imdbRating = int(movieinfo.local_ratings[imdb]['imdbRating'] * 10) # 6.5 -> 65
                  tRatings += 1
              else:
                  imdbRating = 0
              if movieinfo.local_ratings[imdb].get('metaRating'):
                  metaRating = movieinfo.local_ratings[imdb]['metaRating']
                  tRatings += 1
              else:
                  metaRating = 0
              if movieinfo.local_ratings[imdb].get('rottRating'):
                  rottRating = movieinfo.local_ratings[imdb]['rottRating']
                  tRatings += 1
              else:
                  rottRating = 0
              if movieinfo.local_ratings[imdb].get('rottAudience'):
                  rottAudience = movieinfo.local_ratings[imdb]['rottAudience']
                  tRatings += 1
              else:
                  rottAudience = 0
              if movieinfo.local_ratings[imdb].get('traktRating'):
                  traktRating = movieinfo.local_ratings[imdb]['traktRating']
                  tRatings += 1
              else:
                  traktRating = 0
              if tRatings == 2:
                  # Only 2 ratings out of 5, will increase 4 instead of 5 time
                  movieRating = int((imdbRating + metaRating + rottRating + traktRating + rottAudience) / 2 * 4)
              elif tRatings == 3: 
                  movieRating = int((imdbRating + metaRating + rottRating + traktRating + rottAudience) / 3 * 5)
              elif tRatings == 4:
                  movieRating = int((imdbRating + metaRating + rottRating + traktRating + rottAudience) / 4 * 5)
              else:
                  movieRating = imdbRating + metaRating + rottRating + traktRating + rottAudience
              
              radarr_movies[imdb] = movieRating
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

    radarr_collection_ord = OrderedDict(sorted(radarr_collection.items(), key=lambda x: x[1], reverse=True))

    for imdb in trakt_collection:
        post_data_remove.append({'ids': {'imdb': '{0}'.format(imdb)}})
    pprint(trakt.post_oauth_request('users/me/lists/{0}/items/remove'.format(list_id), data={'movies': post_data_remove}).json())

    for imdb in radarr_collection_ord:
        post_data_add.append({'ids': {'imdb': '{0}'.format(imdb)}})    
    pprint(trakt.post_oauth_request('users/me/lists/{0}/items'.format(list_id), data={'movies': post_data_add}).json())

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

    movieinfo.save_local_db()

if __name__ == '__main__':
    main()
