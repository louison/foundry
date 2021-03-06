import pandas as pd

from gql import gql
import logging

from rapsodie.platforms.GQLDatabase import GQLDatabase

from playlist_maker.auto_playlists import AutoPlaylist
from playlist_maker.types import NotifierMessage
from rapsodie.dsci.compute.top_streams import compute_evolution

logger = logging.getLogger(__name__)

GQL_QUERY = """
query Tracks($isrcs: [String!]!) {
  bq_spotify_track(
    where: {isrc: {_in: $isrcs},
   bq_spotify_track_artist_maps: {artist: {is_blacklisted: {_eq: false}}}}) {
    name
    isrc
    id
    album_release_date
    bq_spotify_track_artist_maps {
      artist {
        is_blacklisted
        names {
          name
        }
      }
    }
  }
}
"""


class DailyTop(AutoPlaylist):

    def get_announcements(self):
        announcements = []
        if not self.data:
            return None
        tracks = []
        for index, row in enumerate(self.data):
            anames = []
            for amap in row['bq_spotify_track_artist_maps']:
                cartist_names = amap['artist'].get('names')
                if cartist_names:
                    anames.append(cartist_names[0]['name'])
            track = {
                "rank": index + 1,
                "track_name": row.get("name"),
                "artist_name": " ".join(anames),
                "evolution": round(row.get("pct") * 100, 2),
            }
            tracks.append(
                f"#{track.get('rank')} {track.get('track_name')}, {track.get('artist_name')} +{track.get('evolution')}%"
            )
        top = len(tracks)
        prefix = "🤖 Top {top} des sons les plus streamés aujourd'hui\n".format(
            top=top)
        body = "\n".join(tracks[:top])
        suffix = "\nhttps://sdz.sh/ftAg2x"
        while len(prefix) + len(body) + len(suffix) > 280:
            top = top - 1
            body = "\n".join(tracks[:top])
        prefix = "🤖 Top {top} des sons les plus streamés aujourd'hui\n".format(
            top=top)
        tweet = prefix + body + suffix
        announcements.append(NotifierMessage(platforms=["slack"], body=tweet))

        url = "https://i.imgur.com/XHWcrsI.jpg"
        announcements.append(NotifierMessage(platforms=["slack"], body=url))

        return announcements

    def get_tracks(self, top_length=50, top_timeframe=7):
        df = compute_evolution(1, returns_df=True) # Get stream evolution for timeframe = 1
        df = df.sort_values('pct', ascending=False).head(top_length) # We want the top_length highest pct values
        # Query additional metadata for tracks
        database = GQLDatabase()
        query = gql(GQL_QUERY)
        params = {'isrcs': list(df['isrc'])}
        result = database.client.execute(query, variable_values=params)
        df2 = pd.DataFrame(result['bq_spotify_track'])
        df2 = df2.groupby('isrc').first()
        df = df.merge(df2, left_on='isrc', right_on='isrc')
        self.data = df.sort_values('pct', ascending=False).to_dict(
            orient='records')
        return list(df['id'])
