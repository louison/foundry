# Foundry

The foundry app (previsouly known as the playlist maker) is used by Rapsodie to push machine-generated playlists on Spotify.

## Design

Foundry is basically just a Google Cloud Function triggered by events sent on a PubSub topic. Each playlist is triggered by a given event which contains all necessary information for the playlist to be created/updated.

The core playlist logic is containted in Foundry within classes in the `auto_playlists` directory.

The execution logic is handled in the `entrypoint.py` file.

For example the `RandomTracks.py` file defines the `RandomTracks` class with the `get_tracks()` method. This method fetches 10 random track in the db rand returns them. Those tracks are them passed to the `generic()` method that will connect to Spotify and update/create the playlist if needed.

## Run locally

### Virtual env
```sh
python3 -m venv venv
source venv/bin/activate
```

### Spotify credentials
At the root of the repo run the following commands
```sh
export PYTHONPATH=$(pwd)
export SPOTIFY_CLIENT_ID=e109534e11a24370aec072e3c798d41f
export SPOTIFY_CLIENT_SECRET= 
export SPOTIFY_REDIRECT_URI=https://localhost:8888
export SPOTIFY_SCOPES="playlist-read-collaborative playlist-modify-public playlist-read-private playlist-modify-private"
python scripts/connect.py -u your_spotify_username
```

This will generate a `.spotify_cache` file at the root of the repo.

### Personal event
To run Foundry locally you should start by defining your own event. It will simulate the kind of event that is sent on Cloud Scheduler to trigger the function in production. You can find a template in the `event/` directory at the root or the repo.

Here's an example of how to complete it
```json
{
    "entrypoint": "diggers", # which playlist is concerned [random, diggers]
    "username": "heus92", # your Spotify user name
    "playlist_name": "", # if it doesn't exist a new playlist will be created
    "playlist_id": "", # your existing playlist id
    "description": "", # playlist description that will appear in Spotify
    "public": "False", # public playlist are visible to anyone
    "playlist_cover": "", # not implemented
    "override": "True", # if False playlist should be empty not to fail
    "push_method": "replace", # [append, replace, keep]
    "append": "True", # not sure why we have this tbh
    "tracks": [], # not implemented 
    "credentials": {} # copy .spotify_cache file json
}
```

Make sure to name with the following convention to make sure you're credentials won't be committed: `user-entrypoint-event.json`. 

For example Rashad's event for the random playlist will be name `rashad-random-event.json` and production event for the diggers playlist will be `rapsodie-diggers-event.json`

### Go live ! 
Once you're all set up change the event file to be used in the `rapsodie/playlist_maker/__main__.py` file 
```python
event = "rashad-random-event.json"
```

And you can then run the magic command
```sh
python rapsodie/playlist_maker/__main__.py
```

## deploy to gcp

### deploy function

### create new trigger

export PYTHONPATH=\$(pwd) export SPOTIFY_CLIENT_ID=e109534e11a24370aec072e3c798d41f export SPOTIFY_CLIENT_SECRET= export SPOTIFY_SCOPES="playlist-read-collaborative playlist-modify-public playlist-read-private playlist-modify-private" export SPOTIFY_REDIRECT_URI=https://localhost:8888
