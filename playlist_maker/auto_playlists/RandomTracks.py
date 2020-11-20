import logging
import os
import random
import string

from google.cloud import bigquery
from playlist_maker.auto_playlists import AutoPlaylist

ENVIRONMENT = os.environ.get("PYTHON_ENV")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RandomTracks(AutoPlaylist):
    def random_string(self, str_size=12):
        chars = string.ascii_letters + string.punctuation
        return "".join(random.choice(chars) for x in range(str_size))

    def get_tracks(self):
        """Get random tracks to send to playlist
        Returns:
            list: `tracks` key contains spotify id lists of tracks
        """
        query = """
        SELECT
            id
        FROM
            rapsodie_main.spotify_track
        ORDER BY
            rand()
        LIMIT
            10
        """
        bq_client = bigquery.Client()
        rows = bq_client.query(query).result()
        tracks = [row[0] for row in rows]

        return tracks