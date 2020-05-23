# playlist_maker
New cloud version of the playlist maker.
To better understand the logic we built an example playlist that selects 10 random tracks from our database and pushes them in a playlist.

A playlist is composed of 2 files: `playlist_yourplaylist.py` and `playlist_yourplaylist_deploy.sh`.

## 1. Create the Spotify playlist
Manually create the playlist on Rapsodie's Spotify account. 
Get the playlist id. You can find it in the URL you get from the share button. It's a long ugly string that should look like `6olAehDHbcmZYMYCz6sl79`.

## 2. Create your core logic
Create a new file name `playlist_yourplaylist.py` at the root of the folder.
It must implement a `get_tracks` method that will be called by the cloud function.

## 3. Create the cloud function
Update the `main.py` file to add the cloud function. The structure is always the same, get the tracks and then push to Spotify.
Make sure that you filter out all events that are not related to your playlit

Basically you'll always have something like
```
def random_tracks(event, context):
    data = pubsub.decode_message_data(event)
    if 'playlist_random_tracks' in data: # make sure we're concerned
        tracks = playlist_random_tracks.get_tracks()
        spotify.push_to_playlist(tracks, playlist_id)
```
The `event` and `context` parameters are required by Google Cloud and will allow us to update the functions asynchronously.

## 4. Deploy your function
Create a new `playlist_yourplaylist_deploy.sh` file to handle your function deployment.
Below is a template for such a file.
```
gcloud functions deploy playlist_nameofyourplaylist \
   --entry-point nameofyourfunctioninmainpy \
   --runtime python37 \
   --trigger-resource playlists_update \
   --trigger-event google.pubsub.topic.publish \
   --env-vars-file=.env.yaml \
   --service-account=playlist-maker@rapsodie.iam.gserviceaccount.com \
   --timeout 540s \
   --region europe-west1 \
   --verbosity info \
```

- The first argument defines the cloud function. It must start with `playlist_` so that we don't mess up the Cloud Console items and can easily identify them.
- The second argument is the name of the function you created in the `main.py` file.
- Do not change other parameters ⚠️

## 5. Create the event !

## Side Notes
🕵️‍♀️ If you need to store environment variables you can use a local `.env` file. If those variables need to be pushed to the cloud function using the .env.yaml file.

👨‍🏫 Make sure you are consistent with the function, and playlist names otherwise the repo will become garbage in no time.


🐍 You might need to set your `PYTHONPATH` at some point using the following command
```
export PYTHONPATH=$PWD
```
