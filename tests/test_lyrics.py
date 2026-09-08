from core.lyrics import (
    parse_lrc,
    build_lyrics_index,
    get_current_lyric,
)


def test_parse_lrc():
    lrc = """[00:10.00]First line
[00:20.50]Second line
[01:05.25]Third line
"""

    lyrics = parse_lrc(lrc)

    assert len(lyrics) == 3

    assert lyrics[0]["time"] == 10.0
    assert lyrics[0]["text"] == "First line"

    assert lyrics[1]["time"] == 20.5
    assert lyrics[1]["text"] == "Second line"

    assert lyrics[2]["time"] == 65.25
    assert lyrics[2]["text"] == "Third line"


def test_multiple_timestamps():
    lrc = "[00:10.00][00:20.00]Same lyric"

    lyrics = parse_lrc(lrc)

    assert len(lyrics) == 2

    assert lyrics[0]["time"] == 10.0
    assert lyrics[0]["text"] == "Same lyric"

    assert lyrics[1]["time"] == 20.0
    assert lyrics[1]["text"] == "Same lyric"


def test_sorting():
    lrc = """[00:30.00]Third
[00:10.00]First
[00:20.00]Second
"""

    lyrics = parse_lrc(lrc)

    assert lyrics[0]["text"] == "First"
    assert lyrics[1]["text"] == "Second"
    assert lyrics[2]["text"] == "Third"


def test_ignore_invalid_lines():
    lrc = """[00:10.00]Valid
This is not a lyric
[00:20.00]
[00:30.00]Another valid
"""

    lyrics = parse_lrc(lrc)

    assert len(lyrics) == 2

    assert lyrics[0]["text"] == "Valid"
    assert lyrics[1]["text"] == "Another valid"


def test_build_lyrics_index():
    lyrics = [
        {"time": 10.0, "text": "First"},
        {"time": 20.5, "text": "Second"},
        {"time": 30.0, "text": "Third"},
    ]

    times = build_lyrics_index(lyrics)

    assert times == [10.0, 20.5, 30.0]


def test_current_lyric():
    lyrics = [
        {"time": 10.0, "text": "First"},
        {"time": 20.0, "text": "Second"},
        {"time": 30.0, "text": "Third"},
    ]

    times = build_lyrics_index(lyrics)

    assert get_current_lyric(
        lyrics,
        times,
        5.0
    ) is None

    assert get_current_lyric(
        lyrics,
        times,
        10.0
    ) == "First"

    assert get_current_lyric(
        lyrics,
        times,
        15.0
    ) == "First"

    assert get_current_lyric(
        lyrics,
        times,
        20.0
    ) == "Second"

    assert get_current_lyric(
        lyrics,
        times,
        29.9
    ) == "Second"

    assert get_current_lyric(
        lyrics,
        times,
        30.0
    ) == "Third"


print("All lyrics tests passed.")