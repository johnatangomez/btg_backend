#!/usr/bin/env python3
"""
Script para crear usuarios desde línea de comandos.

Uso:
    python scripts/crear_usuario.py
    
Requisitos:
    - Estar en el directorio raíz del proyecto
    - Tener MongoDB corriendo
"""

import asyncio
import sys
import os
from pathlib import Path
import re

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import db
from app.logger import logger
from app.utils import hashear_contraseña

async def crear_usuario():
    """Crea un usuario interactivamente"""
    
    print("\n" + "="*60)
    print("  CREAR NUEVO USUARIO BTG FONDOS".center(60))
    print("="*60 + "\n")
    
    try:
        cliente_id = input("ID del cliente (ej: cliente001): ").strip()
        if not cliente_id:
            print("ID de cliente no puede estar vacío")
            return
        
        nombre = input("Nombre completo: ").strip()
        if not nombre or len(nombre) < 2:
            print("Nombre debe tener al menos 2 caracteres")
            return
        
        # Validar email o teléfono
        while True:
            print("\n Selecciona tipo de contacto:")
            print("  1. Email")
            print("  2. Teléfono (SMS)")
            tipo_contacto = input("Opción (1 o 2): ").strip()
            
            if tipo_contacto == "1":
                preferencia = "email"
                contacto = input("📧 Email: ").strip()
                email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_regex, contacto):
                    print("Email inválido. Intenta de nuevo.")
                    continue
                break
            elif tipo_contacto == "2":
                preferencia = "sms"
                contacto = input("Teléfono (formato: +1234567890): ").strip()
                if not re.match(r'^\+?[1-9]\d{1,14}$', contacto):
                    print("Teléfono inválido. Usa formato: +1234567890")
                    continue
                break
            else:
                print("Opción inválida. Selecciona 1 o 2.")
        
        saldo = input("\nSaldo inicial (default: 500000): ").strip()
        if saldo:
            try:
                saldo = float(saldo)
                if saldo < 0:
                    print("El saldo no puede ser negativo")
                    return
            except ValueError:
                print("El saldo debe ser un número válido")
                return
        else:
            saldo = 500000.0
        
        # Solicitar contraseña
        while True:
            password = input("\nContraseña (mínimo 8 caracteres): ").strip()
            if len(password) < 8:
                print("La contraseña debe tener al menos 8 caracteres")
                continue
            
            password_confirm = input("Confirmar contraseña: ").strip()
            if password != password_confirm:
                print("Las contraseñas no coinciden. Intenta de nuevo.")
                continue
            break
        
        # VALIDAR QUE NO EXISTA
        cliente_existente = await db.clientes.find_one({"_id": cliente_id})
        if cliente_existente:
            print(f"\nEl usuario '{cliente_id}' ya existe")
            return
        
        # HASHEAR CONTRASEÑA
        logger.info(f"Hasheando contraseña para {cliente_id}")
        password_hash = hashear_contraseña(password)
        
        # CREAR DOCUMENTO
        nuevo_cliente = {
            "_id": cliente_id,
            "nombre": nombre,
            "saldo": saldo,
            "preferencia_notificacion": preferencia,
            "contacto": contacto,
            "password_hash": password_hash,
            "activo": True
        }
        
        # INSERTAR EN BD
        resultado = await db.clientes.insert_one(nuevo_cliente)
        
        print("\n" + "="*60)
        print("USUARIO CREADO EXITOSAMENTE".center(60))
        print("="*60)
        print(f"\n Datos del usuario:")
        print(f"   ID: {cliente_id}")
        print(f"   Nombre: {nombre}")
        print(f"   Contacto: {contacto} ({preferencia})")
        print(f"   Saldo inicial: ${saldo:,.2f}")
        print(f"   Estado: Activo")
        print("\n Ahora puede hacer login en la API con:")
        print(f"   POST /fondos/login")
        print(f"   Body: {{\n      \"cliente_id\": \"{cliente_id}\",")
        print(f"           \"password\": \"<contraseña>\"\n   }}")
        print("="*60 + "\n")
        
        logger.info(f"Usuario creado exitosamente: {cliente_id}")
        
    except KeyboardInterrupt:
        print("\n\n Operación cancelada")
        return
    except Exception as e:
        print(f"\n Error creando usuario: {str(e)}")
        logger.error(f"Error en crear_usuario: {str(e)}", exc_info=True)
        return

async def main():
    """Función principal"""
    try:
        await crear_usuario()
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())