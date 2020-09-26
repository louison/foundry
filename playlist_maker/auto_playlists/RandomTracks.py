import logging
import os
import random

from google.cloud import bigquery
from playlist_maker.auto_playlists import AutoPlaylist

ENVIRONMENT = os.environ.get("PYTHON_ENV")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RandomTracks(AutoPlaylist):
    def get_tracks(self):
        """Core playlist logic. Gather tracks you want here

        Returns:
            list -- A list of Spotify tracks song id (strings)
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

    def get_metadata(self, message):
        metadata = {}
        rand = str(random.randint(1, 300))

        name = f"Test #{rand}"
        metadata["playlist_name"] = name

        description = f"test #{rand}"
        metadata["playlist_description"] = description

        return metadata

