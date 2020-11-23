#!/usr/bin/env bash

gcloud functions deploy playlist_maker \
   --allow-unauthenticated \
   --entry-point main \
   --runtime python38 \
   --trigger-resource playlists_update \
   --trigger-event google.pubsub.topic.publish \
   --service-account playlist-maker@rapsodie.iam.gserviceaccount.com \
   --timeout 540s \
   --region europe-west1 \
   --verbosity info \
   --env-vars-file .env.yaml