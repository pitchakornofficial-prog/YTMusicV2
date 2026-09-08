import asyncio
import time
import bisect

from core.music import (
    get_manager,
    get_current_session,
    get_music_info,
)

from core.lyrics import (
    search_lyrics,
    parse_lrc,
    build_lyrics_index,
)

from core.bluetooth import (
    find_and_connect,
    send,
)


PLAYING = 4

MEDIA_POLL_INTERVAL = 0.5

LYRIC_UPDATE_INTERVAL = 0.02

SEEK_THRESHOLD = 2.0


class PlayerState:

    def __init__(self):

        self.title = ""

        self.artist = ""

        self.album = ""

        self.thumbnail = None

        self.source = "Unknown"

        self.duration = 0.0

        self.lyrics = []

        self.lyric_times = []

        self.anchor_position = 0.0

        self.anchor_clock = time.perf_counter()

        self.playing = False

        self.rate = 1.0

        self.windows_position = 0.0

        self.display_position = 0.0

        self.last_lyric_index = -1

        self.bluetooth_connected = False

        self.lock = asyncio.Lock()


state = PlayerState()


async def set_anchor(position, playing, rate):

    async with state.lock:

        state.anchor_position = float(position)

        state.anchor_clock = time.perf_counter()

        state.playing = playing

        state.rate = rate or 1.0

        state.windows_position = float(position)

        state.display_position = float(position)


async def get_position():

    async with state.lock:

        anchor_position = state.anchor_position

        anchor_clock = state.anchor_clock

        playing = state.playing

        rate = state.rate

        duration = state.duration

    if not playing:
        return anchor_position

    elapsed = (
        time.perf_counter()
        - anchor_clock
    )

    position = (
        anchor_position
        + elapsed * rate
    )

    if duration > 0:

        position = min(
            position,
            duration
        )

    return position


async def load_song(music, connection):

    title = music["title"]

    artist = music["artist"]

    album = music.get(
        "album",
        ""
    )

    thumbnail = music.get(
        "thumbnail"
    )

    duration = music["duration"]

    source = music["source"]

    position = music["position"]

    status = music["status"]

    rate = music["rate"] or 1.0

    playing = (
        status == PLAYING
    )

    async with state.lock:

        state.title = title

        state.artist = artist

        state.album = album

        state.thumbnail = thumbnail

        state.source = source

        state.duration = duration

        state.lyrics = []

        state.lyric_times = []

        state.last_lyric_index = -1

        state.anchor_position = position

        state.anchor_clock = time.perf_counter()

        state.playing = playing

        state.rate = rate

        state.windows_position = position

        state.display_position = position

        state.bluetooth_connected = (
            connection is not None
        )

    print()

    print("==============================")

    print(f"Title    : {title}")

    print(f"Artist   : {artist}")

    print(f"Album    : {album}")

    print(f"Duration : {duration:.2f}")

    print(f"Source   : {source}")

    print(f"Position : {position:.2f}")

    print(
        f"Thumbnail: "
        f"{'YES' if thumbnail else 'NO'}"
    )

    print("==============================")

    if connection:

        send(
            connection,
            f"INFO={title}|{artist}|"
        )

    print("Searching lyrics...")

    try:

        lrc = await asyncio.to_thread(
            search_lyrics,
            title,
            artist,
            duration
        )

    except Exception as e:

        print(
            f"Lyrics search error: {e}"
        )

        return

    if not lrc:

        print("Lyrics not found.")

        return

    lyrics = parse_lrc(lrc)

    lyric_times = build_lyrics_index(
        lyrics
    )

    if not lyrics:

        print("Lyrics empty.")

        return

    async with state.lock:

        state.lyrics = lyrics

        state.lyric_times = lyric_times

        state.last_lyric_index = -1

    print(
        f"Found {len(lyrics)} lyric lines"
    )


async def media_monitor(manager, connection):

    current_session = None

    current_song = None

    previous_status = None

    previous_rate = None

    previous_position = None

    while True:

        try:

            session = await get_current_session(
                manager
            )

            if session != current_session:

                current_session = session

                current_song = None

                previous_status = None

                previous_rate = None

                previous_position = None

                print(
                    "\nMedia session changed."
                )

                if session is None:

                    await asyncio.sleep(
                        MEDIA_POLL_INTERVAL
                    )

                    continue

            if session is None:

                await asyncio.sleep(
                    MEDIA_POLL_INTERVAL
                )

                continue

            music = await get_music_info(
                session
            )

            title = music["title"]

            artist = music["artist"]

            duration = music["duration"]

            windows_position = float(
                music["position"]
            )

            status = music["status"]

            rate = (
                music["rate"] or 1.0
            )

            playing = (
                status == PLAYING
            )

            song_id = (
                title,
                artist,
                round(duration, 1)
            )

            if song_id != current_song:

                current_song = song_id

                previous_status = status

                previous_rate = rate

                previous_position = (
                    windows_position
                )

                await load_song(
                    music,
                    connection
                )

                await asyncio.sleep(
                    MEDIA_POLL_INTERVAL
                )

                continue

            if previous_status is not None:

                was_playing = (
                    previous_status == PLAYING
                )

                if playing != was_playing:

                    print(
                        "\nPlayback:",
                        "PLAYING"
                        if playing
                        else "PAUSED"
                    )

                    await set_anchor(
                        windows_position,
                        playing,
                        rate
                    )

            if previous_rate is not None:

                if abs(
                    rate - previous_rate
                ) > 0.01:

                    print(
                        f"\nPlayback rate changed: "
                        f"{previous_rate:.2f} "
                        f"-> "
                        f"{rate:.2f}"
                    )

                    await set_anchor(
                        windows_position,
                        playing,
                        rate
                    )

            if (
                previous_position is not None
                and playing
            ):

                position_delta = (
                    windows_position
                    - previous_position
                )

                expected_delta = (
                    MEDIA_POLL_INTERVAL
                    * rate
                )

                seek_amount = abs(
                    position_delta
                    - expected_delta
                )

                if seek_amount > SEEK_THRESHOLD:

                    print(
                        f"\nSeek detected: "
                        f"{previous_position:.2f} "
                        f"-> "
                        f"{windows_position:.2f}"
                    )

                    await set_anchor(
                        windows_position,
                        True,
                        rate
                    )

            previous_status = status

            previous_rate = rate

            previous_position = (
                windows_position
            )

            async with state.lock:

                state.windows_position = (
                    windows_position
                )

            await asyncio.sleep(
                MEDIA_POLL_INTERVAL
            )

        except Exception as e:

            print(
                f"\nMonitor error: {e}"
            )

            await asyncio.sleep(
                1.0
            )


async def lyric_engine(connection):

    while True:

        try:

            position = await get_position()

            async with state.lock:

                state.display_position = (
                    position
                )

                lyrics = state.lyrics

                lyric_times = (
                    state.lyric_times
                )

                last_index = (
                    state.last_lyric_index
                )

            if not lyrics:

                await asyncio.sleep(
                    LYRIC_UPDATE_INTERVAL
                )

                continue

            if not lyric_times:

                await asyncio.sleep(
                    LYRIC_UPDATE_INTERVAL
                )

                continue

            index = bisect.bisect_right(
                lyric_times,
                position
            ) - 1

            if index < 0:

                await asyncio.sleep(
                    LYRIC_UPDATE_INTERVAL
                )

                continue

            if index != last_index:

                lyric = lyrics[index]["text"]

                async with state.lock:

                    state.last_lyric_index = (
                        index
                    )

                print(
                    f"[{position:08.2f}] {lyric}"
                )

                if connection:

                    send(
                        connection,
                        f"LYRIC={lyric}"
                    )

            await asyncio.sleep(
                LYRIC_UPDATE_INTERVAL
            )

        except Exception as e:

            print(
                f"\nLyrics engine error: {e}"
            )

            await asyncio.sleep(
                0.1
            )


async def main():

    print("==============================")

    print("       TYMusicV2")

    print("==============================")

    print(
        "\nSearching TYMusicV2 Bluetooth..."
    )

    connection = find_and_connect()

    async with state.lock:

        state.bluetooth_connected = (
            connection is not None
        )

    if connection:

        print(
            "\nTYMusicV2 connected."
        )

        send(
            connection,
            "MODE=INFO"
        )

    else:

        print(
            "\nTYMusicV2 Bluetooth device not found."
        )

    print(
        "\nWaiting for music...\n"
    )

    manager = await get_manager()

    await asyncio.gather(

        media_monitor(
            manager,
            connection
        ),

        lyric_engine(
            connection
        ),
    )


if __name__ == "__main__":

    asyncio.run(main())