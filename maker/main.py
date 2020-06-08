import logging
import os
import spotipy
import argparse
from google.cloud import bigquery

from maker import User

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

spotify_client_id = os.environ.get("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
spotify_redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI")
spotify_scopes = os.environ.get("SPOTIFY_SCOPES")


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
    bq_client = bigquery.Client()
    rows = bq_client.query(query).result()
    tracks = [row[0] for row in rows]
    return tracks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", required=True)
    parser.add_argument("-o", "--override", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-n", "--playlist-name")
    group.add_argument("-i", "--playlist-id")
    args = parser.parse_args()
    if not args.playlist_name and not args.playlist_id:
        raise ValueError("You must provide a name or an id for the playlist")
    creds = spotipy.SpotifyOAuth(
        scope=spotify_scopes,
        client_id=spotify_client_id,
        client_secret=spotify_client_secret,
        redirect_uri=spotify_redirect_uri,
        cache_path=".spotify_cache",
    )
    spotipy.Spotify()
    client = spotipy.Spotify(client_credentials_manager=creds)
    user = User(args.username, client=client)
    user.connect()
    user.fetch()
    if args.playlist_name:
        playlists = user.get_playlists()
        names = list(map(lambda x: x['name'], playlists))
        if args.playlist_name in names:
            if args.override:
                playlist_object = list(filter(
                    lambda x: x['name'] == args.playlist_name, playlists
                ))[0]
            else:
                raise ValueError(
                    f"Playlist with name: {args.playlist_name}"
                    f" already exist for user {user.username} use -o to override")
        else:
            playlist_object = client.user_playlist_create(
                user.username,
                args.playlist_name
            )
    else:
        playlist_object = client.playlist(args.playlist_id)
    tracks = get_tracks()
    client.user_playlist_replace_tracks(
        user.username,
        playlist_object['id'],
        tracks=tracks
    )


if __name__ == '__main__':
    main()
