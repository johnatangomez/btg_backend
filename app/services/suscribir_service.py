from app.notifications.context import NotificationContext
from app.notifications.email_strategy import GmailSMTPNotification
from app.notifications.sms_strategy import SMSNotification
from fastapi import HTTPException, status
from app.repositories.fondos_repo import obtener_fondo, actualizar_saldo_cliente
from app.crud import obtener_cliente, crear_transaccion
from app.logger import logger, log_transaccion
from app.config import MONTO_MINIMO_PERMITIDO, MONTO_MAXIMO_PERMITIDO, TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM

async def suscribir_fondo(transaccion):
    """
    Suscribe a un cliente a un fondo de inversión, validando el monto mínimo 
    y el saldo disponible. Luego, envía una notificación al cliente según su 
    preferencia (email o SMS).
    
    Args:
        transaccion (Transaccion): La transacción de suscripción con validaciones Pydantic.
    
    Returns:
        dict: Mensaje de éxito y nuevo saldo del cliente.
    
    Raises:
        HTTPException: Si cliente no existe, fondo no existe, 
                       monto insuficiente o validación falla.
    """
    cliente_id = transaccion.id_cliente
    fondo_id = transaccion.id_fondo
    monto = transaccion.monto
    
    logger.info(f"Iniciando suscripción: cliente={cliente_id}, fondo={fondo_id}, monto={monto}")
    
    try:
        if monto < MONTO_MINIMO_PERMITIDO or monto > MONTO_MAXIMO_PERMITIDO:
            logger.warning(f"Monto fuera de rango: {monto}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Monto debe estar entre {MONTO_MINIMO_PERMITIDO} y {MONTO_MAXIMO_PERMITIDO}"
            )
        
        # Buscar cliente
        cliente = await obtener_cliente(cliente_id)
        if not cliente:
            logger.error(f"Cliente no encontrado: {cliente_id}")
            log_transaccion(
                evento="suscripcion",
                cliente_id=cliente_id,
                fondo_id=fondo_id,
                monto=monto,
                estado="error",
                detalles={"error": "Cliente no encontrado"}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )
        
        # Buscar fondo
        fondo = await obtener_fondo(fondo_id)
        if not fondo:
            logger.error(f"Fondo no encontrado: {fondo_id}")
            log_transaccion(
                evento="suscripcion",
                cliente_id=cliente_id,
                fondo_id=fondo_id,
                monto=monto,
                estado="error",
                detalles={"error": "Fondo no encontrado"}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fondo no encontrado"
            )
        
        # Validar monto mínimo del fondo
        if monto < float(fondo.get("monto_minimo", 0)):
            logger.warning(f"Monto inferior al mínimo: {monto} < {fondo['monto_minimo']}")
            log_transaccion(
                evento="suscripcion",
                cliente_id=cliente_id,
                fondo_id=fondo_id,
                monto=monto,
                estado="error",
                detalles={"error": "Monto inferior al mínimo"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El monto es inferior al mínimo requerido para {fondo['nombre']}: {fondo['monto_minimo']}"
            )
        
        # Validar saldo del cliente
        saldo_cliente = float(cliente.get("saldo", 0))
        if saldo_cliente < monto:
            logger.warning(f"Saldo insuficiente: {saldo_cliente} < {monto}")
            log_transaccion(
                evento="suscripcion",
                cliente_id=cliente_id,
                fondo_id=fondo_id,
                monto=monto,
                estado="error",
                detalles={"error": "Saldo insuficiente", "saldo_actual": saldo_cliente}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Saldo insuficiente. Disponible: {saldo_cliente}, Requerido: {monto}"
            )
        
        # Actualizar saldo
        nuevo_saldo = saldo_cliente - monto
        try:
            await actualizar_saldo_cliente(cliente["_id"], nuevo_saldo)
            logger.info(f"Saldo actualizado: {saldo_cliente} -> {nuevo_saldo}")
        except Exception as e:
            logger.error(f"Error actualizando saldo: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar la transacción"
            )
        
        # Registrar transacción
        try:
            await crear_transaccion(transaccion)
            logger.info(f"Transacción registrada: {transaccion.id}")
        except Exception as e:
            logger.error(f"Error registrando transacción: {str(e)}")
            # ROLLBACK: revertir saldo
            await actualizar_saldo_cliente(cliente["_id"], saldo_cliente)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al registrar la transacción"
            )
        
        # Enviar notificación (NO debe fallar toda la transacción si la notificación falla)
        preferencia = cliente.get("preferencia_notificacion", "email")
        destinatario = cliente.get("contacto", "")
        
        try:
            mensaje = f"Suscripción exitosa al fondo {fondo['nombre']} por ${monto:,.2f}"
            
            if preferencia == "email":
                context = NotificationContext(GmailSMTPNotification())
                await context.notify(
                    destinatario,
                    mensaje,
                    datos={"fondo": fondo["nombre"], "monto": monto}
                )
                logger.info(f"Email enviado a {destinatario}")
            elif preferencia == "sms":
                context = NotificationContext(
                    SMSNotification(TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM)
                )
                await context.notify(destinatario, mensaje)
                logger.info(f"SMS enviado a {destinatario}")
            else:
                logger.warning(f"Preferencia de notificación desconocida: {preferencia}")
        except Exception as e:
            # Log pero NO fallar la suscripción
            logger.warning(f"Error enviando notificación: {str(e)}")
            log_transaccion(
                evento="suscripcion",
                cliente_id=cliente_id,
                fondo_id=fondo_id,
                monto=monto,
                estado="success_notificacion_fallida",
                detalles={"error_notificacion": str(e)}
            )
        
        # Log de éxito
        log_transaccion(
            evento="suscripcion",
            cliente_id=cliente_id,
            fondo_id=fondo_id,
            monto=monto,
            estado="success",
            detalles={"nuevo_saldo": nuevo_saldo}
        )
        
        return {
            "mensaje": f"Suscripción exitosa al fondo {fondo['nombre']}",
            "nuevo_saldo": nuevo_saldo,
            "transaccion_id": transaccion.id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en suscribir_fondo: {str(e)}", exc_info=True)
        log_transaccion(
            evento="suscripcion",
            cliente_id=cliente_id,
            fondo_id=fondo_id,
            monto=monto,
            estado="error",
            detalles={"error_inesperado": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )