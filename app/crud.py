from app.database import db
from app.models import Cliente, Fondo, Transaccion
from app.logger import logger
from fastapi import HTTPException, status

async def crear_cliente(cliente: Cliente):
    """
    Crea un nuevo cliente en la base de datos.
    
    Args:
        cliente (Cliente): Objeto Cliente con datos validados.
    
    Returns:
        dict: Resultado de la inserción.
    
    Raises:
        HTTPException: Si hay error en BD.
    """
    cliente_id = cliente.id
    logger.info(f"Creando cliente: {cliente_id}")
    
    try:
        # Verificar que cliente no exista
        cliente_existente = await db.clientes.find_one({"_id": cliente_id})
        if cliente_existente:
            logger.warning(f"Cliente ya existe: {cliente_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cliente {cliente_id} ya existe"
            )
        
        # Insertar cliente
        resultado = await db.clientes.insert_one(cliente.model_dump())
        logger.info(f"Cliente creado exitosamente: {cliente_id} (ObjectId: {resultado.inserted_id})")
        
        return {
            "cliente_id": cliente_id,
            "mensaje": "Cliente creado exitosamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando cliente {cliente_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear cliente: {str(e)}"
        )

async def obtener_cliente(id_cliente: str):
    """
    Obtiene un cliente por su ID.
    
    Args:
        id_cliente (str): ID del cliente.
    
    Returns:
        dict: Documento del cliente o None si no existe.
    
    Raises:
        HTTPException: Si hay error en BD.
    """
    logger.debug(f"Buscando cliente: {id_cliente}")
    
    try:
        # Validación de entrada
        if not id_cliente or not isinstance(id_cliente, str):
            logger.warning(f"ID de cliente inválido: {id_cliente}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cliente debe ser una cadena no vacía"
            )
        
        # Consultar BD
        cliente = await db.clientes.find_one({"_id": id_cliente})
        
        if cliente:
            logger.debug(f"Cliente encontrado: {id_cliente}")
        else:
            logger.debug(f"Cliente no encontrado: {id_cliente}")
        
        return cliente
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo cliente {id_cliente}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar cliente"
        )

async def crear_transaccion(transaccion: Transaccion):
    """
    Crea un registro de transacción en la base de datos.
    
    Args:
        transaccion (Transaccion): Objeto Transaccion con datos validados.
    
    Returns:
        dict: ID de la transacción creada.
    
    Raises:
        HTTPException: Si hay error en BD.
    """
    transaccion_id = transaccion.id
    cliente_id = transaccion.id_cliente
    fondo_id = transaccion.id_fondo
    monto = transaccion.monto
    tipo = transaccion.tipo
    
    logger.info(
        f"Creando transacción: "
        f"id={transaccion_id}, cliente={cliente_id}, "
        f"fondo={fondo_id}, tipo={tipo}, monto={monto}"
    )
    
    try:
        # Validación de entrada
        if not transaccion_id or not cliente_id or not fondo_id:
            logger.warning("Transacción con campos requeridos vacíos")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transacción requiere id, id_cliente e id_fondo"
            )
        
        if monto <= 0:
            logger.warning(f"Monto inválido: {monto}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monto debe ser positivo"
            )
        
        # Insertar transacción
        resultado = await db.transacciones.insert_one(transaccion.model_dump())
        logger.info(
            f"Transacción creada exitosamente: {transaccion_id} "
            f"(ObjectId: {resultado.inserted_id})"
        )
        
        return {
            "transaccion_id": transaccion_id,
            "mensaje": "Transacción registrada exitosamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error creando transacción {transaccion_id}: {str(e)}", 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al registrar transacción"
        )

async def obtener_transacciones(id_cliente: str):
    """
    Obtiene todas las transacciones de un cliente.
    
    Args:
        id_cliente (str): ID del cliente.
    
    Returns:
        list: Lista de documentos de transacciones.
    
    Raises:
        HTTPException: Si hay error en BD.
    """
    logger.info(f"Obteniendo transacciones para cliente: {id_cliente}")
    
    try:
        # Validación de entrada
        if not id_cliente or not isinstance(id_cliente, str):
            logger.warning(f"ID de cliente inválido: {id_cliente}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cliente debe ser una cadena no vacía"
            )
        
        # Consultar transacciones
        cursor = db.transacciones.find({"id_cliente": id_cliente}).sort("fecha", -1)
        transacciones = [t async for t in cursor]
        
        logger.info(f"Se recuperaron {len(transacciones)} transacciones para {id_cliente}")
        
        return transacciones
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error obteniendo transacciones de {id_cliente}: {str(e)}", 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar transacciones"
        )