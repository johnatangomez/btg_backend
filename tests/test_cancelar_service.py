import pytest
import pytest_asyncio
from fastapi import HTTPException
from app.services.cancelar_service import cancelar_fondo
from app.models import TipoTransaccion

@pytest_asyncio.fixture
async def fake_repo_cancelar(monkeypatch):
    """Fixture con datos para tests de cancelación"""
    cliente = {"_id": "c1", "saldo": 100000}
    fondo = {"_id": 1, "nombre": "Fondo Prueba"}
    transacciones = [
        {"id_cliente": "c1", "id_fondo": "1", "tipo": "apertura", "monto": 100000}
    ]

    async def fake_obtener_cliente(id_cliente):
        return cliente if id_cliente == "c1" else None

    async def fake_obtener_fondo(id_fondo):
        return fondo if int(id_fondo) == 1 else None

    async def fake_actualizar_saldo_cliente(cliente_id, nuevo_saldo):
        cliente["saldo"] = nuevo_saldo

    async def fake_obtener_transacciones_cliente_fondo(id_cliente, id_fondo):
        return transacciones

    async def fake_crear_transaccion(transaccion):
        transacciones.append(transaccion.model_dump())
        return True

    monkeypatch.setattr("app.services.cancelar_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.cancelar_service.obtener_fondo", fake_obtener_fondo)
    monkeypatch.setattr("app.services.cancelar_service.actualizar_saldo_cliente", fake_actualizar_saldo_cliente)
    monkeypatch.setattr("app.services.cancelar_service.obtener_transacciones_cliente_fondo", fake_obtener_transacciones_cliente_fondo)
    monkeypatch.setattr("app.services.cancelar_service.crear_transaccion", fake_crear_transaccion)

    return {"cliente": cliente, "fondo": fondo, "transacciones": transacciones}

@pytest.mark.asyncio
async def test_cancelar_fondo_success(fake_repo_cancelar):
    """Test: Cancelación exitosa"""
    result = await cancelar_fondo("c1", "1")
    
    assert result["monto_devuelto"] == 100000
    assert result["nuevo_saldo"] == 200000  # 100000 + 100000
    assert "Cancelación exitosa" in result["mensaje"]

@pytest.mark.asyncio
async def test_cancelar_fondo_sin_saldo(fake_repo_cancelar):
    """Test: Sin saldo invertido (múltiples cancelaciones)"""
    # Agregamos una cancelación para que saldo_invertido = 0
    fake_repo_cancelar["transacciones"].append({
        "id_cliente": "c1", "id_fondo": "1", "tipo": "cancelación", "monto": 100000
    })
    
    with pytest.raises(HTTPException) as exc_info:
        await cancelar_fondo("c1", "1")
    assert exc_info.value.status_code == 400
    assert "No hay dinero invertido" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_cancelar_fondo_cliente_no_existe(fake_repo_cancelar):
    """Test: Cliente no existe"""
    with pytest.raises(HTTPException) as exc_info:
        await cancelar_fondo("c999", "1")
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_cancelar_fondo_fondo_no_existe(fake_repo_cancelar):
    """Test: Fondo no existe"""
    with pytest.raises(HTTPException) as exc_info:
        await cancelar_fondo("c1", "999")
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_cancelar_fondo_calculo_correcto(monkeypatch):
    """Test: Cálculo correcto de saldo con múltiples transacciones"""
    cliente = {"_id": "c1", "saldo": 100000}
    fondo = {"_id": 1, "nombre": "Fondo Prueba"}
    transacciones = [
        {"id_cliente": "c1", "id_fondo": "1", "tipo": "apertura", "monto": 150000},
        {"id_cliente": "c1", "id_fondo": "1", "tipo": "cancelación", "monto": 50000},
    ]

    async def fake_obtener_cliente(id_cliente):
        return cliente

    async def fake_obtener_fondo(id_fondo):
        return fondo

    async def fake_actualizar_saldo_cliente(cliente_id, nuevo_saldo):
        cliente["saldo"] = nuevo_saldo

    async def fake_obtener_transacciones_cliente_fondo(id_cliente, id_fondo):
        return transacciones

    async def fake_crear_transaccion(transaccion):
        return True

    monkeypatch.setattr("app.services.cancelar_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.cancelar_service.obtener_fondo", fake_obtener_fondo)
    monkeypatch.setattr("app.services.cancelar_service.actualizar_saldo_cliente", fake_actualizar_saldo_cliente)
    monkeypatch.setattr("app.services.cancelar_service.obtener_transacciones_cliente_fondo", fake_obtener_transacciones_cliente_fondo)
    monkeypatch.setattr("app.services.cancelar_service.crear_transaccion", fake_crear_transaccion)

    result = await cancelar_fondo("c1", "1")
    
    # Saldo invertido = 150000 - 50000 = 100000
    assert result["monto_devuelto"] == 100000
    assert result["nuevo_saldo"] == 200000  # 100000 + 100000

@pytest.mark.asyncio
async def test_cancelar_fondo_error_actualizando_saldo(monkeypatch):
    """Test: Error al actualizar saldo"""
    cliente = {"_id": "c1", "saldo": 100000}
    fondo = {"_id": 1, "nombre": "Fondo Prueba"}
    transacciones = [
        {"id_cliente": "c1", "id_fondo": "1", "tipo": "apertura", "monto": 100000}
    ]

    async def fake_obtener_cliente(id_cliente):
        return cliente

    async def fake_obtener_fondo(id_fondo):
        return fondo

    async def fake_actualizar_saldo_error(cliente_id, nuevo_saldo):
        raise Exception("BD Error")

    async def fake_obtener_transacciones_cliente_fondo(id_cliente, id_fondo):
        return transacciones

    async def fake_crear_transaccion(transaccion):
        return True

    monkeypatch.setattr("app.services.cancelar_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.cancelar_service.obtener_fondo", fake_obtener_fondo)
    monkeypatch.setattr("app.services.cancelar_service.actualizar_saldo_cliente", fake_actualizar_saldo_error)
    monkeypatch.setattr("app.services.cancelar_service.obtener_transacciones_cliente_fondo", fake_obtener_transacciones_cliente_fondo)
    monkeypatch.setattr("app.services.cancelar_service.crear_transaccion", fake_crear_transaccion)

    with pytest.raises(HTTPException) as exc_info:
        await cancelar_fondo("c1", "1")
    assert exc_info.value.status_code == 500