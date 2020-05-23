# playlist_maker
New cloud version of the playlist maker

A playlist = 1 folder. The structure is similar to the sample app name `random_playlist` that creates a playlist out of 10 random tracks from BigQuery.

To create a new playlist you need to
1. Manually create the playlist on Rapsodie's Spotify accounnt
2. Get the playlist id. You can find it in the URL you get from the share button


export PYTHONPATH=$PWD

# Deployment
```
 gcloud functions deploy playlist_name \
    --entry-point playlist_function \
    --runtime python37 \
    --trigger-resource playlists_update \
    --trigger-event google.pubsub.topic.publish \
    --env-vars-file=.env.yaml \
    --timeout 540s \
    --region europe-west1 \
    --verbosity info \
```