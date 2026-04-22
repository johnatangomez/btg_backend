from fastapi import HTTPException, status
from app.models import TipoTransaccion
from app.repositories.fondos_repo import obtener_fondo, actualizar_saldo_cliente, obtener_transacciones_cliente_fondo
from app.crud import obtener_cliente, crear_transaccion
from app.logger import logger, log_transaccion

async def cancelar_fondo(cliente_id: str, fondo_id: str):
    """
    Cancela completamente la inversión de un cliente en un fondo.
    
    Por regla de negocio: Al cancelar una suscripción, se retorna 
    el VALOR COMPLETO de vinculación al cliente (todo lo invertido).
    
    Args:
        cliente_id (str): ID del cliente
        fondo_id (str): ID del fondo a cancelar
    
    Returns:
        dict: Mensaje de éxito, monto devuelto y nuevo saldo del cliente.
    
    Raises:
        HTTPException: Si cliente/fondo no existe o sin saldo invertido.
    """
    logger.info(f"Iniciando cancelación: cliente={cliente_id}, fondo={fondo_id}")
    
    try:
        if not cliente_id or not fondo_id:
            logger.warning("IDs de cliente o fondo vacíos")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cliente ID y Fondo ID son requeridos"
            )
        
        cliente = await obtener_cliente(cliente_id)
        if not cliente:
            logger.error(f"Cliente no encontrado en cancelación: {cliente_id}")
            log_transaccion(
                evento="cancelacion",
                cliente_id=cliente_id,
                fondo_id=fondo_id,
                estado="error",
                detalles={"error": "Cliente no encontrado"}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )
        
        fondo = await obtener_fondo(fondo_id)
        if not fondo:
            logger.error(f"Fondo no encontrado en cancelación: {fondo_id}")
            log_transaccion(
                evento="cancelacion",
                cliente_id=cliente_id,
                fondo_id=fondo_id,
                estado="error",
                detalles={"error": "Fondo no encontrado"}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fondo no encontrado"
            )
        
        # OBTENER HISTORIAL DE TRANSACCIONES DEL CLIENTE EN ESTE FONDO
        try:
            transacciones = await obtener_transacciones_cliente_fondo(cliente_id, fondo_id)
            if not transacciones:
                logger.warning(f"Sin transacciones previas para cancelar: {cliente_id}/{fondo_id}")
                log_transaccion(
                    evento="cancelacion",
                    cliente_id=cliente_id,
                    fondo_id=fondo_id,
                    estado="error",
                    detalles={"error": "Sin transacciones previas"}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No hay suscripciones previas en este fondo"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo transacciones: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al consultar historial de transacciones"
            )
        
        # CALCULAR SALDO INVERTIDO ACTUAL (automáticamente)
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
                f"Cálculo de saldo invertido: "
                f"aperturas={aperturas}, cancelaciones={cancelaciones}, "
                f"saldo_invertido={saldo_invertido}"
            )
        except Exception as e:
            logger.error(f"Error calculando saldo invertido: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al calcular saldo invertido"
            )
        
        # VALIDAR QUE HAY SALDO INVERTIDO
        if saldo_invertido <= 0:
            logger.warning(f"Sin saldo invertido para cancelar: {saldo_invertido}")
            log_transaccion(
                evento="cancelacion",
                cliente_id=cliente_id,
                fondo_id=fondo_id,
                monto=saldo_invertido,
                estado="error",
                detalles={"error": "Sin saldo invertido"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay dinero invertido en este fondo para cancelar"
            )
        
        # OBTENER SALDO ACTUAL DEL CLIENTE
        saldo_cliente_actual = float(cliente.get("saldo", 0))
        nuevo_saldo = saldo_cliente_actual + saldo_invertido
        
        logger.info(
            f"Dinero a devolver: ${saldo_invertido:,.2f} | "
            f"Saldo anterior: ${saldo_cliente_actual:,.2f} | "
            f"Nuevo saldo: ${nuevo_saldo:,.2f}"
        )
        
        # ACTUALIZAR SALDO DEL CLIENTE
        try:
            await actualizar_saldo_cliente(cliente["_id"], nuevo_saldo)
            logger.info(f"Saldo actualizado: ${saldo_cliente_actual:,.2f} -> ${nuevo_saldo:,.2f}")
        except Exception as e:
            logger.error(f"Error actualizando saldo en cancelación: {str(e)}")
            log_transaccion(
                evento="cancelacion",
                cliente_id=cliente_id,
                fondo_id=fondo_id,
                monto=saldo_invertido,
                estado="error",
                detalles={"error": f"Error actualizando saldo: {str(e)}"}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar la cancelación"
            )
        
        # REGISTRAR TRANSACCIÓN DE CANCELACIÓN
        from app.models import Transaccion
        transaccion_cancelacion = Transaccion(
            id_cliente=cliente_id,
            id_fondo=fondo_id,
            tipo=TipoTransaccion.cancelacion,
            monto=saldo_invertido  # Se usa el saldo invertido calculado
        )
        
        try:
            await crear_transaccion(transaccion_cancelacion)
            logger.info(
                f"Transacción de cancelación registrada: {transaccion_cancelacion.id} | "
                f"Monto: ${saldo_invertido:,.2f}"
            )
        except Exception as e:
            logger.error(f"Error registrando transacción de cancelación: {str(e)}")
            # ROLLBACK: revertir saldo
            try:
                await actualizar_saldo_cliente(cliente["_id"], saldo_cliente_actual)
                logger.info(f"ROLLBACK: Saldo revertido a: ${saldo_cliente_actual:,.2f}")
            except Exception as rollback_error:
                logger.critical(f"CRITICAL: Error en rollback de saldo: {str(rollback_error)}")
            
            log_transaccion(
                evento="cancelacion",
                cliente_id=cliente_id,
                fondo_id=fondo_id,
                monto=saldo_invertido,
                estado="error",
                detalles={"error": f"Error registrando transacción: {str(e)}"}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al registrar la cancelación"
            )
        
        # LOG DE ÉXITO
        log_transaccion(
            evento="cancelacion",
            cliente_id=cliente_id,
            fondo_id=fondo_id,
            monto=saldo_invertido,
            estado="success",
            detalles={
                "nuevo_saldo": nuevo_saldo,
                "saldo_devuelto": saldo_invertido
            }
        )
        
        logger.info(
            f" Cancelación exitosa: "
            f"cliente={cliente_id}, fondo={fondo_id}, "
            f"monto_devuelto=${saldo_invertido:,.2f}, "
            f"nuevo_saldo=${nuevo_saldo:,.2f}"
        )
        
        return {
            "mensaje": f"Cancelación exitosa del fondo {fondo['nombre']}. "
                      f"Se ha devuelto ${saldo_invertido:,.2f} a tu cuenta.",
            "fondo": fondo['nombre'],
            "monto_devuelto": saldo_invertido,
            "saldo_anterior": saldo_cliente_actual,
            "nuevo_saldo": nuevo_saldo,
            "transaccion_id": transaccion_cancelacion.id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en cancelar_fondo: {str(e)}", exc_info=True)
        log_transaccion(
            evento="cancelacion",
            cliente_id=cliente_id,
            fondo_id=fondo_id,
            estado="error",
            detalles={"error_inesperado": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )