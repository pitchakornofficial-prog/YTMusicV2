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
        self.duration = 0.0

        self.lyrics = []
        self.lyric_times = []

        self.anchor_position = 0.0
        self.anchor_clock = time.perf_counter()

        self.playing = False
        self.rate = 1.0

        self.windows_position = 0.0
        self.last_lyric_index = -1

        self.lock = asyncio.Lock()


state = PlayerState()


# =========================================================
# Position / Clock
# =========================================================

async def set_anchor(position, playing, rate):
    async with state.lock:
        state.anchor_position = float(position)
        state.anchor_clock = time.perf_counter()
        state.playing = playing
        state.rate = rate or 1.0
        state.windows_position = float(position)


async def get_position():
    async with state.lock:
        anchor_position = state.anchor_position
        anchor_clock = state.anchor_clock
        playing = state.playing
        rate = state.rate
        duration = state.duration

    if not playing:
        return anchor_position

    elapsed = time.perf_counter() - anchor_clock

    position = anchor_position + elapsed * rate

    if duration > 0:
        position = min(position, duration)

    return position


# =========================================================
# Load Song
# =========================================================

async def load_song(music, connection):
    title = music["title"]
    artist = music["artist"]
    duration = music["duration"]
    position = music["position"]

    status = music["status"]
    rate = music["rate"] or 1.0

    playing = status == PLAYING

    async with state.lock:
        state.title = title
        state.artist = artist
        state.duration = duration

        state.lyrics = []
        state.lyric_times = []

        state.last_lyric_index = -1

        state.anchor_position = position
        state.anchor_clock = time.perf_counter()

        state.playing = playing
        state.rate = rate

        state.windows_position = position

    print()
    print("==============================")
    print(f"Title    : {title}")
    print(f"Artist   : {artist}")
    print(f"Duration : {duration:.2f}")
    print(f"Position : {position:.2f}")
    print("==============================")

    # Send song information to ESP32
    if connection:
        send(connection, f"INFO={title}|{artist}|")

    # Search lyrics
    print("Searching lyrics...")

    try:
        lrc = await asyncio.to_thread(
            search_lyrics,
            title,
            artist,
            duration
        )

    except Exception as e:
        print(f"Lyrics search error: {e}")
        return

    if not lrc:
        print("Lyrics not found.")
        return

    # Parse LRC
    lyrics = parse_lrc(lrc)
    lyric_times = build_lyrics_index(lyrics)

    if not lyrics:
        print("Lyrics empty.")
        return

    async with state.lock:
        state.lyrics = lyrics
        state.lyric_times = lyric_times
        state.last_lyric_index = -1

    print(f"Found {len(lyrics)} lyric lines")


# =========================================================
# Media Monitor
# =========================================================

async def media_monitor(manager, connection):
    current_session = None
    current_song = None

    previous_status = None
    previous_rate = None
    previous_position = None

    while True:
        try:
            session = await get_current_session(manager)

            # -------------------------------------------------
            # Media session changed
            # -------------------------------------------------

            if session != current_session:
                current_session = session

                current_song = None

                previous_status = None
                previous_rate = None
                previous_position = None

                print("\nMedia session changed.")

                if session is None:
                    await asyncio.sleep(MEDIA_POLL_INTERVAL)
                    continue

            if session is None:
                await asyncio.sleep(MEDIA_POLL_INTERVAL)
                continue

            # -------------------------------------------------
            # Read media information
            # -------------------------------------------------

            music = await get_music_info(session)

            title = music["title"]
            artist = music["artist"]
            duration = music["duration"]

            windows_position = float(music["position"])

            status = music["status"]
            rate = music["rate"] or 1.0

            playing = status == PLAYING

            # -------------------------------------------------
            # Song ID
            # -------------------------------------------------

            song_id = (
                title,
                artist,
                round(duration, 1)
            )

            # -------------------------------------------------
            # New song
            # -------------------------------------------------

            if song_id != current_song:

                current_song = song_id

                previous_status = status
                previous_rate = rate
                previous_position = windows_position

                await load_song(
                    music,
                    connection
                )

                await asyncio.sleep(
                    MEDIA_POLL_INTERVAL
                )

                continue

            # -------------------------------------------------
            # Play / Pause
            # -------------------------------------------------

            if previous_status is not None:

                was_playing = (
                    previous_status == PLAYING
                )

                if playing != was_playing:

                    print(
                        "\nPlayback:",
                        "PLAYING" if playing else "PAUSED"
                    )

                    await set_anchor(
                        windows_position,
                        playing,
                        rate
                    )

            # -------------------------------------------------
            # Playback rate changed
            # -------------------------------------------------

            if previous_rate is not None:

                if abs(rate - previous_rate) > 0.01:

                    print(
                        f"\nPlayback rate changed: "
                        f"{previous_rate:.2f} -> {rate:.2f}"
                    )

                    await set_anchor(
                        windows_position,
                        playing,
                        rate
                    )

            # -------------------------------------------------
            # Seek detection
            #
            # IMPORTANT:
            # This compares Windows positions against the
            # previous Windows position.
            #
            # It does NOT compare Windows position against
            # our local clock.
            #
            # This prevents the repeated seek loop.
            # -------------------------------------------------

            if previous_position is not None and playing:

                position_delta = (
                    windows_position
                    - previous_position
                )

                expected_delta = (
                    MEDIA_POLL_INTERVAL * rate
                )

                seek_amount = abs(
                    position_delta - expected_delta
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

            # -------------------------------------------------
            # Save previous values
            # -------------------------------------------------

            previous_status = status
            previous_rate = rate
            previous_position = windows_position

            async with state.lock:
                state.windows_position = windows_position

            await asyncio.sleep(
                MEDIA_POLL_INTERVAL
            )

        except Exception as e:

            print(
                f"\nMonitor error: {e}"
            )

            await asyncio.sleep(1.0)


# =========================================================
# Lyrics Engine
# =========================================================

async def lyric_engine(connection):

    while True:

        try:

            position = await get_position()

            async with state.lock:
                lyrics = state.lyrics
                lyric_times = state.lyric_times
                last_index = state.last_lyric_index

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

            # -------------------------------------------------
            # Find current lyric
            # -------------------------------------------------

            index = bisect.bisect_right(
                lyric_times,
                position
            ) - 1

            if index < 0:

                await asyncio.sleep(
                    LYRIC_UPDATE_INTERVAL
                )

                continue

            # -------------------------------------------------
            # New lyric line
            # -------------------------------------------------

            if index != last_index:

                lyric = lyrics[index]["text"]

                async with state.lock:
                    state.last_lyric_index = index

                print(
                    f"[{position:08.2f}] {lyric}"
                )

                # Send lyric to ESP32
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

            await asyncio.sleep(0.1)


# =========================================================
# Main
# =========================================================

async def main():

    print("==============================")
    print("       TYMusicV2")
    print("==============================")

    # -------------------------------------------------------
    # Bluetooth Auto Detect
    # -------------------------------------------------------

    print(
        "\nSearching TYMusicV2 Bluetooth..."
    )

    connection = find_and_connect()

    if connection:

        print(
            "\nTYMusicV2 connected."
        )

        # Set initial display mode
        send(
            connection,
            "MODE=INFO"
        )

    else:

        print(
            "\nTYMusicV2 Bluetooth device not found."
        )

    # -------------------------------------------------------
    # Start Music Detection
    # -------------------------------------------------------

    print(
        "\nWaiting for music...\n"
    )

    manager = await get_manager()

    # -------------------------------------------------------
    # Run Media Monitor + Lyrics Engine
    # -------------------------------------------------------

    await asyncio.gather(

        media_monitor(
            manager,
            connection
        ),

        lyric_engine(
            connection
        ),
    )


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":

    asyncio.run(main())