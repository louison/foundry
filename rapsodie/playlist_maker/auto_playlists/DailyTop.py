import datetime as dt
import logging
import os
import time

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

from rapsodie.playlist_maker.auto_playlists import AutoPlaylist

# load_dotenv()

ENVIRONMENT = os.environ.get("PYTHONENV")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

relevant_columns = [
    "track",
    "track_id",
    "playcount",
    "playcount_diff",
    "artist",
    "artist_id",
    "update_date",
]


class DailyTop(AutoPlaylist):
    def compute_playcount_diff(self, df, isrc):
        track_data = (
            df[df["isrc"] == isrc]
            .sort_values(["track_id", "update_date"], ascending=False)
            .drop_duplicates(subset=["update_date"])
        )
        nb_rows = track_data.shape[0]
        if nb_rows != 2:
            return

        today = dt.date(2020, 7, 17)
        ystdy = today - dt.timedelta(days=1)
        bfr_ystdy = today - dt.timedelta(days=2)
        dates = track_data["update_date"].to_list()
        if (ystdy in dates) and (bfr_ystdy in dates):
            track_data["playcount_diff"] = track_data["playcount"].diff(periods=-1)
            return track_data[relevant_columns].iloc[0]
        print("else", track_data["isrc"].iloc[0])
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
            rapsodie_main.spotify_last_stream_rashad_20200717 AS stream
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
        logger.info("fetching data from bigquery")
        if ENVIRONMENT == "local":
            bq_client = bigquery.Client().from_service_account_json(
                "./sandox_creds.json"
            )
        else:
            logger.debug("SUCE")
            # bq_client = bigquery.Client()
        data = bq_client.query(daily_top_query).result().to_dataframe()

        # Clean raw data
        logger.info("cleaning data")
        data.dropna(subset=["artist_id", "last_updated"], inplace=True)
        data.drop_duplicates(subset=["last_updated"], inplace=True)
        data = data[data["album_type"] != "compilation"]
        data = data[data["album_type"] != "single"]
        # data.dropna(subset=['last_updated'], inplace=True)
        data["update_date"] = data.apply(lambda x: x["last_updated"].date(), axis=1)
        data["primary_album_artist_id"] = data.apply(
            lambda x: x["album_artists"][0], axis=1
        )

        data.sort_values(
            by=["track_id", "last_updated"], ascending=False, inplace=True
        )  # keep ?

        # remove bad artists
        data = data[data["artist_id"] != "55Aa2cqylxrFIXC767Z865"]  # Lil Wayne
        data = data[data["artist_id"] != "3nFkdlSjzX9mRTtwJOzDYB"]  # Jay-Z
        data = data[data["artist_id"] != "5j4HeCoUlzhfWtjAfM1acR"]  # Stroame
        data = data[
            ~data["primary_album_artist_id"].isin(["0LyfQWJT6nXafLPZqxe9Of"])
        ]  # Various artists for f*cking compliations

        logger.info("computing diff playcount")
        start = time.time()
        delta = pd.DataFrame(columns=relevant_columns)
        for isrc in data["isrc"].unique():
            delta = delta.append(self.compute_playcount_diff(data, isrc))
        end = time.time()
        logger.info(f"done with duration: {round(end-start,2)}s")
        delta.drop_duplicates(subset=["track_id", "track"], keep="first", inplace=True)
        delta.sort_values(by="playcount_diff", ascending=False, inplace=True)
        return delta[:top_length]["track_id"].to_list()
