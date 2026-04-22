from pydantic import BaseModel, Field, EmailStr, field_validator
from enum import Enum
from typing import Optional
from datetime import UTC, datetime
import uuid
import re


class LoginRequest(BaseModel):
    """Modelo para login de clientes"""
    cliente_id: str = Field(..., min_length=1, description="ID del cliente")
    password: str = Field(..., min_length=8, description="Contraseña (mín 8 caracteres)")

class CredencialesCliente(BaseModel):
    """Modelo para almacenar credenciales (SOLO en BD, nunca en respuestas)"""
    cliente_id: str
    password_hash: str
    activo: bool = True


class TipoTransaccion(str, Enum):
    apertura = "apertura"
    cancelacion = "cancelación"

class Cliente(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del cliente")
    saldo: float = 500000.0
    preferencia_notificacion: str  # "email" o "sms"
    contacto: str
    

    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if not isinstance(v, str) or len(v.strip()) == 0:
            raise ValueError("Nombre no puede estar vacío")
        return v.strip()
    
    @field_validator('contacto')
    @classmethod
    def validar_contacto(cls, v, info):
        preferencia = info.data.get('preferencia_notificacion')
        if preferencia == "email":
            # Validar email
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, v):
                raise ValueError("Email inválido")
        elif preferencia == "sms":
            # Validar teléfono (formato básico)
            if not re.match(r'^\+?[1-9]\d{1,14}$', v):
                raise ValueError("Teléfono inválido (formato: +1234567890)")
        return v

class Fondo(BaseModel):
    id: str = Field(..., min_length=1, description="ID del fondo")
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del fondo")
    monto_minimo: float = Field(..., gt=0, description="Monto mínimo de inversión")
    categoria: str = Field(..., min_length=2, description="Categoría del fondo")
    

    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if len(v.strip()) == 0:
            raise ValueError("Nombre del fondo no puede estar vacío")
        return v.strip()

class Transaccion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    id_cliente: str = Field(..., min_length=1, description="ID del cliente")
    id_fondo: str = Field(..., min_length=1, description="ID del fondo")
    tipo: TipoTransaccion
    monto: float = Field(..., gt=0, description="Monto debe ser positivo")
    fecha: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator('monto')
    @classmethod
    def validar_monto(cls, v):
        from app.config import MONTO_MINIMO_PERMITIDO, MONTO_MAXIMO_PERMITIDO
        if v < MONTO_MINIMO_PERMITIDO:
            raise ValueError(f"Monto mínimo permitido: {MONTO_MINIMO_PERMITIDO}")
        if v > MONTO_MAXIMO_PERMITIDO:
            raise ValueError(f"Monto máximo permitido: {MONTO_MAXIMO_PERMITIDO}")
        return v
    
    @field_validator('id_cliente', 'id_fondo')
    @classmethod
    def validar_ids(cls, v):
        if not isinstance(v, str) or len(v.strip()) == 0:
            raise ValueError("IDs no pueden estar vacíos")
        return v.strip()
    
class CancelacionRequest(BaseModel):
    """Modelo para cancelación de fondo (sin monto - se cancela todo)"""
    id_cliente: str = Field(..., min_length=1, description="ID del cliente")
    id_fondo: str = Field(..., min_length=1, description="ID del fondo")
    
    @field_validator('id_cliente', 'id_fondo')
    @classmethod
    def validar_ids(cls, v):
        if not isinstance(v, str) or len(v.strip()) == 0:
            raise ValueError("IDs no pueden estar vacíos")
        return v.strip()
