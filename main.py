from google.cloud import bigquery
import logging
from spotipy import SpotifyOAuth
import spotipy
import os
from dotenv import load_dotenv

load_dotenv()  # regular get env does not work

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ENVIRONMENT = os.environ.get("PYTHON_ENV")
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI")
SPOTIFY_SCOPES = os.environ.get("SPOTIFY_SCOPES")


def random_playlist():
    QUERY = """
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
            "./rapsodie-21e551b04683.json"
        )
    else:
        bq_client = bigquery.Client()
    rows = bq_client.query(QUERY).result()
    tracks = [row[0] for row in rows]
    return tracks


def push_to_playlist(tracks):
    """
    tracks: list of spotify track ids
    """
    creds = SpotifyOAuth(
        scope="playlist-read-collaborative playlist-modify-public playlist-read-private playlist-modify-private",
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        cache_path=".spotify_cache",
    )
    sp = spotipy.Spotify(client_credentials_manager=creds)
    # username = "rogf0dbg03x23xcod0ya7zapf" # Rapsodie
    username = "heus92"  # Rashad
    new_playlist = sp.user_playlist_create(username, "weshalor", description="c bo")
    new_id = new_playlist.get("id")
    sp.user_playlist_add_tracks(username, new_id, tracks=tracks)


def cloud_playlist(event, context):
    tracks = random_playlist()
    push_to_playlist(tracks)


if __name__ == "__main__":
    tracks = random_playlist()
    push_to_playlist(tracks)
