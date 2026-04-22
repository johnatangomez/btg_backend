from fastapi import HTTPException, status
from bson import json_util
import json
from app.repositories.fondos_repo import obtener_transacciones_cliente_fondo
from app.crud import obtener_cliente
from app.database import db
from app.logger import logger

async def historial_cliente_fondo(id_cliente: str, id_fondo: str):
    """
    Obtiene el historial de transacciones de un cliente para un fondo 
    específico, junto con el saldo invertido actual y el saldo actual 
    del cliente.
    
    Args:
        id_cliente (str): El ID del cliente.
        id_fondo (str): El ID del fondo.
    
    Returns:
        dict: Historial de transacciones, saldo invertido actual 
              y saldo actual del cliente.
    
    Raises:
        HTTPException: Si no hay transacciones o cliente no existe.
    """
    logger.info(f"Consultando historial: cliente={id_cliente}, fondo={id_fondo}")
    
    try:
        if not id_cliente or not isinstance(id_cliente, str):
            logger.warning("Cliente ID inválido")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cliente ID debe ser una cadena no vacía"
            )
        
        if not id_fondo or not isinstance(id_fondo, str):
            logger.warning("Fondo ID inválido")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fondo ID debe ser una cadena no vacía"
            )
        
        try:
            cliente = await obtener_cliente(id_cliente)
            if not cliente:
                logger.error(f"Cliente no encontrado: {id_cliente}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente no encontrado"
                )
            logger.info(f"Cliente encontrado: {id_cliente}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo cliente: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al consultar cliente"
            )

        try:
            transacciones = await obtener_transacciones_cliente_fondo(id_cliente, id_fondo)
            logger.info(f"Se recuperaron {len(transacciones)} transacciones")
        except Exception as e:
            logger.error(f"Error obteniendo transacciones: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al consultar transacciones"
            )
        
        # Validar que hay transacciones
        if not transacciones:
            logger.warning(f"Sin transacciones: cliente={id_cliente}, fondo={id_fondo}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay transacciones para este cliente y fondo"
            )
        
        # Calcular saldo invertido
        try:
            aperturas = sum(
                float(t.get("monto", 0)) for t in transacciones 
                if t.get("tipo") == "apertura"
            )
            cancelaciones = sum(
                float(t.get("monto", 0)) for t in transacciones 
                if t.get("tipo") == "cancelación"
            )
            saldo_invertido = aperturas - cancelaciones
            
            logger.info(
                f"Cálculo saldo invertido: "
                f"aperturas={aperturas}, cancelaciones={cancelaciones}, "
                f"saldo_invertido={saldo_invertido}"
            )
        except Exception as e:
            logger.error(f"Error calculando saldo invertido: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al calcular saldo invertido"
            )
        
        # Validar consistencia de saldos
        if saldo_invertido < 0:
            logger.warning(
                f"ADVERTENCIA: Saldo invertido negativo: "
                f"cliente={id_cliente}, fondo={id_fondo}, saldo={saldo_invertido}"
            )
        
        try:
            saldo_actual = float(cliente.get("saldo", 0))
            logger.info(f"Saldo actual del cliente: {saldo_actual}")
        except Exception as e:
            logger.error(f"Error obteniendo saldo del cliente: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener saldo del cliente"
            )
        

        try:
            respuesta = json.loads(json_util.dumps({
                "id_cliente": id_cliente,
                "id_fondo": id_fondo,
                "saldo_invertido_actual": saldo_invertido,
                "aperturas_totales": aperturas,
                "cancelaciones_totales": cancelaciones,
                "saldo_actual_cliente": saldo_actual,
                "cantidad_transacciones": len(transacciones),
                "historial": transacciones
            }))
            
            logger.info(f"Historial serializado exitosamente")
            return respuesta
        except Exception as e:
            logger.error(f"Error serializando respuesta: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al serializar respuesta"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error inesperado en historial_cliente_fondo: {str(e)}", 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )