 gcloud functions deploy random_playlist \
    --entry-point random_playlist \
    --runtime python37 \
    --trigger-resource playlists_update \
    --trigger-event google.pubsub.topic.publish \
    --set-env-vars PYTHON_ENV=dev \
    --timeout 540s \
    --region europe-west1 \
    --verbosity info \