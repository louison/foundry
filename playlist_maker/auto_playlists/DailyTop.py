import datetime as dt
import logging
import os
import time

import pandas as pd
from google.cloud import bigquery, pubsub_v1
from twitter import OAuth, Twitter

from rapsodie.playlist_maker.auto_playlists import AutoPlaylist

ENVIRONMENT = os.environ.get("PYTHONENV")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
                        row["track"],
                        row["artist"],
                        round(row["playcount_diff"] / row["playcount"] * 100, 2),
                    )
                )
                i += 1
            tweet = f"🤖 Top {top} des sons les plus streamés hier\n"
            for track in l:
                tweet += f"#{track[0]} {track[1]}, {track[2]} +{track[3]}%\n"
            tweet += "https://sdz.sh/ftAg2x"
            top -= 1

        message = {"platforms": ["slack", "twitter"], "body": tweet}
        notifier_topic = "projects/rapsodie/topics/notifier"
        publisher = pubsub_v1.PublisherClient()
        publisher.publish(notifier_topic, json.dumps(message).encode("utf-8"))

    def compute_playcount_diff(self, df, isrc):
        track_data = (
            df[df["isrc"] == isrc]
            .sort_values(["track_id", "update_date"], ascending=False)
            .drop_duplicates(subset=["update_date"])
        )
        nb_rows = track_data.shape[0]
        if nb_rows < 2:
            return
        today = dt.datetime.today().date()
        ystdy = today - dt.timedelta(days=1)
        bfr_ystdy = today - dt.timedelta(days=2)
        dates = track_data["update_date"].to_list()
        if (ystdy in dates) and (bfr_ystdy in dates):
            track_data["playcount_diff"] = track_data["playcount"].diff(periods=-1)
            track_data["playcount_diff_percent"] = (
                track_data["playcount"].diff(periods=-1)
                / track_data[track_data["update_date"] == bfr_ystdy]["playcount"].iloc[
                    0
                ]
            ) * 100
            # success
            return track_data[relevant_columns].iloc[0]
        return

    def get_tracks(self, top_length=50):
        """Most streams tracks daily
        Args:
            top_length (int, optional): How big the ranking is. Defaults to 50.
        """

        daily_top_query = """
        SELECT
            track.name track,
            track.id track_id,
            track.isrc isrc,
            artist.name artist,
            artist.id artist_id,
            stream.popularity popularity,
            stream.playcount playcount,
            stream.last_updated last_updated,
            album.id album_id,
            --   album.name album,
            TO_JSON_STRING(album.artists) album_artists,
        FROM
            rapsodie_main.spotify_track_playcount_trunc_latest AS stream
        LEFT JOIN
            rapsodie_main.spotify_track_artist_map AS track_artist
        ON
            track_artist.track_id = stream.track_id
        LEFT JOIN
            rapsodie_main.spotify_artist AS artist
        ON
            artist.id = track_artist.artist_id
        LEFT JOIN
            rapsodie_main.spotify_track AS track
        ON
            track.id = stream.track_id
        LEFT JOIN
            rapsodie_main.spotify_album AS album
        ON
            album.id = track.album_id
        WHERE
            artist_id != '55Aa2cqylxrFIXC767Z865' -- Lil Wayne
        AND artist_id != '3nFkdlSjzX9mRTtwJOzDYB' -- Jay-Z
        AND artist_id != '5j4HeCoUlzhfWtjAfM1acR' -- Stromae
        AND artist_id != '1KQJOTeIMbixtnSWY4sYs2' -- Stromae
        AND album.album_type != 'compilation'
        AND album.album_type != 'single'
        AND stream.last_updated IS NOT NULL
        AND '0LyfQWJT6nXafLPZqxe9Of' NOT IN UNNEST(album.artists)
        AND artist_id IS NOT NULL -- not working :(
        GROUP BY
                track,
                track_id,
                isrc,
                artist,
                artist_id,
                popularity,
                playcount,
                last_updated,
                album_id,
                album_artists
        """

        # Get Data
        logger.info("fetch data from bigquery")
        start = time.time()
        if ENVIRONMENT == "local":
            bq_client = bigquery.Client().from_service_account_json(
                "./sandox_creds.json"
            )
        else:
            bq_client = bigquery.Client()
        data = bq_client.query(daily_top_query).result().to_dataframe()
        end = time.time()
        logger.debug(f"done {round(end-start,2)}s")

        # Clean raw data
        logger.info("clean data")
        data.drop_duplicates(subset=["last_updated"], inplace=True)
        data["update_date"] = data.apply(lambda x: x["last_updated"].date(), axis=1)
        data["primary_album_artist_id"] = data.apply(
            lambda x: x["album_artists"][0], axis=1
        )

        data.sort_values(by=["track_id", "last_updated"], ascending=False, inplace=True)

        # Compute playcount delta
        logger.info("compute diff playcount...")
        start = time.time()
        delta = pd.DataFrame(columns=relevant_columns)
        nb_isrc = data["isrc"].nunique()
        for i, isrc in enumerate(data["isrc"].unique()):
            if i % 500 == 0:
                logger.debug(f"computing delta {i}/{nb_isrc}")
            delta = delta.append(self.compute_playcount_diff(data, isrc))
        end = time.time()
        logger.info(f"done: {round(end-start,2)}s")
        delta.drop_duplicates(subset=["track_id", "track"], keep="first", inplace=True)
        delta.sort_values(by="playcount_diff_percent", ascending=False, inplace=True)

        # Send tweet
        logger.info("send tweet")
        self.create_tweet(delta)

        # Return tracks for playlist
        return delta[:top_length]["track_id"].to_list()
