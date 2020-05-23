from google.cloud import bigquery
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def random_playlist(event, context):
    QUERY = """
    SELECT
        id
    FROM
        rapsodie_main.spotify_track
    ORDER BY
        rand()
    LIMIT
        10
    """
    bq_client = bigquery.Client()
    rows = bq_client.query(QUERY).result()
    for row in rows:
        logger.info(row)
