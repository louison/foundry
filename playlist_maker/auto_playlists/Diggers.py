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
with sap as ( 
select 
REPLACE(latest_release_uri, 'spotify:album:','') as album_id,
artist_id, 
latest_release_date, 
sap.monthly_listeners,
-- selectionner uniquement les dernières updates
row_number() over (partition by artist_id order by last_updated DESC) as rn
from `rapsodie.rapsodie_main.spotify_artist_page` as sap

)
select 
array_agg(struct(track_id, stp.popularity, sap.latest_release_date) ORDER BY sap.latest_release_date desc)[offset(0)] as str,
artist_id, 
--array_agg(stp.popularity  ORDER BY stp.popularity desc)[offset(0)] as pop
from sap
left join (
  with stp as (
    select
      playcount,
      popularity, 
      album_id, 
      track_id,
      row_number() over (partition by track_id order by last_updated DESC) as rn
    from
      `rapsodie.rapsodie_main.spotify_track_playcount`
  )
    select * from stp
    where rn = 1
)
as stp on sap.album_id = stp.album_id
where sap.rn = 1
and stp.track_id is not null
and  DATE_DIFF(CURRENT_DATE ()
            , sap.latest_release_date 
            , DAY) <= 30
and sap.monthly_listeners <= 10000
and sap.artist_id not in ('{blacklisted}') 
group by sap.artist_id
order by str.popularity desc;
        """

        logger.info("Fetching data in database...")
        client = bigquery.Client()
        rows = client.query(query).result()
        tracks = []
        for row in rows:
            tracks.append(row['str']['track_id'])
        self.announcement_data = tracks
        return tracks

    def get_announcements(self) -> List[NotifierMessage]:
        platforms = ['slack']
        body = "\n".join(self.announcement_data)
        return [NotifierMessage(platforms=platforms, body=body)]
