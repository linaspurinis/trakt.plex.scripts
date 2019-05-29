## trakt.lists

trakt.pirated.list.py - Creates Trakt list from Torrentfreak Most pirated movies of the week feed: http://torrentfreak.com/category/dvdrip/feed/

trakt.top.watched.list.py - Creates Trakt list from Trakts Top Watched Movies of The Week with additional filer by votes, rating and year (in config.py)

### How to run it:

1. Open config.py.example and follow the instructions there
2. Rename config.py.example to config.py
3. Install requirements

	pip install -r requirements.txt

4. Run the main script:

	python trakt.pirated.list.py
  or
  python trakt.top.watched.list.py
