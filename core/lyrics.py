import requests
import re
from bisect import bisect_right


LRCLIB_URL = "https://lrclib.net/api/search"


def search_lyrics(title, artist, duration=None):

    try:

        response = requests.get(
            LRCLIB_URL,
            params={
                "track_name": title,
                "artist_name": artist
            },
            timeout=10
        )

        response.raise_for_status()

        results = response.json()

        if not results:
            return None

        candidates = []

        for result in results:

            synced = result.get("syncedLyrics")

            if not synced:
                continue

            result_duration = result.get("duration")

            if (
                duration is not None
                and result_duration is not None
            ):

                difference = abs(
                    float(result_duration)
                    - float(duration)
                )

            else:

                difference = 999999

            candidates.append(
                (
                    difference,
                    synced
                )
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: x[0]
        )

        print("Lyrics found!")

        return candidates[0][1]

    except Exception as e:

        print(f"Lyrics error: {e}")

        return None


def parse_lrc(lrc):

    lyrics = []

    pattern = re.compile(
        r"\[(\d+):(\d+(?:\.\d+)?)\]"
    )

    for line in lrc.splitlines():

        matches = pattern.findall(line)

        if not matches:
            continue

        text = pattern.sub(
            "",
            line
        ).strip()

        if not text:
            continue

        for minutes, seconds in matches:

            timestamp = (
                int(minutes) * 60
                + float(seconds)
            )

            lyrics.append({
                "time": timestamp,
                "text": text
            })

    lyrics.sort(
        key=lambda x: x["time"]
    )

    return lyrics


def build_lyrics_index(lyrics):

    return [
        lyric["time"]
        for lyric in lyrics
    ]


def get_current_lyric(
    lyrics,
    lyric_times,
    position
):

    if not lyrics:
        return None

    index = bisect_right(
        lyric_times,
        position
    ) - 1

    if index < 0:
        return None

    return lyrics[index]["text"]