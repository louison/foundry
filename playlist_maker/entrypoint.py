import base64
import logging
import os
import json
from typing import List

import spotipy
from google.cloud import pubsub_v1

from playlist_maker import User
from playlist_maker.auto_playlists import AllArtists
from playlist_maker.auto_playlists import LatestReleases
from playlist_maker.auto_playlists import Diggers
from playlist_maker.auto_playlists import RandomTracks
from playlist_maker.auto_playlists import BillionStreams
from playlist_maker.auto_playlists import DailyTop
from playlist_maker.types import Message, NotifierMessage
from playlist_maker.utils import get_credentials, chunks

logger = logging.getLogger(__name__)

NOTIFIER_TOPIC = "projects/rapsodie/topics/notifier"
ANNOUNCER_TOPIC = os.environ.get("ANNOUNCER_TOPIC")

PUSH_METHODS = ["append", "replace", "keep"]

AUTO_PLAYLIST = {
    "generic": None,
    "random": RandomTracks,
    "diggers": Diggers,
    "allartists": AllArtists,
    "latestreleases": LatestReleases,
    "billionstreams": BillionStreams,
    "dailytop": DailyTop,
}


def announce(notifier_messages: List[NotifierMessage], pub_client=None,
             debug=False):
    if not pub_client:
        pub_client = pubsub_v1.PublisherClient()
    for notifier_message in notifier_messages:
        if debug:
            print(notifier_message)
        else:
            pub_client.publish(
                NOTIFIER_TOPIC,
                json.dumps(notifier_message).encode("utf-8")
            )


def start(event, context):
    if "data" in event:
        message = base64.b64decode(event["data"]).decode("utf-8")
        message = json.loads(message)
    else:
        message = event
    message = Message(**message)

    entrypoint_choice = message["entrypoint"]
    if entrypoint_choice in AUTO_PLAYLIST.keys():
        logger.debug(f"playlist {entrypoint_choice}")
        auto_playlist_class = AUTO_PLAYLIST.get(entrypoint_choice, None)
        if auto_playlist_class:
            auto_playlist = auto_playlist_class()
            args = message.get("entrypoint_args", {})
            message["tracks"] = auto_playlist.get_tracks(**args)
            announcements = auto_playlist.get_announcements()
            if announcements:
                message["announcements"] = announcements
        return generic(message)
    else:
        raise ValueError(f"{message.get('entrypoint')} is not supported")


def generic(message=None):
    if not "playlist_name" in message and not "playlist_id" in message:
        raise ValueError("You must provide a name or an id for the playlist")

    credentials = get_credentials(message)
    client = spotipy.Spotify(client_credentials_manager=credentials)
    user = User(message["username"], client=client)
    user.connect()
    user.fetch()
    playlist_name = message["playlist_name"]
    playlist_id = message.get('playlist_id', None)
    playlists = user.get_playlists()
    playlist_object = None
    if playlist_id:
        playlist_object = client.playlist(message.get("playlist_id"))

    if not playlist_object:
        names = list(map(lambda x: x["name"], playlists))
        if playlist_name in names:
            print(playlist_name)
            playlist_object = list(
                filter(lambda x: x["name"] == playlist_name, playlists)
            )[0]
            print(playlist_object)
    if playlist_object and not message['override']:
        raise ValueError(
            f"Playlist with name: {playlist_name} and id: {playlist_id}"
            f" already exist for user {message['username']} use -o to override"
        )
    if not playlist_object:
        playlist_object = client.user_playlist_create(
            user.username,
            playlist_name,
            public=message.get("public", False),
            description=message.get("description", ""),
        )

    push_method = message.get("push_method")
    if push_method == "append":
        tracks = user.get_playlist_tracks(playlist_object["id"])
        tracks_ids = list(map(lambda x: x["track"]["id"], tracks))
        message["tracks"].extend(tracks_ids)
    elif push_method == "keep":
        tracks = user.get_playlist_tracks(playlist_object["id"])
        tracks_ids = list(map(lambda x: x["track"]["id"], tracks))
        message["tracks"] = tracks_ids

    track_chunks = chunks(message["tracks"], 100)
    # First empty the playlist
    client.playlist_replace_items(playlist_object["id"], [])
    # Then append new tracks by batch of 100
    for chunk in track_chunks:
        client.playlist_add_items(playlist_object["id"], chunk)

    client.playlist_change_details(
        playlist_object["id"],
        name=message.get('playlist_name', playlist_object.get('name', "")),
        description=message.get("description", playlist_object.get('description', "")),
        public=message.get("public",  playlist_object.get('public', False)),
    )
    if message.get('announcements'):
        announce(message.get('announcements'))
