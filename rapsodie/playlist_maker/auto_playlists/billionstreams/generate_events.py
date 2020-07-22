import json
import math
from pprint import pprint

from rapsodie.playlist_maker import entrypoint

description_template = "Les morceaux du rap francophone entre {min} et {max} écoutes"
long_millnames = ['', ' Milliers', ' Millions', ' Milliards', ' Trillion']
short_millnames = ['', 'K', 'M', 'B', 'T']

DEFAULT_EVENT = {
    "entrypoint": "billionstreams",
    "entrypoint_args": {},
    "username": "",
    "playlist_name": "",
    "playlist_id": "",
    "description": "",
    "public": True,
    "playlist_cover": "",
    "override": True,
    "push_method": "replace",
    "append": False,
    "tracks": []
}


def millify(n, millnames):
    n = float(n)
    millidx = max(0, min(len(millnames) - 1,
                         int(math.floor(
                             0 if n == 0 else math.log10(abs(n)) / 3))))

    return '{:.0f}{}'.format(n / 10 ** (3 * millidx), millnames[millidx])


def main():
    for i in range(1, 10):
        thres_min = i * 10000000
        thres_max = (i + 1) * 10000000
        DEFAULT_EVENT["entrypoint_args"] = {
            "threshold_min": thres_min,
            "threshold_max": thres_max
        }
        DEFAULT_EVENT[
            "playlist_name"] = f"{millify(thres_min, short_millnames)}-{millify(thres_max, short_millnames)} Streams"
        DEFAULT_EVENT["description"] = description_template.format(
            min=millify(thres_min, long_millnames),
            max=millify(thres_max, long_millnames)
        )

        with open(".spotify_cache", "r") as file:
            creds = json.load(file)
        DEFAULT_EVENT["credentials"] = creds
        entrypoint.start(DEFAULT_EVENT, None)


if __name__ == '__main__':
    main()
