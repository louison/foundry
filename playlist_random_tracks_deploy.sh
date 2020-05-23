 gcloud functions deploy playlist_random_tracks \
    --entry-point random_playlist \
    --runtime python37 \
    --trigger-resource playlists_update \
    --trigger-event google.pubsub.topic.publish \
    --env-vars-file=.env.yaml \
    --service-account=playlist-maker@rapsodie.iam.gserviceaccount.com \
    --timeout 540s \
    --region europe-west1 \
    --verbosity info \