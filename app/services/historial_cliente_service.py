from fastapi import HTTPException, status
from bson import json_util
import json
from app.database import db
from app.logger import logger

async def historial_por_cliente(id_cliente: str):
    """
    Obtiene el historial completo de transacciones de un cliente, 
    agrupado por fondo, con el saldo invertido actual y el total 
    invertido en todos los fondos.
    
    Args:
        id_cliente (str): El ID del cliente.
    
    Returns:
        dict: Historial de transacciones por fondo, saldo invertido 
              actual por fondo y total invertido en todos los fondos.
    
    Raises:
        HTTPException: Si no hay transacciones para el cliente.
    """
    logger.info(f"Consultando historial completo para cliente: {id_cliente}")
    
    try:
        if not id_cliente or not isinstance(id_cliente, str):
            logger.warning("Cliente ID inválido")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cliente ID debe ser una cadena no vacía"
            )
        

        try:
            cursor = db.transacciones.find({"id_cliente": id_cliente}).sort("fecha", 1)
            transacciones = [t async for t in cursor]
            logger.info(f"Se recuperaron {len(transacciones)} transacciones")
        except Exception as e:
            logger.error(f"Error consultando BD para transacciones: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al consultar historial de transacciones"
            )
        
        # Validar que hay transacciones
        if not transacciones:
            logger.warning(f"Sin transacciones para cliente: {id_cliente}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay transacciones para este cliente"
            )
        
        # Procesar datos
        try:
            # Agrupar por fondo
            resumen = {}
            for t in transacciones:
                id_fondo = t.get("id_fondo")
                tipo = t.get("tipo", "")
                monto = float(t.get("monto", 0))
                
                if not id_fondo:
                    logger.warning(f"Transacción sin id_fondo: {t.get('id')}")
                    continue
                
                if id_fondo not in resumen:
                    resumen[id_fondo] = {
                        "aperturas": 0.0,
                        "cancelaciones": 0.0,
                        "historial": []
                    }
                
                if tipo == "apertura":
                    resumen[id_fondo]["aperturas"] += monto
                elif tipo == "cancelación":
                    resumen[id_fondo]["cancelaciones"] += monto
                
                resumen[id_fondo]["historial"].append(t)
            
            logger.info(f"Agrupadas transacciones en {len(resumen)} fondos")
        except Exception as e:
            logger.error(f"Error procesando transacciones: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar historial"
            )
        
        # Calcular saldos
        try:
            resultado = []
            for id_fondo, datos in resumen.items():
                saldo_invertido = datos["aperturas"] - datos["cancelaciones"]
                
                # Validar que saldo sea consistente
                if saldo_invertido < 0:
                    logger.warning(
                        f"Saldo invertido negativo detectado: "
                        f"cliente={id_cliente}, fondo={id_fondo}, saldo={saldo_invertido}"
                    )
                
                resultado.append({
                    "id_fondo": id_fondo,
                    "saldo_invertido_actual": saldo_invertido,
                    "aperturas_totales": datos["aperturas"],
                    "cancelaciones_totales": datos["cancelaciones"],
                    "historial": datos["historial"]
                })
            
            # Total invertido en todos los fondos
            total_invertido = sum(r["saldo_invertido_actual"] for r in resultado)
            
            logger.info(
                f"Cálculos completados: {len(resultado)} fondos, "
                f"total invertido: {total_invertido}"
            )
        except Exception as e:
            logger.error(f"Error calculando saldos: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al calcular saldos"
            )
        
        # Serializar respuesta
        try:
            respuesta = json.loads(json_util.dumps({
                "id_cliente": id_cliente,
                "cantidad_fondos": len(resultado),
                "total_invertido": total_invertido,
                "fondos": resultado
            }))
            
            logger.info(f"Historial serializado exitosamente para cliente: {id_cliente}")
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
        logger.error(f"Error inesperado en historial_por_cliente: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )