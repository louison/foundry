import json
from rapsodie.playlist_maker import entrypoint


def init():
    message = {
        "entrypoint": "random",
        # "entrypoint_args": {"max_timeframe": 90, "max_followers": 1500},
        "username": "heus92",
        "playlist_name": "goldiggers",
        "playlist_id": "",
        "description": "coucou",
        "public": False,
        "playlist_cover": "",
        "override": True,
        "push_method": "replace",  # replace or append or keep
        "append": True,
        "tracks": ["0fAHY4PWSEbov0OHjj2Gek"],
    }
    with open(".spotify_cache", "r") as file:
        creds = json.load(file)
    message["credentials"] = creds
    entrypoint.start(message, None)


if __name__ == "__main__":
    init()
