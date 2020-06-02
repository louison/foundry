import base64
import logging


def decode_message_data(event):
    """Decode data content in PubSub message

    Args:
        event (dict): The dictionary with data specific to this type of
         event. The `data` field contains the PubsubMessage message. The
         `attributes` field will contain custom attributes if there are any.

    Returns:
        string: The decoded value of the data key.
    """
    if "data" in event:
        return base64.b64decode(event["data"]).decode("utf-8")
