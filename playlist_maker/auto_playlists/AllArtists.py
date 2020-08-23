import logging
import os

from google.cloud import bigquery

from playlist_maker.auto_playlists import AutoPlaylist


ENVIRONMENT = os.environ.get("PYTHON_ENV")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AllArtists(AutoPlaylist):
    def get_tracks(self):


        query = """
      select array_agg(stam.track_id)[OFFSET(0)] as track_id, sa.id from `rapsodie.rapsodie_main.spotify_artist` as sa
join `rapsodie.rapsodie_main.spotify_track_artist_map` as stam on stam.artist_id = sa.id
where stam.is_primary = true
group by sa.id 
        """

        bq_client = bigquery.Client()
        data = bq_client.query(query).result().to_dataframe()
        logger.info("Processing data")
        logger.info("Done!")
        return data["track_id"].to_list()

if __name__ == '__main__':
    allartist = AllArtists()
    allartist.get_tracks()