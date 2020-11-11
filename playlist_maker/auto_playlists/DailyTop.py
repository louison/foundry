import datetime as dt
import json
import logging
import os
import time

import pandas as pd
from google.cloud import bigquery, pubsub_v1
from playlist_maker.auto_playlists import AutoPlaylist
from twitter import OAuth, Twitter

# ANNOUNCER_TOPIC = "projects/rapsodie/topics/announcer"  # TODO: pass to env var
ANNOUNCER_TOPIC = os.environ.get("ANNOUNCER_TOPIC")

logger = logging.getLogger(__name__)

relevant_columns = [
    "track",
    "track_id",
    "isrc",
    "playcount",
    "playcount_diff",
    "playcount_diff_percent",
    "artist",
    "artist_id",
    "update_date",
]


class DailyTop(AutoPlaylist):
    def get_tracks(self, top_length=50, top_timeframe=7):
        """Most streams tracks daily
        Args:
            top_length (int, optional): How big the ranking is. Defaults to 50.
        """

        daily_top_query = f"""
        SELECT
            ARRAY_AGG(DISTINCT track.id)[
        OFFSET
            (0)] track_id,
            --track.id track_id,
            track.name track_name,
            ARRAY_AGG(DISTINCT artist.name) artist_name,
            stream_evolution.pct,
            stream_evolution.playcount,
            stream_evolution.isrc,
            MAX(track.album_release_date) release_date,
            stream_evolution.timeframe_ends,
            stream_evolution.timeframe_length,
        FROM
            rapsodie_main.spotify_track_stream_evolution AS stream_evolution
        INNER JOIN
            rapsodie_main.spotify_track AS track
        ON
            track.isrc = stream_evolution.isrc
        INNER JOIN
            rapsodie_main.spotify_track_artist_map AS track_artist
        ON
            track_artist.track_id = track.id
        INNER JOIN
            rapsodie_main.spotify_artist AS artist
        ON
            artist.id = track_artist.artist_id
        WHERE
            timeframe_ends = CURRENT_DATE() - 3
            AND timeframe_length = 7
        GROUP BY
            isrc,
            track.name,
            stream_evolution.pct,
            stream_evolution.playcount,
            stream_evolution.timeframe_ends,
            stream_evolution.timeframe_length
            ORDER BY
            pct DESC
        LIMIT
            {top_length}
        """

        # Get Data
        logger.info("fetch data from bigquery")
        bq_client = bigquery.Client()
        data = bq_client.query(daily_top_query).result().to_dataframe()

        if data.empty:
            raise ValueError("DailyTop got empty dataframe from BigQuery!")

        # Send announce
        logger.info("sending message to announcer")
        message_data = data.head(top_length).to_json(orient="records")
        message = {
            "entrypoint": "dailytop",
            "platforms": ["slack"],
            "entrypoint_args": {"data": json.loads(message_data)},
        }
        publisher = pubsub_v1.PublisherClient()
        publisher.publish(ANNOUNCER_TOPIC, json.dumps(message).encode("utf-8"))

        # Return tracks for playlist
        logger.info("return tracklist to foundry")
        return data["track_id"].to_list()
