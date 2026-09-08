import io

from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager
)

from winrt.windows.storage.streams import DataReader

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


async def get_thumbnail(session):
    try:
        info = await session.try_get_media_properties_async()

        thumbnail = info.thumbnail

        if thumbnail is None:
            return None

        stream = await thumbnail.open_read_async()

        if not stream.size:
            stream.close()
            return None

        reader = DataReader(
            stream.get_input_stream_at(0)
        )

        await reader.load_async(
            stream.size
        )

        data = bytearray(
            stream.size
        )

        reader.read_bytes(data)

        reader.close()
        stream.close()

        return bytes(data)

    except Exception as e:
        print(f"Thumbnail error: {e}")
        return None


async def get_music_info(session):

    info = await session.try_get_media_properties_async()

    timeline = session.get_timeline_properties()

    playback = session.get_playback_info()

    source = detect_source(session)

    thumbnail = await get_thumbnail(session)

    return {
        "title": info.title or "",
        "artist": info.artist or "",
        "album": info.album_title or "",

        "position": (
            timeline.position.total_seconds()
        ),

        "duration": (
            timeline.end_time.total_seconds()
        ),

        "last_updated": (
            timeline.last_updated_time
        ),

        "status": (
            playback.playback_status
        ),

        "rate": (
            playback.playback_rate or 1.0
        ),

        "source": source,

        "thumbnail": thumbnail,
    }