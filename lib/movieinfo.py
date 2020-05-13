import os
import json
import requests
import time
import random
from bs4 import BeautifulSoup
from lib import trakt
from difflib import SequenceMatcher

OMDB_APIKEY = 'NoNe'
TRAKT_RATINGS = 'NoNe'

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
  if not imdbid:
      print('imdb is not set!')
      return
  omdb_url = "http://www.omdbapi.com/?i={}&apikey={}&tomatoes=true".format(imdbid, OMDB_APIKEY)
  request = requests.get(omdb_url)
  data = request.json()
  if data['Response'] == 'False':
      print('OMDB returned error...')
      return
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
    # Trying Rottentomatoes ratings directly from site
    ROTTEN_URL = data['tomatoURL']
    if ROTTEN_URL == 'N/A':
      # Searching for Rotten URL
      print('No Rotten URL')
      RURL = ''
      MovieTitle = data['Title']
      response = requests.get('https://www.rottentomatoes.com/api/private/v2.0/search?q='+MovieTitle+'&limit=10')
      rottenmovies = response.json()
      Confidence = 0
      for rottenmovie in rottenmovies['movies']:
        tConfidence = SequenceMatcher(None, MovieTitle, rottenmovie['name'].split("(")[0]).ratio()
        if isinstance(rottenmovie['year'], int):
          if tConfidence > Confidence and (int(data['Year']) == int(rottenmovie['year']) or int(data['Year']) == int(rottenmovie['year']) + 1 or int(data['Year']) == int(rottenmovie['year']) -1):
            Confidence = tConfidence
            RURL = rottenmovie['url']
      print('Best match {} with confidence: {}'.format(RURL, Confidence))
      if Confidence > 0.9:
        ROTTEN_URL = 'https://www.rottentomatoes.com'+RURL
    print('Rotten URL:'+ROTTEN_URL)
    response = requests.get(ROTTEN_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    #tomatometer
    result = soup.find('div', {'class': 'mop-ratings-wrap__half'})
    rating = result.find('span', {'class': 'mop-ratings-wrap__percentage'}).get_text()
    local_ratings[imdbid]['rottRating'] = int(rating.strip().replace("%",""))
    #tomatoaudience
    result = soup.find('div', {'class': 'mop-ratings-wrap__half audience-score'})
    rating = result.find('span', {'class': 'mop-ratings-wrap__percentage'}).get_text()
    local_ratings[imdbid]['rottAudience'] = int(rating.strip().replace("%",""))
  except:
    pass

  try:
    local_ratings[imdbid]['metaRating'] = int(data['Metascore'])
  except ValueError:
    pass

  try:
    local_ratings[imdbid]['Bollywood'] = 0
    if data['Language'] == 'Hindi' and data['Country'] == 'India':
      local_ratings[imdbid]['Bollywood'] = 1
  except ValueError:
    pass

  #TRAKT_RATINGS
  if TRAKT_RATINGS == 'True':
    try:
      list_api_url = 'movies/{0}/ratings'.format(imdbid)
      req = trakt.get_oauth_request(list_api_url)   
      local_ratings[imdbid]['traktRating'] = int(req["rating"]*10)
      local_ratings[imdbid]['traktVotes'] = int(req["votes"])
    except:
      pass

  return
 
def movie_get_info(imdbid):
    if not local_ratings.get(imdbid):
        print('Not found, getting movie info for: {}'.format(imdbid))
        omdbapi_get_info(imdbid)
    else:
        if ((int(round(time.time() * 1000)) - local_ratings[imdbid]['updated']) / 1000) > (86400 * (5+random.randint(0,5))):
            print('Refreshing movie info for: '+imdbid)
            omdbapi_get_info(imdbid)

def save_local_db():
    print("Saving local db....")
    with open(RATINGSFILE, 'w') as fp:
        json.dump(local_ratings, fp, indent=2, sort_keys=True)
