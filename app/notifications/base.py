from abc import ABC, abstractmethod

class NotificationStrategy(ABC):
    @abstractmethod
    async def send(self, destinatario: str, mensaje: str, datos: dict = None, archivos_adjuntos=None):
        pass
