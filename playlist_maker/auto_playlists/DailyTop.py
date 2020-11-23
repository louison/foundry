import datetime
import json
import logging

from google.cloud import bigquery
from playlist_maker.auto_playlists import AutoPlaylist
from playlist_maker.types import NotifierMessage

logger = logging.getLogger(__name__)


class DailyTop(AutoPlaylist):

    def get_announcements(self):
        announcements = []
        self.data = json.loads(self.data)
        if not self.data:
            return None
        tweet = ""
        top = 5
        while len(tweet) > 280 or not tweet:
            # i = 1
            l = []
            for i, row in enumerate(self.data[:top]):
                l.append(
                    {
                        "rank": i + 1,
                        "track_name": row.get("track_name"),
                        "artist_name": " ".join(row["artist_name"]),
                        "evolution": round(row.get("pct"), 2),
                    }
                )
                i += 1
            tweet = f"🤖 Top {top} des sons les plus streamés aujourd'hui\n"
            for track in l:
                tweet += f"#{track.get('rank')} {track.get('track_name')}, {track.get('artist_name')} +{track.get('evolution')}%\n"
            tweet += "https://sdz.sh/ftAg2x"
            top -= 1
        announcements.append(NotifierMessage(platforms=["slack"], body=tweet))

        url = "https://i.imgur.com/XHWcrsI.jpg"
        announcements.append(NotifierMessage(platforms=["slack"], body=url))

        return announcements

    def get_tracks(self, top_length=50, top_timeframe=7):
        """Most streams tracks

        Args:
            top_length (int, optional): How many tracks in the playlist. Defaults to 50.
            top_timeframe (int, optional): Timeframe to compute top. Defaults to 7.

        Raises:
            ValueError: If data is missing from source

        Returns:
            list: `tracks` key contains spotify id lists of tracks
        """

        daily_top_query = """
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
                --timeframe_ends = CURRENT_DATE() - 5
                --AND timeframe_length = 7
                timeframe_ends = "{date}"
                AND timeframe_length = 1
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
        data = bq_client.query(
            daily_top_query.format(
                top_length=top_length,
                date=datetime.datetime.today().date()
            )
        ).result().to_dataframe()

        if data.empty:
            raise ValueError("DailyTop got empty dataframe from BigQuery!")

        self.data = data.head(top_length).to_json(orient="records")
        return data["track_id"].to_list()
