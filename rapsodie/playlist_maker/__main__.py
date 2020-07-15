import json
from rapsodie.playlist_maker import entrypoint


def init():
    message = {
        "entrypoint": "allartists",
        "entrypoint_args": {},
        "username": "loulouxd",
        "playlist_name": "allartists",
        "playlist_id": "",
        "description": "All artists",
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
