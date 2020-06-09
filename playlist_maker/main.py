import base64
import json
import logging
import os
import spotipy
import os

from playlist_maker.User import User

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

spotify_client_id = os.environ.get("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
spotify_redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI")
spotify_scopes = os.environ.get("SPOTIFY_SCOPES")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def entrypoint(event, context, message=None):
    if not message:
        if not 'data' in event:
            return
        message = base64.b64decode(event["data"]).decode("utf-8")
    if message['entrypoint'] == "generic":
        generic(message)


def generic(message=None):
    if not 'playlist_name' in message and not 'playlist_id' in message:
        raise ValueError("You must provide a name or an id for the playlist")

    credentials = message['credentials']
    credentials_filepath = f"{message['username']}_credentials.json"
    with open(credentials_filepath, "w") as file:
        file.write(json.dumps(credentials))
    creds = spotipy.SpotifyOAuth(
        scope=spotify_scopes,
        client_id=spotify_client_id,
        client_secret=spotify_client_secret,
        redirect_uri=spotify_redirect_uri,
        cache_path=".spotify_cache",
    )
    spotipy.Spotify()
    client = spotipy.Spotify(client_credentials_manager=creds)
    user = User(message['username'], client=client)
    user.connect()
    user.fetch()
    playlist_name = message['playlist_name']
    if playlist_name:
        playlists = user.get_playlists()
        names = list(map(lambda x: x['name'], playlists))
        if playlist_name in names:
            if message['override']:
                playlist_object = list(filter(
                    lambda x: x['name'] == playlist_name, playlists
                ))[0]
            else:
                raise ValueError(
                    f"Playlist with name: {playlist_name}"
                    f" already exist for user {message['username']} use -o to override")
        else:
            playlist_object = client.user_playlist_create(
                user.username,
                playlist_name
            )
    else:
        playlist_object = client.playlist(message['playlist_id'])
    client.user_playlist_replace_tracks(
        user.username,
        playlist_object['id'],
        tracks=message['tracks']
    )
    os.remove(credentials_filepath)


def init():
    message = {
        "entrypoint": "generic",
        "username": "loulouxd",
        "playlist_name": "Random",
        "playlist_id": "",
        "description": "blabla",
        "public": True,
        "playlist_cover": "",
        "override": True,
        "tracks": ["0fAHY4PWSEbov0OHjj2Gek"],
    }
    with open('.spotify_cache', 'r') as file:
        creds = json.load(file)
    message['credentials'] = creds
    entrypoint(None, None, message=message)


if __name__ == '__main__':
    init()
