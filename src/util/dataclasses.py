from dataclasses import dataclass, fields

from src.util.logging import get_logger

logger = get_logger(__name__)


@dataclass(init=False)
class Base:
    def __init__(self, **kwargs):
        _self_fields = {field.name: field.type for field in fields(self)}
        for field, typ in _self_fields.items():
            value = kwargs.pop(field, None)
            if value:
                try:
                    value = typ(value)
                except ValueError as e:
                    logger.warn(f'Failed to cast {value} to {typ} in dataclass init.')
                    # logger.exception(e)
            setattr(self, field, value)
        if kwargs:
            logger.warn(f'Unexpected kwargs received in dataclass init: {kwargs}')


@dataclass
class Subscription(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    user_name: str  # username of the streamer
    server_id: int  # the server in which to post announcements
    channel_id: int  # the channel in which to post announcements
    server_name: str  # the name of the server in which to post announcements. this is mostly just for log readability.
    mention: str  # the role to mention


@dataclass()
class Notification(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id: int  # the ID of this notification
    user_id: int  # the id of the user whose status changed
    user_name: str
    game_id: int  #
    type: str  # 'live'
    title: str
    viewer_count: int
    started_at: str  # todo write down format
    language: str
    thumbnail_url: str
    tag_ids: list  # not part of docs https://dev.twitch.tv/docs/api/webhooks-reference
    community_ids: list
