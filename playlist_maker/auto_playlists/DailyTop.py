import datetime as dt
import logging
import os
import time

import pandas as pd
from google.cloud import bigquery, pubsub_v1
from twitter import OAuth, Twitter

from playlist_maker.auto_playlists import AutoPlaylist

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
    def create_tweet(self, df, top=5):
        # TODO: use twitter handles of rappers we have
        tweet = ""
        while len(tweet) > 280 or not tweet:
            i = 1
            l = []
            for index, row in df[:top].iterrows():
                l.append(
                    (
                        i,
                        row["track_name"],
                        " ".join(row["artist_name"]),
                        round(row["pct"] * 100, 2),
                    )
                )
                i += 1
            tweet = f"🤖 Top {top} des sons les plus streamés cette semaine\n"
            for track in l:
                tweet += f"#{track[0]} {track[1]}, {track[2]} +{track[3]}%\n"
            tweet += "https://sdz.sh/ftAg2x"
            top -= 1

        logger.debug(tweet)
        message = {"platforms": ["slack", "twitter"], "body": tweet}
        notifier_topic = "projects/rapsodie/topics/notifier"
        # publisher = pubsub_v1.PublisherClient()
        # publisher.publish(notifier_topic, json.dumps(message).encode("utf-8"))

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
            --timeframe_ends = CURRENT_DATE() - 1
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

        # Send tweet
        # logger.info("send tweet")
        # self.create_tweet(data)

        # Return tracks for playlist
        return data["track_id"].to_list()
