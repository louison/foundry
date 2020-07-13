import logging
import os

from dotenv import load_dotenv
from google.cloud import bigquery

from rapsodie.playlist_maker.auto_playlists import AutoPlaylist

load_dotenv()

ENVIRONMENT = os.environ.get("PYTHON_ENV")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Diggers(AutoPlaylist):
    def get_tracks(self, max_timeframe=30, max_followers=5000):
        """Get small artists latest tracks

        Args:
            max_timeframe (int, optional): [Oldest track]. Defaults to 30.
            max_followers (int, optional): Defaults to 5000.
        """

        query = f"""
        SELECT
            strack.name track,
            strack.id track_id,
            strack.album_release_date,
            strack.popularity,
            sartist.name artist,
            sartist.id artist_id,
            sartist.followers_total
        FROM
            rapsodie_main.spotify_track_artist_map AS sp_track_artist_map
        INNER JOIN
            rapsodie_main.spotify_artist AS sartist
        ON
            sartist.id = sp_track_artist_map.artist_id
        INNER JOIN
            rapsodie_main.spotify_track AS strack
        ON
            strack.id = sp_track_artist_map.track_id
        WHERE
            sartist.id IS NOT NULL
            AND sartist.followers_total < {max_followers}
            AND DATE_DIFF(CURRENT_DATE('Europe/Paris'), strack.album_release_date, DAY) <= {max_timeframe}
        ORDER BY
            popularity DESC,
            album_release_date DESC,
            followers_total DESC
        """

        logger.info("Fetching data in database...")
        if ENVIRONMENT == "local":
            bq_client = bigquery.Client().from_service_account_json(
                "./sandbox_credentials.json"
            )
        else:
            bq_client = bigquery.Client()
        data = bq_client.query(query).result().to_dataframe()
        logger.info("Processing data")
        data.drop_duplicates(subset="artist_id", keep="first", inplace=True)
        data = data[:50]
        logger.info("Done!")
        return data["track_id"].to_list()
