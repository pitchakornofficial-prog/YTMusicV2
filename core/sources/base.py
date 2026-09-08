from abc import ABC, abstractmethod


class MusicSource(ABC):

    @abstractmethod
    def can_handle(self, session):
        """
        ตรวจสอบว่า source นี้รองรับ media session หรือไม่
        """
        pass

    @abstractmethod
    def get_name(self):
        """
        คืนชื่อ source
        """
        pass