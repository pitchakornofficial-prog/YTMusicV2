from core.sources.base import MusicSource


class SpotifySource(MusicSource):

    def can_handle(self, session):
        app_id = session.source_app_user_model_id

        if not app_id:
            return False

        return "spotify.exe" in app_id.lower()

    def get_name(self):
        return "Spotify"