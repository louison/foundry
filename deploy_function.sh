export SPOTIFY_CLIENT_ID=c1a13ee99e88428e9e42a0dede318030
export SPOTIFY_CLIENT_SECRET=998d38d8c56146208fd4713384be909b
export SPOTIFY_SCOPES="playlist-read-collaborative playlist-modify-public playlist-read-private playlist-modify-private"
gcloud functions deploy playlist_maker \
   --allow-unauthenticated \
   --entry-point main \
   --runtime python37 \
   --trigger-resource playlists_update \
   --trigger-event google.pubsub.topic.publish \
   --service-account playlist-maker@rapsodie.iam.gserviceaccount.com \
   --timeout 540s \
   --region europe-west1 \
   --verbosity info