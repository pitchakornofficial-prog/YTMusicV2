from core.sources.base import MusicSource


class YouTubeMusicSource(MusicSource):

    def can_handle(self, session):
        return False

    def get_name(self):
        return "YouTube Music"