import datetime as dt
import logging
import os
import time

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery, bigquery_storage_v1beta1
from twitter import Twitter, OAuth

from rapsodie.playlist_maker.auto_playlists import AutoPlaylist

# load_dotenv()

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
            # tweet += "https://sdz.sh/YwpKZ6"
            top -= 1

        t = Twitter(
            auth=OAuth(
                "1294658089-fTUOaVJ8V3IKPgQ8pj4g4jSWRc9OxAUot28QD8q",
                "muFlvClaGqvmeGsn2dhGmWTNaHeMMC6aecaDapIonsoZr",
                "idwPNaHFvcgtioKmfjvkchZZs",
                "ZMS1gmPuOrLIfEhOcefiOR0UhkKGFO7aeHDuW42TC7ZhyzGGDn",
            )
        )
        response = t.statuses.update(status=tweet)
        return response

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
            album.name album,
            album.album_type album_type,
            album.artists album_artists,
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
        ORDER BY
            stream.last_updated DESC
        """

        # Get Data
        logger.info("fetch data from bigquery")
        start = time.time()
        if ENVIRONMENT == "local":
            bq_client = bigquery.Client().from_service_account_json(
                "./sandox_creds.json"
            )
        else:
            logger.debug("SUCE")
            # bq_client = bigquery.Client()
        data = bq_client.query(daily_top_query).result().to_dataframe()
        end = time.time()
        logger.debug(f"done {round(end-start,2)}s")

        # Clean raw data
        logger.info("clean data")
        data.dropna(subset=["artist_id", "last_updated"], inplace=True)
        data.drop_duplicates(subset=["last_updated"], inplace=True)
        data = data[data["album_type"] != "compilation"]
        data = data[data["album_type"] != "single"]
        data["update_date"] = data.apply(lambda x: x["last_updated"].date(), axis=1)
        data["primary_album_artist_id"] = data.apply(
            lambda x: x["album_artists"][0], axis=1
        )

        # Remove bad artists
        data = data[data["artist_id"] != "55Aa2cqylxrFIXC767Z865"]  # Lil Wayne
        data = data[data["artist_id"] != "3nFkdlSjzX9mRTtwJOzDYB"]  # Jay-Z
        data = data[data["artist_id"] != "5j4HeCoUlzhfWtjAfM1acR"]  # Stroame
        data = data[
            ~data["primary_album_artist_id"].isin(["0LyfQWJT6nXafLPZqxe9Of"])
        ]  # Various artists for f*cking compliations
        data = data[data["artist_id"] != "1KQJOTeIMbixtnSWY4sYs2"]  # Paky IT

        data.sort_values(
            by=["track_id", "last_updated"], ascending=False, inplace=True
        )  # keep ?

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
        logger.debug(delta[:50])

        # Send tweet
        logger.info("create tweet")
        # t = self.create_tweet(delta)
        tweet_url = f"https://twitter.com/{t.get('user').get('screen_name')}/status/{t.get('id_str')}"
        logger.info(f"tweeted {tweet_url}")

        # Return tracks for playlist
        return delta[:top_length]["track_id"].to_list()
