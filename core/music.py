import asyncio

from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager
)

from core.sources.spotify import SpotifySource
from core.sources.youtube_music import YouTubeMusicSource
from core.sources.youtube import YouTubeSource


SOURCES = [
    SpotifySource(),
    YouTubeMusicSource(),
    YouTubeSource(),
]


async def get_manager():
    return await GlobalSystemMediaTransportControlsSessionManager.request_async()


async def get_current_session(manager):
    return manager.get_current_session()


def detect_source(session):

    for source in SOURCES:
        if source.can_handle(session):
            return source.get_name()

    return "Unknown"


async def get_music_info(session):

    info = await session.try_get_media_properties_async()

    timeline = session.get_timeline_properties()

    playback = session.get_playback_info()

    source = detect_source(session)

    return {
        "title": info.title or "",
        "artist": info.artist or "",
        "album": info.album_title or "",

        "position": timeline.position.total_seconds(),
        "duration": timeline.end_time.total_seconds(),

        "last_updated": timeline.last_updated_time,

        "status": playback.playback_status,
        "rate": playback.playback_rate or 1.0,

        "source": source,
    }