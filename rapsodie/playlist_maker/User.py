import logging
import os
from typing import Optional

import spotipy
from spotipy import Spotify

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class User(dict):
    def __init__(self, username, client: Spotify = None):
        self.username = username
        self.client = client
        self.playlists = None

    def connect(self):
        if not self.client:
            spotify_client_id = os.environ.get("SPOTIFY_CLIENT_ID")
            spotify_client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
            spotify_redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI")
            spotify_scopes = os.environ.get("SPOTIFY_SCOPES")

            creds = spotipy.SpotifyOAuth(
                scope=spotify_scopes,
                client_id=spotify_client_id,
                client_secret=spotify_client_secret,
                redirect_uri=spotify_redirect_uri,
                cache_path=".spotify_cache",
            )
            self.client = spotipy.Spotify(client_credentials_manager=creds)
        else:
            logger.warning(
                f"user: {self.username} already connected with another client")

    def fetch(self):
        user = self.client.user(self.username)
        self.update(user)

    def get_playlist_count(self):
        playlists = self.client.user_playlists(self.username, offset=50)
        return playlists.get('total', None)

    def get_playlists(self):
        playlists = []
        offset = 0
        response = self.client.user_playlists(self.username, offset=offset)
        if response['items']:
            playlists.extend(response['items'])
        while response['items']:
            offset += 50
            response = self.client.user_playlists(self.username, offset=offset)
            playlists.extend(response['items'])
        return playlists

    def get_playlist_tracks(self,playlist_id):
        tracks = []
        offset = 0
        response = self.client.playlist_tracks(playlist_id,offset=0)
        if response['items']:
            tracks.extend(response['items'])
        while response['items']:
            offset += 50
            response = self.client.playlist_tracks(playlist_id, offset=offset)
            tracks.extend(response['items'])
        return tracks

