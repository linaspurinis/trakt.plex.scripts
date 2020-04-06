import os
import json
import requests
import time
import random
from bs4 import BeautifulSoup

OMDB_APIKEY = 'NoNe'

HERE = os.path.abspath(os.path.dirname(__file__))
RATINGSFILE = os.path.join(HERE, '../.ratings.db')
local_ratings = {}
if os.path.exists(RATINGSFILE):
  with open(RATINGSFILE, 'r') as fp:
    local_ratings = json.load(fp)

def omdbapi_get_info(imdbid):
  if OMDB_APIKEY == 'NoNe':
      print('OMDB API KEY is not set!')
      return
  omdb_url = "http://www.omdbapi.com/?i={}&apikey={}".format(imdbid, OMDB_APIKEY)
  request = requests.get(omdb_url)
  data = request.json()
  local_ratings[imdbid] = {'year': int(data['Year']), 
                           'updated': int(round(time.time() * 1000))
                           }
  ratings = data['Ratings']
  for rating in ratings:
    if rating['Source'] == 'Rotten Tomatoes':
      local_ratings[imdbid]['rottRating'] = int(rating['Value'].replace("%",""))
  try:
    local_ratings[imdbid]['imdbRating'] = float(data['imdbRating'])
    local_ratings[imdbid]['imdbVotes'] = int(data['imdbVotes'].replace(",",""))
  except ValueError:
    pass
  try:
    # Trying directly from IMDB
    IMDB_URL = 'https://www.imdb.com/title/'+imdbid+'/'
    response = requests.get(IMDB_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    local_ratings[imdbid]['imdbRating'] = float(soup.find(itemprop="ratingValue").get_text())
    local_ratings[imdbid]['imdbVotes'] = int(soup.find(itemprop="ratingCount").get_text().replace(",",""))
  except:
    pass
  try:
    local_ratings[imdbid]['metaRating'] = int(data['Metascore'])
  except ValueError:
    pass
  return

def movie_get_info(imdbid):
    if not local_ratings.get(imdbid):
        print('Not found, getting movie info for: {}'.format(imdbid))
        omdbapi_get_info(imdbid)
    else:
        if ((int(round(time.time() * 1000)) - local_ratings[imdbid]['updated']) / 1000) > (86400 * (5+random.randint(0,10))):
            print('Refreshing movie info for: '+imdbid)
            omdbapi_get_info(imdbid)

def save_local_db():
    print("Saving local db....")
    with open(RATINGSFILE, 'w') as fp:
        json.dump(local_ratings, fp, indent=2, sort_keys=True)
