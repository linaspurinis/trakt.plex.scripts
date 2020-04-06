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

def get_filtered_ids():
    list_api_url_1 = 'movies/watched/weekly?limit=100'
    req = trakt.get_oauth_request(list_api_url_1)
    # ignored config params config.VOTES config.YEAR config.RATING
    trakt_movies = []
    for trakt_movie in req:
        #get movie ratings
        imdb = trakt_movie["movie"]["ids"]["imdb"]
        if not imdb:
            # Sometimes Trakt does not have imdbid for some movies
            continue
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
        if (movieinfo.local_ratings[imdb]['year'] > (datetime.today().year - 2) and movieinfo.local_ratings[imdb]['imdbRating'] >= 6 and movieinfo.local_ratings[imdb]['imdbVotes'] >= 5000 and metaRating >= 50 and rottRating >= 50):
           trakt_movies.append(imdb)
        else:
            print('Not good... Ignoring: '+imdb)
    return trakt_movies

def main():
    list_id = trakt.get_list_id(config.TRAKT_LIST_NAME_WATCHED)
    list_api_url = 'users/me/lists/{0}/items'.format(list_id)
        
    # update list description
    trakt.put_oauth_request('users/me/lists/{0}'.format(list_id), data={
        'description': 'Updated at ' + datetime.today().strftime('%Y-%m-%d') + 
        '\r\nTrakts The most watched movies for the last 7 days with filters:'+
        '\r\nReleased in last 2 years, imdbRating >= 6, imdbVotes >= 5000, Metacritics >= 50, Rotten >= 50' +
        '\r\nSource code: https://github.com/linaspurinis/trakt.lists'
    })
    time.sleep(0.5) 

    print('List URL - https://trakt.tv/users/me/lists/{0}'.format(list_id))
    print('')
    
    # delete movies from trakt list no longer in top watched list   
    post_data = []
    trakt_topwatched_list = get_filtered_ids()
    trakt_filtered_list = get_trakt_ids(list_id)

    for imdb in trakt_filtered_list:
        #print('Will delete {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}}) 
    list_api_url_rm = 'users/me/lists/{0}/items/remove'.format(list_id)
    pprint(trakt.post_oauth_request(list_api_url_rm, data={'movies': post_data}).json())

    # add missing list to trakt from top watched list    
    post_data = []
    for imdb in trakt_topwatched_list:    
        print('Will add {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}})
    pprint(trakt.post_oauth_request(list_api_url, data={'movies': post_data}).json())

    movieinfo.save_local_db()

if __name__ == '__main__':
    main()
