## trakt.lists

trakt.pirated.list.py - Creates Trakt list from Torrentfreak Most pirated movies of the week feed: http://torrentfreak.com/category/dvdrip/feed/

trakt.top.watched.list.py - Creates Trakt list from Trakts Top Watched Movies of The Week with additional filer by votes, rating and year (in config.py)

radarr.delete.trakt.rating.py - Would delete movies from Radarr when you rate them low on trakt

### How to run it:

1. Open config.py.example and follow the instructions there
2. Rename config.py.example to config.py
3. Install requirements

	pip install -r requirements.txt

4. Run the main script:

	python trakt.pirated.list.py
  or
  python trakt.top.watched.list.py

### Code
Code used in these scripts are based on https://gitlab.com/tanel/trakt-torrentfreak-top-10/

# missing_trailers.sh
Downloads missing trailers - it goes through all your movies and matchs them up with an entry
in plex, grabs the imdb id from plex, and then parses the trailer url from youtube search, then passes
that to youtube-dl to download the trailer, it skips entries if the trailer already exists
must have 'sqlite', 'youtube-dl' and 'bash' packages installed.
set 'mpath' and 'pms' accordingly in missing_trailers.cfg
