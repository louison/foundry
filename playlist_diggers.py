import logging
import os

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

import utils.spotify as spotify

load_dotenv()

ENVIRONMENT = os.environ.get("PYTHON_ENV")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_tracks(max_timeframe=30, max_followers=5000):
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
        album_release_date DESC,
        followers_total DESC
    """

    logger.info("Fetching data in database...")
    if ENVIRONMENT == "local":
        bq_client = bigquery.Client().from_service_account_json(
            "./utils/rapsodie-21e551b04683.json"
        )
    else:
        bq_client = bigquery.Client()
    data = bq_client.query(query).result().to_dataframe()
    logger.info("Processing data")
    data.drop_duplicates(subset="artist_id", keep="first", inplace=True)
    logger.info("Done!")
    return data["track_id"].to_list()


if __name__ == "__main__":
    tracks = get_tracks()
    spotify.push_to_playlist(tracks, "2g2nZEjXnMW4jCDZcdw42M")
