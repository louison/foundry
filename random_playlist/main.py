import logging
import os

from dotenv import load_dotenv
from google.cloud import bigquery

from utils import spotify

load_dotenv()  # regular get env does not work

ENVIRONMENT = os.environ.get("PYTHON_ENV")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_tracks():
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
    if ENVIRONMENT == "local":
        bq_client = bigquery.Client().from_service_account_json(
            "../utils/rapsodie-21e551b04683.json"
        )
    else:
        bq_client = bigquery.Client()
    rows = bq_client.query(query).result()
    tracks = [row[0] for row in rows]
    return tracks


def update_playlist(event, context):
    """Updates the playlist of this file

    Arguments:
        event {dict} -- Some random stuff Google Cloud neeeds
        context {dict} -- Some other random stuff Google Cloud needs
    """
    tracks = get_tracks()
    spotify.push_to_playlist(tracks, "6hlAehDHbcmZXXYCz6sl72")


if __name__ == "__main__":
    update_playlist("event", "context")
