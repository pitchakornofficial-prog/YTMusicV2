from core.music import detect_source


class FakeSession:
    def __init__(self, app_id):
        self.source_app_user_model_id = app_id


def test_spotify():
    session = FakeSession("Spotify.exe")

    result = detect_source(session)

    assert result == "Spotify"


def test_spotify_case_insensitive():
    session = FakeSession("SPOTIFY.EXE")

    result = detect_source(session)

    assert result == "Spotify"


def test_unknown():
    session = FakeSession("Chrome")

    result = detect_source(session)

    assert result == "Unknown"


def test_empty_app_id():
    session = FakeSession("")

    result = detect_source(session)

    assert result == "Unknown"


def test_none_app_id():
    session = FakeSession(None)

    result = detect_source(session)

    assert result == "Unknown"


print("All music source tests passed.")