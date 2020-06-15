import json
from playlist_maker import main

def init():
    message = {
        "entrypoint": "diggers",
        "entrypoint_args": {"max_timeframe": 90, "max_followers": 1500},
        "username": "heus92",
        "playlist_name": "goldiggers",
        "playlist_id": "",
        "description": "My super random playlist v9.2",
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
    main.entrypoint(message, None)
    # entrypoint(None, None, message=message)


if __name__ == "__main__":
    init()