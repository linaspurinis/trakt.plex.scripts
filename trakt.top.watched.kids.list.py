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

def get_trakt_ids(list_id):
    req = trakt.get_oauth_request('users/me/lists/{0}/items'.format(list_id))
    trakt_movies = []
    for movie in req:
        imdb = movie["movie"]["ids"]["imdb"]
        trakt_movies.append(imdb)
    return trakt_movies

def get_imdb_ids():
  filter_year = str(datetime.today().year - 2)
  list_api_url_1 = 'movies/watched/weekly?limit=20&genres=animation,anime,family&certifications=g,pg&years='+filter_year+'-2025'
  print(list_api_url_1)
  req = trakt.get_oauth_request(list_api_url_1)
  movies = []

  for trakt_movie in req:
    imdb = trakt_movie["movie"]["ids"]["imdb"]
    #get movie ratings
    movieinfo.movie_get_info(imdb)
    if not movieinfo.local_ratings[imdb].get('imdbRating'):
      print('No iMDB rating, ignoring:'+imdb)
      continue
    if movieinfo.local_ratings[imdb].get('metaRating'):
      metaRating = movieinfo.local_ratings[imdb]['metaRating']
    else:
      metaRating = 100
    if movieinfo.local_ratings[imdb].get('rottRating'):
      rottRating = movieinfo.local_ratings[imdb]['rottRating']
    else:
      rottRating = 100

    if (movieinfo.local_ratings[imdb]['imdbRating'] >= 6 and movieinfo.local_ratings[imdb]['imdbVotes'] >= 5000 and metaRating >= 45 and rottRating >= 45):
      movies.append(imdb)
    else:
      print('Not good... Ignoring: '+imdb)

  return movies

def main():
    list_id = trakt.get_list_id(config.TRAKT_LIST_NAME_WATCHED_KIDS)
    list_api_url = 'users/me/lists/{0}/items'.format(list_id)
        
    # update list description
    trakt.put_oauth_request('users/me/lists/{0}'.format(list_id), data={
        'description': 'Updated at ' + datetime.today().strftime('%Y-%m-%d') + 
        '\r\n\r\n' + 'Trakts The most watched movies for the last 7 days with additional filters for KiDS.' +
        '\r\n' + 'Source code: https://github.com/linaspurinis/trakt.lists'
    })
    time.sleep(0.5) 

    print('List URL - https://trakt.tv/users/me/lists/{0}'.format(list_id))
    print('')
    
    # delete movies from trakt list no longer in top watched list   
    post_data = []
    movies_in_watched_list = get_imdb_ids()
    trakt_list = get_trakt_ids(list_id)

    for imdb in trakt_list:
        #print('Will delete {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}}) 
    list_api_url_rm = 'users/me/lists/{0}/items/remove'.format(list_id)
    pprint(trakt.post_oauth_request(list_api_url_rm, data={'movies': post_data}).json())

    # add missing list to trakt from top watched list    
    post_data = []
    for imdb in movies_in_watched_list:    
        print('Will add {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}})
    pprint(trakt.post_oauth_request(list_api_url, data={'movies': post_data}).json())

    movieinfo.save_local_db()

if __name__ == '__main__':
    main()
