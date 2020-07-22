import base64
import logging
import os
import json

import spotipy

from rapsodie.playlist_maker.User import User
from rapsodie.playlist_maker.auto_playlists import Diggers, RandomTracks
from rapsodie.playlist_maker.auto_playlists import AllArtists
from rapsodie.playlist_maker.auto_playlists import BillionStreams
from rapsodie.playlist_maker.utils import chunks

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

spotify_client_id = os.environ.get("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
spotify_redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI")
spotify_scopes = os.environ.get("SPOTIFY_SCOPES")

PUSH_METHODS = ["append", "replace", "keep"]

AUTO_PLAYLIST = {
    "generic": None,
    "random": RandomTracks,
    "diggers": Diggers,
    "allartists": AllArtists,
    "billionstreams": BillionStreams
}


def start(event, context):
    if 'data' in event:
        message = base64.b64decode(event['data']).decode('utf-8')
        message = json.loads(message)
    else:
        message = event

    entrypoint_choice = message["entrypoint"]
    if entrypoint_choice in AUTO_PLAYLIST.keys():
        logger.debug(f"playlist {entrypoint_choice}")
        auto_playlist_class = AUTO_PLAYLIST.get(entrypoint_choice, None)
        if auto_playlist_class:
            auto_playlist = auto_playlist_class()
            args = message.get("entrypoint_args", {})
            tracks = auto_playlist.get_tracks(**args)
            message["tracks"] = tracks
        return generic(message)
    else:
        raise ValueError(f"{message.get('entrypoint')} is not supported")


def generic(message=None):
    if not "playlist_name" in message and not "playlist_id" in message:
        raise ValueError("You must provide a name or an id for the playlist")

    credentials = message["credentials"]
    credentials_path = f"/tmp/{message['username']}_credentials.json"
    with open(credentials_path, "w") as f:
        f.write(json.dumps(credentials))

    creds = spotipy.SpotifyOAuth(
        scope=spotify_scopes,
        client_id=spotify_client_id,
        client_secret=spotify_client_secret,
        redirect_uri=spotify_redirect_uri,
        # cache_path=".spotify_cache",
        cache_path=credentials_path,
    )
    client = spotipy.Spotify(client_credentials_manager=creds)
    user = User(message["username"], client=client)
    user.connect()
    user.fetch()
    playlist_name = message["playlist_name"]
    if playlist_name:
        playlists = user.get_playlists()
        names = list(map(lambda x: x["name"], playlists))
        if playlist_name in names:
            push_method = message.get("push_method")
            if push_method not in PUSH_METHODS:
                raise ValueError(f"push method: {push_method} not supported")
            if message.get("override", False):
                playlist_object = list(
                    filter(lambda x: x["name"] == playlist_name, playlists)
                )[0]
                if push_method == "append":
                    tracks = user.get_playlist_tracks(playlist_object["id"])
                    tracks_ids = list(map(lambda x: x["track"]["id"], tracks))
                    message["tracks"].extend(tracks_ids)
                elif push_method == "keep":
                    tracks = user.get_playlist_tracks(playlist_object["id"])
                    tracks_ids = list(map(lambda x: x["track"]["id"], tracks))
                    message["tracks"] = tracks_ids
            else:
                raise ValueError(
                    f"Playlist with name: {playlist_name}"
                    f" already exist for user {message['username']} use -o to override"
                )
        else:
            playlist_object = client.user_playlist_create(
                user.username,
                playlist_name,
                public=message.get("public", False),
                description=message.get("description", ""),
            )
    else:
        playlist_object = client.playlist(message["playlist_id"])

    track_chunks = chunks(message['tracks'], 100)
    # First empty the playlist
    client.user_playlist_replace_tracks(
        user.username,
        playlist_object["id"],
        tracks=[]
    )
    # Then append new tracks by batch of 100
    for chunk in track_chunks:
        client.user_playlist_add_tracks(
            user.username, playlist_object["id"], tracks=chunk
        )

    client.user_playlist_change_details(
        message["username"],
        playlist_object["id"],
        description=message.get("description", ""),
        public=message.get("public", False),
    )
    os.remove(credentials_path)
