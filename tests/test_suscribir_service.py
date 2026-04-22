import pytest
import pytest_asyncio
from fastapi import HTTPException
from pydantic import ValidationError
from app.services.suscribir_service import suscribir_fondo
from app.models import Transaccion

@pytest_asyncio.fixture
async def fake_repo_suscribir(monkeypatch):
    """Fixture con datos correctos para tests de suscripción"""
    cliente = {"_id": "c1", "saldo": 200000, "preferencia_notificacion": "email", "contacto": "test@example.com"}
    fondo = {"_id": 1, "nombre": "Fondo Prueba", "monto_minimo": 50000}
    transacciones = []

    async def fake_obtener_cliente(id_cliente):
        return cliente if id_cliente == "c1" else None

    async def fake_obtener_fondo(id_fondo):
        return fondo if int(id_fondo) == 1 else None

    async def fake_actualizar_saldo_cliente(cliente_id, nuevo_saldo):
        cliente["saldo"] = nuevo_saldo
        return {"cliente_id": cliente_id, "saldo_nuevo": nuevo_saldo}

    async def fake_crear_transaccion(transaccion):
        transacciones.append(transaccion.model_dump())
        return True

    monkeypatch.setattr("app.services.suscribir_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.suscribir_service.obtener_fondo", fake_obtener_fondo)
    monkeypatch.setattr("app.services.suscribir_service.actualizar_saldo_cliente", fake_actualizar_saldo_cliente)
    monkeypatch.setattr("app.services.suscribir_service.crear_transaccion", fake_crear_transaccion)

    return {"cliente": cliente, "fondo": fondo, "transacciones": transacciones}

@pytest.mark.asyncio
async def test_suscribir_fondo_success(fake_repo_suscribir):
    """Test: Suscripción exitosa"""
    transaccion = Transaccion(id="tx1", id_cliente="c1", id_fondo="1", tipo="apertura", monto=100000)
    result = await suscribir_fondo(transaccion)
    
    assert result["nuevo_saldo"] == 100000
    assert "Suscripción exitosa" in result["mensaje"]
    assert result["transaccion_id"] == "tx1"

@pytest.mark.asyncio
async def test_suscribir_fondo_monto_inferior_fondo(fake_repo_suscribir):
    """Test: Monto inferior al mínimo del fondo"""
    transaccion = Transaccion(id="tx2", id_cliente="c1", id_fondo="1", tipo="apertura", monto=40000)
    with pytest.raises(HTTPException) as exc_info:
        await suscribir_fondo(transaccion)
    assert exc_info.value.status_code == 400
    assert "inferior al mínimo" in str(exc_info.value.detail)

def test_suscribir_fondo_monto_minimo_global():
    """Test: Error de validación Pydantic por monto < 1000"""
    with pytest.raises(ValidationError) as exc_info:
        Transaccion(id="tx3", id_cliente="c1", id_fondo="1", tipo="apertura", monto=500)
    assert "Monto mínimo permitido" in str(exc_info.value)

def test_suscribir_fondo_monto_maximo_global():
    """Test: Error de validación Pydantic por monto > 500000"""
    with pytest.raises(ValidationError) as exc_info:
        Transaccion(id="tx4", id_cliente="c1", id_fondo="1", tipo="apertura", monto=600000)
    assert "Monto máximo permitido" in str(exc_info.value)

@pytest.mark.asyncio
async def test_suscribir_fondo_saldo_insuficiente(fake_repo_suscribir):
    """Test: Saldo insuficiente del cliente"""
    transaccion = Transaccion(id="tx5", id_cliente="c1", id_fondo="1", tipo="apertura", monto=300000)
    with pytest.raises(HTTPException) as exc_info:
        await suscribir_fondo(transaccion)
    assert exc_info.value.status_code == 400
    assert "Saldo insuficiente" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_suscribir_fondo_cliente_no_existe(fake_repo_suscribir):
    """Test: Cliente no existe"""
    transaccion = Transaccion(id="tx6", id_cliente="c999", id_fondo="1", tipo="apertura", monto=100000)
    with pytest.raises(HTTPException) as exc_info:
        await suscribir_fondo(transaccion)
    assert exc_info.value.status_code == 404
    assert "Cliente no encontrado" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_suscribir_fondo_fondo_no_existe(fake_repo_suscribir):
    """Test: Fondo no existe"""
    transaccion = Transaccion(id="tx7", id_cliente="c1", id_fondo="999", tipo="apertura", monto=100000)
    with pytest.raises(HTTPException) as exc_info:
        await suscribir_fondo(transaccion)
    assert exc_info.value.status_code == 404
    assert "Fondo no encontrado" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_suscribir_fondo_error_actualizando_saldo(monkeypatch):
    """Test: Error al actualizar saldo en BD"""
    cliente = {"_id": "c1", "saldo": 200000}
    fondo = {"_id": 1, "nombre": "Fondo Prueba", "monto_minimo": 50000}

    async def fake_obtener_cliente(id_cliente):
        return cliente

    async def fake_obtener_fondo(id_fondo):
        return fondo

    async def fake_actualizar_saldo_error(cliente_id, nuevo_saldo):
        raise Exception("DB Error")

    async def fake_crear_transaccion(transaccion):
        return True

    monkeypatch.setattr("app.services.suscribir_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.suscribir_service.obtener_fondo", fake_obtener_fondo)
    monkeypatch.setattr("app.services.suscribir_service.actualizar_saldo_cliente", fake_actualizar_saldo_error)
    monkeypatch.setattr("app.services.suscribir_service.crear_transaccion", fake_crear_transaccion)

    transaccion = Transaccion(id="tx8", id_cliente="c1", id_fondo="1", tipo="apertura", monto=100000)
    with pytest.raises(HTTPException) as exc_info:
        await suscribir_fondo(transaccion)
    assert exc_info.value.status_code == 500

@pytest.mark.asyncio
async def test_suscribir_fondo_error_creando_transaccion(monkeypatch):
    """Test: Error al crear transacción - validar rollback"""
    cliente = {"_id": "c1", "saldo": 200000}
    fondo = {"_id": 1, "nombre": "Fondo Prueba", "monto_minimo": 50000}
    saldo_original = cliente["saldo"]

    async def fake_obtener_cliente(id_cliente):
        return cliente

    async def fake_obtener_fondo(id_fondo):
        return fondo

    async def fake_actualizar_saldo(cliente_id, nuevo_saldo):
        cliente["saldo"] = nuevo_saldo

    async def fake_crear_transaccion_error(transaccion):
        raise Exception("BD Error")

    monkeypatch.setattr("app.services.suscribir_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.suscribir_service.obtener_fondo", fake_obtener_fondo)
    monkeypatch.setattr("app.services.suscribir_service.actualizar_saldo_cliente", fake_actualizar_saldo)
    monkeypatch.setattr("app.services.suscribir_service.crear_transaccion", fake_crear_transaccion_error)

    transaccion = Transaccion(id="tx9", id_cliente="c1", id_fondo="1", tipo="apertura", monto=100000)
    with pytest.raises(HTTPException) as exc_info:
        await suscribir_fondo(transaccion)
    assert exc_info.value.status_code == 500
    # Validar rollback - saldo vuelve a original
    assert cliente["saldo"] == saldo_original
