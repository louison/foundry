#!/bin/bash

if [ $1 == "production" ]
then
    gcf="playlist_maker"
    topic="playlists_update"
elif [ $1 == "debug" ]
then
    gcf="playlist_maker_debug"
    topic="playlists_update_debug"
else
    echo "arg should be production or debug"
    exit
fi

echo "deploying $gcf"
gcloud functions deploy $gcf \
    --allow-unauthenticated \
    --entry-point main \
    --runtime python38 \
    --trigger-resource $topic \
    --trigger-event google.pubsub.topic.publish \
    --service-account playlist-maker@rapsodie.iam.gserviceaccount.com \
    --timeout 540s \
    --region europe-west1 \
    --verbosity info \
    --env-vars-file .env.yaml
