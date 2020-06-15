# from rapsodie.playlist_maker import entrypoint
from rapsodie.playlist_maker import main as entrypoint


def main(event, context):
    entrypoint.start(event, context)
