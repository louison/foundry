import logging
import os

import spotipy
from dotenv import load_dotenv
from spotipy import SpotifyOAuth

load_dotenv()  # regular get env does not work

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI")
SPOTIFY_SCOPES = os.environ.get("SPOTIFY_SCOPES")
SPOTIFY_USER = os.environ.get("SPOTIFY_USER")

def push_to_playlist(tracks, playlist_id):
    """Update tracks for a givent Spotify playlist

    Arguments:
        tracks {list} -- list of Spotify track ids
        playlist_id {string} -- the Spotify playlist id
    """

    creds = SpotifyOAuth(
        scope=SPOTIFY_SCOPES,
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        cache_path="./utils/.spotify_cache",
    )
    sp = spotipy.Spotify(client_credentials_manager=creds)
    sp.current_user_playlists()
    sp.user_playlist_replace_tracks(SPOTIFY_USER, playlist_id, tracks=tracks)
