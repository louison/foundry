import logging
import os
from typing import Optional, List

from google.cloud import bigquery
from rapsodie.platforms.GQLDatabase import GQLDatabase

from playlist_maker.auto_playlists import AutoPlaylist
from playlist_maker.types import NotifierMessage

logger = logging.getLogger(__name__)


class Diggers(AutoPlaylist):
    def get_tracks(self, max_timeframe=30, max_followers=5000,
                   only_primary=False):
        """Get small artists latest tracks

        Args:
            max_timeframe (int, optional): [Oldest track]. Defaults to 30.
            max_followers (int, optional): Defaults to 5000.
        
        Returns:
            list: `tracks` key contains spotify id lists of tracks
        """

        database = GQLDatabase()
        artists = database.fetch_all()

        blacklisted = list(filter(lambda x: x.is_blacklisted, artists))
        blacklisted = list(map(lambda x: x.spotify_id, blacklisted))
        blacklisted = list(filter(lambda x: x is not None, blacklisted))
        blacklisted = "', '".join(blacklisted)

        # Condition to tell whether the small artist must be primary on track
        oprimary_condition = " and is_primary = true" if only_primary else ""

        query = f"""
WITH
  small_artists AS (
  SELECT
    DISTINCT artist_id,
    sap.name,
    sac.monthly_listeners,
    sap.popularity
  FROM
    `rapsodie.rapsodie_main.spotify_artist_creatorabout` AS sac
  INNER JOIN
    `rapsodie.rapsodie_main.spotify_artist_popularity` AS sap
  ON
    sap.id = artist_id
  WHERE
    sac.monthly_listeners <= 15000
    AND CAST(sac.last_updated AS date) >= CURRENT_DATE()
    AND CAST(sap.last_updated AS date) >= CURRENT_DATE())
SELECT
  *
FROM (
  SELECT
    DISTINCT small_artists.artist_id,
    monthly_listeners,
    small_artists.name artist_name,
    st.id track_id,
    st.name track_name,
    small_artists.popularity,
    stp.playcount AS playcount,
    stp.last_updated,
    ROW_NUMBER() OVER (PARTITION BY small_artists.artist_id ORDER BY st.album_release_date DESC) AS row_rank,
    st.album_release_date,
    sal.album_type,
    (
      -- Get first release date for an artist
    SELECT
      MIN(st.album_release_date)
    FROM
      `rapsodie.rapsodie_main.spotify_track` AS st
    CROSS JOIN
      `rapsodie.rapsodie_main.spotify_artist` AS sa
    WHERE
      sa.id IN UNNEST(st.artists)
      AND sa.id = small_artists.artist_id
    GROUP BY
      sa.id) AS first_release_date
  FROM
    small_artists
  CROSS JOIN
    `rapsodie.rapsodie_main.spotify_track` AS st
  LEFT JOIN
    `rapsodie.rapsodie_main.spotify_album` AS sal
  ON
    st.album_id = sal.id
  LEFT JOIN (
    SELECT
      track_id,
      playcount,
      last_updated,
      ROW_NUMBER() OVER (PARTITION BY stp.track_id ORDER BY last_updated DESC) AS row_rank,
    FROM
      `rapsodie.rapsodie_main.spotify_track_playcount` AS stp ) AS stp
  ON
    st.id = stp.track_id
  WHERE
    small_artists.artist_id IN UNNEST(st.artists)
    AND small_artists.artist_id not in ('{blacklisted}')
    AND st.album_release_date > CURRENT_DATE() - 60
    AND sal.album_type != 'compilation'
    AND '0LyfQWJT6nXafLPZqxe9Of' not in unnest(sal.artists)
    -- Remove featurings ?
    --AND ARRAY_LENGTH(st.artists) < 2
    )
WHERE
  row_rank = 1
  AND first_release_date > CURRENT_DATE() - 1095
ORDER BY
  popularity DESC,
  playcount DESC
        """

        logger.info("Fetching data in database...")
        client = bigquery.Client()
        rows = client.query(query).result()
        tracks = []
        for row in rows:
            tracks.append(row['track_id'])
        self.announcement_data = tracks
        return tracks

    def get_announcements(self) -> List[NotifierMessage]:
        platforms = ['slack']
        body = "\n".join(self.announcement_data)
        return [NotifierMessage(platforms=platforms, body=body)]
