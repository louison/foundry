import logging

import playlist_diggers
import playlist_random_tracks
from utils import pubsub, spotify

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def random_tracks(event, context):
    """Get 10 random tracks from BigQuery as a playlist
    Args:
        event (dict):  The dictionary with data specific to this type of
        event. The `data` field contains the PubsubMessage message. The
        `attributes` field will contain custom attributes if there are any.
        context (google.cloud.functions.Context): The Cloud Functions event
        metadata. The `event_id` field contains the Pub/Sub message ID. The
        `timestamp` field contains the publish time.
    """
    data = pubsub.decode_message_data(event)
    if "playlist_random_tracks" in data:
        tracks = playlist_random_tracks.get_tracks()
        spotify.push_to_playlist(tracks, "6hlAehDHbcmZXXYCz6sl72")


def diggers(event, context):
    """Get small artists latest tracks
    """
    data = pubsub.decode_message_data(event)
    if "playlist_diggers" in data:
        tracks = playlist_diggers.get_tracks()  # default parameters
        spotify.push_to_playlist(tracks, "2g2nZEjXnMW4jCDZcdw42M")
