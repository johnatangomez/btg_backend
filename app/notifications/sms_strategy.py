from twilio.rest import Client
from app.notifications.base import NotificationStrategy

class SMSNotification(NotificationStrategy):
    def __init__(self):
        self.client = Client("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN")

    async def send(self, destinatario: str, mensaje: str):
        self.client.messages.create(
            body=mensaje,
            from_="+1234567890",  # número de Twilio
            to=destinatario
        )
