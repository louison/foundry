import json
import logging
import re

import requests
import time

"""
A helper class to grab a public spotify token from their home page http://open.spotify.com
"""

TOKEN = None
TIME = time.time()
MAIN_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'

logging.basicConfig()
logger = logging.getLogger(__name__)


def get_token():
    """
    Get current cached token or ask for a new one if expired
    :return: spotify token
    :rtype: str
    """
    global TOKEN, TIME
    current_time = time.time()
    if not TOKEN or (current_time - TIME > 500):
        logger.debug("refreshing token")
        TOKEN = refresh_token()
        TIME = time.time()
    return TOKEN


def force_token_refresh():
    """
    Ask for a new token, never check cache
    :return: spotify token
    :rtype: str
    """
    global TOKEN, TIME
    TOKEN = refresh_token()
    TIME = time.time()


def refresh_token():
    """
    Fetch token from spotify home page
    :return: spotify token
    :rtype: str
    """
    headers = {
        'User-Agent': MAIN_USER_AGENT
    }
    url = 'https://open.spotify.com/'
    response = requests.get(url, headers=headers)
    text = response.text
    text = text.replace('\n', '')
    result = re.search(
        r'type="application/json">(.*?)</script>', text)
    if result:
        try:
            json_data = json.loads(result.group(1))
            token = json_data.get('accessToken')
            logger.info(f"new token issued: {token}")
            return token
        except ValueError as e:
            logger.error(
                'invalid json when trying to extract spotify access token')
            logger.error(e)
    token_cookie = response.cookies.get('wp_access_token', None)
    if token_cookie:
        token = token_cookie.value
        logger.info(f"new token issued: {token}")

if __name__ == '__main__':
    get_token()
