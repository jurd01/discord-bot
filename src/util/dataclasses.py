from dataclasses import dataclass


@dataclass
class Subscription:
    user_name: str  # username of the streamer
    server_id: int  # the server in which to post announcements
    channel_id: int  # the channel in which to post announcements
    server_name: str  # the name of the server in which to post announcements. this is mostly just for log readability.
    mention: str  # the role to mention


@dataclass
class Notification:
    id: int  # the ID of this notification
    user_id: int  # the id of the user whose status changed
    user_name: str
    game_id: int  #
    community_ids: str  # /shrug
    type: str  # 'live'
    title: str
    viewer_count: int
    started_at: str  # todo write down format
    language: str
    thumbnail_url: str
