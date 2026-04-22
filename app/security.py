from datetime import datetime, timedelta, UTC
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Header
from pydantic import BaseModel
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from app.logger import logger

class TokenData(BaseModel):
    """Datos contenidos en el JWT"""
    cliente_id: str
    exp: datetime

class TokenResponse(BaseModel):
    """Respuesta de login"""
    access_token: str
    token_type: str
    expires_in: int

def crear_token_acceso(cliente_id: str) -> dict:
    """
    Crea un JWT con expiración.
    
    Args:
        cliente_id: ID del cliente a autenticar
    
    Returns:
        dict con token y metadata
    """
    ahora = datetime.now(UTC)
    expiracion = ahora + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        "cliente_id": cliente_id,
        "exp": expiracion,
        "iat": ahora
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    logger.info(f"Token creado para cliente: {cliente_id}")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600
    }

async def verificar_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Valida el JWT y retorna el cliente_id.
    
    Extrae el token del header Authorization (formato: "Bearer <token>")
    
    Args:
        authorization: Header Authorization con Bearer token
    
    Returns:
        cliente_id extraído del token
    
    Raises:
        HTTPException: Si el token es inválido, expirado o ausente
    """

    if not authorization:
        logger.warning("Request sin header Authorization")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta header Authorization",
            headers={"WWW-Authenticate": "Bearer"}
        )
    

    try:
        # Formato esperado: "Bearer <token>"
        if not authorization.startswith("Bearer "):
            logger.warning(f"Header Authorization con formato inválido: {authorization[:20]}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Formato inválido. Use: Authorization: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = authorization.split(" ")[1]
        
        if not token:
            logger.warning("Token vacío en Authorization header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no proporcionado",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except IndexError:
        logger.warning("Error parsing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de Authorization inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        cliente_id: str = payload.get("cliente_id")
        
        if cliente_id is None:
            logger.warning("Token sin campo cliente_id")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        logger.info(f"Token validado para cliente: {cliente_id}")
        return cliente_id
    
    except JWTError as e:
        logger.error(f"Error validando token JWT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado o inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en verificar_token: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autorizado"
        )

def validar_acceso_cliente(cliente_solicitado: str, cliente_autenticado: str) -> bool:
    """
    Valida que el cliente autenticado solo acceda a sus propios datos.
    
    Args:
        cliente_solicitado: ID del cliente a acceder
        cliente_autenticado: ID del cliente del token
    
    Returns:
        True si tiene acceso
    
    Raises:
        HTTPException: Si no tiene permiso
    """
    if cliente_solicitado != cliente_autenticado:
        logger.warning(
            f"Intento de acceso no autorizado: {cliente_autenticado} "
            f"intentó acceder a {cliente_solicitado}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a este recurso"
        )
    return True