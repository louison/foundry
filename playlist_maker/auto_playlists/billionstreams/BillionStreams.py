import logging
import os
import sys

from google.cloud import bigquery

from playlist_maker.auto_playlists import AutoPlaylist

ENVIRONMENT = os.environ.get("PYTHON_ENV")

logger = logging.getLogger(__name__)

class BillionStreams(AutoPlaylist):

    def get_tracks(self, threshold_max=None, threshold_min=0):
        """Core playlist logic. Gather tracks you want here

        Returns:
            list -- A list of Spotify tracks song id (strings)
        """
        if threshold_max:
            pp = f"and playcount <= {threshold_max}"
        else:
            pp = ""

        query = f"""
with max_pc as (
select distinct track_id, max(playcount) playcount  from `rapsodie.rapsodie_main.spotify_track_playcount`
group by track_id
)
select max(max_pc.track_id) from max_pc
join `rapsodie.rapsodie_main.spotify_track` as st on st.id = max_pc.track_id 
left join `rapsodie.rapsodie_main.spotify_track_artist_map` as stam on stam.track_id = max_pc.track_id
where stam.artist_id in (select distinct id from `rapsodie.rapsodie_main.spotify_artist`)
and stam.artist_id not in (
'5j4HeCoUlzhfWtjAfM1acR', # Stromae
'55Aa2cqylxrFIXC767Z865',
'15UsOTVnJzReFVN1VCnxy4',
'3nFkdlSjzX9mRTtwJOzDYB',
'5pKCCKE2ajJHZ9KAiaK11H',
'5K4W6rqBFWDnAN6FQUkS6x',
'3DiDSECUqqY1AuBP8qtaIa',
'3TVXtAsR1Inumwj472S9r4',
'7FAnawAJI7lHt4s1Ohde8w'
)
and playcount > {threshold_min}
{pp}

group by st.isrc, playcount
order by playcount desc;


        """
        bq_client = bigquery.Client()
        rows = bq_client.query(query).result()
        tracks = [row[0] for row in rows]

        return tracks
