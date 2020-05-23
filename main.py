from google.cloud import bigquery
import logging
from spotipy import SpotifyOAuth
import spotipy
import os

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ENVIRONMENT = os.environ.get("PYTHON_ENV") or 'local'

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
    if ENVIRONMENT == 'local':
        bq_client = bigquery.Client().from_service_account_json('./rapsodie-21e551b04683.json')
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
        scope = "playlist-read-collaborative playlist-modify-public playlist-read-private playlist-modify-private",
        client_id="d4f84d8d1f6d4c18860c118954f13e50",
        client_secret="017b19d8270948e6b6f1670c9483e8f6",
        redirect_uri="https://localhost:8888",
        cache_path=".spotify_cache"
    )
    sp = spotipy.Spotify(client_credentials_manager=creds)
    # username = "rogf0dbg03x23xcod0ya7zapf" # Rapsodie
    username = "heus92" # Rashad
    new_playlist = sp.user_playlist_create(username, "weshalor", description="c bo")
    new_id = new_playlist.get('id')
    sp.user_playlist_add_tracks(
        username,
        new_id,
        tracks=tracks
    )

def cloud_playlist(event, context):
    tracks = random_playlist()
    push_to_playlist(tracks)

if __name__ == "__main__":
    tracks = random_playlist()
    push_to_playlist(tracks)