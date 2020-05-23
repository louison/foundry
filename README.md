# playlist_maker
New cloud version of the playlist maker

A playlist = 1 folder. The structure is similar to the sample app name `random_playlist` that creates a playlist out of 10 random tracks from BigQuery.

To create a new playlist you need to
1. Manually create the playlist on Rapsodie's Spotify accounnt
2. Get the playlist id. You can find it in the URL you get from the share button


.
└── playlist_repo
    ├── deploy_function.sh
    ├── main.py
    └── requirements.txt

export PYTHONPATH=$PWD