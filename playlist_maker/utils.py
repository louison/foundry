import os
import json
import spotipy

from playlist_maker.types import Message


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_credentials(message: Message = None) -> spotipy.SpotifyOAuth:
    spotify_client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    spotify_client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    spotify_redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI")
    spotify_scopes = os.environ.get("SPOTIFY_SCOPES")
    if message:
        raw_credentials = message["credentials"]
        credentials_path = f"/tmp/{message['username']}_credentials.json"
        with open(credentials_path, "w") as f:
            f.write(json.dumps(raw_credentials))
    else:
        credentials_path = ".spotify_cache"
    creds = spotipy.SpotifyOAuth(
        scope=spotify_scopes,
        client_id=spotify_client_id,
        client_secret=spotify_client_secret,
        redirect_uri=spotify_redirect_uri,
        cache_path=credentials_path,
    )
    return creds
