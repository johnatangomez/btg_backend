from fastapi import APIRouter, HTTPException, Depends, status
from app.models import Transaccion, LoginRequest
from app.services.suscribir_service import suscribir_fondo
from app.services.cancelar_service import cancelar_fondo
from app.services.historial_cliente_fondo_service import historial_cliente_fondo
from app.services.historial_cliente_service import historial_por_cliente
from app.security import verificar_token, validar_acceso_cliente, crear_token_acceso, TokenResponse
from app.database import db
from app.logger import logger
from bson import json_util
from app.utils import verificar_contraseña
import json

router = APIRouter(prefix="/fondos", tags=["Fondos"])

@router.post("/login", response_model=TokenResponse)
async def login(request_login: LoginRequest):
    """
    Autentica un cliente y retorna JWT.
    
    Args:
        request_login: LoginRequest con cliente_id y password
    
    Returns:
        Token JWT para usar en requests posteriores
        
    Raises:
        HTTPException: Si credenciales son inválidas
    """
    cliente_id = request_login.cliente_id
    password = request_login.password
    
    logger.info(f"Intento de login para cliente: {cliente_id}")
    
    try:
        # Validar que no esté vacío
        if not cliente_id or not password:
            logger.warning(f"Login con campos vacíos")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cliente_id y password son requeridos"
            )
        
        # Buscar cliente en BD
        try:
            cliente = await db.clientes.find_one({"_id": cliente_id})
        except Exception as e:
            logger.error(f"Error buscando cliente: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al consultar usuario"
            )
        
        if not cliente:
            logger.warning(f"Login fallido: cliente no encontrado - {cliente_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Verificar que tenga contraseña hasheada
        password_hash = cliente.get("password_hash")
        if not password_hash:
            logger.error(f"Cliente sin password_hash: {cliente_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Validar que está activo
        if not cliente.get("activo", True):
            logger.warning(f"Login fallido: cliente inactivo - {cliente_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo"
            )
        
        # Verificar contraseña
        if not verificar_contraseña(password, password_hash):
            logger.warning(f"Login fallido: contraseña incorrecta - {cliente_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Crear token
        token_data = crear_token_acceso(cliente_id)
        logger.info(f"Login exitoso para cliente: {cliente_id}")
        
        return token_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el servidor"
        )

@router.post("/suscribir")
async def suscribir(
    transaccion: Transaccion,
    cliente_autenticado: str = Depends(verificar_token)
):
    """
    Suscribe un cliente a un fondo.
    
    Args:
        transaccion: Datos de suscripción
        cliente_autenticado: Cliente del JWT (inyectado automáticamente)
    """
    validar_acceso_cliente(transaccion.id_cliente, cliente_autenticado)
    
    logger.info(f"Iniciando suscripción - Cliente: {transaccion.id_cliente}, Fondo: {transaccion.id_fondo}, Monto: {transaccion.monto}")
    
    try:
        result = await suscribir_fondo(transaccion)
        logger.info(f"Suscripción exitosa: {result}")
        return result
    except HTTPException as e:
        logger.warning(f"Error en suscripción: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en suscribir: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/cancelar")
async def cancelar(
    cliente_id: str,
    fondo_id: str,
    cliente_autenticado: str = Depends(verificar_token)
):
    """
    Cancela completamente la inversión de un cliente en un fondo.
    
    Por regla de negocio: Retorna el VALOR COMPLETO de la vinculación.
    
    No requiere indicar monto - se cancela TODO lo invertido en ese fondo.
    
    Args:
        cliente_id: ID del cliente (en query parameter)
        fondo_id: ID del fondo (en query parameter)
        cliente_autenticado: Cliente del JWT (validación automática)
    
    Returns:
        Dict con mensaje de éxito, monto devuelto y nuevo saldo
        
    Example:
        POST /fondos/cancelar?cliente_id=cliente001&fondo_id=fondo_1
        Headers: Authorization: Bearer <token>
    """
    # Validar que el usuario opera solo sus datos
    validar_acceso_cliente(cliente_id, cliente_autenticado)
    
    logger.info(f"Endpoint cancelar - Cliente: {cliente_id}, Fondo: {fondo_id}")
    
    try:
        result = await cancelar_fondo(cliente_id, fondo_id)
        logger.info(f"Cancelación exitosa: {result}")
        return result
    except HTTPException as e:
        logger.warning(f"Error en cancelación: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en cancelar: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.get("/historial/{id_cliente}/{id_fondo}")
async def historial_fondo(
    id_cliente: str,
    id_fondo: str,
    cliente_autenticado: str = Depends(verificar_token)
):
    """
    Obtiene historial de transacciones de un cliente en un fondo específico.
    """
    validar_acceso_cliente(id_cliente, cliente_autenticado)
    
    logger.info(f"Consultando historial - Cliente: {id_cliente}, Fondo: {id_fondo}")
    
    try:
        return await historial_cliente_fondo(id_cliente, id_fondo)
    except Exception as e:
        logger.error(f"Error en historial_fondo: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/historial/{id_cliente}")
async def historial_cliente(
    id_cliente: str,
    cliente_autenticado: str = Depends(verificar_token)
):
    """
    Obtiene historial completo de transacciones de un cliente.
    """
    validar_acceso_cliente(id_cliente, cliente_autenticado)
    
    logger.info(f"Consultando historial completo - Cliente: {id_cliente}")
    
    try:
        return await historial_por_cliente(id_cliente)
    except Exception as e:
        logger.error(f"Error en historial_cliente: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)