from typing import TypedDict, List, Optional, Dict


class NotifierMessage(TypedDict):
    platforms: List[str]
    body: str


class Message(TypedDict):
    entrypoint: str
    entrypoint_args: Optional[Dict]
    username: str
    playlist_name: str
    playlist_id: Optional[str]
    description: Optional[str]
    public: Optional[bool]
    playlist_cover: Optional[str]
    override: Optional[bool]
    push_method: str
    append: bool
    credentials: Dict
    tracks: List[str]
    announcements: List[NotifierMessage]
