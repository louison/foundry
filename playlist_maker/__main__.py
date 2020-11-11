import json
import os

from playlist_maker import entrypoint


def init():
    # event = "rapsodie-dailytop-event.json"
    event = "event.json"
    events_dir = os.getcwd() + "/events/"
    with open(events_dir + event) as f:
        message = json.load(f)
    # with open(".spotify_cache", "r") as file:
    #     creds = json.load(file)
    # message["credentials"] = creds
    entrypoint.start(message, None)


if __name__ == "__main__":
    init()
