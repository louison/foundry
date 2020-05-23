 gcloud functions deploy playlist_maker \
    --entry-point cloud_playlist \
    --runtime python37 \
    --trigger-resource playlists_update \
    --trigger-event google.pubsub.topic.publish \
    --env-vars-file=.env.yaml \
    --timeout 540s \
    --region europe-west1 \
    --verbosity info \