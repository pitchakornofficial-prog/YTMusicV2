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
    reconnect,
    send,
    is_connected,
    SEND_FAILURE_THRESHOLD,
)


PLAYING = 4

MEDIA_POLL_INTERVAL = 0.5
LYRIC_UPDATE_INTERVAL = 0.02

BLUETOOTH_CHECK_INTERVAL = 3.0

SEEK_THRESHOLD = 2.0


# =========================================================
# Player State
# =========================================================

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


# =========================================================
# Bluetooth State
# =========================================================

class BluetoothState:

    def __init__(self):

        self.connection = None

        # ใช้ป้องกัน connection ถูกเปลี่ยน
        # ระหว่างที่กำลังส่งข้อมูล
        self.lock = asyncio.Lock()

        self.reconnecting = False

        # จำนวน send ที่ล้มเหลวติดต่อกัน
        self.send_failures = 0


bluetooth = BluetoothState()


# =========================================================
# Player Position
# =========================================================

async def set_anchor(
    position,
    playing,
    rate
):

    async with state.lock:

        state.anchor_position = float(
            position
        )

        state.anchor_clock = (
            time.perf_counter()
        )

        state.playing = playing

        state.rate = rate or 1.0

        state.windows_position = float(
            position
        )

        state.display_position = float(
            position
        )


async def get_position():

    async with state.lock:

        anchor_position = (
            state.anchor_position
        )

        anchor_clock = (
            state.anchor_clock
        )

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


# =========================================================
# Bluetooth Connection Helpers
# =========================================================

async def get_bluetooth_connection():

    async with bluetooth.lock:

        return bluetooth.connection


async def set_bluetooth_connection(
    connection
):

    async with bluetooth.lock:

        bluetooth.connection = connection

        bluetooth.send_failures = 0

    async with state.lock:

        state.bluetooth_connected = (
            connection is not None
        )


# =========================================================
# Bluetooth Send
# =========================================================

async def bluetooth_send(message):

    # -----------------------------------------------------
    # สำคัญ:
    # lock จะครอบทั้งการตรวจ connection และการส่ง
    # ป้องกัน reconnect เข้ามาเปลี่ยน connection
    # ระหว่างที่กำลังส่งข้อมูล
    # -----------------------------------------------------

    async with bluetooth.lock:

        if bluetooth.reconnecting:

            return False

        connection = bluetooth.connection

        if not connection:

            return False

        if not is_connected(connection):

            return False

        success = await asyncio.to_thread(
            send,
            connection,
            message
        )

        # -------------------------------------------------
        # ส่งสำเร็จ
        # -------------------------------------------------

        if success:

            bluetooth.send_failures = 0

            return True

        # -------------------------------------------------
        # ส่งไม่สำเร็จ
        # -------------------------------------------------

        bluetooth.send_failures += 1

        failures = (
            bluetooth.send_failures
        )

        print(
            f"Bluetooth send failed "
            f"({failures}/"
            f"{SEND_FAILURE_THRESHOLD})"
        )

        return False


# =========================================================
# Send Current State to ESP32
# =========================================================

async def send_current_state():

    async with bluetooth.lock:

        if bluetooth.reconnecting:

            return

        connection = bluetooth.connection

        if not connection:

            return

        if not is_connected(connection):

            return

        async with state.lock:

            title = state.title
            artist = state.artist

            lyric_index = (
                state.last_lyric_index
            )

            lyrics = state.lyrics

        print(
            "\nSynchronizing ESP32..."
        )

        # -------------------------------------------------
        # MODE
        # -------------------------------------------------

        success = await asyncio.to_thread(
            send,
            connection,
            "MODE=INFO"
        )

        if not success:

            bluetooth.send_failures += 1

            return

        bluetooth.send_failures = 0

        # -------------------------------------------------
        # INFO
        # -------------------------------------------------

        if title or artist:

            success = await asyncio.to_thread(
                send,
                connection,
                f"INFO={title}|{artist}|"
            )

            if not success:

                bluetooth.send_failures += 1

                return

            bluetooth.send_failures = 0

        # -------------------------------------------------
        # Current lyric
        # -------------------------------------------------

        if (
            lyrics
            and lyric_index >= 0
            and lyric_index < len(lyrics)
        ):

            lyric = lyrics[
                lyric_index
            ]["text"]

            success = await asyncio.to_thread(
                send,
                connection,
                f"LYRIC={lyric}"
            )

            if not success:

                bluetooth.send_failures += 1

                return

            bluetooth.send_failures = 0

        print(
            "ESP32 synchronization complete."
        )


# =========================================================
# Bluetooth Auto Reconnect
# =========================================================

async def bluetooth_reconnect():

    while True:

        await asyncio.sleep(
            BLUETOOTH_CHECK_INTERVAL
        )

        try:

            # -------------------------------------------------
            # ถ้ากำลัง reconnect อยู่
            # ไม่ต้องเริ่ม reconnect ซ้ำ
            # -------------------------------------------------

            async with bluetooth.lock:

                if bluetooth.reconnecting:

                    continue

                connection = (
                    bluetooth.connection
                )

                failures = (
                    bluetooth.send_failures
                )

            # -------------------------------------------------
            # กรณีไม่มี connection
            # -------------------------------------------------

            if connection is None:

                async with bluetooth.lock:

                    if bluetooth.reconnecting:

                        continue

                    bluetooth.reconnecting = True

                async with state.lock:

                    state.bluetooth_connected = (
                        False
                    )

                print()
                print(
                    "=============================="
                )
                print(
                    "Bluetooth is disconnected."
                )
                print(
                    "Starting reconnect..."
                )
                print(
                    "=============================="
                )

                try:

                    new_connection = (
                        await asyncio.to_thread(
                            reconnect,
                            None
                        )
                    )

                    if new_connection:

                        await set_bluetooth_connection(
                            new_connection
                        )

                        print(
                            "\nBluetooth reconnect "
                            "successful."
                        )

                        await send_current_state()

                    else:

                        print(
                            "\nBluetooth reconnect "
                            "failed."
                        )

                except Exception as e:

                    print(
                        f"\nBluetooth reconnect "
                        f"error: {e}"
                    )

                finally:

                    async with bluetooth.lock:

                        bluetooth.reconnecting = (
                            False
                        )

                continue

            # -------------------------------------------------
            # สำคัญ:
            #
            # ไม่เรียก test_connection()
            #
            # ใช้ send failure เป็นตัวตรวจแทน
            # -------------------------------------------------

            if failures < SEND_FAILURE_THRESHOLD:

                continue

            # -------------------------------------------------
            # Connection ถือว่าหลุดแล้ว
            # -------------------------------------------------

            print()
            print(
                "=============================="
            )
            print(
                "Bluetooth connection lost."
            )
            print(
                "Closing old connection..."
            )
            print(
                "=============================="
            )

            async with bluetooth.lock:

                if bluetooth.reconnecting:

                    continue

                bluetooth.reconnecting = True

                old_connection = (
                    bluetooth.connection
                )

                # ตัด connection เก่าออกจากระบบทันที
                bluetooth.connection = None

                bluetooth.send_failures = 0

            async with state.lock:

                state.bluetooth_connected = (
                    False
                )

            try:

                new_connection = (
                    await asyncio.to_thread(
                        reconnect,
                        old_connection
                    )
                )

                if new_connection:

                    await set_bluetooth_connection(
                        new_connection
                    )

                    print(
                        "\nBluetooth reconnect "
                        "successful."
                    )

                    await send_current_state()

                else:

                    print(
                        "\nBluetooth reconnect "
                        "failed."
                    )

            except Exception as e:

                print(
                    f"\nBluetooth reconnect "
                    f"error: {e}"
                )

            finally:

                async with bluetooth.lock:

                    bluetooth.reconnecting = (
                        False
                    )

        except Exception as e:

            print(
                f"\nBluetooth monitor "
                f"error: {e}"
            )


# =========================================================
# Load Song
# =========================================================

async def load_song(music):

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

    playing = status == PLAYING

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

        state.anchor_clock = (
            time.perf_counter()
        )

        state.playing = playing

        state.rate = rate

        state.windows_position = position

        state.display_position = position

    print()

    print(
        "=============================="
    )

    print(
        f"Title    : {title}"
    )

    print(
        f"Artist   : {artist}"
    )

    print(
        f"Album    : {album}"
    )

    print(
        f"Duration : {duration:.2f}"
    )

    print(
        f"Source   : {source}"
    )

    print(
        f"Position : {position:.2f}"
    )

    print(
        f"Thumbnail: "
        f"{'YES' if thumbnail else 'NO'}"
    )

    print(
        "=============================="
    )

    await bluetooth_send(
        f"INFO={title}|{artist}|"
    )

    print(
        "Searching lyrics..."
    )

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

        print(
            "Lyrics not found."
        )

        return

    lyrics = parse_lrc(
        lrc
    )

    lyric_times = (
        build_lyrics_index(
            lyrics
        )
    )

    if not lyrics:

        print(
            "Lyrics empty."
        )

        return

    async with state.lock:

        state.lyrics = lyrics

        state.lyric_times = (
            lyric_times
        )

        state.last_lyric_index = -1

    print(
        f"Found {len(lyrics)} "
        f"lyric lines"
    )


# =========================================================
# Media Monitor
# =========================================================

async def media_monitor(manager):

    current_session = None

    current_song = None

    previous_status = None
    previous_rate = None
    previous_position = None

    while True:

        try:

            session = (
                await get_current_session(
                    manager
                )
            )

            # -------------------------------------------------
            # Media session changed
            # -------------------------------------------------

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
                music["rate"]
                or 1.0
            )

            playing = (
                status == PLAYING
            )

            song_id = (
                title,
                artist,
                round(
                    duration,
                    1
                )
            )

            # -------------------------------------------------
            # New song
            # -------------------------------------------------

            if song_id != current_song:

                current_song = song_id

                previous_status = status

                previous_rate = rate

                previous_position = (
                    windows_position
                )

                await load_song(
                    music
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
                    previous_status
                    == PLAYING
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

            # -------------------------------------------------
            # Playback Rate
            # -------------------------------------------------

            if previous_rate is not None:

                if abs(
                    rate
                    - previous_rate
                ) > 0.01:

                    print(
                        f"\nPlayback rate "
                        f"changed: "
                        f"{previous_rate:.2f} "
                        f"-> "
                        f"{rate:.2f}"
                    )

                    await set_anchor(
                        windows_position,
                        playing,
                        rate
                    )

            # -------------------------------------------------
            # Seek
            # -------------------------------------------------

            if (
                previous_position
                is not None
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

                if (
                    seek_amount
                    > SEEK_THRESHOLD
                ):

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


# =========================================================
# Lyrics Engine
# =========================================================

async def lyric_engine():

    while True:

        try:

            position = (
                await get_position()
            )

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

            index = (
                bisect.bisect_right(
                    lyric_times,
                    position
                )
                - 1
            )

            if index < 0:

                await asyncio.sleep(
                    LYRIC_UPDATE_INTERVAL
                )

                continue

            if index != last_index:

                lyric = lyrics[
                    index
                ]["text"]

                async with state.lock:

                    state.last_lyric_index = (
                        index
                    )

                print(
                    f"[{position:08.2f}] "
                    f"{lyric}"
                )

                await bluetooth_send(
                    f"LYRIC={lyric}"
                )

            await asyncio.sleep(
                LYRIC_UPDATE_INTERVAL
            )

        except Exception as e:

            print(
                f"\nLyrics engine "
                f"error: {e}"
            )

            await asyncio.sleep(
                0.1
            )


# =========================================================
# Main
# =========================================================

async def main():

    print(
        "=============================="
    )

    print(
        "       TYMusicV2"
    )

    print(
        "=============================="
    )

    print(
        "\nSearching TYMusicV2 Bluetooth..."
    )

    connection = (
        await asyncio.to_thread(
            find_and_connect
        )
    )

    await set_bluetooth_connection(
        connection
    )

    if connection:

        print(
            "\nTYMusicV2 connected."
        )

        await bluetooth_send(
            "MODE=INFO"
        )

    else:

        print(
            "\nTYMusicV2 Bluetooth device "
            "not found."
        )

    print(
        "\nWaiting for music...\n"
    )

    manager = await get_manager()

    await asyncio.gather(

        media_monitor(
            manager
        ),

        lyric_engine(),

        bluetooth_reconnect(),

    )


if __name__ == "__main__":

    asyncio.run(main())