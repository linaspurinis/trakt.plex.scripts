#!/bin/bash
# downloads all missing trailers - it goes through all your movies and matchs them up with an entry
# in plex, grabs the imdb id from plex, and then parses the trailer url from the imdb site, then passes
# that to youtube-dl to download the trailer, it skips entries that dont have a matching imdb entry
# or if the trailer already exists
# must have 'sqlite3' and 'youtube-dl' packages (apt-get install sqlite3 youtube-dl)
# set 'mpath' and 'pms' accordingly

# Read config variables
. $(dirname $(readlink -f $0))/missing_trailers.cfg

function guid_from_filename() {
  sql="${1//\'/\'\'}"
  sqlite3 "${pms}Plug-in Support/Databases/com.plexapp.plugins.library.db" \
   "select title, year, guid from media_parts, media_items, metadata_items where media_parts.media_item_id=media_items.id and
   media_items.metadata_item_id=metadata_items.id and media_parts.file='$sql';";
}

function dirhash_from_guid() {
 echo -n "$1" | sha1sum | cut -d" " -f1 | sed -e 's/^\(.\{1\}\)/\1\//' -e 's/ .*//';
}

function imdb_xml_from_guid() {
 # Download only if no Extras file present (or extras = 1)
 if [ ! -f "${pms}Metadata/Movies/$(dirhash_from_guid "$1").bundle/Contents/com.plexapp.agents.imdb/extras.xml" ] || [ ${extras} -eq 1 ]; then
   cat "${pms}Metadata/Movies/$(dirhash_from_guid "$1").bundle/Contents/com.plexapp.agents.imdb/Info.xml";
 fi
}

function imdb_from_guid() {
  imdb_xml_from_guid "$1" | grep 'Movie id' | awk -F 'Movie id' '{print $2}' | cut -d\" -f2 |grep -v "^$";
}

function videos_from_yt_search() {
 curl -s -G "https://www.googleapis.com/youtube/v3/search" --data-urlencode "part=snippet" --data-urlencode "q=${1}+movie+trailer" --data-urlencode "key=${ytapi}" | \
 grep videoId | cut -d\" -f4;
}

IFS="
";
echo -n "Building Movies List..."; files="$(find "${mpath}" -type f  |grep -vi -e "\-trailer\.*" -e "@eaDir" \
-e "\.ass$" -e "\.srt$" -e "\.idx$" -e "\.sub$" -e "\.ssa$" -e "\.alt$" -e "\.smi$" -e "\.txt$" -e "\.rar$" \
-e "\.nfo$" -e "\.jpg$" -e "\.png$" -e "\.jpeg$")"; echo done;
for filename in $files; do
  #echo "Working on $filename";
  cd "$(dirname "${filename}")";
  #pwd
  justfile="$(basename "${filename}")";
  mname="$(echo "${PWD}" | sed s#"^.*/"#""#g)";
  #echo "Just File: $justfile";
  #echo "Movie Name: $mname";
  if [ ! -e "$(dirname "${filename}")/${mname}-trailer."* ]; then
    IFS='|' read -r -a sqlarray <<< "$(guid_from_filename "${filename}")";
    #echo "Got GUID ${guid}"
    mfulltitle="${sqlarray[0]} (${sqlarray[1]})"
    guid="${sqlarray[2]}"
    #echo "Title ${mfulltitle}"
    [ -z "${guid}" ] && continue
    imdbi="$(imdb_from_guid "${guid}")";
    #echo "Got IMDB ID ${imdbi}"
    [ -z "${imdbi}" ] && continue
    echo "No extras.xml found, will download the trailer for ${mfulltitle}..."
    imdbv="$(videos_from_yt_search "${mfulltitle}")";
    #echo "$imdbv"
    IFS=$'\n' imdbvs=($imdbv)
    for (( i=0; i<${#imdbvs[@]}; i++ ))
    do
        youtubeurl="https://www.youtube.com/watch?v=${imdbvs[$i]}"
        echo "Got Youtube URL ${youtubeurl}"
        echo "youtube-dl -o \"${mname}-trailer.%(ext)s\" \"${youtubeurl}\"";
        youtube-dl -o "${mname}-trailer.%(ext)s" "${youtubeurl}";
        if [ $? -eq 0 ]; then
          echo "youtube-dl success"
          break
        fi
    done

  fi;
done;

