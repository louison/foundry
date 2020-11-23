import logging
import os

from google.cloud import bigquery

from rapsodie.platforms.database import Database, Artist

from playlist_maker.auto_playlists import AutoPlaylist


ENVIRONMENT = os.environ.get("PYTHON_ENV")

logger = logging.getLogger(__name__)


class Diggers(AutoPlaylist):
    def get_tracks(self, max_timeframe=30, max_followers=5000, only_primary=False):
        """Get small artists latest tracks

        Args:
            max_timeframe (int, optional): [Oldest track]. Defaults to 30.
            max_followers (int, optional): Defaults to 5000.
        
        Returns:
            list: `tracks` key contains spotify id lists of tracks
        """

        database = Database()
        artists = database.session.query(Artist).all()

        blacklisted = list(filter(lambda x: x.is_blacklisted, artists))
        blacklisted = list(map(lambda x: x.spotify_id, blacklisted))
        blacklisted = list(filter(lambda x: x is not None, blacklisted))
        blacklisted = "', '".join(blacklisted)

        # Condition to tell whether the small artist must be primary on track
        oprimary_condition = " and is_primary = true" if only_primary else ""

        query = f"""
       -- Select latest track statistics (playcount, popularity)
        -- Remove tracks issued on compilation
        -- group by isrc to avoid track duplicates
        with tracks as (
            select isrc,
                   array_agg(struct(a.album_id, playcount, a.popularity, a.track_id, sa.type, sa.release_date)
                             order by a.popularity DESC)[safe_offset(0)] as t_data,
            from (
                     select *, row_number() over (partition by track_id,album_id order by last_updated DESC) as rn
                     from rapsodie.rapsodie_main.spotify_track_playcount_trunc_latest
                 ) a
                     left join rapsodie.rapsodie_main.spotify_track as st
            on st.id = a.track_id
                left join rapsodie.rapsodie_main.spotify_album as sa on sa.id = a.album_id
            where sa.type not like 'compilation'
              and rn=1
              and isrc is not null
            group by isrc
        )
        select tracks.isrc,
               tracks.t_data.album_id     as album_id,
               tracks.t_data.playcount    as playcount,
               tracks.t_data.popularity   as popularity,
               tracks.t_data.track_id     as track_id,
               tracks.t_data.release_date as release_date,
               stam.artist_id,
               is_primary,
               ac.followers,
               ac.monthly_listeners
        from tracks
                 left join rapsodie.rapsodie_main.spotify_track_artist_map as stam
        on stam.track_id = tracks.t_data.track_id
            -- select latest statistics for artists (followers + monthly listeners)
            left join (select artist_id, followers, monthly_listeners
            from
            (
            select * , row_number() over (partition by artist_id order by last_updated DESC) as rn
            from rapsodie.rapsodie_main.spotify_artist_creatorabout
            ) where rn =1 ) as ac on ac.artist_id = stam.artist_id
        where ac.artist_id is not null
        {oprimary_condition}
          and followers
            < {max_followers}         -- select only tracks with an artist < X followers (currently)
          and DATE_DIFF(CURRENT_DATE ()
            , t_data.release_date
            , DAY) <= {max_timeframe} -- select only tracks released withing max_timeframe days
          and stam.artist_id not in ('{blacklisted}') -- select only tracks where the artist is not black listed
        """

        logger.info("Fetching data in database...")
        client = bigquery.Client()
        df = client.query(query).to_dataframe()
        # Sort tracks by most recent release and the by playcount
        df = df.sort_values(
            ["popularity", "playcount", "release_date"], ascending=[False, False, False]
        )
        # Group all tracks by artist_id an keep the first one (the most recent one and the most streamed)
        df = df.groupby(["artist_id"]).first().reset_index()
        # Order results by monthely_listeners and number of followers
        df = df.sort_values(
            ["monthly_listeners", "followers"], ascending=[False, False]
        )
        logger.info("Done!")
        tracks = list(df["track_id"].head(50))
        return tracks
