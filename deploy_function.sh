 gcloud functions deploy playlist_maker \
    --entry-point cloud_playlist \
    --runtime python37 \
    --trigger-resource playlists_update \
    --trigger-event google.pubsub.topic.publish \
    --set-env-vars PYTHON_ENV=development \
    --timeout 540s \
    --region europe-west1 \
    --verbosity info \