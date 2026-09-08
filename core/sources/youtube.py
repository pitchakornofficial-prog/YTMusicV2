from core.sources.base import MusicSource


class YouTubeSource(MusicSource):

    def can_handle(self, session):
        return False

    def get_name(self):
        return "YouTube"