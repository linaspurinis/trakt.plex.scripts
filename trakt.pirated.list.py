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

FEED_URL = 'http://torrentfreak.com/category/dvdrip/feed/'

def get_pirated_ids():
    rss = requests.get(FEED_URL).text
    #we split the first top10 from the rest rss feed
    rss = rss.split('</table>',1)[0]
    pirated_movies = []
    for imdbid in re.findall('tt(\d{7,8})', rss)[::-1]:
        if 'tt'+imdbid not in pirated_movies:
            #yield imdbid
            pirated_movies.append('tt'+imdbid)
            #print(imdbid)
    pirated_movies.reverse()
    return pirated_movies

def get_trakt_ids(list_id):
    req = trakt.get_oauth_request('users/me/lists/{0}/items'.format(list_id))
    trakt_movies = set()
    for movie in req:
        imdb = movie["movie"]["ids"]["imdb"]
        trakt_movies.add(imdb)
    return trakt_movies

def main():
    list_id = trakt.get_list_id(config.TRAKT_LIST_NAME)
    list_api_url = 'users/me/lists/{0}/items'.format(list_id)

    # update list description
    trakt.put_oauth_request('users/me/lists/{0}'.format(list_id), data={
        'description': 'Updated at ' + datetime.today().strftime('%Y-%m-%d') + 
        '\r\n\r\n' + 'feed:https://torrentfreak.com/category/dvdrip/feed/' +
        '\r\n' + 'Source code: https://github.com/linaspurinis/trakt.lists'
    })
    time.sleep(0.5) 

    print('List URL - https://trakt.tv/users/me/lists/{0}'.format(list_id))
    print('')
    
    # delete movies from trakt list no longer in pirated list   
    trakt_list = get_trakt_ids(list_id)
    pirated_list = get_pirated_ids()
    post_data = []

    for imdb in trakt_list:
        #print('Will delete {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}}) 
    list_api_url_rm = 'users/me/lists/{0}/items/remove'.format(list_id)
    pprint(trakt.post_oauth_request(list_api_url_rm, data={'movies': post_data}).json())

    # add missing list to trakt from pirated list   
    post_data = []

    for imdb in pirated_list:
        print('Will add {0}...'.format(imdb))
        post_data.append({'ids': {'imdb': '{0}'.format(imdb)}})
    pprint(trakt.post_oauth_request(list_api_url, data={'movies': post_data}).json())


if __name__ == '__main__':
    main()
