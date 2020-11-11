import logging
import os

import requests
from google.cloud import bigquery

from playlist_maker.auto_playlists import AutoPlaylist
from playlist_maker.tokenito import get_token

ENVIRONMENT = os.environ.get("PYTHON_ENV")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LatestReleases(AutoPlaylist):
    def get_tracks(self):
        query = """
       SELECT a.artist_id, a.latest_release_date , a.latest_release_uri 
        FROM `rapsodie.rapsodie_main.artist_page` a
        INNER JOIN (
            SELECT artist_id, max(latest_release_date) latest_release_date
        FROM `rapsodie.rapsodie_main.artist_page` 
        GROUP BY artist_id
        ) b ON a.artist_id = b.artist_id AND a.latest_release_date = b.latest_release_date
        where cast(a.latest_release_date as DATE) between DATE_SUB(current_date(), INTERVAL 0 DAY) and current_date()
        """
        bq_client = bigquery.Client()
        rows = bq_client.query(query).result()
        s_token = get_token()
        tracks = []
        for row in rows:
            album_id = row[2].replace("spotify:album:", "")
            album_id = album_id.replace('"', "")
            url = f"https://api.spotify.com/v1/albums/{album_id}/tracks?country=FR&limit=50&offset=0"
            response = requests.get(url, headers={"Authorization": f"Bearer {s_token}"})
            response_body = response.json()
            for track in response_body["items"]:
                tracks.append(track["id"])
        return {"tracks": tracks}
