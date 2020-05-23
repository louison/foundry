import logging

import playlist_random_tracks
from utils import spotify

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def random_tracks(event, context):
    """Creates a playlist with random tracks from BigQuery

    Arguments:
        event {dict} -- Some random stuff Google Cloud neeeds
        context {dict} -- Some other random stuff Google Cloud needs
    """
    tracks = playlist_random_tracks.get_tracks()
    spotify.push_to_playlist(tracks, "6hlAehDHbcmZXXYCz6sl72")
