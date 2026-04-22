import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from jinja2 import Template
from app.notifications.base import NotificationStrategy

load_dotenv()  

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def cargar_plantilla(nombre="respuesta.html"):
    with open(os.path.join(BASE_DIR, "templates", nombre), "r", encoding="utf-8") as f:
        return Template(f.read())

class GmailSMTPNotification(NotificationStrategy): #cree el docstring
    """Estrategia de notificación que utiliza el servicio SMTP de Gmail para enviar correos electrónicos. Renderiza una plantilla HTML para el cuerpo del mensaje, permitiendo personalización con datos dinámicos.
    """
    async def send(self, destinatario: str, mensaje: str, datos: dict = None, archivos_adjuntos=None):
        # Renderizamos la plantilla HTML con el nombre del fondo
        plantilla = cargar_plantilla()
        cuerpo_html = plantilla.render(datos or {"mensaje": mensaje})

        msg = MIMEText(cuerpo_html, "html")
        msg["Subject"] = "Notificación de Suscripción"
        msg["From"] = os.getenv("SENDER_EMAIL")
        msg["To"] = destinatario

        # Conexión vía SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)