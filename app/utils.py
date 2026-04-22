import bcrypt
from app.logger import logger

def hashear_contraseña(contraseña: str) -> str:
    """
    Hashea una contraseña usando bcrypt.
    
    Args:
        contraseña: Contraseña en texto plano
    
    Returns:
        Contraseña hasheada
    """
    logger.debug("Hasheando contraseña")
    try:
        salt = bcrypt.gensalt(rounds=12)  # 12 rondas para mayor seguridad
        hash_contraseña = bcrypt.hashpw(contraseña.encode('utf-8'), salt)
        return hash_contraseña.decode('utf-8')
    except Exception as e:
        logger.error(f"Error hasheando contraseña: {str(e)}")
        raise

def verificar_contraseña(contraseña_plain: str, hash_contraseña: str) -> bool:
    """
    Verifica una contraseña contra su hash.
    
    Args:
        contraseña_plain: Contraseña en texto plano
        hash_contraseña: Hash de la contraseña almacenada
    
    Returns:
        True si coinciden, False si no
    """
    logger.debug("Verificando contraseña")
    try:
        return bcrypt.checkpw(
            contraseña_plain.encode('utf-8'),
            hash_contraseña.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Error verificando contraseña: {str(e)}")
        return False