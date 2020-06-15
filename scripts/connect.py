import argparse
from rapsodie.playlist_maker import User

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", required=True)
    args = parser.parse_args()
    user = User(args.username)
    user.connect()
    user.fetch()
