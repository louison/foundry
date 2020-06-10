import base64
import json
import logging
import spotipy
import os

from auto_playlists import Diggers, RandomTracks
from playlist_maker.User import User

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

spotify_client_id = os.environ.get("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
spotify_redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI")
spotify_scopes = os.environ.get("SPOTIFY_SCOPES")

PUSH_METHODS = ["append", "replace", "keep"]

def entrypoint(event, context, message=None):
    if not message:
        if not 'data' in event:
            return
        message = base64.b64decode(event["data"]).decode("utf-8")
    if message['entrypoint'] == "generic":
        generic(message)
    elif message['entrypoint'] == "random":
        random_tracks = RandomTracks()
        tracks = random_tracks.get_tracks()
        message['tracks'] = tracks
        generic(message)
    elif message['entrypoint'] == "diggers":
        diggers = Diggers()
        tracks = diggers.get_tracks()
        message['tracks'] = tracks
        generic(message)
    else:
        raise ValueError(f"{message.get('entrypoint')} is not supported")


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
            push_method = message.get('push_method')
            if push_method not in PUSH_METHODS:
                raise ValueError(f"push method: {push_method} not supported")
            if message.get('override', False):
                playlist_object = list(filter(
                    lambda x: x['name'] == playlist_name, playlists
                ))[0]
                if push_method == "append":
                    tracks = user.get_playlist_tracks(playlist_object['id'])
                    tracks_ids = list(map(lambda x: x['track']['id'], tracks))
                    message['tracks'].extend(tracks_ids)
                elif push_method == "keep":
                    tracks = user.get_playlist_tracks(playlist_object['id'])
                    tracks_ids = list(map(lambda x: x['track']['id'], tracks))
                    message['tracks'] = tracks_ids
            else:
                raise ValueError(
                    f"Playlist with name: {playlist_name}"
                    f" already exist for user {message['username']} use -o to override")
        else:
            playlist_object = client.user_playlist_create(
                user.username,
                playlist_name,
                public=message.get('public', False),
                description=message.get('description', "")
            )
    else:
        playlist_object = client.playlist(message['playlist_id'])
    client.user_playlist_replace_tracks(
        user.username,
        playlist_object['id'],
        tracks=message['tracks']
    )
    client.user_playlist_change_details(
        message['username'],
        playlist_object['id'],
        description=message.get('description', ""),
        public=message.get('public', False)
    )
    os.remove(credentials_filepath)


def init():
    message = {
        "entrypoint": "random",
        "username": "heus92",
        "playlist_name": "weshalors",
        "playlist_id": "",
        "description": "My super random playlist v9.2",
        "public": False,
        "playlist_cover": "",
        "override": True,
        "push_method": "replace",  # replace or append or keep
        "append": True,
        "tracks": ["0fAHY4PWSEbov0OHjj2Gek"],
    }
    with open('.spotify_cache', 'r') as file:
        creds = json.load(file)
    message['credentials'] = creds
    entrypoint(None, None, message=message)


if __name__ == '__main__':
    init()
