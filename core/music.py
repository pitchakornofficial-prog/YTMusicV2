import asyncio

from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager
)


async def get_manager():
    return await GlobalSystemMediaTransportControlsSessionManager.request_async()


async def get_current_session(manager):
    return manager.get_current_session()


def detect_source(session):
    app_id = session.source_app_user_model_id

    if not app_id:
        return "Unknown"

    app_id = app_id.lower()

    # Spotify Desktop
    if "spotify.exe" in app_id:
        return "Spotify"

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