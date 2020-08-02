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
        with tracks as (
        select isrc,
        array_agg(struct(a.album_id, playcount, a.popularity, a.track_id, sa.type, sa.release_date) order by a.popularity DESC)[safe_offset(0)] as t_data,
        from
        (
        select * , row_number() over(partition by track_id,album_id order by last_updated DESC) as rn
        from `rapsodie.rapsodie_main.spotify_track_playcount_trunc_latest`
        ) a
        left join `rapsodie.rapsodie_main.spotify_track` as st on st.id = a.track_id
        left join `rapsodie.rapsodie_main.spotify_album` as sa on sa.id = a.album_id
        where sa.type not like 'compilation'
        and rn=1 
        and isrc is not null
        group by isrc
        )
        select
        tracks.isrc,
        tracks.t_data.album_id as album_id,
        tracks.t_data.playcount as playcount,
        tracks.t_data.popularity as popularity,
        tracks.t_data.track_id as track_id,
        tracks.t_data.release_date as release_date,
        stam.artist_id, 
        is_primary, 
        ac.followers, 
        ac.monthly_listeners 
        from tracks
        left join `rapsodie.rapsodie_main.spotify_track_artist_map` as stam on stam.track_id = tracks.t_data.track_id
        left join (select artist_id, followers, monthly_listeners
        from
        (
        select * , row_number() over(partition by artist_id order by last_updated DESC) as rn
        from `rapsodie.rapsodie_main.artist_creatorabout` 
        ) where rn =1  ) as ac on ac.artist_id = stam.artist_id
        where ac.artist_id is not null
        and
        is_primary = true
        and followers < {max_followers}
        and  DATE_DIFF(CURRENT_DATE(), t_data.release_date, DAY) <= {max_timeframe}
        and  stam.artist_id not in ('{blacklisted}')
        """

        logger.info("Fetching data in database...")
        client = bigquery.Client()
        df = client.query(query).to_dataframe()
        df = df.sort_values(['release_date', 'playcount'],
                            ascending=[False, False])
        df = df.groupby(['artist_id']).first().reset_index()
        df = df.sort_values(['monthly_listeners', 'followers'],
                            ascending=[False, False])
        logger.info("Done!")
        return list(df['track_id'].head(50))

