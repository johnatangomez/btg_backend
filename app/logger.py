import logging
import logging.handlers
from app.config import LOG_LEVEL, LOG_FILE
from datetime import datetime

# Crear logger
logger = logging.getLogger("btg_api")
logger.setLevel(LOG_LEVEL)

# Handler para archivo
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE,
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Handler para consola
console_handler = logging.StreamHandler()

# Formato con timestamp
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

def log_transaccion(evento: str, cliente_id: str, fondo_id: str = None, monto: float = None, estado: str = "success", detalles: dict = None):
    """
    Registra transacciones financieras para auditoría.
    
    Args:
        evento: Tipo de evento (suscripcion, cancelacion, etc)
        cliente_id: ID del cliente
        fondo_id: ID del fondo
        monto: Monto de la transacción
        estado: success, error, etc
        detalles: Información adicional
    """
    extra = {
        "evento": evento,
        "cliente_id": cliente_id,
        "fondo_id": fondo_id,
        "monto": monto,
        "estado": estado,
        "detalles": detalles
    }
    logger.info(f"TRANSACCION: {evento} | Cliente: {cliente_id} | Fondo: {fondo_id} | Monto: {monto} | Estado: {estado}")
    if detalles:
        logger.info(f"Detalles: {detalles}")