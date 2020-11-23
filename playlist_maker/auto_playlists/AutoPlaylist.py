from typing import TypedDict, List, Optional

from playlist_maker.types import NotifierMessage


class AutoPlaylist:
    def __init__(self):
        self.data = None

    def get_tracks(self):
        raise NotImplementedError(f"get_tracks not implemented")

    def get_announcements(self) -> List[NotifierMessage]:
        return []
