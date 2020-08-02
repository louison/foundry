import logging
import os
import sys

from dotenv import load_dotenv
from google.cloud import bigquery

from rapsodie import artistdb

from playlist_maker.auto_playlists import AutoPlaylist

load_dotenv()

ENVIRONMENT = os.environ.get("PYTHON_ENV")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Diggers(AutoPlaylist):
    def get_tracks(self, max_timeframe=30, max_followers=5000):
        """Get small artists latest tracks

        Args:
            max_timeframe (int, optional): [Oldest track]. Defaults to 30.
            max_followers (int, optional): Defaults to 5000.
        """

        database = artistdb.Database()
        artists = database.session.query(artistdb.Artist).all()

        blacklisted = list(filter(lambda x: x.is_blacklisted, artists))
        blacklisted = list(map(lambda x: x.spotify_id, blacklisted))
        blacklisted = list(filter(lambda x: x is not None, blacklisted))
        blacklisted = '\', \''.join(blacklisted)

        query = f"""
        with current_follo as (
        select artist_id, 
        array_agg(struct(followers, monthly_listeners )  order by last_updated desc limit 1)[safe_offset(0)] as follo_ml
        from `rapsodie.rapsodie_main.artist_creatorabout`
        group by artist_id
        ) 
        select 
        array_agg(st.id order by st.album_release_date  DESC limit 1)[safe_offset(0)] as track,
        from current_follo 
        inner join `rapsodie.rapsodie_main.spotify_track_artist_map` as stam on stam.artist_id = current_follo.artist_id 
        inner join (select track_id,
        array_agg(struct(playcount, popularity )  order by last_updated desc limit 1)[safe_offset(0)] as ppop
        from `rapsodie.rapsodie_main.spotify_track_playcount_trunc_latest` as stpltl
        group by track_id)
        as stptl on stptl.track_id = stam.track_id
        inner join `rapsodie.rapsodie_main.spotify_track` as st on st.id = stam.track_id
        where 
        current_follo.follo_ml.followers < {max_followers}
        and 
        DATE_DIFF(CURRENT_DATE('Europe/Paris'), st.album_release_date, DAY) <= {max_timeframe}
        and
        current_follo.artist_id not in ('{blacklisted}')

        group by current_follo.artist_id, current_follo.follo_ml.monthly_listeners
        order by current_follo.follo_ml.monthly_listeners DESC
        """

        logger.info("Fetching data in database...")
        bq_client = bigquery.Client()
        data = bq_client.query(query).result()
        rows = []
        for r in data:
            rows.append(r[0])


        logger.info("Done!")
        return rows[:50]

