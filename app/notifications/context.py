from app.notifications.base import NotificationStrategy

class NotificationContext:
    def __init__(self, strategy: NotificationStrategy):
        self.strategy = strategy

    async def notify(self, destinatario: str, mensaje: str, datos: dict = None, archivos_adjuntos=None):
        await self.strategy.send(destinatario, mensaje, datos, archivos_adjuntos)

