from app.database import db
from app.logger import logger
from fastapi import HTTPException, status

async def obtener_fondo(id_fondo: str):
    """
    Obtiene un fondo por su ID.
    
    Args:
        id_fondo (str): ID del fondo.
    
    Returns:
        dict: Documento del fondo o None si no existe.
    
    Raises:
        HTTPException: Si hay error en BD.
    """
    logger.debug(f"Buscando fondo: {id_fondo}")
    
    try:
        # Validación de entrada
        if not id_fondo or not isinstance(id_fondo, str):
            logger.warning(f"ID de fondo inválido: {id_fondo}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de fondo debe ser una cadena no vacía"
            )
        
        # Convertir a int si es necesario
        try:
            id_fondo_int = int(id_fondo)
        except ValueError:
            logger.warning(f"ID de fondo no es numérico: {id_fondo}")
            # Intentar buscar como string directamente
            id_fondo_int = id_fondo
        
        # Consultar fondo
        fondo = await db.fondos.find_one({"_id": id_fondo_int})
        
        if fondo:
            logger.debug(f"Fondo encontrado: {id_fondo}")
        else:
            logger.debug(f"Fondo no encontrado: {id_fondo}")
        
        return fondo
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo fondo {id_fondo}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar fondo"
        )

async def actualizar_saldo_cliente(cliente_id: str, nuevo_saldo: float):
    """
    Actualiza el saldo de un cliente.
    
    Args:
        cliente_id (str): ID del cliente.
        nuevo_saldo (float): Nuevo saldo a establecer.
    
    Returns:
        dict: Resultado de la actualización.
    
    Raises:
        HTTPException: Si hay error en BD.
    """
    logger.info(f"Actualizando saldo del cliente {cliente_id}: nuevo_saldo={nuevo_saldo}")
    
    try:
        # Validación de entrada
        if not cliente_id or not isinstance(cliente_id, str):
            logger.warning(f"ID de cliente inválido: {cliente_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cliente debe ser una cadena no vacía"
            )
        
        if nuevo_saldo < 0:
            logger.warning(f"Saldo negativo rechazado para {cliente_id}: {nuevo_saldo}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Saldo no puede ser negativo"
            )
        
        # Obtener saldo anterior para auditoría
        cliente = await db.clientes.find_one({"_id": cliente_id})
        if not cliente:
            logger.error(f"Cliente no encontrado al actualizar saldo: {cliente_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )
        
        saldo_anterior = float(cliente.get("saldo", 0))
        
        # Actualizar saldo
        resultado = await db.clientes.update_one(
            {"_id": cliente_id},
            {"$set": {"saldo": nuevo_saldo}}
        )
        
        # Validar que se actualizó
        if resultado.matched_count == 0:
            logger.error(f"Cliente no encontrado en actualización: {cliente_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )
        
        if resultado.modified_count == 0:
            logger.warning(f"Saldo no fue modificado para {cliente_id}")
        
        logger.info(
            f"Saldo actualizado para {cliente_id}: "
            f"{saldo_anterior} -> {nuevo_saldo} "
            f"(diferencia: {nuevo_saldo - saldo_anterior:+.2f})"
        )
        
        return {
            "cliente_id": cliente_id,
            "saldo_anterior": saldo_anterior,
            "saldo_nuevo": nuevo_saldo,
            "diferencia": nuevo_saldo - saldo_anterior,
            "modificado": resultado.modified_count > 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error actualizando saldo de {cliente_id}: {str(e)}", 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar saldo"
        )

async def obtener_transacciones_cliente_fondo(id_cliente: str, id_fondo: str):
    """
    Obtiene todas las transacciones de un cliente para un fondo específico.
    
    Args:
        id_cliente (str): ID del cliente.
        id_fondo (str): ID del fondo.
    
    Returns:
        list: Lista de documentos de transacciones.
    
    Raises:
        HTTPException: Si hay error en BD.
    """
    logger.info(f"Obteniendo transacciones: cliente={id_cliente}, fondo={id_fondo}")
    
    try:
        # Validación de entrada
        if not id_cliente or not isinstance(id_cliente, str):
            logger.warning(f"ID de cliente inválido: {id_cliente}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cliente debe ser una cadena no vacía"
            )
        
        if not id_fondo or not isinstance(id_fondo, str):
            logger.warning(f"ID de fondo inválido: {id_fondo}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de fondo debe ser una cadena no vacía"
            )
        
        # Consultar transacciones
        cursor = db.transacciones.find({
            "id_cliente": id_cliente,
            "id_fondo": id_fondo
        }).sort("fecha", -1)
        
        transacciones = [t async for t in cursor]
        
        logger.info(
            f"Se recuperaron {len(transacciones)} transacciones para "
            f"cliente={id_cliente}, fondo={id_fondo}"
        )
        
        return transacciones
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error obteniendo transacciones de {id_cliente} en {id_fondo}: {str(e)}", 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar transacciones"
        )